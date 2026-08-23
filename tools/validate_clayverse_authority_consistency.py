#!/usr/bin/env python3
"""Fail closed when ClayVerse product authority or inherited safety fences disagree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

OWNER_DIRECTIVE = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"
EXPECTED_PROGRAM = "CLAYVERSE_SINGLE_CONTAINER"
EXPECTED_STAGE = "CLAYVERSE_ARTIFACT"
EXPECTED_RELEASE = "ONE_OCI_DOCKER_COMPATIBLE_CONTAINER_IMAGE"
EXPECTED_EFFECTIVE_CONTROL = "4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+4.4-clayverse-product-authority-addendum"
IDENTITY_GUARD = "research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md"
CONTROL41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
STEERING844 = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_44.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


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
        "control41": root / CONTROL41,
        "control42": root / CONTROL42,
        "control43": root / CONTROL43,
        "control44": root / CONTROL44,
        "steering844": root / STEERING844,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": "CLAYVERSE_AUTHORITY_CONSISTENCY/v2", "pass": False, "errors": errors}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        manifest = load_json(paths["manifest"])
        control41 = load_json(paths["control41"])
        control42 = load_json(paths["control42"])
        control43 = load_json(paths["control43"])
        control44 = load_json(paths["control44"])
        steering = load_json(paths["steering844"])
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": "CLAYVERSE_AUTHORITY_CONSISTENCY/v2",
            "pass": False,
            "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"],
        }

    directive = paths["directive"].read_text(encoding="utf-8")
    fast_boot = paths["fast_boot"].read_text(encoding="utf-8")
    footer = paths["footer"].read_text(encoding="utf-8")
    architecture = paths["architecture"].read_text(encoding="utf-8")
    readme = paths["readme"].read_text(encoding="utf-8")

    # Preserve the canonical research-entity join/identity fences while changing product authority.
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
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(errors, execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_ONLY_MISSING")
    require(errors, execution.get("vps_testing_forbidden") is True, "PROGRAM_VPS_TEST_FENCE_MISSING")
    require(errors, execution.get("together_forbidden") is True, "PROGRAM_TOGETHER_FENCE_MISSING")

    require(errors, manifest.get("artifact") == "ClayVerse", "MANIFEST_ARTIFACT_MISMATCH")
    require(errors, manifest.get("product_endpoint") == "ClayVerse", "MANIFEST_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, manifest.get("release_form") == EXPECTED_RELEASE, "MANIFEST_RELEASE_FORM_MISMATCH")
    require(errors, manifest.get("canonical_workspace") == "the artefact/", "MANIFEST_WORKSPACE_MISMATCH")

    # Preserve the inherited 4.1 -> 4.2 -> 4.3 safety chain instead of trusting 4.4's self-report.
    require(errors, control41.get("schema_version") == "4.1", "CONTROL41_VERSION_MISMATCH")
    require(errors, control41.get("status") == "ACTIVE" and control41.get("mode") == "FREE_ONLY", "CONTROL41_FREE_ONLY_WEAKENED")
    cycle41 = control41.get("cycle_policy") or {}
    require(errors, cycle41.get("paid_fallback") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(errors, cycle41.get("automatic_subscription_upgrade") is False, "CONTROL41_AUTO_UPGRADE_WEAKENED")
    require(errors, cycle41.get("vps_testing") == "FORBIDDEN", "CONTROL41_VPS_TEST_WEAKENED")
    authority41 = control41.get("authority_rules") or []
    require(errors, "model_output_is_candidate_not_truth" in authority41, "CONTROL41_MODEL_TRUTH_FENCE_MISSING")
    require(errors, "autonomous_cycle_may_not_modify_FRANK_harness" in authority41, "CONTROL41_FRANK_HARNESS_FENCE_MISSING")

    blob41 = git_blob_sha(paths["control41"])
    blob42 = git_blob_sha(paths["control42"])
    blob43 = git_blob_sha(paths["control43"])

    require(errors, control42.get("schema_version") == "4.2-execution-boundary-addendum", "CONTROL42_VERSION_MISMATCH")
    require(errors, control42.get("status") == "ACTIVE" and control42.get("mode") == "FREE_ONLY", "CONTROL42_FREE_ONLY_WEAKENED")
    require(errors, control42.get("base_control_path") == CONTROL41, "CONTROL42_BASE_PATH_MISMATCH")
    require(errors, control42.get("base_control_blob_sha") == blob41, "CONTROL42_BASE_BLOB_MISMATCH")
    hard42 = control42.get("preserved_hard_rules") or {}
    require(errors, hard42.get("free_only") is True and hard42.get("paid_fallback") is False, "CONTROL42_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard42.get("together_forbidden") is True, "CONTROL42_TOGETHER_FENCE_WEAKENED")
    require(errors, hard42.get("frank_harness_modification") == "FORBIDDEN", "CONTROL42_FRANK_HARNESS_FENCE_WEAKENED")
    routing42 = control42.get("execution_routing") or {}
    require(errors, routing42.get("direct_vps_host_candidate_execution") == "FORBIDDEN", "CONTROL42_DIRECT_VPS_FENCE_WEAKENED")
    require(errors, routing42.get("persistent_self_hosted_candidate_execution") == "FORBIDDEN", "CONTROL42_SELF_HOSTED_FENCE_WEAKENED")
    require(errors, routing42.get("production_host_testing") == "FORBIDDEN", "CONTROL42_PRODUCTION_TEST_FENCE_WEAKENED")

    require(errors, control43.get("schema_version") == "4.3-program-authority-addendum", "CONTROL43_VERSION_MISMATCH")
    require(errors, control43.get("status") == "ACTIVE" and control43.get("mode") == "FREE_ONLY", "CONTROL43_FREE_ONLY_WEAKENED")
    require(errors, control43.get("base_control_path") == CONTROL41, "CONTROL43_BASE_PATH_MISMATCH")
    require(errors, control43.get("base_control_blob_sha") == blob41, "CONTROL43_BASE_BLOB_MISMATCH")
    require(errors, control43.get("execution_boundary_addendum_path") == CONTROL42, "CONTROL43_EXEC_PATH_MISMATCH")
    require(errors, control43.get("execution_boundary_addendum_blob_sha") == blob42, "CONTROL43_EXEC_BLOB_MISMATCH")
    hard43 = control43.get("preserved_hard_rules") or {}
    require(errors, hard43.get("free_only") is True and hard43.get("paid_fallback") is False, "CONTROL43_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard43.get("together_forbidden_under_current_control") is True, "CONTROL43_TOGETHER_FENCE_WEAKENED")
    require(errors, hard43.get("model_output_is_candidate_not_truth") is True, "CONTROL43_MODEL_TRUTH_FENCE_WEAKENED")
    require(errors, hard43.get("runtime_credit_requires_exact_admitted_execution") is True, "CONTROL43_RUNTIME_EVIDENCE_WEAKENED")
    require(errors, hard43.get("frank_harness_modification") == "FORBIDDEN", "CONTROL43_FRANK_HARNESS_FENCE_WEAKENED")

    override = control44.get("program_identity_override") or {}
    hard44 = control44.get("preserved_hard_rules") or {}
    require(errors, control44.get("status") == "ACTIVE" and control44.get("mode") == "FREE_ONLY", "CONTROL44_NOT_ACTIVE_FREE_ONLY")
    require(errors, control44.get("base_control_path") == CONTROL41, "CONTROL44_BASE_PATH_MISMATCH")
    require(errors, control44.get("execution_boundary_addendum_path") == CONTROL42, "CONTROL44_EXEC_PATH_MISMATCH")
    require(errors, control44.get("prior_program_authority_addendum_path") == CONTROL43, "CONTROL44_PRIOR_PATH_MISMATCH")
    require(errors, control44.get("prior_program_authority_addendum_blob_sha") == blob43, "CONTROL44_PRIOR_BLOB_MISMATCH")
    require(errors, control44.get("composition_order") == ["4.1", "4.2-execution-boundary-addendum", "4.3-program-authority-addendum", "4.4-clayverse-product-authority-addendum"], "CONTROL44_COMPOSITION_ORDER_MISMATCH")
    require(errors, control44.get("effective_control_version") == EXPECTED_EFFECTIVE_CONTROL, "CONTROL44_EFFECTIVE_VERSION_MISMATCH")
    require(errors, override.get("active_program") == EXPECTED_PROGRAM, "CONTROL44_PROGRAM_MISMATCH")
    require(errors, override.get("target_stage") == EXPECTED_STAGE, "CONTROL44_STAGE_MISMATCH")
    require(errors, override.get("product_endpoint") == "ClayVerse", "CONTROL44_ENDPOINT_MISMATCH")
    require(errors, override.get("release_form") == EXPECTED_RELEASE, "CONTROL44_RELEASE_MISMATCH")
    require(errors, hard44.get("free_only") is True and hard44.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, hard44.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, hard44.get("vps_testing") is False, "CONTROL44_VPS_TEST_WEAKENED")
    require(errors, hard44.get("runtime_credit_requires_exact_admitted_isolated_execution") is True, "CONTROL44_RUNTIME_EVIDENCE_WEAKENED")
    require(errors, hard44.get("model_output_is_candidate_not_truth") is True, "CONTROL44_MODEL_TRUTH_FENCE_WEAKENED")
    require(errors, hard44.get("frank_harness_modification") == "FORBIDDEN", "CONTROL44_FRANK_HARNESS_FENCE_WEAKENED")

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

    return {
        "schema": "CLAYVERSE_AUTHORITY_CONSISTENCY/v2",
        "pass": not errors,
        "errors": errors,
        "checked": {name: path.relative_to(root).as_posix() for name, path in paths.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = validate(Path(args.repo_root).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
