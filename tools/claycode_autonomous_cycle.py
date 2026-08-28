#!/usr/bin/env python3
"""Fail-closed direct entrypoint for the provider-capable autonomous ClayCode cycle.

The historical implementation lives in ``claycode_autonomous_cycle_legacy_impl.py``.
This shim intentionally imports only standard-library modules plus the standard-library-only
authority gate before any secret loader or provider-capable module can be imported.
"""
from __future__ import annotations

import json
import runpy
from pathlib import Path

from claycode_autonomous_provider_gate import check_inbox

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "tools/claycode_autonomous_cycle_legacy_impl.py"


def main() -> int:
    decision = check_inbox()
    if decision.get("admitted") is not True:
        print(json.dumps({
            "status": "SKIPPED_PROVIDER_AUTHORITY",
            "entrypoint": "DIRECT_CLI_GATED",
            "provider_calls": 0,
            "secret_lookups": 0,
            "authority": decision,
        }, sort_keys=True))
        return 0

    # This boundary is crossed only after explicit current authority admits provider use.
    runpy.run_path(str(IMPL), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
