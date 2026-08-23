#!/usr/bin/env python3
"""Fail-closed admission shim for the current Xeno GO/ZERO controller.

This shim performs source/control-plane checks only. It does not inspect provider
secrets and will not execute a stale Mini Entity/ClayVerse controller. A child
controller is admitted only when current Xeno authority, dual-track markers and the
current-facing Xeno artefact anchor agree.
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
XENO_ROOT = ROOT / "the artefact/Xeno"
XENO_MANIFEST = XENO_ROOT / "manifest.json"
XENO_ARCHITECTURE = XENO_ROOT / "ARCHITECTURE.md"
XENO_README = XENO_ROOT / "README.md"
XENO_ENTRY = XENO_ROOT / "entry_fabric_v1.py"
XENO_ENTRY_TEST = XENO_ROOT / "test_entry_fabric_v1.py"

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
REQUIRED_ARCHITECTURE_MARKERS = (
    "XENO ENTRY FABRIC",
    "XRAM STATE FABRIC",
    "XPU CONTROL",
    "XCU ACCELERATOR",
    "EffectGate/EffectJournal",
    "logical_module_count != resident_model_count != physical_decode_concurrency",
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
    require(state.get("product_endpoint") == "EntityOS", "PROGRAM_STATE_ENDPOINT_MISMATCH")
    require(state.get("identity", {}).get("active_bootstrap_name") == "Xeno", "PROGRAM_STATE_XENO_IDENTITY_MISSING")
    tracks = state.get("go_required_tracks") or {}
    require(tracks.get("track_a") == "XENO_EXECUTABLE_CONVERGENCE", "PROGRAM_TRACK_A_MISSING")
    require(tracks.get("track_b") == "XCU_AND_ENTRY_FABRIC_CO_DEVELOPMENT", "PROGRAM_TRACK_B_MISSING")

    for path, code in (
        (OWNER, "XENO_OWNER_DIRECTIVE_MISSING"),
        (WORKER_PROTOCOL, "WORKER_PROTOCOL_MISSING"),
        (RESEARCH_FUSION, "XENO_RESEARCH_FUSION_MISSING"),
        (CONTROLLER, "COORDINATED_CONTROLLER_MISSING"),
        (XENO_MANIFEST, "XENO_MANIFEST_MISSING"),
        (XENO_ARCHITECTURE, "XENO_ARCHITECTURE_MISSING"),
        (XENO_README, "XENO_README_MISSING"),
        (XENO_ENTRY, "XENO_ENTRY_FABRIC_MISSING"),
        (XENO_ENTRY_TEST, "XENO_ENTRY_FABRIC_TEST_MISSING"),
    ):
        require(path.exists(), code)

    xeno_manifest = load_json(XENO_MANIFEST)
    require(xeno_manifest.get("schema_version") == "XENO_CURRENT_MANIFEST/v1", "XENO_MANIFEST_SCHEMA_MISMATCH")
    require(xeno_manifest.get("artifact") == "Xeno", "XENO_MANIFEST_ARTIFACT_MISMATCH")
    require(xeno_manifest.get("active_program") == PROGRAM, "XENO_MANIFEST_PROGRAM_MISMATCH")
    require(xeno_manifest.get("active_stage") == STAGE, "XENO_MANIFEST_STAGE_MISMATCH")
    require(xeno_manifest.get("product_endpoint") == "EntityOS", "XENO_MANIFEST_ENDPOINT_MISMATCH")
    require(xeno_manifest.get("owner_directive") == OWNER_REL, "XENO_MANIFEST_OWNER_MISMATCH")
    require(xeno_manifest.get("execution_policy") == "AUTHORIZED_ISOLATED_SANDBOX_ONLY", "XENO_MANIFEST_EXECUTION_BOUNDARY_WEAKENED")
    require(xeno_manifest.get("together_api") == "FORBIDDEN", "XENO_MANIFEST_TOGETHER_NOT_FORBIDDEN")
    require(xeno_manifest.get("runtime_credit") == 0, "XENO_MANIFEST_RUNTIME_CREDIT_NONZERO")
    manifest_tracks = xeno_manifest.get("go_required_tracks") or {}
    require(manifest_tracks.get("track_a") == "XENO_EXECUTABLE_CONVERGENCE", "XENO_MANIFEST_TRACK_A_MISSING")
    require(manifest_tracks.get("track_b") == "XCU_AND_ENTRY_FABRIC_CO_DEVELOPMENT", "XENO_MANIFEST_TRACK_B_MISSING")
    entry = xeno_manifest.get("entry_fabric") or {}
    require(entry.get("schema") == "XENO_ENTRY_PACKET/v1", "XENO_MANIFEST_ENTRY_SCHEMA_MISMATCH")
    require(entry.get("effect_authority") is False, "XENO_ENTRY_EFFECT_AUTHORITY_LEAK")
    require(entry.get("truth_authority") is False, "XENO_ENTRY_TRUTH_AUTHORITY_LEAK")

    architecture_text = XENO_ARCHITECTURE.read_text(encoding="utf-8")
    missing_arch = [marker for marker in REQUIRED_ARCHITECTURE_MARKERS if marker not in architecture_text]
    require(not missing_arch, "XENO_ARCHITECTURE_MARKERS_MISSING:" + ",".join(missing_arch))

    readme_text = XENO_README.read_text(encoding="utf-8")
    require("manifest.json" in readme_text and "entry_fabric_v1.py" in readme_text, "XENO_README_CURRENT_ANCHOR_MISSING")
    require("MUST NOT override this current-facing Xeno authority" in readme_text, "XENO_README_LEGACY_OVERRIDE_FENCE_MISSING")

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
