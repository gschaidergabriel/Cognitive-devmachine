#!/usr/bin/env python3
"""Fail-closed authority successor-closure guard for current EntityOS + HCU.

The compatibility filename is retained because workflows and historical receipts address
it. Current authority is discovered from the newest versioned SUPERVISOR_STEERING file
and must be closed across all current work-selection surfaces. Historical ClayVerse
4.1->4.4 controls remain hash-bound donor/safety ancestry only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

CURRENT_PROGRAM = "ENTITYOS_HCU"
CURRENT_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
CURRENT_PRODUCT = "EntityOS"
CURRENT_COMPUTE_ARCHITECTURE = "HCU"
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v3"
MIN_AUTHORITY_VERSION = (8, 63)
AUTHORITY_DIR = "research_entity/claycode/autonomous"
AUTHORITY_RE = re.compile(r"^SUPERVISOR_STEERING_(\d+)_(\d+)\.json$")
TRAINING_PROVENANCE = "research_entity/claycode/OWNER_ONE_SHOT_08B_JSPACE_GWT_TRAINING_DIRECTIVE_2026-08-24.md"
PAID_BOUNDARY = "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION"
CURRENT_SUPERVISOR_TRAINING = "FORBIDDEN_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION"

CONTROL41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
LEGACY_EXPECTED_CONTROL = "4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+4.4-clayverse-product-authority-addendum"
ROOT_CLAUDE = "CLAUDE.md"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def discover_current_authority(root: Path) -> tuple[str | None, tuple[int, int] | None, list[str]]:
    errors: list[str] = []
    authority_root = root / AUTHORITY_DIR
    if not authority_root.is_dir():
        return None, None, [f"MISSING:authority_dir:{AUTHORITY_DIR}"]
    found: list[tuple[tuple[int, int], str]] = []
    for path in authority_root.glob("SUPERVISOR_STEERING_*.json"):
        match = AUTHORITY_RE.match(path.name)
        if match:
            found.append(((int(match.group(1)), int(match.group(2))), f"{AUTHORITY_DIR}/{path.name}"))
    if not found:
        return None, None, ["NO_VERSIONED_SUPERVISOR_STEERING"]
    found.sort()
    version, rel = found[-1]
    if version < MIN_AUTHORITY_VERSION:
        errors.append("SUPERVISOR_AUTHORITY_BELOW_8_63")
    return rel, version, errors


def _validate_legacy_safety_ancestry(errors: list[str], paths: dict[str, Path], c41, c42, c43, c44) -> None:
    require(errors, c41.get("schema_version") == "4.1", "CONTROL41_VERSION_MISMATCH")
    require(errors, c41.get("status") == "ACTIVE" and c41.get("mode") == "FREE_ONLY", "CONTROL41_FREE_ONLY_WEAKENED")
    cycle41 = c41.get("cycle_policy") or {}
    require(errors, cycle41.get("paid_fallback") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(errors, cycle41.get("automatic_subscription_upgrade") is False, "CONTROL41_AUTO_UPGRADE_WEAKENED")
    require(errors, cycle41.get("vps_testing") == "FORBIDDEN", "CONTROL41_VPS_TEST_WEAKENED")
    rules41 = set(c41.get("authority_rules") or [])
    require(errors, "model_output_is_candidate_not_truth" in rules41, "CONTROL41_MODEL_TRUTH_FENCE_MISSING")
    require(errors, "autonomous_cycle_may_not_modify_FRANK_harness" in rules41, "CONTROL41_FRANK_HARNESS_FENCE_MISSING")

    blob41 = git_blob_sha(paths["control41"])
    blob42 = git_blob_sha(paths["control42"])
    blob43 = git_blob_sha(paths["control43"])

    require(errors, c42.get("schema_version") == "4.2-execution-boundary-addendum", "CONTROL42_VERSION_MISMATCH")
    require(errors, c42.get("base_control_path") == CONTROL41, "CONTROL42_BASE_PATH_MISMATCH")
    require(errors, c42.get("base_control_blob_sha") == blob41, "CONTROL42_BASE_BLOB_MISMATCH")
    h42 = c42.get("preserved_hard_rules") or {}
    require(errors, h42.get("free_only") is True and h42.get("paid_fallback") is False, "CONTROL42_FREE_ONLY_FENCE_WEAKENED")
    require(errors, h42.get("together_forbidden") is True, "CONTROL42_TOGETHER_FENCE_WEAKENED")
    r42 = c42.get("execution_routing") or {}
    require(errors, r42.get("direct_vps_host_candidate_execution") == "FORBIDDEN", "CONTROL42_DIRECT_VPS_FENCE_WEAKENED")
    require(errors, r42.get("persistent_self_hosted_candidate_execution") == "FORBIDDEN", "CONTROL42_SELF_HOSTED_FENCE_WEAKENED")
    require(errors, r42.get("production_host_testing") == "FORBIDDEN", "CONTROL42_PRODUCTION_TEST_FENCE_WEAKENED")

    require(errors, c43.get("schema_version") == "4.3-program-authority-addendum", "CONTROL43_VERSION_MISMATCH")
    require(errors, c43.get("base_control_blob_sha") == blob41, "CONTROL43_BASE_BLOB_MISMATCH")
    require(errors, c43.get("execution_boundary_addendum_path") == CONTROL42, "CONTROL43_EXEC_PATH_MISMATCH")
    require(errors, c43.get("execution_boundary_addendum_blob_sha") == blob42, "CONTROL43_EXEC_BLOB_MISMATCH")
    h43 = c43.get("preserved_hard_rules") or {}
    require(errors, h43.get("free_only") is True and h43.get("paid_fallback") is False, "CONTROL43_FREE_ONLY_FENCE_WEAKENED")
    require(errors, h43.get("together_forbidden_under_current_control") is True, "CONTROL43_TOGETHER_FENCE_WEAKENED")
    require(errors, h43.get("runtime_credit_requires_exact_admitted_execution") is True, "CONTROL43_RUNTIME_EVIDENCE_WEAKENED")

    require(errors, c44.get("schema_version") == "4.4-clayverse-product-authority-addendum", "CONTROL44_VERSION_MISMATCH")
    require(errors, c44.get("prior_program_authority_addendum_path") == CONTROL43, "CONTROL44_PRIOR_PATH_MISMATCH")
    require(errors, c44.get("prior_program_authority_addendum_blob_sha") == blob43, "CONTROL44_PRIOR_BLOB_MISMATCH")
    require(errors, c44.get("effective_control_version") == LEGACY_EXPECTED_CONTROL, "CONTROL44_EFFECTIVE_VERSION_MISMATCH")
    override = c44.get("program_identity_override") or {}
    require(
        errors,
        override.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER"
        and override.get("target_stage") == "CLAYVERSE_ARTIFACT"
        and override.get("product_endpoint") == "ClayVerse",
        "CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH",
    )
    h44 = c44.get("preserved_hard_rules") or {}
    require(errors, h44.get("free_only") is True and h44.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, h44.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, h44.get("vps_testing") is False, "CONTROL44_VPS_TEST_WEAKENED")
    require(errors, h44.get("runtime_credit_requires_exact_admitted_isolated_execution") is True, "CONTROL44_RUNTIME_EVIDENCE_WEAKENED")


def validate(root: Path) -> dict:
    errors: list[str] = []
    current_authority, current_version, discovery_errors = discover_current_authority(root)
    errors.extend(discovery_errors)
    if current_authority is None or current_version is None:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": errors}

    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "supervisor": root / current_authority,
        "inbox": root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
        "training_provenance": root / TRAINING_PROVENANCE,
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
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": errors, "current_authority": current_authority}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        supervisor = load_json(paths["supervisor"])
        inbox = load_json(paths["inbox"])
        manifest = load_json(paths["manifest"])
        c41 = load_json(paths["control41"])
        c42 = load_json(paths["control42"])
        c43 = load_json(paths["control43"])
        c44 = load_json(paths["control44"])
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"]}

    version_string = f"{current_version[0]}.{current_version[1]}"
    require(errors, supervisor.get("schema_version") == version_string, "SUPERVISOR_FILENAME_SCHEMA_MISMATCH")
    require(errors, supervisor.get("program") == CURRENT_PROGRAM, "SUPERVISOR_PROGRAM_MISMATCH")
    require(errors, supervisor.get("product") == CURRENT_PRODUCT, "SUPERVISOR_PRODUCT_MISMATCH")
    require(errors, supervisor.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "SUPERVISOR_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, supervisor.get("mode") == "FREE_ONLY", "SUPERVISOR_MODE_NOT_FREE_ONLY")
    free = supervisor.get("free_only_policy") or {}
    require(errors, free.get("no_paid_fallback") is True, "SUPERVISOR_PAID_FALLBACK_WEAKENED")
    require(errors, free.get("paid_subscription_unknown_fail_closed") is True, "SUPERVISOR_UNKNOWN_PAID_LANE_NOT_FAIL_CLOSED")
    together_closed = (
        free.get("together_forbidden") is True
        or (
            free.get("together_general_inference") == "FORBIDDEN"
            and free.get("together_training") == "FORBIDDEN"
            and free.get("together_preflight_or_key_lookup") == "FORBIDDEN"
        )
    )
    require(errors, together_closed, "SUPERVISOR_TOGETHER_FENCE_WEAKENED")
    vercel_scope = str(free.get("vercel_hobby_sandbox") or "")
    require(errors, "BOUNDED" in vercel_scope and "FIXED_HASH_BOUND" in vercel_scope, "SUPERVISOR_BOUNDED_SANDBOX_SCOPE_MISSING")
    require(errors, free.get("fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path") is True, "SUPERVISOR_COST_FAIL_CLOSED_FENCE_MISSING")
    if current_version >= (8, 63):
        coordination = supervisor.get("coordination_authority") or {}
        require(errors, coordination.get("required_before_unusual_intervention") is True, "SUPERVISOR_ATOMIC_LEASE_NOT_REQUIRED")
        require(errors, "GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md" in str(coordination.get("atomic_lease_protocol") or ""), "SUPERVISOR_ATOMIC_LEASE_PROTOCOL_MISSING")
        require(errors, "ZERO_NEW_UNUSUAL_EXPERIMENTS" in str(coordination.get("fail_closed_rule") or ""), "SUPERVISOR_UNUSUAL_EXPERIMENT_FAIL_CLOSED_MISSING")
    sprom = supervisor.get("promotion_state") or {}
    require(errors, sprom.get("entityos_whole_runtime_pass") is False, "SUPERVISOR_WHOLE_PASS_PREMATURE")
    require(errors, sprom.get("training_credit") == 0, "SUPERVISOR_TRAINING_CREDIT_NONZERO")

    require(errors, inbox.get("steering") == current_authority, "INBOX_STEERING_NOT_NEWEST")
    require(errors, inbox.get("schema_version") == version_string, "INBOX_SCHEMA_NOT_NEWEST")
    ifree = inbox.get("free_only") or {}
    require(errors, ifree.get("enabled") is True and ifree.get("no_paid_fallback") is True, "INBOX_FREE_ONLY_WEAKENED")
    require(errors, ifree.get("together_forbidden") is True, "INBOX_TOGETHER_FENCE_WEAKENED")
    if current_version >= (8, 63):
        icoord = inbox.get("coordination") or {}
        require(errors, icoord.get("required_before_unusual_intervention") is True, "INBOX_ATOMIC_LEASE_NOT_REQUIRED")
        require(errors, icoord.get("no_valid_shared_id_or_atomic_claim") == "ZERO_NEW_UNUSUAL_EXPERIMENTS", "INBOX_UNUSUAL_EXPERIMENT_FAIL_CLOSED_MISSING")

    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    ident = bootstrap.get("identity") or {}
    require(errors, ident.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, ident.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_TEMP_WORKER_ROLE_MISMATCH")
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, bootstrap.get("authority_correction") == current_authority, "BOOTSTRAP_AUTHORITY_POINTER_MISMATCH")
    require(errors, bootstrap.get("free_only") is True and bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_FREE_ONLY_MISMATCH")
    require(errors, "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE" in str(bootstrap.get("together_api")), "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("together_training_authority_provenance") == TRAINING_PROVENANCE, "BOOTSTRAP_TRAINING_PROVENANCE_MISMATCH")
    require(errors, bootstrap.get("together_one_shot_training_consumed") is False, "BOOTSTRAP_ONE_SHOT_PREMATURELY_CONSUMED")
    bootstrap_training_fence = str(bootstrap.get("current_supervisor_together_training") or "")
    require(
        errors,
        bootstrap_training_fence.startswith("FORBIDDEN_BEFORE_")
        and "KEY_LOOKUP" in bootstrap_training_fence
        and "NETWORK_IO" in bootstrap_training_fence
        and "JOB_CREATION" in bootstrap_training_fence,
        "BOOTSTRAP_TRAINING_ADMISSION_FENCE_MISSING",
    )
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")
    execution_surface = str(bootstrap.get("execution_surface") or "")
    require(errors, "AUTHORIZED_ISOLATED_FREE_SANDBOX_ONLY" in execution_surface, "BOOTSTRAP_EXECUTION_FENCE_MISSING")
    require(errors, "VERCEL_HOBBY" in execution_surface and "FIXED_HASH_BOUND" in execution_surface, "BOOTSTRAP_BOUNDED_SANDBOX_SCOPE_MISSING")
    if current_version >= (8, 63):
        require(errors, bootstrap.get("go_unusual_experiment_atomic_lease_protocol") == "research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md", "BOOTSTRAP_ATOMIC_LEASE_PROTOCOL_MISSING")
        require(errors, "CREATE_ONLY_CANONICAL_CLAIM" in str(bootstrap.get("go_unusual_experiment_claim_rule") or ""), "BOOTSTRAP_ATOMIC_LEASE_CLAIM_RULE_MISSING")

    require(errors, program.get("program_id") == "entityos-hcu" and program.get("status") == "ACTIVE", "PROGRAM_ID_OR_STATUS_MISMATCH")
    require(errors, program.get("stage") == CURRENT_STAGE and program.get("current_stage") == CURRENT_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("product") == CURRENT_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(errors, program.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, program.get("authority_correction") == current_authority, "PROGRAM_AUTHORITY_POINTER_MISMATCH")
    pauth = program.get("authority") or {}
    require(errors, pauth.get("external_effects") == "EffectGate+EffectJournal", "PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    require(errors, pauth.get("second_persistent_identity") == "FORBIDDEN", "PROGRAM_SECOND_IDENTITY_NOT_FORBIDDEN")
    require(errors, pauth.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN", "PROGRAM_SECOND_AUTHORITY_NOT_FORBIDDEN")
    pexec = program.get("execution_policy") or {}
    require(errors, pexec.get("free_only") is True and pexec.get("isolated_sandbox_only") is True, "PROGRAM_FREE_ONLY_EXECUTION_MISMATCH")
    require(errors, pexec.get("vercel_hobby_bounded_included_tier_sandbox_admitted") is True, "PROGRAM_FREE_SANDBOX_ADMISSION_MISSING")
    require(errors, pexec.get("remaining_monthly_sandbox_quota_directly_observed") is False, "PROGRAM_QUOTA_MUST_NOT_BE_ASSUMED")
    require(errors, pexec.get("vps_testing_forbidden") is True and pexec.get("self_hosted_vps_test_runners_forbidden") is True and pexec.get("production_host_testing_forbidden") is True, "PROGRAM_HOST_EXECUTION_FENCE_WEAKENED")
    require(errors, pexec.get("together_general_inference_and_fallback_forbidden") is True, "PROGRAM_TOGETHER_INFERENCE_FENCE_MISSING")
    require(errors, pexec.get("owner_paid_one_shot_job_consumed") is False, "PROGRAM_ONE_SHOT_PREMATURELY_CONSUMED")
    require(errors, pexec.get("current_supervisor_together_training_forbidden") is True, "PROGRAM_TOGETHER_TRAINING_FENCE_MISSING")
    require(errors, pexec.get("paid_or_unknown_provider_admission_boundary") == PAID_BOUNDARY, "PROGRAM_PAID_ADMISSION_FENCE_MISSING")
    require(errors, pexec.get("other_paid_fallback") is False, "PROGRAM_OTHER_PAID_FALLBACK_WEAKENED")
    if current_version >= (8, 63):
        require(errors, pexec.get("go_unusual_experiment_atomic_lease_protocol") == "research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md", "PROGRAM_ATOMIC_LEASE_PROTOCOL_MISSING")
        require(errors, pexec.get("unusual_experiment_without_reproducible_claim") == "COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT", "PROGRAM_UNUSUAL_EXPERIMENT_FAIL_CLOSED_MISSING")
    credit = program.get("runtime_credit") or {}
    require(errors, credit.get("entityos_hcu_whole_runtime_credit") == 0, "PROGRAM_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("jspace_model_runtime_credit") == 0, "PROGRAM_JSPACE_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("training_credit") == 0, "PROGRAM_TRAINING_CREDIT_NONZERO")
    require(errors, credit.get("whole_product_pass") is False, "PROGRAM_WHOLE_PASS_PREMATURE")

    require(errors, manifest.get("artifact") == CURRENT_PRODUCT and manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_MISMATCH")
    require(errors, manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, manifest.get("stage") == CURRENT_STAGE, "MANIFEST_STAGE_MISMATCH")
    require(errors, manifest.get("authority_correction") == current_authority, "MANIFEST_AUTHORITY_POINTER_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    mexec = manifest.get("execution_policy") or {}
    require(errors, mexec.get("free_only_default") is True and mexec.get("active_supervisor_free_only") is True, "MANIFEST_FREE_ONLY_MISSING")
    require(errors, mexec.get("isolated_sandbox_only") is True, "MANIFEST_ISOLATED_ONLY_MISSING")
    require(errors, mexec.get("vercel_hobby_bounded_included_tier_fixed_capsules") is True, "MANIFEST_FIXED_CAPSULE_ADMISSION_MISSING")
    require(errors, mexec.get("remaining_vercel_sandbox_quota_assumed") is False, "MANIFEST_QUOTA_ASSUMPTION_NOT_FORBIDDEN")
    require(errors, mexec.get("fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path") is True, "MANIFEST_COST_FAIL_CLOSED_FENCE_MISSING")
    require(errors, mexec.get("generic_caller_supplied_sandbox_command_credit") == "FORBIDDEN", "MANIFEST_GENERIC_SANDBOX_COMMAND_NOT_FORBIDDEN")
    require(errors, mexec.get("vps_testing_forbidden") is True and mexec.get("self_hosted_vps_test_runners_forbidden") is True and mexec.get("production_host_testing_forbidden") is True, "MANIFEST_HOST_EXECUTION_FENCE_WEAKENED")
    require(errors, mexec.get("together_general_inference_and_fallback_forbidden") is True, "MANIFEST_TOGETHER_FENCE_MISSING")
    require(errors, mexec.get("owner_paid_one_shot_08b_jspace_gwt_finetune_consumed") is False, "MANIFEST_ONE_SHOT_PREMATURELY_CONSUMED")
    manifest_training_fence = str(mexec.get("current_supervisor_together_training") or "")
    require(
        errors,
        manifest_training_fence.startswith("FORBIDDEN_BEFORE_")
        and "KEY_LOOKUP" in manifest_training_fence
        and "NETWORK_IO" in manifest_training_fence
        and "JOB_CREATION" in manifest_training_fence,
        "MANIFEST_TRAINING_FENCE_MISSING",
    )
    require(errors, mexec.get("paid_or_unknown_provider_admission_boundary") == PAID_BOUNDARY, "MANIFEST_PAID_ADMISSION_FENCE_MISSING")
    require(errors, mexec.get("other_paid_fallback") is False, "MANIFEST_OTHER_PAID_FALLBACK_WEAKENED")
    if current_version >= (8, 63):
        require(errors, mexec.get("go_unusual_experiment_atomic_lease_protocol") == "research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md", "MANIFEST_ATOMIC_LEASE_PROTOCOL_MISSING")
        require(errors, mexec.get("unusual_experiment_without_reproducible_claim") == "COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT", "MANIFEST_UNUSUAL_EXPERIMENT_FAIL_CLOSED_MISSING")
    mcredit = manifest.get("runtime_credit") or {}
    require(errors, mcredit.get("entityos_hcu_whole_runtime_credit") == 0, "MANIFEST_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("hcu_full_runtime_credit") == 0, "MANIFEST_HCU_FULL_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("jspace_model_runtime_credit") == 0, "MANIFEST_JSPACE_MODEL_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("training_credit") == 0, "MANIFEST_TRAINING_CREDIT_NONZERO")
    require(errors, mcredit.get("whole_product_pass") is False, "MANIFEST_WHOLE_PASS_PREMATURE")

    _validate_legacy_safety_ancestry(errors, paths, c41, c42, c43, c44)

    authority_name = Path(current_authority).name.upper()
    footer = paths["footer"].read_text(encoding="utf-8").upper()
    architecture = paths["architecture"].read_text(encoding="utf-8").upper()
    readme = paths["readme"].read_text(encoding="utf-8").upper()
    repo_claude = paths["repo_claude"].read_text(encoding="utf-8").upper()
    require(errors, "PROGRAM: ENTITYOS + HCU" in footer, "FOOTER_PROGRAM_MISMATCH")
    require(errors, authority_name in footer, "FOOTER_CURRENT_AUTHORITY_MISSING")
    require(errors, "ENTITYOS" in architecture[:2500] and "HCU" in architecture[:2500], "ARCHITECTURE_ENTITYOS_HCU_MISSING")
    require(errors, authority_name in readme[:5000], "README_CURRENT_AUTHORITY_MISSING")
    require(errors, "`PROGRAM=ENTITYOS_HCU`" in repo_claude[:6000], "ROOT_CLAUDE_PROGRAM_MISMATCH")
    require(errors, authority_name in repo_claude[:6000], "ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING")
    require(errors, "`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`" not in repo_claude[:6000], "ROOT_CLAUDE_STALE_CLAYVERSE_PROGRAM_ACTIVE")

    return {
        "schema": CURRENT_SCHEMA,
        "pass": not errors,
        "errors": errors,
        "current_authority": current_authority,
        "current_authority_version": version_string,
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
