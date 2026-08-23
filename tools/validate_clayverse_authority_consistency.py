#!/usr/bin/env python3
"""Compatibility-named fail-closed authority guard for current EntityOS + HCU.

The filename is retained because workflows/receipts may address it.  Current product
selection is EntityOS + HCU.  Historical ClayVerse 4.1->4.4 controls remain checked as
immutable donor/safety ancestry; their historical product choice is not current
work-selection authority.
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
CURRENT_AUTHORITY = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v1"

# Historical donor/safety ancestry.  These paths and bytes remain validated so the
# authority migration cannot silently weaken inherited free-only/execution/provenance
# fences.  Their ClayVerse product selection is historical, not current authority.
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


def _validate_legacy_safety_ancestry(
    errors: list[str],
    paths: dict[str, Path],
    control41: dict,
    control42: dict,
    control43: dict,
    control44: dict,
) -> None:
    """Preserve prior hard safety/provenance fences without reactivating old product authority."""
    require(errors, control41.get("schema_version") == "4.1", "CONTROL41_VERSION_MISMATCH")
    require(
        errors,
        control41.get("status") == "ACTIVE" and control41.get("mode") == "FREE_ONLY",
        "CONTROL41_FREE_ONLY_WEAKENED",
    )
    cycle41 = control41.get("cycle_policy") or {}
    require(errors, cycle41.get("paid_fallback") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(
        errors,
        cycle41.get("automatic_subscription_upgrade") is False,
        "CONTROL41_AUTO_UPGRADE_WEAKENED",
    )
    require(errors, cycle41.get("vps_testing") == "FORBIDDEN", "CONTROL41_VPS_TEST_WEAKENED")
    authority41 = control41.get("authority_rules") or []
    require(errors, "model_output_is_candidate_not_truth" in authority41, "CONTROL41_MODEL_TRUTH_FENCE_MISSING")
    require(
        errors,
        "autonomous_cycle_may_not_modify_FRANK_harness" in authority41,
        "CONTROL41_FRANK_HARNESS_FENCE_MISSING",
    )

    blob41 = git_blob_sha(paths["control41"])
    blob42 = git_blob_sha(paths["control42"])
    blob43 = git_blob_sha(paths["control43"])

    require(
        errors,
        control42.get("schema_version") == "4.2-execution-boundary-addendum",
        "CONTROL42_VERSION_MISMATCH",
    )
    require(
        errors,
        control42.get("status") == "ACTIVE" and control42.get("mode") == "FREE_ONLY",
        "CONTROL42_FREE_ONLY_WEAKENED",
    )
    require(errors, control42.get("base_control_path") == CONTROL41, "CONTROL42_BASE_PATH_MISMATCH")
    require(errors, control42.get("base_control_blob_sha") == blob41, "CONTROL42_BASE_BLOB_MISMATCH")
    hard42 = control42.get("preserved_hard_rules") or {}
    require(
        errors,
        hard42.get("free_only") is True and hard42.get("paid_fallback") is False,
        "CONTROL42_FREE_ONLY_FENCE_WEAKENED",
    )
    require(errors, hard42.get("together_forbidden") is True, "CONTROL42_TOGETHER_FENCE_WEAKENED")
    require(
        errors,
        hard42.get("frank_harness_modification") == "FORBIDDEN",
        "CONTROL42_FRANK_HARNESS_FENCE_WEAKENED",
    )
    routing42 = control42.get("execution_routing") or {}
    require(
        errors,
        routing42.get("direct_vps_host_candidate_execution") == "FORBIDDEN",
        "CONTROL42_DIRECT_VPS_FENCE_WEAKENED",
    )
    require(
        errors,
        routing42.get("persistent_self_hosted_candidate_execution") == "FORBIDDEN",
        "CONTROL42_SELF_HOSTED_FENCE_WEAKENED",
    )
    require(
        errors,
        routing42.get("production_host_testing") == "FORBIDDEN",
        "CONTROL42_PRODUCTION_TEST_FENCE_WEAKENED",
    )

    require(
        errors,
        control43.get("schema_version") == "4.3-program-authority-addendum",
        "CONTROL43_VERSION_MISMATCH",
    )
    require(
        errors,
        control43.get("status") == "ACTIVE" and control43.get("mode") == "FREE_ONLY",
        "CONTROL43_FREE_ONLY_WEAKENED",
    )
    require(errors, control43.get("base_control_path") == CONTROL41, "CONTROL43_BASE_PATH_MISMATCH")
    require(errors, control43.get("base_control_blob_sha") == blob41, "CONTROL43_BASE_BLOB_MISMATCH")
    require(
        errors,
        control43.get("execution_boundary_addendum_path") == CONTROL42,
        "CONTROL43_EXEC_PATH_MISMATCH",
    )
    require(
        errors,
        control43.get("execution_boundary_addendum_blob_sha") == blob42,
        "CONTROL43_EXEC_BLOB_MISMATCH",
    )
    hard43 = control43.get("preserved_hard_rules") or {}
    require(
        errors,
        hard43.get("free_only") is True and hard43.get("paid_fallback") is False,
        "CONTROL43_FREE_ONLY_FENCE_WEAKENED",
    )
    require(
        errors,
        hard43.get("together_forbidden_under_current_control") is True,
        "CONTROL43_TOGETHER_FENCE_WEAKENED",
    )
    require(
        errors,
        hard43.get("model_output_is_candidate_not_truth") is True,
        "CONTROL43_MODEL_TRUTH_FENCE_WEAKENED",
    )
    require(
        errors,
        hard43.get("runtime_credit_requires_exact_admitted_execution") is True,
        "CONTROL43_RUNTIME_EVIDENCE_WEAKENED",
    )
    require(
        errors,
        hard43.get("frank_harness_modification") == "FORBIDDEN",
        "CONTROL43_FRANK_HARNESS_FENCE_WEAKENED",
    )

    require(
        errors,
        control44.get("schema_version") == "4.4-clayverse-product-authority-addendum",
        "CONTROL44_VERSION_MISMATCH",
    )
    require(
        errors,
        control44.get("status") == "ACTIVE" and control44.get("mode") == "FREE_ONLY",
        "CONTROL44_NOT_ACTIVE_FREE_ONLY",
    )
    require(errors, control44.get("base_control_path") == CONTROL41, "CONTROL44_BASE_PATH_MISMATCH")
    require(
        errors,
        control44.get("execution_boundary_addendum_path") == CONTROL42,
        "CONTROL44_EXEC_PATH_MISMATCH",
    )
    require(
        errors,
        control44.get("prior_program_authority_addendum_path") == CONTROL43,
        "CONTROL44_PRIOR_PATH_MISMATCH",
    )
    require(
        errors,
        control44.get("prior_program_authority_addendum_blob_sha") == blob43,
        "CONTROL44_PRIOR_BLOB_MISMATCH",
    )
    require(
        errors,
        control44.get("composition_order")
        == [
            "4.1",
            "4.2-execution-boundary-addendum",
            "4.3-program-authority-addendum",
            "4.4-clayverse-product-authority-addendum",
        ],
        "CONTROL44_COMPOSITION_ORDER_MISMATCH",
    )
    require(
        errors,
        control44.get("effective_control_version") == LEGACY_EXPECTED_CONTROL,
        "CONTROL44_EFFECTIVE_VERSION_MISMATCH",
    )

    # Historical product identity is checked as provenance, never as current authority.
    override = control44.get("program_identity_override") or {}
    require(
        errors,
        override.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER"
        and override.get("target_stage") == "CLAYVERSE_ARTIFACT"
        and override.get("product_endpoint") == "ClayVerse",
        "CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH",
    )
    hard44 = control44.get("preserved_hard_rules") or {}
    require(
        errors,
        hard44.get("free_only") is True and hard44.get("paid_fallback") is False,
        "CONTROL44_FREE_ONLY_WEAKENED",
    )
    require(errors, hard44.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, hard44.get("vps_testing") is False, "CONTROL44_VPS_TEST_WEAKENED")
    require(
        errors,
        hard44.get("runtime_credit_requires_exact_admitted_isolated_execution") is True,
        "CONTROL44_RUNTIME_EVIDENCE_WEAKENED",
    )
    require(
        errors,
        hard44.get("model_output_is_candidate_not_truth") is True,
        "CONTROL44_MODEL_TRUTH_FENCE_WEAKENED",
    )
    require(
        errors,
        hard44.get("frank_harness_modification") == "FORBIDDEN",
        "CONTROL44_FRANK_HARNESS_FENCE_WEAKENED",
    )


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "steering852": root / CURRENT_AUTHORITY,
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
        steering852 = load_json(paths["steering852"])
        manifest = load_json(paths["manifest"])
        control41 = load_json(paths["control41"])
        control42 = load_json(paths["control42"])
        control43 = load_json(paths["control43"])
        control44 = load_json(paths["control44"])
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": CURRENT_SCHEMA,
            "pass": False,
            "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"],
        }

    # Persistent research-entity identity must survive product migrations.
    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    identity = bootstrap.get("identity") or {}
    require(errors, identity.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_TEMP_WORKER_ROLE_MISMATCH")

    # Current product/work-selection authority.
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(
        errors,
        bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE,
        "BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    require(errors, bootstrap.get("authority_correction") == CURRENT_AUTHORITY, "BOOTSTRAP_AUTHORITY_POINTER_MISMATCH")
    require(errors, bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_SANDBOX_ONLY", "BOOTSTRAP_EXECUTION_FENCE_MISSING")
    require(errors, bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_FENCE_MISSING")
    require(
        errors,
        bootstrap.get("final_paid_model_training") == "OWNER_AUTHORIZATION_REQUIRED",
        "BOOTSTRAP_PAID_TRAINING_GATE_MISSING",
    )
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")
    invariants = set(str(x) for x in bootstrap.get("mandatory_invariants") or [])
    require(errors, "EntityOS is the sole current product/system identity" in invariants, "BOOTSTRAP_ENTITYOS_INVARIANT_MISSING")
    require(errors, "HCU is the sole current integrated cognition/compute architecture" in invariants, "BOOTSTRAP_HCU_INVARIANT_MISSING")
    require(errors, "FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT" in invariants, "BOOTSTRAP_EPISTEMIC_FENCE_MISSING")

    require(errors, program.get("program_id") == "entityos-hcu", "PROGRAM_ID_MISMATCH")
    require(errors, program.get("status") == "ACTIVE", "PROGRAM_NOT_ACTIVE")
    require(
        errors,
        program.get("stage") == CURRENT_STAGE and program.get("current_stage") == CURRENT_STAGE,
        "PROGRAM_STAGE_MISMATCH",
    )
    require(errors, program.get("product") == CURRENT_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(
        errors,
        program.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE,
        "PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    pidentity = program.get("identity") or {}
    require(errors, pidentity.get("persistent_research_entity") == "Clay", "PROGRAM_PERSISTENT_ENTITY_MISMATCH")
    require(errors, pidentity.get("temporary_workers") == "ORGANS_NOT_ENTITIES", "PROGRAM_TEMP_WORKER_ROLE_MISMATCH")
    pauthority = program.get("authority") or {}
    require(errors, pauthority.get("external_effects") == "EffectGate+EffectJournal", "PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    require(errors, pauthority.get("second_persistent_identity") == "FORBIDDEN", "PROGRAM_SECOND_IDENTITY_NOT_FORBIDDEN")
    require(
        errors,
        pauthority.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN",
        "PROGRAM_SECOND_AUTHORITY_NOT_FORBIDDEN",
    )
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(errors, execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_ONLY_MISSING")
    require(errors, execution.get("vps_testing_forbidden") is True, "PROGRAM_VPS_TEST_FENCE_MISSING")
    require(errors, execution.get("self_hosted_vps_test_runners_forbidden") is True, "PROGRAM_SELF_HOSTED_FENCE_MISSING")
    require(errors, execution.get("production_host_testing_forbidden") is True, "PROGRAM_PRODUCTION_TEST_FENCE_MISSING")
    require(errors, execution.get("together_forbidden") is True, "PROGRAM_TOGETHER_FENCE_MISSING")
    require(errors, execution.get("paid_fallback") is False, "PROGRAM_PAID_FALLBACK_WEAKENED")
    tracks = program.get("go_required_tracks") or {}
    require(errors, tracks.get("track_a") == "ENTITYOS_EXECUTABLE_CONVERGENCE", "PROGRAM_GO_TRACK_A_MISMATCH")
    require(
        errors,
        tracks.get("track_b") == "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT",
        "PROGRAM_GO_TRACK_B_MISMATCH",
    )
    credit = program.get("runtime_credit") or {}
    require(errors, credit.get("entityos_hcu_whole_runtime_credit") == 0, "PROGRAM_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("whole_product_pass") is False, "PROGRAM_WHOLE_PASS_PREMATURE")

    require(errors, steering852.get("schema_version") == "8.52", "STEERING852_SCHEMA_MISMATCH")
    require(
        errors,
        steering852.get("status") == "CURRENT_OWNER_AUTHORITY_CORRECTION",
        "STEERING852_STATUS_MISMATCH",
    )
    require(errors, steering852.get("program") == CURRENT_PROGRAM, "STEERING852_PROGRAM_MISMATCH")
    require(errors, steering852.get("product") == CURRENT_PRODUCT, "STEERING852_PRODUCT_MISMATCH")
    require(
        errors,
        steering852.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE,
        "STEERING852_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    adjudication = steering852.get("adjudication") or {}
    require(errors, adjudication.get("entityos") == "SOLE_CURRENT_PRODUCT_SYSTEM_IDENTITY", "STEERING852_ENTITYOS_AUTHORITY_MISMATCH")
    require(errors, adjudication.get("hcu") == "SOLE_CURRENT_INTEGRATED_COGNITION_COMPUTE_ARCHITECTURE", "STEERING852_HCU_AUTHORITY_MISMATCH")
    require(errors, adjudication.get("clayverse") == "HISTORICAL_DONOR_PROVENANCE_ONLY", "STEERING852_CLAYVERSE_NOT_DONOR")
    routing = set(str(x) for x in steering852.get("routing_law") or [])
    require(errors, "FREE_ONLY_REMAINS_FAIL_CLOSED_WITH_NO_PAID_FALLBACK" in routing, "STEERING852_FREE_ONLY_FENCE_MISSING")
    require(errors, "EXECUTABLE_EVIDENCE_OUTRANKS_MODEL_CONSENSUS" in routing, "STEERING852_EVIDENCE_FENCE_MISSING")
    sruntime = steering852.get("current_runtime_evidence") or {}
    require(errors, sruntime.get("entityos_hcu_whole_runtime_credit") == 0, "STEERING852_RUNTIME_CREDIT_NONZERO")
    require(errors, sruntime.get("whole_product_pass") is False, "STEERING852_WHOLE_PASS_PREMATURE")

    require(errors, manifest.get("artifact") == CURRENT_PRODUCT, "MANIFEST_ARTIFACT_MISMATCH")
    require(errors, manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_ENDPOINT_MISMATCH")
    require(
        errors,
        manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE,
        "MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    require(errors, manifest.get("stage") == CURRENT_STAGE, "MANIFEST_STAGE_MISMATCH")
    require(errors, manifest.get("canonical_workspace") == "the artefact/", "MANIFEST_WORKSPACE_MISMATCH")
    require(errors, manifest.get("authority_correction") == CURRENT_AUTHORITY, "MANIFEST_AUTHORITY_POINTER_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    mexec = manifest.get("execution_policy") or {}
    require(errors, mexec.get("free_only") is True, "MANIFEST_FREE_ONLY_MISSING")
    require(errors, mexec.get("isolated_sandbox_only") is True, "MANIFEST_ISOLATED_ONLY_MISSING")
    require(errors, mexec.get("vps_testing_forbidden") is True, "MANIFEST_VPS_TEST_FENCE_MISSING")
    require(errors, mexec.get("together_forbidden") is True, "MANIFEST_TOGETHER_FENCE_MISSING")
    require(errors, mexec.get("paid_fallback") is False, "MANIFEST_PAID_FALLBACK_WEAKENED")
    mcredit = manifest.get("runtime_credit") or {}
    require(errors, mcredit.get("entityos_hcu_whole_runtime_credit") == 0, "MANIFEST_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("whole_product_pass") is False, "MANIFEST_WHOLE_PASS_PREMATURE")
    donor = manifest.get("legacy_donor") or {}
    require(errors, donor.get("prior_product") == "ClayVerse", "MANIFEST_DONOR_PRODUCT_MISSING")
    require(errors, donor.get("scope") == "HISTORICAL_DONOR_PROVENANCE_ONLY", "MANIFEST_DONOR_SCOPE_MISMATCH")

    _validate_legacy_safety_ancestry(errors, paths, control41, control42, control43, control44)

    footer = paths["footer"].read_text(encoding="utf-8").upper()
    architecture = paths["architecture"].read_text(encoding="utf-8").upper()
    readme = paths["readme"].read_text(encoding="utf-8").upper()
    repo_claude = paths["repo_claude"].read_text(encoding="utf-8").upper()

    require(errors, "PROGRAM: ENTITYOS + HCU" in footer, "FOOTER_PROGRAM_MISMATCH")
    require(errors, "STAGE: ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP" in footer, "FOOTER_STAGE_MISMATCH")
    require(errors, "PRODUCT: ENTITYOS" in footer, "FOOTER_PRODUCT_MISMATCH")
    require(errors, "COMPUTE ARCHITECTURE: HCU" in footer, "FOOTER_COMPUTE_ARCHITECTURE_MISMATCH")

    require(errors, "ENTITYOS" in architecture[:2500], "ARCHITECTURE_ENTITYOS_MISSING")
    require(errors, "HCU" in architecture[:2500], "ARCHITECTURE_HCU_MISSING")
    require(
        errors,
        "CLAYVERSE IS THE PRODUCT ENDPOINT" not in architecture[:2500],
        "ARCHITECTURE_STALE_CLAYVERSE_PRODUCT_AUTHORITY",
    )
    require(errors, "ENTITYOS" in readme[:2500] and "HCU" in readme[:2500], "README_ENTITYOS_HCU_MISSING")

    require(errors, "`PROGRAM=ENTITYOS_HCU`" in repo_claude[:5000], "ROOT_CLAUDE_PROGRAM_MISMATCH")
    require(
        errors,
        "`STAGE=ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP`" in repo_claude[:5000],
        "ROOT_CLAUDE_STAGE_MISMATCH",
    )
    require(errors, "`PRODUCT=ENTITYOS`" in repo_claude[:5000], "ROOT_CLAUDE_PRODUCT_MISMATCH")
    require(errors, "`COMPUTE_ARCHITECTURE=HCU`" in repo_claude[:5000], "ROOT_CLAUDE_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, "SUPERVISOR_STEERING_8_52.JSON" in repo_claude[:5000], "ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING")
    require(
        errors,
        "`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`" not in repo_claude[:5000],
        "ROOT_CLAUDE_STALE_CLAYVERSE_PROGRAM_ACTIVE",
    )

    return {
        "schema": CURRENT_SCHEMA,
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
