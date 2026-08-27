#!/usr/bin/env python3
"""Deterministic calibration-only semantic-simplex rank discriminator for Trigger-1.

No model is run and no holdout is opened. Matched scenario-family activation triads
(AFFIRMATIVE/NEGATIVE/NEUTRAL) are reduced to the established primary contrast
A - 0.5*(N+U) and the orthogonal N-U contrast. The existing within-family N<->U
sign-flip null is retained.

Promotion now also requires the same rank classification after scaling each family's
contrast pair together by inverse pair energy. This preserves each family's internal
axis ratio while preventing a single high-energy family from dominating cross-family
rank metrology. Raw and family-energy-balanced disagreement fails closed as UNRESOLVED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

INPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION_ACTIVATIONS/v1"
OUTPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_RANK_ANALYSIS/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _as_finite_vector(value: Any, *, name: str, dimension: int | None) -> np.ndarray:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name}:NONEMPTY_VECTOR_REQUIRED")
    try:
        arr = np.asarray(value, dtype=np.float64)
    except Exception as exc:
        raise ValueError(f"{name}:NUMERIC_VECTOR_REQUIRED") from exc
    if arr.ndim != 1:
        raise ValueError(f"{name}:VECTOR_MUST_BE_1D")
    if dimension is not None and arr.size != dimension:
        raise ValueError(f"{name}:DIMENSION_MISMATCH:{arr.size}!={dimension}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name}:NONFINITE_VECTOR")
    return arr


def _validate_config(config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ValueError("decision_config:OBJECT_REQUIRED")
    required = (
        "alpha", "rank1_equivalence_max_ratio", "rank2_min_ratio",
        "rank2_min_lofo_cosine", "min_matched_families",
        "max_exact_signflip_families", "monte_carlo_signflips",
    )
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"decision_config:MISSING:{','.join(missing)}")
    alpha = float(config["alpha"])
    r1 = float(config["rank1_equivalence_max_ratio"])
    r2 = float(config["rank2_min_ratio"])
    cosine = float(config["rank2_min_lofo_cosine"])
    min_families = int(config["min_matched_families"])
    max_exact = int(config["max_exact_signflip_families"])
    mc = int(config["monte_carlo_signflips"])
    if not (0.0 < alpha < 1.0):
        raise ValueError("decision_config:ALPHA_RANGE")
    if not (0.0 <= r1 < r2):
        raise ValueError("decision_config:RANK_RATIO_ORDER")
    if not (-1.0 <= cosine <= 1.0):
        raise ValueError("decision_config:COSINE_RANGE")
    if min_families < 3:
        raise ValueError("decision_config:MIN_FAMILIES_AT_LEAST_3")
    if max_exact < 1 or max_exact > 20:
        raise ValueError("decision_config:MAX_EXACT_RANGE_1_20")
    if mc < 256:
        raise ValueError("decision_config:MONTE_CARLO_AT_LEAST_256")
    return {
        "alpha": alpha,
        "rank1_equivalence_max_ratio": r1,
        "rank2_min_ratio": r2,
        "rank2_min_lofo_cosine": cosine,
        "min_matched_families": min_families,
        "max_exact_signflip_families": max_exact,
        "monte_carlo_signflips": mc,
    }


def _parse_input(payload: Any) -> tuple[list[str], dict[str, dict[str, np.ndarray]], dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("schema") != INPUT_SCHEMA:
        raise ValueError("INPUT_SCHEMA_INVALID")
    config = _validate_config(payload.get("decision_config"))
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("rows:NONEMPTY_LIST_REQUIRED")
    declared_dimension = payload.get("dimension")
    dimension = int(declared_dimension) if declared_dimension is not None else None
    if dimension is not None and dimension <= 0:
        raise ValueError("dimension:MUST_BE_POSITIVE")

    grouped: dict[str, dict[str, np.ndarray]] = {}
    seen_row_ids: set[str] = set()
    inferred_dimension = dimension
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"row[{index}]:OBJECT_REQUIRED")
        row_id = str(row.get("row_id") or "").strip()
        family = str(row.get("family_group_id") or "").strip()
        semantic = str(row.get("semantic_class") or "").strip().upper()
        if not row_id:
            raise ValueError(f"row[{index}]:ROW_ID_REQUIRED")
        if row_id in seen_row_ids:
            raise ValueError(f"row[{index}]:DUPLICATE_ROW_ID:{row_id}")
        seen_row_ids.add(row_id)
        if not family:
            raise ValueError(f"row[{index}]:FAMILY_GROUP_ID_REQUIRED")
        if semantic not in CLASSES:
            raise ValueError(f"row[{index}]:SEMANTIC_CLASS_INVALID:{semantic}")
        vector = _as_finite_vector(row.get("activation"), name=f"row[{index}].activation", dimension=inferred_dimension)
        if inferred_dimension is None:
            inferred_dimension = int(vector.size)
        family_rows = grouped.setdefault(family, {})
        if semantic in family_rows:
            raise ValueError(f"family[{family}]:DUPLICATE_CLASS:{semantic}")
        family_rows[semantic] = vector

    families = sorted(grouped)
    if len(families) < config["min_matched_families"]:
        raise ValueError(f"MATCHED_FAMILY_COUNT_BELOW_DECLARED_MIN:{len(families)}<{config['min_matched_families']}")
    for family in families:
        missing = [name for name in CLASSES if name not in grouped[family]]
        if missing:
            raise ValueError(f"family[{family}]:MISSING_CLASSES:{','.join(missing)}")
    if inferred_dimension is None:
        raise ValueError("DIMENSION_UNRESOLVED")
    return families, grouped, {**config, "dimension": inferred_dimension}


def _norm(vector: np.ndarray) -> float:
    return float(np.linalg.norm(vector))


def _unit(vector: np.ndarray, *, name: str) -> np.ndarray:
    n = _norm(vector)
    if not math.isfinite(n) or n <= 1e-12:
        raise ValueError(f"{name}:DEGENERATE")
    return vector / n


def _project_perp(vector: np.ndarray, unit_axis: np.ndarray) -> np.ndarray:
    return vector - float(np.dot(vector, unit_axis)) * unit_axis


def _cosine(a: np.ndarray, b: np.ndarray) -> float | None:
    na, nb = _norm(a), _norm(b)
    if na <= 1e-12 or nb <= 1e-12:
        return None
    return float(np.dot(a, b) / (na * nb))


def _signflip_test(second_contrasts: list[np.ndarray], h1_unit: np.ndarray, *, payload_sha256: str, max_exact_families: int, monte_carlo_signflips: int) -> dict[str, Any]:
    g = len(second_contrasts)

    def statistic(signs: np.ndarray) -> float:
        acc = np.zeros_like(second_contrasts[0], dtype=np.float64)
        for sign, vector in zip(signs, second_contrasts):
            acc += float(sign) * vector
        return _norm(_project_perp(acc / float(g), h1_unit))

    observed = statistic(np.ones(g, dtype=np.float64))
    if g <= max_exact_families:
        total = 1 << g
        extreme = 0
        values: list[float] = []
        for bits in range(total):
            signs = np.fromiter((1.0 if (bits >> i) & 1 else -1.0 for i in range(g)), dtype=np.float64, count=g)
            value = statistic(signs)
            values.append(value)
            if value >= observed - 1e-12:
                extreme += 1
        p_value = extreme / float(total)
        mode = "EXACT_ALL_N_U_SIGN_FLIPS"
        samples = total
        theoretical_min_p = min(1.0, 2.0 / float(total))
    else:
        rng = np.random.default_rng(int(payload_sha256[:16], 16))
        extreme = 0
        values = []
        for _ in range(monte_carlo_signflips):
            signs = rng.choice(np.array([-1.0, 1.0]), size=g)
            value = statistic(signs)
            values.append(value)
            if value >= observed - 1e-12:
                extreme += 1
        p_value = (extreme + 1.0) / (monte_carlo_signflips + 1.0)
        mode = "DETERMINISTIC_MONTE_CARLO_N_U_SIGN_FLIPS"
        samples = monte_carlo_signflips
        theoretical_min_p = 1.0 / float(monte_carlo_signflips + 1)

    values_arr = np.asarray(values, dtype=np.float64)
    return {
        "mode": mode,
        "samples": samples,
        "observed_orthogonal_h2_norm": observed,
        "p_value": float(p_value),
        "null_q50": float(np.quantile(values_arr, 0.50)),
        "null_q95": float(np.quantile(values_arr, 0.95)),
        "null_max": float(np.max(values_arr)),
        "theoretical_min_p_for_mode": float(theoretical_min_p),
    }


def _geometry(h1_by_family: list[np.ndarray], d2_by_family: list[np.ndarray], *, payload_sha: str, config: dict[str, Any], label: str) -> dict[str, Any]:
    h1 = np.mean(np.stack(h1_by_family, axis=0), axis=0)
    h1_unit = _unit(h1, name=f"{label}_H1")
    d2 = np.mean(np.stack(d2_by_family, axis=0), axis=0)
    h2 = _project_perp(d2, h1_unit)
    h1_norm, h2_norm = _norm(h1), _norm(h2)
    ratio = h2_norm / h1_norm

    lofo_rows: list[dict[str, Any]] = []
    lofo_cosines: list[float] = []
    if len(h1_by_family) >= 2 and h2_norm > 1e-12:
        h2_unit = h2 / h2_norm
        for leave_index in range(len(h1_by_family)):
            keep_h1 = [v for i, v in enumerate(h1_by_family) if i != leave_index]
            keep_d2 = [v for i, v in enumerate(d2_by_family) if i != leave_index]
            h1_lofo = np.mean(np.stack(keep_h1, axis=0), axis=0)
            h1_lofo_unit = _unit(h1_lofo, name=f"{label}_LOFO_H1:{leave_index}")
            d2_lofo = np.mean(np.stack(keep_d2, axis=0), axis=0)
            h2_lofo = _project_perp(d2_lofo, h1_lofo_unit)
            cosine = _cosine(h2_lofo, h2_unit)
            if cosine is not None:
                lofo_cosines.append(cosine)
            lofo_rows.append({"index": leave_index, "h2_to_h1_ratio": float(_norm(h2_lofo) / _norm(h1_lofo)), "h2_cosine_to_full": cosine})

    signflip = _signflip_test(
        d2_by_family,
        h1_unit,
        payload_sha256=payload_sha,
        max_exact_families=int(config["max_exact_signflip_families"]),
        monte_carlo_signflips=int(config["monte_carlo_signflips"]),
    )
    return {
        "h1": h1,
        "h2": h2,
        "h1_norm": h1_norm,
        "h2_norm": h2_norm,
        "ratio": ratio,
        "lofo_rows": lofo_rows,
        "min_lofo_cosine": min(lofo_cosines) if lofo_cosines else None,
        "signflip": signflip,
    }


def _classify(geometry: dict[str, Any], config: dict[str, Any]) -> tuple[str, bool]:
    alpha = float(config["alpha"])
    rank1_max = float(config["rank1_equivalence_max_ratio"])
    rank2_min = float(config["rank2_min_ratio"])
    required_cosine = float(config["rank2_min_lofo_cosine"])
    signflip = geometry["signflip"]
    exact_underpowered = signflip["mode"] == "EXACT_ALL_N_U_SIGN_FLIPS" and float(signflip["theoretical_min_p_for_mode"]) > alpha
    rank2_pass = (
        not exact_underpowered
        and geometry["ratio"] >= rank2_min
        and float(signflip["p_value"]) <= alpha
        and geometry["min_lofo_cosine"] is not None
        and geometry["min_lofo_cosine"] >= required_cosine
    )
    rank1_pass = (
        not exact_underpowered
        and geometry["ratio"] <= rank1_max
        and all(float(row["h2_to_h1_ratio"]) <= rank1_max for row in geometry["lofo_rows"])
        and float(signflip["p_value"]) > alpha
    )
    if rank2_pass:
        return "TWO_DIMENSIONAL_REQUIRED", exact_underpowered
    if rank1_pass:
        return "ONE_DIMENSIONAL_SUPPORTED", exact_underpowered
    return "UNRESOLVED", exact_underpowered


def analyze(payload: dict[str, Any]) -> dict[str, Any]:
    payload_sha = canonical_sha(payload)
    families, grouped, config = _parse_input(payload)
    dim = int(config["dimension"])

    h1_by_family: list[np.ndarray] = []
    d2_by_family: list[np.ndarray] = []
    balanced_h1: list[np.ndarray] = []
    balanced_d2: list[np.ndarray] = []
    family_receipts: list[dict[str, Any]] = []
    for family in families:
        a, n, u = grouped[family]["AFFIRMATIVE"], grouped[family]["NEGATIVE"], grouped[family]["NEUTRAL"]
        h1g = a - 0.5 * (n + u)
        d2g = n - u
        pair_energy = math.sqrt(_norm(h1g) ** 2 + _norm(d2g) ** 2)
        if not math.isfinite(pair_energy) or pair_energy <= 1e-12:
            raise ValueError(f"family[{family}]:DEGENERATE_MATCHED_CONTRAST_PAIR")
        h1_by_family.append(h1g)
        d2_by_family.append(d2g)
        balanced_h1.append(h1g / pair_energy)
        balanced_d2.append(d2g / pair_energy)
        family_receipts.append({
            "family_group_id": family,
            "h1_norm": _norm(h1g),
            "n_minus_u_norm": _norm(d2g),
            "contrast_pair_energy": pair_energy,
            "triad_sha256": hashlib.sha256(np.concatenate([a, n, u]).astype("<f8", copy=False).tobytes()).hexdigest(),
        })

    raw = _geometry(h1_by_family, d2_by_family, payload_sha=payload_sha, config=config, label="RAW")
    balanced = _geometry(balanced_h1, balanced_d2, payload_sha=payload_sha, config=config, label="FAMILY_ENERGY_BALANCED")
    raw_class, raw_underpowered = _classify(raw, config)
    balanced_class, balanced_underpowered = _classify(balanced, config)

    reasons: list[str] = []
    if raw_class == balanced_class and raw_class != "UNRESOLVED":
        verdict = raw_class
    else:
        verdict = "UNRESOLVED"
        if raw_class != balanced_class:
            reasons.append("RAW_AND_FAMILY_ENERGY_BALANCED_CLASSIFICATIONS_DISAGREE")

    if verdict == "TWO_DIMENSIONAL_REQUIRED":
        reasons.append("STABLE_ORTHOGONAL_N_MINUS_U_CONTRAST_EXCEEDS_PREREGISTERED_GATE_IN_RAW_AND_FAMILY_BALANCED_ANALYSES")
    elif verdict == "ONE_DIMENSIONAL_SUPPORTED":
        reasons.append("SECOND_CONTRAST_WITHIN_PREREGISTERED_EQUIVALENCE_BOUND_IN_RAW_AND_FAMILY_BALANCED_ANALYSES")
    else:
        if raw_underpowered or balanced_underpowered:
            reasons.append("EXACT_SIGNFLIP_DESIGN_CANNOT_REACH_DECLARED_ALPHA_AT_THIS_FAMILY_COUNT")
        if not reasons:
            reasons.append("RANK_DECISION_REMAINS_UNRESOLVED_UNDER_ROBUSTNESS_GATES")

    class_means = {semantic: np.mean(np.stack([grouped[family][semantic] for family in families], axis=0), axis=0) for semantic in CLASSES}
    grand = sum(class_means.values()) / 3.0
    centered = np.stack([class_means[name] - grand for name in CLASSES], axis=0)
    singular = np.linalg.svd(centered, compute_uv=False)
    sigma1 = float(singular[0]) if singular.size >= 1 else 0.0
    sigma2 = float(singular[1]) if singular.size >= 2 else 0.0

    raw_lofo = [{"left_out_family_group_id": family, **row} for family, row in zip(families, raw["lofo_rows"])]
    balanced_lofo = [{"left_out_family_group_id": family, **row} for family, row in zip(families, balanced["lofo_rows"])]
    result_core = {
        "schema": OUTPUT_SCHEMA,
        "input_schema": INPUT_SCHEMA,
        "input_sha256": payload_sha,
        "analysis_scope": "CALIBRATION_ONLY_NO_MODEL_RUNTIME_NO_HOLDOUT_OPEN",
        "dimension": dim,
        "matched_family_count": len(families),
        "families": families,
        "decision_config": {key: config[key] for key in ("alpha", "rank1_equivalence_max_ratio", "rank2_min_ratio", "rank2_min_lofo_cosine", "min_matched_families", "max_exact_signflip_families", "monte_carlo_signflips")},
        "geometry": {
            "h1_definition": "mean_family[A - 0.5*(N+U)]",
            "h2_definition": "project_perpendicular_to_h1(mean_family[N-U])",
            "h1_norm": raw["h1_norm"],
            "h2_orthogonal_norm": raw["h2_norm"],
            "h2_to_h1_ratio": raw["ratio"],
            "class_centroid_singular_values": [float(v) for v in singular[:3]],
            "sigma2_to_sigma1_ratio": sigma2 / sigma1 if sigma1 > 1e-12 else float("inf"),
            "h1_sha256_f64le": hashlib.sha256(np.asarray(raw["h1"], dtype="<f8").tobytes()).hexdigest(),
            "h2_orthogonal_sha256_f64le": hashlib.sha256(np.asarray(raw["h2"], dtype="<f8").tobytes()).hexdigest(),
        },
        "randomization": raw["signflip"],
        "leave_one_family_out": {"rows": raw_lofo, "min_h2_cosine_to_full": raw["min_lofo_cosine"]},
        "family_energy_balanced_robustness": {
            "normalization": "scale each family's h1 and N-U together by inverse sqrt(||h1||^2+||N-U||^2); preserves within-family contrast ratio while removing cross-family magnitude domination",
            "classification": balanced_class,
            "h1_norm": balanced["h1_norm"],
            "h2_orthogonal_norm": balanced["h2_norm"],
            "h2_to_h1_ratio": balanced["ratio"],
            "randomization": balanced["signflip"],
            "leave_one_family_out": {"rows": balanced_lofo, "min_h2_cosine_to_full": balanced["min_lofo_cosine"]},
        },
        "family_receipts": family_receipts,
        "verdict": verdict,
        "reasons": reasons,
        "promotion_boundary": {
            "opens_holdout": False,
            "runs_model": False,
            "new_runtime_credit": 0,
            "jspace_model_runtime_credit": 0,
            "training_credit": 0,
            "whole_entityos_hcu_runtime_credit": 0,
            "canonical_semantics_promotion": False,
        },
    }
    return {**result_core, "analysis_receipt_sha256": canonical_sha(result_core)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Calibration activation JSON")
    parser.add_argument("--output", required=True, help="Write deterministic analysis JSON")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = analyze(payload)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "verdict": result["verdict"],
        "matched_family_count": result["matched_family_count"],
        "h2_to_h1_ratio": result["geometry"]["h2_to_h1_ratio"],
        "p_value": result["randomization"]["p_value"],
        "analysis_receipt_sha256": result["analysis_receipt_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
