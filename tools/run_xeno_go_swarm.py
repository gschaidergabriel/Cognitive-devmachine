#!/usr/bin/env python3
"""Fail-closed EntityOS/HCU admission shim over the retained GO/ZERO swarm.

The filename is retained as a transitional Xeno compatibility surface. It is not a
second product or controller authority. This shim admits only the current EntityOS/HCU
control state, then reuses the single retained coordinated FREE_ONLY swarm controller
with an in-process current protocol/lane overlay.

No provider secrets are inspected here. No runtime/product credit is created by source
admission alone.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
SUPERVISOR = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"
SUPERVISOR_INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
AUTHORITY_REBASE = ROOT / "research_entity/claycode/autonomous/GO_20260823_1744_ENTITYOS_HCU_AUTHORITY_REBASE.json"
WORKER_PROTOCOL = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
CONTROLLER = ROOT / "tools/run_go_zero_swarm.py"

PROGRAM = "ENTITYOS_HCU"
PROGRAM_ID = "entityos-hcu"
PRODUCT = "EntityOS"
ARCHITECTURE = "HCU"
TRANSITIONAL_STAGE = "XENO_COMPUTATIONAL_UNIT_BOOTSTRAP"
PROTOCOL_BEGIN = "[ENTITYOS_HCU :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
PROTOCOL_END = "[/ENTITYOS_HCU :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"

ENTITYOS_HCU_LANES: tuple[tuple[str, str], ...] = (
    ("ARCH::PRODUCT_BOUNDARY", "Re-evaluate the sole current EntityOS product boundary and find one highest-information convergence delta without creating a second system."),
    ("ARCH::HCU_ENTRY", "Advance or falsify the EntityOS/HCU typed Entry Fabric and bind new data to causal identity, generation, provenance, permissions and budget before cognition."),
    ("ARCH::HCU_COMPUTE", "Stress the HCU shared-weight logical-cell architecture, deterministic control, interconnect and state tiers for one reusable computerization delta."),
    ("TRUTH::EPISTEMIC", "Attack UNKNOWN/ZERO/ERROR/MEASURED and REPORTED/MEASURED separation with concrete counterexamples; HCU/model output never mints truth."),
    ("TRUTH::AUTHORITY", "Attack model/HCU/world-model output versus canonical truth/effect authority and propose deterministic falsifiers."),
    ("DB::ATOMICITY", "Stress the current canonical UnifiedDB/MiniUnifiedDB compatibility substrate for atomicity, CAS, generations and crash ambiguity with one concrete failure schedule."),
    ("DB::EXACTLY_ONCE", "Stress exactly-once/effect receipts/replay ambiguity and find a duplicate-effect counterexample if one exists."),
    ("DB::RECOVERY", "Analyze EntityOS restart/recovery/provenance continuity and preserve UNKNOWN where receipts are missing."),
    ("HCU::ROUTER", "Attack HCU reactive routing, positive local engine admission, causal event identity and downstream inference echo; prefer one discriminating falsifier."),
    ("HCU::GRID10", "Advance the 10-logical-cell shared-worker baseline as a compute-matched reference without conflating logical cells with physical decode concurrency."),
    ("HCU::COGSIM", "Advance request-scoped cognition simulation as noncanonical candidate computation with no direct effect authority."),
    ("HCU::WORLD_MODEL", "Test bounded world-model prediction/calibration and identify where selective invocation should beat forced simulation."),
    ("HCU::NESTED_SIM", "Challenge the optional world-model -> virtual computer -> simulated AI -> candidate-action path for compounded error and define a cheapest discriminator."),
    ("HCU::SCALEOUT", "Advance measured logical-context scaleout planning while keeping resident model count, KV contexts and physical decode concurrency separate."),
    ("JSPACE::IDENTITY", "Stress exact checkpoint/tokenizer/runtime/J-Space identity and stale-profile rejection; closed-model text output is not hidden-state access."),
    ("JSPACE::CAUSALITY", "Design a causal intervention distinguishing useful Global J-Space coupling from mere context display/injection."),
    ("GWT::WORKSPACE", "Stress bounded workspace competition/broadcast/occupancy semantics without equating stability or majority with truth."),
    ("HYPERPOSITION::REDUCTION", "Find premature-collapse failure modes in Hyperposition and propose calibrated evidence-bound reduction tests."),
    ("INFER::LOCAL_ENGINE", "Stress positive bound local/internal HCU engine identity, model/runtime identity, timeout/error classification and zero external secret/network access."),
    ("INFER::CLAUDE_ADAPTER", "Review the targeted Claude Code candidate-inference boundary without granting identity/truth/effect authority; preserve compiled-external J-Space semantics."),
    ("SEC::SECRETS", "Attack secret/token isolation, logs, prompts, exports and telemetry for leak paths before any provider network access."),
    ("SEC::STALE_GENERATION", "Attack stale-generation rejection and concurrent commit/effect races across EntityOS/HCU boundaries."),
    ("SEC::PROMPT_BOUNDARY", "Attack runtime-editable prompt/configuration versus immutable authority/truth/effect gates."),
    ("EFFECT::GATE", "Stress candidate-to-effect translation, EffectGate/EffectJournal non-bypass and unknown-after-crash behavior."),
    ("TEST::MUTATION", "Generate one high-information mutation/property test for the current EntityOS/HCU frontier."),
    ("TEST::DIFFERENTIAL", "Generate one high-information differential test across independent implementations/backends without granting donor code current authority."),
    ("TEST::FAILURE_PATH", "Generate one concrete failure-path schedule that could falsify a current green EntityOS/HCU claim."),
    ("REVIEW::OVERCLAIM", "Search current evidence for source-only, stale-head, fixture-only or zero-step overclaims; runtime credit requires exact execution."),
    ("REVIEW::ANCESTRY", "Check whether supposedly independent evidence shares implementation/model/test ancestry and preserve Goodman-ancestry collapse."),
    ("FUSION::CONFLICTS", "Fuse recent EntityOS/HCU results while preserving unresolved contradictions instead of averaging them away."),
    ("FUSION::NEXT_GATE", "Select the next cheapest executable EntityOS/HCU discriminator from current evidence."),
)


class AdmissionError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AdmissionError(f"NOT_OBJECT:{path}")
    return value


def require(ok: bool, code: str) -> None:
    if not ok:
        raise AdmissionError(code)


def preflight() -> None:
    bootstrap = load_json(BOOTSTRAP)
    state = load_json(PROGRAM_STATE)
    supervisor = load_json(SUPERVISOR)
    inbox = load_json(SUPERVISOR_INBOX)
    rebase = load_json(AUTHORITY_REBASE)

    require(bootstrap.get("active_program") == PROGRAM, "BOOTSTRAP_PROGRAM_MISMATCH")
    require(bootstrap.get("active_stage") == TRANSITIONAL_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(bootstrap.get("active_stage_semantics") == "TRANSITIONAL_IMPLEMENTATION_STAGE_LABEL_ONLY", "BOOTSTRAP_STAGE_AUTHORITY_AMBIGUOUS")
    require(bootstrap.get("product_endpoint") == PRODUCT, "BOOTSTRAP_PRODUCT_MISMATCH")
    require(bootstrap.get("integrated_cognition_architecture") == ARCHITECTURE, "BOOTSTRAP_HCU_MISSING")
    require(bootstrap.get("entry_fabric") == "MANDATORY_HCU_CO_DEVELOPMENT", "BOOTSTRAP_ENTRY_CO_DEVELOPMENT_MISSING")
    require(bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_NOT_FORBIDDEN")
    require(bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_SANDBOX_ONLY", "BOOTSTRAP_SANDBOX_ONLY_MISSING")

    require(state.get("program_id") == PROGRAM_ID, "PROGRAM_STATE_ID_MISMATCH")
    require(state.get("product_endpoint") == PRODUCT, "PROGRAM_STATE_PRODUCT_MISMATCH")
    require(state.get("integrated_cognition_architecture") == ARCHITECTURE, "PROGRAM_STATE_HCU_MISMATCH")
    tracks = state.get("go_required_tracks") or {}
    require(tracks.get("track_a") == "ENTITYOS_EXECUTABLE_CONVERGENCE", "PROGRAM_TRACK_A_MISSING")
    require(tracks.get("track_b") == "HCU_AND_ENTRY_FABRIC_CO_DEVELOPMENT", "PROGRAM_TRACK_B_MISSING")

    require(supervisor.get("program") == PROGRAM, "SUPERVISOR_PROGRAM_MISMATCH")
    require(supervisor.get("product") == PRODUCT, "SUPERVISOR_PRODUCT_MISMATCH")
    require(supervisor.get("integrated_cognition_compute_architecture") == ARCHITECTURE, "SUPERVISOR_HCU_MISMATCH")
    adjudication = supervisor.get("adjudication") or {}
    require(adjudication.get("entityos") == "SOLE_CURRENT_PRODUCT_SYSTEM_IDENTITY", "SUPERVISOR_ENTITYOS_NOT_SOLE")
    require(adjudication.get("hcu") == "SOLE_CURRENT_INTEGRATED_COGNITION_COMPUTE_ARCHITECTURE", "SUPERVISOR_HCU_NOT_SOLE")

    require(inbox.get("active_program") == PROGRAM, "SUPERVISOR_INBOX_PROGRAM_MISMATCH")
    require(inbox.get("product") == PRODUCT, "SUPERVISOR_INBOX_PRODUCT_MISMATCH")
    require(inbox.get("integrated_cognition_compute_architecture") == ARCHITECTURE, "SUPERVISOR_INBOX_HCU_MISMATCH")
    require(rebase.get("current_program") == "ENTITYOS_HCU_ONLY", "AUTHORITY_REBASE_PROGRAM_MISMATCH")

    require(WORKER_PROTOCOL.exists(), "WORKER_PROTOCOL_MISSING")
    require(CONTROLLER.exists(), "COORDINATED_CONTROLLER_MISSING")
    worker_text = WORKER_PROTOCOL.read_text(encoding="utf-8")
    require(PROTOCOL_BEGIN in worker_text and PROTOCOL_END in worker_text, "ENTITYOS_HCU_WORKER_PROTOCOL_MARKER_MISSING")
    require("ENTITYOS_EXECUTABLE_CONVERGENCE" in worker_text, "WORKER_TRACK_A_MISSING")
    require("HCU_AND_ENTRY_FABRIC_CO_DEVELOPMENT" in worker_text, "WORKER_TRACK_B_MISSING")
    require("EntityOS is the sole current product/runtime system identity" in worker_text, "WORKER_ENTITYOS_AUTHORITY_MISSING")
    require("HCU is the sole current integrated cognition/compute architecture" in worker_text, "WORKER_HCU_AUTHORITY_MISSING")

    attested = (os.getenv("CLAY_FREE_ONLY_ATTESTED") or "").strip().lower()
    require(attested in {"1", "true", "yes", "on", "attested"}, "CLAY_FREE_ONLY_ATTESTED_REQUIRED")


def load_controller():
    spec = importlib.util.spec_from_file_location("clay_entityos_hcu_go_zero_swarm", CONTROLLER)
    if spec is None or spec.loader is None:
        raise AdmissionError(f"CANNOT_LOAD_CONTROLLER:{CONTROLLER}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def install_current_overlay(controller) -> None:
    # The retained base controller is implementation plumbing. Current authority and
    # current child task semantics are supplied here without creating a second ledger,
    # provider runtime, lease coordinator, effect path or output sink.
    controller.BASE.PROTOCOL_BEGIN = PROTOCOL_BEGIN
    controller.BASE.PROTOCOL_END = PROTOCOL_END
    controller.BASE.OWNER_DIRECTIVE_PATH = SUPERVISOR
    controller.LANES = ENTITYOS_HCU_LANES


def main(argv: list[str] | None = None) -> int:
    try:
        preflight()
        controller = load_controller()
        install_current_overlay(controller)
        args = controller.parse_args(sys.argv[1:] if argv is None else argv)
        return asyncio.run(controller.run(args))
    except AdmissionError as exc:
        print(f"ENTITYOS_HCU_GO_SWARM_ADMISSION_FAIL:{exc}", file=sys.stderr)
        return 5
    except RuntimeError as exc:
        print(f"ENTITYOS_HCU_GO_SWARM_RUNTIME_FAIL:{exc}", file=sys.stderr)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
