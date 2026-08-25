#!/usr/bin/env python3
"""Emit llama.cpp cvec bytes from evidence-bound family-balanced Q8 geometry.

This is the actuation-byte successor to trigger1_native_q8_geometry_balance_v2.  It does
not estimate rank independently, tune gain, run a model, or open holdout.  It recomputes
and binds the canonical rank on the exact activation payload through geometry v2, rebuilds
the equal-family-energy semantic vectors, verifies those vectors against the v2 geometry
receipt, and only then serializes them into the pinned Qwen3-0.6B llama.cpp cvec layout.

The emitted vectors are unitless geometry vectors.  A common calibration-only scalar gain
must be applied separately; this tool intentionally cannot choose it.  Output files therefore
represent the semantic direction/simplex geometry, not an authorized intervention by itself.

No runtime, J-Space-model, HCU, EntityOS, training, canonical-semantics, or effect credit is
minted by this source-only serializer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

import numpy as np

from tools import trigger1_native_q8_geometry_balance as geometry_v1
from tools import trigger1_native_q8_geometry_balance_v2 as geometry_v2

SCHEMA = "CLAY_TRIGGER1_NATIVE_Q8_FAMILY_BALANCED_CVEC_EMISSION/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
N_EMBD = 1024
N_LAYER = 28
INJECTION_LAYER = 20
PINNED_GGUF_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
PINNED_LLAMA_CPP_COMMIT = "bb4caa7540188872173c44d161602d9271386413"


class EmitError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def vector_sha_f64(vector: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vector, dtype="<f8").tobytes()).hexdigest()


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


def _git_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def validate_runtime_identity(identity: Any) -> dict[str, str]:
    if not isinstance(identity, dict):
        raise EmitError("RUNTIME_IDENTITY_OBJECT_REQUIRED")
    gguf = identity.get("gguf_sha256")
    llama_commit = identity.get("llama_cpp_commit")
    harness = identity.get("native_capture_harness_sha256")
    if gguf != PINNED_GGUF_SHA256:
        raise EmitError("PINNED_GGUF_SHA256_MISMATCH")
    if llama_commit != PINNED_LLAMA_CPP_COMMIT or not _git_sha(llama_commit):
        raise EmitError("PINNED_LLAMA_CPP_COMMIT_MISMATCH")
    if not _sha256(harness):
        raise EmitError("NATIVE_CAPTURE_HARNESS_SHA256_REQUIRED")
    return {
        "gguf_sha256": gguf,
        "llama_cpp_commit": llama_commit,
        "native_capture_harness_sha256": harness,
    }


def cvec_bytes(vector: np.ndarray, *, n_embd: int = N_EMBD, n_layer: int = N_LAYER, injection_layer: int = INJECTION_LAYER) -> bytes:
    values = np.asarray(vector, dtype="<f4")
    if values.shape != (n_embd,):
        raise EmitError(f"VECTOR_DIMENSION_MISMATCH:{values.shape}!={(n_embd,)}")
    if not np.all(np.isfinite(values)):
        raise EmitError("VECTOR_NONFINITE")
    if n_layer <= 1 or not (1 <= injection_layer < n_layer):
        raise EmitError("CVEC_LAYER_LAYOUT_INVALID")
    chunk = values.tobytes(order="C")
    zero = b"\x00" * (4 * n_embd)
    raw = b"".join(chunk if il == injection_layer else zero for il in range(1, n_layer))
    expected = (n_layer - 1) * n_embd * 4
    if len(raw) != expected:
        raise EmitError("CVEC_BYTE_COUNT_INVARIANT_FAILED")
    return raw


def _balanced_vectors(payload: dict[str, Any], bound_geometry: dict[str, Any]) -> dict[str, np.ndarray]:
    families, grouped, dimension = geometry_v1._parse(payload)
    if dimension != N_EMBD:
        raise EmitError(f"PINNED_Q8_DIMENSION_REQUIRED:{dimension}!={N_EMBD}")
    rank = bound_geometry.get("rank")
    if rank not in (1, 2):
        raise EmitError("BOUND_GEOMETRY_RANK_INVALID")
    raw = geometry_v1._geometry_from_family_rows(
        families,
        grouped,
        energy_balance=True,
        rank=int(rank),
    )
    vectors = raw["vectors"]
    for semantic in CLASSES:
        expected = bound_geometry.get("balanced_target_vectors", {}).get(semantic, {}).get("vector_sha256_f64le")
        observed = vector_sha_f64(vectors[semantic])
        if expected != observed:
            raise EmitError(f"BALANCED_VECTOR_GEOMETRY_RECEIPT_MISMATCH:{semantic}")
    residual = float(np.linalg.norm(sum(vectors.values())))
    if residual > 1e-9:
        raise EmitError(f"TARGET_VECTOR_ZERO_SUM_INVARIANT_FAILED:{residual}")
    return vectors


def emit(
    payload: dict[str, Any],
    declared_rank: dict[str, Any],
    runtime_identity: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    identity = validate_runtime_identity(runtime_identity)
    bound_geometry = geometry_v2.finalize(payload, declared_rank)
    vectors = _balanced_vectors(payload, bound_geometry)

    output_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    for semantic in CLASSES:
        vector = vectors[semantic]
        raw = cvec_bytes(vector)
        path = output_dir / f"target-{semantic.lower()}.family-balanced.cvec.f32le"
        path.write_bytes(raw)
        files[semantic] = {
            "filename": path.name,
            "vector_sha256_f64le": vector_sha_f64(vector),
            "serialized_vector_sha256_f32le": vector_sha_f32(vector),
            "serialized_vector_l2_f32": float(np.linalg.norm(np.asarray(vector, dtype=np.float32))),
            "cvec_sha256": hashlib.sha256(raw).hexdigest(),
            "cvec_bytes": len(raw),
            "cvec_float_count": len(raw) // 4,
            "injection_layer": INJECTION_LAYER,
            "nonzero_layer_blocks": [INJECTION_LAYER],
        }

    core = {
        "schema": SCHEMA,
        "runtime_identity": identity,
        "activation_payload_sha256": canonical_sha(payload),
        "rank_analysis_receipt_sha256": bound_geometry["rank_binding"]["recomputed_rank_analysis_receipt_sha256"],
        "geometry_receipt_sha256": bound_geometry["geometry_receipt_sha256"],
        "geometry_schema": bound_geometry["schema"],
        "rank": bound_geometry["rank"],
        "rank_verdict": bound_geometry["rank_verdict"],
        "family_weighting": bound_geometry["family_weighting"],
        "raw_vs_balanced_diagnostic": bound_geometry["raw_vs_balanced_diagnostic"],
        "n_embd": N_EMBD,
        "n_layer": N_LAYER,
        "injection_layer": INJECTION_LAYER,
        "target_cvecs": files,
        "common_gain_required": True,
        "gain_selected_here": False,
        "gain_value": None,
        "holdout_opened": False,
        "model_executed": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "full_hcu_runtime_credit": False,
        "whole_entityos_hcu_runtime_credit": False,
        "training_credit": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "Source-only serialization of exact-payload-bound, family-energy-balanced calibration geometry "
            "into the pinned Qwen3-0.6B Q8_0 llama.cpp cvec layout. The files are not an intervention and "
            "carry no semantic/runtime/system credit until an independently authorized execution binds the "
            "exact emitted digest, calibration-only gain, case universe, transport and behavioral evidence."
        ),
    }
    return {**core, "emission_receipt_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--activation-payload", required=True)
    ap.add_argument("--rank-result", required=True)
    ap.add_argument("--runtime-identity", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    payload = json.loads(Path(args.activation_payload).read_text(encoding="utf-8"))
    rank = json.loads(Path(args.rank_result).read_text(encoding="utf-8"))
    identity = json.loads(Path(args.runtime_identity).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    receipt = emit(payload, rank, identity, output_dir)
    (output_dir / "family-balanced-cvec-emission.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "schema": receipt["schema"],
        "rank": receipt["rank"],
        "geometry_receipt_sha256": receipt["geometry_receipt_sha256"],
        "emission_receipt_sha256": receipt["emission_receipt_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
