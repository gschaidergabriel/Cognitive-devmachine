#!/usr/bin/env python3
"""Compatibility entry point for the current fail-closed EntityOS/HCU authority assertion.

The historical filename remains callable by workflows and receipts. Product selection is
owned by the current consistency validator; this wrapper must report that same resolved
authority rather than re-emit a historical ClayVerse program label.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from validate_clayverse_authority_consistency import (
    CURRENT_COMPUTE_ARCHITECTURE,
    CURRENT_PRODUCT,
    CURRENT_PROGRAM,
    CURRENT_SCHEMA,
    CURRENT_STAGE,
    validate,
)

ASSERTION_SCHEMA = "EFFECTIVE_PROGRAM_AUTHORITY_ASSERTION/v3"


def assertion_payload(result: dict) -> dict:
    passed = result.get("pass") is True
    return {
        "schema": ASSERTION_SCHEMA,
        "status": "PASS" if passed else "FAIL",
        "program": CURRENT_PROGRAM,
        "stage": CURRENT_STAGE,
        "product": CURRENT_PRODUCT,
        "compute_architecture": CURRENT_COMPUTE_ARCHITECTURE,
        "authority_validator": CURRENT_SCHEMA,
        "errors": result.get("errors", []),
        "credit": (
            "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT"
            if passed
            else "ZERO_RUNTIME_CREDIT"
        ),
    }


def main() -> int:
    result = validate(ROOT)
    print(json.dumps(assertion_payload(result), sort_keys=True))
    return 0 if result.get("pass") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
