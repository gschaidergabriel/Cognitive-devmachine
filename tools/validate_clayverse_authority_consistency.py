#!/usr/bin/env python3
"""Compatibility-named fail-closed authority guard for current EntityOS + HCU.

The filename is retained for workflow/receipt compatibility. Current work-selection
is EntityOS + HCU under the newest admitted supervisor. Historical ClayVerse 4.1-4.4
controls remain immutable safety/provenance ancestry only.
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
PAID_DIRECTIVE_PROVENANCE = "research_entity/claycode/OWNER_ONE_SHOT_08B_JSPACE_GWT_TRAINING_DIRECTIVE_2026-08-24.md"
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v2"
CONTROL41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
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


def _validate_legacy_safety_ancestry(errors: list[str], paths: dict[str, Path], c41: dict, c42: dict, c43: dict, c44: dict) -> None:
    """Keep inherited hard fences without reactivating historical product/provider authority."""
    require(errors, c41.get("schema_version") == "4.1" and c41.get("mode") == "FREE_ONLY", "CONTROL41_IDENTITY_MISMATCH")
    cycle41 = c41.get("cycle_policy") or {}
    require(errors, cycle41.get("paid_fallback") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(errors, cycle41.get("vps_testing") == "FORBIDDEN", "CONTROL41_VPS_TEST_WEAKENED")

    b41 = git_blob_sha(paths["control41"])
    b42 = git_blob_sha(paths["control42"])
    b43 = git_blob_sha(paths["control43"])
    require(errors, c42.get("base_control_path") == CONTROL41 and c42.get("base_control_blob_sha") == b41, "CONTROL42_BASE_BLOB_MISMATCH")
    h42 = c42.get("preserved_hard_rules") or {}
    require(errors, h42.get("free_only") is True and h42.get("paid_fallback") is False, "CONTROL42_FREE_ONLY_FENCE_WEAKENED")
    require(errors, h42.get("together_forbidden") is True, "CONTROL42_TOGETHER_FENCE_WEAKENED")
    r42 = c42.get("execution_routing") or {}
    require(errors, r42.get("direct_vps_host_candidate_execution") == "FORBIDDEN", "CONTROL42_DIRECT_VPS_FENCE_WEAKENED")
    require(errors, r42.get("persistent_self_hosted_candidate_execution") == "FORBIDDEN", "CONTROL42_SELF_HOSTED_FENCE_WEAKENED")
    require(errors, r42.get("production_host_testing") == "FORBIDDEN", "CONTROL42_PRODUCTION_TEST_FENCE_WEAKENED")

    require(errors, c43.get("base_control_blob_sha") == b41 and c43.get("execution_boundary_addendum_blob_sha") == b42, "CONTROL43_ANCESTRY_MISMATCH")
    h43 = c43.get("preserved_hard_rules") or {}
    require(errors, h43.get("free_only") is True and h43.get("paid_fallback") is False, "CONTROL43_FREE_ONLY_FENCE_WEAKENED")
    require(errors, h43.get("together_forbidden_under_current_control") is True, "CONTROL43_TOGETHER_FENCE_WEAKENED")
    require(errors, h43.get("runtime_credit_requires_exact_admitted_execution") is True, "CONTROL43_RUNTIME_EVIDENCE_WEAKENED")

    require(errors, c44.get("prior_program_authority_addendum_blob_sha") == b43, "CONTROL44_PRIOR_BLOB_MISMATCH")
    override = c44.get("program_identity_override") or {}
    require(errors, override.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER" and override.get("product_endpoint") == "ClayVerse", "CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH")
    h44 = c44.get("preserved_hard_rules") or {}
    require(errors, h44.get("free_only") is True and h44.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, h44.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, h44.get("runtime_credit_requires_exact_admitted_isolated_execution") is True, "CONTROL44_RUNTIME_EVIDENCE_WEAKENED")


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "steering861": root / CURRENT_AUTHORITY,
        "manifest": root / "the artefact/manifest.json",
        "footer": root / "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
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
        c41, c42, c43, c44 = (load_json(paths[x]) for x in ("control41", "control42", "control43", "control44"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"]}

    # Persistent identity + newest active program authority.
    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    identity = bootstrap.get("identity") or {}
    require(errors, identity.get("persistent_research_entity") == "Clay" and identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_IDENTITY_MISMATCH")
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, bootstrap.get("authority_correction") == CURRENT_AUTHORITY, "BOOTSTRAP_AUTHORITY_POINTER_MISMATCH")

    # FREE_ONLY successor contract must win over paid provenance before key/preflight/network/job creation.
    require(errors, bootstrap.get("free_only") is True, "BOOTSTRAP_FREE_ONLY_MISSING")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_WEAKENED")
    require(errors, bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_FREE_SANDBOX_ONLY_IN_CURRENT_AUTONOMOUS_SUPERVISOR_MODE", "BOOTSTRAP_EXECUTION_FENCE_MISSING")
    require(errors, "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE" in str(bootstrap.get("together_api")), "BOOTSTRAP_TOGETHER_FREE_ONLY_FENCE_MISSING")
    require(errors, bootstrap.get("together_one_shot_training_consumed") is False, "BOOTSTRAP_PAID_PROVENANCE_CONSUMPTION_MISMATCH")
    require(errors, bootstrap.get("current_supervisor_together_training") == "FORBIDDEN_BEFORE_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION", "BOOTSTRAP_TRAINING_PRENETWORK_FENCE_MISSING")

    require(errors, program.get("program_id") == "entityos-hcu" and program.get("status") == "ACTIVE", "PROGRAM_ID_OR_STATUS_MISMATCH")
    require(errors, program.get("authority_correction") == CURRENT_AUTHORITY, "PROGRAM_AUTHORITY_POINTER_MISMATCH")
    require(errors, program.get("stage") == CURRENT_STAGE and program.get("current_stage") == CURRENT_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("product") == CURRENT_PRODUCT and program.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROGRAM_PRODUCT_OR_COMPUTE_MISMATCH")
    pexec = program.get("execution_policy") or {}
    require(errors, pexec.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(errors, pexec.get("isolated_sandbox_only") is True and pexec.get("vps_testing_forbidden") is True and pexec.get("self_hosted_vps_test_runners_forbidden") is True and pexec.get("production_host_testing_forbidden") is True, "PROGRAM_EXECUTION_FENCE_MISSING")
    require(errors, pexec.get("together_general_inference_and_fallback_forbidden") is True and pexec.get("current_supervisor_together_training_forbidden") is True, "PROGRAM_TOGETHER_FREE_ONLY_FENCE_MISSING")
    require(errors, pexec.get("owner_paid_one_shot_directive_present_as_provenance") is True and pexec.get("owner_paid_one_shot_job_consumed") is False, "PROGRAM_PAID_DIRECTIVE_PROVENANCE_MISMATCH")
    require(errors, pexec.get("owner_paid_one_shot_directive_file") == PAID_DIRECTIVE_PROVENANCE, "PROGRAM_PAID_DIRECTIVE_PATH_MISMATCH")
    require(errors, pexec.get("paid_or_unknown_provider_admission_boundary") == "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION", "PROGRAM_PRENETWORK_PAID_FENCE_MISSING")
    require(errors, pexec.get("other_paid_fallback") is False, "PROGRAM_OTHER_PAID_FALLBACK_WEAKENED")
    tracks = program.get("go_required_tracks") or {}
    require(errors, tracks.get("track_a") == "ENTITYOS_EXECUTABLE_CONVERGENCE", "PROGRAM_GO_TRACK_A_MISMATCH")
    require(errors, tracks.get("track_b") == "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT", "PROGRAM_GO_TRACK_B_MISMATCH")
    require(errors, tracks.get("track_c") == "GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS", "PROGRAM_GO_TRACK_C_MISMATCH")
    training = program.get("training_program") or {}
    require(errors, training.get("owner_paid_one_shot_directive_status") == "QUARANTINED_FOR_CURRENT_FREE_ONLY_SUPERVISOR", "PROGRAM_PAID_DIRECTIVE_NOT_QUARANTINED")
    require(errors, training.get("paid_preflight_or_job_creation_allowed_now") is False, "PROGRAM_PAID_PREFLIGHT_NOT_FORBIDDEN")
    credit = program.get("runtime_credit") or {}
    require(errors, credit.get("entityos_hcu_whole_runtime_credit") == 0 and credit.get("jspace_model_runtime_credit") == 0 and credit.get("training_credit") == 0 and credit.get("whole_product_pass") is False, "PROGRAM_RUNTIME_CREDIT_PREMATURE")

    require(errors, steering.get("schema_version") == "8.61" and steering.get("status") == "CURRENT_AUTONOMOUS_SUPERVISOR_STEERING", "STEERING861_IDENTITY_MISMATCH")
    require(errors, steering.get("program") == CURRENT_PROGRAM and steering.get("product") == CURRENT_PRODUCT and steering.get("compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "STEERING861_PROGRAM_MISMATCH")
    free = steering.get("free_only") or {}
    require(errors, free.get("enabled") is True and free.get("no_paid_fallback") is True, "STEERING861_FREE_ONLY_WEAKENED")
    require(errors, free.get("together_training") == "FORBIDDEN_IN_THIS_SUPERVISOR_MODE" and free.get("together_general_inference") == "FORBIDDEN", "STEERING861_TOGETHER_FENCE_WEAKENED")
    require(errors, free.get("paid_subscription_unknown_provider_execution") == "FAIL_CLOSED", "STEERING861_UNKNOWN_PROVIDER_FENCE_WEAKENED")
    require(errors, "before credential/key lookup" in str(free.get("rule")), "STEERING861_PRENETWORK_FENCE_MISSING")
    promotion = steering.get("promotion_state") or {}
    require(errors, promotion.get("entityos_whole_runtime_pass") is False and promotion.get("hcu_runtime_credit_change") is False and promotion.get("canonical_semantics_promotion") is False and promotion.get("training_credit") == 0, "STEERING861_PREMATURE_PROMOTION")

    # Current artifact manifest must not lag the supervisor or re-enable the quarantined paid lane.
    require(errors, manifest.get("artifact") == CURRENT_PRODUCT and manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_MISMATCH")
    require(errors, manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE and manifest.get("stage") == CURRENT_STAGE, "MANIFEST_COMPUTE_OR_STAGE_MISMATCH")
    require(errors, manifest.get("authority_correction") == CURRENT_AUTHORITY, "MANIFEST_AUTHORITY_POINTER_MISMATCH")
    mexec = manifest.get("execution_policy") or {}
    require(errors, mexec.get("free_only") is True and mexec.get("isolated_sandbox_only") is True and mexec.get("vps_testing_forbidden") is True, "MANIFEST_FREE_ONLY_EXECUTION_FENCE_MISSING")
    require(errors, mexec.get("together_general_inference_and_fallback_forbidden") is True and mexec.get("current_supervisor_together_training_forbidden") is True, "MANIFEST_TOGETHER_FREE_ONLY_FENCE_MISSING")
    require(errors, mexec.get("owner_paid_one_shot_directive_present_as_provenance") is True and mexec.get("owner_paid_one_shot_job_consumed") is False, "MANIFEST_PAID_PROVENANCE_MISMATCH")
    require(errors, mexec.get("paid_or_unknown_provider_admission_boundary") == "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION", "MANIFEST_PRENETWORK_PAID_FENCE_MISSING")
    require(errors, mexec.get("other_paid_fallback") is False, "MANIFEST_OTHER_PAID_FALLBACK_WEAKENED")
    mcredit = manifest.get("runtime_credit") or {}
    require(errors, mcredit.get("entityos_hcu_whole_runtime_credit") == 0 and mcredit.get("jspace_model_runtime_credit") == 0 and mcredit.get("training_credit") == 0 and mcredit.get("whole_product_pass") is False, "MANIFEST_RUNTIME_CREDIT_PREMATURE")

    _validate_legacy_safety_ancestry(errors, paths, c41, c42, c43, c44)

    footer = paths["footer"].read_text(encoding="utf-8").upper()
    architecture = paths["architecture"].read_text(encoding="utf-8").upper()
    readme = paths["readme"].read_text(encoding="utf-8").upper()
    repo_claude = paths["repo_claude"].read_text(encoding="utf-8").upper()
    require(errors, "PROGRAM: ENTITYOS + HCU" in footer and "FREE_ONLY" in footer, "FOOTER_CURRENT_AUTHORITY_MISSING")
    require(errors, "ENTITYOS" in architecture[:2500] and "HCU" in architecture[:2500] and "CLAYVERSE IS THE PRODUCT ENDPOINT" not in architecture[:2500], "ARCHITECTURE_CURRENT_PRODUCT_MISMATCH")
    require(errors, "SUPERVISOR_STEERING_8_61.JSON" in readme[:3000] and "FREE_ONLY" in readme, "README_CURRENT_AUTHORITY_MISSING")
    require(errors, "SUPERVISOR_STEERING_8_61.JSON" in repo_claude[:5000], "ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING")
    require(errors, "TOGETHER" in repo_claude and "FREE_ONLY" in repo_claude and "PAID" in repo_claude, "ROOT_CLAUDE_FREE_ONLY_SCOPE_MISSING")

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
