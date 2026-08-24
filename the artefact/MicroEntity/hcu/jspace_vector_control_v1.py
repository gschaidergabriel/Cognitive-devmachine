#!/usr/bin/env python3
"""Deterministic Q8 wire J-Space Vector Control ABI for EntityOS/HCU.

This is an observable control codec, not hidden-state evidence and not a truth/state/effect
authority. It converts a finite binary64 vector into a versioned q8 packet whose identity is
RFC8785/JCS hash-bound. The packet can be reproduced by text-token SFT and by a local HCU
runtime without claiming direct residual-stream injection.

The wire ABI name is intentionally distinct from ``JSPACE_VECTOR_CONTROL_ABI/v1``, which
canonical main already uses for a model-specific Trigger-1 source/derivation descriptor.
The historical colliding name is not accepted as an alias by this codec.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
import math
from typing import Any, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

ABI_SCHEMA = "JSPACE_Q8_VECTOR_CONTROL_WIRE_ABI/v1"
LEGACY_COLLIDING_ABI_SCHEMA = "JSPACE_VECTOR_CONTROL_ABI/v1"
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
# Every scale emitted from a finite IEEE-754 binary64 source vector is far below this
# bound (max finite numerator ~309 decimal digits; min subnormal denominator ~326).
# Bound text before int/Fraction construction so an untrusted packet cannot turn scale
# parsing into arbitrary big-integer work.
MAX_SCALE_DECIMAL_DIGITS = 512
_PACKET_FIELDS = frozenset({
    "schema",
    "abi_schema",
    "canonicalization_schema",
    "codec_schema",
    "wire_format",
    "basis_id",
    "basis_sha256",
    "generation",
    "role",
    "dimension",
    "control_condition",
    "source_vector_sha256",
    "scale_numerator",
    "scale_denominator",
    "q8_values",
    "packet_sha256",
})


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


def _validate_scale_text_syntax(numerator_text: Any, denominator_text: Any) -> None:
    """Cheap pre-hash bounds only; semantic rational admission happens after digest identity."""
    for value, field in (
        (numerator_text, "scale_numerator"),
        (denominator_text, "scale_denominator"),
    ):
        if not isinstance(value, str) or not 1 <= len(value) <= MAX_SCALE_DECIMAL_DIGITS:
            raise JSpaceVectorControlError(f"{field}:DECIMAL_STRING_BOUNDS_REQUIRED")
        if any(ch < "0" or ch > "9" for ch in value):
            raise JSpaceVectorControlError(f"{field}:UNSIGNED_DECIMAL_STRING_REQUIRED")


def _scale_fraction(numerator_text: Any, denominator_text: Any) -> Fraction:
    """Parse the sole admitted finite-binary64 q8 scale representation.

    Packet hashes authenticate bytes, not semantic safety. A caller can construct and hash a
    new packet, so the scale itself must be bounded, reduced and provably derived from one
    positive finite binary64 max-absolute anchor exactly as the canonical encoder emits it.
    """
    _validate_scale_text_syntax(numerator_text, denominator_text)

    scale_numerator = int(numerator_text)
    scale_denominator = int(denominator_text)
    if str(scale_numerator) != numerator_text or str(scale_denominator) != denominator_text:
        raise JSpaceVectorControlError("SCALE_RATIONAL_NONCANONICAL_DECIMAL_STRING")
    if scale_denominator <= 0:
        raise JSpaceVectorControlError("SCALE_RATIONAL_INVALID")

    scale = Fraction(scale_numerator, scale_denominator)
    if scale.numerator != scale_numerator or scale.denominator != scale_denominator:
        raise JSpaceVectorControlError("SCALE_RATIONAL_NOT_REDUCED")
    if scale_numerator > 0:
        anchor_fraction = scale * 127
        try:
            anchor = float(anchor_fraction)
        except OverflowError as exc:
            raise JSpaceVectorControlError("SCALE_RATIONAL_BINARY64_RANGE_REQUIRED") from exc
        if not math.isfinite(anchor) or anchor <= 0.0:
            raise JSpaceVectorControlError("SCALE_RATIONAL_BINARY64_RANGE_REQUIRED")
        # The canonical encoder defines scale = Fraction.from_float(max_abs) / 127.
        # Merely being finite after rounding to float is weaker: an attacker can mint a
        # self-consistent packet around an arbitrary rational (for example 1/3), producing
        # valid packet bytes that no finite-binary64 source vector can cause the encoder to
        # emit. Require the exact encoder image so one ABI has one canonical scale language.
        if Fraction.from_float(anchor) != anchor_fraction:
            raise JSpaceVectorControlError("SCALE_RATIONAL_BINARY64_ANCHOR_EXACT_REQUIRED")
    return scale


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

    # Validation must admit one exact wire identity, not a value that becomes valid only
    # after helper normalization. Otherwise a caller can mint self-consistent packet bytes
    # with padded identifiers/digests which validate here but compare differently at the
    # decoder or downstream admission boundary.
    if packet.basis_id != _text(packet.basis_id, "basis_id"):
        raise JSpaceVectorControlError("basis_id:NONCANONICAL_TEXT")
    if packet.basis_sha256 != _sha256(packet.basis_sha256, "basis_sha256"):
        raise JSpaceVectorControlError("basis_sha256:NONCANONICAL_SHA256")
    _generation(packet.generation)
    if packet.role != _text(packet.role, "role"):
        raise JSpaceVectorControlError("role:NONCANONICAL_TEXT")
    if packet.control_condition not in CONTROL_CONDITIONS:
        raise JSpaceVectorControlError("control_condition:UNSUPPORTED")
    if isinstance(packet.dimension, bool) or not isinstance(packet.dimension, int) or not 1 <= packet.dimension <= MAX_DIMENSION:
        raise JSpaceVectorControlError("dimension:OUT_OF_RANGE")
    if len(packet.q8_values) != packet.dimension:
        raise JSpaceVectorControlError("Q8_DIMENSION_MISMATCH")
    for index, value in enumerate(packet.q8_values):
        if isinstance(value, bool) or not isinstance(value, int) or not -127 <= value <= 127:
            raise JSpaceVectorControlError(f"q8_values[{index}]:SIGNED_Q8_REQUIRED")
    if packet.source_vector_sha256 != _sha256(packet.source_vector_sha256, "source_vector_sha256"):
        raise JSpaceVectorControlError("source_vector_sha256:NONCANONICAL_SHA256")

    # Bound untrusted scale text before hashing, but preserve the established identity fence:
    # syntactically admissible packets with changed content fail DIGEST_MISMATCH before any
    # semantic q8/scale interpretation. Self-consistent newly hashed packets then face the
    # stronger rational/range admission below.
    _validate_scale_text_syntax(packet.scale_numerator, packet.scale_denominator)
    observed = _sha256(packet.packet_sha256, "packet_sha256")
    if packet.packet_sha256 != observed:
        raise JSpaceVectorControlError("packet_sha256:NONCANONICAL_SHA256")
    expected = _canonical_sha256(_packet_material(packet), "VECTOR_CONTROL_PACKET")
    if observed != expected:
        raise JSpaceVectorControlError("VECTOR_CONTROL_PACKET_DIGEST_MISMATCH")

    scale = _scale_fraction(packet.scale_numerator, packet.scale_denominator)
    if scale.numerator == 0 and any(packet.q8_values):
        raise JSpaceVectorControlError("ZERO_SCALE_REQUIRES_NULL_Q8_VECTOR")
    if scale.numerator > 0 and max(abs(value) for value in packet.q8_values) != 127:
        raise JSpaceVectorControlError("NONZERO_VECTOR_REQUIRES_FULL_Q8_SCALE_ANCHOR")


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

    scale = _scale_fraction(packet.scale_numerator, packet.scale_denominator)
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


def packet_text(packet: VectorControlPacket) -> str:
    """Return the sole admitted text form: exact RFC8785/JCS UTF-8 packet bytes."""
    return packet_bytes(packet).decode("utf-8", "strict")


def parse_packet_text(text: str) -> VectorControlPacket:
    """Parse only the exact canonical JCS text form; aliases/extra fields fail closed."""
    if not isinstance(text, str) or not text:
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_REQUIRED")
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_JSON_INVALID") from exc
    if not isinstance(value, dict) or set(value) != _PACKET_FIELDS:
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_SCHEMA_MISMATCH")
    if not isinstance(value.get("q8_values"), list):
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_Q8_ARRAY_REQUIRED")
    packet = VectorControlPacket(
        schema=value.get("schema"),
        abi_schema=value.get("abi_schema"),
        canonicalization_schema=value.get("canonicalization_schema"),
        codec_schema=value.get("codec_schema"),
        wire_format=value.get("wire_format"),
        basis_id=value.get("basis_id"),
        basis_sha256=value.get("basis_sha256"),
        generation=value.get("generation"),
        role=value.get("role"),
        dimension=value.get("dimension"),
        control_condition=value.get("control_condition"),
        source_vector_sha256=value.get("source_vector_sha256"),
        scale_numerator=value.get("scale_numerator"),
        scale_denominator=value.get("scale_denominator"),
        q8_values=tuple(value.get("q8_values")),
        packet_sha256=value.get("packet_sha256"),
    )
    validate_packet(packet)
    if packet_text(packet) != text:
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_NONCANONICAL")
    return packet
