#!/usr/bin/env python3
"""Compatibility-named fail-closed authority guard for current EntityOS + HCU.

The filename remains stable for workflows/receipts. Historical ClayVerse 4.1->4.4
controls are hash-bound donor/safety ancestry only. Current authority is resolved
successor-dynamically from SUPERVISOR_INBOX whenever that canonical surface exists;
no fixed historical steering version may become its own expectation oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CURRENT_PROGRAM = "ENTITYOS_HCU"
CURRENT_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
CURRENT_PRODUCT = "EntityOS"
CURRENT_COMPUTE_ARCHITECTURE = "HCU"
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v2"
SUPERVISOR_INBOX = "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"

# Historical compatibility only. validate() never prefers this when the inbox exists.
CURRENT_AUTHORITY = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"

CONTROL41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
LEGACY_EXPECTED_CONTROL = "4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+4.4-clayverse-product-authority-addendum"
ROOT_CLAUDE = "CLAUDE.md"


class AuthorityResolutionError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"OBJECT_REQUIRED:{path.as_posix()}")
    return payload


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def _safe_repo_rel(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthorityResolutionError("CURRENT_STEERING_POINTER_REQUIRED")
    rel = Path(value.strip())
    if rel.is_absolute() or ".." in rel.parts:
        raise AuthorityResolutionError("CURRENT_STEERING_POINTER_INVALID")
    return rel.as_posix()


def resolve_current_supervisor(
    root: Path, bootstrap: dict[str, Any]
) -> tuple[str, str, dict[str, Any], dict[str, Any] | None]:
    """Resolve current steering from canonical inbox; fail closed on ambiguity."""
    root = root.resolve()
    inbox_path = root / SUPERVISOR_INBOX
    if inbox_path.is_file():
        try:
            inbox = load_json(inbox_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise AuthorityResolutionError(f"SUPERVISOR_INBOX_INVALID:{type(exc).__name__}") from exc
        epoch = str(inbox.get("schema_version") or "").strip()
        if not epoch:
            raise AuthorityResolutionError("SUPERVISOR_INBOX_EPOCH_REQUIRED")
        rel = _safe_repo_rel(inbox.get("steering"))
        steering_path = (root / rel).resolve()
        try:
            steering_path.relative_to(root)
        except ValueError as exc:
            raise AuthorityResolutionError("CURRENT_STEERING_OUTSIDE_REPO") from exc
        if not steering_path.is_file():
            raise AuthorityResolutionError(f"CURRENT_STEERING_MISSING:{rel}")
        try:
            steering = load_json(steering_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise AuthorityResolutionError(f"CURRENT_STEERING_INVALID:{type(exc).__name__}") from exc
        if str(steering.get("schema_version") or "").strip() != epoch:
            raise AuthorityResolutionError("SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH")
        return epoch, rel, steering, inbox

    # Pre-inbox historical fixture compatibility only.
    rel = _safe_repo_rel(bootstrap.get("authority_correction") or CURRENT_AUTHORITY)
    steering_path = root / rel
    if not steering_path.is_file():
        raise AuthorityResolutionError(f"CURRENT_STEERING_MISSING:{rel}")
    steering = load_json(steering_path)
    epoch = str(steering.get("schema_version") or bootstrap.get("schema_version") or "").strip()
    if not epoch:
        raise AuthorityResolutionError("CURRENT_STEERING_EPOCH_REQUIRED")
    return epoch, rel, steering, None


def _validate_modern_execution(
    errors: list[str], bootstrap: dict[str, Any], program: dict[str, Any], manifest: dict[str, Any]
) -> None:
    require(errors, bootstrap.get("free_only") is True, "BOOTSTRAP_FREE_ONLY_MISSING")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_FENCE_MISSING")
    require(errors, "FORBIDDEN" in str(bootstrap.get("together_api") or ""), "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, "FREE_ONLY" in str(bootstrap.get("execution_surface") or ""), "BOOTSTRAP_EXECUTION_FENCE_MISSING")

    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(
        errors,
        execution.get("other_paid_fallback") is False or execution.get("paid_fallback") is False,
        "PROGRAM_PAID_FALLBACK_WEAKENED",
    )
    require(
        errors,
        execution.get("together_general_inference_and_fallback_forbidden") is True
        or execution.get("together_forbidden") is True,
        "PROGRAM_TOGETHER_FENCE_MISSING",
    )
    if "unknown_paid_subscription_provider" in execution:
        require(
            errors,
            "FAIL_CLOSED" in str(execution.get("unknown_paid_subscription_provider") or ""),
            "PROGRAM_UNKNOWN_COST_FAIL_CLOSED_MISSING",
        )

    mexec = manifest.get("execution_policy") or {}
    require(
        errors,
        mexec.get("active_supervisor_free_only") is True or mexec.get("free_only") is True,
        "MANIFEST_FREE_ONLY_MISSING",
    )
    require(
        errors,
        mexec.get("other_paid_fallback") is False or mexec.get("paid_fallback") is False,
        "MANIFEST_PAID_FALLBACK_WEAKENED",
    )
    require(
        errors,
        mexec.get("together_general_inference_and_fallback_forbidden") is True
        or mexec.get("together_forbidden") is True,
        "MANIFEST_TOGETHER_FENCE_MISSING",
    )


def _validate_historical_execution_fixture(
    errors: list[str], bootstrap: dict[str, Any], program: dict[str, Any], manifest: dict[str, Any]
) -> None:
    require(errors, bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_SANDBOX_ONLY", "BOOTSTRAP_EXECUTION_FENCE_MISSING")
    require(errors, bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_FENCE_MISSING")
    if "final_paid_model_training" in bootstrap:
        require(
            errors,
            bootstrap.get("final_paid_model_training") == "OWNER_AUTHORIZATION_REQUIRED",
            "BOOTSTRAP_PAID_TRAINING_GATE_MISSING",
        )
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(errors, execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_ONLY_MISSING")
    require(errors, execution.get("vps_testing_forbidden") is True, "PROGRAM_VPS_TEST_FENCE_MISSING")
    require(errors, execution.get("self_hosted_vps_test_runners_forbidden") is True, "PROGRAM_SELF_HOSTED_FENCE_MISSING")
    require(errors, execution.get("production_host_testing_forbidden") is True, "PROGRAM_PRODUCTION_TEST_FENCE_MISSING")
    require(errors, execution.get("together_forbidden") is True, "PROGRAM_TOGETHER_FENCE_MISSING")
    require(errors, execution.get("paid_fallback") is False, "PROGRAM_PAID_FALLBACK_WEAKENED")
    mexec = manifest.get("execution_policy") or {}
    require(errors, mexec.get("free_only") is True, "MANIFEST_FREE_ONLY_MISSING")
    require(errors, mexec.get("isolated_sandbox_only") is True, "MANIFEST_ISOLATED_ONLY_MISSING")
    require(errors, mexec.get("vps_testing_forbidden") is True, "MANIFEST_VPS_TEST_FENCE_MISSING")
    require(errors, mexec.get("together_forbidden") is True, "MANIFEST_TOGETHER_FENCE_MISSING")
    require(errors, mexec.get("paid_fallback") is False, "MANIFEST_PAID_FALLBACK_WEAKENED")


def _validate_current_steering(
    errors: list[str], epoch: str, steering: dict[str, Any], inbox: dict[str, Any] | None
) -> None:
    require(errors, str(steering.get("schema_version") or "") == epoch, "CURRENT_STEERING_SCHEMA_MISMATCH")
    require(
        errors,
        (steering.get("active_program") or steering.get("program")) == CURRENT_PROGRAM,
        "CURRENT_STEERING_PROGRAM_MISMATCH",
    )
    require(errors, steering.get("product") == CURRENT_PRODUCT, "CURRENT_STEERING_PRODUCT_MISMATCH")
    require(
        errors,
        steering.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE,
        "CURRENT_STEERING_COMPUTE_ARCHITECTURE_MISMATCH",
    )

    free = steering.get("free_only") or {}
    routing = set(str(x) for x in steering.get("routing_law") or [])
    if isinstance(free, dict) and free:
        require(errors, free.get("enabled") is True, "CURRENT_STEERING_FREE_ONLY_FENCE_MISSING")
        require(errors, free.get("no_paid_fallback") is True, "CURRENT_STEERING_PAID_FALLBACK_WEAKENED")
        require(errors, free.get("together_forbidden") is True, "CURRENT_STEERING_TOGETHER_FENCE_MISSING")
        unknown = free.get("unknown_or_unlisted_route") or free.get("unknown_or_unlisted_provider")
        if unknown is not None:
            require(errors, "FAIL_CLOSED" in str(unknown), "CURRENT_STEERING_UNKNOWN_ROUTE_NOT_FAIL_CLOSED")
    else:
        require(
            errors,
            "FREE_ONLY_REMAINS_FAIL_CLOSED_WITH_NO_PAID_FALLBACK" in routing,
            "STEERING852_FREE_ONLY_FENCE_MISSING",
        )
        if routing:
            require(
                errors,
                "EXECUTABLE_EVIDENCE_OUTRANKS_MODEL_CONSENSUS" in routing,
                "STEERING852_EVIDENCE_FENCE_MISSING",
            )

    promotion = steering.get("promotion") or steering.get("current_runtime_evidence") or {}
    require(
        errors,
        promotion.get("entityos_whole_runtime_pass") is False
        or promotion.get("whole_product_pass") is False,
        "CURRENT_STEERING_WHOLE_PASS_PREMATURE",
    )
    for key in ("provider_runtime_credit", "training_credit", "entityos_hcu_whole_runtime_credit"):
        if key in promotion:
            require(errors, promotion.get(key) == 0, f"CURRENT_STEERING_{key.upper()}_NONZERO")

    if inbox is not None:
        require(errors, str(inbox.get("schema_version") or "") == epoch, "SUPERVISOR_INBOX_EPOCH_MISMATCH")
        require(errors, inbox.get("active_program") == CURRENT_PROGRAM, "SUPERVISOR_INBOX_PROGRAM_MISMATCH")
        require(errors, inbox.get("product") == CURRENT_PRODUCT, "SUPERVISOR_INBOX_PRODUCT_MISMATCH")
        require(
            errors,
            inbox.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE,
            "SUPERVISOR_INBOX_COMPUTE_ARCHITECTURE_MISMATCH",
        )
        infree = inbox.get("free_only") or {}
        if isinstance(infree, dict) and infree:
            require(errors, infree.get("enabled") is True, "SUPERVISOR_INBOX_FREE_ONLY_MISSING")
            require(errors, infree.get("no_paid_fallback") is True, "SUPERVISOR_INBOX_PAID_FALLBACK_WEAKENED")
            require(errors, infree.get("together_forbidden") is True, "SUPERVISOR_INBOX_TOGETHER_FENCE_MISSING")
        evidence = set(str(x) for x in inbox.get("evidence_law") or [])
        if evidence:
            require(
                errors,
                any("NO_POSTHOC" in x or "HISTORICAL_RECEIPTS_ARE_APPEND_ONLY" in x for x in evidence),
                "SUPERVISOR_INBOX_STALE_EVIDENCE_QUARANTINE_MISSING",
            )


def _validate_legacy_safety_ancestry(
    errors: list[str],
    paths: dict[str, Path],
    control41: dict[str, Any],
    control42: dict[str, Any],
    control43: dict[str, Any],
    control44: dict[str, Any],
) -> None:
    """Preserve every pre-existing hard 4.1->4.4 safety/provenance fence."""
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

    require(errors, control44.get("schema_version") == "4.4-clayverse-product-authority-addendum", "CONTROL44_VERSION_MISMATCH")
    require(errors, control44.get("status") == "ACTIVE" and control44.get("mode") == "FREE_ONLY", "CONTROL44_NOT_ACTIVE_FREE_ONLY")
    require(errors, control44.get("base_control_path") == CONTROL41, "CONTROL44_BASE_PATH_MISMATCH")
    require(errors, control44.get("execution_boundary_addendum_path") == CONTROL42, "CONTROL44_EXEC_PATH_MISMATCH")
    require(errors, control44.get("prior_program_authority_addendum_path") == CONTROL43, "CONTROL44_PRIOR_PATH_MISMATCH")
    require(errors, control44.get("prior_program_authority_addendum_blob_sha") == blob43, "CONTROL44_PRIOR_BLOB_MISMATCH")
    require(
        errors,
        control44.get("composition_order") == [
            "4.1",
            "4.2-execution-boundary-addendum",
            "4.3-program-authority-addendum",
            "4.4-clayverse-product-authority-addendum",
        ],
        "CONTROL44_COMPOSITION_ORDER_MISMATCH",
    )
    require(errors, control44.get("effective_control_version") == LEGACY_EXPECTED_CONTROL, "CONTROL44_EFFECTIVE_VERSION_MISMATCH")
    override = control44.get("program_identity_override") or {}
    require(
        errors,
        override.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER"
        and override.get("target_stage") == "CLAYVERSE_ARTIFACT"
        and override.get("product_endpoint") == "ClayVerse",
        "CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH",
    )
    hard44 = control44.get("preserved_hard_rules") or {}
    require(errors, hard44.get("free_only") is True and hard44.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, hard44.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, hard44.get("vps_testing") is False, "CONTROL44_VPS_TEST_WEAKENED")
    require(errors, hard44.get("runtime_credit_requires_exact_admitted_isolated_execution") is True, "CONTROL44_RUNTIME_EVIDENCE_WEAKENED")
    require(errors, hard44.get("model_output_is_candidate_not_truth") is True, "CONTROL44_MODEL_TRUTH_FENCE_WEAKENED")
    require(errors, hard44.get("frank_harness_modification") == "FORBIDDEN", "CONTROL44_FRANK_HARNESS_FENCE_WEAKENED")


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    base_paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
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
    for name, path in base_paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": errors}

    try:
        canonical = load_json(base_paths["canonical"])
        bootstrap = load_json(base_paths["bootstrap"])
        program = load_json(base_paths["program"])
        manifest = load_json(base_paths["manifest"])
        control41 = load_json(base_paths["control41"])
        control42 = load_json(base_paths["control42"])
        control43 = load_json(base_paths["control43"])
        control44 = load_json(base_paths["control44"])
        epoch, authority_rel, steering, inbox = resolve_current_supervisor(root, bootstrap)
    except AuthorityResolutionError as exc:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": [str(exc)]}
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"]}

    paths = dict(base_paths)
    paths["steering_current"] = root / authority_rel
    if inbox is not None:
        paths["supervisor_inbox"] = root / SUPERVISOR_INBOX

    # Persistent identity and product authority.
    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    identity = bootstrap.get("identity") or {}
    require(errors, identity.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_TEMP_WORKER_ROLE_MISMATCH")
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")

    # Successor-dynamic anti-stale-island checks.
    require(errors, bootstrap.get("authority_correction") == authority_rel, "BOOTSTRAP_AUTHORITY_POINTER_MISMATCH")
    require(errors, program.get("authority_correction") == authority_rel or inbox is None, "PROGRAM_AUTHORITY_POINTER_MISMATCH")
    require(errors, manifest.get("authority_correction") == authority_rel, "MANIFEST_AUTHORITY_POINTER_MISMATCH")
    if inbox is not None:
        require(errors, str(bootstrap.get("schema_version") or "") == epoch, "BOOTSTRAP_AUTHORITY_EPOCH_DRIFT")
        require(errors, str(program.get("schema_version") or "") == epoch, "PROGRAM_AUTHORITY_EPOCH_DRIFT")
        mexec = manifest.get("execution_policy") or {}
        if "active_supervisor_epoch" in mexec:
            require(errors, str(mexec.get("active_supervisor_epoch")) == epoch, "MANIFEST_AUTHORITY_EPOCH_DRIFT")

    invariants = set(str(x) for x in bootstrap.get("mandatory_invariants") or [])
    require(errors, "EntityOS is the sole current product/system identity" in invariants, "BOOTSTRAP_ENTITYOS_INVARIANT_MISSING")
    require(errors, "HCU is the sole current integrated cognition/compute architecture" in invariants, "BOOTSTRAP_HCU_INVARIANT_MISSING")
    require(errors, "FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT" in invariants, "BOOTSTRAP_EPISTEMIC_FENCE_MISSING")

    require(errors, program.get("program_id") == "entityos-hcu", "PROGRAM_ID_MISMATCH")
    require(errors, program.get("status") == "ACTIVE", "PROGRAM_NOT_ACTIVE")
    require(errors, program.get("stage") == CURRENT_STAGE and program.get("current_stage") == CURRENT_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("product") == CURRENT_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(errors, program.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH")
    pidentity = program.get("identity") or {}
    require(errors, pidentity.get("persistent_research_entity") == "Clay", "PROGRAM_PERSISTENT_ENTITY_MISMATCH")
    require(errors, pidentity.get("temporary_workers") == "ORGANS_NOT_ENTITIES", "PROGRAM_TEMP_WORKER_ROLE_MISMATCH")
    pauthority = program.get("authority") or {}
    require(errors, pauthority.get("external_effects") == "EffectGate+EffectJournal", "PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    require(errors, pauthority.get("second_persistent_identity") == "FORBIDDEN", "PROGRAM_SECOND_IDENTITY_NOT_FORBIDDEN")
    require(errors, pauthority.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN", "PROGRAM_SECOND_AUTHORITY_NOT_FORBIDDEN")
    tracks = program.get("go_required_tracks") or {}
    require(errors, tracks.get("track_a") == "ENTITYOS_EXECUTABLE_CONVERGENCE", "PROGRAM_GO_TRACK_A_MISMATCH")
    require(errors, tracks.get("track_b") == "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT", "PROGRAM_GO_TRACK_B_MISMATCH")
    credit = program.get("runtime_credit") or {}
    require(errors, credit.get("entityos_hcu_whole_runtime_credit") == 0, "PROGRAM_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("whole_product_pass") is False, "PROGRAM_WHOLE_PASS_PREMATURE")

    require(errors, manifest.get("artifact") == CURRENT_PRODUCT, "MANIFEST_ARTIFACT_MISMATCH")
    require(errors, manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, manifest.get("stage") == CURRENT_STAGE, "MANIFEST_STAGE_MISMATCH")
    require(errors, manifest.get("canonical_workspace") == "the artefact/", "MANIFEST_WORKSPACE_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    mcredit = manifest.get("runtime_credit") or {}
    require(errors, mcredit.get("entityos_hcu_whole_runtime_credit") == 0, "MANIFEST_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("hcu_full_runtime_credit", 0) == 0, "MANIFEST_HCU_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("jspace_model_runtime_credit", 0) == 0, "MANIFEST_JSPACE_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("training_credit", 0) == 0, "MANIFEST_TRAINING_CREDIT_NONZERO")
    require(errors, mcredit.get("whole_product_pass") is False, "MANIFEST_WHOLE_PASS_PREMATURE")
    donor = manifest.get("legacy_donor") or {}
    require(errors, donor.get("prior_product") == "ClayVerse", "MANIFEST_DONOR_PRODUCT_MISSING")
    require(errors, donor.get("scope") == "HISTORICAL_DONOR_PROVENANCE_ONLY", "MANIFEST_DONOR_SCOPE_MISMATCH")

    if inbox is not None:
        _validate_modern_execution(errors, bootstrap, program, manifest)
    else:
        _validate_historical_execution_fixture(errors, bootstrap, program, manifest)

    _validate_current_steering(errors, epoch, steering, inbox)
    _validate_legacy_safety_ancestry(errors, paths, control41, control42, control43, control44)

    footer = base_paths["footer"].read_text(encoding="utf-8").upper()
    architecture = base_paths["architecture"].read_text(encoding="utf-8").upper()
    readme = base_paths["readme"].read_text(encoding="utf-8").upper()
    repo_claude = base_paths["repo_claude"].read_text(encoding="utf-8").upper()
    require(errors, "PROGRAM: ENTITYOS + HCU" in footer, "FOOTER_PROGRAM_MISMATCH")
    require(errors, "STAGE: ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP" in footer, "FOOTER_STAGE_MISMATCH")
    require(errors, "PRODUCT: ENTITYOS" in footer, "FOOTER_PRODUCT_MISMATCH")
    require(errors, "COMPUTE ARCHITECTURE: HCU" in footer, "FOOTER_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, "ENTITYOS" in architecture[:2500], "ARCHITECTURE_ENTITYOS_MISSING")
    require(errors, "HCU" in architecture[:2500], "ARCHITECTURE_HCU_MISSING")
    require(errors, "CLAYVERSE IS THE PRODUCT ENDPOINT" not in architecture[:2500], "ARCHITECTURE_STALE_CLAYVERSE_PRODUCT_AUTHORITY")
    require(errors, "ENTITYOS" in readme[:2500] and "HCU" in readme[:2500], "README_ENTITYOS_HCU_MISSING")
    require(errors, "`PROGRAM=ENTITYOS_HCU`" in repo_claude[:6000], "ROOT_CLAUDE_PROGRAM_MISMATCH")
    require(errors, "`STAGE=ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP`" in repo_claude[:6000], "ROOT_CLAUDE_STAGE_MISMATCH")
    require(errors, "`PRODUCT=ENTITYOS`" in repo_claude[:6000], "ROOT_CLAUDE_PRODUCT_MISMATCH")
    require(errors, "`COMPUTE_ARCHITECTURE=HCU`" in repo_claude[:6000], "ROOT_CLAUDE_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, Path(authority_rel).name.upper() in repo_claude[:6000], "ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING")
    require(errors, "`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`" not in repo_claude[:6000], "ROOT_CLAUDE_STALE_CLAYVERSE_PROGRAM_ACTIVE")

    return {
        "schema": CURRENT_SCHEMA,
        "pass": not errors,
        "errors": errors,
        "resolved_supervisor_epoch": epoch,
        "resolved_supervisor": authority_rel,
        "resolution_source": "SUPERVISOR_INBOX" if inbox is not None else "HISTORICAL_COMPATIBILITY_FALLBACK",
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
