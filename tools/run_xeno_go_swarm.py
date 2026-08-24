#!/usr/bin/env python3
"""Successor-dynamic compatibility entrypoint for current EntityOS/HCU GO/ZERO.

The historical Xeno filename is retained as loader/invocation compatibility only.
Current product, authority and execution semantics are resolved from canonical
EntityOS/HCU control-plane files at invocation time. Xeno is never promoted into
another product or persistent entity.

This shim performs no provider secret lookup and no provider network I/O. It
fails closed unless the current supervisor, FREE_ONLY provider admission and the
route-level economic gate agree, then delegates to ``run_go_zero_swarm_v2.py``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
SUPERVISOR_INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
FREE_PROVIDER_ADMISSION = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
WORKER_PROTOCOL = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
ROUTE_PROVENANCE = ROOT / "tools/free_lane_provenance.py"
CONTROLLER = ROOT / "tools/run_go_zero_swarm_v2.py"

PROGRAM = "ENTITYOS_HCU"
STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
PROGRAM_ID = "entityos-hcu"
PRODUCT = "EntityOS"
COMPUTE_ARCH = "HCU"
CURRENT_PROTOCOL_MARKER = "[ENTITYOS/HCU CURRENT AUTHORITY]"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"NOT_OBJECT:{path}")
    return value


def require(ok: bool, code: str) -> None:
    if not ok:
        raise RuntimeError(code)


def forbidden(value: Any) -> bool:
    return "FORBIDDEN" in str(value or "").upper()


def steering_path(inbox: dict[str, Any]) -> Path:
    rel = str(inbox.get("steering") or "").strip()
    require(rel.startswith("research_entity/claycode/autonomous/SUPERVISOR_STEERING_"),
            "SUPERVISOR_STEERING_POINTER_INVALID")
    require(rel.endswith(".json"), "SUPERVISOR_STEERING_POINTER_INVALID")
    path = (ROOT / rel).resolve()
    allowed_root = (ROOT / "research_entity/claycode/autonomous").resolve()
    require(path.parent == allowed_root, "SUPERVISOR_STEERING_POINTER_ESCAPES_AUTHORITY_ROOT")
    require(path.exists(), "CURRENT_SUPERVISOR_STEERING_MISSING")
    return path


def preflight() -> None:
    bootstrap = load_json(BOOTSTRAP)
    state = load_json(PROGRAM_STATE)
    inbox = load_json(SUPERVISOR_INBOX)
    steering = load_json(steering_path(inbox))
    admission = load_json(FREE_PROVIDER_ADMISSION)

    # Stable identity/product law. BOOTSTRAP_MINIMAL and PROGRAM_STATE are caches/
    # ledgers and may temporarily lag the newest admitted supervisor epoch, but
    # they must never disagree on product/stage/architecture.
    require(bootstrap.get("active_program") == PROGRAM, "BOOTSTRAP_PROGRAM_MISMATCH")
    require(bootstrap.get("active_stage") == STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(bootstrap.get("product_endpoint") == PRODUCT, "BOOTSTRAP_PRODUCT_MISMATCH")
    require(bootstrap.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH,
            "BOOTSTRAP_HCU_ARCH_MISMATCH")
    require(bool(bootstrap.get("free_only")), "BOOTSTRAP_FREE_ONLY_MISSING")
    require(forbidden(bootstrap.get("together_api")), "BOOTSTRAP_TOGETHER_NOT_FORBIDDEN")
    require(forbidden(bootstrap.get("paid_fallback")), "BOOTSTRAP_PAID_FALLBACK_NOT_FORBIDDEN")

    tracks = set(bootstrap.get("go_required_tracks") or [])
    require("ENTITYOS_EXECUTABLE_CONVERGENCE" in tracks, "BOOTSTRAP_TRACK_A_MISSING")
    require("HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT_OR_HCU_NO_CHANGE_WITH_REASON" in tracks,
            "BOOTSTRAP_TRACK_B_MISSING")
    require("GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS_OR_NO_CHANGE_WITH_REASON" in tracks,
            "BOOTSTRAP_TRACK_C_MISSING")

    require(state.get("program_id") == PROGRAM_ID, "PROGRAM_STATE_ID_MISMATCH")
    require(state.get("stage") == STAGE, "PROGRAM_STATE_STAGE_MISMATCH")
    require(state.get("product") == PRODUCT, "PROGRAM_STATE_PRODUCT_MISMATCH")
    require(state.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH,
            "PROGRAM_STATE_HCU_ARCH_MISMATCH")
    state_tracks = state.get("go_required_tracks") or {}
    require(state_tracks.get("track_a") == "ENTITYOS_EXECUTABLE_CONVERGENCE", "PROGRAM_TRACK_A_MISSING")
    require(state_tracks.get("track_b") == "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT", "PROGRAM_TRACK_B_MISSING")
    require(state_tracks.get("track_c") == "GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS",
            "PROGRAM_TRACK_C_MISSING")

    # Newest admitted supervisor is resolved dynamically from SUPERVISOR_INBOX,
    # avoiding the stale-island failure caused by a hard-coded 8.xx filename.
    current_epoch = str(inbox.get("schema_version") or "")
    require(current_epoch != "", "SUPERVISOR_INBOX_EPOCH_MISSING")
    require(str(steering.get("schema_version") or "") == current_epoch,
            "SUPERVISOR_STEERING_EPOCH_MISMATCH")
    require(steering.get("active_program") == PROGRAM, "AUTHORITY_PROGRAM_MISMATCH")
    require(steering.get("product") == PRODUCT, "AUTHORITY_PRODUCT_MISMATCH")
    require(steering.get("integrated_cognition_compute_architecture") == COMPUTE_ARCH,
            "AUTHORITY_HCU_ARCH_MISMATCH")
    free_only = steering.get("free_only") or {}
    require(bool(free_only.get("enabled")), "AUTHORITY_FREE_ONLY_DISABLED")
    require(bool(free_only.get("no_paid_fallback")), "AUTHORITY_PAID_FALLBACK_ALLOWED")
    require(bool(free_only.get("together_forbidden")), "AUTHORITY_TOGETHER_NOT_FORBIDDEN")
    require(bool(free_only.get("provider_level_admission_is_not_runtime_cost_proof")),
            "AUTHORITY_ROUTE_LEVEL_COST_PROVENANCE_MISSING")
    require(str(free_only.get("unknown_or_unlisted_route")) == "FAIL_CLOSED",
            "AUTHORITY_UNKNOWN_ROUTE_NOT_FAIL_CLOSED")

    # Provider-level typed admission and per-lane economic admission must be at
    # the same current epoch before this trigger path is executable.
    require(str(admission.get("authority_epoch") or "") == current_epoch,
            "FREE_PROVIDER_ADMISSION_EPOCH_MISMATCH")
    require(admission.get("mode") == "FREE_ONLY", "FREE_PROVIDER_ADMISSION_MODE_MISMATCH")
    require(admission.get("product") == PRODUCT, "FREE_PROVIDER_ADMISSION_PRODUCT_MISMATCH")
    require(admission.get("compute_architecture") == COMPUTE_ARCH,
            "FREE_PROVIDER_ADMISSION_ARCH_MISMATCH")
    route_gate = admission.get("route_level_gate") or {}
    require(route_gate.get("implementation") == "tools/free_lane_provenance.py",
            "FREE_LANE_PROVENANCE_IMPLEMENTATION_MISMATCH")
    require(route_gate.get("receipt_schema") == "FREE_LANE_EXECUTION_RECEIPT/v1",
            "FREE_LANE_RECEIPT_SCHEMA_MISMATCH")
    require(route_gate.get("unknown_or_unbound_route") == "FAIL_CLOSED",
            "FREE_LANE_UNKNOWN_ROUTE_NOT_FAIL_CLOSED")
    require(int(route_gate.get("paid_fallback_attempt_count", -1)) == 0,
            "FREE_LANE_PAID_FALLBACK_NONZERO")

    require(WORKER_PROTOCOL.exists(), "WORKER_PROTOCOL_MISSING")
    require(ROUTE_PROVENANCE.exists(), "FREE_LANE_PROVENANCE_MISSING")
    require(CONTROLLER.exists(), "ROUTE_BOUND_TRIGGER_CONTROLLER_MISSING")

    worker_text = WORKER_PROTOCOL.read_text(encoding="utf-8")
    require(CURRENT_PROTOCOL_MARKER in worker_text, "ENTITYOS_HCU_PROTOCOL_MARKER_MISSING")
    require("Sole current product/system: EntityOS." in worker_text, "ENTITYOS_PROTOCOL_AUTHORITY_MISSING")
    require("Sole current integrated cognition/compute architecture: HCU." in worker_text,
            "HCU_PROTOCOL_AUTHORITY_MISSING")

    provenance_text = ROUTE_PROVENANCE.read_text(encoding="utf-8")
    controller_text = CONTROLLER.read_text(encoding="utf-8")
    require("def lane_evidence(" in provenance_text, "FREE_LANE_EVIDENCE_FUNCTION_MISSING")
    require("FREE_LANE_EXECUTION_RECEIPT/v1" in provenance_text, "FREE_LANE_RECEIPT_IMPLEMENTATION_MISSING")
    require("lane_evidence" in controller_text, "TRIGGER_CONTROLLER_ROUTE_GATE_MISSING")
    require("emit_execution_receipt" in controller_text, "TRIGGER_CONTROLLER_RECEIPT_MISSING")
    require("gated_next_key_model" in controller_text, "TRIGGER_CONTROLLER_RESERVATION_GATE_MISSING")
    require("gated_request_chat" in controller_text, "TRIGGER_CONTROLLER_NETWORK_GATE_MISSING")

    # Compatibility attestation remains an additional caller assertion only; it
    # cannot replace canonical typed admission or route-level economic evidence.
    attested = (os.getenv("CLAY_FREE_ONLY_ATTESTED") or "").strip().lower()
    require(attested in {"1", "true", "yes", "on", "attested"},
            "CLAY_FREE_ONLY_ATTESTED_REQUIRED")


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
