#!/usr/bin/env python3
"""Compatibility-named fail-closed authority guard for current EntityOS + HCU.

The filename stays stable because workflows and receipts already address it.  Current
work/execution authority is autonomous supervisor 8.61 in FREE_ONLY mode.  The owner
paid one-shot training directive remains provenance but is quarantined by 8.61 and is
not executable permission for this organ.  Historical ClayVerse controls remain
hash-bound donor/safety ancestry, not current product authority.
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
TRAINING_PROVENANCE = "research_entity/claycode/OWNER_ONE_SHOT_08B_JSPACE_GWT_TRAINING_DIRECTIVE_2026-08-24.md"
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v2"

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


def _validate_legacy_safety_ancestry(errors, paths, c41, c42, c43, c44) -> None:
    """Preserve prior hard safety/provenance fences without reactivating old product authority."""
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
    hard42 = c42.get("preserved_hard_rules") or {}
    require(errors, hard42.get("free_only") is True and hard42.get("paid_fallback") is False, "CONTROL42_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard42.get("together_forbidden") is True, "CONTROL42_TOGETHER_FENCE_WEAKENED")
    routing42 = c42.get("execution_routing") or {}
    require(errors, routing42.get("direct_vps_host_candidate_execution") == "FORBIDDEN", "CONTROL42_DIRECT_VPS_FENCE_WEAKENED")
    require(errors, routing42.get("persistent_self_hosted_candidate_execution") == "FORBIDDEN", "CONTROL42_SELF_HOSTED_FENCE_WEAKENED")
    require(errors, routing42.get("production_host_testing") == "FORBIDDEN", "CONTROL42_PRODUCTION_TEST_FENCE_WEAKENED")

    require(errors, c43.get("schema_version") == "4.3-program-authority-addendum", "CONTROL43_VERSION_MISMATCH")
    require(errors, c43.get("base_control_blob_sha") == blob41, "CONTROL43_BASE_BLOB_MISMATCH")
    require(errors, c43.get("execution_boundary_addendum_path") == CONTROL42, "CONTROL43_EXEC_PATH_MISMATCH")
    require(errors, c43.get("execution_boundary_addendum_blob_sha") == blob42, "CONTROL43_EXEC_BLOB_MISMATCH")
    hard43 = c43.get("preserved_hard_rules") or {}
    require(errors, hard43.get("free_only") is True and hard43.get("paid_fallback") is False, "CONTROL43_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard43.get("together_forbidden_under_current_control") is True, "CONTROL43_TOGETHER_FENCE_WEAKENED")
    require(errors, hard43.get("runtime_credit_requires_exact_admitted_execution") is True, "CONTROL43_RUNTIME_EVIDENCE_WEAKENED")

    require(errors, c44.get("schema_version") == "4.4-clayverse-product-authority-addendum", "CONTROL44_VERSION_MISMATCH")
    require(errors, c44.get("prior_program_authority_addendum_path") == CONTROL43, "CONTROL44_PRIOR_PATH_MISMATCH")
    require(errors, c44.get("prior_program_authority_addendum_blob_sha") == blob43, "CONTROL44_PRIOR_BLOB_MISMATCH")
    require(errors, c44.get("effective_control_version") == LEGACY_EXPECTED_CONTROL, "CONTROL44_EFFECTIVE_VERSION_MISMATCH")
    override = c44.get("program_identity_override") or {}
    require(errors, override.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER" and override.get("target_stage") == "CLAYVERSE_ARTIFACT" and override.get("product_endpoint") == "ClayVerse", "CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH")
    hard44 = c44.get("preserved_hard_rules") or {}
    require(errors, hard44.get("free_only") is True and hard44.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, hard44.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, hard44.get("vps_testing") is False, "CONTROL44_VPS_TEST_WEAKENED")
    require(errors, hard44.get("runtime_credit_requires_exact_admitted_isolated_execution") is True, "CONTROL44_RUNTIME_EVIDENCE_WEAKENED")


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "supervisor861": root / CURRENT_AUTHORITY,
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
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": errors}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        supervisor = load_json(paths["supervisor861"])
        inbox = load_json(paths["inbox"])
        manifest = load_json(paths["manifest"])
        c41 = load_json(paths["control41"])
        c42 = load_json(paths["control42"])
        c43 = load_json(paths["control43"])
        c44 = load_json(paths["control44"])
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"]}

    identity = bootstrap.get("identity") or {}
    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    require(errors, identity.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_TEMP_WORKER_ROLE_MISMATCH")
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, bootstrap.get("authority_correction") == CURRENT_AUTHORITY, "BOOTSTRAP_AUTHORITY_POINTER_MISMATCH")
    require(errors, bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_FREE_SANDBOX_ONLY_IN_CURRENT_AUTONOMOUS_SUPERVISOR_MODE", "BOOTSTRAP_EXECUTION_FENCE_MISMATCH")
    require(errors, bootstrap.get("free_only") is True, "BOOTSTRAP_FREE_ONLY_MISSING")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_WEAKENED")
    require(errors, "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE" in str(bootstrap.get("together_api")), "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("together_training_authority_provenance") == TRAINING_PROVENANCE, "BOOTSTRAP_TRAINING_PROVENANCE_MISMATCH")
    require(errors, bootstrap.get("together_one_shot_training_consumed") is False, "BOOTSTRAP_ONE_SHOT_PREMATURELY_CONSUMED")
    require(errors, bootstrap.get("current_supervisor_together_training") == "FORBIDDEN_BEFORE_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION", "BOOTSTRAP_PAID_ADMISSION_FENCE_MISSING")
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")
    inv = set(str(x) for x in bootstrap.get("mandatory_invariants") or [])
    require(errors, "EntityOS is the sole current product/system identity" in inv, "BOOTSTRAP_ENTITYOS_INVARIANT_MISSING")
    require(errors, "HCU is the sole current integrated cognition/compute architecture" in inv, "BOOTSTRAP_HCU_INVARIANT_MISSING")
    require(errors, "FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT" in inv, "BOOTSTRAP_EPISTEMIC_FENCE_MISSING")

    require(errors, program.get("program_id") == "entityos-hcu" and program.get("status") == "ACTIVE", "PROGRAM_ID_OR_STATUS_MISMATCH")
    require(errors, program.get("stage") == CURRENT_STAGE and program.get("current_stage") == CURRENT_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("product") == CURRENT_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(errors, program.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, program.get("authority_correction") == CURRENT_AUTHORITY, "PROGRAM_AUTHORITY_POINTER_MISMATCH")
    pauth = program.get("authority") or {}
    require(errors, pauth.get("external_effects") == "EffectGate+EffectJournal", "PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    require(errors, pauth.get("second_persistent_identity") == "FORBIDDEN", "PROGRAM_SECOND_IDENTITY_NOT_FORBIDDEN")
    require(errors, pauth.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN", "PROGRAM_SECOND_AUTHORITY_NOT_FORBIDDEN")
    pexec = program.get("execution_policy") or {}
    require(errors, pexec.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(errors, pexec.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_ONLY_MISSING")
    require(errors, pexec.get("vps_testing_forbidden") is True and pexec.get("self_hosted_vps_test_runners_forbidden") is True and pexec.get("production_host_testing_forbidden") is True, "PROGRAM_HOST_EXECUTION_FENCE_WEAKENED")
    require(errors, pexec.get("together_general_inference_and_fallback_forbidden") is True, "PROGRAM_TOGETHER_INFERENCE_FENCE_MISSING")
    require(errors, pexec.get("owner_paid_one_shot_directive_present_as_provenance") is True, "PROGRAM_OWNER_TRAINING_PROVENANCE_MISSING")
    require(errors, pexec.get("owner_paid_one_shot_directive_file") == TRAINING_PROVENANCE, "PROGRAM_TRAINING_PROVENANCE_PATH_MISMATCH")
    require(errors, pexec.get("owner_paid_one_shot_job_consumed") is False, "PROGRAM_ONE_SHOT_PREMATURELY_CONSUMED")
    require(errors, pexec.get("current_supervisor_together_training_forbidden") is True, "PROGRAM_TOGETHER_TRAINING_FENCE_MISSING")
    require(errors, pexec.get("paid_or_unknown_provider_admission_boundary") == "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION", "PROGRAM_PAID_ADMISSION_FENCE_MISSING")
    require(errors, pexec.get("other_paid_fallback") is False, "PROGRAM_OTHER_PAID_FALLBACK_WEAKENED")
    tracks = program.get("go_required_tracks") or {}
    require(errors, tracks.get("track_a") == "ENTITYOS_EXECUTABLE_CONVERGENCE", "PROGRAM_GO_TRACK_A_MISMATCH")
    require(errors, tracks.get("track_b") == "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT", "PROGRAM_GO_TRACK_B_MISMATCH")
    require(errors, tracks.get("track_c") == "GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS", "PROGRAM_GO_TRACK_C_MISMATCH")
    credit = program.get("runtime_credit") or {}
    require(errors, credit.get("entityos_hcu_whole_runtime_credit") == 0, "PROGRAM_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("jspace_model_runtime_credit") == 0, "PROGRAM_JSPACE_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("training_credit") == 0, "PROGRAM_TRAINING_CREDIT_NONZERO")
    require(errors, credit.get("whole_product_pass") is False, "PROGRAM_WHOLE_PASS_PREMATURE")

    require(errors, supervisor.get("schema_version") == "8.61", "SUPERVISOR861_SCHEMA_MISMATCH")
    require(errors, supervisor.get("status") == "CURRENT_AUTONOMOUS_SUPERVISOR_STEERING", "SUPERVISOR861_STATUS_MISMATCH")
    require(errors, supervisor.get("program") == CURRENT_PROGRAM and supervisor.get("product") == CURRENT_PRODUCT, "SUPERVISOR861_PROGRAM_PRODUCT_MISMATCH")
    require(errors, supervisor.get("compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "SUPERVISOR861_COMPUTE_ARCHITECTURE_MISMATCH")
    free = supervisor.get("free_only") or {}
    require(errors, free.get("enabled") is True and free.get("no_paid_fallback") is True, "SUPERVISOR861_FREE_ONLY_WEAKENED")
    require(errors, free.get("together_training") == "FORBIDDEN_IN_THIS_SUPERVISOR_MODE", "SUPERVISOR861_TOGETHER_TRAINING_FENCE_MISSING")
    require(errors, free.get("together_general_inference") == "FORBIDDEN", "SUPERVISOR861_TOGETHER_INFERENCE_FENCE_MISSING")
    require(errors, free.get("paid_subscription_unknown_provider_execution") == "FAIL_CLOSED", "SUPERVISOR861_UNKNOWN_PAID_LANE_NOT_FAIL_CLOSED")
    evidence = supervisor.get("evidence") or {}
    require(errors, evidence.get("together_job_created") is False, "SUPERVISOR861_TOGETHER_JOB_PREMATURE")
    promotion = supervisor.get("promotion_state") or {}
    require(errors, promotion.get("entityos_whole_runtime_pass") is False, "SUPERVISOR861_WHOLE_PASS_PREMATURE")
    require(errors, promotion.get("training_credit") == 0, "SUPERVISOR861_TRAINING_CREDIT_NONZERO")

    require(errors, inbox.get("steering") == CURRENT_AUTHORITY, "INBOX_ACTIVE_SUPERVISOR_MISMATCH")
    inbox_free = inbox.get("free_only") or {}
    require(errors, inbox_free.get("enabled") is True and inbox_free.get("no_paid_fallback") is True, "INBOX_FREE_ONLY_WEAKENED")

    require(errors, manifest.get("artifact") == CURRENT_PRODUCT and manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, manifest.get("stage") == CURRENT_STAGE, "MANIFEST_STAGE_MISMATCH")
    require(errors, manifest.get("authority_correction") == CURRENT_AUTHORITY, "MANIFEST_AUTHORITY_POINTER_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    mexec = manifest.get("execution_policy") or {}
    require(errors, mexec.get("free_only") is True, "MANIFEST_FREE_ONLY_MISSING")
    require(errors, mexec.get("isolated_sandbox_only") is True, "MANIFEST_ISOLATED_ONLY_MISSING")
    require(errors, mexec.get("vps_testing_forbidden") is True and mexec.get("self_hosted_vps_test_runners_forbidden") is True and mexec.get("production_host_testing_forbidden") is True, "MANIFEST_HOST_EXECUTION_FENCE_WEAKENED")
    require(errors, mexec.get("together_general_inference_and_fallback_forbidden") is True, "MANIFEST_TOGETHER_INFERENCE_FENCE_MISSING")
    require(errors, mexec.get("owner_paid_one_shot_directive_present_as_provenance") is True, "MANIFEST_OWNER_TRAINING_PROVENANCE_MISSING")
    require(errors, mexec.get("owner_paid_one_shot_directive_file") == TRAINING_PROVENANCE, "MANIFEST_TRAINING_PROVENANCE_PATH_MISMATCH")
    require(errors, mexec.get("current_supervisor_together_training_forbidden") is True, "MANIFEST_TOGETHER_TRAINING_FENCE_MISSING")
    require(errors, mexec.get("paid_or_unknown_provider_admission_boundary") == "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION", "MANIFEST_PAID_ADMISSION_FENCE_MISSING")
    require(errors, mexec.get("other_paid_fallback") is False, "MANIFEST_OTHER_PAID_FALLBACK_WEAKENED")
    mcredit = manifest.get("runtime_credit") or {}
    require(errors, mcredit.get("entityos_hcu_whole_runtime_credit") == 0, "MANIFEST_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("jspace_model_runtime_credit") == 0, "MANIFEST_JSPACE_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("training_credit") == 0, "MANIFEST_TRAINING_CREDIT_NONZERO")
    require(errors, mcredit.get("whole_product_pass") is False, "MANIFEST_WHOLE_PASS_PREMATURE")

    _validate_legacy_safety_ancestry(errors, paths, c41, c42, c43, c44)

    footer = paths["footer"].read_text(encoding="utf-8").upper()
    architecture = paths["architecture"].read_text(encoding="utf-8").upper()
    readme = paths["readme"].read_text(encoding="utf-8").upper()
    repo_claude = paths["repo_claude"].read_text(encoding="utf-8").upper()
    require(errors, "PROGRAM: ENTITYOS + HCU" in footer, "FOOTER_PROGRAM_MISMATCH")
    require(errors, "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE" in footer, "FOOTER_FREE_ONLY_TOGETHER_FENCE_MISSING")
    require(errors, "ENTITYOS" in architecture[:2500] and "HCU" in architecture[:2500], "ARCHITECTURE_ENTITYOS_HCU_MISSING")
    require(errors, "CLAYVERSE IS THE PRODUCT ENDPOINT" not in architecture[:2500], "ARCHITECTURE_STALE_CLAYVERSE_PRODUCT_AUTHORITY")
    require(errors, "SUPERVISOR_STEERING_8_61.JSON" in readme[:4000], "README_ACTIVE_SUPERVISOR_MISSING")
    require(errors, "`PROGRAM=ENTITYOS_HCU`" in repo_claude[:6000], "ROOT_CLAUDE_PROGRAM_MISMATCH")
    require(errors, "SUPERVISOR_STEERING_8_61.JSON" in repo_claude[:6000], "ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING")
    require(errors, "FREE_ONLY" in repo_claude[:9000], "ROOT_CLAUDE_FREE_ONLY_FENCE_MISSING")
    require(errors, "`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`" not in repo_claude[:6000], "ROOT_CLAUDE_STALE_CLAYVERSE_PROGRAM_ACTIVE")

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
