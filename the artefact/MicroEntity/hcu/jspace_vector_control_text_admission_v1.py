#!/usr/bin/env python3
"""Bounded untrusted-text ingress for the canonical EntityOS/HCU J-Space Vector Control ABI.

This module does not define a second packet format or parser. It is a deterministic admission
fence in front of ``jspace_vector_control_v1.parse_packet_text`` so untrusted text cannot hand
an arbitrarily large document to ``json.loads`` before the canonical packet's dimension, field,
digest, generation, basis, role and control-condition checks run.

The admitted wire remains ``JSPACE_VECTOR_CONTROL_ABI/v1`` / RFC8785-JCS UTF-8. This helper
mints no state, truth, model-runtime, training or effect authority.
"""
from __future__ import annotations

try:
    from .jspace_vector_control_v1 import (
        ABI_SCHEMA,
        WIRE_FORMAT,
        JSpaceVectorControlError,
        VectorControlPacket,
        parse_packet_text as _parse_packet_text,
    )
except ImportError:
    from jspace_vector_control_v1 import (
        ABI_SCHEMA,
        WIRE_FORMAT,
        JSpaceVectorControlError,
        VectorControlPacket,
        parse_packet_text as _parse_packet_text,
    )

ADMISSION_SCHEMA = "JSPACE_VECTOR_CONTROL_TEXT_ADMISSION/v1"
# Canonical packets are materially smaller than this at MAX_DIMENSION=4096. Keep a generous
# ceiling so the fence cannot reject currently admissible q8 packets while still bounding the
# pre-json parser workload. The UTF-8 ceiling is exactly four bytes per admitted Python scalar
# count, the maximum UTF-8 width for a valid Unicode scalar value.
MAX_PACKET_TEXT_CHARS = 65_536
MAX_PACKET_TEXT_UTF8_BYTES = 262_144


def admit_packet_text(text: str) -> VectorControlPacket:
    """Admit bounded canonical packet text, then delegate to the sole ABI parser."""
    if not isinstance(text, str) or not text:
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_REQUIRED")
    if len(text) > MAX_PACKET_TEXT_CHARS:
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_CHAR_BUDGET_EXCEEDED")
    try:
        wire = text.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_UTF8_REQUIRED") from exc
    if len(wire) > MAX_PACKET_TEXT_UTF8_BYTES:
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_UTF8_BUDGET_EXCEEDED")
    try:
        return _parse_packet_text(text)
    except RecursionError as exc:
        # Deep but byte-bounded JSON can still exhaust the host decoder recursion budget.
        # Normalize that implementation failure at the untrusted-ingress boundary instead of
        # leaking a host exception or encouraging a second parser/wire format.
        raise JSpaceVectorControlError("VECTOR_CONTROL_TEXT_JSON_DEPTH_EXCEEDED") from exc


__all__ = [
    "ABI_SCHEMA",
    "WIRE_FORMAT",
    "ADMISSION_SCHEMA",
    "MAX_PACKET_TEXT_CHARS",
    "MAX_PACKET_TEXT_UTF8_BYTES",
    "JSpaceVectorControlError",
    "VectorControlPacket",
    "admit_packet_text",
]
