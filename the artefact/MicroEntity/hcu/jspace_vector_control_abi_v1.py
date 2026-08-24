#!/usr/bin/env python3
"""Compatibility guard for the retained EntityOS/HCU Q8 vector-control wire codec.

Canonical implementation and wire format live in ``jspace_vector_control_v1.py`` and now
emit ``JSPACE_Q8_VECTOR_CONTROL_WIRE_ABI/v1``. Canonical main already uses the historical
literal ``JSPACE_VECTOR_CONTROL_ABI/v1`` for a materially different model-specific
Trigger-1 source/derivation descriptor, so that colliding literal is retired for this donor
wire codec and MUST NOT be accepted as an alias.

This historical filename remains only so old import paths do not silently create a second
implementation. The superseded envelope/q8-b64 implementation that previously lived here
is also fail-closed retired. New callers must use the canonical API re-exported below.
"""
from __future__ import annotations

try:
    from .jspace_vector_control_v1 import (
        ABI_SCHEMA,
        CODEC_SCHEMA,
        CONTROL_CONDITIONS,
        LEGACY_COLLIDING_ABI_SCHEMA,
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
        LEGACY_COLLIDING_ABI_SCHEMA,
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
COMPATIBILITY_STATUS = "RETIRED_COLLIDING_ABI_AND_SECOND_WIRE_CANONICAL_Q8_WIRE_API_ONLY"


def encode_vector_control(*args, **kwargs):
    """Reject the retired incompatible constructor instead of minting a second wire."""
    raise JSpaceVectorControlError(
        "LEGACY_VECTOR_CONTROL_CONSTRUCTOR_RETIRED_USE_ENCODE_VECTOR"
    )


def decode_vector_control(*args, **kwargs):
    """Reject the retired incompatible decoder instead of accepting ambiguous bytes."""
    raise JSpaceVectorControlError(
        "LEGACY_VECTOR_CONTROL_DECODER_RETIRED_USE_PARSE_PACKET_TEXT_AND_DECODE_VECTOR"
    )


__all__ = [
    "ABI_SCHEMA",
    "CODEC_SCHEMA",
    "CONTROL_CONDITIONS",
    "LEGACY_COLLIDING_ABI_SCHEMA",
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
