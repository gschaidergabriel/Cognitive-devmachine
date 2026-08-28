#!/usr/bin/env python3
"""Canonical Xeno implementation-codename GO entrypoint for EntityOS/HCU.

Preflight resolves current machine-readable supervisor/provider authority, binds the newest
explicit owner GO target currently mirrored by XENO_ACTIVE_BUILD_STATE, validates the first
shared-state boundary primitive, and transfers execution to the active build fabric.
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
SHARED_STATE_PRIMITIVE = ROOT / "tools/xeno_shared_state_v1.py"
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


def _safe_repo_path(pointer: str, code: str) -> Path:
    path = (ROOT / pointer).resolve()
    root = ROOT.resolve()
    require(path == root or root in path.parents, code + "_ESCAPES_REPO")
    require(path.is_file(), code + "_MISSING")
    return path


def _validate_owner_go_target(build_state: dict) -> dict:
    target = build_state.get("current_owner_go_target") or {}
    require(target.get("mirror_only_not_independent_authority") is True, "XENO_OWNER_TARGET_MIRROR_LAW_MISSING")
    require(target.get("first_model_target") == "Qwen/Qwen3.5-0.8B", "XENO_QWEN35_08B_TARGET_MISSING")
    require(target.get("role_flexible_identical_nodes") is True, "XENO_ROLE_FLEXIBLE_NODE_TARGET_MISSING")
    require(target.get("autonomous_boot_required") is True, "XENO_AUTONOMOUS_BOOT_TARGET_MISSING")
    require(target.get("ordinary_node_s1_access") == "READ_ONLY", "XENO_ORDINARY_S1_READ_ONLY_TARGET_MISSING")
    require(target.get("node_result_schema") == "NODE_RESULT/v1", "XENO_NODE_RESULT_TARGET_MISSING")
    require(target.get("coordinator_lease_schema") == "GRID_COORDINATOR_LEASE/v1", "XENO_COORDINATOR_LEASE_TARGET_MISSING")
    require(target.get("coordinator_only_s1_write") is True, "XENO_COORDINATOR_ONLY_WRITE_TARGET_MISSING")
    require(target.get("s1_write_requires_epoch_digest_cas") is True, "XENO_S1_CAS_TARGET_MISSING")
    require(target.get("first_acceptance_grid") == "PHYSICAL_GRID10", "XENO_PHYSICAL_GRID10_TARGET_MISSING")
    require(target.get("physical_grid10_nodes") == 10, "XENO_PHYSICAL_GRID10_NODE_COUNT_MISSING")
    require(target.get("same_checkpoint_for_first_grid") is True, "XENO_SAME_CHECKPOINT_GRID_TARGET_MISSING")
    require(target.get("logical_grid10_is_acceptance") is False, "XENO_LOGICAL_GRID10_FALSE_ACCEPTANCE")
    require(target.get("current_component_primitive") == "tools/xeno_shared_state_v1.py", "XENO_SHARED_STATE_PRIMITIVE_NOT_BOUND")

    owner_path = _safe_repo_path(str(target.get("authority_source") or ""), "XENO_OWNER_GO_TARGET")
    text = owner_path.read_text(encoding="utf-8")
    for marker, code in (
        ("CURRENT OWNER TARGET / SUPERSEDES PRIOR GO OPTIMIZATION TARGETS WHERE THEY CONFLICT", "XENO_OWNER_TARGET_STATUS_MISSING"),
        ("`AUTONOMOUS_BOOT`", "XENO_OWNER_AUTONOMOUS_BOOT_PRIORITY_MISSING"),
        ("`NODE_RESULT/v1`", "XENO_OWNER_NODE_RESULT_LAW_MISSING"),
        ("`GRID_COORDINATOR_LEASE`", "XENO_OWNER_COORDINATOR_LEASE_LAW_MISSING"),
        ("physical GRID10", "XENO_OWNER_PHYSICAL_GRID10_LAW_MISSING"),
    ):
        require(marker in text, code)
    return {
        "owner_target_path": str(owner_path.relative_to(ROOT)),
        "owner_target_sha256": hashlib.sha256(owner_path.read_bytes()).hexdigest(),
        "optimization_target": target.get("optimization_target"),
        "first_acceptance_grid": target.get("first_acceptance_grid"),
    }


def preflight() -> dict:
    bootstrap = load_json(BOOTSTRAP)
    state = load_json(PROGRAM_STATE)
    build_state = load_json(BUILD_STATE)

    # Bootstrap/Program State remain structural mirrors and may trail a successor supervisor.
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

    authority = live_authority.resolve_current_authority(ROOT)
    protocol = live_authority.build_protocol(ROOT)
    require(protocol.startswith(live_authority.PROTOCOL_BEGIN), "LIVE_PROTOCOL_BEGIN_MISSING")
    require(protocol.endswith(live_authority.PROTOCOL_END), "LIVE_PROTOCOL_END_MISSING")
    require(live_authority.LIVE_MARKER in protocol, "LIVE_PROTOCOL_MARKER_MISSING")

    require(BUILD_DIRECTIVE.exists(), "XENO_BUILD_DIRECTIVE_MISSING")
    require(HARNESS_CONTRACT.exists(), "XENO_HARNESS_CONTRACT_MISSING")
    require(build_state.get("schema") == "XENO_ACTIVE_BUILD_STATE/v2", "XENO_BUILD_STATE_SCHEMA_STALE")
    require(build_state.get("mode") == "ACTIVE_BUILD_THEN_INFINITE_RECURSIVE_IMPROVEMENT", "XENO_BUILD_MODE_MISMATCH")
    require(build_state.get("implementation_codename") == "Xeno", "XENO_CODENAME_MISMATCH")
    require(build_state.get("target_core_class") == "APPROX_0_8B_FINE_TUNED", "XENO_08B_TARGET_MISSING")
    require(build_state.get("preferred_current_exact_base_candidate") == "Qwen/Qwen3.5-0.8B", "XENO_QWEN35_TARGET_MISSING")
    require(build_state.get("recursive_on_every_go_until_superseded") is True, "XENO_PER_GO_RECURSION_NOT_ARMED")
    require(build_state.get("terminal_done_state_after_v1") is False, "XENO_TERMINAL_DONE_STATE_FORBIDDEN")
    require((build_state.get("recursive_promotion") or {}).get("gate_schema") == "XENO_PROMOTION_GATE/v2", "XENO_PROMOTION_V2_NOT_BOUND")
    owner_target = _validate_owner_go_target(build_state)

    for path, code in (
        (CONTROLLER, "XENO_CONTROLLER_MISSING"),
        (PROMOTION_GATE, "XENO_PROMOTION_GATE_MISSING"),
        (HARNESS_VALIDATOR, "XENO_HARNESS_VALIDATOR_MISSING"),
        (SHARED_STATE_PRIMITIVE, "XENO_SHARED_STATE_PRIMITIVE_MISSING"),
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
        "current_phase": build_state.get("current_phase"),
        "recursive_each_go": True,
        "terminal_done_state_after_v1": False,
        "harness_contract": str(HARNESS_CONTRACT.relative_to(ROOT)),
        "legacy_harness_scope": build_state.get("legacy_harness_scope"),
        "shared_state_primitive": str(SHARED_STATE_PRIMITIVE.relative_to(ROOT)),
        **owner_target,
    }


def main() -> int:
    try:
        info = preflight()
    except Exception as exc:
        print(f"XENO_ACTIVE_GO_ADMISSION_FAIL:{exc}", file=sys.stderr)
        return 5
    print(json.dumps({"schema": "XENO_ACTIVE_GO_PREFLIGHT/v4", "status": "PASS", **info}, sort_keys=True))
    os.execv(sys.executable, [sys.executable, str(CONTROLLER), *sys.argv[1:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
