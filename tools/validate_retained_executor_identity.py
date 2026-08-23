#!/usr/bin/env python3
"""Fail-closed validator for the single retained EntityOS/HCU execution-controller identity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "ENTITYOS_HCU_RETAINED_EXECUTION_CONTROLLER_IDENTITY/v1"
EXPECTED_RESEARCH_REPO = "gschaidergabriel/clay-global-research-entity"
EXPECTED_DONOR_REF = "gschaidergabriel/clay-global-research-entity#1263"
EXPECTED_EXECUTOR_REPO = "gschaidergabriel/Dr.-Unterweger"
EXPECTED_EXECUTOR_PR = 810
EXPECTED_EXECUTOR_REF = f"{EXPECTED_EXECUTOR_REPO}#{EXPECTED_EXECUTOR_PR}"
CONTRACT_REL = "research_entity/continuity/RETAINED_EXECUTION_CONTROLLER_IDENTITY.json"
WRONG_LOCAL_REF = "gschaidergabriel/clay-global-research-entity#810"

class ExecutorIdentityError(ValueError):
    pass

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutorIdentityError(message)

def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)

def validate_contract(contract: dict[str, Any]) -> None:
    _require(contract.get("schema") == SCHEMA, "schema:mismatch")
    _require(contract.get("product") == "EntityOS", "product:mismatch")
    _require(contract.get("compute_architecture") == "HCU", "architecture:mismatch")
    _require(contract.get("mode") == "FREE_ONLY", "mode:not_free_only")
    _require(contract.get("research_repository") == EXPECTED_RESEARCH_REPO, "research_repository:mismatch")
    donor = contract.get("retained_hcu_donor")
    _require(isinstance(donor, dict), "donor:missing")
    _require(donor.get("qualified_ref") == EXPECTED_DONOR_REF, "donor:qualified_ref_mismatch")
    _require(_valid_sha(donor.get("head_observed_2026_08_24")), "donor:head_sha_invalid")
    executor = contract.get("retained_execution_controller")
    _require(isinstance(executor, dict), "executor:missing")
    _require(executor.get("repository") == EXPECTED_EXECUTOR_REPO, "executor:wrong_repository")
    _require(executor.get("pull_request") == EXPECTED_EXECUTOR_PR, "executor:wrong_pull_request")
    _require(executor.get("qualified_ref") == EXPECTED_EXECUTOR_REF, "executor:qualified_ref_mismatch")
    _require(executor.get("qualified_ref") != WRONG_LOCAL_REF, "executor:resolved_to_research_repo_pr810")
    _require(_valid_sha(executor.get("head_observed_2026_08_24")), "executor:head_sha_invalid")
    freshness = contract.get("head_freshness")
    _require(isinstance(freshness, dict), "head_freshness:missing")
    _require(freshness.get("snapshot_heads_are_current_authority") is False, "head_freshness:snapshot_promoted_to_authority")
    _require(freshness.get("execution_requires_live_refresh") is True, "head_freshness:live_refresh_not_required")
    fence = contract.get("ambiguity_fence")
    _require(isinstance(fence, dict), "ambiguity_fence:missing")
    _require(fence.get("unqualified_pr810_for_current_executor_selection") == "FORBIDDEN", "ambiguity_fence:unqualified_pr810_not_forbidden")
    _require(fence.get("known_wrong_resolution") == WRONG_LOCAL_REF, "ambiguity_fence:wrong_local_resolution_not_bound")
    _require("MUST additionally bind the exact live head SHA" in fence.get("selection_rule", ""), "ambiguity_fence:live_head_binding_not_mandatory")
    boundary = contract.get("authority_boundary")
    _require(isinstance(boundary, dict), "authority_boundary:missing")
    _require(boundary.get("creates_new_executor") is False, "authority_boundary:new_executor")
    _require(boundary.get("creates_new_state_or_effect_authority") is False, "authority_boundary:new_authority")
    _require(boundary.get("runtime_credit_change") == 0, "authority_boundary:runtime_credit")
    _require(boundary.get("jspace_model_runtime_credit_change") == 0, "authority_boundary:jspace_credit")
    _require(boundary.get("training_credit_change") == 0, "authority_boundary:training_credit")
    _require(boundary.get("whole_product_pass") is False, "authority_boundary:whole_product_pass")

def _load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))

def validate_repo_surfaces(root: Path) -> None:
    bootstrap = _load_json(root, "research_entity/continuity/BOOTSTRAP_MINIMAL.json")
    _require(bootstrap.get("retained_hcu_donor") == EXPECTED_DONOR_REF, "surface:bootstrap_donor")
    _require(bootstrap.get("retained_execution_controller") == EXPECTED_EXECUTOR_REF, "surface:bootstrap_executor")
    _require(bootstrap.get("retained_execution_controller_identity_contract") == CONTRACT_REL, "surface:bootstrap_contract")
    program = _load_json(root, "research_entity/rooms/PROGRAM_STATE.json")
    retained = program.get("retained_lanes") or {}
    _require(retained.get("hcu_donor") == EXPECTED_DONOR_REF, "surface:program_donor")
    _require(retained.get("execution_controller") == EXPECTED_EXECUTOR_REF, "surface:program_executor")
    _require(retained.get("execution_controller_identity_contract") == CONTRACT_REL, "surface:program_contract")
    _require(retained.get("unqualified_pr810_executor_selection") == "FORBIDDEN_REPOSITORY_AMBIGUOUS", "surface:program_unqualified_fence")
    manifest = _load_json(root, "the artefact/manifest.json")
    lanes = manifest.get("retained_lane_identity") or {}
    _require(lanes.get("hcu_donor") == EXPECTED_DONOR_REF, "surface:manifest_donor")
    _require(lanes.get("execution_controller") == EXPECTED_EXECUTOR_REF, "surface:manifest_executor")
    _require(lanes.get("execution_controller_contract") == CONTRACT_REL, "surface:manifest_contract")
    inbox = _load_json(root, "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
    frontier = inbox.get("current_frontier") or {}
    _require(frontier.get("retained_hcu_pr_qualified_ref") == EXPECTED_DONOR_REF, "surface:inbox_donor")
    _require(frontier.get("retained_execution_controller_qualified_ref") == EXPECTED_EXECUTOR_REF, "surface:inbox_executor")
    _require(frontier.get("retained_execution_controller_identity_contract") == CONTRACT_REL, "surface:inbox_contract")
    steering = _load_json(root, "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_63.json")
    _require(steering.get("schema_version") == "8.63", "surface:steering_epoch")
    _require(steering.get("mode") == "FREE_ONLY", "surface:steering_mode")
    for name, path in {
        "root": root / "CLAUDE.md",
        "workers": root / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_8_63.md",
        "readme": root / "the artefact/README.md",
    }.items():
        text = path.read_text(encoding="utf-8")
        _require(EXPECTED_DONOR_REF in text, f"surface:{name}_donor")
        _require(EXPECTED_EXECUTOR_REF in text, f"surface:{name}_executor")
        _require(CONTRACT_REL in text, f"surface:{name}_contract")

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    contract = _load_json(root, CONTRACT_REL)
    validate_contract(contract)
    validate_repo_surfaces(root)
    print("RETAINED_EXECUTION_CONTROLLER_IDENTITY:PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
