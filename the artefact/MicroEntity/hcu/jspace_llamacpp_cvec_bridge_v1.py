#!/usr/bin/env python3
"""Exact J-Space -> llama.cpp control-vector buffer bridge for EntityOS/HCU.

This module translates one already-admitted ``JSPACE_VECTOR_CONTROL_ABI/v1`` packet into
an exact float32 layer-major buffer consumable by llama.cpp ``llama_set_adapter_cvec``.
It is deterministic source/evidence plumbing only. It does not load a model, perform
inference, prove hidden-state efficacy, create canonical truth, or authorize effects.

Pinned zero-cost candidate targeted by the convenience constructor:
- Qwen/Qwen3-0.6B-GGUF, Q8_0
- checkpoint SHA-256 9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031
- llama.cpp source b95502ba9aa0eb73a2f4fc8878d7fbe6a847a0b9
- Qwen3-0.6B: n_embd=1024, n_layer=28

At the pinned llama.cpp source identity, control-vector storage has no layer-0 tensor;
``llama_adapter_cvec::apply`` consumes layer-major chunks using
``off = n_embd * (il - 1)`` for layers 1..n_layer-1. The Qwen3 graph applies
``build_cvec(cur, il)`` to the residual layer output before it becomes the next layer input.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
import struct
from typing import Any

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
    from .jspace_vector_control_v1 import VectorControlPacket, decode_vector, validate_packet
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize
    from jspace_vector_control_v1 import VectorControlPacket, decode_vector, validate_packet

SCHEMA = "ENTITYOS_HCU_JSPACE_LLAMA_CPP_CVEC_BINDING/v1"
LAYOUT_SCHEMA = "LLAMA_CPP_CVEC_LAYER_MAJOR_F32LE_NO_LAYER0/v1"
LLAMA_API = "llama_set_adapter_cvec"

QWEN3_06B_CHECKPOINT_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
QWEN3_06B_LLAMA_CPP_SOURCE_COMMIT = "b95502ba9aa0eb73a2f4fc8878d7fbe6a847a0b9"
QWEN3_06B_N_EMBD = 1024
QWEN3_06B_N_LAYER = 28
MAX_ABS_STRENGTH = 64.0
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class LlamaCppCVecBridgeError(ValueError):
    pass


@dataclass(frozen=True)
class LlamaCppCVecBinding:
    schema: str
    layout_schema: str
    llama_api: str
    generation: int
    vector_control_packet_sha256: str
    vector_control_condition: str
    basis_id: str
    basis_sha256: str
    role: str
    checkpoint_sha256: str
    llama_cpp_source_commit: str
    n_embd: int
    n_layer: int
    il_start: int
    il_end: int
    strength: float
    float_count: int
    byte_count: int
    cvec_f32le_sha256: str
    binding_sha256: str


def _sha256_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise LlamaCppCVecBridgeError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if any(ch not in "0123456789abcdef" for ch in value):
        raise LlamaCppCVecBridgeError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise LlamaCppCVecBridgeError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _commit(value: Any) -> str:
    if not isinstance(value, str) or len(value) != 40 or value.lower() != value:
        raise LlamaCppCVecBridgeError("llama_cpp_source_commit:LOWERCASE_GIT_SHA1_REQUIRED")
    if any(ch not in "0123456789abcdef" for ch in value):
        raise LlamaCppCVecBridgeError("llama_cpp_source_commit:LOWERCASE_GIT_SHA1_REQUIRED")
    if value in {"0" * 40, "f" * 40}:
        raise LlamaCppCVecBridgeError("llama_cpp_source_commit:PLACEHOLDER_GIT_SHA1_FORBIDDEN")
    return value


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise LlamaCppCVecBridgeError(f"{field}:POSITIVE_INTEGER_REQUIRED")
    if value > MAX_SAFE_INTEGER:
        raise LlamaCppCVecBridgeError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _strength(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LlamaCppCVecBridgeError("strength:FINITE_NUMBER_REQUIRED")
    value = float(value)
    if not math.isfinite(value):
        raise LlamaCppCVecBridgeError("strength:FINITE_NUMBER_REQUIRED")
    if abs(value) > MAX_ABS_STRENGTH:
        raise LlamaCppCVecBridgeError("strength:ABS_BOUND_EXCEEDED")
    return 0.0 if value == 0.0 else value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise LlamaCppCVecBridgeError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _binding_material(binding: LlamaCppCVecBinding) -> dict[str, Any]:
    material = asdict(binding)
    material.pop("binding_sha256", None)
    return material


def _validate_shape(n_embd: Any, n_layer: Any, il_start: Any, il_end: Any) -> tuple[int, int, int, int]:
    n_embd = _positive_int(n_embd, "n_embd")
    n_layer = _positive_int(n_layer, "n_layer")
    if n_layer < 2:
        raise LlamaCppCVecBridgeError("n_layer:AT_LEAST_TWO_REQUIRED")
    if isinstance(il_start, bool) or not isinstance(il_start, int):
        raise LlamaCppCVecBridgeError("il_start:INTEGER_REQUIRED")
    if isinstance(il_end, bool) or not isinstance(il_end, int):
        raise LlamaCppCVecBridgeError("il_end:INTEGER_REQUIRED")
    if not (1 <= il_start <= il_end < n_layer):
        raise LlamaCppCVecBridgeError("layer_range:MUST_BE_WITHIN_1_TO_N_LAYER_MINUS_1")
    return n_embd, n_layer, il_start, il_end


def _pack_controlled_chunk(decoded: tuple[float, ...], strength: float) -> bytes:
    values: list[bytes] = []
    for value in decoded:
        scaled = float(value) * strength
        if not math.isfinite(scaled):
            raise LlamaCppCVecBridgeError("SCALED_CONTROL_VECTOR_NONFINITE")
        try:
            values.append(struct.pack("<f", scaled))
        except (OverflowError, struct.error) as exc:
            raise LlamaCppCVecBridgeError("SCALED_CONTROL_VECTOR_BINARY32_RANGE_REQUIRED") from exc
    return b"".join(values)


def _raw_from_packet(
    packet: VectorControlPacket,
    *,
    n_embd: int,
    n_layer: int,
    il_start: int,
    il_end: int,
    strength: float,
) -> bytes:
    decoded = decode_vector(
        packet,
        current_generation=packet.generation,
        expected_basis_id=packet.basis_id,
        expected_basis_sha256=packet.basis_sha256,
        expected_role=packet.role,
        expected_control_condition=packet.control_condition,
    )
    if len(decoded) != n_embd:
        raise LlamaCppCVecBridgeError("VECTOR_DIMENSION_MUST_EQUAL_MODEL_N_EMBD")
    controlled_chunk = _pack_controlled_chunk(decoded, strength)
    zero_chunk = b"\x00" * (4 * n_embd)
    return b"".join(
        controlled_chunk if il_start <= il <= il_end else zero_chunk
        for il in range(1, n_layer)
    )


def build_llamacpp_cvec_buffer(
    packet: VectorControlPacket,
    *,
    current_generation: int,
    expected_basis_id: str,
    expected_basis_sha256: str,
    expected_role: str,
    checkpoint_sha256: str,
    llama_cpp_source_commit: str,
    n_embd: int,
    n_layer: int,
    il_start: int,
    il_end: int,
    strength: float = 1.0,
) -> tuple[bytes, LlamaCppCVecBinding]:
    """Build the exact F32LE buffer and a self-authenticating binding.

    The output contains one chunk for each llama.cpp control-vector tensor layer
    ``1..n_layer-1``. Selected chunks contain ``decoded_jspace_vector * strength``;
    chunks outside ``[il_start, il_end]`` are all-zero. Layer 0 is intentionally absent.
    """
    validate_packet(packet)
    # Enforce the caller's current causal fences before converting anything into a model input.
    decode_vector(
        packet,
        current_generation=current_generation,
        expected_basis_id=expected_basis_id,
        expected_basis_sha256=expected_basis_sha256,
        expected_role=expected_role,
    )
    checkpoint_sha256 = _sha256_text(checkpoint_sha256, "checkpoint_sha256")
    llama_cpp_source_commit = _commit(llama_cpp_source_commit)
    n_embd, n_layer, il_start, il_end = _validate_shape(n_embd, n_layer, il_start, il_end)
    strength = _strength(strength)

    raw = _raw_from_packet(
        packet,
        n_embd=n_embd,
        n_layer=n_layer,
        il_start=il_start,
        il_end=il_end,
        strength=strength,
    )
    float_count = (n_layer - 1) * n_embd
    if len(raw) != float_count * 4:
        raise AssertionError("internal cvec buffer length invariant violated")

    material = {
        "schema": SCHEMA,
        "layout_schema": LAYOUT_SCHEMA,
        "llama_api": LLAMA_API,
        "generation": packet.generation,
        "vector_control_packet_sha256": packet.packet_sha256,
        "vector_control_condition": packet.control_condition,
        "basis_id": packet.basis_id,
        "basis_sha256": packet.basis_sha256,
        "role": packet.role,
        "checkpoint_sha256": checkpoint_sha256,
        "llama_cpp_source_commit": llama_cpp_source_commit,
        "n_embd": n_embd,
        "n_layer": n_layer,
        "il_start": il_start,
        "il_end": il_end,
        "strength": strength,
        "float_count": float_count,
        "byte_count": len(raw),
        "cvec_f32le_sha256": hashlib.sha256(raw).hexdigest(),
    }
    provisional = LlamaCppCVecBinding(**material, binding_sha256="1" * 64)
    binding = LlamaCppCVecBinding(
        **material,
        binding_sha256=_canonical_sha256(_binding_material(provisional), "LLAMA_CPP_CVEC_BINDING"),
    )
    validate_llamacpp_cvec_binding(binding, raw, packet)
    return raw, binding


def build_qwen3_06b_candidate_cvec(
    packet: VectorControlPacket,
    *,
    current_generation: int,
    expected_basis_id: str,
    expected_basis_sha256: str,
    expected_role: str,
    il_start: int,
    il_end: int,
    strength: float = 1.0,
) -> tuple[bytes, LlamaCppCVecBinding]:
    """Exact-source convenience wrapper for the already-pinned Qwen3-0.6B candidate."""
    return build_llamacpp_cvec_buffer(
        packet,
        current_generation=current_generation,
        expected_basis_id=expected_basis_id,
        expected_basis_sha256=expected_basis_sha256,
        expected_role=expected_role,
        checkpoint_sha256=QWEN3_06B_CHECKPOINT_SHA256,
        llama_cpp_source_commit=QWEN3_06B_LLAMA_CPP_SOURCE_COMMIT,
        n_embd=QWEN3_06B_N_EMBD,
        n_layer=QWEN3_06B_N_LAYER,
        il_start=il_start,
        il_end=il_end,
        strength=strength,
    )


def validate_llamacpp_cvec_binding(
    binding: LlamaCppCVecBinding,
    raw: bytes,
    packet: VectorControlPacket,
) -> None:
    """Recompute semantics and exact bytes; fail closed on any caller-minted alias."""
    if not isinstance(binding, LlamaCppCVecBinding):
        raise LlamaCppCVecBridgeError("LLAMA_CPP_CVEC_BINDING_REQUIRED")
    if not isinstance(raw, bytes):
        raise LlamaCppCVecBridgeError("CVEC_RAW_BYTES_REQUIRED")
    validate_packet(packet)
    if binding.schema != SCHEMA or binding.layout_schema != LAYOUT_SCHEMA or binding.llama_api != LLAMA_API:
        raise LlamaCppCVecBridgeError("LLAMA_CPP_CVEC_SCHEMA_UNSUPPORTED")

    _sha256_text(binding.checkpoint_sha256, "checkpoint_sha256")
    _commit(binding.llama_cpp_source_commit)
    n_embd, n_layer, il_start, il_end = _validate_shape(
        binding.n_embd, binding.n_layer, binding.il_start, binding.il_end
    )
    strength = _strength(binding.strength)
    expected_float_count = (n_layer - 1) * n_embd
    if binding.float_count != expected_float_count:
        raise LlamaCppCVecBridgeError("CVEC_FLOAT_COUNT_MISMATCH")
    if binding.byte_count != expected_float_count * 4:
        raise LlamaCppCVecBridgeError("CVEC_BYTE_COUNT_MISMATCH")
    _sha256_text(binding.cvec_f32le_sha256, "cvec_f32le_sha256")

    if binding.vector_control_packet_sha256 != packet.packet_sha256:
        raise LlamaCppCVecBridgeError("VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH")
    if binding.generation != packet.generation:
        raise LlamaCppCVecBridgeError("GENERATION_MISMATCH")
    if binding.vector_control_condition != packet.control_condition:
        raise LlamaCppCVecBridgeError("CONTROL_CONDITION_MISMATCH")
    if binding.basis_id != packet.basis_id or binding.basis_sha256 != packet.basis_sha256:
        raise LlamaCppCVecBridgeError("JSPACE_BASIS_IDENTITY_MISMATCH")
    if binding.role != packet.role:
        raise LlamaCppCVecBridgeError("ROLE_MISMATCH")

    expected_raw = _raw_from_packet(
        packet,
        n_embd=n_embd,
        n_layer=n_layer,
        il_start=il_start,
        il_end=il_end,
        strength=strength,
    )
    if raw != expected_raw:
        raise LlamaCppCVecBridgeError("CVEC_BUFFER_SEMANTIC_REVALIDATION_MISMATCH")
    if len(raw) != binding.byte_count:
        raise LlamaCppCVecBridgeError("CVEC_BUFFER_SIZE_MISMATCH")
    if hashlib.sha256(raw).hexdigest() != binding.cvec_f32le_sha256:
        raise LlamaCppCVecBridgeError("CVEC_BUFFER_DIGEST_MISMATCH")
    observed = _sha256_text(binding.binding_sha256, "binding_sha256")
    expected = _canonical_sha256(_binding_material(binding), "LLAMA_CPP_CVEC_BINDING")
    if observed != expected:
        raise LlamaCppCVecBridgeError("LLAMA_CPP_CVEC_BINDING_DIGEST_MISMATCH")
