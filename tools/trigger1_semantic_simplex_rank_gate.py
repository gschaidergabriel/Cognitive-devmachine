#!/usr/bin/env python3
"""Deterministic calibration-only rank gate for Trigger-1 semantic simplex research.

This tool does not execute a model and does not open holdout. It consumes already-captured,
label-free calibration activations with frozen provenance and distinguishes:
  ONE_DIMENSIONAL_SUPPORTED
  TWO_DIMENSIONAL_REQUIRED
  UNRESOLVED

The decision is deliberately equivalence-aware: failure to detect a second dimension is
not enough to claim rank-1. Rank-1 requires a preregistered small-effect ceiling plus
leave-one-family-out stability. Rank-2 requires both effect size and an independent
within-family label-permutation null.

Input schema: CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION/v1
Output schema: CLAY_TRIGGER1_SEMANTIC_SIMPLEX_RANK_GATE_RESULT/v1
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import struct
from pathlib import Path
from typing import Any, Iterable

INPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION/v1"
OUTPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_RANK_GATE_RESULT/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
SOURCE_HASH_KEYS = (
    "model_checkpoint_sha256",
    "tokenizer_sha256",
    "runtime_build_sha256",
)
ATTESTATION_TRUE_KEYS = (
    "calibration_only",
    "label_free_model_facing_prompts",
    "lexically_disjoint_families",
    "output_code_independent",
)
REQUIRED_THRESHOLDS = (
    "min_families",
    "null_percentile",
    "null_max_exact",
    "null_sample_count",
    "null_seed",
    "rank2_min_sigma2_over_sigma1",
    "rank2_min_null_excess",
    "rank2_min_loo_fraction",
    "rank1_max_sigma2_over_sigma1",
    "rank1_min_loo_fraction",
)
EPS = 1e-12


class GateError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def vector_sha(vector: list[float]) -> str:
    raw = b"".join(struct.pack("<d", float(x)) for x in vector)
    return hashlib.sha256(raw).hexdigest()


def _finite_vector(value: Any, *, row_index: int) -> list[float]:
    if not isinstance(value, list) or len(value) < 2:
        raise GateError(f"ROW_{row_index}_VECTOR_INVALID")
    out = [float(x) for x in value]
    if not all(math.isfinite(x) for x in out):
        raise GateError(f"ROW_{row_index}_VECTOR_NONFINITE")
    return out


def _dot(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b))


def _sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]


def _mean(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        raise GateError("EMPTY_VECTOR_GROUP")
    dim = len(vectors[0])
    if any(len(v) != dim for v in vectors):
        raise GateError("VECTOR_DIMENSION_MISMATCH")
    return [math.fsum(v[j] for v in vectors) / len(vectors) for j in range(dim)]


def _geometry(class_means: dict[str, list[float]]) -> dict[str, float]:
    """SVD of the centered 3-class centroid matrix via a 2xD Helmert contrast basis."""
    a = class_means["AFFIRMATIVE"]
    n = class_means["NEGATIVE"]
    u = class_means["NEUTRAL"]
    if not (len(a) == len(n) == len(u)):
        raise GateError("CLASS_MEAN_DIMENSION_MISMATCH")

    q1_a = math.sqrt(2.0 / 3.0)
    q1_other = -1.0 / math.sqrt(6.0)
    q2 = 1.0 / math.sqrt(2.0)
    v1 = [q1_a * a[i] + q1_other * n[i] + q1_other * u[i] for i in range(len(a))]
    v2 = [q2 * n[i] - q2 * u[i] for i in range(len(a))]

    g11 = _dot(v1, v1)
    g22 = _dot(v2, v2)
    g12 = _dot(v1, v2)
    trace = g11 + g22
    disc = max(0.0, (g11 - g22) ** 2 + 4.0 * g12 * g12)
    root = math.sqrt(disc)
    lam1 = max(0.0, 0.5 * (trace + root))
    lam2 = max(0.0, 0.5 * (trace - root))
    sigma1 = math.sqrt(lam1)
    sigma2 = math.sqrt(lam2)
    ratio = sigma2 / sigma1 if sigma1 > EPS else float("nan")
    return {
        "sigma1": sigma1,
        "sigma2": sigma2,
        "sigma2_over_sigma1": ratio,
        "contrast1_sha256": vector_sha(v1),
        "contrast2_sha256": vector_sha(v2),
    }


def _family_scale(families: dict[str, dict[str, list[float]]]) -> float:
    """RMS within-family centered class displacement; invariant to class relabeling."""
    energies: list[float] = []
    for family_id in sorted(families):
        class_map = families[family_id]
        center = _mean([class_map[c] for c in CLASSES])
        energies.append(
            math.fsum(_dot(_sub(class_map[c], center), _sub(class_map[c], center)) for c in CLASSES)
            / len(CLASSES)
        )
    value = math.sqrt(math.fsum(energies) / len(energies))
    if not math.isfinite(value) or value <= EPS:
        raise GateError("FAMILY_CENTERED_SCALE_DEGENERATE")
    return value


def _aggregate_class_means(families: dict[str, dict[str, list[float]]]) -> dict[str, list[float]]:
    return {
        c: _mean([families[f][c] for f in sorted(families)])
        for c in CLASSES
    }


def _nearest_rank_quantile(values: list[float], q: float) -> float:
    if not values:
        raise GateError("EMPTY_NULL_DISTRIBUTION")
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))
    return ordered[idx]


def _permuted_family(
    original: dict[str, list[float]], permutation: tuple[str, str, str]
) -> dict[str, list[float]]:
    return {target: original[source] for target, source in zip(CLASSES, permutation)}


def _null_choices(
    family_count: int,
    *,
    max_exact: int,
    sample_count: int,
    seed: int,
) -> tuple[str, Iterable[tuple[int, ...]], int]:
    """Anchor family 0 to remove irrelevant global-label permutation symmetry."""
    movable = family_count - 1
    total = 6 ** movable
    nonidentity_total = total - 1
    if nonidentity_total <= 0:
        raise GateError("NULL_REQUIRES_AT_LEAST_TWO_FAMILIES")

    if nonidentity_total <= max_exact:
        choices = (
            x
            for x in itertools.product(range(6), repeat=movable)
            if any(i != 0 for i in x)
        )
        return "EXACT", choices, nonidentity_total

    target = min(sample_count, nonidentity_total)
    rng = random.Random(seed)
    seen: set[tuple[int, ...]] = set()
    while len(seen) < target:
        choice = tuple(rng.randrange(6) for _ in range(movable))
        if any(i != 0 for i in choice):
            seen.add(choice)
    ordered = sorted(seen)
    return "DETERMINISTIC_SAMPLED", ordered, len(ordered)


def _permutation_null(
    families: dict[str, dict[str, list[float]]],
    family_scale: float,
    *,
    null_percentile: float,
    max_exact: int,
    sample_count: int,
    seed: int,
) -> dict[str, Any]:
    keys = sorted(families)
    permutations = list(itertools.permutations(CLASSES))
    mode, choices, count = _null_choices(
        len(keys), max_exact=max_exact, sample_count=sample_count, seed=seed
    )
    null_values: list[float] = []
    for choice in choices:
        permuted: dict[str, dict[str, list[float]]] = {keys[0]: families[keys[0]]}
        for family_id, perm_idx in zip(keys[1:], choice):
            permuted[family_id] = _permuted_family(families[family_id], permutations[perm_idx])
        geom = _geometry(_aggregate_class_means(permuted))
        null_values.append(float(geom["sigma2"]) / family_scale)

    q = _nearest_rank_quantile(null_values, null_percentile)
    return {
        "mode": mode,
        "anchored_family_id": keys[0],
        "global_label_symmetry_removed": True,
        "samples": count,
        "percentile": null_percentile,
        "sigma2_over_family_scale_quantile": q,
        "sigma2_over_family_scale_min": min(null_values),
        "sigma2_over_family_scale_max": max(null_values),
        "null_values_sha256": canonical_sha(null_values),
    }


def _validate_thresholds(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise GateError("PREREGISTRATION_REQUIRED")
    missing = [k for k in REQUIRED_THRESHOLDS if k not in raw]
    if missing:
        raise GateError("PREREGISTRATION_MISSING:" + ",".join(missing))

    p = {
        "min_families": int(raw["min_families"]),
        "null_percentile": float(raw["null_percentile"]),
        "null_max_exact": int(raw["null_max_exact"]),
        "null_sample_count": int(raw["null_sample_count"]),
        "null_seed": int(raw["null_seed"]),
        "rank2_min_sigma2_over_sigma1": float(raw["rank2_min_sigma2_over_sigma1"]),
        "rank2_min_null_excess": float(raw["rank2_min_null_excess"]),
        "rank2_min_loo_fraction": float(raw["rank2_min_loo_fraction"]),
        "rank1_max_sigma2_over_sigma1": float(raw["rank1_max_sigma2_over_sigma1"]),
        "rank1_min_loo_fraction": float(raw["rank1_min_loo_fraction"]),
    }
    if p["min_families"] < 3:
        raise GateError("MIN_FAMILIES_MUST_BE_AT_LEAST_3")
    if not (0.5 <= p["null_percentile"] < 1.0):
        raise GateError("NULL_PERCENTILE_INVALID")
    if p["null_max_exact"] < 1 or p["null_sample_count"] < 1:
        raise GateError("NULL_BUDGET_INVALID")
    if not (0.0 <= p["rank1_max_sigma2_over_sigma1"] < p["rank2_min_sigma2_over_sigma1"] <= 1.0):
        raise GateError("RANK_EFFECT_THRESHOLDS_INVALID")
    if p["rank2_min_null_excess"] < 0.0:
        raise GateError("RANK2_NULL_EXCESS_INVALID")
    for key in ("rank2_min_loo_fraction", "rank1_min_loo_fraction"):
        if not (0.0 < p[key] <= 1.0):
            raise GateError(f"{key.upper()}_INVALID")
    return p


def _validate_payload(payload: Any) -> tuple[
    dict[str, dict[str, list[float]]], dict[str, Any], dict[str, Any], int
]:
    if not isinstance(payload, dict) or payload.get("schema") != INPUT_SCHEMA:
        raise GateError("INPUT_SCHEMA_MISMATCH")

    att = payload.get("design_attestation")
    if not isinstance(att, dict):
        raise GateError("DESIGN_ATTESTATION_REQUIRED")
    for key in ATTESTATION_TRUE_KEYS:
        if att.get(key) is not True:
            raise GateError(f"DESIGN_ATTESTATION_FAIL:{key}")
    if att.get("fresh_holdout_opened") is not False:
        raise GateError("FRESH_HOLDOUT_MUST_REMAIN_CLOSED")

    source = payload.get("source_identity")
    if not isinstance(source, dict):
        raise GateError("SOURCE_IDENTITY_REQUIRED")
    for key in SOURCE_HASH_KEYS:
        value = source.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
            raise GateError(f"SOURCE_HASH_INVALID:{key}")
    if not isinstance(source.get("activation_site"), str) or not source["activation_site"]:
        raise GateError("ACTIVATION_SITE_REQUIRED")
    if not isinstance(source.get("token_scope"), str) or not source["token_scope"]:
        raise GateError("TOKEN_SCOPE_REQUIRED")
    if not isinstance(source.get("layer"), int) or source["layer"] < 0:
        raise GateError("LAYER_REQUIRED")

    prereg = _validate_thresholds(payload.get("preregistration"))

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise GateError("ROWS_REQUIRED")

    prompt_hashes: set[str] = set()
    dim: int | None = None
    grouped: dict[str, dict[str, list[list[float]]]] = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise GateError(f"ROW_{idx}_INVALID")
        family = row.get("family_id")
        semantic = row.get("semantic_class")
        if not isinstance(family, str) or not family:
            raise GateError(f"ROW_{idx}_FAMILY_ID_INVALID")
        if semantic not in CLASSES:
            raise GateError(f"ROW_{idx}_SEMANTIC_CLASS_INVALID")
        if row.get("label_free") is not True:
            raise GateError(f"ROW_{idx}_LABEL_FREE_ATTESTATION_FAIL")
        if row.get("output_code_free") is not True:
            raise GateError(f"ROW_{idx}_OUTPUT_CODE_FREE_ATTESTATION_FAIL")
        prompt_sha = row.get("prompt_sha256")
        if not isinstance(prompt_sha, str) or len(prompt_sha) != 64:
            raise GateError(f"ROW_{idx}_PROMPT_SHA_INVALID")
        if prompt_sha in prompt_hashes:
            raise GateError(f"ROW_{idx}_PROMPT_SHA_REUSED")
        prompt_hashes.add(prompt_sha)

        vec = _finite_vector(row.get("vector"), row_index=idx)
        if dim is None:
            dim = len(vec)
        elif len(vec) != dim:
            raise GateError(f"ROW_{idx}_VECTOR_DIMENSION_MISMATCH")
        grouped.setdefault(family, {}).setdefault(semantic, []).append(vec)

    if dim is None:
        raise GateError("VECTOR_DIMENSION_UNRESOLVED")
    if len(grouped) < prereg["min_families"]:
        raise GateError("INSUFFICIENT_FAMILIES")
    for family, class_map in grouped.items():
        missing = [c for c in CLASSES if c not in class_map]
        if missing:
            raise GateError(f"FAMILY_INCOMPLETE:{family}:{','.join(missing)}")

    families = {
        family: {c: _mean(class_map[c]) for c in CLASSES}
        for family, class_map in grouped.items()
    }
    return families, prereg, source, dim


def analyze(payload: Any) -> dict[str, Any]:
    families, p, source, dim = _validate_payload(payload)
    family_scale = _family_scale(families)
    global_means = _aggregate_class_means(families)
    geom = _geometry(global_means)
    if not math.isfinite(float(geom["sigma2_over_sigma1"])):
        raise GateError("GLOBAL_GEOMETRY_DEGENERATE")

    observed_norm_sigma2 = float(geom["sigma2"]) / family_scale
    null = _permutation_null(
        families,
        family_scale,
        null_percentile=p["null_percentile"],
        max_exact=p["null_max_exact"],
        sample_count=p["null_sample_count"],
        seed=p["null_seed"],
    )
    null_q = float(null["sigma2_over_family_scale_quantile"])

    loo: list[dict[str, Any]] = []
    for omitted in sorted(families):
        subset = {k: v for k, v in families.items() if k != omitted}
        subset_geom = _geometry(_aggregate_class_means(subset))
        subset_scale = _family_scale(subset)
        loo.append(
            {
                "omitted_family_id": omitted,
                "sigma2_over_sigma1": float(subset_geom["sigma2_over_sigma1"]),
                "sigma2_over_family_scale": float(subset_geom["sigma2"]) / subset_scale,
            }
        )

    rank2_loo_fraction = sum(
        row["sigma2_over_sigma1"] >= p["rank2_min_sigma2_over_sigma1"] for row in loo
    ) / len(loo)
    rank1_loo_fraction = sum(
        row["sigma2_over_sigma1"] <= p["rank1_max_sigma2_over_sigma1"] for row in loo
    ) / len(loo)

    rank2_effect = float(geom["sigma2_over_sigma1"]) >= p["rank2_min_sigma2_over_sigma1"]
    rank2_null = observed_norm_sigma2 >= null_q + p["rank2_min_null_excess"]
    rank2_stable = rank2_loo_fraction >= p["rank2_min_loo_fraction"]

    rank1_effect = float(geom["sigma2_over_sigma1"]) <= p["rank1_max_sigma2_over_sigma1"]
    rank1_null = observed_norm_sigma2 <= null_q + EPS
    rank1_stable = rank1_loo_fraction >= p["rank1_min_loo_fraction"]

    if rank2_effect and rank2_null and rank2_stable:
        decision = "TWO_DIMENSIONAL_REQUIRED"
        rationale = "SECOND_SINGULAR_COMPONENT_EXCEEDS_PREREGISTERED_EFFECT_NULL_AND_LOO_GATES"
    elif rank1_effect and rank1_null and rank1_stable:
        decision = "ONE_DIMENSIONAL_SUPPORTED"
        rationale = "SECOND_COMPONENT_WITHIN_PREREGISTERED_EQUIVALENCE_CEILING_AND_LOO_STABLE"
    else:
        decision = "UNRESOLVED"
        rationale = "NEITHER_RANK1_EQUIVALENCE_NOR_RANK2_PROMOTION_GATE_CLOSED"

    result = {
        "schema": OUTPUT_SCHEMA,
        "input_schema": INPUT_SCHEMA,
        "input_sha256": canonical_sha(payload),
        "source_identity": source,
        "design_scope": {
            "calibration_only": True,
            "fresh_holdout_opened": False,
            "model_executed_by_gate": False,
            "native_cvec_intervention_executed_by_gate": False,
            "label_free_status": "UPSTREAM_DECLARED_AND_FAIL_CLOSED_REQUIRED_NOT_SEMANTICALLY_REAUDITED_BY_THIS_NUMERIC_GATE",
        },
        "vector_dimension": dim,
        "family_count": len(families),
        "family_ids": sorted(families),
        "family_centered_scale": family_scale,
        "global_geometry": {
            **geom,
            "sigma2_over_family_scale": observed_norm_sigma2,
            "class_centroid_sha256": {c: vector_sha(global_means[c]) for c in CLASSES},
        },
        "permutation_null": null,
        "leave_one_family_out": loo,
        "gate_checks": {
            "rank2_effect": rank2_effect,
            "rank2_null_excess": rank2_null,
            "rank2_loo_stable": rank2_stable,
            "rank2_loo_fraction": rank2_loo_fraction,
            "rank1_equivalence_effect": rank1_effect,
            "rank1_no_null_excess": rank1_null,
            "rank1_loo_stable": rank1_stable,
            "rank1_loo_fraction": rank1_loo_fraction,
        },
        "preregistration": p,
        "decision": decision,
        "rationale": rationale,
        "credit_boundary": "NUMERIC_CALIBRATION_ANALYSIS_ONLY_NO_MODEL_RUNTIME_JSPACE_HCU_TRAINING_OR_CANONICAL_SEMANTICS_CREDIT",
    }
    result["result_sha256"] = canonical_sha(result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = analyze(payload)
    except (OSError, json.JSONDecodeError, GateError, ValueError) as exc:
        failure = {
            "schema": OUTPUT_SCHEMA,
            "decision": "UNRESOLVED",
            "fail_closed": True,
            "error": str(exc),
            "credit_boundary": "NO_CREDIT",
        }
        Path(args.output).write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
