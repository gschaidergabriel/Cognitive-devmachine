#!/usr/bin/env python3
"""Serialize nuisance-residualized Trigger-1 semantic vectors into pinned Q8 cvec bytes.

Consumes the canonical `trigger1_nuisance_residualize` result and reuses the retained native
Q8 cvec byte serializer.  It does not refit nuisance axes, alter the projected vectors,
choose a gain, run a model, or open holdout.  The emitted files therefore represent only the
post-deconfound actuator geometry at the pinned layer-20 cvec layout.

A common calibration-only scalar gain must still be selected/frozen separately before any
fresh holdout intervention.  Emission is source/serialization evidence only and mints no
semantic/J-Space/HCU/EntityOS/training/canonical credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from tools import trigger1_native_q8_family_balanced_cvec_emit as retained_emit
from tools import trigger1_nuisance_residualize as residualizer

SCHEMA = "CLAY_TRIGGER1_NATIVE_Q8_NUISANCE_RESIDUALIZED_CVEC_EMISSION/v1"
CLASSES = residualizer.CLASSES


class ResidualizedEmitError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def vector_sha_f32(vector: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vector, dtype="<f4").tobytes()).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def validate_residualized(value: Any) -> dict[str, np.ndarray]:
    if not isinstance(value, dict) or value.get("schema") != residualizer.OUTPUT_SCHEMA:
        raise ResidualizedEmitError("RESIDUALIZATION_RESULT_SCHEMA_INVALID")
    if value.get("fit_split") != "CALIBRATION" or value.get("frozen_before_holdout") is not True:
        raise ResidualizedEmitError("CALIBRATION_ONLY_FROZEN_RESIDUALIZATION_REQUIRED")
    if set(value.get("required_nuisance_families") or []) != set(residualizer.REQUIRED_NUISANCE_FAMILIES):
        raise ResidualizedEmitError("EXACT_REQUIRED_NUISANCE_FAMILIES_REQUIRED")
    if not _sha256(value.get("semantic_source_receipt_sha256")) or not _sha256(value.get("nuisance_source_receipt_sha256")):
        raise ResidualizedEmitError("SOURCE_RECEIPTS_REQUIRED")
    declared_result_sha = value.get("result_sha256")
    core = dict(value)
    core.pop("result_sha256", None)
    if declared_result_sha != residualizer.canonical_sha(core):
        raise ResidualizedEmitError("RESIDUALIZATION_RESULT_SHA256_MISMATCH")

    post_cos = value.get("post_projection_max_abs_nuisance_cosine")
    retained = value.get("retained_semantic_subspace_norm_fraction")
    if not isinstance(post_cos, (int, float)) or not math.isfinite(float(post_cos)):
        raise ResidualizedEmitError("POST_PROJECTION_NUISANCE_COSINE_REQUIRED")
    if float(post_cos) > residualizer.MAX_POST_PROJECTION_ABS_NUISANCE_COSINE:
        raise ResidualizedEmitError("POST_PROJECTION_NUISANCE_ORTHOGONALITY_REQUIRED")
    if not isinstance(retained, (int, float)) or not math.isfinite(float(retained)):
        raise ResidualizedEmitError("RETAINED_SEMANTIC_NORM_REQUIRED")
    if float(retained) < residualizer.MIN_RETAINED_SEMANTIC_NORM_FRACTION:
        raise ResidualizedEmitError("SEMANTIC_RESIDUAL_TOO_SMALL")

    raw_vectors = value.get("projected_semantic_unit_vectors")
    raw_hashes = value.get("projected_semantic_vector_sha256")
    if not isinstance(raw_vectors, dict) or set(raw_vectors) != set(CLASSES):
        raise ResidualizedEmitError("EXACT_THREE_PROJECTED_SEMANTIC_VECTORS_REQUIRED")
    if not isinstance(raw_hashes, dict) or set(raw_hashes) != set(CLASSES):
        raise ResidualizedEmitError("EXACT_THREE_PROJECTED_VECTOR_HASHES_REQUIRED")

    vectors: dict[str, np.ndarray] = {}
    for semantic in CLASSES:
        arr = np.asarray(raw_vectors[semantic], dtype=np.float64)
        if arr.shape != (retained_emit.N_EMBD,) or not np.all(np.isfinite(arr)):
            raise ResidualizedEmitError(f"PROJECTED_VECTOR_INVALID:{semantic}")
        norm = float(np.linalg.norm(arr))
        if abs(norm - 1.0) > 1e-6:
            raise ResidualizedEmitError(f"PROJECTED_VECTOR_UNIT_NORM_REQUIRED:{semantic}:{norm}")
        observed = vector_sha_f32(arr)
        if observed != raw_hashes[semantic]:
            raise ResidualizedEmitError(f"PROJECTED_VECTOR_SHA256_MISMATCH:{semantic}")
        vectors[semantic] = arr
    return vectors


def emit(residualized: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    vectors = validate_residualized(residualized)
    output_dir.mkdir(parents=True, exist_ok=True)

    files: dict[str, dict[str, Any]] = {}
    for semantic in CLASSES:
        vector = vectors[semantic]
        raw = retained_emit.cvec_bytes(
            vector,
            n_embd=retained_emit.N_EMBD,
            n_layer=retained_emit.N_LAYER,
            injection_layer=retained_emit.INJECTION_LAYER,
        )
        path = output_dir / f"target-{semantic.lower()}.nuisance-residualized.cvec.f32le"
        path.write_bytes(raw)
        files[semantic] = {
            "filename": path.name,
            "projected_vector_sha256_f32le": vector_sha_f32(vector),
            "projected_vector_l2": float(np.linalg.norm(vector)),
            "cvec_sha256": hashlib.sha256(raw).hexdigest(),
            "cvec_bytes": len(raw),
            "cvec_float_count": len(raw) // 4,
            "injection_layer": retained_emit.INJECTION_LAYER,
            "nonzero_layer_blocks": [retained_emit.INJECTION_LAYER],
        }

    core = {
        "schema": SCHEMA,
        "residualization_result_sha256": residualized["result_sha256"],
        "semantic_source_receipt_sha256": residualized["semantic_source_receipt_sha256"],
        "nuisance_source_receipt_sha256": residualized["nuisance_source_receipt_sha256"],
        "post_projection_max_abs_nuisance_cosine": residualized["post_projection_max_abs_nuisance_cosine"],
        "retained_semantic_subspace_norm_fraction": residualized["retained_semantic_subspace_norm_fraction"],
        "nuisance_subspace_rank": residualized["nuisance_subspace_rank"],
        "n_embd": retained_emit.N_EMBD,
        "n_layer": retained_emit.N_LAYER,
        "injection_layer": retained_emit.INJECTION_LAYER,
        "target_cvecs": files,
        "common_gain_required": True,
        "gain_selected_here": False,
        "gain_value": None,
        "model_executed": False,
        "holdout_opened": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "full_hcu_runtime_credit": False,
        "whole_entityos_hcu_runtime_credit": False,
        "training_credit": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "Serialization of the exact calibration-frozen nuisance-residualized semantic unit vectors into the "
            "pinned Qwen3-0.6B llama.cpp cvec layout. The files are not causal holdout evidence and carry no "
            "semantic/runtime/product credit until a separately authorized exact-byte intervention passes the "
            "current v13 successor gates."
        ),
    }
    return {**core, "emission_receipt_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--residualized", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    residualized = json.loads(Path(args.residualized).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    result = emit(residualized, output_dir)
    (output_dir / "nuisance-residualized-cvec-emission.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"schema": result["schema"], "emission_receipt_sha256": result["emission_receipt_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
