#!/usr/bin/env python3
"""Current-authority entrypoint for the adaptive EntityOS/HCU research swarm."""
from __future__ import annotations

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_free_go_swarm as base
from entityos_worker_authority import WorkerAuthorityError, install_worker_authority

try:
    install_worker_authority(base, ROOT)
except WorkerAuthorityError as exc:
    raise SystemExit(f"WORKER_AUTHORITY_FAIL_CLOSED:{exc}")

import run_24h_entityos_swarm as driver


if __name__ == "__main__":
    raise SystemExit(asyncio.run(driver.main(driver.parse_args())))
