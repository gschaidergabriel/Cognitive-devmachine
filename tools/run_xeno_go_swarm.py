#!/usr/bin/env python3
"""Canonical Xeno implementation-codename GO entrypoint for EntityOS/HCU.

This launcher resolves the current supervisor dynamically, validates the three-track
EntityOS/HCU contract, requires the Xeno active-build controls, and then transfers
execution to the implementation-focused 6000-logical-worker fabric. It never reads
provider secrets during preflight and does not create a competing product identity.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
SUPERVISOR_INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
WORKER_PROTOCOL = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
BUILD_DIRECTIVE = ROOT / "research_entity/claycode/XENO_V1_ACTIVE_BUILD_AND_RECURSIVE_IMPROVEMENT_DIRECTIVE_2026-08-24.md"
BUILD_STATE = ROOT / "research_entity/claycode/XENO_ACTIVE_BUILD_STATE.json"
CONTROLLER = ROOT / "tools/run_xeno_active_build_swarm.py"
PROMOTION_GATE = ROOT / "tools/xeno_build_gate.py"

PROGRAM = "ENTITYOS_HCU"
PROGRAM_ID = "entityos-hcu"
PRODUCT = "EntityOS"
COMPUTE_ARCH = "HCU"
COMPAT_PROTOCOL_BEGIN = "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
CURRENT_PROTOCOL_MARKER = "[ENTITYOS/HCU CURRENT AUTHORITY]"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"NOT_OBJECT:{path}")
    return value


def require(ok: bool, code: str) -> None:
    if not ok:
        raise RuntimeError(code)


def resolve_supervisor(inbox: dict) -> tuple[Path, dict]:
    steering = inbox.get("steering")
    require(isinstance(steering, str) and steering, "SUPERVISOR_STEERING_POINTER_MISSING")
    path = (ROOT / steering).resolve()
    require(ROOT.resolve() in path.parents, "SUPERVISOR_STEERING_POINTER_ESCAPES_REPO")
    require(path.exists(), "SUPERVISOR_STEERING_TARGET_MISSING")
    return path, load_json(path)


def preflight() -> dict:
    bootstrap = load_json(BOOTSTRAP)
    state = load_json(PROGRAM_STATE)
    inbox = load_json(SUPERVISOR_INBOX)
    authority_path, authority = resolve_supervisor(inbox)
    build_state = load_json(BUILD_STATE)

    require(bootstrap.get("active_program") == PROGRAM, "BOOTSTRAP_PROGRAM_MISMATCH")
    require(bootstrap.get("product_endpoint") == PRODUCT, "BOOTSTRAP_PRODUCT_MISMATCH")
    require(bootstrap.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH, "BOOTSTRAP_HCU_ARCH_MISMATCH")
    tracks = bootstrap.get("go_required_tracks") or []
    require("ENTITYOS_EXECUTABLE_CONVERGENCE" in tracks, "BOOTSTRAP_TRACK_A_MISSING")
    require("HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT_OR_HCU_NO_CHANGE_WITH_REASON" in tracks, "BOOTSTRAP_TRACK_B_MISSING")
    require("GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS_OR_NO_CHANGE_WITH_REASON" in tracks, "BOOTSTRAP_TRACK_C_MISSING")

    require(state.get("program_id") == PROGRAM_ID, "PROGRAM_STATE_ID_MISMATCH")
    require(state.get("product") == PRODUCT, "PROGRAM_STATE_PRODUCT_MISMATCH")
    require(state.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH, "PROGRAM_STATE_HCU_ARCH_MISMATCH")
    state_tracks = state.get("go_required_tracks") or {}
    require(state_tracks.get("track_a") == "ENTITYOS_EXECUTABLE_CONVERGENCE", "PROGRAM_TRACK_A_MISSING")
    require(state_tracks.get("track_b") == "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT", "PROGRAM_TRACK_B_MISSING")
    require(state_tracks.get("track_c") == "GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS", "PROGRAM_TRACK_C_MISSING")

    require(inbox.get("active_program") == PROGRAM, "INBOX_PROGRAM_MISMATCH")
    require(inbox.get("product") == PRODUCT, "INBOX_PRODUCT_MISMATCH")
    require(inbox.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH, "INBOX_HCU_ARCH_MISMATCH")
    require(str(inbox.get("schema_version")) == str(authority.get("schema_version")), "SUPERVISOR_EPOCH_MISMATCH")
    require(authority.get("active_program") == PROGRAM, "AUTHORITY_PROGRAM_MISMATCH")
    require(authority.get("product") == PRODUCT, "AUTHORITY_PRODUCT_MISMATCH")
    require(authority.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH, "AUTHORITY_HCU_ARCH_MISMATCH")
    require((authority.get("free_only") or {}).get("no_paid_fallback") is True, "AUTHORITY_NO_PAID_FALLBACK_MISSING")

    require(BUILD_DIRECTIVE.exists(), "XENO_BUILD_DIRECTIVE_MISSING")
    require(build_state.get("mode") == "ACTIVE_BUILD_THEN_RECURSIVE_IMPROVEMENT", "XENO_BUILD_MODE_MISMATCH")
    require(build_state.get("implementation_codename") == "Xeno", "XENO_CODENAME_MISMATCH")
    require(build_state.get("target_core_class") == "APPROX_0_8B_FINE_TUNED", "XENO_08B_TARGET_MISSING")
    require(build_state.get("recursive_until_superseded") is True, "XENO_RECURSION_NOT_ARMED")

    for path, code in (
        (WORKER_PROTOCOL, "WORKER_PROTOCOL_MISSING"),
        (CONTROLLER, "XENO_CONTROLLER_MISSING"),
        (PROMOTION_GATE, "XENO_PROMOTION_GATE_MISSING"),
    ):
        require(path.exists(), code)
    worker_text = WORKER_PROTOCOL.read_text(encoding="utf-8")
    require(COMPAT_PROTOCOL_BEGIN in worker_text, "COMPAT_PROTOCOL_ABI_MARKER_MISSING")
    require(CURRENT_PROTOCOL_MARKER in worker_text, "ENTITYOS_HCU_PROTOCOL_MARKER_MISSING")
    require("Sole current product/system: EntityOS." in worker_text, "ENTITYOS_PROTOCOL_AUTHORITY_MISSING")
    require("Sole current integrated cognition/compute architecture: HCU." in worker_text, "HCU_PROTOCOL_AUTHORITY_MISSING")

    attested = (os.getenv("CLAY_FREE_ONLY_ATTESTED") or "").strip().lower()
    require(attested in {"1", "true", "yes", "on", "attested"}, "CLAY_FREE_ONLY_ATTESTED_REQUIRED")
    return {
        "supervisor": str(authority_path.relative_to(ROOT)),
        "supervisor_epoch": authority.get("schema_version"),
        "build_mode": build_state.get("mode"),
    }


def main() -> int:
    try:
        info = preflight()
    except Exception as exc:
        print(f"XENO_ACTIVE_GO_ADMISSION_FAIL:{exc}", file=sys.stderr)
        return 5
    print(json.dumps({"schema": "XENO_ACTIVE_GO_PREFLIGHT/v1", "status": "PASS", **info}, sort_keys=True))
    os.execv(sys.executable, [sys.executable, str(CONTROLLER), *sys.argv[1:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
