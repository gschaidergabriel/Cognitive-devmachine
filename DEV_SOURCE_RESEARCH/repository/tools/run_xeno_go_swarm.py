#!/usr/bin/env python3
"""Canonical Xeno implementation-codename GO entrypoint for EntityOS/HCU.

Preflight resolves current machine-readable supervisor/provider authority, validates
Xeno active-build contracts, and transfers execution to the route/credential-gated
active build fabric. Historical worker-directive prose is not used as current authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

import xeno_current_authority_protocol as live_authority

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
BUILD_DIRECTIVE = ROOT / "research_entity/claycode/XENO_V1_ACTIVE_BUILD_AND_RECURSIVE_IMPROVEMENT_DIRECTIVE_2026-08-24.md"
BUILD_STATE = ROOT / "research_entity/claycode/XENO_ACTIVE_BUILD_STATE.json"
HARNESS_CONTRACT = ROOT / "the artefact/Xeno/XENO_HARNESS_V1_ACCEPTANCE_CONTRACT.md"
HARNESS_VALIDATOR = ROOT / "tools/xeno_harness_config.py"
CONTROLLER = ROOT / "tools/run_xeno_active_build_swarm.py"
PROMOTION_GATE = ROOT / "tools/xeno_build_gate.py"
ECONOMIC_GATE = ROOT / "tools/run_6000_free_swarm_v3.py"

PROGRAM = "ENTITYOS_HCU"
PROGRAM_ID = "entityos-hcu"
PRODUCT = "EntityOS"
COMPUTE_ARCH = "HCU"


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"NOT_OBJECT:{path}")
    return value


def require(ok: bool, code: str) -> None:
    if not ok:
        raise RuntimeError(code)


def preflight() -> dict:
    bootstrap = load_json(BOOTSTRAP)
    state = load_json(PROGRAM_STATE)
    build_state = load_json(BUILD_STATE)

    # Bootstrap/Program State remain structural mirrors. Their epoch may trail the
    # newest supervisor during concurrent convergence, so they cannot override the
    # live Inbox -> steering -> provider-admission chain below.
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

    authority = live_authority.resolve_current_authority(ROOT)
    protocol = live_authority.build_protocol(ROOT)
    require(protocol.startswith(live_authority.PROTOCOL_BEGIN), "LIVE_PROTOCOL_BEGIN_MISSING")
    require(protocol.endswith(live_authority.PROTOCOL_END), "LIVE_PROTOCOL_END_MISSING")
    require(live_authority.LIVE_MARKER in protocol, "LIVE_PROTOCOL_MARKER_MISSING")

    require(BUILD_DIRECTIVE.exists(), "XENO_BUILD_DIRECTIVE_MISSING")
    require(HARNESS_CONTRACT.exists(), "XENO_HARNESS_CONTRACT_MISSING")
    require(build_state.get("mode") == "ACTIVE_BUILD_THEN_INFINITE_RECURSIVE_IMPROVEMENT", "XENO_BUILD_MODE_MISMATCH")
    require(build_state.get("implementation_codename") == "Xeno", "XENO_CODENAME_MISMATCH")
    require(build_state.get("target_core_class") == "APPROX_0_8B_FINE_TUNED", "XENO_08B_TARGET_MISSING")
    require(build_state.get("recursive_on_every_go_until_superseded") is True, "XENO_PER_GO_RECURSION_NOT_ARMED")
    require(build_state.get("terminal_done_state_after_v1") is False, "XENO_TERMINAL_DONE_STATE_FORBIDDEN")
    require((build_state.get("recursive_promotion") or {}).get("gate_schema") == "XENO_PROMOTION_GATE/v2", "XENO_PROMOTION_V2_NOT_BOUND")

    harness = build_state.get("harness_requirements") or {}
    require(harness.get("internal_08b_switchable") is True, "XENO_INTERNAL_08B_SWITCH_MISSING")
    require(harness.get("external_llm_slots_max") == 2, "XENO_TWO_SLOT_LIMIT_MISSING")
    require(harness.get("prestage_switchable") is True, "XENO_PRESTAGE_SWITCH_MISSING")
    require(harness.get("grid10_logical_cells") == 10, "XENO_GRID10_REQUIREMENT_MISSING")
    require(harness.get("xeno_peer_link_required") == "XENO_PEER_LINK/v1", "XENO_PEER_LINK_REQUIREMENT_MISSING")

    for path, code in (
        (CONTROLLER, "XENO_CONTROLLER_MISSING"),
        (PROMOTION_GATE, "XENO_PROMOTION_GATE_MISSING"),
        (HARNESS_VALIDATOR, "XENO_HARNESS_VALIDATOR_MISSING"),
        (ECONOMIC_GATE, "FREE_LANE_ECONOMIC_GATE_MISSING"),
        (ROOT / "tools/xeno_current_authority_protocol.py", "XENO_LIVE_AUTHORITY_HELPER_MISSING"),
    ):
        require(path.exists(), code)

    attested = (os.getenv("CLAY_FREE_ONLY_ATTESTED") or "").strip().lower()
    require(attested in {"1", "true", "yes", "on", "attested"}, "CLAY_FREE_ONLY_ATTESTED_REQUIRED")
    return {
        "supervisor": authority["steering_path"],
        "supervisor_epoch": authority["epoch"],
        "provider_admission": authority["provider_admission_path"],
        "route_receipt_schema": authority["receipt_schema"],
        "route_implementation": authority["route_implementation"],
        "worker_authority_mode": "SYNTHESIZED_LIVE_MACHINE_READABLE_AUTHORITY",
        "worker_protocol_sha256": hashlib.sha256(protocol.encode("utf-8")).hexdigest(),
        "build_mode": build_state.get("mode"),
        "recursive_each_go": True,
        "terminal_done_state_after_v1": False,
        "harness_contract": str(HARNESS_CONTRACT.relative_to(ROOT)),
    }


def main() -> int:
    try:
        info = preflight()
    except Exception as exc:
        print(f"XENO_ACTIVE_GO_ADMISSION_FAIL:{exc}", file=sys.stderr)
        return 5
    print(json.dumps({"schema": "XENO_ACTIVE_GO_PREFLIGHT/v3", "status": "PASS", **info}, sort_keys=True))
    os.execv(sys.executable, [sys.executable, str(CONTROLLER), *sys.argv[1:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
