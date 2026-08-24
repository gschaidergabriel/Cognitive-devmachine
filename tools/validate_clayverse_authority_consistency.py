#!/usr/bin/env python3
"""Successor-dynamic fail-closed authority guard for current EntityOS + HCU.

The compatibility filename is retained for existing workflows and receipts. Current
authority is never selected by a hard-coded supervisor minor version. The guard
requires pointer consensus across canonical current-facing surfaces, validates the
exact referenced supervisor, and preserves the full historical 4.1 -> 4.4 safety /
provenance ancestry without reactivating historical product-selection authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

CURRENT_PROGRAM = "ENTITYOS_HCU"
CURRENT_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
CURRENT_PRODUCT = "EntityOS"
CURRENT_COMPUTE_ARCHITECTURE = "HCU"
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v4"
AUTHORITY_RE = re.compile(
    r"^research_entity/claycode/autonomous/SUPERVISOR_STEERING_(\d+)_(\d+)\.json$"
)
ROOT_CLAUDE = "CLAUDE.md"

CONTROL41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
LEGACY_EXPECTED_CONTROL = (
    "4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+"
    "4.4-clayverse-product-authority-addendum"
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        value = json.load(fh)
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def _safe_authority_path(value: object) -> str | None:
    if not isinstance(value, str) or not AUTHORITY_RE.fullmatch(value):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return value


def _authority_version_from_path(path: str) -> str:
    match = AUTHORITY_RE.fullmatch(path)
    assert match
    return f"{int(match.group(1))}.{int(match.group(2)):02d}"


def _validate_legacy_safety_ancestry(errors: list[str], root: Path) -> None:
    """Preserve every inherited safety/provenance fence without reviving old product law."""
    paths = {
        "c41": root / CONTROL41,
        "c42": root / CONTROL42,
        "c43": root / CONTROL43,
        "c44": root / CONTROL44,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING_LEGACY:{name}")
    if any(not path.is_file() for path in paths.values()):
        return

    try:
        c41 = load_json(paths["c41"])
        c42 = load_json(paths["c42"])
        c43 = load_json(paths["c43"])
        c44 = load_json(paths["c44"])
    except (OSError, json.JSONDecodeError, ValueError):
        errors.append("LEGACY_JSON_LOAD_ERROR")
        return

    require(errors, c41.get("schema_version") == "4.1", "CONTROL41_VERSION_MISMATCH")
    require(
        errors,
        c41.get("status") == "ACTIVE" and c41.get("mode") == "FREE_ONLY",
        "CONTROL41_FREE_ONLY_WEAKENED",
    )
    cycle41 = c41.get("cycle_policy") or {}
    require(errors, cycle41.get("paid_fallback") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(
        errors,
        cycle41.get("automatic_subscription_upgrade") is False,
        "CONTROL41_AUTO_UPGRADE_WEAKENED",
    )
    require(errors, cycle41.get("vps_testing") == "FORBIDDEN", "CONTROL41_VPS_TEST_WEAKENED")
    rules41 = set(c41.get("authority_rules") or [])
    require(
        errors,
        "model_output_is_candidate_not_truth" in rules41,
        "CONTROL41_MODEL_TRUTH_FENCE_MISSING",
    )
    require(
        errors,
        "autonomous_cycle_may_not_modify_FRANK_harness" in rules41,
        "CONTROL41_FRANK_HARNESS_FENCE_MISSING",
    )

    blob41 = git_blob_sha(paths["c41"])
    blob42 = git_blob_sha(paths["c42"])
    blob43 = git_blob_sha(paths["c43"])

    require(
        errors,
        c42.get("schema_version") == "4.2-execution-boundary-addendum",
        "CONTROL42_VERSION_MISMATCH",
    )
    require(
        errors,
        c42.get("status") == "ACTIVE" and c42.get("mode") == "FREE_ONLY",
        "CONTROL42_FREE_ONLY_WEAKENED",
    )
    require(errors, c42.get("base_control_path") == CONTROL41, "CONTROL42_BASE_PATH_MISMATCH")
    require(errors, c42.get("base_control_blob_sha") == blob41, "CONTROL42_BASE_BLOB_MISMATCH")
    hard42 = c42.get("preserved_hard_rules") or {}
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
    routing42 = c42.get("execution_routing") or {}
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
        c43.get("schema_version") == "4.3-program-authority-addendum",
        "CONTROL43_VERSION_MISMATCH",
    )
    require(
        errors,
        c43.get("status") == "ACTIVE" and c43.get("mode") == "FREE_ONLY",
        "CONTROL43_FREE_ONLY_WEAKENED",
    )
    require(errors, c43.get("base_control_path") == CONTROL41, "CONTROL43_BASE_PATH_MISMATCH")
    require(errors, c43.get("base_control_blob_sha") == blob41, "CONTROL43_BASE_BLOB_MISMATCH")
    require(
        errors,
        c43.get("execution_boundary_addendum_path") == CONTROL42,
        "CONTROL43_EXEC_PATH_MISMATCH",
    )
    require(
        errors,
        c43.get("execution_boundary_addendum_blob_sha") == blob42,
        "CONTROL43_EXEC_BLOB_MISMATCH",
    )
    hard43 = c43.get("preserved_hard_rules") or {}
    require(
        errors,
        hard43.get("free_only") is True and hard43.get("paid_fallback") is False,
        "CONTROL43_FREE_ONLY_WEAKENED",
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
        c44.get("schema_version") == "4.4-clayverse-product-authority-addendum",
        "CONTROL44_VERSION_MISMATCH",
    )
    require(
        errors,
        c44.get("status") == "ACTIVE" and c44.get("mode") == "FREE_ONLY",
        "CONTROL44_NOT_ACTIVE_FREE_ONLY",
    )
    require(errors, c44.get("base_control_path") == CONTROL41, "CONTROL44_BASE_PATH_MISMATCH")
    require(
        errors,
        c44.get("execution_boundary_addendum_path") == CONTROL42,
        "CONTROL44_EXEC_PATH_MISMATCH",
    )
    require(
        errors,
        c44.get("prior_program_authority_addendum_path") == CONTROL43,
        "CONTROL44_PRIOR_PATH_MISMATCH",
    )
    require(
        errors,
        c44.get("prior_program_authority_addendum_blob_sha") == blob43,
        "CONTROL44_PRIOR_BLOB_MISMATCH",
    )
    require(
        errors,
        c44.get("composition_order")
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
        c44.get("effective_control_version") == LEGACY_EXPECTED_CONTROL,
        "CONTROL44_EFFECTIVE_VERSION_MISMATCH",
    )
    override44 = c44.get("program_identity_override") or {}
    require(
        errors,
        override44.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER"
        and override44.get("target_stage") == "CLAYVERSE_ARTIFACT"
        and override44.get("product_endpoint") == "ClayVerse",
        "CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH",
    )
    hard44 = c44.get("preserved_hard_rules") or {}
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


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "inbox": root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
        "footer": root / "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
        "manifest": root / "the artefact/manifest.json",
        "architecture": root / "the artefact/ARCHITECTURE.md",
        "readme": root / "the artefact/README.md",
        "repo_claude": root / ROOT_CLAUDE,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": errors}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        inbox = load_json(paths["inbox"])
        manifest = load_json(paths["manifest"])
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "schema": CURRENT_SCHEMA,
            "pass": False,
            "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}"],
        }

    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    identity = bootstrap.get("identity") or {}
    require(errors, identity.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_TEMP_WORKER_ROLE_MISMATCH")
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(
        errors,
        bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE,
        "BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    require(errors, bootstrap.get("free_only") is True, "BOOTSTRAP_FREE_ONLY_MISMATCH")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_FENCE_MISSING")
    require(errors, "FORBIDDEN" in str(bootstrap.get("together_api", "")), "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")
    invariants = set(str(x) for x in bootstrap.get("mandatory_invariants") or [])
    require(
        errors,
        "EntityOS is the sole current product/system identity" in invariants,
        "BOOTSTRAP_ENTITYOS_INVARIANT_MISSING",
    )
    require(
        errors,
        "HCU is the sole current integrated cognition/compute architecture" in invariants,
        "BOOTSTRAP_HCU_INVARIANT_MISSING",
    )
    require(
        errors,
        "FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT" in invariants,
        "BOOTSTRAP_EPISTEMIC_FENCE_MISSING",
    )
    bootstrap_surface = str(bootstrap.get("execution_surface") or "")
    require(errors, "FREE_ONLY" in bootstrap_surface, "BOOTSTRAP_EXECUTION_FREE_ONLY_MISSING")
    require(
        errors,
        "EXTERNAL_LLM_PROVIDER_TRAFFIC_QUARANTINED" in bootstrap_surface,
        "BOOTSTRAP_PROVIDER_QUARANTINE_MISSING",
    )

    require(
        errors,
        program.get("program_id") == "entityos-hcu" and program.get("status") == "ACTIVE",
        "PROGRAM_ID_OR_STATUS_MISMATCH",
    )
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
    authority = program.get("authority") or {}
    require(errors, authority.get("external_effects") == "EffectGate+EffectJournal", "PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    require(errors, authority.get("second_persistent_identity") == "FORBIDDEN", "PROGRAM_SECOND_IDENTITY_NOT_FORBIDDEN")
    require(
        errors,
        authority.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN",
        "PROGRAM_SECOND_AUTHORITY_NOT_FORBIDDEN",
    )
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_EXECUTION_MISMATCH")
    require(
        errors,
        execution.get("authorized_zero_cost_local_normal_user_execution") is True,
        "PROGRAM_LOCAL_ZERO_COST_EXECUTION_AUTHORITY_MISSING",
    )
    require(
        errors,
        execution.get("authorized_clay_direct_dev_vps_sandbox_execution") is True,
        "PROGRAM_CLAY_DIRECT_DEV_AUTHORITY_MISSING",
    )
    require(
        errors,
        execution.get("production_host_testing_forbidden") is True,
        "PROGRAM_PRODUCTION_TEST_FENCE_WEAKENED",
    )
    require(
        errors,
        execution.get("together_general_inference_and_fallback_forbidden") is True,
        "PROGRAM_TOGETHER_INFERENCE_FENCE_MISSING",
    )
    require(
        errors,
        execution.get("current_supervisor_together_training_forbidden") is True,
        "PROGRAM_TOGETHER_TRAINING_FENCE_MISSING",
    )
    require(errors, execution.get("other_paid_fallback") is False, "PROGRAM_OTHER_PAID_FALLBACK_WEAKENED")
    require(errors, execution.get("current_provider_runtime_credit") == 0, "PROGRAM_PROVIDER_RUNTIME_CREDIT_NONZERO")
    provider_inventory = str(execution.get("current_provider_runtime_inventory") or "")
    require(errors, "QUARANTINED" in provider_inventory, "PROGRAM_PROVIDER_QUARANTINE_MISSING")
    credit = program.get("runtime_credit") or {}
    for field, code in (
        ("free_swarm_provider_admission_runtime_credit", "PROGRAM_FREE_ADMISSION_RUNTIME_CREDIT_NONZERO"),
        ("external_provider_worker_runtime_credit", "PROGRAM_EXTERNAL_PROVIDER_RUNTIME_CREDIT_NONZERO"),
        ("entityos_hcu_whole_runtime_credit", "PROGRAM_RUNTIME_CREDIT_NONZERO"),
        ("hcu_full_runtime_credit", "PROGRAM_HCU_RUNTIME_CREDIT_NONZERO"),
        ("jspace_model_runtime_credit", "PROGRAM_JSPACE_RUNTIME_CREDIT_NONZERO"),
        ("training_credit", "PROGRAM_TRAINING_CREDIT_NONZERO"),
    ):
        require(errors, credit.get(field) == 0, code)
    require(errors, credit.get("whole_product_pass") is False, "PROGRAM_WHOLE_PASS_PREMATURE")

    require(errors, manifest.get("artifact") == CURRENT_PRODUCT, "MANIFEST_ARTIFACT_MISMATCH")
    require(errors, manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_ENDPOINT_MISMATCH")
    require(
        errors,
        manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE,
        "MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH",
    )
    require(errors, manifest.get("stage") == CURRENT_STAGE, "MANIFEST_STAGE_MISMATCH")
    require(errors, manifest.get("canonical_workspace") == "the artefact/", "MANIFEST_WORKSPACE_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    donor = manifest.get("legacy_donor") or {}
    require(errors, donor.get("prior_product") == "ClayVerse", "MANIFEST_DONOR_PRODUCT_MISSING")
    require(
        errors,
        donor.get("scope") == "HISTORICAL_DONOR_PROVENANCE_ONLY",
        "MANIFEST_DONOR_SCOPE_MISMATCH",
    )
    mexec = manifest.get("execution_policy") or {}
    require(
        errors,
        mexec.get("free_only_default") is True and mexec.get("active_supervisor_free_only") is True,
        "MANIFEST_FREE_ONLY_EXECUTION_MISMATCH",
    )
    require(
        errors,
        mexec.get("authorized_zero_cost_local_normal_user_execution") is True,
        "MANIFEST_LOCAL_ZERO_COST_EXECUTION_AUTHORITY_MISSING",
    )
    require(
        errors,
        mexec.get("authorized_clay_direct_dev_vps_sandbox_execution") is True,
        "MANIFEST_CLAY_DIRECT_DEV_AUTHORITY_MISSING",
    )
    require(
        errors,
        mexec.get("external_llm_provider_execution")
        == "QUARANTINED_UNTIL_FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT_V1_EXACT_SOURCE_PASS",
        "MANIFEST_PROVIDER_QUARANTINE_MISSING",
    )
    require(
        errors,
        mexec.get("together_general_inference_and_fallback_forbidden") is True,
        "MANIFEST_TOGETHER_INFERENCE_FENCE_MISSING",
    )
    require(errors, mexec.get("other_paid_fallback") is False, "MANIFEST_OTHER_PAID_FALLBACK_WEAKENED")
    mcredit = manifest.get("runtime_credit") or {}
    for field, code in (
        ("free_swarm_provider_admission_runtime_credit", "MANIFEST_FREE_ADMISSION_RUNTIME_CREDIT_NONZERO"),
        ("external_provider_worker_runtime_credit", "MANIFEST_EXTERNAL_PROVIDER_RUNTIME_CREDIT_NONZERO"),
        ("entityos_hcu_whole_runtime_credit", "MANIFEST_RUNTIME_CREDIT_NONZERO"),
        ("hcu_full_runtime_credit", "MANIFEST_HCU_RUNTIME_CREDIT_NONZERO"),
        ("jspace_model_runtime_credit", "MANIFEST_JSPACE_RUNTIME_CREDIT_NONZERO"),
        ("training_credit", "MANIFEST_TRAINING_CREDIT_NONZERO"),
    ):
        require(errors, mcredit.get(field) == 0, code)
    require(errors, mcredit.get("whole_product_pass") is False, "MANIFEST_WHOLE_PASS_PREMATURE")

    raw_pointers = {
        "bootstrap": bootstrap.get("authority_correction"),
        "program": program.get("authority_correction"),
        "manifest": manifest.get("authority_correction"),
        "inbox": inbox.get("steering"),
    }
    pointers = {name: _safe_authority_path(value) for name, value in raw_pointers.items()}
    for name, value in pointers.items():
        require(errors, value is not None, f"AUTHORITY_POINTER_INVALID:{name}")
    valid = [value for value in pointers.values() if value is not None]
    authority_path = valid[0] if valid else None
    require(errors, len(valid) == len(pointers) and len(set(valid)) == 1, "AUTHORITY_POINTER_SPLIT_BRAIN")

    supervisor: dict[str, Any] | None = None
    if authority_path is not None:
        supervisor_file = root / authority_path
        require(errors, supervisor_file.is_file(), "AUTHORITY_TARGET_MISSING")
        if supervisor_file.is_file():
            try:
                supervisor = load_json(supervisor_file)
            except (OSError, json.JSONDecodeError, ValueError):
                errors.append("AUTHORITY_TARGET_JSON_LOAD_ERROR")

    if supervisor is not None and authority_path is not None:
        expected_version = _authority_version_from_path(authority_path)
        require(errors, str(supervisor.get("schema_version")) == expected_version, "AUTHORITY_FILENAME_SCHEMA_MISMATCH")
        observed_program = supervisor.get("active_program", supervisor.get("program"))
        require(errors, observed_program == CURRENT_PROGRAM, "SUPERVISOR_PROGRAM_MISMATCH")
        require(errors, supervisor.get("product") == CURRENT_PRODUCT, "SUPERVISOR_PRODUCT_MISMATCH")
        observed_arch = supervisor.get("integrated_cognition_compute_architecture", supervisor.get("compute_architecture"))
        require(errors, observed_arch == CURRENT_COMPUTE_ARCHITECTURE, "SUPERVISOR_COMPUTE_ARCHITECTURE_MISMATCH")
        free = supervisor.get("free_only") or supervisor.get("free_only_policy") or {}
        require(errors, free.get("enabled", True) is True, "SUPERVISOR_FREE_ONLY_DISABLED")
        require(errors, free.get("no_paid_fallback") is True, "SUPERVISOR_PAID_FALLBACK_WEAKENED")
        require(errors, free.get("together_forbidden") is True, "SUPERVISOR_TOGETHER_FENCE_MISSING")
        provider_state = str(free.get("external_llm_provider_execution") or "")
        require(errors, "QUARANTINED" in provider_state, "SUPERVISOR_PROVIDER_QUARANTINE_MISSING")
        promotion = supervisor.get("promotion") or supervisor.get("promotion_state") or {}
        require(errors, promotion.get("entityos_whole_runtime_pass") is False, "SUPERVISOR_WHOLE_PASS_PREMATURE")
        require(errors, promotion.get("hcu_full_runtime_pass") is False, "SUPERVISOR_HCU_PASS_PREMATURE")
        require(errors, promotion.get("provider_runtime_credit") == 0, "SUPERVISOR_PROVIDER_RUNTIME_CREDIT_NONZERO")
        require(errors, promotion.get("training_credit") == 0, "SUPERVISOR_TRAINING_CREDIT_NONZERO")

    footer = paths["footer"].read_text(encoding="utf-8").upper()
    architecture = paths["architecture"].read_text(encoding="utf-8").upper()
    readme = paths["readme"].read_text(encoding="utf-8").upper()
    repo_claude_raw = paths["repo_claude"].read_text(encoding="utf-8")
    repo_claude = repo_claude_raw.upper()

    require(errors, "PROGRAM: ENTITYOS + HCU" in footer, "FOOTER_PROGRAM_MISMATCH")
    require(errors, "STAGE: ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP" in footer, "FOOTER_STAGE_MISMATCH")
    require(errors, "PRODUCT: ENTITYOS" in footer, "FOOTER_PRODUCT_MISMATCH")
    require(errors, "COMPUTE ARCHITECTURE: HCU" in footer, "FOOTER_COMPUTE_ARCHITECTURE_MISMATCH")

    require(errors, "ENTITYOS" in architecture[:3000] and "HCU" in architecture[:3000], "ARCHITECTURE_ENTITYOS_HCU_MISSING")
    require(
        errors,
        "CLAYVERSE IS THE PRODUCT ENDPOINT" not in architecture[:3000],
        "ARCHITECTURE_STALE_CLAYVERSE_PRODUCT_AUTHORITY",
    )
    require(errors, "ENTITYOS" in readme[:3000] and "HCU" in readme[:3000], "README_ENTITYOS_HCU_MISSING")

    require(errors, "`PROGRAM=ENTITYOS_HCU`" in repo_claude[:5000], "ROOT_CLAUDE_PROGRAM_MISMATCH")
    require(
        errors,
        "`STAGE=ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP`" in repo_claude[:5000],
        "ROOT_CLAUDE_STAGE_MISMATCH",
    )
    require(errors, "`PRODUCT=ENTITYOS`" in repo_claude[:5000], "ROOT_CLAUDE_PRODUCT_MISMATCH")
    require(errors, "`COMPUTE_ARCHITECTURE=HCU`" in repo_claude[:5000], "ROOT_CLAUDE_COMPUTE_ARCHITECTURE_MISMATCH")
    require(
        errors,
        "SUPERVISOR_INBOX.JSON" in repo_claude,
        "ROOT_CLAUDE_DYNAMIC_SUPERVISOR_ROUTING_MISSING",
    )
    require(
        errors,
        re.search(r"AUTONOMOUS_SUPERVISOR\s*=\s*SUPERVISOR_STEERING_\d+_\d+", repo_claude_raw) is None,
        "ROOT_CLAUDE_FIXED_SUPERVISOR_PIN_FORBIDDEN",
    )
    require(
        errors,
        "RESOLVE" in repo_claude and "STEERING" in repo_claude,
        "ROOT_CLAUDE_DYNAMIC_RESOLUTION_TEXT_MISSING",
    )
    require(
        errors,
        "`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`" not in repo_claude[:5000],
        "ROOT_CLAUDE_STALE_CLAYVERSE_PROGRAM_ACTIVE",
    )

    _validate_legacy_safety_ancestry(errors, root)

    return {
        "schema": CURRENT_SCHEMA,
        "pass": not errors,
        "errors": errors,
        "resolved_authority": authority_path,
        "resolved_authority_schema": supervisor.get("schema_version") if supervisor else None,
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
