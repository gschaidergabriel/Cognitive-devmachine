#!/usr/bin/env python3
"""Guarded entrypoint for the provider-capable autonomous ClayCode research cycle.

The provider authority gate executes before importing/running the legacy cycle. Therefore a
HARD_OFF, emergency stop, missing/malformed inbox, or stale authority cannot reach secret
lookup, provider discovery, rerank/embed, probe, or chat code.
"""
from __future__ import annotations

import json
import runpy
from pathlib import Path

from claycode_autonomous_provider_gate import check_inbox

ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT / "tools/claycode_autonomous_cycle.py"


def main() -> int:
    decision = check_inbox()
    if decision.get("admitted") is not True:
        print(json.dumps({
            "status": "SKIPPED_PROVIDER_AUTHORITY",
            "provider_calls": 0,
            "secret_lookups": 0,
            "authority": decision,
        }, sort_keys=True))
        return 0

    # Only an explicitly admitted current authority may cross this import/execution boundary.
    runpy.run_path(str(CYCLE), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
