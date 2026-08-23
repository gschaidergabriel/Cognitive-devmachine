#!/usr/bin/env python3
"""Compatibility entry point for the current fail-closed EntityOS + HCU authority guard.

The filename and imported validator module retain historical names for workflow/receipt
compatibility. Their names are not product authority. Current work-selection authority
comes from the EntityOS/HCU validator bound to SUPERVISOR_STEERING_8_52.
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
    LEGACY_EXPECTED_CONTROL,
    validate,
)

ASSERTION_SCHEMA = "EFFECTIVE_PROGRAM_AUTHORITY_ASSERTION/v3"
CURRENT_AUTHORITY_CHAIN = (
    f"{LEGACY_EXPECTED_CONTROL}+SUPERVISOR_STEERING_8_52-current-authority-correction"
)


def _payload(status: str, errors: list[str] | None = None) -> dict:
    payload = {
        "schema": ASSERTION_SCHEMA,
        "status": status,
        "program": CURRENT_PROGRAM,
        "stage": CURRENT_STAGE,
        "product": CURRENT_PRODUCT,
        "compute_architecture": CURRENT_COMPUTE_ARCHITECTURE,
        "effective_authority": CURRENT_AUTHORITY_CHAIN,
        "authority_validator": CURRENT_SCHEMA,
        "legacy_validator_filename": "validate_clayverse_authority_consistency.py",
        "legacy_filename_scope": "COMPATIBILITY_NAME_ONLY_NOT_CURRENT_PRODUCT_AUTHORITY",
        "credit": (
            "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT"
            if status == "PASS"
            else "ZERO_RUNTIME_CREDIT"
        ),
    }
    if errors:
        payload["errors"] = errors
    return payload


def main() -> int:
    result = validate(ROOT)
    if not result.get("pass"):
        print(json.dumps(_payload("FAIL", list(result.get("errors", []))), sort_keys=True))
        return 2
    print(json.dumps(_payload("PASS"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
