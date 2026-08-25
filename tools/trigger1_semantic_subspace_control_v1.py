#!/usr/bin/env python3
"""Deterministic semantic-subspace coordinate -> native llama.cpp cvec candidate builder.

This source-only controller is the bridge from a frozen blocked semantic-simplex rank
measurement to an executable native control vector. It recomputes the rank result from the
same BASIS/CALIBRATION activations, reconstructs the orthonormal h1/h2 basis, applies a
preregistered residual-norm-relative magnitude envelope, and serializes the requested
coordinate into the llama.cpp cvec layout used by the retained native harness.

It never executes a model and never claims that a requested coordinate causes the requested
semantic behavior. Native semantic causality still requires unopened matched holdout families,
all matched controls, context-bound readout, and an observed llama_set_adapter_cvec receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import trigger1_semantic_simplex_blocked_rank_v1 as ranker

REQUEST_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SUBSPACE_CONTROL_REQUEST/v1"
OUTPUT_SCHEMA = "JSPACE_SEMANTIC_SUBSPACE_CONTROL_CANDIDATE/v1"
NATIVE_API = "llama_set_adapter_cvec"
EPS = 1e-12


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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
        raise ValueError(code)
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(code)
    return parsed


def _positive(value: Any, code: str) -> float:
    parsed = _finite(value, code)
    if parsed <= 0.0:
        raise ValueError(code)
    return parsed


def _validate_native_target(target: Any, source: dict[str, Any], dim: int) -> dict[str, Any]:
    if not isinstance(target, dict):
        raise ValueError("NATIVE_TARGET_REQUIRED")
    if target.get("api_symbol") != NATIVE_API:
        raise ValueError("NATIVE_API_SYMBOL_INVALID")
    if target.get("native_runtime_observed") is not False:
        raise ValueError("PREEXECUTION_CONTROLLER_MUST_NOT_PRECLAIM_NATIVE_RUNTIME")
    if not isinstance(target.get("model_or_route"), str) or not target["model_or_route"].strip():
        raise ValueError("NATIVE_TARGET_MODEL_REQUIRED")
    for key in ("runtime_build_sha256", "gguf_sha256", "tokenizer_sha256", "mapping_receipt_sha256"):
        if not _sha256(target.get(key)):
            raise ValueError(f"NATIVE_TARGET_{key.upper()}_REQUIRED")
    if not _git_sha(target.get("llama_cpp_source_commit")):
        raise ValueError("NATIVE_TARGET_LLAMA_CPP_COMMIT_REQUIRED")
    n_embd = target.get("n_embd")
    n_layer = target.get("n_layer")
    il_start = target.get("layer_start")
    il_end = target.get("layer_end")
    for value, code in (
        (n_embd, "NATIVE_TARGET_N_EMBD_REQUIRED"),
        (n_layer, "NATIVE_TARGET_N_LAYER_REQUIRED"),
        (il_start, "NATIVE_TARGET_LAYER_START_REQUIRED"),
        (il_end, "NATIVE_TARGET_LAYER_END_REQUIRED"),
    ):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(code)
    if n_embd != dim:
        raise ValueError("NATIVE_TARGET_EMBEDDING_DIM_MISMATCH")
    if n_layer < 2:
        raise ValueError("NATIVE_TARGET_N_LAYER_INVALID")
    if not (1 <= il_start <= il_end < n_layer):
        raise ValueError("NATIVE_TARGET_LAYER_RANGE_INVALID")
    if target.get("token_scope") != "ALL_PROMPT_TOKENS":
        raise ValueError("NATIVE_CVEC_TOKEN_SCOPE_MUST_BE_ALL_PROMPT_TOKENS")
    if target.get("source_layer") != source.get("layer"):
        raise ValueError("NATIVE_TARGET_SOURCE_LAYER_MISMATCH")
    if not isinstance(target.get("mapping_semantics"), str) or not target["mapping_semantics"].strip():
        raise ValueError("NATIVE_TARGET_MAPPING_SEMANTICS_REQUIRED")
    return target


def _validate_magnitude_policy(policy: Any) -> dict[str, float | str | bool]:
    if not isinstance(policy, dict):
        raise ValueError("MAGNITUDE_POLICY_REQUIRED")
    if policy.get("selected_on_calibration_only") is not True:
        raise ValueError("MAGNITUDE_POLICY_MUST_BE_CALIBRATION_ONLY")
    if policy.get("frozen_before_holdout") is not True:
        raise ValueError("MAGNITUDE_POLICY_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(policy.get("operating_point_receipt_sha256")):
        raise ValueError("MAGNITUDE_POLICY_RECEIPT_REQUIRED")
    max_vector_l2 = _positive(policy.get("max_vector_l2"), "MAGNITUDE_MAX_VECTOR_L2_REQUIRED")
    residual_ref = _positive(policy.get("residual_norm_reference"), "MAGNITUDE_RESIDUAL_NORM_REFERENCE_REQUIRED")
    max_ratio = _positive(policy.get("max_residual_norm_ratio"), "MAGNITUDE_MAX_RESIDUAL_RATIO_REQUIRED")
    if max_ratio > 1.0:
        raise ValueError("MAGNITUDE_MAX_RESIDUAL_RATIO_MUST_NOT_EXCEED_ONE")
    return {
        "selected_on_calibration_only": True,
        "frozen_before_holdout": True,
        "operating_point_receipt_sha256": policy["operating_point_receipt_sha256"],
        "max_vector_l2": max_vector_l2,
        "residual_norm_reference": residual_ref,
        "max_residual_norm_ratio": max_ratio,
    }


def _coordinates(request: dict[str, Any], basis_dim: int) -> tuple[float, float]:
    coords = request.get("coordinates")
    if not isinstance(coords, dict):
        raise ValueError("SUBSPACE_COORDINATES_REQUIRED")
    h1 = _finite(coords.get("h1"), "H1_COORDINATE_REQUIRED")
    h2 = _finite(coords.get("h2", 0.0), "H2_COORDINATE_INVALID")
    if basis_dim == 1 and abs(h2) > EPS:
        raise ValueError("H2_COORDINATE_FORBIDDEN_UNDER_RANK1")
    if basis_dim not in {1, 2}:
        raise ValueError("RANK_DECISION_UNRESOLVED_NO_CONTROL_BASIS")
    if math.hypot(h1, h2) <= EPS:
        raise ValueError("ZERO_SUBSPACE_CONTROL_VECTOR_FORBIDDEN")
    return h1, h2


def _serialize_cvec(vector: np.ndarray, *, n_embd: int, n_layer: int, il_start: int, il_end: int) -> bytes:
    raw = np.asarray(vector, dtype=np.float32)
    if raw.ndim != 1 or raw.shape[0] != n_embd or not np.all(np.isfinite(raw)):
        raise ValueError("CONTROL_VECTOR_F32_SERIALIZATION_INVALID")
    chunk = b"".join(struct.pack("<f", float(x)) for x in raw.tolist())
    zero = b"\x00" * (4 * n_embd)
    payload = b"".join(chunk if il_start <= il <= il_end else zero for il in range(1, n_layer))
    expected = (n_layer - 1) * n_embd * 4
    if len(payload) != expected:
        raise ValueError("CVEC_BUFFER_LENGTH_INVARIANT")
    return payload


def build_candidate(activation_packet: dict[str, Any], rank_result: dict[str, Any], request: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    if not isinstance(activation_packet, dict) or not isinstance(rank_result, dict) or not isinstance(request, dict):
        raise ValueError("JSON_OBJECT_INPUTS_REQUIRED")
    if request.get("schema") != REQUEST_SCHEMA:
        raise ValueError("CONTROL_REQUEST_SCHEMA_INVALID")

    recomputed = ranker.analyze(activation_packet)
    if recomputed != rank_result:
        raise ValueError("RANK_RESULT_MUST_EQUAL_EXACT_RECOMPUTATION")
    if request.get("rank_result_sha256") != rank_result.get("result_sha256"):
        raise ValueError("CONTROL_REQUEST_RANK_RESULT_IDENTITY_MISMATCH")
    basis_dim = int(rank_result.get("selected_basis_dimension", 0))
    if basis_dim not in {1, 2}:
        raise ValueError("RANK_DECISION_UNRESOLVED_NO_CONTROL_BASIS")

    dim, families, _validation = ranker.validate_packet(activation_packet)
    geom = ranker.family_geometry(families)
    h1 = np.asarray(geom["h1"], dtype=np.float64)
    h2 = np.asarray(geom["h2"], dtype=np.float64)
    if ranker.vector_sha(h1) != rank_result["observed"].get("h1_sha256"):
        raise ValueError("H1_BASIS_HASH_RECOMPUTE_MISMATCH")
    if ranker.vector_sha(h2) != rank_result["observed"].get("h2_sha256"):
        raise ValueError("H2_BASIS_HASH_RECOMPUTE_MISMATCH")
    if abs(float(np.linalg.norm(h1)) - 1.0) > 1e-8:
        raise ValueError("H1_BASIS_NOT_UNIT")
    if basis_dim == 2:
        if abs(float(np.linalg.norm(h2)) - 1.0) > 1e-8:
            raise ValueError("H2_BASIS_NOT_UNIT")
        if abs(float(np.dot(h1, h2))) > 1e-8:
            raise ValueError("SEMANTIC_BASIS_NOT_ORTHOGONAL")

    c1, c2 = _coordinates(request, basis_dim)
    vector = c1 * h1 + (c2 * h2 if basis_dim == 2 else 0.0)
    vector = np.asarray(vector, dtype=np.float64)
    vector_l2 = float(np.linalg.norm(vector))
    policy = _validate_magnitude_policy(request.get("magnitude_policy"))
    residual_ratio = vector_l2 / float(policy["residual_norm_reference"])
    if vector_l2 > float(policy["max_vector_l2"]) + 1e-12:
        raise ValueError("CONTROL_VECTOR_EXCEEDS_CALIBRATED_L2_ENVELOPE")
    if residual_ratio > float(policy["max_residual_norm_ratio"]) + 1e-12:
        raise ValueError("CONTROL_VECTOR_EXCEEDS_RESIDUAL_NORM_RATIO_ENVELOPE")

    source = activation_packet["source_identity"]
    target = _validate_native_target(request.get("native_target"), source, dim)
    payload = _serialize_cvec(
        vector,
        n_embd=int(target["n_embd"]),
        n_layer=int(target["n_layer"]),
        il_start=int(target["layer_start"]),
        il_end=int(target["layer_end"]),
    )
    vector_f32 = np.asarray(vector, dtype="<f4")
    basis = {
        "dimension": basis_dim,
        "h1_f64le_sha256": ranker.vector_sha(h1),
        "h2_f64le_sha256": ranker.vector_sha(h2),
        "orthogonality_dot": float(np.dot(h1, h2)) if basis_dim == 2 else None,
        "derivation_rank_result_sha256": rank_result["result_sha256"],
        "derivation_input_sha256": rank_result["input_sha256"],
    }
    candidate = {
        "schema": OUTPUT_SCHEMA,
        "truth_status": "CANDIDATE_MEASUREMENT_ONLY",
        "canonical_truth": False,
        "source_identity": source,
        "source_identity_sha256": rank_result["source_identity_sha256"],
        "rank_decision": rank_result["decision"],
        "basis": basis,
        "control_request_sha256": canonical_sha(request),
        "coordinates": {"h1": c1, "h2": c2},
        "vector": {
            "dimension": dim,
            "l2": vector_l2,
            "residual_norm_ratio": residual_ratio,
            "f64le_sha256": ranker.vector_sha(vector),
            "f32le_sha256": hashlib.sha256(vector_f32.tobytes()).hexdigest(),
        },
        "magnitude_policy": policy,
        "native_target": target,
        "native_cvec": {
            "layout": "LLAMA_CPP_LAYER_MAJOR_F32LE_LAYERS_1_TO_N_MINUS_1",
            "api_symbol": NATIVE_API,
            "n_embd": int(target["n_embd"]),
            "n_layer": int(target["n_layer"]),
            "layer_start": int(target["layer_start"]),
            "layer_end": int(target["layer_end"]),
            "token_scope": "ALL_PROMPT_TOKENS",
            "float_count": len(payload) // 4,
            "byte_count": len(payload),
            "cvec_f32le_sha256": hashlib.sha256(payload).hexdigest(),
            "native_runtime_observed": False,
        },
        "semantic_causality_established": False,
        "promotion_candidate": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": 0,
        "hcu_full_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
        "training_credit": 0,
        "next_gate": "Execute this exact cvec on an admitted native runtime only after the control request and magnitude policy are frozen, then measure the full class-direction x requested-target matrix on unopened matched holdout families with sign/null/orthogonal/permuted/label-only nuisance controls and context-bound dual readout.",
        "evidence_boundary": "Coordinate-to-cvec construction is deterministic source/control-plane readiness only. No model was executed and semantic causality is not inferred from geometry.",
    }
    candidate["candidate_sha256"] = canonical_sha(candidate)
    return candidate, payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--activations", required=True, type=Path)
    ap.add_argument("--rank-result", required=True, type=Path)
    ap.add_argument("--request", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--cvec-output", required=True, type=Path)
    args = ap.parse_args()
    activation_packet = json.loads(args.activations.read_text(encoding="utf-8"))
    rank_result = json.loads(args.rank_result.read_text(encoding="utf-8"))
    request = json.loads(args.request.read_text(encoding="utf-8"))
    candidate, payload = build_candidate(activation_packet, rank_result, request)
    args.output.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    args.cvec_output.write_bytes(payload)
    print(json.dumps({
        "schema": "JSPACE_SEMANTIC_SUBSPACE_CONTROL_BUILD/v1",
        "status": "PASS",
        "candidate_sha256": candidate["candidate_sha256"],
        "cvec_f32le_sha256": candidate["native_cvec"]["cvec_f32le_sha256"],
        "byte_count": candidate["native_cvec"]["byte_count"],
        "native_runtime_observed": False,
        "semantic_causality_established": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
