#!/usr/bin/env python3
"""Versioned deterministic CBOR subset for EntityOS/HCU Typed Entry identity.

The encoder follows RFC 8949 core deterministic rules for the admitted subset:
null, booleans, I-JSON-safe integers, byte strings, UTF-8 text, arrays, and maps with
text keys. Floats are intentionally rejected at this boundary so independent producers
do not inherit language-specific number formatting into causal identity.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

CANONICALIZATION_SCHEMA = "ENTITYOS_HCU_ENTRY_CBOR_RFC8949_SUBSET/v1"
SAFE_INTEGER_MAX = 9_007_199_254_740_991


class CanonicalEncodingError(ValueError):
    pass


def _head(major: int, value: int) -> bytes:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CanonicalEncodingError("CBOR_ARGUMENT_NONNEGATIVE_INTEGER_REQUIRED")
    prefix = major << 5
    if value < 24:
        return bytes((prefix | value,))
    if value <= 0xFF:
        return bytes((prefix | 24, value))
    if value <= 0xFFFF:
        return bytes((prefix | 25,)) + value.to_bytes(2, "big")
    if value <= 0xFFFFFFFF:
        return bytes((prefix | 26,)) + value.to_bytes(4, "big")
    if value <= 0xFFFFFFFFFFFFFFFF:
        return bytes((prefix | 27,)) + value.to_bytes(8, "big")
    raise CanonicalEncodingError("CBOR_ARGUMENT_UINT64_OVERFLOW")


def encode_canonical(value: Any) -> bytes:
    if value is None:
        return b"\xf6"
    if value is False:
        return b"\xf4"
    if value is True:
        return b"\xf5"
    if isinstance(value, int) and not isinstance(value, bool):
        if not -SAFE_INTEGER_MAX <= value <= SAFE_INTEGER_MAX:
            raise CanonicalEncodingError("INTEGER_OUTSIDE_IJSON_SAFE_RANGE")
        if value >= 0:
            return _head(0, value)
        return _head(1, -1 - value)
    if isinstance(value, float):
        raise CanonicalEncodingError("FLOAT_FORBIDDEN_AT_TYPED_ENTRY_IDENTITY_BOUNDARY")
    if isinstance(value, (bytes, bytearray, memoryview)):
        payload = bytes(value)
        return _head(2, len(payload)) + payload
    if isinstance(value, str):
        payload = value.encode("utf-8", errors="strict")
        return _head(3, len(payload)) + payload
    if isinstance(value, Mapping):
        encoded_items: list[tuple[bytes, bytes]] = []
        for key, child in value.items():
            if not isinstance(key, str):
                raise CanonicalEncodingError("MAP_KEYS_MUST_BE_TEXT")
            encoded_key = encode_canonical(key)
            encoded_items.append((encoded_key, encode_canonical(child)))
        encoded_items.sort(key=lambda item: item[0])
        return _head(5, len(encoded_items)) + b"".join(k + v for k, v in encoded_items)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, memoryview)):
        items = tuple(value)
        return _head(4, len(items)) + b"".join(encode_canonical(item) for item in items)
    raise CanonicalEncodingError(f"UNSUPPORTED_CANONICAL_TYPE:{type(value).__name__}")
