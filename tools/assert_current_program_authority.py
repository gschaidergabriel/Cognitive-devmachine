#!/usr/bin/env python3
"""Fail closed if active Clay control metadata regresses behind current program authority.

This is a source/control assertion only. Passing it does not grant runtime, model,
J-Space/GWT, Claude-adapter, BASE, Frank-v0.1, or whole-product credit.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
SUPERVISOR_INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
AUTONOMOUS_CONTROL = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"

EXPECTED_PROGRAM = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
EXPECTED_PROGRAM_ID = "mini-entity-pipeline-all-in-one"
EXPECTED_STAGE = "MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT"
EXPECTED_OWNER_DIRECTIVE = (
    "research_entity/global/ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION.md"
)
LEGACY_ACTIVE_PROGRAM = "CLAYVERSE_CLAY_MACHINE_ONLY"
LEGACY_STAGE = "CLAY_MACHINE"
LEGACY_ENDPOINT_DEFINITION = "SINGLE_FILE_CLAY_COMPUTER"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"PROGRAM_AUTHORITY_ASSERTION_FAIL:{path}:NOT_OBJECT")
    return value


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SystemExit(f"PROGRAM_AUTHORITY_ASSERTION_FAIL:{code}")


def main() -> int:
    bootstrap = load(BOOTSTRAP)
    state = load(PROGRAM_STATE)
    inbox = load(SUPERVISOR_INBOX)
    control = load(AUTONOMOUS_CONTROL)

    # Canonical owner/program cross-binding.
    require(bootstrap.get("active_program") == EXPECTED_PROGRAM, "BOOTSTRAP_PROGRAM")
    require(bootstrap.get("active_stage") == EXPECTED_STAGE, "BOOTSTRAP_STAGE")
    require(
        bootstrap.get("sole_owner_directive") == EXPECTED_OWNER_DIRECTIVE,
        "BOOTSTRAP_OWNER_DIRECTIVE",
    )
    require(state.get("program_id") == EXPECTED_PROGRAM_ID, "PROGRAM_STATE_PROGRAM_ID")
    require(state.get("stage") == EXPECTED_STAGE, "PROGRAM_STATE_STAGE")
    require(state.get("owner_directive") == EXPECTED_OWNER_DIRECTIVE, "PROGRAM_STATE_OWNER_DIRECTIVE")
    require(inbox.get("active_program") == EXPECTED_PROGRAM, "SUPERVISOR_INBOX_PROGRAM")
    require(control.get("active_program") == EXPECTED_PROGRAM, "CONTROL_PROGRAM")
    require(control.get("target_stage") == EXPECTED_STAGE, "CONTROL_STAGE")
    require(LEGACY_ACTIVE_PROGRAM != control.get("active_program"), "CONTROL_LEGACY_PROGRAM")
    require(LEGACY_STAGE != control.get("target_stage"), "CONTROL_LEGACY_STAGE")
    require(
        LEGACY_ENDPOINT_DEFINITION != control.get("product_endpoint_definition"),
        "CONTROL_LEGACY_ENDPOINT",
    )
    require(EXPECTED_OWNER_DIRECTIVE in control.get("owner_directive", ""), "CONTROL_OWNER_DIRECTIVE")

    # Safety controls must survive program migration unchanged in force.
    policy = control.get("cycle_policy") or {}
    require(control.get("mode") == "FREE_ONLY", "CONTROL_FREE_ONLY")
    require(policy.get("paid_fallback") is False, "PAID_FALLBACK_DISABLED")
    require(policy.get("automatic_subscription_upgrade") is False, "AUTO_UPGRADE_DISABLED")
    require(policy.get("github_hosted_actions_paid_remediation") is False, "PAID_ACTIONS_REMEDIATION_DISABLED")
    require(policy.get("vps_testing") == "FORBIDDEN", "VPS_TESTING_FORBIDDEN")
    require(policy.get("self_hosted_vps_test_runners") == "FORBIDDEN", "SELF_HOSTED_VPS_FORBIDDEN")
    require(policy.get("production_host_testing") == "FORBIDDEN", "PRODUCTION_TESTING_FORBIDDEN")

    rules = set(control.get("authority_rules") or [])
    require("model_output_is_candidate_not_truth" in rules, "MODEL_NOT_TRUTH")
    require("autonomous_cycle_may_not_modify_FRANK_harness" in rules, "HARNESS_PROTECTED")
    require(
        "all_current_build_test_experiment_and_runtime_validation_execution_is_isolated_sandbox_only"
        in rules,
        "SANDBOX_ONLY",
    )
    require(
        "zero_step_or_no_runner_red_is_instrument_state_not_code_or_semantic_failure" in rules,
        "PRESTEP_CLASSIFICATION",
    )

    print(
        json.dumps(
            {
                "schema": "CURRENT_PROGRAM_AUTHORITY_ASSERTION/v1",
                "status": "PASS",
                "program": EXPECTED_PROGRAM,
                "stage": EXPECTED_STAGE,
                "owner_directive": EXPECTED_OWNER_DIRECTIVE,
                "credit": "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
