#!/usr/bin/env python3
"""Calibration-only nuisance residualizer for Trigger-1 abstract-state vectors.

Input supplies one semantic vector per evaluator-side class and calibration-derived nuisance
contrast vectors grouped into the four required nuisance families. The tool constructs a
single orthonormal nuisance subspace with SVD, projects the centered semantic geometry into
its orthogonal complement, and fails closed if too little semantic norm survives.

The output is suitable for binding into `abstract_state_deconfound` evidence used by the
v11 promotion gate. It does not run a model, choose a cvec gain, or open holdout data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

INPUT_SCHEMA = "CLAY_TRIGGER1_NUISANCE_RESIDUALIZE_INPUT/v1"
OUTPUT_SCHEMA = "CLAY_TRIGGER1_NUISANCE_RESIDUALIZE_RESULT/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
REQUIRED_NUISANCE_FAMILIES = (
    "CANONICAL_LABEL_LEXEME",
    "SEMANTIC_SYNONYM_LEXICON",
    "GENERIC_INSTRUCTION_COMPLIANCE",
    "OUTPUT_CODE_IDENTITY",
)
MAX_POST_PROJECTION_ABS_NUISANCE_COSINE = 1e-3
MIN_RETAINED_SEMANTIC_NORM_FRACTION = 0.20
SVD_RELATIVE_TOLERANCE = 1e-10


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _vector(value: Any, dimension: int, name: str) -> np.ndarray:
    if not isinstance(value, list) or len(value) != dimension:
        raise ValueError(f"{name}_DIMENSION_MISMATCH")
    arr = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name}_NONFINITE")
    if float(np.linalg.norm(arr)) <= 1e-12:
        raise ValueError(f"{name}_DEGENERATE")
    return arr


def _unit(arr: np.ndarray, name: str) -> np.ndarray:
    n = float(np.linalg.norm(arr))
    if not math.isfinite(n) or n <= 1e-12:
        raise ValueError(f"{name}_DEGENERATE")
    return arr / n


def residualize(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != INPUT_SCHEMA:
        raise ValueError("INPUT_SCHEMA_INVALID")
    if payload.get("fit_split") != "CALIBRATION":
        raise ValueError("NUISANCE_FIT_MUST_BE_CALIBRATION_ONLY")
    if payload.get("frozen_before_holdout") is not True:
        raise ValueError("RESIDUALIZATION_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(payload.get("semantic_source_receipt_sha256")):
        raise ValueError("SEMANTIC_SOURCE_RECEIPT_REQUIRED")
    if not _sha256(payload.get("nuisance_source_receipt_sha256")):
        raise ValueError("NUISANCE_SOURCE_RECEIPT_REQUIRED")

    dimension = payload.get("dimension")
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 4:
        raise ValueError("DIMENSION_INVALID")

    semantic_raw = payload.get("semantic_vectors")
    if not isinstance(semantic_raw, dict) or set(semantic_raw) != set(CLASSES):
        raise ValueError("EXACT_THREE_SEMANTIC_VECTORS_REQUIRED")
    semantic = {name: _vector(semantic_raw[name], dimension, f"SEMANTIC_{name}") for name in CLASSES}

    nuisance_raw = payload.get("nuisance_vectors")
    if not isinstance(nuisance_raw, dict) or set(nuisance_raw) != set(REQUIRED_NUISANCE_FAMILIES):
        raise ValueError("EXACT_REQUIRED_NUISANCE_FAMILIES_REQUIRED")

    nuisance_rows: list[np.ndarray] = []
    family_counts: dict[str, int] = {}
    for family in REQUIRED_NUISANCE_FAMILIES:
        rows = nuisance_raw.get(family)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"NUISANCE_FAMILY_EMPTY:{family}")
        family_counts[family] = len(rows)
        for i, row in enumerate(rows):
            nuisance_rows.append(_unit(_vector(row, dimension, f"NUISANCE_{family}_{i}"), f"NUISANCE_{family}_{i}"))

    matrix = np.stack(nuisance_rows, axis=0)
    _, singular, vh = np.linalg.svd(matrix, full_matrices=False)
    if not singular.size or float(singular[0]) <= 1e-12:
        raise ValueError("NUISANCE_SUBSPACE_DEGENERATE")
    rank = int(np.sum(singular > float(singular[0]) * SVD_RELATIVE_TOLERANCE))
    if rank <= 0 or rank >= dimension:
        raise ValueError("NUISANCE_SUBSPACE_RANK_INVALID")
    q = vh[:rank, :]

    # Center the semantic simplex before projection so a common activation offset cannot
    # masquerade as either semantic geometry or nuisance contamination.
    grand = sum(semantic.values()) / float(len(CLASSES))
    centered = {name: semantic[name] - grand for name in CLASSES}

    projected: dict[str, np.ndarray] = {}
    retained: dict[str, float] = {}
    max_cosine = 0.0
    for name in CLASSES:
        raw = centered[name]
        raw_norm = float(np.linalg.norm(raw))
        if raw_norm <= 1e-12:
            raise ValueError(f"CENTERED_SEMANTIC_DEGENERATE:{name}")
        proj = raw - q.T @ (q @ raw)
        proj_norm = float(np.linalg.norm(proj))
        retained[name] = proj_norm / raw_norm
        if proj_norm <= 1e-12:
            raise ValueError(f"PROJECTED_SEMANTIC_DEGENERATE:{name}")
        projected[name] = proj
        u = proj / proj_norm
        max_cosine = max(max_cosine, float(np.max(np.abs(q @ u))))

    min_retained = min(retained.values())
    if max_cosine > MAX_POST_PROJECTION_ABS_NUISANCE_COSINE:
        raise ValueError("POST_PROJECTION_NUISANCE_ORTHOGONALITY_FAIL")
    if min_retained < MIN_RETAINED_SEMANTIC_NORM_FRACTION:
        raise ValueError("SEMANTIC_RESIDUAL_TOO_SMALL")

    projected_grand = sum(projected.values()) / float(len(CLASSES))
    projected = {name: projected[name] - projected_grand for name in CLASSES}
    unit_vectors = {name: _unit(projected[name], f"PROJECTED_{name}") for name in CLASSES}

    result_core = {
        "schema": OUTPUT_SCHEMA,
        "dimension": dimension,
        "fit_split": "CALIBRATION",
        "frozen_before_holdout": True,
        "required_nuisance_families": list(REQUIRED_NUISANCE_FAMILIES),
        "nuisance_family_vector_counts": family_counts,
        "nuisance_subspace_rank": rank,
        "nuisance_singular_values": [float(x) for x in singular[:rank]],
        "post_projection_max_abs_nuisance_cosine": max_cosine,
        "max_allowed_post_projection_abs_nuisance_cosine": MAX_POST_PROJECTION_ABS_NUISANCE_COSINE,
        "retained_semantic_subspace_norm_fraction_by_class": retained,
        "retained_semantic_subspace_norm_fraction": min_retained,
        "min_required_retained_semantic_norm_fraction": MIN_RETAINED_SEMANTIC_NORM_FRACTION,
        "semantic_source_receipt_sha256": payload["semantic_source_receipt_sha256"],
        "nuisance_source_receipt_sha256": payload["nuisance_source_receipt_sha256"],
        "projected_semantic_unit_vectors": {name: unit_vectors[name].tolist() for name in CLASSES},
        "projected_semantic_vector_sha256": {
            name: hashlib.sha256(np.asarray(unit_vectors[name], dtype="<f4").tobytes()).hexdigest()
            for name in CLASSES
        },
        "model_executed": False,
        "holdout_opened": False,
        "runtime_credit_minted": False,
    }
    return {**result_core, "result_sha256": canonical_sha(result_core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    out = residualize(payload)
    text = json.dumps(out, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
