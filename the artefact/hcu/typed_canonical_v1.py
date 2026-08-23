#!/usr/bin/env python3
"""Versioned typed canonical JSON for EntityOS/HCU causal identity.

This is intentionally NOT a general RFC 8785 implementation. It is a smaller,
explicitly versioned typed equivalent for identity-bearing Entry/HCU structures.
The subset avoids cross-runtime JSON-number ambiguity by rejecting floats and
restricting integers to the exact IEEE-754 safe range. Structural object keys are
ASCII tokens, so Python lexical order is the same as RFC 8785 UTF-16 order for the
admitted key domain. Unicode string values are preserved byte-for-byte after UTF-8
encoding; no Unicode normalization is performed.

Use this only for deterministic identity/receipt material. Payloads remain referenced
by digest/ref and canonical truth/effect authority remains outside this module.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "ENTITYOS_TYPED_CANONICAL_JSON/v1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991
_KEY_RE = re.compile(r"^[A-Za-z0-9_.:/-]{1,128}$")


class TypedCanonicalizationError(ValueError):
    pass


def _need(condition: bool, code: str) -> None:
    if not condition:
        raise TypedCanonicalizationError(code)


def _string(value: str, *, key: bool = False) -> str:
    _need(type(value) is str, "STRING_REQUIRED")
    try:
        value.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise TypedCanonicalizationError("INVALID_UNICODE_SCALAR") from exc
    if key:
        _need(_KEY_RE.fullmatch(value) is not None, "OBJECT_KEY_OUTSIDE_TYPED_ASCII_DOMAIN")
    return value


def _validate(value: Any) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        _need(-MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER, "INTEGER_OUTSIDE_SAFE_RANGE")
        return
    if type(value) is float:
        raise TypedCanonicalizationError("FLOAT_FORBIDDEN_USE_EXPLICIT_FIXED_POINT_INTEGER")
    if type(value) is str:
        _string(value)
        return
    if type(value) is list:
        for item in value:
            _validate(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _need(type(key) is str, "OBJECT_KEY_STRING_REQUIRED")
            _string(key, key=True)
            _validate(item)
        return
    raise TypedCanonicalizationError(f"TYPE_NOT_ADMITTED:{type(value).__name__}")


def _encode_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _serialize(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if type(value) is int:
        return str(value)
    if type(value) is str:
        return _encode_string(value)
    if type(value) is list:
        return "[" + ",".join(_serialize(item) for item in value) + "]"
    if isinstance(value, Mapping):
        # Keys are restricted to ASCII; code-point and UTF-16 lexical ordering coincide.
        items = sorted(value.items(), key=lambda item: item[0])
        return "{" + ",".join(
            _encode_string(key) + ":" + _serialize(item) for key, item in items
        ) + "}"
    raise TypedCanonicalizationError(f"TYPE_NOT_ADMITTED:{type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Return canonical UTF-8 bytes for the admitted typed subset."""
    _validate(value)
    return _serialize(value).encode("utf-8", "strict")


def canonical_sha256(value: Any) -> str:
    """Hash an identity value with the canonicalization schema/version in the preimage."""
    envelope = {
        "canonicalization_schema": SCHEMA,
        "value": value,
    }
    return hashlib.sha256(canonical_bytes(envelope)).hexdigest()


def strict_loads(text: str) -> Any:
    """Parse JSON while rejecting duplicate keys and non-integer JSON numbers."""
    _need(type(text) is str, "JSON_TEXT_REQUIRED")

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise TypedCanonicalizationError("DUPLICATE_OBJECT_KEY")
            out[key] = value
        return out

    def reject_float(_: str) -> Any:
        raise TypedCanonicalizationError("FLOAT_FORBIDDEN_USE_EXPLICIT_FIXED_POINT_INTEGER")

    def reject_constant(_: str) -> Any:
        raise TypedCanonicalizationError("NON_JSON_NUMBER_FORBIDDEN")

    try:
        value = json.loads(
            text,
            object_pairs_hook=pairs_hook,
            parse_float=reject_float,
            parse_constant=reject_constant,
        )
    except TypedCanonicalizationError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise TypedCanonicalizationError("INVALID_JSON") from exc
    _validate(value)
    return value
