#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rae_core.ledger_chain import (  # noqa: E402
    GENESIS_PATH,
    LedgerChainError,
    load_genesis,
    verify_ledger,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify tamper-evident RAE JSONL ledger chains.")
    ap.add_argument(
        "--ledger",
        action="append",
        default=[],
        help="Repository-relative ledger path; repeat for multiple ledgers. Default: all anchored ledgers.",
    )
    ap.add_argument(
        "--genesis",
        default=str(GENESIS_PATH),
        help="Genesis anchor JSON path.",
    )
    args = ap.parse_args()

    genesis_path = Path(args.genesis)
    if not genesis_path.is_absolute():
        genesis_path = ROOT / genesis_path
    doc = load_genesis(genesis_path)
    ledger_keys = args.ledger or sorted(doc["ledgers"])

    reports = []
    errors = []
    for key in ledger_keys:
        path = Path(key)
        if not path.is_absolute():
            path = ROOT / path
        try:
            reports.append(
                verify_ledger(path, genesis_path=genesis_path, ledger_key=str(key))
            )
        except Exception as exc:
            errors.append({"ledger": str(key), "error": str(exc)})

    result = {
        "schema": "RAE_LEDGER_CHAIN_VERIFY_RESULT/v1",
        "ok": not errors,
        "genesis": str(genesis_path.relative_to(ROOT)) if genesis_path.is_relative_to(ROOT) else str(genesis_path),
        "reports": reports,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
