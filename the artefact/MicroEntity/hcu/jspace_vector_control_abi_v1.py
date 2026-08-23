#!/usr/bin/env python3
"""Deterministic token/byte Vector Control ABI for EntityOS/HCU Global J-Space.

This is a control serialization boundary, not evidence of direct residual-stream injection.
It converts a finite binary64 vector into a versioned q8 packet that a text-token fine-tune
and the local HCU runtime can reproduce. Canonical truth/effect authority remains elsewhere.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import math
import struct
from typing import Any, Iterable, Sequence

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize

SCHEMA = "JSPACE_VECTOR_CONTROL_ABI/v1"
PACKET_PREFIX = b"<jctl:v1>"
PACKET_SUFFIX = b"</jctl>"
MAX_DIMENSIONS = 4096
MAX_WORKSPACE_REFS = 64
MAX_TEXT_BYTES = 256


class JSpaceVectorControlError(ValueError):
    pass


@dataclass(frozen=True)
class VectorControlPacket:
    schema: str
    basis_id: str
    role: str
    generation: int
    dimensions: int
    scale_f64_be_hex: str
    q8_b64url: str
    gate_u8: int
    workspace_refs: tuple[str, ...]
    lesion_indices: tuple[int, ...]
    null_vector: bool
    packet_bytes: bytes
    packet_sha256: str


@dataclass(frozen=True)
class DecodedVectorControl:
    schema: str
    basis_id: str
    role: str
    generation: int
    vector: tuple[float, ...]
    gate: float
    workspace_refs: tuple[str, ...]
    lesion_indices: tuple[int, ...]
    null_vector: bool
    packet_sha256: str


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceVectorControlError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value.encode("utf-8")) > MAX_TEXT_BYTES:
        raise JSpaceVectorControlError(f"{field}:TOO_LONG")
    return value


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceVectorControlError("generation:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _finite_binary64(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise JSpaceVectorControlError(f"{field}:FINITE_NUMBER_REQUIRED")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as exc:
        raise JSpaceVectorControlError(f"{field}:FINITE_BINARY64_REQUIRED") from exc
    if not math.isfinite(converted):
        raise JSpaceVectorControlError(f"{field}:FINITE_BINARY64_REQUIRED")
    return converted


def _canonical_sha256(value: Any) -> tuple[bytes, str]:
    try:
        body = canonicalize(value)
    except CanonicalizationError as exc:
        raise JSpaceVectorControlError(f"CANONICALIZATION_FAILED:{exc}") from exc
    return body, hashlib.sha256(PACKET_PREFIX + body + PACKET_SUFFIX).hexdigest()


def _normalize_workspace_refs(values: Iterable[str]) -> tuple[str, ...]:
    refs = tuple(sorted({_text(value, "workspace_ref") for value in values}))
    if len(refs) > MAX_WORKSPACE_REFS:
        raise JSpaceVectorControlError("workspace_refs:TOO_MANY")
    return refs


def _normalize_lesions(values: Iterable[int], dimensions: int) -> tuple[int, ...]:
    lesions: set[int] = set()
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise JSpaceVectorControlError("lesion_indices:INTEGER_REQUIRED")
        if value < 0 or value >= dimensions:
            raise JSpaceVectorControlError("lesion_indices:OUT_OF_RANGE")
        lesions.add(value)
    return tuple(sorted(lesions))


def _round_half_away_from_zero(value: float) -> int:
    if value >= 0.0:
        return math.floor(value + 0.5)
    return math.ceil(value - 0.5)


def _scale_to_hex(scale: float) -> str:
    return struct.pack(">d", scale).hex()


def _scale_from_hex(value: Any) -> float:
    value = _text(value, "scale_f64_be_hex")
    if len(value) != 16 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceVectorControlError("scale_f64_be_hex:IEEE754_HEX_REQUIRED")
    scale = struct.unpack(">d", bytes.fromhex(value))[0]
    if not math.isfinite(scale) or scale < 0.0:
        raise JSpaceVectorControlError("scale_f64_be_hex:FINITE_NONNEGATIVE_REQUIRED")
    return scale


def _q8_encode(values: Sequence[int]) -> str:
    raw = bytes((value & 0xFF) for value in values)
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _q8_decode(value: Any, dimensions: int) -> tuple[int, ...]:
    value = _text(value, "q8_b64url")
    if any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for ch in value):
        raise JSpaceVectorControlError("q8_b64url:BASE64URL_REQUIRED")
    padding = "=" * ((4 - len(value) % 4) % 4)
    try:
        raw = base64.urlsafe_b64decode(value + padding)
    except Exception as exc:
        raise JSpaceVectorControlError("q8_b64url:DECODE_FAILED") from exc
    if len(raw) != dimensions:
        raise JSpaceVectorControlError("q8_b64url:DIMENSION_MISMATCH")
    decoded = tuple(byte if byte < 128 else byte - 256 for byte in raw)
    if any(value == -128 for value in decoded):
        raise JSpaceVectorControlError("q8_b64url:NEGATIVE_128_FORBIDDEN")
    return decoded


def _gate_u8(value: Any) -> int:
    gate = _finite_binary64(value, "gate")
    if gate < 0.0 or gate > 1.0:
        raise JSpaceVectorControlError("gate:RANGE_0_1_REQUIRED")
    return max(0, min(255, _round_half_away_from_zero(gate * 255.0)))


def encode_vector_control(
    vector: Sequence[float],
    *,
    basis_id: str,
    role: str,
    generation: int,
    gate: float = 1.0,
    workspace_refs: Iterable[str] = (),
    lesion_indices: Iterable[int] = (),
) -> VectorControlPacket:
    """Encode one bounded J-Space vector into the trainable/replayable ABI packet."""
    if isinstance(vector, (str, bytes, bytearray)) or not isinstance(vector, Sequence):
        raise JSpaceVectorControlError("vector:SEQUENCE_REQUIRED")
    dimensions = len(vector)
    if dimensions <= 0 or dimensions > MAX_DIMENSIONS:
        raise JSpaceVectorControlError("vector:DIMENSIONS_OUT_OF_RANGE")
    values = tuple(_finite_binary64(value, f"vector[{index}]") for index, value in enumerate(vector))
    basis_id = _text(basis_id, "basis_id")
    role = _text(role, "role")
    generation = _generation(generation)
    refs = _normalize_workspace_refs(workspace_refs)
    lesions = _normalize_lesions(lesion_indices, dimensions)
    lesion_set = set(lesions)
    effective = tuple(0.0 if index in lesion_set else value for index, value in enumerate(values))
    max_abs = max(abs(value) for value in effective)
    null_vector = max_abs == 0.0
    scale = 0.0 if null_vector else max_abs / 127.0
    if null_vector:
        quantized = (0,) * dimensions
    else:
        quantized = tuple(
            max(-127, min(127, _round_half_away_from_zero(value / scale)))
            for value in effective
        )
    material = {
        "schema": SCHEMA,
        "basis_id": basis_id,
        "role": role,
        "generation": generation,
        "dimensions": dimensions,
        "scale_f64_be_hex": _scale_to_hex(scale),
        "q8_b64url": _q8_encode(quantized),
        "gate_u8": _gate_u8(gate),
        "workspace_refs": list(refs),
        "lesion_indices": list(lesions),
        "null_vector": null_vector,
    }
    body, packet_sha256 = _canonical_sha256(material)
    packet_bytes = PACKET_PREFIX + body + PACKET_SUFFIX
    return VectorControlPacket(
        schema=SCHEMA,
        basis_id=basis_id,
        role=role,
        generation=generation,
        dimensions=dimensions,
        scale_f64_be_hex=material["scale_f64_be_hex"],
        q8_b64url=material["q8_b64url"],
        gate_u8=material["gate_u8"],
        workspace_refs=refs,
        lesion_indices=lesions,
        null_vector=null_vector,
        packet_bytes=packet_bytes,
        packet_sha256=packet_sha256,
    )


def decode_vector_control(
    packet: bytes | str,
    *,
    expected_basis_id: str,
    current_generation: int,
    expected_role: str | None = None,
    expected_packet_sha256: str | None = None,
) -> DecodedVectorControl:
    """Decode and fail closed on stale generation, basis/role mismatch, or noncanonical bytes."""
    if isinstance(packet, str):
        packet_bytes = packet.encode("utf-8")
    elif isinstance(packet, bytes):
        packet_bytes = packet
    else:
        raise JSpaceVectorControlError("packet:BYTES_OR_STRING_REQUIRED")
    if not packet_bytes.startswith(PACKET_PREFIX) or not packet_bytes.endswith(PACKET_SUFFIX):
        raise JSpaceVectorControlError("packet:ENVELOPE_MISMATCH")
    body = packet_bytes[len(PACKET_PREFIX):-len(PACKET_SUFFIX)]
    try:
        material = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise JSpaceVectorControlError("packet:JSON_DECODE_FAILED") from exc
    try:
        canonical_body = canonicalize(material)
    except CanonicalizationError as exc:
        raise JSpaceVectorControlError(f"packet:CANONICALIZATION_FAILED:{exc}") from exc
    if canonical_body != body:
        raise JSpaceVectorControlError("packet:NONCANONICAL_BODY")
    digest = hashlib.sha256(packet_bytes).hexdigest()
    if expected_packet_sha256 is not None and digest != expected_packet_sha256:
        raise JSpaceVectorControlError("packet:DIGEST_MISMATCH")
    if not isinstance(material, dict) or material.get("schema") != SCHEMA:
        raise JSpaceVectorControlError("packet:SCHEMA_MISMATCH")
    required = {
        "schema", "basis_id", "role", "generation", "dimensions", "scale_f64_be_hex",
        "q8_b64url", "gate_u8", "workspace_refs", "lesion_indices", "null_vector",
    }
    if set(material) != required:
        raise JSpaceVectorControlError("packet:FIELD_SET_MISMATCH")
    basis_id = _text(material["basis_id"], "basis_id")
    role = _text(material["role"], "role")
    generation = _generation(material["generation"])
    if basis_id != _text(expected_basis_id, "expected_basis_id"):
        raise JSpaceVectorControlError("WRONG_JSPACE_BASIS")
    if generation != _generation(current_generation):
        raise JSpaceVectorControlError("STALE_ENTITY_GENERATION")
    if expected_role is not None and role != _text(expected_role, "expected_role"):
        raise JSpaceVectorControlError("ROLE_MISMATCH")
    dimensions = material["dimensions"]
    if isinstance(dimensions, bool) or not isinstance(dimensions, int) or dimensions <= 0 or dimensions > MAX_DIMENSIONS:
        raise JSpaceVectorControlError("dimensions:OUT_OF_RANGE")
    scale = _scale_from_hex(material["scale_f64_be_hex"])
    q8 = _q8_decode(material["q8_b64url"], dimensions)
    gate_u8 = material["gate_u8"]
    if isinstance(gate_u8, bool) or not isinstance(gate_u8, int) or gate_u8 < 0 or gate_u8 > 255:
        raise JSpaceVectorControlError("gate_u8:RANGE_0_255_REQUIRED")
    refs_raw = material["workspace_refs"]
    if not isinstance(refs_raw, list):
        raise JSpaceVectorControlError("workspace_refs:LIST_REQUIRED")
    refs = _normalize_workspace_refs(refs_raw)
    if list(refs) != refs_raw:
        raise JSpaceVectorControlError("workspace_refs:NONCANONICAL_ORDER_OR_DUPLICATE")
    lesions_raw = material["lesion_indices"]
    if not isinstance(lesions_raw, list):
        raise JSpaceVectorControlError("lesion_indices:LIST_REQUIRED")
    lesions = _normalize_lesions(lesions_raw, dimensions)
    if list(lesions) != lesions_raw:
        raise JSpaceVectorControlError("lesion_indices:NONCANONICAL_ORDER_OR_DUPLICATE")
    null_vector = material["null_vector"]
    if not isinstance(null_vector, bool):
        raise JSpaceVectorControlError("null_vector:BOOLEAN_REQUIRED")
    if null_vector:
        if scale != 0.0 or any(q8):
            raise JSpaceVectorControlError("null_vector:INCONSISTENT_ENCODING")
    elif scale <= 0.0:
        raise JSpaceVectorControlError("scale_f64_be_hex:POSITIVE_REQUIRED_FOR_NON_NULL")
    if any(q8[index] != 0 for index in lesions):
        raise JSpaceVectorControlError("lesion_indices:NONZERO_LESION_COORDINATE")
    vector = tuple(value * scale for value in q8)
    return DecodedVectorControl(
        schema=SCHEMA,
        basis_id=basis_id,
        role=role,
        generation=generation,
        vector=vector,
        gate=gate_u8 / 255.0,
        workspace_refs=refs,
        lesion_indices=lesions,
        null_vector=null_vector,
        packet_sha256=digest,
    )
