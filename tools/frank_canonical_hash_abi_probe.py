#!/usr/bin/env python3
"""FRANK canonical-hash ABI portability probe.

Executable negative-result probe derived from RFC 8785 requirements.
It does not implement JCS and does not change FRANK state. It only demonstrates
whether Python's ordinary json.dumps(sort_keys=True) can be treated as a JCS
cross-runtime hash ABI for specific normative edge cases.
"""
from __future__ import annotations
import hashlib
import json
import platform
from typing import Any

SCHEMA = "frank-canonical-hash-abi-probe-1"


def py_json(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def utf16_units(s: str) -> tuple[int, ...]:
    b = s.encode("utf-16-be")
    return tuple(int.from_bytes(b[i:i+2], "big") for i in range(0, len(b), 2))


def sha256_json(v: Any) -> str:
    return hashlib.sha256(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    # RFC 8785 §3.2.3 requires property sorting by unsigned UTF-16 code units.
    keys = ["\ue000", "\U0001f600"]
    python_order = sorted(keys)
    jcs_utf16_order = sorted(keys, key=utf16_units)

    # RFC 8785 Appendix B exact ECMAScript-compatible number vectors.
    cases = [
        {
            "id": "utf16_property_order",
            "python": [f"U+{ord(x):04X}" for x in python_order],
            "rfc8785_expected": [f"U+{ord(x):04X}" for x in jcs_utf16_order],
            "diverges": python_order != jcs_utf16_order,
        },
        {
            "id": "minus_zero",
            "python": py_json(-0.0),
            "rfc8785_expected": "0",
            "diverges": py_json(-0.0) != "0",
        },
        {
            "id": "one_e_minus_six",
            "python": py_json(1e-6),
            "rfc8785_expected": "0.000001",
            "diverges": py_json(1e-6) != "0.000001",
        },
    ]

    finite_rejection = {}
    for name, value in (("nan", float("nan")), ("pos_inf", float("inf")), ("neg_inf", float("-inf"))):
        try:
            py_json(value)
            finite_rejection[name] = False
        except ValueError:
            finite_rejection[name] = True

    divergence_count = sum(bool(c["diverges"]) for c in cases)
    result = {
        "schema": SCHEMA,
        "actor": {"actor_id": "chatgpt-secondary", "provider": "OpenAI", "model": "GPT-5.6 Sol"},
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "reference": "RFC 8785 JSON Canonicalization Scheme",
        "cases": cases,
        "positive_control": {"python_allow_nan_false_rejects_nonfinite": finite_rejection},
        "synthesis": {
            "divergence_count": divergence_count,
            "finding": "PYTHON_JSON_SORT_KEYS_NOT_JCS_HASH_ABI" if divergence_count else "NO_DIVERGENCE_OBSERVED",
            "scope": "specific normative edge cases only; not a full JCS conformance suite",
            "architecture_implication": "version a canonical hash ABI before Python-to-Clay/native state-hash interoperability",
            "promotion": "NONE",
        },
    }
    result["receipt_sha256"] = sha256_json(result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if divergence_count == len(cases) and all(finite_rejection.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
