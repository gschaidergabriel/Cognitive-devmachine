#!/usr/bin/env python3
"""Versioned cross-language canonical bytes for EntityOS/HCU causal identities.

This is an explicitly typed alternative to RFC 8785 JCS for internal hash inputs.
It accepts the JSON/I-JSON-like value domain used by HCU identity records and emits
one language-neutral byte representation. It is not a wire format and carries no
truth, capability, or effect authority.
"""
from __future__ import annotations

import hashlib
import math
import struct
from typing import Any, Mapping, Sequence

CANONICALIZATION_SCHEMA = "ENTITYOS_HCU_TYPED_CANONICAL/v1"
_PREFIX = CANONICALIZATION_SCHEMA.encode("ascii") + b"\x00"
_MAX_SAFE_INTEGER = (1 << 53) - 1


class HCUCanonicalizationError(ValueError):
    pass


def _u64(value: int) -> bytes:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > (1 << 64) - 1:
        raise HCUCanonicalizationError("LENGTH_OUT_OF_RANGE")
    return struct.pack(">Q", value)


def _text_bytes(value: str) -> bytes:
    try:
        raw = value.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise HCUCanonicalizationError("STRING_NOT_VALID_UNICODE") from exc
    return b"s" + _u64(len(raw)) + raw


def _number_bytes(value: int | float) -> bytes:
    if isinstance(value, bool):
        raise HCUCanonicalizationError("BOOLEAN_IS_NOT_NUMBER")
    if isinstance(value, int):
        if abs(value) > _MAX_SAFE_INTEGER:
            raise HCUCanonicalizationError("INTEGER_OUTSIDE_IJSON_SAFE_RANGE")
        number = float(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise HCUCanonicalizationError("NONFINITE_NUMBER_FORBIDDEN")
        number = value
        if number.is_integer() and abs(number) > _MAX_SAFE_INTEGER:
            raise HCUCanonicalizationError("INTEGER_OUTSIDE_IJSON_SAFE_RANGE")
    else:
        raise HCUCanonicalizationError("NUMBER_REQUIRED")
    # Match JSON/JCS numeric equivalence for negative zero without depending on text rendering.
    if number == 0.0:
        number = 0.0
    return b"d" + struct.pack(">d", number)


def _encode(value: Any) -> bytes:
    if value is None:
        return b"n"
    if value is True:
        return b"t"
    if value is False:
        return b"f"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number_bytes(value)
    if isinstance(value, str):
        return _text_bytes(value)
    if isinstance(value, Mapping):
        items: list[tuple[bytes, str, Any]] = []
        for key, child in value.items():
            if not isinstance(key, str):
                raise HCUCanonicalizationError("OBJECT_KEY_STRING_REQUIRED")
            try:
                key_bytes = key.encode("utf-8", "strict")
            except UnicodeEncodeError as exc:
                raise HCUCanonicalizationError("OBJECT_KEY_NOT_VALID_UNICODE") from exc
            items.append((key_bytes, key, child))
        items.sort(key=lambda row: row[0])
        output = bytearray(b"o" + _u64(len(items)))
        for _, key, child in items:
            output.extend(_text_bytes(key))
            output.extend(_encode(child))
        return bytes(output)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, memoryview)):
        output = bytearray(b"a" + _u64(len(value)))
        for child in value:
            output.extend(_encode(child))
        return bytes(output)
    raise HCUCanonicalizationError(f"TYPE_UNSUPPORTED:{type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Return exact version-prefixed canonical bytes for one admitted identity value."""
    return _PREFIX + _encode(value)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
