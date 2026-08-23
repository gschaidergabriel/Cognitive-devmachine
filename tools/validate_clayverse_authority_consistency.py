#!/usr/bin/env python3
"""Current EntityOS/HCU authority guard under the historical compatibility filename.

The filename is intentionally retained because CI/receipts may still reference it. The
current product authority is EntityOS + HCU. Historical 4.1->4.4 controls are checked
only for inherited safety/provenance fences; their older product-selection metadata is
not current authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v1"
EXPECTED_PROGRAM = "ENTITYOS_HCU"
EXPECTED_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
EXPECTED_PRODUCT = "EntityOS"
EXPECTED_COMPUTE = "HCU"
STEERING852 = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"
CONTROL41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "steering852": root / STEERING852,
        "manifest": root / "the artefact/manifest.json",
        "architecture": root / "the artefact/ENTITYOS_HCU_ARCHITECTURE.md",
        "readme": root / "the artefact/README.md",
        "footer": root / "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
        "control41": root / CONTROL41,
        "control42": root / CONTROL42,
        "control43": root / CONTROL43,
        "control44": root / CONTROL44,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": SCHEMA, "pass": False, "errors": errors}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        steering = load_json(paths["steering852"])
        manifest = load_json(paths["manifest"])
        c41 = load_json(paths["control41"])
        c42 = load_json(paths["control42"])
        c43 = load_json(paths["control43"])
        c44 = load_json(paths["control44"])
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": SCHEMA, "pass": False, "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"]}

    # Persistent research identity is preserved while product authority changes.
    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    identity = bootstrap.get("identity") or {}
    require(errors, bootstrap.get("entity_display_name") == "Clay", "BOOTSTRAP_ENTITY_DISPLAY_MISMATCH")
    require(errors, identity.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_WORKER_IDENTITY_FENCE_MISSING")

    # Current owner/program/product authority.
    require(errors, bootstrap.get("active_program") == EXPECTED_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == EXPECTED_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == EXPECTED_PRODUCT, "BOOTSTRAP_PRODUCT_MISMATCH")
    require(errors, bootstrap.get("integrated_cognition_compute_architecture") == EXPECTED_COMPUTE, "BOOTSTRAP_COMPUTE_MISMATCH")
    require(errors, bootstrap.get("authority_correction") == STEERING852, "BOOTSTRAP_AUTHORITY_POINTER_MISMATCH")
    require(errors, bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_SANDBOX_ONLY", "BOOTSTRAP_EXECUTION_SURFACE_WEAKENED")
    require(errors, bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_FENCE_WEAKENED")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_WEAKENED")
    require(errors, bootstrap.get("final_paid_model_training") == "OWNER_AUTHORIZATION_REQUIRED", "BOOTSTRAP_TRAINING_GATE_WEAKENED")
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")
    tracks = set(bootstrap.get("go_required_tracks") or [])
    require(errors, "ENTITYOS_EXECUTABLE_CONVERGENCE" in tracks, "BOOTSTRAP_GO_TRACK_A_MISSING")
    require(errors, any(str(x).startswith("HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT") for x in tracks), "BOOTSTRAP_GO_TRACK_B_MISSING")

    compat = bootstrap.get("compatibility_names") or {}
    require(errors, compat.get("xeno") == "TRANSITIONAL_IMPLEMENTATION_COMPATIBILITY_CODENAME_ONLY", "BOOTSTRAP_XENO_NOT_COMPAT_ONLY")
    require(errors, compat.get("xcu") == "TRANSITIONAL_RESEARCH_ALIAS_FOR_HCU_ONLY", "BOOTSTRAP_XCU_NOT_ALIAS_ONLY")
    require(errors, "HISTORICAL" in str(compat.get("clayverse_frank", "")), "BOOTSTRAP_CLAYVERSE_FRANK_NOT_HISTORICAL")

    # Program-state agreement and fail-closed execution/effect law.
    require(errors, program.get("program_id") == "entityos-hcu", "PROGRAM_ID_MISMATCH")
    require(errors, program.get("status") == "ACTIVE", "PROGRAM_NOT_ACTIVE")
    require(errors, program.get("stage") == EXPECTED_STAGE and program.get("current_stage") == EXPECTED_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("product") == EXPECTED_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(errors, program.get("integrated_cognition_compute_architecture") == EXPECTED_COMPUTE, "PROGRAM_COMPUTE_MISMATCH")
    require(errors, program.get("authority_correction") == STEERING852, "PROGRAM_AUTHORITY_POINTER_MISMATCH")
    pexec = program.get("execution_policy") or {}
    require(errors, pexec.get("free_only") is True, "PROGRAM_FREE_ONLY_WEAKENED")
    require(errors, pexec.get("isolated_sandbox_only") is True, "PROGRAM_SANDBOX_ONLY_WEAKENED")
    require(errors, pexec.get("vps_testing_forbidden") is True, "PROGRAM_VPS_FENCE_WEAKENED")
    require(errors, pexec.get("self_hosted_vps_test_runners_forbidden") is True, "PROGRAM_SELFHOSTED_FENCE_WEAKENED")
    require(errors, pexec.get("production_host_testing_forbidden") is True, "PROGRAM_PRODUCTION_FENCE_WEAKENED")
    require(errors, pexec.get("together_forbidden") is True, "PROGRAM_TOGETHER_FENCE_WEAKENED")
    require(errors, pexec.get("paid_fallback") is False, "PROGRAM_PAID_FALLBACK_WEAKENED")
    require(errors, pexec.get("final_paid_or_model_training_requires_owner_authorization") is True, "PROGRAM_TRAINING_GATE_WEAKENED")
    pauth = program.get("authority") or {}
    require(errors, pauth.get("external_effects") == "EffectGate+EffectJournal", "PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    require(errors, pauth.get("second_persistent_identity") == "FORBIDDEN", "PROGRAM_SECOND_IDENTITY_NOT_FORBIDDEN")
    require(errors, pauth.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN", "PROGRAM_SECOND_AUTHORITY_NOT_FORBIDDEN")

    # Current steering must explicitly supersede old product work-selection authority.
    require(errors, steering.get("schema_version") == "8.52", "STEERING852_SCHEMA_MISMATCH")
    require(errors, steering.get("status") == "CURRENT_OWNER_AUTHORITY_CORRECTION", "STEERING852_STATUS_MISMATCH")
    require(errors, steering.get("program") == EXPECTED_PROGRAM, "STEERING852_PROGRAM_MISMATCH")
    require(errors, steering.get("product") == EXPECTED_PRODUCT, "STEERING852_PRODUCT_MISMATCH")
    require(errors, steering.get("integrated_cognition_compute_architecture") == EXPECTED_COMPUTE, "STEERING852_COMPUTE_MISMATCH")
    adjud = steering.get("adjudication") or {}
    require(errors, adjud.get("entityos") == "SOLE_CURRENT_PRODUCT_SYSTEM_IDENTITY", "STEERING852_ENTITYOS_NOT_SOLE_PRODUCT")
    require(errors, adjud.get("hcu") == "SOLE_CURRENT_INTEGRATED_COGNITION_COMPUTE_ARCHITECTURE", "STEERING852_HCU_NOT_SOLE_COMPUTE")
    require(errors, "HISTORICAL" in str(adjud.get("clayverse", "")), "STEERING852_CLAYVERSE_NOT_HISTORICAL")
    routing = set(steering.get("routing_law") or [])
    require(errors, "DO_NOT_CREATE_A_SECOND_IDENTITY_STATE_AUTHORITY_EFFECT_PATH_RECOVERY_LEDGER_OR_PRODUCT_TRACK" in routing, "STEERING852_SECOND_AUTHORITY_FENCE_MISSING")
    require(errors, "FREE_ONLY_REMAINS_FAIL_CLOSED_WITH_NO_PAID_FALLBACK" in routing, "STEERING852_FREE_ONLY_FENCE_MISSING")

    # Current artifact manifest and architecture. Old ClayVerse material is donor only.
    require(errors, manifest.get("schema_version") == "ENTITYOS_HCU_ARTIFACT_MANIFEST/v1", "MANIFEST_SCHEMA_MISMATCH")
    require(errors, manifest.get("artifact") == EXPECTED_PRODUCT and manifest.get("product_endpoint") == EXPECTED_PRODUCT, "MANIFEST_PRODUCT_MISMATCH")
    require(errors, manifest.get("integrated_cognition_compute_architecture") == EXPECTED_COMPUTE, "MANIFEST_COMPUTE_MISMATCH")
    require(errors, manifest.get("stage") == EXPECTED_STAGE, "MANIFEST_STAGE_MISMATCH")
    require(errors, manifest.get("current_authority") == STEERING852, "MANIFEST_AUTHORITY_POINTER_MISMATCH")
    require(errors, manifest.get("current_architecture") == "ENTITYOS_HCU_ARCHITECTURE.md", "MANIFEST_ARCHITECTURE_POINTER_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    mexec = manifest.get("execution_policy") or {}
    require(errors, mexec.get("authorized_isolated_sandbox_only") is True, "MANIFEST_SANDBOX_ONLY_WEAKENED")
    require(errors, mexec.get("vps_testing_forbidden") is True and mexec.get("self_hosted_vps_test_runners_forbidden") is True and mexec.get("production_host_testing_forbidden") is True, "MANIFEST_HOST_EXECUTION_FENCE_WEAKENED")
    require(errors, mexec.get("free_only") is True and mexec.get("together_forbidden") is True and mexec.get("paid_fallback") is False, "MANIFEST_FREE_ONLY_FENCE_WEAKENED")
    legacy = manifest.get("legacy_clayverse_material") or {}
    require(errors, "SUPERSEDED" in str(legacy.get("status", "")) and "HISTORICAL" in str(legacy.get("status", "")), "MANIFEST_CLAYVERSE_NOT_DONOR_ONLY")

    arch_text = paths["architecture"].read_text(encoding="utf-8")
    readme_text = paths["readme"].read_text(encoding="utf-8")
    footer_text = paths["footer"].read_text(encoding="utf-8")
    require(errors, "EntityOS" in arch_text and "HCU" in arch_text and "sole current product/system identity" in arch_text, "ARCHITECTURE_CURRENT_AUTHORITY_MISSING")
    require(errors, "EntityOS" in readme_text and "HCU" in readme_text, "README_CURRENT_AUTHORITY_MISSING")
    require(errors, "Program: EntityOS + HCU" in footer_text and f"Stage: {EXPECTED_STAGE}" in footer_text, "FOOTER_CURRENT_AUTHORITY_MISMATCH")

    # Inherited control ancestry is still checked for provenance/safety. Product-selection
    # fields inside 4.3/4.4 are historical and MUST NOT be used as current authority.
    require(errors, c42.get("base_control_blob_sha") == git_blob_sha(paths["control41"]), "CONTROL42_BASE_BLOB_MISMATCH")
    require(errors, c43.get("base_control_blob_sha") == git_blob_sha(paths["control41"]), "CONTROL43_BASE_BLOB_MISMATCH")
    require(errors, c43.get("execution_boundary_addendum_blob_sha") == git_blob_sha(paths["control42"]), "CONTROL43_EXEC_BLOB_MISMATCH")
    require(errors, c44.get("prior_program_authority_addendum_blob_sha") == git_blob_sha(paths["control43"]), "CONTROL44_PRIOR_BLOB_MISMATCH")

    require(errors, c41.get("mode") == "FREE_ONLY", "CONTROL41_FREE_ONLY_WEAKENED")
    c41cycle = c41.get("cycle_policy") or {}
    require(errors, c41cycle.get("paid_fallback") is False and c41cycle.get("automatic_subscription_upgrade") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(errors, c41cycle.get("vps_testing") == "FORBIDDEN" and c41cycle.get("self_hosted_vps_test_runners") == "FORBIDDEN" and c41cycle.get("production_host_testing") == "FORBIDDEN", "CONTROL41_HOST_EXECUTION_FENCE_WEAKENED")
    c41rules = set(c41.get("authority_rules") or [])
    require(errors, "model_output_is_candidate_not_truth" in c41rules, "CONTROL41_MODEL_TRUTH_FENCE_MISSING")
    require(errors, "autonomous_cycle_may_not_modify_FRANK_harness" in c41rules, "CONTROL41_HARNESS_FENCE_MISSING")

    c42routing = c42.get("execution_routing") or {}
    c42hard = c42.get("preserved_hard_rules") or {}
    require(errors, c42routing.get("direct_vps_host_candidate_execution") == "FORBIDDEN" and c42routing.get("persistent_self_hosted_candidate_execution") == "FORBIDDEN" and c42routing.get("production_host_testing") == "FORBIDDEN", "CONTROL42_HOST_EXECUTION_FENCE_WEAKENED")
    require(errors, c42hard.get("free_only") is True and c42hard.get("paid_fallback") is False and c42hard.get("together_forbidden") is True, "CONTROL42_FREE_ONLY_FENCE_WEAKENED")
    require(errors, c42hard.get("frank_harness_modification") == "FORBIDDEN", "CONTROL42_HARNESS_FENCE_MISSING")

    c43hard = c43.get("preserved_hard_rules") or {}
    require(errors, c43hard.get("free_only") is True and c43hard.get("paid_fallback") is False and c43hard.get("together_forbidden_under_current_control") is True, "CONTROL43_FREE_ONLY_FENCE_WEAKENED")
    require(errors, c43hard.get("model_output_is_candidate_not_truth") is True and c43hard.get("runtime_credit_requires_exact_admitted_execution") is True, "CONTROL43_EVIDENCE_FENCE_WEAKENED")
    require(errors, c43hard.get("frank_harness_modification") == "FORBIDDEN", "CONTROL43_HARNESS_FENCE_MISSING")

    c44hard = c44.get("preserved_hard_rules") or {}
    require(errors, c44hard.get("free_only") is True and c44hard.get("paid_fallback") is False and c44hard.get("together_forbidden") is True, "CONTROL44_FREE_ONLY_FENCE_WEAKENED")
    require(errors, c44hard.get("authorized_isolated_sandbox_only") is True and c44hard.get("vps_testing") is False and c44hard.get("self_hosted_vps_test_runners") is False and c44hard.get("production_host_testing") is False, "CONTROL44_EXECUTION_FENCE_WEAKENED")
    require(errors, c44hard.get("runtime_credit_requires_exact_admitted_isolated_execution") is True and c44hard.get("model_output_is_candidate_not_truth") is True, "CONTROL44_EVIDENCE_FENCE_WEAKENED")
    require(errors, c44hard.get("frank_harness_modification") == "FORBIDDEN", "CONTROL44_HARNESS_FENCE_MISSING")

    return {
        "schema": SCHEMA,
        "pass": not errors,
        "errors": errors,
        "current_program": EXPECTED_PROGRAM,
        "product": EXPECTED_PRODUCT,
        "compute_architecture": EXPECTED_COMPUTE,
        "historical_control_product_metadata_used_for_current_authority": False,
        "inherited_control_ancestry_checked": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    result = validate(Path(args.root).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
