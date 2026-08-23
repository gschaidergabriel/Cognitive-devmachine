#!/usr/bin/env python3
"""Fail-closed compatibility admission shim for current EntityOS/HCU GO/ZERO orchestration.

The historical filename is retained for invocation/path compatibility only. This shim
performs source/control-plane checks, never inspects provider secrets, and refuses to
execute when current EntityOS/HCU authority or the mandatory dual-track worker protocol
is missing. Xeno/XCU are not admitted as competing current identities.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
AUTHORITY = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"
WORKER_PROTOCOL = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
CONTROLLER = ROOT / "tools/run_go_zero_swarm.py"

PROGRAM = "ENTITYOS_HCU"
STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
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


def preflight() -> None:
    bootstrap = load_json(BOOTSTRAP)
    state = load_json(PROGRAM_STATE)
    authority = load_json(AUTHORITY)

    require(bootstrap.get("active_program") == PROGRAM, "BOOTSTRAP_PROGRAM_MISMATCH")
    require(bootstrap.get("active_stage") == STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(bootstrap.get("product_endpoint") == PRODUCT, "BOOTSTRAP_PRODUCT_MISMATCH")
    require(
        bootstrap.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH,
        "BOOTSTRAP_HCU_ARCH_MISMATCH",
    )
    require(bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_NOT_FORBIDDEN")
    require(
        bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_SANDBOX_ONLY",
        "BOOTSTRAP_SANDBOX_ONLY_MISSING",
    )

    tracks = bootstrap.get("go_required_tracks") or []
    require("ENTITYOS_EXECUTABLE_CONVERGENCE" in tracks, "BOOTSTRAP_TRACK_A_MISSING")
    require(
        "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT_OR_HCU_NO_CHANGE_WITH_REASON" in tracks,
        "BOOTSTRAP_TRACK_B_MISSING",
    )

    require(state.get("program_id") == PROGRAM_ID, "PROGRAM_STATE_ID_MISMATCH")
    require(state.get("stage") == STAGE, "PROGRAM_STATE_STAGE_MISMATCH")
    require(state.get("product") == PRODUCT, "PROGRAM_STATE_PRODUCT_MISMATCH")
    require(
        state.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH,
        "PROGRAM_STATE_HCU_ARCH_MISMATCH",
    )
    state_tracks = state.get("go_required_tracks") or {}
    require(state_tracks.get("track_a") == "ENTITYOS_EXECUTABLE_CONVERGENCE", "PROGRAM_TRACK_A_MISSING")
    require(
        state_tracks.get("track_b") == "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT",
        "PROGRAM_TRACK_B_MISSING",
    )

    require(authority.get("program") == PROGRAM, "AUTHORITY_PROGRAM_MISMATCH")
    require(authority.get("product") == PRODUCT, "AUTHORITY_PRODUCT_MISMATCH")
    require(
        authority.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH,
        "AUTHORITY_HCU_ARCH_MISMATCH",
    )

    require(WORKER_PROTOCOL.exists(), "WORKER_PROTOCOL_MISSING")
    require(CONTROLLER.exists(), "COORDINATED_CONTROLLER_MISSING")

    worker_text = WORKER_PROTOCOL.read_text(encoding="utf-8")
    # The outer legacy marker is loader ABI only; current authority must also be literal.
    require(COMPAT_PROTOCOL_BEGIN in worker_text, "COMPAT_PROTOCOL_ABI_MARKER_MISSING")
    require(CURRENT_PROTOCOL_MARKER in worker_text, "ENTITYOS_HCU_PROTOCOL_MARKER_MISSING")
    require("Sole current product/system: EntityOS." in worker_text, "ENTITYOS_PROTOCOL_AUTHORITY_MISSING")
    require("Sole current integrated cognition/compute architecture: HCU." in worker_text, "HCU_PROTOCOL_AUTHORITY_MISSING")
    require("ENTITYOS_EXECUTABLE_CONVERGENCE" in worker_text, "WORKER_TRACK_A_MISSING")
    require("HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT" in worker_text, "WORKER_TRACK_B_MISSING")
    require("HCU_NO_CHANGE_WITH_REASON" in worker_text, "WORKER_HCU_NO_CHANGE_MISSING")

    # The retained controller may still contain historical Mini Entity lane labels, but the
    # mandatory injected protocol must explicitly demote those labels to compatibility/provenance.
    controller_text = CONTROLLER.read_text(encoding="utf-8")
    require("protocol = BASE.load_protocol()" in controller_text, "CONTROLLER_PROTOCOL_INJECTION_MISSING")
    require("prompt.startswith(BASE.PROTOCOL_BEGIN)" in controller_text, "CONTROLLER_PROTOCOL_CONFORMANCE_MISSING")
    require("CLAY_FREE_ONLY_ATTESTED" in controller_text, "CONTROLLER_FREE_ONLY_GATE_MISSING")
    require("HTTP_402_HARD_STOP" in controller_text, "CONTROLLER_PAYMENT_HARD_STOP_MISSING")

    attested = (os.getenv("CLAY_FREE_ONLY_ATTESTED") or "").strip().lower()
    require(attested in {"1", "true", "yes", "on", "attested"}, "CLAY_FREE_ONLY_ATTESTED_REQUIRED")


def main() -> int:
    try:
        preflight()
    except Exception as exc:
        print(f"ENTITYOS_HCU_GO_SWARM_ADMISSION_FAIL:{exc}", file=sys.stderr)
        return 5

    os.execv(sys.executable, [sys.executable, str(CONTROLLER), *sys.argv[1:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
