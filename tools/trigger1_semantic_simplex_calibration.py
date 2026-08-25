#!/usr/bin/env python3
"""Calibration-only semantic dimensionality discriminator for Trigger-1 J-Space.

This capsule consumes label-free calibration centroids for three semantic states and
asks a narrower question than a steering run: is the reproducible between-class
geometry adequately one-dimensional, or is a second semantic dimension supported?

It never opens holdout, never invokes a model, never mints canonical/J-Space/HCU/
training credit, and never changes the current promotion gate.  Its output is a
measurement candidate that can decide which *future* native-cvec discriminator is
scientifically appropriate.

Input schema (abridged):
  {
    "schema": "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION_INPUT/v1",
    "source_identity": {... exact hashes ..., "layer": 20},
    "label_free": {
      "scan_pass": true,
      "scan_receipt_sha256": "<64 hex>",
      "holdout_opened": false
    },
    "rank_gate": {
      "rank1_ratio_max": 0.12,
      "rank2_ratio_min": 0.25,
      "min_h1_family_cosine": 0.75,
      "min_h2_family_cosine": 0.65,
      "null_samples": 128,
      "null_quantile": 0.95,
      "rank2_null_multiplier": 1.05
    },
    "families": [
      {"family_id": "...", "centroids": {
        "AFFIRMATIVE": [..], "NEGATIVE": [..], "NEUTRAL": [..]
      }}
    ]
  }

The class-centroid plane has rank <= 2 after centering.  sigma2/sigma1 tests whether
one signed contrast is enough.  A deterministic independent within-family class-label
permutation null tests whether sigma2 survives loss of cross-family semantic alignment.
Cross-family h1/h2 cosine checks prevent a pooled average from hiding sign instability.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

INPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION_INPUT/v1"
RESULT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION_RESULT/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
PERMUTATIONS = tuple(itertools.permutations(CLASSES))
EPS = 1e-12


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def as_vector(value: Any, *, name: str, dimension: int | None) -> tuple[np.ndarray, int]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"VECTOR_REQUIRED:{name}")
    try:
        vector = np.asarray([float(x) for x in value], dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"VECTOR_NON_NUMERIC:{name}") from exc
    if vector.ndim != 1 or not np.all(np.isfinite(vector)):
        raise ValueError(f"VECTOR_NONFINITE_OR_NONDIM1:{name}")
    if dimension is None:
        dimension = int(vector.shape[0])
        if dimension < 2:
            raise ValueError("VECTOR_DIMENSION_MUST_BE_AT_LEAST_2")
    elif int(vector.shape[0]) != dimension:
        raise ValueError(f"VECTOR_DIMENSION_MISMATCH:{name}:{vector.shape[0]}:{dimension}")
    return vector, dimension


def unit(vector: np.ndarray) -> np.ndarray | None:
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= EPS:
        return None
    return vector / norm


def cosine(a: np.ndarray, b: np.ndarray) -> float | None:
    ua = unit(a)
    ub = unit(b)
    if ua is None or ub is None:
        return None
    return float(np.clip(np.dot(ua, ub), -1.0, 1.0))


def quantile_higher(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("NULL_VALUES_REQUIRED")
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))
    return float(ordered[idx])


def geometry(families: list[dict[str, np.ndarray]]) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    means = {
        semantic_class: np.mean([family[semantic_class] for family in families], axis=0)
        for semantic_class in CLASSES
    }
    centroid = sum(means.values()) / float(len(CLASSES))
    centered = np.stack([means[semantic_class] - centroid for semantic_class in CLASSES], axis=0)
    singular = np.linalg.svd(centered, compute_uv=False)
    if singular.shape[0] < 2:
        singular = np.pad(singular, (0, 2 - singular.shape[0]))
    return means, centered, singular


def h1_h2(means: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray | None]:
    h1_raw = means["AFFIRMATIVE"] - 0.5 * (means["NEGATIVE"] + means["NEUTRAL"])
    h1 = unit(h1_raw)
    if h1 is None:
        raise ValueError("H1_DEGENERATE")
    h2_raw = means["NEGATIVE"] - means["NEUTRAL"]
    h2_residual = h2_raw - np.dot(h2_raw, h1) * h1
    return h1, unit(h2_residual)


def deterministic_null_sigma2(
    families: list[dict[str, np.ndarray]], input_sha: str, null_samples: int
) -> list[float]:
    values: list[float] = []
    for sample_index in range(null_samples):
        permuted: list[dict[str, np.ndarray]] = []
        selected: list[int] = []
        for family_index, family in enumerate(families):
            digest = hashlib.sha256(
                f"{input_sha}|null|{sample_index}|family|{family_index}".encode("utf-8")
            ).digest()
            permutation_index = int.from_bytes(digest[:8], "big") % len(PERMUTATIONS)
            selected.append(permutation_index)
            permutation = PERMUTATIONS[permutation_index]
            permuted.append({
                semantic_class: family[permutation[position]]
                for position, semantic_class in enumerate(CLASSES)
            })
        # A globally identical identity assignment is not a null intervention.
        if all(index == 0 for index in selected):
            permutation = PERMUTATIONS[1]
            family = families[-1]
            permuted[-1] = {
                semantic_class: family[permutation[position]]
                for position, semantic_class in enumerate(CLASSES)
            }
        _, _, singular = geometry(permuted)
        values.append(float(singular[1]))
    return values


def adjudicate(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if payload.get("schema") != INPUT_SCHEMA:
        failures.append("INPUT_SCHEMA_INVALID")

    identity = payload.get("source_identity")
    if not isinstance(identity, dict):
        failures.append("SOURCE_IDENTITY_REQUIRED")
        identity = {}
    for key in ("checkpoint_sha256", "tokenizer_sha256", "runtime_build_sha256"):
        if not is_sha256(identity.get(key)):
            failures.append(f"SOURCE_IDENTITY_SHA256_REQUIRED:{key}")
    if not isinstance(identity.get("layer"), int) or identity.get("layer") < 0:
        failures.append("SOURCE_LAYER_REQUIRED")

    label_free = payload.get("label_free")
    if not isinstance(label_free, dict):
        failures.append("LABEL_FREE_EVIDENCE_REQUIRED")
        label_free = {}
    if label_free.get("scan_pass") is not True:
        failures.append("LABEL_FREE_SCAN_PASS_REQUIRED")
    if not is_sha256(label_free.get("scan_receipt_sha256")):
        failures.append("LABEL_FREE_SCAN_RECEIPT_REQUIRED")
    if label_free.get("holdout_opened") is not False:
        failures.append("CALIBRATION_CAPSULE_REQUIRES_HOLDOUT_CLOSED")

    gate = payload.get("rank_gate")
    if not isinstance(gate, dict):
        failures.append("RANK_GATE_REQUIRED")
        gate = {}
    try:
        rank1_ratio_max = float(gate.get("rank1_ratio_max"))
        rank2_ratio_min = float(gate.get("rank2_ratio_min"))
        min_h1 = float(gate.get("min_h1_family_cosine"))
        min_h2 = float(gate.get("min_h2_family_cosine"))
        null_samples = int(gate.get("null_samples"))
        null_quantile = float(gate.get("null_quantile"))
        null_multiplier = float(gate.get("rank2_null_multiplier"))
        if not (0.0 <= rank1_ratio_max < rank2_ratio_min <= 1.0):
            raise ValueError
        if not (-1.0 <= min_h1 <= 1.0 and -1.0 <= min_h2 <= 1.0):
            raise ValueError
        if not (16 <= null_samples <= 4096):
            raise ValueError
        if not (0.5 <= null_quantile < 1.0):
            raise ValueError
        if null_multiplier < 1.0:
            raise ValueError
    except (TypeError, ValueError):
        failures.append("RANK_GATE_INVALID")

    raw_families = payload.get("families")
    parsed: list[dict[str, np.ndarray]] = []
    family_ids: set[str] = set()
    dimension: int | None = None
    if not isinstance(raw_families, list) or len(raw_families) < 3:
        failures.append("AT_LEAST_THREE_CALIBRATION_FAMILIES_REQUIRED")
    else:
        try:
            for row_index, row in enumerate(raw_families):
                if not isinstance(row, dict):
                    raise ValueError(f"FAMILY_OBJECT_REQUIRED:{row_index}")
                family_id = row.get("family_id")
                if not isinstance(family_id, str) or not family_id.strip():
                    raise ValueError(f"FAMILY_ID_REQUIRED:{row_index}")
                if family_id in family_ids:
                    raise ValueError(f"FAMILY_ID_DUPLICATE:{family_id}")
                family_ids.add(family_id)
                centroids = row.get("centroids")
                if not isinstance(centroids, dict) or set(centroids) != set(CLASSES):
                    raise ValueError(f"EXACT_THREE_CLASS_CENTROIDS_REQUIRED:{family_id}")
                parsed_row: dict[str, np.ndarray] = {}
                for semantic_class in CLASSES:
                    vector, dimension = as_vector(
                        centroids[semantic_class], name=f"{family_id}:{semantic_class}", dimension=dimension
                    )
                    parsed_row[semantic_class] = vector
                parsed.append(parsed_row)
        except ValueError as exc:
            failures.append(str(exc))

    input_sha = canonical_sha(payload)
    if failures:
        return {
            "schema": RESULT_SCHEMA,
            "status": "INVALID_INPUT_FAIL_CLOSED",
            "input_sha256": input_sha,
            "decision": "UNRESOLVED",
            "failures": sorted(set(failures)),
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        }

    means, _, singular = geometry(parsed)
    sigma1 = float(singular[0])
    sigma2 = float(singular[1])
    if sigma1 <= EPS:
        return {
            "schema": RESULT_SCHEMA,
            "status": "MEASUREMENT_UNRESOLVED",
            "input_sha256": input_sha,
            "decision": "UNRESOLVED",
            "failures": ["BETWEEN_CLASS_GEOMETRY_DEGENERATE"],
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        }

    rank_ratio = sigma2 / sigma1
    global_h1, global_h2 = h1_h2(means)
    h1_cosines: list[float] = []
    h2_cosines: list[float] = []
    h2_degenerate_families = 0
    for family in parsed:
        fh1, fh2 = h1_h2(family)
        h1_value = cosine(fh1, global_h1)
        if h1_value is None:
            h1_value = -1.0
        h1_cosines.append(h1_value)
        if global_h2 is not None:
            if fh2 is None:
                h2_degenerate_families += 1
            else:
                value = cosine(fh2, global_h2)
                h2_cosines.append(-1.0 if value is None else value)

    null_sigma2 = deterministic_null_sigma2(parsed, input_sha, null_samples)
    null_threshold = quantile_higher(null_sigma2, null_quantile)
    min_h1_observed = min(h1_cosines)
    min_h2_observed = min(h2_cosines) if h2_cosines and h2_degenerate_families == 0 else None

    decision = "UNRESOLVED"
    decision_reason = "MEASUREMENT_FALLS_IN_PREDECLARED_UNRESOLVED_REGION"
    if min_h1_observed < min_h1:
        decision_reason = "H1_CROSS_FAMILY_COHERENCE_BELOW_GATE"
    elif rank_ratio <= rank1_ratio_max:
        decision = "ONE_DIMENSIONAL_SUPPORTED"
        decision_reason = "SIGMA2_TO_SIGMA1_WITHIN_PREDECLARED_RANK1_REGION"
    elif (
        rank_ratio >= rank2_ratio_min
        and sigma2 > null_threshold * null_multiplier
        and global_h2 is not None
        and min_h2_observed is not None
        and min_h2_observed >= min_h2
    ):
        decision = "TWO_DIMENSIONAL_REQUIRED"
        decision_reason = "RANK2_RATIO_NULL_AND_CROSS_FAMILY_H2_GATES_ALL_PASS"
    elif rank_ratio >= rank2_ratio_min and (global_h2 is None or min_h2_observed is None or min_h2_observed < min_h2):
        decision_reason = "RANK2_MAGNITUDE_PRESENT_BUT_H2_CROSS_FAMILY_COHERENCE_INSUFFICIENT"
    elif rank_ratio >= rank2_ratio_min and sigma2 <= null_threshold * null_multiplier:
        decision_reason = "RANK2_MAGNITUDE_NOT_ABOVE_PREDECLARED_PERMUTATION_NULL_GATE"

    h1_sha = canonical_sha(global_h1.tolist())
    h2_sha = canonical_sha(global_h2.tolist()) if global_h2 is not None else None
    return {
        "schema": RESULT_SCHEMA,
        "status": "CALIBRATION_MEASUREMENT_COMPLETE",
        "input_sha256": input_sha,
        "source_identity": identity,
        "family_count": len(parsed),
        "dimension": dimension,
        "singular_values": [float(x) for x in singular[:3]],
        "sigma2_over_sigma1": rank_ratio,
        "null": {
            "samples": null_samples,
            "quantile": null_quantile,
            "sigma2_threshold": null_threshold,
            "rank2_null_multiplier": null_multiplier,
            "max_sigma2": max(null_sigma2),
        },
        "cross_family": {
            "min_h1_cosine": min_h1_observed,
            "min_h2_cosine": min_h2_observed,
            "h2_degenerate_families": h2_degenerate_families,
        },
        "basis_measurement": {
            "h1_sha256": h1_sha,
            "h2_sha256": h2_sha,
            "h2_present": global_h2 is not None,
        },
        "decision": decision,
        "decision_reason": decision_reason,
        "failures": [],
        "holdout_opened": False,
        "model_invoked": False,
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "This is calibration-only representation geometry. ONE_DIMENSIONAL_SUPPORTED or "
            "TWO_DIMENSIONAL_REQUIRED selects a future causal test shape; neither result is "
            "model-specific J-Space causal credit without fresh native intervention evidence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("INPUT_OBJECT_REQUIRED")
        result = adjudicate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {
            "schema": RESULT_SCHEMA,
            "status": "INVALID_INPUT_FAIL_CLOSED",
            "decision": "UNRESOLVED",
            "failures": [f"INPUT_LOAD_FAILED:{type(exc).__name__}:{str(exc)[:300]}"],
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        }
    encoded = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
