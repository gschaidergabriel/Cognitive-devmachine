#!/usr/bin/env python3
"""Compatibility entry point for the current fail-closed EntityOS/HCU authority assertion.

The filename and import path are retained because existing workflows/receipts may call
this entry point. Current product selection comes from the EntityOS/HCU consistency
validator; historical ClayVerse control names are provenance/safety donors only.
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

PROGRAM = "ENTITYOS_HCU"
STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
PRODUCT = "EntityOS"
COMPUTE_ARCHITECTURE = "HCU"
VALIDATOR_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v1"


def main() -> int:
    result = validate(ROOT)
    payload = {
        "schema": "EFFECTIVE_PROGRAM_AUTHORITY_ASSERTION/v3",
        "status": "PASS" if result.get("pass") else "FAIL",
        "program": PROGRAM,
        "stage": STAGE,
        "product": PRODUCT,
        "compute_architecture": COMPUTE_ARCHITECTURE,
        "authority_validator": VALIDATOR_SCHEMA,
        "errors": result.get("errors", []),
        "credit": (
            "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT"
            if result.get("pass")
            else "ZERO_RUNTIME_CREDIT"
        ),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if result.get("pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
