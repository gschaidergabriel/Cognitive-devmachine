#!/usr/bin/env python3
"""Versioned language-neutral typed canonical bytes for EntityOS/HCU identities.

This is deliberately NOT labelled RFC 8785/JCS. It is a smaller typed equivalent for
already-admitted HCU data structures, designed so a second implementation can reproduce
exact bytes without inheriting host-language JSON number or map-order serialization.

Wire law (v1):
- domain-separated header ``HCU_TYPED_CANONICAL/v1``;
- null, bool, signed int64, IEEE-754 binary64, UTF-8 string, list/tuple and string-key map;
- float -0.0 normalizes to +0.0; NaN/Infinity are rejected;
- strings are encoded as strict UTF-8 with no Unicode normalization;
- map keys are sorted by their raw UTF-8 byte sequence;
- integers and floats remain different types;
- unsupported values fail closed.

This codec only canonicalizes already-typed values. Raw JSON duplicate-key rejection is
an ingress/parser responsibility and MUST occur before Mapping construction when raw JSON
is the source format.
"""
from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Mapping
from typing import Any

SCHEMA = "HCU_TYPED_CANONICAL/v1"
_HEADER = SCHEMA.encode("ascii") + b"\x00"
_MAX_U32 = (1 << 32) - 1
_MIN_I64 = -(1 << 63)
_MAX_I64 = (1 << 63) - 1


class CanonicalizationError(ValueError):
    pass


def _u32(value: int, field: str) -> bytes:
    if value < 0 or value > _MAX_U32:
        raise CanonicalizationError(f"{field}:U32_RANGE_REQUIRED")
    return struct.pack(">I", value)


def _utf8(value: str, field: str) -> bytes:
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise CanonicalizationError(f"{field}:VALID_UNICODE_REQUIRED") from exc
    if len(encoded) > _MAX_U32:
        raise CanonicalizationError(f"{field}:UTF8_TOO_LONG")
    return encoded


def _encode_string(value: str, field: str = "string") -> bytes:
    encoded = _utf8(value, field)
    return b"S" + _u32(len(encoded), field) + encoded


def _encode(value: Any) -> bytes:
    if value is None:
        return b"N"
    if isinstance(value, bool):
        return b"B\x01" if value else b"B\x00"
    if isinstance(value, int):
        if value < _MIN_I64 or value > _MAX_I64:
            raise CanonicalizationError("integer:I64_RANGE_REQUIRED")
        return b"I" + struct.pack(">q", value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("float:FINITE_BINARY64_REQUIRED")
        # Treat semantically equal zero values identically across runtimes.
        if value == 0.0:
            value = 0.0
        return b"F" + struct.pack(">d", value)
    if isinstance(value, str):
        return _encode_string(value)
    if isinstance(value, (list, tuple)):
        if len(value) > _MAX_U32:
            raise CanonicalizationError("sequence:TOO_LONG")
        return b"L" + _u32(len(value), "sequence") + b"".join(_encode(item) for item in value)
    if isinstance(value, Mapping):
        if len(value) > _MAX_U32:
            raise CanonicalizationError("mapping:TOO_LARGE")
        keyed: list[tuple[bytes, str, Any]] = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("mapping:STRING_KEYS_REQUIRED")
            raw_key = _utf8(key, "mapping_key")
            keyed.append((raw_key, key, item))
        keyed.sort(key=lambda row: row[0])
        body = bytearray(b"M" + _u32(len(keyed), "mapping"))
        for _raw_key, key, item in keyed:
            body.extend(_encode_string(key, "mapping_key"))
            body.extend(_encode(item))
        return bytes(body)
    raise CanonicalizationError(f"value:UNSUPPORTED_TYPE:{type(value).__name__}")


def canonical_bytes(value: Any, *, domain: str) -> bytes:
    if not isinstance(domain, str) or not domain:
        raise CanonicalizationError("domain:NONEMPTY_STRING_REQUIRED")
    return _HEADER + _encode_string(domain, "domain") + _encode(value)


def canonical_sha256(value: Any, *, domain: str) -> str:
    return hashlib.sha256(canonical_bytes(value, domain=domain)).hexdigest()
