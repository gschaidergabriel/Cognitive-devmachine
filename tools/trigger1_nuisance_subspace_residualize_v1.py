#!/usr/bin/env python3
"""Fit and remove the canonical Trigger-1 nuisance subspace on calibration only.

Input binds a frozen semantic basis plus matched activation contrasts for exactly four
canonical nuisance axes:
  CANONICAL_LABEL_LEXEME
  SEMANTIC_SYNONYM_LEXICON
  GENERIC_INSTRUCTION_COMPLIANCE
  OUTPUT_CODE_IDENTITY

For each axis, matched positive-minus-negative activation contrasts are family-averaged.
The resulting nuisance span is SVD-orthonormalized, projected out of every semantic basis
axis, and the residual basis is measured for nuisance orthogonality and retained norm.
No holdout data is accepted or touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

INPUT_SCHEMA = "CLAY_TRIGGER1_NUISANCE_RESIDUALIZATION_INPUT/v1"
RECEIPT_SCHEMA = "CLAY_TRIGGER1_NUISANCE_SUBSPACE_RECEIPT/v1"
PROJECTED_SCHEMA = "CLAY_TRIGGER1_PROJECTED_SEMANTIC_BASIS/v1"
AXES = (
    "CANONICAL_LABEL_LEXEME",
    "SEMANTIC_SYNONYM_LEXICON",
    "GENERIC_INSTRUCTION_COMPLIANCE",
    "OUTPUT_CODE_IDENTITY",
)
MAX_ABS_COS = 1e-3
MIN_RETAINED = 0.20


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def is_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def vec(raw: Any, dimension: int, label: str) -> np.ndarray:
    if not isinstance(raw, list) or len(raw) != dimension:
        raise ValueError(f"{label}_DIMENSION_MISMATCH")
    out = np.asarray(raw, dtype=np.float64)
    if not np.all(np.isfinite(out)):
        raise ValueError(f"{label}_NONFINITE")
    return out


def vsha(x: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(x, dtype="<f4").tobytes()).hexdigest()


def residualize(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != INPUT_SCHEMA:
        raise ValueError("INPUT_SCHEMA_INVALID")
    if payload.get("calibration_only") is not True or payload.get("holdout_opened") is not False:
        raise ValueError("CALIBRATION_ONLY_HOLDOUT_CLOSED_REQUIRED")
    if payload.get("frozen_before_holdout") is not True:
        raise ValueError("RESIDUALIZATION_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    try:
        dimension = int(payload["dimension"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("DIMENSION_REQUIRED")
    if dimension <= 0:
        raise ValueError("DIMENSION_INVALID")
    for field in ("semantic_basis_receipt_sha256", "calibration_case_plan_sha256"):
        if not is_sha(payload.get(field)):
            raise ValueError(f"{field.upper()}_REQUIRED")

    semantic = payload.get("semantic_basis")
    if not isinstance(semantic, dict) or not (1 <= len(semantic) <= 2):
        raise ValueError("ONE_OR_TWO_SEMANTIC_AXES_REQUIRED")
    semantic_names = sorted(semantic)
    S = np.stack([vec(semantic[name], dimension, f"SEMANTIC_{name}") for name in semantic_names], axis=1)
    original_norm = float(np.linalg.norm(S))
    if not math.isfinite(original_norm) or original_norm <= 1e-12:
        raise ValueError("SEMANTIC_BASIS_DEGENERATE")

    pairs = payload.get("nuisance_pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("NUISANCE_PAIRS_REQUIRED")
    grouped: dict[str, dict[str, tuple[np.ndarray, np.ndarray]]] = {axis: {} for axis in AXES}
    for i, row in enumerate(pairs):
        if not isinstance(row, dict):
            raise ValueError(f"NUISANCE_ROW_{i}_OBJECT_REQUIRED")
        axis = str(row.get("nuisance_axis") or "")
        pair_id = str(row.get("pair_id") or "")
        if axis not in AXES:
            raise ValueError(f"NUISANCE_ROW_{i}_AXIS_INVALID")
        if not pair_id or pair_id in grouped[axis]:
            raise ValueError(f"NUISANCE_ROW_{i}_PAIR_ID_INVALID_OR_DUPLICATE")
        plus = vec(row.get("positive_activation"), dimension, f"NUISANCE_ROW_{i}_POSITIVE")
        minus = vec(row.get("negative_activation"), dimension, f"NUISANCE_ROW_{i}_NEGATIVE")
        grouped[axis][pair_id] = (plus, minus)
    if any(len(grouped[axis]) < 3 for axis in AXES):
        raise ValueError("AT_LEAST_THREE_MATCHED_PAIRS_PER_NUISANCE_AXIS_REQUIRED")

    nuisance_raw: dict[str, np.ndarray] = {}
    for axis in AXES:
        contrasts = [plus - minus for plus, minus in grouped[axis].values()]
        mean = np.mean(np.stack(contrasts, axis=0), axis=0)
        norm = float(np.linalg.norm(mean))
        if not math.isfinite(norm) or norm <= 1e-12:
            raise ValueError(f"NUISANCE_AXIS_DEGENERATE:{axis}")
        nuisance_raw[axis] = mean / norm

    N = np.stack([nuisance_raw[axis] for axis in AXES], axis=1)
    U, singular, _ = np.linalg.svd(N, full_matrices=False)
    tol = max(N.shape) * np.finfo(np.float64).eps * float(singular[0])
    rank = int(np.sum(singular > tol))
    if rank < 1:
        raise ValueError("NUISANCE_SUBSPACE_RANK_ZERO")
    Q = U[:, :rank]
    R = S - Q @ (Q.T @ S)
    residual_norm = float(np.linalg.norm(R))
    retained = residual_norm / original_norm
    if residual_norm <= 1e-12:
        raise ValueError("SEMANTIC_BASIS_ERASED_BY_NUISANCE_PROJECTION")

    # Orthogonality is measured before any optional re-orthonormalization of semantic axes.
    max_abs_cos = 0.0
    for i in range(R.shape[1]):
        rn = float(np.linalg.norm(R[:, i]))
        if rn <= 1e-12:
            raise ValueError(f"PROJECTED_SEMANTIC_AXIS_DEGENERATE:{semantic_names[i]}")
        for j in range(Q.shape[1]):
            qn = float(np.linalg.norm(Q[:, j]))
            max_abs_cos = max(max_abs_cos, abs(float(np.dot(R[:, i], Q[:, j]) / (rn * qn))))

    # Preserve the projected geometry; do not independently normalize axes here.
    projected_axes = {name: [float(x) for x in R[:, i]] for i, name in enumerate(semantic_names)}
    projected_core = {
        "schema": PROJECTED_SCHEMA,
        "dimension": dimension,
        "source_semantic_basis_receipt_sha256": payload["semantic_basis_receipt_sha256"],
        "calibration_case_plan_sha256": payload["calibration_case_plan_sha256"],
        "nuisance_axis_set": list(AXES),
        "nuisance_rank": rank,
        "nuisance_singular_values": [float(x) for x in singular],
        "semantic_axis_names": semantic_names,
        "projected_axes_f32_sha256": {name: vsha(R[:, i]) for i, name in enumerate(semantic_names)},
        "projected_axes": projected_axes,
        "post_projection_max_abs_nuisance_cosine": max_abs_cos,
        "retained_semantic_subspace_norm_fraction": retained,
        "frozen_before_holdout": True,
        "holdout_opened": False,
    }
    projected = {**projected_core, "projected_basis_receipt_sha256": canonical_sha(projected_core)}

    pass_gate = bool(max_abs_cos <= MAX_ABS_COS and retained >= MIN_RETAINED)
    receipt_core = {
        "schema": RECEIPT_SCHEMA,
        "input_sha256": canonical_sha(payload),
        "nuisance_axes": list(AXES),
        "nuisance_axis_pair_counts": {axis: len(grouped[axis]) for axis in AXES},
        "nuisance_axis_f32_sha256": {axis: vsha(nuisance_raw[axis]) for axis in AXES},
        "nuisance_rank": rank,
        "post_projection_max_abs_nuisance_cosine": max_abs_cos,
        "retained_semantic_subspace_norm_fraction": retained,
        "semantic_basis_residualized_against_nuisance_subspace": pass_gate,
        "nuisance_subspace_fit_on_calibration_only": True,
        "residualization_frozen_before_holdout": True,
        "holdout_opened": False,
        "projected_basis_receipt_sha256": projected["projected_basis_receipt_sha256"],
        "pass": pass_gate,
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "evidence_boundary": "Calibration-only linear nuisance-span fit and projection; no holdout/model intervention credit.",
    }
    receipt = {**receipt_core, "nuisance_subspace_receipt_sha256": canonical_sha(receipt_core)}
    return {"projected_basis": projected, "nuisance_receipt": receipt}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = residualize(payload)
        rc = 0 if result["nuisance_receipt"]["pass"] else 2
    except Exception as exc:
        result = {"schema": RECEIPT_SCHEMA, "pass": False, "error": f"{type(exc).__name__}:{str(exc)[:1000]}", "canonical_credit_minted": False}
        rc = 3
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
