#!/usr/bin/env python3
"""Apply Supervisor-8.72 conversion backpressure, then enter the canonical 24h swarm.

The wrapper exists so the already-stable 24h driver does not need a second
throughput-authority implementation. It changes only inherited concurrency env
limits and then execs the canonical entrypoint in the same process slot.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import free_swarm_conversion_backpressure_872 as conversion_backpressure

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "tools" / "run_24h_entityos_swarm.py"


def main() -> int:
    receipt = conversion_backpressure.apply()
    print(json.dumps(receipt, sort_keys=True, ensure_ascii=False), flush=True)
    if not TARGET.is_file():
        raise SystemExit("canonical 24h swarm entrypoint missing")
    env = os.environ.copy()
    os.execvpe(
        sys.executable,
        [sys.executable, str(TARGET), *sys.argv[1:]],
        env,
    )
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
