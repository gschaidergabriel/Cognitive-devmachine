#!/usr/bin/env python3
"""Blocked matched-triplet rank discriminator for Trigger-1 semantic activations.

No model is run and no holdout is opened. The analyzer consumes calibration-only
activations from matched scenario triplets (AFFIRMATIVE/NEGATIVE/NEUTRAL variants of
the same content skeleton), builds orthonormal Helmert semantic contrasts within each
scenario family, and tests cross-family aligned one-vs-two-dimensional geometry against
a semantic-label permutation null blocked within scenario family.

The decision must agree for raw equal-family aggregation and a family-energy-balanced
aggregation, preventing one high-norm family from silently determining the result.
This is research metrology only: no J-Space/HCU/training/canonical-semantics/product
runtime credit is minted.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import struct
from pathlib import Path
from typing import Any, Iterable

INPUT_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_SEMANTIC_ACTIVATIONS/v1"
OUTPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_RANK_DISCRIMINATOR/v2"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
PERMS = tuple(itertools.permutations(CLASSES))
SQRT6 = math.sqrt(6.0)
SQRT2 = math.sqrt(2.0)


def _sha256_text(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _repo_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def canonical_json_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def vector_sha(vector: list[float]) -> str:
    h = hashlib.sha256()
    for value in vector:
        h.update(struct.pack("<d", float(value)))
    return h.hexdigest()


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]


def scale(a: list[float], s: float) -> list[float]:
    return [x * s for x in a]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(a: list[float]) -> float:
    return math.sqrt(max(0.0, dot(a, a)))


def normalize(a: list[float]) -> list[float] | None:
    n = norm(a)
    if not math.isfinite(n) or n <= 1e-15:
        return None
    return scale(a, 1.0 / n)


def mean(vectors: Iterable[list[float]]) -> list[float]:
    rows = list(vectors)
    if not rows:
        raise ValueError("MEAN_REQUIRES_NONEMPTY_VECTORS")
    d = len(rows[0])
    out = [0.0] * d
    for row in rows:
        if len(row) != d:
            raise ValueError("VECTOR_DIMENSION_MISMATCH")
        for i, value in enumerate(row):
            out[i] += value
    return [value / len(rows) for value in out]


def quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("QUANTILE_REQUIRES_VALUES")
    ordered = sorted(values)
    idx = int(math.ceil(q * len(ordered))) - 1
    return ordered[max(0, min(len(ordered) - 1, idx))]


def _two_row_spectrum(a: list[float], b: list[float]) -> tuple[float, float, float]:
    g11, g22, g12 = dot(a, a), dot(b, b), dot(a, b)
    trace = g11 + g22
    disc = math.sqrt(max(0.0, (g11 - g22) ** 2 + 4.0 * g12 * g12))
    lam1 = max(0.0, 0.5 * (trace + disc))
    lam2 = max(0.0, 0.5 * (trace - disc))
    s1, s2 = math.sqrt(lam1), math.sqrt(lam2)
    return s1, s2, (s2 / s1 if s1 > 1e-15 else 0.0)


def _family_contrasts(rows: dict[str, list[float]]) -> tuple[list[float], list[float]]:
    a, n, u = rows["AFFIRMATIVE"], rows["NEGATIVE"], rows["NEUTRAL"]
    c1 = scale(sub(scale(a, 2.0), add(n, u)), 1.0 / SQRT6)
    c2 = scale(sub(n, u), 1.0 / SQRT2)
    return c1, c2


def aligned_helmert_stats(grouped: dict[str, dict[str, list[float]]], *, family_energy_balance: bool) -> dict[str, Any]:
    family: dict[str, tuple[list[float], list[float]]] = {}
    energies: dict[str, float] = {}
    for family_id, rows in grouped.items():
        c1, c2 = _family_contrasts(rows)
        energy = math.sqrt(dot(c1, c1) + dot(c2, c2))
        if not math.isfinite(energy) or energy <= 1e-15:
            raise ValueError(f"DEGENERATE_MATCHED_TRIPLET:{family_id}")
        energies[family_id] = energy
        if family_energy_balance:
            c1, c2 = scale(c1, 1.0 / energy), scale(c2, 1.0 / energy)
        family[family_id] = (c1, c2)

    c1_bar = mean(pair[0] for pair in family.values())
    c2_bar = mean(pair[1] for pair in family.values())
    sigma1, sigma2, ratio = _two_row_spectrum(c1_bar, c2_bar)
    h1 = normalize(c1_bar)
    h2_raw = c2_bar
    if h1 is not None:
        h2_raw = sub(h2_raw, scale(h1, dot(h2_raw, h1)))
    h2 = normalize(h2_raw)

    h1_cosines: list[float] = []
    h2_cosines: list[float] = []
    for c1, c2 in family.values():
        local_h1 = normalize(c1)
        if local_h1 is not None and h1 is not None:
            h1_cosines.append(dot(h1, local_h1))
        local_h2_raw = c2
        if h1 is not None:
            local_h2_raw = sub(local_h2_raw, scale(h1, dot(local_h2_raw, h1)))
        local_h2 = normalize(local_h2_raw)
        if local_h2 is not None and h2 is not None:
            h2_cosines.append(dot(h2, local_h2))

    return {
        "sigma1": sigma1,
        "sigma2": sigma2,
        "sigma2_over_sigma1": ratio,
        "h1": h1,
        "h2": h2,
        "family_h1_cosine_mean": sum(h1_cosines) / len(h1_cosines) if h1_cosines else None,
        "family_h2_cosine_mean": sum(h2_cosines) / len(h2_cosines) if h2_cosines else None,
        "family_pair_energy_min": min(energies.values()),
        "family_pair_energy_max": max(energies.values()),
    }


def _validate_and_group(payload: dict[str, Any]) -> tuple[dict[str, dict[str, list[float]]], int, list[dict[str, Any]]]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError("INPUT_SCHEMA_MISMATCH")
    if payload.get("model_facing_label_free") is not True:
        raise ValueError("MODEL_FACING_LABEL_FREE_REQUIRED")
    if payload.get("lexically_disjoint_families") is not True:
        raise ValueError("LEXICALLY_DISJOINT_FAMILIES_REQUIRED")
    if payload.get("scenario_family_matched_triplets") is not True:
        raise ValueError("SCENARIO_FAMILY_MATCHED_TRIPLETS_REQUIRED")
    if payload.get("holdout_opened") is not False:
        raise ValueError("HOLDOUT_MUST_REMAIN_UNOPENED")
    if not _repo_sha(payload.get("repo_head")):
        raise ValueError("EXACT_REPO_HEAD_REQUIRED")
    for key in ("checkpoint_sha256", "tokenizer_sha256", "runtime_build_sha256"):
        if not _sha256_text(payload.get(key)):
            raise ValueError(f"{key.upper()}_REQUIRED")
    if not isinstance(payload.get("activation_site"), str) or not payload["activation_site"].strip():
        raise ValueError("ACTIVATION_SITE_REQUIRED")
    if not isinstance(payload.get("layer"), int) or payload["layer"] < 0:
        raise ValueError("NONNEGATIVE_LAYER_REQUIRED")

    records = payload.get("records")
    if not isinstance(records, list) or len(records) < 9:
        raise ValueError("AT_LEAST_THREE_COMPLETE_FAMILIES_REQUIRED")
    grouped: dict[str, dict[str, list[float]]] = {}
    bound_rows: list[dict[str, Any]] = []
    dimension: int | None = None
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("RECORD_OBJECT_REQUIRED")
        if any(key in row for key in ("prompt", "text", "model_facing_text", "semantic_label_token")):
            raise ValueError("MODEL_FACING_TEXT_MUST_NOT_ENTER_RANK_ANALYZER")
        family = row.get("family_id")
        semantic = str(row.get("semantic_class") or "").upper()
        vector = row.get("activation")
        if not isinstance(family, str) or not family.strip():
            raise ValueError("FAMILY_ID_REQUIRED")
        if semantic not in CLASSES:
            raise ValueError("SEMANTIC_CLASS_INVALID")
        if not isinstance(vector, list) or len(vector) < 2:
            raise ValueError("ACTIVATION_VECTOR_REQUIRED")
        try:
            parsed = [float(value) for value in vector]
        except (TypeError, ValueError):
            raise ValueError("ACTIVATION_VECTOR_NUMERIC_REQUIRED") from None
        if not all(math.isfinite(value) for value in parsed):
            raise ValueError("ACTIVATION_VECTOR_FINITE_REQUIRED")
        if dimension is None:
            dimension = len(parsed)
        elif len(parsed) != dimension:
            raise ValueError("VECTOR_DIMENSION_MISMATCH")
        slot = grouped.setdefault(family, {})
        if semantic in slot:
            raise ValueError(f"DUPLICATE_CLASS_WITHIN_FAMILY:{family}:{semantic}")
        slot[semantic] = parsed
        bound_rows.append({"family_id": family, "semantic_class": semantic, "activation_sha256_f64le": vector_sha(parsed)})

    assert dimension is not None
    if len(grouped) < 3:
        raise ValueError("AT_LEAST_THREE_COMPLETE_FAMILIES_REQUIRED")
    for family, rows in grouped.items():
        if set(rows) != set(CLASSES):
            raise ValueError(f"FAMILY_MUST_CONTAIN_EXACTLY_THREE_CLASSES:{family}")
    return grouped, dimension, sorted(bound_rows, key=lambda x: (x["family_id"], x["semantic_class"]))


def _perm_configs(family_ids: list[str], max_null: int, seed_material: str) -> list[tuple[tuple[str, ...], ...]]:
    total = 6 ** len(family_ids)
    identity = tuple(CLASSES)
    if total <= max_null:
        return list(itertools.product(PERMS, repeat=len(family_ids)))
    configs: list[tuple[tuple[str, ...], ...]] = [tuple(identity for _ in family_ids)]
    seen = {configs[0]}
    counter = 0
    while len(configs) < max_null:
        digest = hashlib.sha256(f"{seed_material}:{counter}".encode()).digest()
        counter += 1
        config = tuple(PERMS[digest[i % len(digest)] % len(PERMS)] for i in range(len(family_ids)))
        if config not in seen:
            seen.add(config)
            configs.append(config)
    return configs


def _permuted_grouped(grouped: dict[str, dict[str, list[float]]], family_ids: list[str], config: tuple[tuple[str, ...], ...]) -> dict[str, dict[str, list[float]]]:
    out: dict[str, dict[str, list[float]]] = {}
    for family, perm in zip(family_ids, config):
        original = grouped[family]
        out[family] = {target: original[source] for source, target in zip(CLASSES, perm)}
    return out


def analyze(payload: dict[str, Any], *, rank2_ratio_threshold: float = 0.15, null_q: float = 0.95, max_null: int = 4096) -> dict[str, Any]:
    if not (0.0 < rank2_ratio_threshold < 1.0):
        raise ValueError("RANK2_RATIO_THRESHOLD_RANGE")
    if not (0.5 <= null_q < 1.0):
        raise ValueError("NULL_Q_RANGE")
    if max_null < 32:
        raise ValueError("MAX_NULL_TOO_SMALL")

    grouped, dimension, bound_rows = _validate_and_group(payload)
    family_ids = sorted(grouped)
    raw = aligned_helmert_stats(grouped, family_energy_balance=False)
    balanced = aligned_helmert_stats(grouped, family_energy_balance=True)

    seed_material = canonical_json_sha({
        "repo_head": payload["repo_head"],
        "checkpoint_sha256": payload["checkpoint_sha256"],
        "activation_site": payload["activation_site"],
        "layer": payload["layer"],
        "rows": bound_rows,
    })
    configs = _perm_configs(family_ids, max_null, seed_material)
    identity_config = tuple(tuple(CLASSES) for _ in family_ids)
    null_raw_s1: list[float] = []
    null_raw_s2: list[float] = []
    null_bal_s1: list[float] = []
    null_bal_s2: list[float] = []
    for config in configs:
        if config == identity_config:
            continue
        permuted = _permuted_grouped(grouped, family_ids, config)
        nr = aligned_helmert_stats(permuted, family_energy_balance=False)
        nb = aligned_helmert_stats(permuted, family_energy_balance=True)
        null_raw_s1.append(float(nr["sigma1"]))
        null_raw_s2.append(float(nr["sigma2"]))
        null_bal_s1.append(float(nb["sigma1"]))
        null_bal_s2.append(float(nb["sigma2"]))
    if not null_raw_s1:
        raise ValueError("NULL_PERMUTATION_SET_EMPTY")

    loo_raw: list[float] = []
    loo_bal: list[float] = []
    for held_out in family_ids:
        subset = {f: rows for f, rows in grouped.items() if f != held_out}
        loo_raw.append(float(aligned_helmert_stats(subset, family_energy_balance=False)["sigma2_over_sigma1"]))
        loo_bal.append(float(aligned_helmert_stats(subset, family_energy_balance=True)["sigma2_over_sigma1"]))

    q = {
        "raw_sigma1": quantile(null_raw_s1, null_q),
        "raw_sigma2": quantile(null_raw_s2, null_q),
        "balanced_sigma1": quantile(null_bal_s1, null_q),
        "balanced_sigma2": quantile(null_bal_s2, null_q),
    }
    rank1_signal = float(raw["sigma1"]) > q["raw_sigma1"] and float(balanced["sigma1"]) > q["balanced_sigma1"]
    rank2_signal = (
        float(raw["sigma2"]) > q["raw_sigma2"]
        and float(balanced["sigma2"]) > q["balanced_sigma2"]
        and float(raw["sigma2_over_sigma1"]) >= rank2_ratio_threshold
        and float(balanced["sigma2_over_sigma1"]) >= rank2_ratio_threshold
    )
    rank1_no_second = (
        float(raw["sigma2"]) <= q["raw_sigma2"]
        and float(balanced["sigma2"]) <= q["balanced_sigma2"]
        and float(raw["sigma2_over_sigma1"]) < rank2_ratio_threshold
        and float(balanced["sigma2_over_sigma1"]) < rank2_ratio_threshold
    )
    loo_rank2 = min(loo_raw) >= rank2_ratio_threshold * 0.5 and min(loo_bal) >= rank2_ratio_threshold * 0.5
    loo_rank1 = max(loo_raw) < rank2_ratio_threshold and max(loo_bal) < rank2_ratio_threshold
    h1_coherent = raw["family_h1_cosine_mean"] is not None and float(raw["family_h1_cosine_mean"]) > 0.0
    h2_coherent = raw["family_h2_cosine_mean"] is not None and float(raw["family_h2_cosine_mean"]) > 0.0

    if rank1_signal and rank2_signal and loo_rank2 and h1_coherent and h2_coherent:
        verdict = "TWO_DIMENSIONAL_REQUIRED"
    elif rank1_signal and rank1_no_second and loo_rank1 and h1_coherent:
        verdict = "ONE_DIMENSIONAL_SUPPORTED"
    else:
        verdict = "UNRESOLVED"

    output = {
        "schema": OUTPUT_SCHEMA,
        "verdict": verdict,
        "credit_effect": "RESEARCH_METROLOGY_ONLY_NO_RUNTIME_OR_PROMOTION_CREDIT",
        "input_identity": {
            "repo_head": payload["repo_head"],
            "checkpoint_sha256": payload["checkpoint_sha256"],
            "tokenizer_sha256": payload["tokenizer_sha256"],
            "runtime_build_sha256": payload["runtime_build_sha256"],
            "activation_site": payload["activation_site"],
            "layer": payload["layer"],
            "family_count": len(family_ids),
            "activation_dimension": dimension,
            "calibration_only": True,
            "holdout_opened": False,
            "model_facing_label_free": True,
            "scenario_family_matched_triplets": True,
            "blocked_permutation_within_scenario_family": True,
            "bound_rows_sha256": canonical_json_sha(bound_rows),
        },
        "observed_geometry": {
            "raw_equal_family": {k: v for k, v in raw.items() if k not in {"h1", "h2"}},
            "family_energy_balanced": {k: v for k, v in balanced.items() if k not in {"h1", "h2"}},
            "leave_one_family_out_raw_sigma2_over_sigma1": loo_raw,
            "leave_one_family_out_balanced_sigma2_over_sigma1": loo_bal,
        },
        "blocked_permutation_null": {
            "quantile": null_q,
            "configurations_evaluated": len(null_raw_s1),
            **q,
            "deterministic_seed_material_sha256": seed_material,
        },
        "decision_rule": {
            "rank2_ratio_threshold": rank2_ratio_threshold,
            "raw_and_balanced_rank1_signal_above_null": rank1_signal,
            "raw_and_balanced_rank2_signal_above_null": rank2_signal,
            "raw_and_balanced_rank1_no_second_dimension": rank1_no_second,
            "leave_one_family_out_rank2_stable": loo_rank2,
            "leave_one_family_out_rank1_stable": loo_rank1,
            "h1_direction_coherent": h1_coherent,
            "h2_direction_coherent": h2_coherent,
        },
        "promotion_boundary": "A blocked matched-triplet rank verdict is representation metrology only. Fresh-holdout native class-selective causal transport, sign, nuisance, output-realization, token-scope and off-target controls remain mandatory.",
    }
    output["analysis_sha256"] = canonical_json_sha(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--rank2-ratio-threshold", type=float, default=0.15)
    parser.add_argument("--null-q", type=float, default=0.95)
    parser.add_argument("--max-null", type=int, default=4096)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze(payload, rank2_ratio_threshold=args.rank2_ratio_threshold, null_q=args.null_q, max_null=args.max_null)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
