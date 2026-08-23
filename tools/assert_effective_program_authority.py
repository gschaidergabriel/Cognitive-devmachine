#!/usr/bin/env python3
"""Compatibility entry point for the current fail-closed product-authority assertion.

The historical 4.1+4.2+4.3 Mini Entity assertion was correct for its then-current
bootstrap, but the 2026-08-23 owner product directive now selects ClayVerse. Keep one
assertion authority by delegating to the ClayVerse consistency validator rather than
leaving a competing Mini Entity gate active.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from validate_clayverse_authority_consistency import validate


def main() -> int:
    result = validate(ROOT)
    if not result.get("pass"):
        print(
            json.dumps(
                {
                    "schema": "EFFECTIVE_PROGRAM_AUTHORITY_ASSERTION/v2",
                    "status": "FAIL",
                    "program": "CLAYVERSE_SINGLE_CONTAINER",
                    "stage": "CLAYVERSE_ARTIFACT",
                    "effective_control": "4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+4.4-clayverse-product-authority-addendum",
                    "errors": result.get("errors", []),
                    "credit": "ZERO_RUNTIME_CREDIT",
                },
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "schema": "EFFECTIVE_PROGRAM_AUTHORITY_ASSERTION/v2",
                "status": "PASS",
                "program": "CLAYVERSE_SINGLE_CONTAINER",
                "stage": "CLAYVERSE_ARTIFACT",
                "effective_control": "4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+4.4-clayverse-product-authority-addendum",
                "authority_validator": "CLAYVERSE_AUTHORITY_CONSISTENCY/v2",
                "credit": "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
