#!/usr/bin/env python3
"""Fail closed on current EntityOS/HCU authority or inherited safety drift.

The filename is retained as a compatibility entry point because workflows and receipts
already reference it. Its *current* authority is EntityOS + HCU. Historical ClayVerse
control files are checked only for safety/provenance fences; they cannot select the
current product or compute architecture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v1"
EXPECTED_PROGRAM = "ENTITYOS_HCU"
EXPECTED_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
EXPECTED_PRODUCT = "EntityOS"
EXPECTED_COMPUTE = "HCU"
EXPECTED_REPO = "gschaidergabriel/clay-global-research-entity"
EXPECTED_WORKSPACE = "the artefact/"
EXPECTED_ENTRY_TRACK = "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT"
EXPECTED_GO_TRACK = "ENTITYOS_EXECUTABLE_CONVERGENCE"
STEERING852 = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"
WORKER_DIRECTIVE = "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
CONTROL41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
LEGACY_MANIFEST_BLOB = "fe6a601efdbe350a7b34816c4ffceb182df5cab8"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        value = json.load(fh)
    if not isinstance(value, dict):
        raise ValueError(f"OBJECT_REQUIRED:{path.as_posix()}")
    return value


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def _contains_all(text: str, values: tuple[str, ...]) -> bool:
    return all(value in text for value in values)


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "steering852": root / STEERING852,
        "worker_directive": root / WORKER_DIRECTIVE,
        "footer": root / "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
        "manifest": root / "the artefact/manifest.json",
        "readme": root / "the artefact/README.md",
        "root_claude": root / "CLAUDE.md",
        "control41": root / CONTROL41,
        "control42": root / CONTROL42,
        "control43": root / CONTROL43,
        "control44": root / CONTROL44,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": SCHEMA, "pass": False, "errors": errors, "credit": "ZERO_RUNTIME_CREDIT"}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        steering = load_json(paths["steering852"])
        manifest = load_json(paths["manifest"])
        control41 = load_json(paths["control41"])
        control42 = load_json(paths["control42"])
        control43 = load_json(paths["control43"])
        control44 = load_json(paths["control44"])
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "schema": SCHEMA,
            "pass": False,
            "errors": [f"LOAD_ERROR:{type(exc).__name__}:{exc}"],
            "credit": "ZERO_RUNTIME_CREDIT",
        }

    worker_directive = paths["worker_directive"].read_text(encoding="utf-8")
    footer = paths["footer"].read_text(encoding="utf-8")
    readme = paths["readme"].read_text(encoding="utf-8")
    root_claude = paths["root_claude"].read_text(encoding="utf-8")

    # Persistent research-entity identity remains the same while product authority changes.
    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    require(errors, bootstrap.get("entity_display_name") == "Clay", "BOOTSTRAP_ENTITY_DISPLAY_MISMATCH")
    identity = bootstrap.get("identity") or {}
    require(errors, identity.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_TEMP_WORKER_IDENTITY_MISMATCH")

    # Current owner/work-selection authority.
    require(errors, bootstrap.get("active_program") == EXPECTED_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == EXPECTED_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == EXPECTED_PRODUCT, "BOOTSTRAP_PRODUCT_MISMATCH")
    require(
        errors,
        bootstrap.get("integrated_cognition_compute_architecture") == EXPECTED_COMPUTE,
        "BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    require(errors, bootstrap.get("authority_correction") == STEERING852, "BOOTSTRAP_STEERING_POINTER_MISMATCH")
    require(errors, bootstrap.get("canonical_repository") == EXPECTED_REPO, "BOOTSTRAP_REPOSITORY_MISMATCH")
    require(errors, bootstrap.get("canonical_branch") == "main", "BOOTSTRAP_BRANCH_MISMATCH")
    require(errors, bootstrap.get("canonical_workspace") == EXPECTED_WORKSPACE, "BOOTSTRAP_WORKSPACE_MISMATCH")
    require(errors, bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_SANDBOX_ONLY", "BOOTSTRAP_EXECUTION_BOUNDARY_WEAKENED")
    require(errors, bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_FENCE_WEAKENED")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_WEAKENED")
    require(
        errors,
        bootstrap.get("final_paid_model_training") == "OWNER_AUTHORIZATION_REQUIRED",
        "BOOTSTRAP_FINAL_TRAINING_GATE_WEAKENED",
    )
    tracks = tuple(bootstrap.get("go_required_tracks") or ())
    require(errors, EXPECTED_GO_TRACK in tracks, "BOOTSTRAP_GO_TRACK_A_MISSING")
    require(
        errors,
        "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT_OR_HCU_NO_CHANGE_WITH_REASON" in tracks,
        "BOOTSTRAP_GO_TRACK_B_MISSING",
    )
    compat = bootstrap.get("compatibility_names") or {}
    require(
        errors,
        compat.get("xeno") == "TRANSITIONAL_IMPLEMENTATION_COMPATIBILITY_CODENAME_ONLY",
        "BOOTSTRAP_XENO_COMPATIBILITY_MISMATCH",
    )
    require(
        errors,
        compat.get("xcu") == "TRANSITIONAL_RESEARCH_ALIAS_FOR_HCU_ONLY",
        "BOOTSTRAP_XCU_COMPATIBILITY_MISMATCH",
    )
    require(
        errors,
        compat.get("clayverse_frank") == "HISTORICAL_DONOR_PROVENANCE_ONLY",
        "BOOTSTRAP_CLAYVERSE_FRANK_COMPATIBILITY_MISMATCH",
    )

    # Program state must independently resolve to the same current product/compute authority.
    require(errors, program.get("program_id") == "entityos-hcu", "PROGRAM_ID_MISMATCH")
    require(errors, program.get("stage") == EXPECTED_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("current_stage") == EXPECTED_STAGE, "PROGRAM_CURRENT_STAGE_MISMATCH")
    require(errors, program.get("product") == EXPECTED_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(
        errors,
        program.get("integrated_cognition_compute_architecture") == EXPECTED_COMPUTE,
        "PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    require(errors, program.get("canonical_repository") == EXPECTED_REPO, "PROGRAM_REPOSITORY_MISMATCH")
    require(errors, program.get("canonical_branch") == "main", "PROGRAM_BRANCH_MISMATCH")
    require(errors, program.get("canonical_workspace") == EXPECTED_WORKSPACE, "PROGRAM_WORKSPACE_MISMATCH")
    go_tracks = program.get("go_required_tracks") or {}
    require(errors, go_tracks.get("track_a") == EXPECTED_GO_TRACK, "PROGRAM_GO_TRACK_A_MISMATCH")
    require(errors, go_tracks.get("track_b") == EXPECTED_ENTRY_TRACK, "PROGRAM_GO_TRACK_B_MISMATCH")
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_WEAKENED")
    require(errors, execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_ONLY_WEAKENED")
    require(errors, execution.get("vps_testing_forbidden") is True, "PROGRAM_VPS_FENCE_WEAKENED")
    require(errors, execution.get("self_hosted_vps_test_runners_forbidden") is True, "PROGRAM_SELFHOSTED_FENCE_WEAKENED")
    require(errors, execution.get("production_host_testing_forbidden") is True, "PROGRAM_PRODUCTION_FENCE_WEAKENED")
    require(errors, execution.get("together_forbidden") is True, "PROGRAM_TOGETHER_FENCE_WEAKENED")
    require(errors, execution.get("paid_fallback") is False, "PROGRAM_PAID_FALLBACK_WEAKENED")

    # Newest explicit owner correction must be the current authority, not a donor alias.
    require(errors, steering.get("schema_version") == "8.52", "STEERING852_SCHEMA_MISMATCH")
    require(errors, steering.get("status") == "CURRENT_OWNER_AUTHORITY_CORRECTION", "STEERING852_STATUS_MISMATCH")
    require(errors, steering.get("program") == EXPECTED_PROGRAM, "STEERING852_PROGRAM_MISMATCH")
    require(errors, steering.get("product") == EXPECTED_PRODUCT, "STEERING852_PRODUCT_MISMATCH")
    require(
        errors,
        steering.get("integrated_cognition_compute_architecture") == EXPECTED_COMPUTE,
        "STEERING852_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    adjudication = steering.get("adjudication") or {}
    require(errors, adjudication.get("entityos") == "SOLE_CURRENT_PRODUCT_SYSTEM_IDENTITY", "STEERING852_ENTITYOS_AUTHORITY_MISMATCH")
    require(
        errors,
        adjudication.get("hcu") == "SOLE_CURRENT_INTEGRATED_COGNITION_COMPUTE_ARCHITECTURE",
        "STEERING852_HCU_AUTHORITY_MISMATCH",
    )
    require(
        errors,
        adjudication.get("clayverse") == "HISTORICAL_DONOR_PROVENANCE_ONLY",
        "STEERING852_CLAYVERSE_NOT_HISTORICAL",
    )

    # Current artifact manifest. Historical ClayVerse manifest bytes are provenance only.
    require(errors, manifest.get("schema_version") == "ENTITYOS_HCU_MANIFEST/v1", "MANIFEST_SCHEMA_MISMATCH")
    require(errors, manifest.get("artifact") == EXPECTED_PRODUCT, "MANIFEST_ARTIFACT_MISMATCH")
    require(errors, manifest.get("product_endpoint") == EXPECTED_PRODUCT, "MANIFEST_PRODUCT_MISMATCH")
    require(errors, manifest.get("program") == EXPECTED_PROGRAM, "MANIFEST_PROGRAM_MISMATCH")
    require(errors, manifest.get("stage") == EXPECTED_STAGE, "MANIFEST_STAGE_MISMATCH")
    require(
        errors,
        manifest.get("integrated_cognition_compute_architecture") == EXPECTED_COMPUTE,
        "MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    require(errors, manifest.get("canonical_repository") == EXPECTED_REPO, "MANIFEST_REPOSITORY_MISMATCH")
    require(errors, manifest.get("canonical_branch") == "main", "MANIFEST_BRANCH_MISMATCH")
    require(errors, manifest.get("canonical_workspace") == EXPECTED_WORKSPACE, "MANIFEST_WORKSPACE_MISMATCH")
    manifest_authority = manifest.get("authority") or {}
    require(
        errors,
        manifest_authority.get("external_effects") == "EffectGate+EffectJournal",
        "MANIFEST_EFFECT_AUTHORITY_MISMATCH",
    )
    require(
        errors,
        manifest_authority.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN",
        "MANIFEST_SECOND_AUTHORITY_FENCE_MISSING",
    )
    manifest_exec = manifest.get("execution_policy") or {}
    require(errors, manifest_exec.get("free_only") is True, "MANIFEST_FREE_ONLY_WEAKENED")
    require(
        errors,
        manifest_exec.get("authorized_isolated_sandbox_only_for_current_runtime_credit") is True,
        "MANIFEST_ISOLATED_EXECUTION_FENCE_WEAKENED",
    )
    require(errors, manifest_exec.get("vps_testing_forbidden") is True, "MANIFEST_VPS_FENCE_WEAKENED")
    require(errors, manifest_exec.get("self_hosted_vps_test_runners_forbidden") is True, "MANIFEST_SELFHOSTED_FENCE_WEAKENED")
    require(errors, manifest_exec.get("production_host_testing_forbidden") is True, "MANIFEST_PRODUCTION_FENCE_WEAKENED")
    require(errors, manifest_exec.get("together_forbidden") is True, "MANIFEST_TOGETHER_FENCE_WEAKENED")
    require(errors, manifest_exec.get("paid_fallback") is False, "MANIFEST_PAID_FALLBACK_WEAKENED")
    legacy_manifest = manifest.get("legacy_manifest_provenance") or {}
    require(
        errors,
        legacy_manifest.get("prior_manifest_git_blob_sha1") == LEGACY_MANIFEST_BLOB,
        "MANIFEST_LEGACY_BLOB_PROVENANCE_MISMATCH",
    )
    require(
        errors,
        legacy_manifest.get("classification") == "HISTORICAL_DONOR_PROVENANCE_ONLY",
        "MANIFEST_LEGACY_CLAYVERSE_AUTHORITY_NOT_RETIRED",
    )
    acceptance = manifest.get("acceptance") or {}
    require(errors, acceptance.get("entityos_hcu_whole_runtime_credit") == 0, "MANIFEST_RUNTIME_CREDIT_NONZERO")
    require(errors, acceptance.get("whole_product_pass") is False, "MANIFEST_WHOLE_PRODUCT_PASS_UNJUSTIFIED")

    # Human/worker-facing routing shims must not silently re-select the historical product.
    require(
        errors,
        _contains_all(root_claude, ("PROGRAM=ENTITYOS_HCU", "PRODUCT=EntityOS", "COMPUTE_ARCHITECTURE=HCU")),
        "ROOT_CLAUDE_CURRENT_AUTHORITY_MISMATCH",
    )
    require(errors, "ClayVerse and Frank = historical donor/provenance only" in root_claude, "ROOT_CLAUDE_LEGACY_SCOPE_MISSING")
    require(
        errors,
        _contains_all(readme, ("EntityOS + HCU cognitive computer", "**EntityOS** = sole current product/system identity", "**HCU** = sole current integrated cognition/compute architecture")),
        "ARTEFACT_README_CURRENT_AUTHORITY_MISMATCH",
    )
    require(
        errors,
        _contains_all(worker_directive, ("Current product/system: **EntityOS**", "Current integrated cognition/compute architecture: **HCU**", EXPECTED_GO_TRACK, EXPECTED_ENTRY_TRACK)),
        "WORKER_DIRECTIVE_CURRENT_AUTHORITY_MISMATCH",
    )
    require(errors, "Program: EntityOS + HCU" in footer, "FOOTER_PROGRAM_MISMATCH")
    require(errors, "Stage: ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP" in footer, "FOOTER_STAGE_MISMATCH")
    require(errors, "Product: EntityOS" in footer, "FOOTER_PRODUCT_MISMATCH")
    require(errors, "Compute architecture: HCU" in footer, "FOOTER_COMPUTE_MISMATCH")

    # Preserve inherited safety/provenance controls without allowing old product labels to
    # override current 8.52 authority. The byte ancestry remains fail-closed.
    blob41 = git_blob_sha(paths["control41"])
    blob42 = git_blob_sha(paths["control42"])
    blob43 = git_blob_sha(paths["control43"])

    require(errors, control41.get("schema_version") == "4.1", "CONTROL41_VERSION_MISMATCH")
    require(errors, control41.get("status") == "ACTIVE", "CONTROL41_STATUS_MISMATCH")
    require(errors, control41.get("mode") == "FREE_ONLY", "CONTROL41_FREE_ONLY_WEAKENED")
    cycle41 = control41.get("cycle_policy") or {}
    require(errors, cycle41.get("paid_fallback") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(errors, cycle41.get("automatic_subscription_upgrade") is False, "CONTROL41_AUTO_UPGRADE_WEAKENED")
    require(errors, cycle41.get("vps_testing") == "FORBIDDEN", "CONTROL41_VPS_FENCE_WEAKENED")
    authority41 = set(control41.get("authority_rules") or ())
    require(errors, "model_output_is_candidate_not_truth" in authority41, "CONTROL41_MODEL_TRUTH_FENCE_MISSING")

    require(errors, control42.get("schema_version") == "4.2-execution-boundary-addendum", "CONTROL42_VERSION_MISMATCH")
    require(errors, control42.get("base_control_path") == CONTROL41, "CONTROL42_BASE_PATH_MISMATCH")
    require(errors, control42.get("base_control_blob_sha") == blob41, "CONTROL42_BASE_BLOB_MISMATCH")
    hard42 = control42.get("preserved_hard_rules") or {}
    require(errors, hard42.get("free_only") is True and hard42.get("paid_fallback") is False, "CONTROL42_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard42.get("together_forbidden") is True, "CONTROL42_TOGETHER_FENCE_WEAKENED")
    routing42 = control42.get("execution_routing") or {}
    require(errors, routing42.get("direct_vps_host_candidate_execution") == "FORBIDDEN", "CONTROL42_DIRECT_VPS_FENCE_WEAKENED")
    require(errors, routing42.get("persistent_self_hosted_candidate_execution") == "FORBIDDEN", "CONTROL42_SELFHOSTED_FENCE_WEAKENED")
    require(errors, routing42.get("production_host_testing") == "FORBIDDEN", "CONTROL42_PRODUCTION_FENCE_WEAKENED")

    require(errors, control43.get("schema_version") == "4.3-program-authority-addendum", "CONTROL43_VERSION_MISMATCH")
    require(errors, control43.get("base_control_path") == CONTROL41, "CONTROL43_BASE_PATH_MISMATCH")
    require(errors, control43.get("base_control_blob_sha") == blob41, "CONTROL43_BASE_BLOB_MISMATCH")
    require(errors, control43.get("execution_boundary_addendum_path") == CONTROL42, "CONTROL43_EXEC_PATH_MISMATCH")
    require(errors, control43.get("execution_boundary_addendum_blob_sha") == blob42, "CONTROL43_EXEC_BLOB_MISMATCH")
    hard43 = control43.get("preserved_hard_rules") or {}
    require(errors, hard43.get("free_only") is True and hard43.get("paid_fallback") is False, "CONTROL43_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard43.get("together_forbidden_under_current_control") is True, "CONTROL43_TOGETHER_FENCE_WEAKENED")
    require(errors, hard43.get("model_output_is_candidate_not_truth") is True, "CONTROL43_MODEL_TRUTH_FENCE_WEAKENED")
    require(errors, hard43.get("runtime_credit_requires_exact_admitted_execution") is True, "CONTROL43_RUNTIME_EVIDENCE_FENCE_WEAKENED")

    require(errors, control44.get("schema_version") == "4.4-clayverse-product-authority-addendum", "CONTROL44_VERSION_MISMATCH")
    require(errors, control44.get("prior_program_authority_addendum_path") == CONTROL43, "CONTROL44_PRIOR_PATH_MISMATCH")
    require(errors, control44.get("prior_program_authority_addendum_blob_sha") == blob43, "CONTROL44_PRIOR_BLOB_MISMATCH")
    hard44 = control44.get("preserved_hard_rules") or {}
    require(errors, hard44.get("free_only") is True and hard44.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard44.get("together_forbidden") is True, "CONTROL44_TOGETHER_FENCE_WEAKENED")
    require(errors, hard44.get("vps_testing") is False, "CONTROL44_VPS_FENCE_WEAKENED")
    require(
        errors,
        hard44.get("runtime_credit_requires_exact_admitted_isolated_execution") is True,
        "CONTROL44_RUNTIME_EVIDENCE_FENCE_WEAKENED",
    )
    require(errors, hard44.get("model_output_is_candidate_not_truth") is True, "CONTROL44_MODEL_TRUTH_FENCE_WEAKENED")

    return {
        "schema": SCHEMA,
        "pass": not errors,
        "program": EXPECTED_PROGRAM,
        "stage": EXPECTED_STAGE,
        "product": EXPECTED_PRODUCT,
        "compute_architecture": EXPECTED_COMPUTE,
        "errors": errors,
        "checked_blobs": {
            "control41": blob41,
            "control42": blob42,
            "control43": blob43,
            "legacy_manifest": LEGACY_MANIFEST_BLOB,
        },
        "credit": "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = validate(args.root.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
