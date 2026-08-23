#!/usr/bin/env python3
"""Deterministic token/byte J-Space Vector Control ABI for EntityOS/HCU.

This is an observable control codec, not hidden-state evidence and not a truth/state/effect
authority. It converts a finite binary64 vector into a versioned q8 packet whose identity is
RFC8785/JCS hash-bound. The packet can be reproduced by text-token SFT and by a local HCU
runtime without claiming direct residual-stream injection.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import math
from typing import Any, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

ABI_SCHEMA = "JSPACE_VECTOR_CONTROL_ABI/v1"
PACKET_SCHEMA = "JSPACE_VECTOR_CONTROL_PACKET/v1"
CODEC_SCHEMA = "JSPACE_Q8_SYMMETRIC_RATIONAL/v1"
WIRE_FORMAT = "RFC8785_JCS_JSON_UTF8"
CONTROL_CONDITIONS = frozenset({
    "BASELINE",
    "NULL_VECTOR",
    "SIGN_FLIP",
    "PERMUTED",
    "ROLE_SWAP",
    "LESION",
})
MAX_DIMENSION = 4096


class JSpaceVectorControlError(ValueError):
    pass


@dataclass(frozen=True)
class VectorControlPacket:
    schema: str
    abi_schema: str
    canonicalization_schema: str
    codec_schema: str
    wire_format: str
    basis_id: str
    basis_sha256: str
    generation: int
    role: str
    dimension: int
    control_condition: str
    source_vector_sha256: str
    scale_numerator: str
    scale_denominator: str
    q8_values: tuple[int, ...]
    packet_sha256: str


def _text(value: Any, field: str, *, max_len: int = 512) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceVectorControlError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise JSpaceVectorControlError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, max_len=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceVectorControlError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _generation(value: Any, field: str = "generation") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceVectorControlError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceVectorControlError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _binary64(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise JSpaceVectorControlError(f"{field}:FINITE_BINARY64_REQUIRED")
    if isinstance(value, int):
        try:
            converted = float(value)
        except OverflowError as exc:
            raise JSpaceVectorControlError(f"{field}:FINITE_BINARY64_REQUIRED") from exc
        if not math.isfinite(converted) or int(converted) != value:
            raise JSpaceVectorControlError(f"{field}:EXACT_BINARY64_REQUIRED")
        value = converted
    else:
        value = float(value)
    if not math.isfinite(value):
        raise JSpaceVectorControlError(f"{field}:FINITE_BINARY64_REQUIRED")
    return 0.0 if value == 0.0 else value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise JSpaceVectorControlError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _round_half_even(value: Fraction) -> int:
    """Round an exact rational to nearest integer, ties to even, without float drift."""
    sign = -1 if value < 0 else 1
    numerator = abs(value.numerator)
    denominator = value.denominator
    quotient, remainder = divmod(numerator, denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient % 2 == 1):
        quotient += 1
    return sign * quotient


def _normalize_vector(values: Sequence[Any]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
        raise JSpaceVectorControlError("vector:SEQUENCE_REQUIRED")
    if not 1 <= len(values) <= MAX_DIMENSION:
        raise JSpaceVectorControlError("vector:DIMENSION_OUT_OF_RANGE")
    return tuple(_binary64(value, f"vector[{index}]") for index, value in enumerate(values))


def _packet_material(packet: VectorControlPacket) -> dict[str, Any]:
    material = asdict(packet)
    material.pop("packet_sha256", None)
    material["q8_values"] = list(packet.q8_values)
    return material


def encode_vector(
    values: Sequence[Any],
    *,
    basis_id: str,
    basis_sha256: str,
    generation: int,
    role: str,
    control_condition: str = "BASELINE",
) -> VectorControlPacket:
    """Encode finite binary64 coordinates into a deterministic symmetric q8 packet.

    Scale is represented as an exact rational decimal-string pair so packet identity does
    not depend on a host decimal context. Quantization itself uses exact Fraction arithmetic.
    """
    vector = _normalize_vector(values)
    basis_id = _text(basis_id, "basis_id")
    basis_sha256 = _sha256(basis_sha256, "basis_sha256")
    generation = _generation(generation)
    role = _text(role, "role")
    if control_condition not in CONTROL_CONDITIONS:
        raise JSpaceVectorControlError("control_condition:UNSUPPORTED")

    source_vector_sha256 = _canonical_sha256(list(vector), "SOURCE_VECTOR")
    max_abs = max(abs(value) for value in vector)
    if max_abs == 0.0:
        scale = Fraction(0, 1)
        q8_values = tuple(0 for _ in vector)
    else:
        scale = Fraction.from_float(max_abs) / 127
        quantized: list[int] = []
        for value in vector:
            q = _round_half_even(Fraction.from_float(value) / scale)
            quantized.append(max(-127, min(127, q)))
        q8_values = tuple(quantized)

    material = {
        "schema": PACKET_SCHEMA,
        "abi_schema": ABI_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "codec_schema": CODEC_SCHEMA,
        "wire_format": WIRE_FORMAT,
        "basis_id": basis_id,
        "basis_sha256": basis_sha256,
        "generation": generation,
        "role": role,
        "dimension": len(vector),
        "control_condition": control_condition,
        "source_vector_sha256": source_vector_sha256,
        "scale_numerator": str(scale.numerator),
        "scale_denominator": str(scale.denominator),
        "q8_values": list(q8_values),
    }
    packet_sha256 = _canonical_sha256(material, "VECTOR_CONTROL_PACKET")
    return VectorControlPacket(
        **{**material, "q8_values": q8_values},
        packet_sha256=packet_sha256,
    )


def validate_packet(packet: VectorControlPacket) -> None:
    if not isinstance(packet, VectorControlPacket):
        raise JSpaceVectorControlError("VECTOR_CONTROL_PACKET_REQUIRED")
    if packet.schema != PACKET_SCHEMA or packet.abi_schema != ABI_SCHEMA:
        raise JSpaceVectorControlError("VECTOR_CONTROL_SCHEMA_UNSUPPORTED")
    if packet.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceVectorControlError("VECTOR_CONTROL_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if packet.codec_schema != CODEC_SCHEMA or packet.wire_format != WIRE_FORMAT:
        raise JSpaceVectorControlError("VECTOR_CONTROL_CODEC_UNSUPPORTED")
    _text(packet.basis_id, "basis_id")
    _sha256(packet.basis_sha256, "basis_sha256")
    _generation(packet.generation)
    _text(packet.role, "role")
    if packet.control_condition not in CONTROL_CONDITIONS:
        raise JSpaceVectorControlError("control_condition:UNSUPPORTED")
    if isinstance(packet.dimension, bool) or not isinstance(packet.dimension, int) or not 1 <= packet.dimension <= MAX_DIMENSION:
        raise JSpaceVectorControlError("dimension:OUT_OF_RANGE")
    if len(packet.q8_values) != packet.dimension:
        raise JSpaceVectorControlError("Q8_DIMENSION_MISMATCH")
    for index, value in enumerate(packet.q8_values):
        if isinstance(value, bool) or not isinstance(value, int) or not -127 <= value <= 127:
            raise JSpaceVectorControlError(f"q8_values[{index}]:SIGNED_Q8_REQUIRED")
    _sha256(packet.source_vector_sha256, "source_vector_sha256")
    try:
        scale_numerator = int(packet.scale_numerator)
        scale_denominator = int(packet.scale_denominator)
    except (TypeError, ValueError) as exc:
        raise JSpaceVectorControlError("SCALE_RATIONAL_DECIMAL_STRINGS_REQUIRED") from exc
    if scale_numerator < 0 or scale_denominator <= 0:
        raise JSpaceVectorControlError("SCALE_RATIONAL_INVALID")
    if scale_numerator == 0 and any(packet.q8_values):
        raise JSpaceVectorControlError("ZERO_SCALE_REQUIRES_NULL_Q8_VECTOR")
    if scale_numerator > 0 and max(abs(value) for value in packet.q8_values) != 127:
        raise JSpaceVectorControlError("NONZERO_VECTOR_REQUIRES_FULL_Q8_SCALE_ANCHOR")
    observed = _sha256(packet.packet_sha256, "packet_sha256")
    expected = _canonical_sha256(_packet_material(packet), "VECTOR_CONTROL_PACKET")
    if observed != expected:
        raise JSpaceVectorControlError("VECTOR_CONTROL_PACKET_DIGEST_MISMATCH")


def decode_vector(
    packet: VectorControlPacket,
    *,
    current_generation: int,
    expected_basis_id: str,
    expected_basis_sha256: str,
    expected_role: str,
    expected_control_condition: str | None = None,
) -> tuple[float, ...]:
    """Decode only after generation/basis/role/control fences are checked."""
    validate_packet(packet)
    if packet.generation != _generation(current_generation, "current_generation"):
        raise JSpaceVectorControlError("STALE_VECTOR_CONTROL_GENERATION")
    if packet.basis_id != _text(expected_basis_id, "expected_basis_id"):
        raise JSpaceVectorControlError("JSPACE_BASIS_ID_MISMATCH")
    if packet.basis_sha256 != _sha256(expected_basis_sha256, "expected_basis_sha256"):
        raise JSpaceVectorControlError("JSPACE_BASIS_SHA256_MISMATCH")
    if packet.role != _text(expected_role, "expected_role"):
        raise JSpaceVectorControlError("JSPACE_ROLE_MISMATCH")
    if expected_control_condition is not None and packet.control_condition != expected_control_condition:
        raise JSpaceVectorControlError("JSPACE_CONTROL_CONDITION_MISMATCH")

    scale = Fraction(int(packet.scale_numerator), int(packet.scale_denominator))
    return tuple(float(value * scale) for value in packet.q8_values)


def reconstruction_metrics(source: Sequence[Any], reconstructed: Sequence[Any]) -> dict[str, float]:
    left = _normalize_vector(source)
    right = _normalize_vector(reconstructed)
    if len(left) != len(right):
        raise JSpaceVectorControlError("RECONSTRUCTION_DIMENSION_MISMATCH")
    errors = [abs(a - b) for a, b in zip(left, right)]
    max_abs_source = max(abs(value) for value in left)
    return {
        "max_abs_error": max(errors),
        "mean_abs_error": sum(errors) / len(errors),
        "max_abs_source": max_abs_source,
        "normalized_max_error": 0.0 if max_abs_source == 0.0 else max(errors) / max_abs_source,
    }


def packet_bytes(packet: VectorControlPacket) -> bytes:
    validate_packet(packet)
    try:
        return canonicalize(asdict(packet))
    except CanonicalizationError as exc:
        raise JSpaceVectorControlError(f"PACKET_WIRE_CANONICALIZATION_FAILED:{exc}") from exc
