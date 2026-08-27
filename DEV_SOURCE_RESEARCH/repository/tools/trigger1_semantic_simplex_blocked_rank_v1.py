#!/usr/bin/env python3
"""Deterministic matched-triplet blocked semantic-simplex rank analyzer.

Consumes already-captured activation vectors only. It does not execute a model or apply
control vectors. It estimates whether three semantic states have a stable one- or
two-dimensional cross-family geometry after within-scenario centering and compares that
geometry with a null that permutes semantic labels inside each matched scenario family.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_IN = "CLAY_TRIGGER1_MATCHED_TRIPLET_ACTIVATIONS/v1"
SCHEMA_OUT = "CLAY_TRIGGER1_BLOCKED_SEMANTIC_SIMPLEX_RANK/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
DEFAULT_CODES = ("A", "B", "C")


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _as_vector(value: Any, dim: int, label: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != 1 or arr.shape[0] != dim:
        raise ValueError(f"{label}:VECTOR_DIMENSION_MISMATCH:{arr.shape}:{dim}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{label}:VECTOR_NONFINITE")
    return arr


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na <= 1e-12 or nb <= 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _quantile(values: list[float], q: float) -> float:
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


def validate_packet(packet: dict[str, Any]) -> tuple[int, list[dict[str, Any]], dict[str, Any]]:
    if packet.get("schema") != SCHEMA_IN:
        raise ValueError("INPUT_SCHEMA_INVALID")
    dim = packet.get("embedding_dim")
    if not isinstance(dim, int) or dim < 2:
        raise ValueError("EMBEDDING_DIM_INVALID")
    families = packet.get("families")
    if not isinstance(families, list) or len(families) < 3:
        raise ValueError("AT_LEAST_THREE_MATCHED_FAMILIES_REQUIRED")

    family_ids: set[str] = set()
    split_ids: set[str] = set()
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
        activations = fam.get("activations")
        if not isinstance(activations, dict) or {str(k).upper() for k in activations} != set(CLASSES):
            raise ValueError(f"MATCHED_TRIPLET_REQUIRED:{family_id}")
        vecs = {
            semantic: _as_vector(
                next(v for k, v in activations.items() if str(k).upper() == semantic), dim, f"{family_id}:{semantic}"
            )
            for semantic in CLASSES
        }
        normalized.append({"family_id": family_id, "split": split, "vectors": vecs, "code_map": fam.get("code_map")})

    code_ok, code_counts = _balanced_code_maps(families)
    if not code_ok:
        raise ValueError(f"OUTPUT_CODE_MAPPING_NOT_COUNTERBALANCED:{code_counts}")
    return dim, normalized, {"code_counts": code_counts, "splits": sorted(split_ids)}


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
    h1 = pooled_a / np.linalg.norm(pooled_a) if np.linalg.norm(pooled_a) > 1e-12 else np.zeros_like(pooled_a)
    b_perp = pooled_b - np.dot(pooled_b, h1) * h1
    h2 = b_perp / np.linalg.norm(b_perp) if np.linalg.norm(b_perp) > 1e-12 else np.zeros_like(b_perp)
    a_cos = [_cosine(row, pooled_a) for row in a_rows]
    b_cos = [_cosine(row - np.dot(row, h1) * h1, b_perp) for row in b_rows]
    return {
        "singular_values": [s1, s2],
        "sigma2_over_sigma1": s2 / s1 if s1 > 1e-12 else 0.0,
        "h1": h1,
        "h2": h2,
        "mean_a_coherence": float(np.mean(a_cos)),
        "mean_b_perp_coherence": float(np.mean(b_cos)),
    }


def blocked_null(families: list[dict[str, Any]], *, permutations: int, seed_material: str) -> dict[str, Any]:
    rng = random.Random(int(seed_material[:16], 16))
    s1_values: list[float] = []
    s2_values: list[float] = []
    labels = list(CLASSES)
    for _ in range(permutations):
        permuted: list[dict[str, Any]] = []
        for fam in families:
            shuffled = labels.copy()
            rng.shuffle(shuffled)
            remapped = {target: fam["vectors"][source] for target, source in zip(CLASSES, shuffled)}
            permuted.append({**fam, "vectors": remapped})
        s1, s2 = family_geometry(permuted)["singular_values"]
        s1_values.append(float(s1))
        s2_values.append(float(s2))
    return {
        "sigma1_q95": _quantile(s1_values, 0.95),
        "sigma2_q95": _quantile(s2_values, 0.95),
        "sigma1_values": s1_values,
        "sigma2_values": s2_values,
    }


def empirical_p(null_values: list[float], observed: float) -> float:
    return (1.0 + sum(value >= observed for value in null_values)) / (1.0 + len(null_values))


def analyze(packet: dict[str, Any], *, permutations: int = 2048, alpha: float = 0.05, coherence_min: float = 0.5) -> dict[str, Any]:
    if permutations < 32:
        raise ValueError("PERMUTATIONS_TOO_SMALL")
    dim, families, validation = validate_packet(packet)
    geom = family_geometry(families)
    seed_material = canonical_sha({"schema": SCHEMA_OUT, "input_sha256": canonical_sha(packet), "permutations": permutations})
    null = blocked_null(families, permutations=permutations, seed_material=seed_material)
    s1, s2 = geom["singular_values"]
    p1, p2 = empirical_p(null["sigma1_values"], s1), empirical_p(null["sigma2_values"], s2)
    first = p1 <= alpha and geom["mean_a_coherence"] >= coherence_min
    second = p2 <= alpha and geom["mean_b_perp_coherence"] >= coherence_min
    decision = "TWO_DIMENSIONAL_REQUIRED" if first and second else ("ONE_DIMENSIONAL_SUPPORTED" if first else "UNRESOLVED")

    family_rows = []
    for fam in families:
        v = fam["vectors"]
        center = (v["AFFIRMATIVE"] + v["NEGATIVE"] + v["NEUTRAL"]) / 3.0
        family_rows.append({
            "family_id": fam["family_id"],
            "split": fam["split"],
            "center_sha256": hashlib.sha256(center.astype("<f8").tobytes()).hexdigest(),
            "class_vector_sha256": {s: hashlib.sha256(v[s].astype("<f8").tobytes()).hexdigest() for s in CLASSES},
        })

    result = {
        "schema": SCHEMA_OUT,
        "input_sha256": canonical_sha(packet),
        "embedding_dim": dim,
        "family_count": len(families),
        "validation": validation,
        "blocked_permutation": {
            "mode": "SEMANTIC_LABELS_PERMUTED_WITHIN_SCENARIO_FAMILY_ONLY",
            "permutations": permutations,
            "seed_sha256": seed_material,
            "alpha": alpha,
            "sigma1_q95": null["sigma1_q95"],
            "sigma2_q95": null["sigma2_q95"],
        },
        "observed": {
            "sigma1": s1,
            "sigma2": s2,
            "sigma2_over_sigma1": geom["sigma2_over_sigma1"],
            "sigma1_empirical_p": p1,
            "sigma2_empirical_p": p2,
            "mean_affirmative_vs_rest_family_coherence": geom["mean_a_coherence"],
            "mean_negative_vs_neutral_perp_family_coherence": geom["mean_b_perp_coherence"],
            "h1_sha256": hashlib.sha256(geom["h1"].astype("<f8").tobytes()).hexdigest(),
            "h2_sha256": hashlib.sha256(geom["h2"].astype("<f8").tobytes()).hexdigest(),
        },
        "decision": decision,
        "promotion_candidate": False,
        "native_intervention_executed": False,
        "jspace_model_runtime_credit": 0,
        "hcu_full_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
        "training_credit": 0,
        "canonical_semantics_promotion": False,
        "family_receipts": family_rows,
        "next_gate": "Freeze the selected basis on calibration only, then run a matched class-direction-by-requested-target native cvec causal matrix on unopened scenario families with sign/null/orthogonal/permuted/label-only nuisance controls and norm/token-scope binding.",
        "evidence_boundary": "Blocked rank is representation-geometry evidence from existing activations only; it is not native cvec causal evidence or canonical semantic truth.",
    }
    result["result_sha256"] = canonical_sha(result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output")
    ap.add_argument("--permutations", type=int, default=2048)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--coherence-min", type=float, default=0.5)
    args = ap.parse_args()
    packet = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise SystemExit("INPUT_OBJECT_REQUIRED")
    result = analyze(packet, permutations=args.permutations, alpha=args.alpha, coherence_min=args.coherence_min)
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
