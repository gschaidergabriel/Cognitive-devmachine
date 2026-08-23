#!/usr/bin/env python3
"""Fail-closed admission shim for the canonical Mini Entity GO/ZERO swarm.

This shim validates current Mini Entity program/control/worker/HCU authority before
handing off to `tools/run_go_zero_swarm.py`. It does not inspect provider secrets.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
CONTROL = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_5_MINI_ENTITY_GO_AUTHORITY.json"
OWNER = ROOT / "research_entity/global/MINI_ENTITY_GO_OWNER_DIRECTIVE.md"
PROTOCOL = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
ROOT_CLAUDE = ROOT / "CLAUDE.md"
HCU_ARCH = ROOT / "the artefact/MicroEntity/hcu/HCU_ARCHITECTURE.md"
MICROENTITY_ZIP = ROOT / "the artefact/MicroEntity/MICROENTITY_CURRENT.zip"
CONTROLLER = ROOT / "tools/run_go_zero_swarm.py"

PROGRAM = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
STAGE = "MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT"
PROGRAM_ID = "mini-entity-pipeline-all-in-one"
OWNER_REL = "research_entity/global/MINI_ENTITY_GO_OWNER_DIRECTIVE.md"
CONTROL_SCHEMA = "4.5-mini-entity-go-authority-addendum"
PROTOCOL_REL = "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
PROTOCOL_MARKER = "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
PROTOCOL_END_MARKER = "[/MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
ROOT_PROGRAM_MARKER = "PROGRAM=MINI_ENTITY_PIPELINE_ALL_IN_ONE"
ROOT_STAGE_MARKER = "STAGE=MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT"
STALE_ROOT_PROGRAM_MARKER = "PROGRAM=CLAYVERSE_SINGLE_CONTAINER"
HCU_MARKER = "Hyperposition Computational Unit"
HCU_PACKAGE_REL = "the artefact/MicroEntity/hcu/"
HCU_ZIP_REL = "the artefact/MicroEntity/MICROENTITY_CURRENT.zip"


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
    control = load_json(CONTROL)

    require(bootstrap.get("active_program") == PROGRAM, "BOOTSTRAP_PROGRAM_MISMATCH")
    require(bootstrap.get("active_stage") == STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(bootstrap.get("sole_owner_directive") == OWNER_REL, "BOOTSTRAP_OWNER_MISMATCH")
    require(bootstrap.get("all_worker_protocol") == PROTOCOL_REL, "BOOTSTRAP_WORKER_PROTOCOL_MISMATCH")
    require(bootstrap.get("free_only") is True, "BOOTSTRAP_FREE_ONLY_MISSING")
    require(bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_NOT_FORBIDDEN")
    require(bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_SANDBOX_ONLY", "BOOTSTRAP_SANDBOX_ONLY_MISSING")
    require(bootstrap.get("vps_testing") == "FORBIDDEN", "BOOTSTRAP_VPS_TESTING_NOT_FORBIDDEN")

    require(state.get("program_id") == PROGRAM_ID, "PROGRAM_STATE_ID_MISMATCH")
    require(state.get("stage") == STAGE, "PROGRAM_STATE_STAGE_MISMATCH")
    require(state.get("owner_directive") == OWNER_REL, "PROGRAM_STATE_OWNER_MISMATCH")
    policy = state.get("execution_policy") or {}
    require(policy.get("free_only") is True, "PROGRAM_STATE_FREE_ONLY_MISSING")
    require(policy.get("together_forbidden") is True, "PROGRAM_STATE_TOGETHER_NOT_FORBIDDEN")
    require(policy.get("isolated_sandbox_only") is True, "PROGRAM_STATE_SANDBOX_ONLY_MISSING")
    require(policy.get("vps_testing_forbidden") is True, "PROGRAM_STATE_VPS_TESTING_NOT_FORBIDDEN")

    require(control.get("schema_version") == CONTROL_SCHEMA, "CONTROL_45_SCHEMA_MISMATCH")
    require(control.get("status") == "ACTIVE", "CONTROL_45_NOT_ACTIVE")
    require(control.get("mode") == "FREE_ONLY", "CONTROL_45_NOT_FREE_ONLY")
    owner = control.get("owner_program_authority") or {}
    require(owner.get("owner_directive_path") == OWNER_REL, "CONTROL_45_OWNER_MISMATCH")
    require(owner.get("active_program") == PROGRAM, "CONTROL_45_PROGRAM_MISMATCH")
    require(owner.get("stage") == STAGE, "CONTROL_45_STAGE_MISMATCH")

    require(OWNER.exists(), "OWNER_DIRECTIVE_MISSING")
    require(CONTROLLER.exists(), "COORDINATED_SWARM_CONTROLLER_MISSING")
    require(HCU_ARCH.exists(), "HCU_ARCHITECTURE_MISSING")
    require(MICROENTITY_ZIP.exists(), "MICROENTITY_ZIP_MISSING")

    owner_text = OWNER.read_text(encoding="utf-8")
    require(HCU_MARKER in owner_text, "OWNER_HCU_WORKSTREAM_MISSING")
    require(HCU_PACKAGE_REL in owner_text, "OWNER_HCU_PACKAGE_PATH_MISSING")
    require(HCU_ZIP_REL in owner_text, "OWNER_HCU_ZIP_PATH_MISSING")

    protocol_text = PROTOCOL.read_text(encoding="utf-8")
    require(PROTOCOL_MARKER in protocol_text, "WORKER_PROTOCOL_MARKER_MISSING")
    require(PROTOCOL_END_MARKER in protocol_text, "WORKER_PROTOCOL_END_MARKER_MISSING")
    require(OWNER_REL in protocol_text, "WORKER_PROTOCOL_OWNER_MISMATCH")
    require(PROGRAM in protocol_text, "WORKER_PROTOCOL_PROGRAM_MISMATCH")
    require(STAGE in protocol_text, "WORKER_PROTOCOL_STAGE_MISMATCH")
    require(HCU_MARKER in protocol_text, "WORKER_PROTOCOL_HCU_WORKSTREAM_MISSING")
    require(HCU_PACKAGE_REL in protocol_text, "WORKER_PROTOCOL_HCU_PACKAGE_PATH_MISSING")
    require(HCU_ZIP_REL in protocol_text, "WORKER_PROTOCOL_HCU_ZIP_PATH_MISSING")

    root_text = ROOT_CLAUDE.read_text(encoding="utf-8")
    require(ROOT_PROGRAM_MARKER in root_text, "ROOT_CLAUDE_PROGRAM_MISMATCH")
    require(ROOT_STAGE_MARKER in root_text, "ROOT_CLAUDE_STAGE_MISMATCH")
    require(OWNER_REL in root_text, "ROOT_CLAUDE_OWNER_MISMATCH")
    require(HCU_MARKER in root_text, "ROOT_CLAUDE_HCU_WORKSTREAM_MISSING")
    require(HCU_PACKAGE_REL in root_text, "ROOT_CLAUDE_HCU_PACKAGE_PATH_MISSING")
    require(HCU_ZIP_REL in root_text, "ROOT_CLAUDE_HCU_ZIP_PATH_MISSING")
    require(STALE_ROOT_PROGRAM_MARKER not in root_text, "ROOT_CLAUDE_STALE_CLAYVERSE_PROGRAM")

    attested = (os.getenv("CLAY_FREE_ONLY_ATTESTED") or "").strip().lower()
    require(attested in {"1", "true", "yes", "on", "attested"}, "CLAY_FREE_ONLY_ATTESTED_REQUIRED")


def main() -> int:
    try:
        preflight()
    except Exception as exc:
        print(f"MINI_ENTITY_GO_SWARM_ADMISSION_FAIL:{exc}", file=sys.stderr)
        return 5
    os.execv(sys.executable, [sys.executable, str(CONTROLLER), *sys.argv[1:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
