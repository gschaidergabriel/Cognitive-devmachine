#!/usr/bin/env python3
"""Build an exact native llama.cpp cvec candidate from canonical Trigger-1 Q8 geometry.

This is a source/control-plane primitive only. It binds the same calibration activation
payload to the canonical semantic-simplex rank analyzer and the exact-payload Q8 geometry
finalizer, reconstructs the admitted family-energy-balanced 1D/2D basis, applies a frozen
calibration magnitude envelope to continuous coordinates, and serializes the result into
the llama.cpp cvec layout used by the retained native harness.

No model is executed here. A generated cvec is a candidate intervention, not evidence of
semantic causality, J-Space runtime acceptance, HCU acceptance, EntityOS acceptance, or
training success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Any

import numpy as np

from tools import trigger1_native_q8_geometry_balance as geometry_v1
from tools import trigger1_native_q8_geometry_balance_v2 as geometry_v2
from tools import trigger1_semantic_simplex_rank_analyze as rank_analyzer

REQUEST_SCHEMA = "CLAY_TRIGGER1_NATIVE_Q8_SUBSPACE_CONTROL_REQUEST/v1"
OUTPUT_SCHEMA = "CLAY_TRIGGER1_NATIVE_Q8_SUBSPACE_CVEC_CANDIDATE/v1"
NATIVE_API = "llama_set_adapter_cvec"
TOKEN_SCOPE = "ALL_PROMPT_TOKENS"
EPS = 1e-12


class ControlError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def vector_sha_f64(vector: np.ndarray) -> str:
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


def _finite(value: Any, code: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ControlError(code)
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ControlError(code)
    return parsed


def _positive(value: Any, code: str) -> float:
    parsed = _finite(value, code)
    if parsed <= 0.0:
        raise ControlError(code)
    return parsed


def _bind_rank(payload: dict[str, Any], declared: dict[str, Any]) -> dict[str, Any]:
    recomputed = rank_analyzer.analyze(payload)
    if not isinstance(declared, dict) or declared.get("schema") != rank_analyzer.OUTPUT_SCHEMA:
        raise ControlError("DECLARED_RANK_RESULT_SCHEMA_INVALID")
    if declared != recomputed:
        raise ControlError("DECLARED_RANK_RESULT_DIFFERS_FROM_EXACT_RECOMPUTATION")
    if declared.get("verdict") not in geometry_v1.RANK_VERDICTS:
        raise ControlError("UNRESOLVED_RANK_HAS_NO_CONTROL_BASIS")
    return recomputed


def _bind_geometry(payload: dict[str, Any], rank_result: dict[str, Any], declared: dict[str, Any]) -> tuple[dict[str, Any], np.ndarray, np.ndarray | None]:
    recomputed = geometry_v2.finalize(payload, rank_result)
    if not isinstance(declared, dict) or declared.get("schema") != geometry_v2.SCHEMA:
        raise ControlError("DECLARED_GEOMETRY_RESULT_SCHEMA_INVALID")
    if declared != recomputed:
        raise ControlError("DECLARED_GEOMETRY_RESULT_DIFFERS_FROM_EXACT_RECOMPUTATION")

    families, grouped, dimension = geometry_v1._parse(payload)
    rank = int(recomputed["rank"])
    balanced = geometry_v1._geometry_from_family_rows(families, grouped, energy_balance=True, rank=rank)
    axis1 = np.asarray(balanced["axis1"], dtype=np.float64)
    axis2 = None if balanced["axis2"] is None else np.asarray(balanced["axis2"], dtype=np.float64)
    if axis1.shape != (dimension,) or not np.all(np.isfinite(axis1)):
        raise ControlError("RECONSTRUCTED_AXIS1_INVALID")
    if vector_sha_f64(axis1) != recomputed.get("balanced_axis_h1_sha256_f64le"):
        raise ControlError("AXIS1_HASH_BINDING_FAILED")
    expected_h2 = recomputed.get("balanced_axis_h2_sha256_f64le")
    if rank == 2:
        if axis2 is None or axis2.shape != (dimension,) or not np.all(np.isfinite(axis2)):
            raise ControlError("RECONSTRUCTED_AXIS2_INVALID")
        if vector_sha_f64(axis2) != expected_h2:
            raise ControlError("AXIS2_HASH_BINDING_FAILED")
        if abs(float(np.dot(axis1, axis2))) > 1e-8:
            raise ControlError("RECONSTRUCTED_BASIS_NOT_ORTHOGONAL")
    elif expected_h2 is not None:
        raise ControlError("RANK1_GEOMETRY_MUST_NOT_DECLARE_AXIS2")
    return recomputed, axis1, axis2


def _validate_request(request: Any, rank_result: dict[str, Any], geometry_result: dict[str, Any], dimension: int) -> tuple[float, float, dict[str, Any], dict[str, Any]]:
    if not isinstance(request, dict) or request.get("schema") != REQUEST_SCHEMA:
        raise ControlError("CONTROL_REQUEST_SCHEMA_INVALID")
    if request.get("rank_analysis_receipt_sha256") != rank_result.get("analysis_receipt_sha256"):
        raise ControlError("CONTROL_REQUEST_RANK_RECEIPT_MISMATCH")
    if request.get("geometry_receipt_sha256") != geometry_result.get("geometry_receipt_sha256"):
        raise ControlError("CONTROL_REQUEST_GEOMETRY_RECEIPT_MISMATCH")

    coords = request.get("coordinates")
    if not isinstance(coords, dict):
        raise ControlError("CONTINUOUS_COORDINATES_REQUIRED")
    c1 = _finite(coords.get("h1"), "H1_COORDINATE_REQUIRED")
    c2 = _finite(coords.get("h2", 0.0), "H2_COORDINATE_INVALID")
    rank = int(geometry_result["rank"])
    if rank == 1 and abs(c2) > EPS:
        raise ControlError("H2_COORDINATE_FORBIDDEN_UNDER_RANK1")
    if math.hypot(c1, c2) <= EPS:
        raise ControlError("ZERO_SUBSPACE_VECTOR_FORBIDDEN")

    policy = request.get("magnitude_policy")
    if not isinstance(policy, dict):
        raise ControlError("MAGNITUDE_POLICY_REQUIRED")
    if policy.get("selected_on_calibration_only") is not True or policy.get("frozen_before_holdout") is not True:
        raise ControlError("MAGNITUDE_POLICY_MUST_BE_FROZEN_FROM_CALIBRATION_ONLY")
    if not _sha256(policy.get("operating_point_receipt_sha256")):
        raise ControlError("MAGNITUDE_OPERATING_POINT_RECEIPT_REQUIRED")
    max_l2 = _positive(policy.get("max_vector_l2"), "MAGNITUDE_MAX_VECTOR_L2_REQUIRED")
    residual_reference = _positive(policy.get("residual_norm_reference"), "MAGNITUDE_RESIDUAL_REFERENCE_REQUIRED")
    max_ratio = _positive(policy.get("max_residual_norm_ratio"), "MAGNITUDE_MAX_RESIDUAL_RATIO_REQUIRED")
    if max_ratio > 1.0:
        raise ControlError("MAGNITUDE_MAX_RESIDUAL_RATIO_MUST_NOT_EXCEED_ONE")
    normalized_policy = {
        "selected_on_calibration_only": True,
        "frozen_before_holdout": True,
        "operating_point_receipt_sha256": policy["operating_point_receipt_sha256"],
        "max_vector_l2": max_l2,
        "residual_norm_reference": residual_reference,
        "max_residual_norm_ratio": max_ratio,
    }

    target = request.get("native_target")
    if not isinstance(target, dict):
        raise ControlError("NATIVE_TARGET_REQUIRED")
    if target.get("api_symbol") != NATIVE_API:
        raise ControlError("NATIVE_API_SYMBOL_INVALID")
    if target.get("native_runtime_observed") is not False:
        raise ControlError("PREEXECUTION_REQUEST_MUST_NOT_PRECLAIM_RUNTIME")
    for key in ("runtime_build_sha256", "gguf_sha256", "tokenizer_sha256", "mapping_receipt_sha256", "conversion_receipt_sha256"):
        if not _sha256(target.get(key)):
            raise ControlError(f"NATIVE_TARGET_{key.upper()}_REQUIRED")
    if not _git_sha(target.get("llama_cpp_source_commit")):
        raise ControlError("NATIVE_TARGET_LLAMA_CPP_SOURCE_COMMIT_REQUIRED")
    for key in ("n_embd", "n_layer", "layer_start", "layer_end", "source_layer"):
        if not isinstance(target.get(key), int) or isinstance(target.get(key), bool):
            raise ControlError(f"NATIVE_TARGET_{key.upper()}_REQUIRED")
    if target["n_embd"] != dimension:
        raise ControlError("NATIVE_TARGET_EMBEDDING_DIMENSION_MISMATCH")
    if target["n_layer"] < 2 or not (1 <= target["layer_start"] <= target["layer_end"] < target["n_layer"]):
        raise ControlError("NATIVE_TARGET_LAYER_RANGE_INVALID")
    if target.get("token_scope") != TOKEN_SCOPE:
        raise ControlError("NATIVE_TARGET_TOKEN_SCOPE_MUST_BE_ALL_PROMPT_TOKENS")
    if not isinstance(target.get("mapping_semantics"), str) or not target["mapping_semantics"].strip():
        raise ControlError("NATIVE_TARGET_MAPPING_SEMANTICS_REQUIRED")
    return c1, c2, normalized_policy, target


def _serialize(vector: np.ndarray, *, n_embd: int, n_layer: int, layer_start: int, layer_end: int) -> bytes:
    raw = np.asarray(vector, dtype=np.float32)
    if raw.shape != (n_embd,) or not np.all(np.isfinite(raw)):
        raise ControlError("CONTROL_VECTOR_SERIALIZATION_INPUT_INVALID")
    chunk = b"".join(struct.pack("<f", float(x)) for x in raw.tolist())
    zero = b"\x00" * (4 * n_embd)
    payload = b"".join(chunk if layer_start <= layer <= layer_end else zero for layer in range(1, n_layer))
    if len(payload) != (n_layer - 1) * n_embd * 4:
        raise ControlError("NATIVE_CVEC_LAYOUT_LENGTH_INVARIANT_FAILED")
    return payload


def build(payload: dict[str, Any], declared_rank: dict[str, Any], declared_geometry: dict[str, Any], request: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    rank_result = _bind_rank(payload, declared_rank)
    geometry_result, axis1, axis2 = _bind_geometry(payload, rank_result, declared_geometry)
    dimension = int(geometry_result["dimension"])
    c1, c2, policy, target = _validate_request(request, rank_result, geometry_result, dimension)

    vector = c1 * axis1
    if int(geometry_result["rank"]) == 2:
        assert axis2 is not None
        vector = vector + c2 * axis2
    vector = np.asarray(vector, dtype=np.float64)
    l2 = float(np.linalg.norm(vector))
    residual_ratio = l2 / float(policy["residual_norm_reference"])
    if l2 > float(policy["max_vector_l2"]) + 1e-12:
        raise ControlError("CONTROL_VECTOR_EXCEEDS_FROZEN_L2_ENVELOPE")
    if residual_ratio > float(policy["max_residual_norm_ratio"]) + 1e-12:
        raise ControlError("CONTROL_VECTOR_EXCEEDS_FROZEN_RESIDUAL_RATIO_ENVELOPE")

    cvec = _serialize(
        vector,
        n_embd=int(target["n_embd"]),
        n_layer=int(target["n_layer"]),
        layer_start=int(target["layer_start"]),
        layer_end=int(target["layer_end"]),
    )
    f32 = np.asarray(vector, dtype="<f4").tobytes()
    core = {
        "schema": OUTPUT_SCHEMA,
        "truth_status": "CANDIDATE_MEASUREMENT_ONLY",
        "canonical_truth": False,
        "activation_payload_sha256": rank_result["input_sha256"],
        "rank_analysis_receipt_sha256": rank_result["analysis_receipt_sha256"],
        "geometry_receipt_sha256": geometry_result["geometry_receipt_sha256"],
        "rank_verdict": rank_result["verdict"],
        "basis": {
            "dimension": int(geometry_result["rank"]),
            "axis_h1_sha256_f64le": vector_sha_f64(axis1),
            "axis_h2_sha256_f64le": vector_sha_f64(axis2) if axis2 is not None else None,
            "family_weighting": geometry_result["family_weighting"],
        },
        "coordinates": {"h1": c1, "h2": c2},
        "vector": {
            "dimension": dimension,
            "l2": l2,
            "residual_norm_ratio": residual_ratio,
            "sha256_f64le": vector_sha_f64(vector),
            "sha256_f32le": hashlib.sha256(f32).hexdigest(),
        },
        "magnitude_policy": policy,
        "native_target": target,
        "native_cvec": {
            "layout": "LLAMA_CPP_LAYER_MAJOR_F32LE_LAYERS_1_TO_N_MINUS_1",
            "api_symbol": NATIVE_API,
            "token_scope": TOKEN_SCOPE,
            "float_count": len(cvec) // 4,
            "byte_count": len(cvec),
            "sha256_f32le": hashlib.sha256(cvec).hexdigest(),
            "native_runtime_observed": False,
        },
        "semantic_causality_established": False,
        "promotion_candidate": False,
        "jspace_model_runtime_credit": 0,
        "hcu_full_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
        "training_credit": 0,
        "canonical_semantics_promotion": False,
        "next_gate": "Execute the exact frozen cvec on an admitted native runtime and evaluate unopened matched holdout families across coordinate/direction x requested semantic target x counterbalanced output code with baseline/sign/null/orthogonal/permuted/label-only-nuisance controls, target/off-target drift, residual-norm binding, explicit native token-scope classification, and context-bound dual readout.",
        "evidence_boundary": "This deterministically maps canonical calibration geometry plus continuous coordinates into native llama.cpp cvec bytes. It executes no model and does not establish semantic causality.",
    }
    return {**core, "candidate_receipt_sha256": canonical_sha(core)}, cvec


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activations", required=True, type=Path)
    parser.add_argument("--rank-result", required=True, type=Path)
    parser.add_argument("--geometry-result", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cvec-output", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(args.activations.read_text(encoding="utf-8"))
    rank_result = json.loads(args.rank_result.read_text(encoding="utf-8"))
    geometry_result = json.loads(args.geometry_result.read_text(encoding="utf-8"))
    request = json.loads(args.request.read_text(encoding="utf-8"))
    result, cvec = build(payload, rank_result, geometry_result, request)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    args.cvec_output.write_bytes(cvec)
    print(json.dumps({"schema": result["schema"], "candidate_receipt_sha256": result["candidate_receipt_sha256"], "cvec_sha256": result["native_cvec"]["sha256_f32le"], "byte_count": result["native_cvec"]["byte_count"], "native_runtime_observed": False, "semantic_causality_established": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
