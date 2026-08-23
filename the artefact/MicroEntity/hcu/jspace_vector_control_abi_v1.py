#!/usr/bin/env python3
"""Compatibility guard for the single EntityOS/HCU J-Space Vector Control ABI.

Canonical implementation and wire format live in ``jspace_vector_control_v1.py``.
This historical filename remains only so old receipts/import paths do not become ambiguous.
It MUST NOT define or emit a second packet format under ``JSPACE_VECTOR_CONTROL_ABI/v1``.

The superseded envelope/q8-b64 implementation that previously lived here claimed the same
ABI schema as the canonical RFC8785/JCS packet while producing incompatible bytes. That wire
is fail-closed retired. New callers must use the canonical API re-exported below.
"""
from __future__ import annotations

try:
    from .jspace_vector_control_v1 import (
        ABI_SCHEMA,
        CODEC_SCHEMA,
        CONTROL_CONDITIONS,
        PACKET_SCHEMA,
        WIRE_FORMAT,
        JSpaceVectorControlError,
        VectorControlPacket,
        decode_vector,
        encode_vector,
        packet_bytes,
        packet_text,
        parse_packet_text,
        reconstruction_metrics,
        validate_packet,
    )
except ImportError:
    from jspace_vector_control_v1 import (
        ABI_SCHEMA,
        CODEC_SCHEMA,
        CONTROL_CONDITIONS,
        PACKET_SCHEMA,
        WIRE_FORMAT,
        JSpaceVectorControlError,
        VectorControlPacket,
        decode_vector,
        encode_vector,
        packet_bytes,
        packet_text,
        parse_packet_text,
        reconstruction_metrics,
        validate_packet,
    )

SCHEMA = ABI_SCHEMA
COMPATIBILITY_STATUS = "RETIRED_SECOND_WIRE_CANONICAL_API_ONLY"


def encode_vector_control(*args, **kwargs):
    """Reject the retired incompatible constructor instead of minting a second v1 wire."""
    raise JSpaceVectorControlError(
        "LEGACY_VECTOR_CONTROL_CONSTRUCTOR_RETIRED_USE_ENCODE_VECTOR"
    )


def decode_vector_control(*args, **kwargs):
    """Reject the retired incompatible decoder instead of accepting ambiguous v1 bytes."""
    raise JSpaceVectorControlError(
        "LEGACY_VECTOR_CONTROL_DECODER_RETIRED_USE_PARSE_PACKET_TEXT_AND_DECODE_VECTOR"
    )


__all__ = [
    "ABI_SCHEMA",
    "CODEC_SCHEMA",
    "CONTROL_CONDITIONS",
    "PACKET_SCHEMA",
    "WIRE_FORMAT",
    "SCHEMA",
    "COMPATIBILITY_STATUS",
    "JSpaceVectorControlError",
    "VectorControlPacket",
    "encode_vector",
    "validate_packet",
    "decode_vector",
    "reconstruction_metrics",
    "packet_bytes",
    "packet_text",
    "parse_packet_text",
    "encode_vector_control",
    "decode_vector_control",
]
