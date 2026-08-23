#!/usr/bin/env python3
"""Fail-closed admission shim for the current Xeno GO/ZERO controller.

This shim performs source/control-plane checks only. It does not inspect provider
secrets and will not execute a stale Mini Entity/ClayVerse controller. A child
controller is admitted only when it literally contains the current Xeno dual-track
markers so future `go` cannot silently lose XCU/Entry co-development.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
OWNER = ROOT / "research_entity/global/XENO_GO_OWNER_DIRECTIVE.md"
WORKER_PROTOCOL = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
RESEARCH_FUSION = ROOT / "research_entity/global/XENO_COMPUTATIONAL_UNIT_RESEARCH_FUSION_2026-08-23.md"
CONTROLLER = ROOT / "tools/run_go_zero_swarm.py"

PROGRAM = "ENTITYOS_HCU_XENO"
STAGE = "XENO_COMPUTATIONAL_UNIT_BOOTSTRAP"
PROGRAM_ID = "entityos-hcu-xeno"
OWNER_REL = "research_entity/global/XENO_GO_OWNER_DIRECTIVE.md"

REQUIRED_CONTROLLER_MARKERS = (
    "Xeno",
    "XENO_EXECUTABLE_CONVERGENCE",
    "XCU_AND_ENTRY_FABRIC_CO_DEVELOPMENT",
    "XENO_GRID10",
    "XENO_COGSIM10",
    "XENO_WM_TEST",
    "XENO_NESTED_SIM",
    "XENO_SCALEOUT",
)


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"NOT_OBJECT:{path}")
    return value


def require(ok: bool, code: str) -> None:
    if not ok:
        raise RuntimeError(code)


def preflight() -> None:
    bootstrap = load_json(BOOTSTRAP)
    state = load_json(PROGRAM_STATE)

    require(bootstrap.get("active_program") == PROGRAM, "BOOTSTRAP_PROGRAM_MISMATCH")
    require(bootstrap.get("active_stage") == STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(bootstrap.get("go_owner_directive") == OWNER_REL, "BOOTSTRAP_OWNER_MISMATCH")
    require(bootstrap.get("go_operational_start") == "XENO_CURRENT_IMPLEMENTATION", "BOOTSTRAP_XENO_START_MISSING")
    require(bootstrap.get("entry_fabric") == "MANDATORY_CO_DEVELOPMENT", "BOOTSTRAP_ENTRY_CO_DEVELOPMENT_MISSING")
    require(bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_NOT_FORBIDDEN")
    require(bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_SANDBOX_ONLY", "BOOTSTRAP_SANDBOX_ONLY_MISSING")

    require(state.get("program_id") == PROGRAM_ID, "PROGRAM_STATE_ID_MISMATCH")
    require(state.get("stage") == STAGE, "PROGRAM_STATE_STAGE_MISMATCH")
    require(state.get("owner_directive") == OWNER_REL, "PROGRAM_STATE_OWNER_MISMATCH")
    tracks = state.get("go_required_tracks") or {}
    require(tracks.get("track_a") == "XENO_EXECUTABLE_CONVERGENCE", "PROGRAM_TRACK_A_MISSING")
    require(tracks.get("track_b") == "XCU_AND_ENTRY_FABRIC_CO_DEVELOPMENT", "PROGRAM_TRACK_B_MISSING")

    require(OWNER.exists(), "XENO_OWNER_DIRECTIVE_MISSING")
    require(WORKER_PROTOCOL.exists(), "WORKER_PROTOCOL_MISSING")
    require(RESEARCH_FUSION.exists(), "XENO_RESEARCH_FUSION_MISSING")
    require(CONTROLLER.exists(), "COORDINATED_CONTROLLER_MISSING")

    worker_text = WORKER_PROTOCOL.read_text(encoding="utf-8")
    require("[XENO :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]" in worker_text, "XENO_WORKER_PROTOCOL_MARKER_MISSING")
    require("XENO_EXECUTABLE_CONVERGENCE" in worker_text, "WORKER_TRACK_A_MISSING")
    require("XCU_AND_ENTRY_FABRIC_CO_DEVELOPMENT" in worker_text, "WORKER_TRACK_B_MISSING")

    # Fail closed on the old controller until its own source is transition-aware.
    controller_text = CONTROLLER.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_CONTROLLER_MARKERS if marker not in controller_text]
    require(not missing, "CONTROLLER_NOT_XENO_ADMITTED:" + ",".join(missing))

    attested = (os.getenv("CLAY_FREE_ONLY_ATTESTED") or "").strip().lower()
    require(attested in {"1", "true", "yes", "on", "attested"}, "CLAY_FREE_ONLY_ATTESTED_REQUIRED")


def main() -> int:
    try:
        preflight()
    except Exception as exc:
        print(f"XENO_GO_SWARM_ADMISSION_FAIL:{exc}", file=sys.stderr)
        return 5

    os.execv(sys.executable, [sys.executable, str(CONTROLLER), *sys.argv[1:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
