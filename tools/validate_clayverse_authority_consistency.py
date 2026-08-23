#!/usr/bin/env python3
"""Fail closed when ClayVerse product authority or inherited safety fences disagree."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

OWNER_DIRECTIVE = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"
EXPECTED_PROGRAM = "CLAYVERSE_SINGLE_CONTAINER"
EXPECTED_STAGE = "CLAYVERSE_ARTIFACT"
EXPECTED_RELEASE = "ONE_OCI_DOCKER_COMPATIBLE_CONTAINER_IMAGE"
EXPECTED_DYNAMIC_PRIMARY = "WHOLE_CLAYVERSE_OCI_PRODUCT"
IDENTITY_GUARD = "research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md"
BASE41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
EXEC42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
PROGRAM43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
STEERING844 = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_44.json"
ROOT_CLAUDE = "CLAUDE.md"
EXPECTED_EFFECTIVE_CONTROL = "4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+4.4-clayverse-product-authority-addendum"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "directive": root / OWNER_DIRECTIVE,
        "fast_boot": root / "research_entity/continuity/CLAYVERSE_FAST_BOOTSTRAP_SOURCE_CURRENT.md",
        "footer": root / "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
        "manifest": root / "the artefact/manifest.json",
        "architecture": root / "the artefact/ARCHITECTURE.md",
        "readme": root / "the artefact/README.md",
        "repo_claude": root / ROOT_CLAUDE,
        "base41": root / BASE41,
        "exec42": root / EXEC42,
        "program43": root / PROGRAM43,
        "control44": root / CONTROL44,
        "steering844": root / STEERING844,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": "CLAYVERSE_AUTHORITY_CONSISTENCY/v3", "pass": False, "errors": errors}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        manifest = load_json(paths["manifest"])
        base = load_json(paths["base41"])
        exec_addendum = load_json(paths["exec42"])
        program_addendum = load_json(paths["program43"])
        control = load_json(paths["control44"])
        steering = load_json(paths["steering844"])
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "CLAYVERSE_AUTHORITY_CONSISTENCY/v3", "pass": False, "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"]}

    directive = paths["directive"].read_text(encoding="utf-8")
    fast_boot = paths["fast_boot"].read_text(encoding="utf-8")
    footer = paths["footer"].read_text(encoding="utf-8")
    architecture = paths["architecture"].read_text(encoding="utf-8")
    readme = paths["readme"].read_text(encoding="utf-8")
    repo_claude = paths["repo_claude"].read_text(encoding="utf-8")

    # Preserve canonical research-entity join/identity fences while changing product authority.
    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    require(errors, bootstrap.get("expected_entity_version") == canonical.get("entity_version"), "BOOTSTRAP_CANONICAL_VERSION_MISMATCH")
    require(errors, bootstrap.get("expected_revision") == canonical.get("revision"), "BOOTSTRAP_CANONICAL_REVISION_MISMATCH")
    require(errors, bootstrap.get("expected_state_hash") == canonical.get("state_hash"), "BOOTSTRAP_CANONICAL_STATE_HASH_MISMATCH")
    require(errors, (bootstrap.get("identity") or {}).get("every_turn_guard") == IDENTITY_GUARD, "BOOTSTRAP_IDENTITY_GUARD_POINTER_MISSING")
    require(errors, "every substantive prompt_run_id" in str((bootstrap.get("per_turn") or {}).get("identity_injection", "")), "BOOTSTRAP_PER_TURN_IDENTITY_INJECTION_MISSING")
    invariants = "\n".join(str(x) for x in bootstrap.get("mandatory_invariants", []))
    require(errors, "every substantive prompt_run_id refreshes the Research Entity identity injection" in invariants, "BOOTSTRAP_IDENTITY_INVARIANT_MISSING")
    require(errors, bootstrap.get("active_program") == EXPECTED_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == EXPECTED_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("sole_owner_directive") == OWNER_DIRECTIVE, "BOOTSTRAP_OWNER_DIRECTIVE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == "ClayVerse", "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, bootstrap.get("release_form") == EXPECTED_RELEASE, "BOOTSTRAP_RELEASE_FORM_MISMATCH")
    require(errors, bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("vps_testing") == "FORBIDDEN", "BOOTSTRAP_VPS_TEST_FENCE_MISSING")

    require(errors, program.get("program_id") == "clayverse-single-container", "PROGRAM_ID_MISMATCH")
    require(errors, program.get("stage") == EXPECTED_STAGE and program.get("current_stage") == EXPECTED_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("owner_directive") == OWNER_DIRECTIVE, "PROGRAM_OWNER_DIRECTIVE_MISMATCH")
    require(errors, program.get("product_endpoint") == "ClayVerse", "PROGRAM_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, program.get("release_form") == EXPECTED_RELEASE, "PROGRAM_RELEASE_FORM_MISMATCH")
    require(errors, "CLAYVERSE" in str(program.get("current_stage_goal", "")).upper(), "PROGRAM_STAGE_GOAL_NOT_CLAYVERSE")
    dynamic = program.get("dynamic_targets") or {}
    require(errors, dynamic.get("primary") == EXPECTED_DYNAMIC_PRIMARY, "PROGRAM_DYNAMIC_PRIMARY_MISMATCH")
    require(errors, "CLAYVERSE" in str(program.get("current_frontier", "")).upper(), "PROGRAM_FRONTIER_NOT_CLAYVERSE")
    require(errors, "CLAYVERSE" in str(program.get("go_contract", "")).upper(), "PROGRAM_GO_CONTRACT_NOT_CLAYVERSE")
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(errors, execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_ONLY_MISSING")
    require(errors, execution.get("vps_testing_forbidden") is True, "PROGRAM_VPS_TEST_FENCE_MISSING")
    require(errors, execution.get("together_forbidden") is True, "PROGRAM_TOGETHER_FENCE_MISSING")

    require(errors, manifest.get("artifact") == "ClayVerse", "MANIFEST_ARTIFACT_MISMATCH")
    require(errors, manifest.get("product_endpoint") == "ClayVerse", "MANIFEST_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, manifest.get("release_form") == EXPECTED_RELEASE, "MANIFEST_RELEASE_FORM_MISMATCH")
    require(errors, manifest.get("canonical_workspace") == "the artefact/", "MANIFEST_WORKSPACE_MISMATCH")

    # 4.4 may override product selection only. Verify inherited 4.1/4.2/4.3 bytes semantically
    # instead of trusting 4.4's own assertion that those safety fences remain preserved.
    require(errors, base.get("schema_version") == "4.1", "BASE41_VERSION_MISMATCH")
    require(errors, base.get("status") == "ACTIVE", "BASE41_NOT_ACTIVE")
    require(errors, base.get("mode") == "FREE_ONLY", "BASE41_FREE_ONLY_WEAKENED")
    base_policy = base.get("cycle_policy") or {}
    require(errors, base_policy.get("paid_fallback") is False, "BASE41_PAID_FALLBACK_WEAKENED")
    require(errors, base_policy.get("automatic_subscription_upgrade") is False, "BASE41_AUTO_UPGRADE_WEAKENED")
    require(errors, base_policy.get("vps_testing") == "FORBIDDEN", "BASE41_VPS_TEST_WEAKENED")
    require(errors, base_policy.get("self_hosted_vps_test_runners") == "FORBIDDEN", "BASE41_SELF_HOSTED_VPS_WEAKENED")
    require(errors, base_policy.get("production_host_testing") == "FORBIDDEN", "BASE41_PRODUCTION_TEST_WEAKENED")

    require(errors, exec_addendum.get("schema_version") == "4.2-execution-boundary-addendum", "EXEC42_VERSION_MISMATCH")
    require(errors, exec_addendum.get("status") == "ACTIVE", "EXEC42_NOT_ACTIVE")
    require(errors, exec_addendum.get("mode") == "FREE_ONLY", "EXEC42_FREE_ONLY_WEAKENED")
    require(errors, exec_addendum.get("base_control_path") == BASE41, "EXEC42_BASE_PATH_MISMATCH")
    require(errors, exec_addendum.get("base_control_version") == "4.1", "EXEC42_BASE_VERSION_MISMATCH")
    exec_hard = exec_addendum.get("preserved_hard_rules") or {}
    require(errors, exec_hard.get("free_only") is True and exec_hard.get("paid_fallback") is False, "EXEC42_FREE_ONLY_CLAIM_WEAKENED")
    require(errors, exec_hard.get("together_forbidden") is True, "EXEC42_TOGETHER_WEAKENED")
    require(errors, exec_hard.get("frank_harness_modification") == "FORBIDDEN", "EXEC42_HARNESS_WEAKENED")
    routing = exec_addendum.get("execution_routing") or {}
    require(errors, routing.get("direct_vps_host_candidate_execution") == "FORBIDDEN", "EXEC42_DIRECT_VPS_WEAKENED")
    require(errors, routing.get("persistent_self_hosted_candidate_execution") == "FORBIDDEN", "EXEC42_SELF_HOSTED_WEAKENED")
    require(errors, routing.get("production_host_testing") == "FORBIDDEN", "EXEC42_PRODUCTION_TEST_WEAKENED")

    require(errors, program_addendum.get("schema_version") == "4.3-program-authority-addendum", "PROGRAM43_VERSION_MISMATCH")
    require(errors, program_addendum.get("status") == "ACTIVE", "PROGRAM43_NOT_ACTIVE")
    require(errors, program_addendum.get("mode") == "FREE_ONLY", "PROGRAM43_FREE_ONLY_WEAKENED")
    require(errors, program_addendum.get("base_control_path") == BASE41, "PROGRAM43_BASE_PATH_MISMATCH")
    require(errors, program_addendum.get("execution_boundary_addendum_path") == EXEC42, "PROGRAM43_EXEC42_PATH_MISMATCH")
    program_hard = program_addendum.get("preserved_hard_rules") or {}
    require(errors, program_hard.get("free_only") is True and program_hard.get("paid_fallback") is False, "PROGRAM43_FREE_ONLY_CLAIM_WEAKENED")
    require(errors, program_hard.get("together_forbidden_under_current_control") is True, "PROGRAM43_TOGETHER_WEAKENED")
    require(errors, program_hard.get("runtime_credit_requires_exact_admitted_execution") is True, "PROGRAM43_RUNTIME_EVIDENCE_WEAKENED")
    require(errors, program_hard.get("frank_harness_modification") == "FORBIDDEN", "PROGRAM43_HARNESS_WEAKENED")

    override = control.get("program_identity_override") or {}
    hard = control.get("preserved_hard_rules") or {}
    require(errors, control.get("schema_version") == "4.4-clayverse-product-authority-addendum", "CONTROL44_VERSION_MISMATCH")
    require(errors, control.get("status") == "ACTIVE", "CONTROL44_NOT_ACTIVE")
    require(errors, control.get("mode") == "FREE_ONLY", "CONTROL44_MODE_WEAKENED")
    require(errors, control.get("base_control_path") == BASE41, "CONTROL44_BASE_PATH_MISMATCH")
    require(errors, control.get("execution_boundary_addendum_path") == EXEC42, "CONTROL44_EXEC42_PATH_MISMATCH")
    require(errors, control.get("prior_program_authority_addendum_path") == PROGRAM43, "CONTROL44_PROGRAM43_PATH_MISMATCH")
    require(errors, control.get("composition_order") == ["4.1", "4.2-execution-boundary-addendum", "4.3-program-authority-addendum", "4.4-clayverse-product-authority-addendum"], "CONTROL44_COMPOSITION_ORDER_MISMATCH")
    require(errors, control.get("effective_control_version") == EXPECTED_EFFECTIVE_CONTROL, "CONTROL44_EFFECTIVE_VERSION_MISMATCH")
    require(errors, override.get("active_program") == EXPECTED_PROGRAM, "CONTROL44_PROGRAM_MISMATCH")
    require(errors, override.get("target_stage") == EXPECTED_STAGE, "CONTROL44_STAGE_MISMATCH")
    require(errors, override.get("product_endpoint") == "ClayVerse", "CONTROL44_ENDPOINT_MISMATCH")
    require(errors, override.get("release_form") == EXPECTED_RELEASE, "CONTROL44_RELEASE_MISMATCH")
    require(errors, hard.get("free_only") is True and hard.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, hard.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, hard.get("vps_testing") is False, "CONTROL44_VPS_TEST_WEAKENED")
    require(errors, hard.get("runtime_credit_requires_exact_admitted_isolated_execution") is True, "CONTROL44_RUNTIME_EVIDENCE_WEAKENED")
    require(errors, hard.get("frank_harness_modification") == "FORBIDDEN", "CONTROL44_HARNESS_WEAKENED")

    require(errors, steering.get("program") == EXPECTED_PROGRAM and steering.get("stage") == EXPECTED_STAGE, "STEERING844_PROGRAM_STAGE_MISMATCH")
    require(errors, steering.get("effective_control") == EXPECTED_EFFECTIVE_CONTROL, "STEERING844_CONTROL44_NOT_EFFECTIVE")
    adjudication = steering.get("adjudication") or {}
    require(errors, adjudication.get("free_only") is True and adjudication.get("together_forbidden") is True and adjudication.get("vps_testing") is False, "STEERING844_SAFETY_WEAKENED")

    directive_upper = directive[:1200].upper()
    require(errors, "CURRENT OWNER DIRECTIVE" in directive_upper, "DIRECTIVE_NOT_CURRENT")
    require(errors, "SUPERSEDED" not in directive_upper[:220], "DIRECTIVE_MARKED_SUPERSEDED")
    require(errors, "ACTIVE CLAYVERSE PROGRAM" in fast_boot.upper(), "FAST_BOOT_NOT_ACTIVE_CLAYVERSE")
    require(errors, "PROGRAM: CLAYVERSE SINGLE-CONTAINER" in footer.upper(), "FOOTER_PROGRAM_MISMATCH")
    require(errors, "STAGE: CLAYVERSE_ARTIFACT" in footer.upper(), "FOOTER_STAGE_MISMATCH")
    require(errors, "CLAYVERSE IS THE PRODUCT ENDPOINT" in architecture.upper(), "ARCHITECTURE_PRODUCT_MISMATCH")
    readme_head = readme[:3000].upper()
    require(errors, "CLAYVERSE SINGLE-CONTAINER PRODUCT" in readme_head, "README_PRODUCT_MISMATCH")
    require(errors, "CLAYVERSE" in readme_head and "ONE OCI/DOCKER-COMPATIBLE" in readme_head, "README_RELEASE_MISMATCH")
    require(errors, not ("CLAYVERSE SINGLE-CONTAINER ENDPOINT" in readme_head and "SUPERSEDED" in readme_head), "README_CLAYVERSE_SUPERSEDED")

    # Root CLAUDE.md is a high-leverage repository-organ routing surface.
    repo_claude_head = repo_claude[:7000].upper()
    require(errors, "`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`" in repo_claude_head, "ROOT_CLAUDE_PROGRAM_MISMATCH")
    require(errors, "`STAGE=CLAYVERSE_ARTIFACT`" in repo_claude_head, "ROOT_CLAUDE_STAGE_MISMATCH")
    require(errors, "CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.MD" in repo_claude_head, "ROOT_CLAUDE_OWNER_DIRECTIVE_MISSING")
    require(errors, "MINI_ENTITY_PIPELINE_ALL_IN_ONE" not in repo_claude_head, "ROOT_CLAUDE_MINI_ENTITY_PROGRAM_ACTIVE")
    require(errors, "BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.MD" not in repo_claude_head, "ROOT_CLAUDE_STALE_BLOGPOST_DIRECTIVE")

    return {"schema": "CLAYVERSE_AUTHORITY_CONSISTENCY/v3", "pass": not errors, "errors": errors, "checked": {name: path.relative_to(root).as_posix() for name, path in paths.items()}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = validate(Path(args.repo_root).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
