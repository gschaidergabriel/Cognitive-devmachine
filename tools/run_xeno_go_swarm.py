#!/usr/bin/env python3
"""Canonical Xeno implementation-codename GO entrypoint for EntityOS/HCU.

This launcher resolves the current supervisor dynamically, validates the current
EntityOS/HCU authority plus Xeno's active-build/recursive-improvement contracts,
and then transfers execution to the implementation-focused 6000-logical-worker
fabric. It never reads provider secrets during preflight and does not create a
competing product or truth authority.
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
FREE_PROVIDER_ADMISSION = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
WORKER_PROTOCOL = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
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
COMPAT_PROTOCOL_BEGIN = "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
CURRENT_PROTOCOL_MARKER = "[ENTITYOS/HCU CURRENT AUTHORITY]"
FREE_LANE_RECEIPT = "FREE_LANE_EXECUTION_RECEIPT/v1"


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
    provider_admission = load_json(FREE_PROVIDER_ADMISSION)
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
    free_only = authority.get("free_only") or {}
    require(free_only.get("enabled") is True, "AUTHORITY_FREE_ONLY_MISSING")
    require(free_only.get("no_paid_fallback") is True, "AUTHORITY_NO_PAID_FALLBACK_MISSING")
    require(free_only.get("together_forbidden") is True, "AUTHORITY_TOGETHER_FENCE_MISSING")

    # Provider-level admission is not enough under current FREE_ONLY authority.
    # Preflight remains secret-blind and verifies only that the canonical typed
    # admission is in the same authority epoch and names the concrete v3 receipt
    # boundary that will later bind each credential+route before network I/O.
    require(provider_admission.get("schema") == "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1", "FREE_PROVIDER_ADMISSION_SCHEMA_MISMATCH")
    require(provider_admission.get("mode") == "FREE_ONLY", "FREE_PROVIDER_ADMISSION_MODE_MISMATCH")
    require(str(provider_admission.get("authority_epoch")) == str(authority.get("schema_version")), "FREE_PROVIDER_ADMISSION_EPOCH_MISMATCH")
    require(provider_admission.get("product") == PRODUCT, "FREE_PROVIDER_ADMISSION_PRODUCT_MISMATCH")
    require(provider_admission.get("compute_architecture") == COMPUTE_ARCH, "FREE_PROVIDER_ADMISSION_HCU_MISMATCH")
    route_gate = provider_admission.get("route_level_gate") or {}
    require(route_gate.get("receipt_schema") == FREE_LANE_RECEIPT, "FREE_LANE_RECEIPT_GATE_MISSING")
    require(route_gate.get("implementation") == "tools/free_lane_provenance.py", "FREE_LANE_PROVENANCE_IMPLEMENTATION_MISMATCH")
    require(route_gate.get("unknown_or_unbound_route") == "FAIL_CLOSED", "FREE_LANE_UNKNOWN_ROUTE_NOT_FAIL_CLOSED")
    require(route_gate.get("paid_fallback_attempt_count") == 0, "FREE_LANE_PAID_FALLBACK_NOT_ZERO")

    require(BUILD_DIRECTIVE.exists(), "XENO_BUILD_DIRECTIVE_MISSING")
    require(HARNESS_CONTRACT.exists(), "XENO_HARNESS_CONTRACT_MISSING")
    require(build_state.get("mode") == "ACTIVE_BUILD_THEN_INFINITE_RECURSIVE_IMPROVEMENT", "XENO_BUILD_MODE_MISMATCH")
    require(build_state.get("implementation_codename") == "Xeno", "XENO_CODENAME_MISMATCH")
    require(build_state.get("target_core_class") == "APPROX_0_8B_FINE_TUNED", "XENO_08B_TARGET_MISSING")
    require(build_state.get("recursive_on_every_go_until_superseded") is True, "XENO_PER_GO_RECURSION_NOT_ARMED")
    require(build_state.get("terminal_done_state_after_v1") is False, "XENO_TERMINAL_DONE_STATE_FORBIDDEN")
    harness = build_state.get("harness_requirements") or {}
    require(harness.get("internal_08b_switchable") is True, "XENO_INTERNAL_08B_SWITCH_MISSING")
    require(harness.get("external_llm_slots_max") == 2, "XENO_TWO_SLOT_LIMIT_MISSING")
    require(harness.get("prestage_switchable") is True, "XENO_PRESTAGE_SWITCH_MISSING")
    require(harness.get("grid10_logical_cells") == 10, "XENO_GRID10_REQUIREMENT_MISSING")
    require(harness.get("xeno_peer_link_required") == "XENO_PEER_LINK/v1", "XENO_PEER_LINK_REQUIREMENT_MISSING")

    for path, code in (
        (WORKER_PROTOCOL, "WORKER_PROTOCOL_MISSING"),
        (CONTROLLER, "XENO_CONTROLLER_MISSING"),
        (PROMOTION_GATE, "XENO_PROMOTION_GATE_MISSING"),
        (HARNESS_VALIDATOR, "XENO_HARNESS_VALIDATOR_MISSING"),
        (ECONOMIC_GATE, "FREE_LANE_ECONOMIC_GATE_MISSING"),
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
        "free_lane_receipt": FREE_LANE_RECEIPT,
        "provider_admission_epoch": provider_admission.get("authority_epoch"),
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
    print(json.dumps({"schema": "XENO_ACTIVE_GO_PREFLIGHT/v2", "status": "PASS", **info}, sort_keys=True))
    os.execv(sys.executable, [sys.executable, str(CONTROLLER), *sys.argv[1:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
