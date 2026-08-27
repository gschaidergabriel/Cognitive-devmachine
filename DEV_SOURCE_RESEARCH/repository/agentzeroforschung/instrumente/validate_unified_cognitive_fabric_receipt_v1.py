#!/usr/bin/env python3
"""Compatibility entry point for the canonical UCF runtime-receipt validator.

Semantic authority lives only in ``tools/validate_unified_cognitive_fabric_receipt_v1.py``.
This file intentionally contains no independent receipt schema or admission logic.
It preserves the historical file-based CLI and ``validate_receipt`` helper while
delegating every semantic decision to the canonical validator.

A PASS is source/mechanism evidence only. It does not create runtime/model/product
credit or replace exact-source execution provenance.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PATH = ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py"
_SPEC = importlib.util.spec_from_file_location("clay_ucf_runtime_receipt_v1_canonical", CANONICAL_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("CANONICAL_UCF_VALIDATOR_IMPORT_FAILED")
_CANONICAL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CANONICAL)

# Compatibility aliases only. They must not diverge from the canonical module.
RECEIPT_VERSION = _CANONICAL.SCHEMA
SCHEMA = _CANONICAL.SCHEMA
ReceiptError = _CANONICAL.ReceiptError
canonical_digest = _CANONICAL.canonical_digest


def validate_receipt(receipt: dict[str, Any]) -> list[str]:
    """Return legacy list-of-errors shape from the one canonical validator."""
    try:
        _CANONICAL.validate(receipt)
    except _CANONICAL.ReceiptError as exc:
        return [str(exc)]
    return []


def validate(receipt: dict[str, Any]) -> dict[str, Any]:
    """Expose the canonical result shape for callers that can migrate directly."""
    return _CANONICAL.validate(receipt)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        with args.receipt.open("r", encoding="utf-8") as handle:
            receipt = json.load(
                handle,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    _CANONICAL.ReceiptError(f"NONFINITE_JSON_CONSTANT:{value}")
                ),
            )
        result = _CANONICAL.validate(receipt)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
