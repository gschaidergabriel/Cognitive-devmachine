#!/usr/bin/env python3
"""Deterministic matched-triplet blocked semantic-simplex rank analyzer.

Consumes already-captured BASIS/CALIBRATION activations only. It never executes a model,
opens fresh holdout, or applies a control vector. The analyzer asks whether three semantic
states have a stable one- or two-dimensional cross-family geometry after within-scenario
centering, using a semantic-label permutation null blocked inside scenario family.

Rank-1 is an equivalence-style claim: failure to detect rank-2 is not sufficient. A rank-1
result additionally requires a preregistered small-secondary-component ceiling and
leave-one-family-out stability. All results remain representation-geometry measurements;
no canonical semantics, J-Space runtime, HCU, EntityOS, or training credit is minted.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_IN = "CLAY_TRIGGER1_MATCHED_TRIPLET_ACTIVATIONS/v1"
SCHEMA_OUT = "CLAY_TRIGGER1_BLOCKED_SEMANTIC_SIMPLEX_RANK/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
DEFAULT_CODES = ("A", "B", "C")
TOKEN_SCOPES = {"LAST_TOKEN_ONLY", "ALL_PROMPT_TOKENS"}
PERMS = tuple(itertools.permutations(CLASSES))
EPS = 1e-12


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def vector_sha(vector: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vector, dtype="<f8").tobytes()).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _git_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _as_vector(value: Any, dim: int, label: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != 1 or arr.shape[0] != dim:
        raise ValueError(f"{label}:VECTOR_DIMENSION_MISMATCH:{arr.shape}:{dim}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{label}:VECTOR_NONFINITE")
    return arr


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na <= EPS or nb <= EPS:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("EMPTY_NULL_DISTRIBUTION")
    return float(np.quantile(np.asarray(values, dtype=np.float64), q, method="higher"))


def _balanced_code_maps(families: list[dict[str, Any]]) -> tuple[bool, dict[str, dict[str, int]]]:
    counts = {semantic: {code: 0 for code in DEFAULT_CODES} for semantic in CLASSES}
    for fam in families:
        mapping = fam.get("code_map")
        if not isinstance(mapping, dict):
            return False, counts
        normalized = {str(k).upper(): str(v).upper() for k, v in mapping.items()}
        if set(normalized) != set(CLASSES) or set(normalized.values()) != set(DEFAULT_CODES):
            return False, counts
        for semantic in CLASSES:
            counts[semantic][normalized[semantic]] += 1
    return all(max(v.values()) - min(v.values()) <= 1 for v in counts.values()), counts


def _validate_source_identity(packet: dict[str, Any], dim: int) -> dict[str, Any]:
    source = packet.get("source_identity")
    if not isinstance(source, dict):
        raise ValueError("SOURCE_IDENTITY_REQUIRED")
    if not _git_sha(source.get("repo_head")):
        raise ValueError("SOURCE_REPO_HEAD_REQUIRED")
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        if not _sha256(source.get(key)):
            raise ValueError(f"SOURCE_{key.upper()}_REQUIRED")
    if not isinstance(source.get("model_or_route"), str) or not source["model_or_route"].strip():
        raise ValueError("SOURCE_MODEL_OR_ROUTE_REQUIRED")
    if not isinstance(source.get("activation_site"), str) or not source["activation_site"].strip():
        raise ValueError("SOURCE_ACTIVATION_SITE_REQUIRED")
    if source.get("token_scope") not in TOKEN_SCOPES:
        raise ValueError("SOURCE_TOKEN_SCOPE_REQUIRED")
    if not isinstance(source.get("layer"), int) or isinstance(source.get("layer"), bool) or source["layer"] < 0:
        raise ValueError("SOURCE_LAYER_REQUIRED")
    if source.get("embedding_dim") != dim:
        raise ValueError("SOURCE_EMBEDDING_DIM_MISMATCH")
    return source


def _validate_attestation(packet: dict[str, Any]) -> dict[str, Any]:
    att = packet.get("design_attestation")
    if not isinstance(att, dict):
        raise ValueError("DESIGN_ATTESTATION_REQUIRED")
    required_true = (
        "calibration_only",
        "model_facing_label_free",
        "lexically_disjoint_families",
        "matched_scenario_triplets",
        "output_code_independent",
    )
    for key in required_true:
        if att.get(key) is not True:
            raise ValueError(f"DESIGN_ATTESTATION_REQUIRED:{key}")
    if att.get("fresh_holdout_opened") is not False:
        raise ValueError("FRESH_HOLDOUT_MUST_REMAIN_CLOSED")
    return att


def _validate_preregistration(packet: dict[str, Any]) -> dict[str, Any]:
    p = packet.get("preregistration")
    if not isinstance(p, dict):
        raise ValueError("PREREGISTRATION_REQUIRED")
    required = (
        "permutations",
        "alpha",
        "coherence_min",
        "rank1_max_sigma2_over_sigma1",
        "rank2_min_sigma2_over_sigma1",
        "rank1_min_loo_fraction",
        "rank2_min_loo_fraction",
    )
    missing = [key for key in required if key not in p]
    if missing:
        raise ValueError("PREREGISTRATION_MISSING:" + ",".join(missing))
    permutations = p["permutations"]
    if not isinstance(permutations, int) or isinstance(permutations, bool) or permutations < 32:
        raise ValueError("PREREGISTRATION_PERMUTATIONS_INVALID")
    for key in ("alpha", "coherence_min", "rank1_max_sigma2_over_sigma1", "rank2_min_sigma2_over_sigma1", "rank1_min_loo_fraction", "rank2_min_loo_fraction"):
        if not _finite_number(p[key]):
            raise ValueError(f"PREREGISTRATION_NUMBER_INVALID:{key}")
    alpha = float(p["alpha"])
    coherence = float(p["coherence_min"])
    rank1_max = float(p["rank1_max_sigma2_over_sigma1"])
    rank2_min = float(p["rank2_min_sigma2_over_sigma1"])
    rank1_loo = float(p["rank1_min_loo_fraction"])
    rank2_loo = float(p["rank2_min_loo_fraction"])
    if not (0.0 < alpha < 0.5):
        raise ValueError("PREREGISTRATION_ALPHA_INVALID")
    if not (-1.0 <= coherence <= 1.0):
        raise ValueError("PREREGISTRATION_COHERENCE_INVALID")
    if not (0.0 <= rank1_max < rank2_min <= 1.0):
        raise ValueError("PREREGISTRATION_RANK_THRESHOLDS_INVALID")
    if not (0.0 < rank1_loo <= 1.0 and 0.0 < rank2_loo <= 1.0):
        raise ValueError("PREREGISTRATION_LOO_FRACTIONS_INVALID")
    return {
        "permutations": permutations,
        "alpha": alpha,
        "coherence_min": coherence,
        "rank1_max_sigma2_over_sigma1": rank1_max,
        "rank2_min_sigma2_over_sigma1": rank2_min,
        "rank1_min_loo_fraction": rank1_loo,
        "rank2_min_loo_fraction": rank2_loo,
    }


def validate_packet(packet: dict[str, Any]) -> tuple[int, list[dict[str, Any]], dict[str, Any]]:
    if packet.get("schema") != SCHEMA_IN:
        raise ValueError("INPUT_SCHEMA_INVALID")
    dim = packet.get("embedding_dim")
    if not isinstance(dim, int) or isinstance(dim, bool) or dim < 2:
        raise ValueError("EMBEDDING_DIM_INVALID")
    source = _validate_source_identity(packet, dim)
    attestation = _validate_attestation(packet)
    prereg = _validate_preregistration(packet)
    families = packet.get("families")
    if not isinstance(families, list) or len(families) < 3:
        raise ValueError("AT_LEAST_THREE_MATCHED_FAMILIES_REQUIRED")

    family_ids: set[str] = set()
    split_ids: set[str] = set()
    prompt_hashes: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, fam in enumerate(families):
        if not isinstance(fam, dict):
            raise ValueError(f"FAMILY_OBJECT_REQUIRED:{index}")
        family_id = str(fam.get("family_id") or "").strip()
        split = str(fam.get("split") or "").strip().upper()
        if not family_id or family_id in family_ids:
            raise ValueError(f"FAMILY_ID_INVALID_OR_DUPLICATE:{family_id}")
        if split not in {"BASIS", "CALIBRATION"}:
            raise ValueError(f"FRESH_HOLDOUT_MUST_NOT_BE_OPENED_BY_RANK_ANALYZER:{split}")
        family_ids.add(family_id)
        split_ids.add(split)

        prompt_map = fam.get("prompt_sha256")
        if not isinstance(prompt_map, dict) or {str(k).upper() for k in prompt_map} != set(CLASSES):
            raise ValueError(f"PROMPT_HASH_TRIPLET_REQUIRED:{family_id}")
        normalized_prompt_map: dict[str, str] = {}
        for semantic in CLASSES:
            prompt_sha = next(v for k, v in prompt_map.items() if str(k).upper() == semantic)
            if not _sha256(prompt_sha):
                raise ValueError(f"PROMPT_HASH_INVALID:{family_id}:{semantic}")
            if prompt_sha in prompt_hashes:
                raise ValueError(f"PROMPT_HASH_REUSE_FORBIDDEN:{prompt_sha}")
            prompt_hashes.add(prompt_sha)
            normalized_prompt_map[semantic] = prompt_sha

        receipt = fam.get("source_receipt_sha256")
        if not _sha256(receipt):
            raise ValueError(f"SOURCE_RECEIPT_REQUIRED:{family_id}")
        activations = fam.get("activations")
        if not isinstance(activations, dict) or {str(k).upper() for k in activations} != set(CLASSES):
            raise ValueError(f"MATCHED_TRIPLET_REQUIRED:{family_id}")
        vecs = {
            semantic: _as_vector(
                next(v for k, v in activations.items() if str(k).upper() == semantic), dim, f"{family_id}:{semantic}"
            )
            for semantic in CLASSES
        }
        normalized.append({
            "family_id": family_id,
            "split": split,
            "vectors": vecs,
            "code_map": fam.get("code_map"),
            "prompt_sha256": normalized_prompt_map,
            "source_receipt_sha256": receipt,
        })

    code_ok, code_counts = _balanced_code_maps(families)
    if not code_ok:
        raise ValueError(f"OUTPUT_CODE_MAPPING_NOT_COUNTERBALANCED:{code_counts}")
    validation = {
        "code_counts": code_counts,
        "splits": sorted(split_ids),
        "source_identity_sha256": canonical_sha(source),
        "design_attestation_sha256": canonical_sha(attestation),
        "preregistration": prereg,
        "preregistration_sha256": canonical_sha(prereg),
        "prompt_hash_count": len(prompt_hashes),
    }
    return dim, normalized, validation


def family_geometry(families: list[dict[str, Any]]) -> dict[str, Any]:
    centered_by_family: list[dict[str, np.ndarray]] = []
    a_rows: list[np.ndarray] = []
    b_rows: list[np.ndarray] = []
    for fam in families:
        v = fam["vectors"]
        center = (v["AFFIRMATIVE"] + v["NEGATIVE"] + v["NEUTRAL"]) / 3.0
        centered_by_family.append({semantic: v[semantic] - center for semantic in CLASSES})
        a_rows.append(v["AFFIRMATIVE"] - 0.5 * (v["NEGATIVE"] + v["NEUTRAL"]))
        b_rows.append(v["NEGATIVE"] - v["NEUTRAL"])

    class_means = {
        semantic: np.mean(np.stack([row[semantic] for row in centered_by_family], axis=0), axis=0)
        for semantic in CLASSES
    }
    singular = np.linalg.svd(np.stack([class_means[s] for s in CLASSES], axis=0), compute_uv=False)
    s1 = float(singular[0]) if len(singular) > 0 else 0.0
    s2 = float(singular[1]) if len(singular) > 1 else 0.0
    pooled_a = np.mean(np.stack(a_rows, axis=0), axis=0)
    pooled_b = np.mean(np.stack(b_rows, axis=0), axis=0)
    h1 = pooled_a / np.linalg.norm(pooled_a) if np.linalg.norm(pooled_a) > EPS else np.zeros_like(pooled_a)
    b_perp = pooled_b - np.dot(pooled_b, h1) * h1
    h2 = b_perp / np.linalg.norm(b_perp) if np.linalg.norm(b_perp) > EPS else np.zeros_like(b_perp)
    a_cos = [_cosine(row, pooled_a) for row in a_rows]
    b_cos = [_cosine(row - np.dot(row, h1) * h1, b_perp) for row in b_rows]
    return {
        "singular_values": [s1, s2],
        "sigma2_over_sigma1": s2 / s1 if s1 > EPS else 0.0,
        "h1": h1,
        "h2": h2,
        "mean_a_coherence": float(np.mean(a_cos)),
        "mean_b_perp_coherence": float(np.mean(b_cos)),
    }


def _permutation_choices(family_count: int, requested: int, seed_material: str) -> tuple[str, list[tuple[int, ...]]]:
    movable = family_count - 1
    total_nonidentity = 6 ** movable - 1
    if total_nonidentity <= 0:
        raise ValueError("NULL_REQUIRES_AT_LEAST_TWO_FAMILIES")
    if total_nonidentity <= requested:
        choices = [x for x in itertools.product(range(6), repeat=movable) if any(i != 0 for i in x)]
        return "EXACT_BLOCKED", choices
    rng = random.Random(int(seed_material[:16], 16))
    seen: set[tuple[int, ...]] = set()
    while len(seen) < requested:
        choice = tuple(rng.randrange(6) for _ in range(movable))
        if any(i != 0 for i in choice):
            seen.add(choice)
    return "DETERMINISTIC_SAMPLED_BLOCKED", sorted(seen)


def blocked_null(families: list[dict[str, Any]], *, permutations: int, seed_material: str) -> dict[str, Any]:
    ids = sorted(range(len(families)), key=lambda i: families[i]["family_id"])
    ordered = [families[i] for i in ids]
    mode, choices = _permutation_choices(len(ordered), permutations, seed_material)
    s1_values: list[float] = []
    s2_values: list[float] = []
    for choice in choices:
        permuted: list[dict[str, Any]] = [ordered[0]]
        for fam, perm_index in zip(ordered[1:], choice):
            perm = PERMS[perm_index]
            remapped = {target: fam["vectors"][source] for target, source in zip(CLASSES, perm)}
            permuted.append({**fam, "vectors": remapped})
        s1, s2 = family_geometry(permuted)["singular_values"]
        s1_values.append(float(s1))
        s2_values.append(float(s2))
    return {
        "mode": mode,
        "anchored_family_id": ordered[0]["family_id"],
        "global_label_symmetry_removed": True,
        "samples": len(choices),
        "sigma1_q95": _quantile(s1_values, 0.95),
        "sigma2_q95": _quantile(s2_values, 0.95),
        "sigma1_values": s1_values,
        "sigma2_values": s2_values,
        "null_values_sha256": canonical_sha({"sigma1": s1_values, "sigma2": s2_values}),
    }


def empirical_p(null_values: list[float], observed: float) -> float:
    return (1.0 + sum(value >= observed for value in null_values)) / (1.0 + len(null_values))


def _loo_ratios(families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for held_out in sorted(fam["family_id"] for fam in families):
        subset = [fam for fam in families if fam["family_id"] != held_out]
        geom = family_geometry(subset)
        rows.append({"held_out_family_id": held_out, "sigma2_over_sigma1": geom["sigma2_over_sigma1"]})
    return rows


def analyze(packet: dict[str, Any]) -> dict[str, Any]:
    dim, families, validation = validate_packet(packet)
    p = validation["preregistration"]
    geom = family_geometry(families)
    seed_material = canonical_sha({
        "schema": SCHEMA_OUT,
        "input_sha256": canonical_sha(packet),
        "preregistration_sha256": validation["preregistration_sha256"],
    })
    null = blocked_null(families, permutations=p["permutations"], seed_material=seed_material)
    s1, s2 = geom["singular_values"]
    p1 = empirical_p(null["sigma1_values"], s1)
    p2 = empirical_p(null["sigma2_values"], s2)
    ratio = geom["sigma2_over_sigma1"]
    loo = _loo_ratios(families)
    rank1_loo_fraction = sum(row["sigma2_over_sigma1"] <= p["rank1_max_sigma2_over_sigma1"] for row in loo) / len(loo)
    rank2_loo_fraction = sum(row["sigma2_over_sigma1"] >= p["rank2_min_sigma2_over_sigma1"] for row in loo) / len(loo)

    first = p1 <= p["alpha"] and geom["mean_a_coherence"] >= p["coherence_min"]
    rank2 = (
        first
        and p2 <= p["alpha"]
        and ratio >= p["rank2_min_sigma2_over_sigma1"]
        and geom["mean_b_perp_coherence"] >= p["coherence_min"]
        and rank2_loo_fraction >= p["rank2_min_loo_fraction"]
    )
    rank1 = (
        first
        and p2 > p["alpha"]
        and ratio <= p["rank1_max_sigma2_over_sigma1"]
        and rank1_loo_fraction >= p["rank1_min_loo_fraction"]
    )
    decision = "TWO_DIMENSIONAL_REQUIRED" if rank2 else ("ONE_DIMENSIONAL_SUPPORTED" if rank1 else "UNRESOLVED")

    family_rows = []
    for fam in sorted(families, key=lambda row: row["family_id"]):
        v = fam["vectors"]
        center = (v["AFFIRMATIVE"] + v["NEGATIVE"] + v["NEUTRAL"]) / 3.0
        family_rows.append({
            "family_id": fam["family_id"],
            "split": fam["split"],
            "prompt_sha256": fam["prompt_sha256"],
            "source_receipt_sha256": fam["source_receipt_sha256"],
            "center_sha256": vector_sha(center),
            "class_vector_sha256": {semantic: vector_sha(v[semantic]) for semantic in CLASSES},
        })

    basis_dim = 2 if decision == "TWO_DIMENSIONAL_REQUIRED" else (1 if decision == "ONE_DIMENSIONAL_SUPPORTED" else 0)
    result = {
        "schema": SCHEMA_OUT,
        "input_sha256": canonical_sha(packet),
        "source_identity": packet["source_identity"],
        "source_identity_sha256": validation["source_identity_sha256"],
        "design_attestation_sha256": validation["design_attestation_sha256"],
        "preregistration": p,
        "preregistration_sha256": validation["preregistration_sha256"],
        "embedding_dim": dim,
        "family_count": len(families),
        "validation": {k: v for k, v in validation.items() if k != "preregistration"},
        "blocked_permutation": {
            "mode": null["mode"],
            "anchored_family_id": null["anchored_family_id"],
            "global_label_symmetry_removed": True,
            "samples": null["samples"],
            "seed_sha256": seed_material,
            "alpha": p["alpha"],
            "sigma1_q95": null["sigma1_q95"],
            "sigma2_q95": null["sigma2_q95"],
            "null_values_sha256": null["null_values_sha256"],
        },
        "observed": {
            "sigma1": s1,
            "sigma2": s2,
            "sigma2_over_sigma1": ratio,
            "sigma1_empirical_p": p1,
            "sigma2_empirical_p": p2,
            "mean_affirmative_vs_rest_family_coherence": geom["mean_a_coherence"],
            "mean_negative_vs_neutral_perp_family_coherence": geom["mean_b_perp_coherence"],
            "rank1_loo_fraction": rank1_loo_fraction,
            "rank2_loo_fraction": rank2_loo_fraction,
            "loo_ratios": loo,
            "h1_sha256": vector_sha(geom["h1"]),
            "h2_sha256": vector_sha(geom["h2"]),
        },
        "decision": decision,
        "selected_basis_dimension": basis_dim,
        "promotion_candidate": False,
        "native_intervention_executed": False,
        "jspace_model_runtime_credit": 0,
        "hcu_full_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
        "training_credit": 0,
        "canonical_semantics_promotion": False,
        "family_receipts": family_rows,
        "next_gate": "Freeze the selected basis and magnitude envelope on calibration only, then run a matched class-direction-by-requested-target native cvec causal matrix on unopened scenario families with sign/null/orthogonal/permuted/label-only nuisance controls, context-bound output-code measurement and explicit native token-scope binding.",
        "evidence_boundary": "Blocked rank is exact-provenance representation-geometry evidence from existing BASIS/CALIBRATION activations only; it is not native cvec causal evidence or canonical semantic truth.",
    }
    result["result_sha256"] = canonical_sha(result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    packet = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise SystemExit("INPUT_OBJECT_REQUIRED")
    result = analyze(packet)
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
