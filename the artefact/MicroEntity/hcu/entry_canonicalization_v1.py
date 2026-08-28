#!/usr/bin/env python3
"""RFC 8785 JCS canonicalization for EntityOS/HCU causal identity.

This module is deterministic identity plumbing only. It is not canonical state,
truth, cognition, permission, recovery, or effect authority.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

CANONICALIZATION_SCHEMA = "RFC8785_JCS_IJSON/v1"
MAX_CANONICAL_NESTING_DEPTH = 256


class CanonicalizationError(ValueError):
    pass


def _string(value: str) -> bytes:
    if not isinstance(value, str):
        raise CanonicalizationError("STRING_REQUIRED")
    out: list[str] = ['"']
    for ch in value:
        cp = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif cp < 0x20:
            out.append(f"\\u{cp:04x}")
        elif 0xD800 <= cp <= 0xDFFF:
            raise CanonicalizationError("LONE_SURROGATE_FORBIDDEN")
        else:
            out.append(ch)
    out.append('"')
    try:
        return "".join(out).encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise CanonicalizationError("UNICODE_UTF8_REQUIRED") from exc


def _normalize_exponent(text: str) -> str:
    mantissa, exponent = text.lower().split("e", 1)
    sign = ""
    if exponent.startswith(("+", "-")):
        sign, exponent = exponent[0], exponent[1:]
    exponent = exponent.lstrip("0") or "0"
    if sign == "-" and exponent != "0":
        return f"{mantissa}e-{exponent}"
    return f"{mantissa}e+{exponent}"


def _scientific_parts(text: str) -> tuple[str, int]:
    text = text.lower()
    if "e" in text:
        mantissa, exponent_text = text.split("e", 1)
        exponent = int(exponent_text)
    else:
        mantissa, exponent = text, 0
    if "." in mantissa:
        whole, fraction = mantissa.split(".", 1)
        digits = whole + fraction
        exponent -= len(fraction)
    else:
        digits = mantissa
    return digits.lstrip("0") or "0", exponent


def _fixed_from_repr(text: str) -> str:
    digits, exponent = _scientific_parts(text)
    if digits == "0":
        return "0"
    decimal_pos = len(digits) + exponent
    if decimal_pos <= 0:
        return "0." + ("0" * (-decimal_pos)) + digits
    if decimal_pos >= len(digits):
        return digits + ("0" * (decimal_pos - len(digits)))
    rendered = digits[:decimal_pos] + "." + digits[decimal_pos:]
    return rendered.rstrip("0").rstrip(".")


def _number(value: int | float) -> bytes:
    if isinstance(value, bool):
        raise CanonicalizationError("BOOLEAN_IS_NOT_NUMBER")

    # JCS number serialization is defined over IEEE-754 binary64 values. Python's JSON
    # object model distinguishes arbitrary-precision int from float, but the wire-level
    # JSON number does not carry that host-language distinction. Accept integer values
    # iff their exact mathematical value is representable as a finite binary64, then feed
    # them through the same ECMAScript-compatible serialization path as floats. This
    # preserves RFC 8785 Appendix-B cases such as 2^53 and 2^68 while rejecting integers
    # (for example 2^53+1) that would require silent precision loss.
    if isinstance(value, int):
        try:
            binary64 = float(value)
        except OverflowError as exc:
            raise CanonicalizationError("INTEGER_NOT_EXACT_BINARY64") from exc
        if not math.isfinite(binary64) or int(binary64) != value:
            raise CanonicalizationError("INTEGER_NOT_EXACT_BINARY64")
        value = binary64
    else:
        value = float(value)

    if not math.isfinite(value):
        raise CanonicalizationError("FINITE_BINARY64_REQUIRED")

    # RFC 8785 verified erratum EID 7920: -0 is valid JSON syntax but JCS
    # serializes it indistinguishably from +0. Reject the signed-zero alias at
    # admission so distinct parsed inputs cannot collapse onto one causal hash.
    if value == 0.0 and math.copysign(1.0, value) < 0.0:
        raise CanonicalizationError("NEGATIVE_ZERO_FORBIDDEN")
    if value == 0.0:
        return b"0"
    if value < 0:
        return b"-" + _number(-value)

    text = repr(value).lower()
    if 1e-6 <= value < 1e21:
        rendered = _fixed_from_repr(text)
    elif "e" in text:
        rendered = _normalize_exponent(text)
    else:
        digits, exponent = _scientific_parts(text)
        exponent += len(digits) - 1
        mantissa = digits[0] + ("." + digits[1:] if len(digits) > 1 else "")
        rendered = f"{mantissa}e+{exponent}"
    return rendered.encode("ascii")


def _canonicalize(value: Any, depth: int) -> bytes:
    if depth > MAX_CANONICAL_NESTING_DEPTH:
        raise CanonicalizationError("MAX_NESTING_DEPTH_EXCEEDED")
    if value is None:
        return b"null"
    if value is True:
        return b"true"
    if value is False:
        return b"false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(value)
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, (list, tuple)):
        return b"[" + b",".join(_canonicalize(item, depth + 1) for item in value) + b"]"
    if isinstance(value, Mapping):
        rows: list[tuple[bytes, str, Any]] = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("OBJECT_STRING_KEYS_REQUIRED")
            try:
                sort_key = key.encode("utf-16be", "strict")
            except UnicodeEncodeError as exc:
                raise CanonicalizationError("LONE_SURROGATE_FORBIDDEN") from exc
            rows.append((sort_key, key, item))
        rows.sort(key=lambda row: row[0])
        return b"{" + b",".join(
            _string(key) + b":" + _canonicalize(item, depth + 1)
            for _, key, item in rows
        ) + b"}"
    raise CanonicalizationError(f"UNSUPPORTED_TYPE:{type(value).__name__}")


def canonicalize(value: Any) -> bytes:
    """Return RFC 8785/JCS UTF-8 bytes for an admitted I-JSON-compatible value.

    The input is depth-bounded so untrusted Typed Entry payloads fail through the
    canonical typed error channel instead of leaking Python recursion behavior.
    """
    return _canonicalize(value, 0)
