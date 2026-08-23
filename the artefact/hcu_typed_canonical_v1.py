#!/usr/bin/env python3
"""Versioned cross-language canonical identity bytes for EntityOS/HCU.

This is intentionally NOT advertised as a full RFC 8785 JCS implementation. It is a
smaller typed equivalent for identity-bearing HCU / Typed Entry envelopes. The domain
is restricted so independent implementations can reproduce exactly the same bytes
without depending on host JSON float formatting, Unicode key collation, locale, or
map iteration order.

Contract ENTITYOS_HCU_TYPED_CANONICAL/v1:
- root/value types: null, bool, safe integer, Unicode scalar string, list/tuple, mapping;
- floats are forbidden; identity-bearing fractional values must enter through an
  explicitly typed higher-level representation (for example integer basis points or a
  schema-defined decimal string) before canonicalization;
- integers are restricted to the exact IEEE-754 / I-JSON safe range;
- mapping keys are printable 7-bit ASCII strings, unique by the mapping abstraction,
  and sorted by unsigned ASCII byte order;
- string values preserve Unicode exactly as supplied; no normalization is performed;
- control characters use one fixed lowercase JSON escape representation;
- no whitespace is emitted;
- identity SHA-256 is domain-separated by the exact contract schema/version.

The module grants no truth, effect, state, provider, or model authority.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

SCHEMA = "ENTITYOS_HCU_TYPED_CANONICAL/v1"
DOMAIN_PREFIX = (SCHEMA + "\x00").encode("ascii")
SAFE_INTEGER_MIN = -(2**53 - 1)
SAFE_INTEGER_MAX = 2**53 - 1


class CanonicalizationError(ValueError):
    pass


def _ascii_key(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise CanonicalizationError("OBJECT_KEY_NONEMPTY_STRING_REQUIRED")
    try:
        raw = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise CanonicalizationError("OBJECT_KEY_PRINTABLE_ASCII_REQUIRED") from exc
    if any(byte < 0x20 or byte > 0x7E for byte in raw):
        raise CanonicalizationError("OBJECT_KEY_PRINTABLE_ASCII_REQUIRED")
    return value


def _quote_string(value: str) -> bytes:
    if not isinstance(value, str):
        raise CanonicalizationError("STRING_REQUIRED")
    out = bytearray(b'"')
    escapes = {
        0x08: b"\\b",
        0x09: b"\\t",
        0x0A: b"\\n",
        0x0C: b"\\f",
        0x0D: b"\\r",
        0x22: b'\\"',
        0x5C: b"\\\\",
    }
    for ch in value:
        cp = ord(ch)
        if 0xD800 <= cp <= 0xDFFF:
            raise CanonicalizationError("UNICODE_SURROGATE_FORBIDDEN")
        escaped = escapes.get(cp)
        if escaped is not None:
            out.extend(escaped)
        elif cp < 0x20:
            out.extend(f"\\u{cp:04x}".encode("ascii"))
        else:
            out.extend(ch.encode("utf-8"))
    out.extend(b'"')
    return bytes(out)


def canonical_bytes(value: Any) -> bytes:
    """Return exact v1 canonical bytes or fail closed for values outside the typed domain."""
    if value is None:
        return b"null"
    if isinstance(value, bool):
        return b"true" if value else b"false"
    if isinstance(value, int):
        if not SAFE_INTEGER_MIN <= value <= SAFE_INTEGER_MAX:
            raise CanonicalizationError("INTEGER_OUTSIDE_IJSON_SAFE_RANGE")
        return str(value).encode("ascii")
    if isinstance(value, float):
        raise CanonicalizationError("FLOAT_FORBIDDEN_USE_SCHEMA_TYPED_REPRESENTATION")
    if isinstance(value, str):
        return _quote_string(value)
    if isinstance(value, (list, tuple)):
        return b"[" + b",".join(canonical_bytes(item) for item in value) + b"]"
    if isinstance(value, Mapping):
        keys = [_ascii_key(key) for key in value.keys()]
        keys.sort(key=lambda item: item.encode("ascii"))
        members = []
        for key in keys:
            members.append(_quote_string(key) + b":" + canonical_bytes(value[key]))
        return b"{" + b",".join(members) + b"}"
    raise CanonicalizationError("TYPE_OUTSIDE_TYPED_CANONICAL_DOMAIN")


def identity_sha256(value: Any) -> str:
    """Domain-separated identity digest for the exact v1 canonical contract."""
    return hashlib.sha256(DOMAIN_PREFIX + canonical_bytes(value)).hexdigest()
