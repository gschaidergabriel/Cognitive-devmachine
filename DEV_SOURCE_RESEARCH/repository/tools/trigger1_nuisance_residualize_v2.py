#!/usr/bin/env python3
"""Calibration-only Trigger-1 nuisance residualizer with causal-basis export.

V1 correctly projects semantic geometry against the full SVD nuisance subspace,
but does not expose a reproducibly addressable orthonormal basis for later causal
controls. V2 preserves the validated v1 result and additionally constructs a
fixed-order modified-Gram-Schmidt (MGS) basis over the same normalized nuisance
contrast rows. It fails closed unless the deterministic MGS rank equals the v1
SVD rank and the basis spans every admitted nuisance row.

The exported q0..q(r-1) axes are calibration-only, frozen before holdout, and
hash-bound for use by the rank-complete cross-task causal gate. This module does
not execute a model, choose a gain, open holdout, or mint runtime credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from tools import trigger1_nuisance_residualize as v1

OUTPUT_SCHEMA = "CLAY_TRIGGER1_NUISANCE_RESIDUALIZE_RESULT/v2"
BASIS_SCHEMA = "CLAY_TRIGGER1_FROZEN_NUISANCE_SUBSPACE_BINDING/v1"
MGS_ABS_TOLERANCE = 1e-10
MAX_BASIS_GRAM_ERROR = 1e-10
MAX_ROW_SPAN_RESIDUAL = 1e-9


def _f32_sha(v: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(v, dtype="<f4").tobytes()).hexdigest()


def _ordered_normalized_rows(payload: dict[str, Any]) -> list[tuple[str, int, np.ndarray]]:
    dimension = payload["dimension"]
    raw = payload["nuisance_vectors"]
    rows: list[tuple[str, int, np.ndarray]] = []
    for family in v1.REQUIRED_NUISANCE_FAMILIES:
        family_rows = raw[family]
        for i, value in enumerate(family_rows):
            arr = v1._unit(
                v1._vector(value, dimension, f"NUISANCE_{family}_{i}"),
                f"NUISANCE_{family}_{i}",
            )
            rows.append((family, i, arr))
    return rows


def _deterministic_mgs(rows: list[tuple[str, int, np.ndarray]]) -> tuple[list[np.ndarray], list[dict[str, Any]]]:
    basis: list[np.ndarray] = []
    provenance: list[dict[str, Any]] = []
    for family, index, row in rows:
        x = np.asarray(row, dtype=np.float64).copy()
        # Two passes reduce loss of orthogonality while preserving fixed row order.
        for _ in range(2):
            for q in basis:
                x = x - float(np.dot(q, x)) * q
        residual_norm = float(np.linalg.norm(x))
        if not math.isfinite(residual_norm):
            raise ValueError(f"MGS_NONFINITE:{family}:{index}")
        if residual_norm <= MGS_ABS_TOLERANCE:
            continue
        q = x / residual_norm
        basis.append(q)
        provenance.append(
            {
                "source_family": family,
                "source_index": index,
                "pre_normalization_residual_l2": residual_norm,
            }
        )
    return basis, provenance


def _basis_audit(rows: list[tuple[str, int, np.ndarray]], basis: list[np.ndarray]) -> dict[str, float]:
    if not basis:
        raise ValueError("MGS_BASIS_EMPTY")
    q = np.stack(basis, axis=0)
    gram = q @ q.T
    gram_error = float(np.max(np.abs(gram - np.eye(len(basis), dtype=np.float64))))
    max_span_residual = 0.0
    for _, _, row in rows:
        residual = row - q.T @ (q @ row)
        max_span_residual = max(max_span_residual, float(np.linalg.norm(residual)))
    if gram_error > MAX_BASIS_GRAM_ERROR:
        raise ValueError(f"MGS_ORTHONORMALITY_FAIL:{gram_error}")
    if max_span_residual > MAX_ROW_SPAN_RESIDUAL:
        raise ValueError(f"MGS_SPAN_FAIL:{max_span_residual}")
    return {
        "max_abs_gram_error": gram_error,
        "max_input_row_span_residual_l2": max_span_residual,
    }


def residualize(payload: dict[str, Any]) -> dict[str, Any]:
    # V1 remains the authoritative semantic-residualization validator.
    base = v1.residualize(payload)
    rows = _ordered_normalized_rows(payload)
    basis, provenance = _deterministic_mgs(rows)
    if len(basis) != int(base["nuisance_subspace_rank"]):
        raise ValueError(
            f"MGS_SVD_RANK_MISMATCH:{len(basis)}:{base['nuisance_subspace_rank']}"
        )
    audit = _basis_audit(rows, basis)

    axes = []
    for i, (axis, src) in enumerate(zip(basis, provenance)):
        axes.append(
            {
                "axis_id": f"q{i}",
                "vector_sha256": _f32_sha(axis),
                "vector_hash_encoding": "IEEE754_FLOAT32_LITTLE_ENDIAN",
                "unit_vector": axis.tolist(),
                "l2": float(np.linalg.norm(axis)),
                **src,
            }
        )

    binding_core = {
        "schema": BASIS_SCHEMA,
        "producer_schema": OUTPUT_SCHEMA,
        "fit_split": "CALIBRATION",
        "frozen_before_holdout": True,
        "basis_method": "ORDERED_TWO_PASS_MODIFIED_GRAM_SCHMIDT_ON_CANONICAL_NORMALIZED_NUISANCE_ROWS",
        "basis_order": "REQUIRED_NUISANCE_FAMILIES_THEN_SOURCE_INDEX",
        "rank": len(axes),
        "axes": [
            {"axis_id": a["axis_id"], "vector_sha256": a["vector_sha256"]}
            for a in axes
        ],
        "v1_result_sha256": base["result_sha256"],
        "nuisance_source_receipt_sha256": base["nuisance_source_receipt_sha256"],
        "basis_max_abs_gram_error": audit["max_abs_gram_error"],
        "basis_max_input_row_span_residual_l2": audit["max_input_row_span_residual_l2"],
    }
    binding = {
        **binding_core,
        "receipt_sha256": v1.canonical_sha(binding_core),
    }

    core = {k: v for k, v in base.items() if k not in ("schema", "result_sha256")}
    core.update(
        {
            "schema": OUTPUT_SCHEMA,
            "base_v1_result_sha256": base["result_sha256"],
            "nuisance_basis_method": binding_core["basis_method"],
            "nuisance_basis_rank": len(axes),
            "nuisance_basis_axes": axes,
            "nuisance_basis_max_abs_gram_error": audit["max_abs_gram_error"],
            "nuisance_basis_max_input_row_span_residual_l2": audit["max_input_row_span_residual_l2"],
            "causal_nuisance_subspace_binding": binding,
            "model_executed": False,
            "holdout_opened": False,
            "runtime_credit_minted": False,
        }
    )
    return {**core, "result_sha256": v1.canonical_sha(core)}


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
