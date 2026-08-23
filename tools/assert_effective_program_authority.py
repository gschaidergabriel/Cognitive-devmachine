#!/usr/bin/env python3
"""Fail closed if effective 4.1+4.2+4.3 control regresses behind owner program authority.

This validates control composition only. PASS grants zero runtime/model/J-Space/GWT/
Claude-adapter/BASE/Frank-v0.1/whole-product credit.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
SUPERVISOR_INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
BASE_CONTROL = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
EXEC_CONTROL = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
PROGRAM_CONTROL = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
STEERING = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_43.json"

EXPECTED_PROGRAM = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
EXPECTED_PROGRAM_ID = "mini-entity-pipeline-all-in-one"
EXPECTED_STAGE = "MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT"
EXPECTED_OWNER_DIRECTIVE = "research_entity/global/ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION.md"
EXPECTED_EFFECTIVE_CONTROL = "4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum"
LEGACY_PROGRAM = "CLAYVERSE_CLAY_MACHINE_ONLY"
LEGACY_STAGE = "CLAY_MACHINE"
LEGACY_ENDPOINT = "SINGLE_FILE_CLAY_COMPUTER"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"EFFECTIVE_PROGRAM_AUTHORITY_FAIL:{path}:NOT_OBJECT")
    return value


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SystemExit(f"EFFECTIVE_PROGRAM_AUTHORITY_FAIL:{code}")


def main() -> int:
    bootstrap = load(BOOTSTRAP)
    state = load(PROGRAM_STATE)
    inbox = load(SUPERVISOR_INBOX)
    base = load(BASE_CONTROL)
    exec_addendum = load(EXEC_CONTROL)
    program_addendum = load(PROGRAM_CONTROL)
    steering = load(STEERING)

    # Owner authority.
    require(bootstrap.get("active_program") == EXPECTED_PROGRAM, "BOOTSTRAP_PROGRAM")
    require(bootstrap.get("active_stage") == EXPECTED_STAGE, "BOOTSTRAP_STAGE")
    require(bootstrap.get("sole_owner_directive") == EXPECTED_OWNER_DIRECTIVE, "BOOTSTRAP_OWNER_DIRECTIVE")
    require(state.get("program_id") == EXPECTED_PROGRAM_ID, "PROGRAM_STATE_PROGRAM_ID")
    require(state.get("stage") == EXPECTED_STAGE, "PROGRAM_STATE_STAGE")
    require(state.get("owner_directive") == EXPECTED_OWNER_DIRECTIVE, "PROGRAM_STATE_OWNER_DIRECTIVE")

    # Lossless effective-control composition.
    require(base.get("schema_version") == "4.1", "BASE_CONTROL_VERSION")
    require(exec_addendum.get("schema_version") == "4.2-execution-boundary-addendum", "EXEC_ADDENDUM_VERSION")
    require(program_addendum.get("schema_version") == "4.3-program-authority-addendum", "PROGRAM_ADDENDUM_VERSION")
    require(program_addendum.get("effective_control_version") == EXPECTED_EFFECTIVE_CONTROL, "EFFECTIVE_CONTROL_VERSION")
    require(
        program_addendum.get("composition_order")
        == ["4.1", "4.2-execution-boundary-addendum", "4.3-program-authority-addendum"],
        "COMPOSITION_ORDER",
    )
    require(program_addendum.get("base_control_path") == "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json", "BASE_CONTROL_PATH")
    require(
        program_addendum.get("execution_boundary_addendum_path")
        == "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json",
        "EXEC_ADDENDUM_PATH",
    )

    owner = program_addendum.get("owner_program_authority") or {}
    override = program_addendum.get("program_identity_override") or {}
    require(owner.get("bootstrap_minimal_path") == "research_entity/continuity/BOOTSTRAP_MINIMAL.json", "OWNER_BOOTSTRAP_PATH")
    require(owner.get("program_state_path") == "research_entity/rooms/PROGRAM_STATE.json", "OWNER_PROGRAM_STATE_PATH")
    require(owner.get("owner_directive_path") == EXPECTED_OWNER_DIRECTIVE, "OWNER_DIRECTIVE_PATH")
    require(override.get("active_program") == EXPECTED_PROGRAM, "EFFECTIVE_PROGRAM")
    require(override.get("target_stage") == EXPECTED_STAGE, "EFFECTIVE_STAGE")
    require(override.get("active_program") != LEGACY_PROGRAM, "LEGACY_PROGRAM_EFFECTIVE")
    require(override.get("target_stage") != LEGACY_STAGE, "LEGACY_STAGE_EFFECTIVE")
    require(override.get("product_endpoint_definition") != LEGACY_ENDPOINT, "LEGACY_ENDPOINT_EFFECTIVE")

    # Supervisor must select the same effective control. The base inbox may remain stale
    # only when 8.43 explicitly quarantines that field from work selection.
    require(steering.get("program") == EXPECTED_PROGRAM, "STEERING_PROGRAM")
    require(steering.get("stage") == EXPECTED_STAGE, "STEERING_STAGE")
    require(steering.get("effective_control") == EXPECTED_EFFECTIVE_CONTROL, "STEERING_EFFECTIVE_CONTROL")
    if inbox.get("active_program") != EXPECTED_PROGRAM:
        adjudication = steering.get("adjudication") or {}
        require(inbox.get("active_program") == LEGACY_PROGRAM, "UNRECOGNIZED_INBOX_PROGRAM")
        require(
            adjudication.get("legacy_supervisor_inbox_active_program")
            == "STALE_COMPATIBILITY_METADATA_PENDING_DOCUMENT_SYNC",
            "INBOX_STALE_NOT_QUARANTINED",
        )
        require(
            adjudication.get("program_selection_control_sync") == "SOURCE_RESOLVED_BY_LOSSLESS_ADDENDUM",
            "PROGRAM_SELECTION_NOT_RESOLVED",
        )

    # Critical safety rules must remain conjunctively active through 4.1 + 4.2 + 4.3.
    require(base.get("mode") == "FREE_ONLY", "BASE_FREE_ONLY")
    base_policy = base.get("cycle_policy") or {}
    require(base_policy.get("paid_fallback") is False, "BASE_PAID_FALLBACK")
    require(base_policy.get("automatic_subscription_upgrade") is False, "BASE_AUTO_UPGRADE")
    require(base_policy.get("vps_testing") == "FORBIDDEN", "BASE_VPS_TESTING")

    exec_rules = exec_addendum.get("preserved_hard_rules") or {}
    require(exec_addendum.get("mode") == "FREE_ONLY", "EXEC_FREE_ONLY")
    require(exec_rules.get("free_only") is True, "EXEC_PRESERVE_FREE_ONLY")
    require(exec_rules.get("paid_fallback") is False, "EXEC_PRESERVE_PAID_FALLBACK")
    require(exec_rules.get("together_forbidden") is True, "EXEC_TOGETHER_FORBIDDEN")
    require(exec_rules.get("frank_harness_modification") == "FORBIDDEN", "EXEC_HARNESS_PROTECTED")

    program_rules = program_addendum.get("preserved_hard_rules") or {}
    require(program_addendum.get("mode") == "FREE_ONLY", "PROGRAM_FREE_ONLY")
    require(program_rules.get("free_only") is True, "PROGRAM_PRESERVE_FREE_ONLY")
    require(program_rules.get("paid_fallback") is False, "PROGRAM_PRESERVE_PAID_FALLBACK")
    require(program_rules.get("together_forbidden_under_current_control") is True, "PROGRAM_TOGETHER_FORBIDDEN")
    require(program_rules.get("model_output_is_candidate_not_truth") is True, "MODEL_NOT_TRUTH")
    require(program_rules.get("runtime_credit_requires_exact_admitted_execution") is True, "EXACT_RUNTIME_REQUIRED")
    require(program_rules.get("frank_harness_modification") == "FORBIDDEN", "PROGRAM_HARNESS_PROTECTED")

    print(
        json.dumps(
            {
                "schema": "EFFECTIVE_PROGRAM_AUTHORITY_ASSERTION/v1",
                "status": "PASS",
                "program": EXPECTED_PROGRAM,
                "stage": EXPECTED_STAGE,
                "effective_control": EXPECTED_EFFECTIVE_CONTROL,
                "supervisor_inbox_document_sync_pending": inbox.get("active_program") != EXPECTED_PROGRAM,
                "credit": "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
