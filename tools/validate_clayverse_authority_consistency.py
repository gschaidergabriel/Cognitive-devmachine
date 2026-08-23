#!/usr/bin/env python3
"""Compatibility-named fail-closed authority guard for current EntityOS + HCU.

Current autonomous-supervisor authority is FREE_ONLY steering 8.61. Historical
ClayVerse 4.1->4.4 controls remain immutable donor/safety ancestry and are not current
product/work-selection authority. Owner paid-training prose remains provenance only in
this supervisor mode and must not enable credential lookup, preflight, network I/O,
job creation, spend, provider credit, or training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CURRENT_PROGRAM = "ENTITYOS_HCU"
CURRENT_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
CURRENT_PRODUCT = "EntityOS"
CURRENT_COMPUTE_ARCHITECTURE = "HCU"
CURRENT_AUTHORITY = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_61.json"
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v3"
PAID_DIRECTIVE_PROVENANCE = "research_entity/claycode/OWNER_ONE_SHOT_08B_JSPACE_GWT_TRAINING_DIRECTIVE_2026-08-24.md"
ROOT_CLAUDE = "CLAUDE.md"
CONTROL41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
LEGACY_EXPECTED_CONTROL = "4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+4.4-clayverse-product-authority-addendum"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def _validate_legacy_safety_ancestry(errors, paths, c41, c42, c43, c44) -> None:
    require(errors, c41.get("schema_version") == "4.1", "CONTROL41_VERSION_MISMATCH")
    require(errors, c41.get("status") == "ACTIVE" and c41.get("mode") == "FREE_ONLY", "CONTROL41_FREE_ONLY_WEAKENED")
    cycle41 = c41.get("cycle_policy") or {}
    require(errors, cycle41.get("paid_fallback") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(errors, cycle41.get("automatic_subscription_upgrade") is False, "CONTROL41_AUTO_UPGRADE_WEAKENED")
    require(errors, cycle41.get("vps_testing") == "FORBIDDEN", "CONTROL41_VPS_TEST_WEAKENED")
    authority41 = c41.get("authority_rules") or []
    require(errors, "model_output_is_candidate_not_truth" in authority41, "CONTROL41_MODEL_TRUTH_FENCE_MISSING")
    require(errors, "autonomous_cycle_may_not_modify_FRANK_harness" in authority41, "CONTROL41_FRANK_HARNESS_FENCE_MISSING")

    blob41 = git_blob_sha(paths["control41"])
    blob42 = git_blob_sha(paths["control42"])
    blob43 = git_blob_sha(paths["control43"])

    require(errors, c42.get("schema_version") == "4.2-execution-boundary-addendum", "CONTROL42_VERSION_MISMATCH")
    require(errors, c42.get("status") == "ACTIVE" and c42.get("mode") == "FREE_ONLY", "CONTROL42_FREE_ONLY_WEAKENED")
    require(errors, c42.get("base_control_path") == CONTROL41, "CONTROL42_BASE_PATH_MISMATCH")
    require(errors, c42.get("base_control_blob_sha") == blob41, "CONTROL42_BASE_BLOB_MISMATCH")
    hard42 = c42.get("preserved_hard_rules") or {}
    require(errors, hard42.get("free_only") is True and hard42.get("paid_fallback") is False, "CONTROL42_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard42.get("together_forbidden") is True, "CONTROL42_TOGETHER_FENCE_WEAKENED")
    require(errors, hard42.get("frank_harness_modification") == "FORBIDDEN", "CONTROL42_FRANK_HARNESS_FENCE_WEAKENED")
    routing42 = c42.get("execution_routing") or {}
    require(errors, routing42.get("direct_vps_host_candidate_execution") == "FORBIDDEN", "CONTROL42_DIRECT_VPS_FENCE_WEAKENED")
    require(errors, routing42.get("persistent_self_hosted_candidate_execution") == "FORBIDDEN", "CONTROL42_SELF_HOSTED_FENCE_WEAKENED")
    require(errors, routing42.get("production_host_testing") == "FORBIDDEN", "CONTROL42_PRODUCTION_TEST_FENCE_WEAKENED")

    require(errors, c43.get("schema_version") == "4.3-program-authority-addendum", "CONTROL43_VERSION_MISMATCH")
    require(errors, c43.get("status") == "ACTIVE" and c43.get("mode") == "FREE_ONLY", "CONTROL43_FREE_ONLY_WEAKENED")
    require(errors, c43.get("base_control_path") == CONTROL41, "CONTROL43_BASE_PATH_MISMATCH")
    require(errors, c43.get("base_control_blob_sha") == blob41, "CONTROL43_BASE_BLOB_MISMATCH")
    require(errors, c43.get("execution_boundary_addendum_path") == CONTROL42, "CONTROL43_EXEC_PATH_MISMATCH")
    require(errors, c43.get("execution_boundary_addendum_blob_sha") == blob42, "CONTROL43_EXEC_BLOB_MISMATCH")
    hard43 = c43.get("preserved_hard_rules") or {}
    require(errors, hard43.get("free_only") is True and hard43.get("paid_fallback") is False, "CONTROL43_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard43.get("together_forbidden_under_current_control") is True, "CONTROL43_TOGETHER_FENCE_WEAKENED")
    require(errors, hard43.get("model_output_is_candidate_not_truth") is True, "CONTROL43_MODEL_TRUTH_FENCE_WEAKENED")
    require(errors, hard43.get("runtime_credit_requires_exact_admitted_execution") is True, "CONTROL43_RUNTIME_EVIDENCE_WEAKENED")
    require(errors, hard43.get("frank_harness_modification") == "FORBIDDEN", "CONTROL43_FRANK_HARNESS_FENCE_WEAKENED")

    require(errors, c44.get("schema_version") == "4.4-clayverse-product-authority-addendum", "CONTROL44_VERSION_MISMATCH")
    require(errors, c44.get("status") == "ACTIVE" and c44.get("mode") == "FREE_ONLY", "CONTROL44_NOT_ACTIVE_FREE_ONLY")
    require(errors, c44.get("base_control_path") == CONTROL41, "CONTROL44_BASE_PATH_MISMATCH")
    require(errors, c44.get("execution_boundary_addendum_path") == CONTROL42, "CONTROL44_EXEC_PATH_MISMATCH")
    require(errors, c44.get("prior_program_authority_addendum_path") == CONTROL43, "CONTROL44_PRIOR_PATH_MISMATCH")
    require(errors, c44.get("prior_program_authority_addendum_blob_sha") == blob43, "CONTROL44_PRIOR_BLOB_MISMATCH")
    require(errors, c44.get("composition_order") == ["4.1", "4.2-execution-boundary-addendum", "4.3-program-authority-addendum", "4.4-clayverse-product-authority-addendum"], "CONTROL44_COMPOSITION_ORDER_MISMATCH")
    require(errors, c44.get("effective_control_version") == LEGACY_EXPECTED_CONTROL, "CONTROL44_EFFECTIVE_VERSION_MISMATCH")
    override = c44.get("program_identity_override") or {}
    require(errors, override.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER" and override.get("target_stage") == "CLAYVERSE_ARTIFACT" and override.get("product_endpoint") == "ClayVerse", "CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH")
    hard44 = c44.get("preserved_hard_rules") or {}
    require(errors, hard44.get("free_only") is True and hard44.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, hard44.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, hard44.get("vps_testing") is False, "CONTROL44_VPS_TEST_WEAKENED")
    require(errors, hard44.get("runtime_credit_requires_exact_admitted_isolated_execution") is True, "CONTROL44_RUNTIME_EVIDENCE_WEAKENED")
    require(errors, hard44.get("model_output_is_candidate_not_truth") is True, "CONTROL44_MODEL_TRUTH_FENCE_WEAKENED")
    require(errors, hard44.get("frank_harness_modification") == "FORBIDDEN", "CONTROL44_FRANK_HARNESS_FENCE_WEAKENED")


def _validate_free_only_policy(errors, execution: dict, prefix: str) -> None:
    require(errors, execution.get("free_only") is True, f"{prefix}_FREE_ONLY_MISSING")
    require(errors, execution.get("isolated_sandbox_only") is True, f"{prefix}_ISOLATED_ONLY_MISSING")
    require(errors, execution.get("vps_testing_forbidden") is True, f"{prefix}_VPS_TEST_FENCE_MISSING")
    require(errors, execution.get("self_hosted_vps_test_runners_forbidden") is True, f"{prefix}_SELF_HOSTED_FENCE_MISSING")
    require(errors, execution.get("production_host_testing_forbidden") is True, f"{prefix}_PRODUCTION_TEST_FENCE_MISSING")
    require(errors, execution.get("together_general_inference_and_fallback_forbidden") is True, f"{prefix}_TOGETHER_GENERAL_FENCE_MISSING")
    require(errors, execution.get("owner_paid_one_shot_directive_present_as_provenance") is True, f"{prefix}_PAID_DIRECTIVE_PROVENANCE_MISSING")
    require(errors, execution.get("owner_paid_one_shot_directive_file") == PAID_DIRECTIVE_PROVENANCE, f"{prefix}_PAID_DIRECTIVE_PATH_MISMATCH")
    require(errors, execution.get("owner_paid_one_shot_job_consumed") is False, f"{prefix}_PAID_ONE_SHOT_CONSUMED_UNEXPECTED")
    require(errors, execution.get("current_supervisor_together_training_forbidden") is True, f"{prefix}_CURRENT_TOGETHER_TRAINING_NOT_FORBIDDEN")
    require(errors, execution.get("paid_or_unknown_provider_admission_boundary") == "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION", f"{prefix}_PAID_ADMISSION_BOUNDARY_WEAKENED")
    require(errors, execution.get("other_paid_fallback") is False, f"{prefix}_OTHER_PAID_FALLBACK_WEAKENED")


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "steering861": root / CURRENT_AUTHORITY,
        "paid_directive_provenance": root / PAID_DIRECTIVE_PROVENANCE,
        "footer": root / "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
        "manifest": root / "the artefact/manifest.json",
        "architecture": root / "the artefact/ARCHITECTURE.md",
        "readme": root / "the artefact/README.md",
        "repo_claude": root / ROOT_CLAUDE,
        "control41": root / CONTROL41,
        "control42": root / CONTROL42,
        "control43": root / CONTROL43,
        "control44": root / CONTROL44,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": errors}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        steering = load_json(paths["steering861"])
        manifest = load_json(paths["manifest"])
        c41 = load_json(paths["control41"]); c42 = load_json(paths["control42"])
        c43 = load_json(paths["control43"]); c44 = load_json(paths["control44"])
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"]}

    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    ident = bootstrap.get("identity") or {}
    require(errors, ident.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, ident.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_TEMP_WORKER_ROLE_MISMATCH")
    require(errors, bootstrap.get("schema_version") == "8.61", "BOOTSTRAP_SCHEMA_MISMATCH")
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, bootstrap.get("authority_correction") == CURRENT_AUTHORITY, "BOOTSTRAP_AUTHORITY_POINTER_MISMATCH")
    require(errors, bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_FREE_SANDBOX_ONLY_IN_CURRENT_AUTONOMOUS_SUPERVISOR_MODE", "BOOTSTRAP_EXECUTION_FENCE_MISMATCH")
    require(errors, bootstrap.get("free_only") is True and bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_FREE_ONLY_OR_PAID_FALLBACK_WEAKENED")
    require(errors, str(bootstrap.get("together_api", "")).startswith("FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE"), "BOOTSTRAP_TOGETHER_POLICY_MISMATCH")
    require(errors, bootstrap.get("together_training_authority_provenance") == PAID_DIRECTIVE_PROVENANCE, "BOOTSTRAP_PAID_DIRECTIVE_PROVENANCE_MISMATCH")
    require(errors, bootstrap.get("current_supervisor_together_training") == "FORBIDDEN_BEFORE_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION", "BOOTSTRAP_CURRENT_TOGETHER_TRAINING_FENCE_MISSING")
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")
    btracks = set(bootstrap.get("go_required_tracks") or [])
    require(errors, "GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS_OR_NO_CHANGE_WITH_REASON" in btracks, "BOOTSTRAP_GO_TRACK_C_MISSING")

    require(errors, program.get("schema_version") == "8.61", "PROGRAM_SCHEMA_MISMATCH")
    require(errors, program.get("program_id") == "entityos-hcu" and program.get("status") == "ACTIVE", "PROGRAM_ID_OR_STATUS_MISMATCH")
    require(errors, program.get("stage") == CURRENT_STAGE and program.get("current_stage") == CURRENT_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("product") == CURRENT_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(errors, program.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, program.get("authority_correction") == CURRENT_AUTHORITY, "PROGRAM_AUTHORITY_POINTER_MISMATCH")
    _validate_free_only_policy(errors, program.get("execution_policy") or {}, "PROGRAM")
    ptracks = program.get("go_required_tracks") or {}
    require(errors, ptracks.get("track_a") == "ENTITYOS_EXECUTABLE_CONVERGENCE", "PROGRAM_GO_TRACK_A_MISMATCH")
    require(errors, ptracks.get("track_b") == "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT", "PROGRAM_GO_TRACK_B_MISMATCH")
    require(errors, ptracks.get("track_c") == "GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS", "PROGRAM_GO_TRACK_C_MISMATCH")
    training = program.get("training_program") or {}
    require(errors, training.get("current_method") == "ZERO_COST_LOCAL_EXPERIMENTATION_ONLY", "PROGRAM_TRAINING_METHOD_NOT_FREE_ONLY")
    require(errors, training.get("owner_paid_one_shot_directive_status") == "QUARANTINED_FOR_CURRENT_FREE_ONLY_SUPERVISOR", "PROGRAM_PAID_DIRECTIVE_NOT_QUARANTINED")
    require(errors, training.get("paid_preflight_or_job_creation_allowed_now") is False, "PROGRAM_PAID_PREFLIGHT_OR_JOB_CREATION_ALLOWED")
    credit = program.get("runtime_credit") or {}
    require(errors, credit.get("entityos_hcu_whole_runtime_credit") == 0 and credit.get("jspace_model_runtime_credit") == 0 and credit.get("training_credit") == 0 and credit.get("whole_product_pass") is False, "PROGRAM_RUNTIME_OR_TRAINING_CREDIT_PREMATURE")

    require(errors, steering.get("schema_version") == "8.61", "STEERING861_SCHEMA_MISMATCH")
    require(errors, steering.get("status") == "CURRENT_AUTONOMOUS_SUPERVISOR_STEERING", "STEERING861_STATUS_MISMATCH")
    require(errors, steering.get("program") == CURRENT_PROGRAM and steering.get("product") == CURRENT_PRODUCT and steering.get("compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "STEERING861_IDENTITY_MISMATCH")
    supersedes = set(steering.get("supersedes_for_this_free_only_supervisor") or [])
    require(errors, "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_53.json" in supersedes, "STEERING861_853_NOT_SUPERSEDED")
    free = steering.get("free_only") or {}
    require(errors, free.get("enabled") is True and free.get("no_paid_fallback") is True, "STEERING861_FREE_ONLY_WEAKENED")
    require(errors, free.get("together_training") == "FORBIDDEN_IN_THIS_SUPERVISOR_MODE", "STEERING861_TOGETHER_TRAINING_WEAKENED")
    require(errors, free.get("together_general_inference") == "FORBIDDEN", "STEERING861_TOGETHER_INFERENCE_WEAKENED")
    require(errors, free.get("paid_subscription_unknown_provider_execution") == "FAIL_CLOSED", "STEERING861_PROVIDER_ADMISSION_WEAKENED")
    promotion = steering.get("promotion_state") or {}
    require(errors, promotion.get("entityos_whole_runtime_pass") is False and promotion.get("hcu_runtime_credit_change") is False and promotion.get("canonical_semantics_promotion") is False and promotion.get("training_credit") == 0, "STEERING861_PROMOTION_PREMATURE")

    require(errors, manifest.get("artifact") == CURRENT_PRODUCT and manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_MISMATCH")
    require(errors, manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, manifest.get("stage") == CURRENT_STAGE and manifest.get("canonical_workspace") == "the artefact/", "MANIFEST_STAGE_OR_WORKSPACE_MISMATCH")
    require(errors, manifest.get("authority_correction") == CURRENT_AUTHORITY, "MANIFEST_AUTHORITY_POINTER_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    _validate_free_only_policy(errors, manifest.get("execution_policy") or {}, "MANIFEST")
    mcredit = manifest.get("runtime_credit") or {}
    require(errors, mcredit.get("entityos_hcu_whole_runtime_credit") == 0 and mcredit.get("jspace_model_runtime_credit") == 0 and mcredit.get("training_credit") == 0 and mcredit.get("whole_product_pass") is False, "MANIFEST_RUNTIME_OR_TRAINING_CREDIT_PREMATURE")

    _validate_legacy_safety_ancestry(errors, paths, c41, c42, c43, c44)

    footer = paths["footer"].read_text(encoding="utf-8").upper()
    architecture = paths["architecture"].read_text(encoding="utf-8").upper()
    readme = paths["readme"].read_text(encoding="utf-8").upper()
    repo_claude = paths["repo_claude"].read_text(encoding="utf-8").upper()
    require(errors, "PROGRAM: ENTITYOS + HCU" in footer and "PRODUCT: ENTITYOS" in footer and "COMPUTE ARCHITECTURE: HCU" in footer, "FOOTER_ENTITYOS_HCU_MISMATCH")
    require(errors, "FREE_ONLY" in footer and "8.61" in footer, "FOOTER_FREE_ONLY_861_MISSING")
    require(errors, "ENTITYOS" in architecture[:2500] and "HCU" in architecture[:2500], "ARCHITECTURE_ENTITYOS_HCU_MISSING")
    require(errors, "CLAYVERSE IS THE PRODUCT ENDPOINT" not in architecture[:2500], "ARCHITECTURE_STALE_CLAYVERSE_PRODUCT_AUTHORITY")
    require(errors, "SUPERVISOR_STEERING_8_61.JSON" in readme[:6000], "README_CURRENT_AUTHORITY_MISSING")
    require(errors, "FREE_ONLY" in readme and "TOGETHER" in readme, "README_FREE_ONLY_PROVIDER_FENCE_MISSING")
    require(errors, "`PROGRAM=ENTITYOS_HCU`" in repo_claude[:6000] and "`PRODUCT=ENTITYOS`" in repo_claude[:6000], "ROOT_CLAUDE_IDENTITY_MISMATCH")
    require(errors, "SUPERVISOR_STEERING_8_61.JSON" in repo_claude[:6000], "ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING")
    require(errors, "FREE_ONLY" in repo_claude and "TOGETHER" in repo_claude, "ROOT_CLAUDE_FREE_ONLY_PROVIDER_FENCE_MISSING")

    return {"schema": CURRENT_SCHEMA, "pass": not errors, "errors": errors, "checked": {name: path.relative_to(root).as_posix() for name, path in paths.items()}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = validate(Path(args.repo_root).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
