#!/usr/bin/env python3
"""Fail-closed authority gate for the external freepool fallback path.

This gate is intentionally standard-library only and safe to execute BEFORE any
credential lookup, provider SDK import, network request, Aider invocation, or fallback
model selection.  It reuses the canonical autonomous provider authority evaluator so
`stern.py -> harness_aider.py -> ~/last-resort/llm.py` cannot treat actor-registry prose
as execution authority.

Exit codes:
  0  provider route explicitly admitted by current authority
  77 provider route blocked / stale / malformed authority

Current HARD_OFF is expected to return 77.  Callers MUST stop before secret lookup or
provider/network work on any nonzero exit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from claycode_autonomous_provider_gate import check_inbox  # noqa: E402


def decision_record() -> dict:
    decision = check_inbox()
    admitted = decision.get("admitted") is True
    return {
        "schema": "FREEPOOL_FALLBACK_PROVIDER_GATE/v1",
        "admitted": admitted,
        "reason": decision.get("reason", "UNKNOWN"),
        "authority_schema_version": decision.get("schema_version"),
        "runtime_provider_authority": decision.get("runtime_provider_authority"),
        "required_caller_behavior": (
            "MAY_CONTINUE_TO_PROVIDER_PATH"
            if admitted
            else "STOP_BEFORE_SECRET_LOOKUP_PROVIDER_IMPORT_NETWORK_OR_AIDER_FALLBACK"
        ),
        "provider_calls_before_gate": 0,
        "secret_lookups_before_gate": 0,
    }


def main() -> int:
    record = decision_record()
    print(json.dumps(record, sort_keys=True))
    return 0 if record["admitted"] else 77


if __name__ == "__main__":
    raise SystemExit(main())
