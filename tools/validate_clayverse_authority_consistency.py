#!/usr/bin/env python3
"""Successor-aware fail-closed authority guard for current EntityOS + HCU.

The compatibility filename remains because workflows and historical receipts address it.
Current authority is never selected by a hard-coded supervisor minor version. The guard
requires one safe supervisor pointer across Bootstrap, Program State, artefact Manifest
and Supervisor Inbox, validates that exact supervisor and binds the typed FREE-provider
authority to the same epoch before accepting current-facing state.

Historical 4.x controls remain immutable donor/safety ancestry. They do not silently
revoke newer explicit owner authority for zero-cost local or clay-direct-dev routing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

CURRENT_PROGRAM = "ENTITYOS_HCU"
CURRENT_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
CURRENT_PRODUCT = "EntityOS"
CURRENT_COMPUTE_ARCHITECTURE = "HCU"
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v5"
AUTHORITY_RE = re.compile(r"^research_entity/claycode/autonomous/SUPERVISOR_STEERING_(\d+)_(\d+)\.json$")
ROOT_CLAUDE = "CLAUDE.md"
PROVIDER_ADMISSION = "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
PROVIDER_SCHEMA = "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1"

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


def _quarantined(value: object) -> bool:
    return isinstance(value, str) and "QUARANTINED" in value


def _validate_legacy_safety_ancestry(errors: list[str], root: Path) -> None:
    """Validate immutable donor ancestry without reactivating its old routing authority."""
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
    except (OSError, json.JSONDecodeError):
        errors.append("LEGACY_JSON_LOAD_ERROR")
        return

    require(errors, c41.get("schema_version") == "4.1", "CONTROL41_VERSION_MISMATCH")
    require(errors, c41.get("status") == "ACTIVE" and c41.get("mode") == "FREE_ONLY", "CONTROL41_FREE_ONLY_WEAKENED")
    cycle41 = c41.get("cycle_policy") or {}
    require(errors, cycle41.get("paid_fallback") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(errors, cycle41.get("automatic_subscription_upgrade") is False, "CONTROL41_AUTO_UPGRADE_WEAKENED")
    require(errors, cycle41.get("vps_testing") == "FORBIDDEN", "CONTROL41_VPS_TEST_ANCESTRY_CHANGED")
    rules41 = set(c41.get("authority_rules") or [])
    require(errors, "model_output_is_candidate_not_truth" in rules41, "CONTROL41_MODEL_TRUTH_FENCE_MISSING")
    require(errors, "autonomous_cycle_may_not_modify_FRANK_harness" in rules41, "CONTROL41_FRANK_HARNESS_FENCE_MISSING")

    blob41 = git_blob_sha(paths["c41"])
    blob42 = git_blob_sha(paths["c42"])
    blob43 = git_blob_sha(paths["c43"])
    require(errors, c42.get("base_control_path") == CONTROL41, "CONTROL42_BASE_PATH_MISMATCH")
    require(errors, c42.get("base_control_blob_sha") == blob41, "CONTROL42_BASE_BLOB_MISMATCH")
    hard42 = c42.get("preserved_hard_rules") or {}
    require(errors, hard42.get("free_only") is True and hard42.get("paid_fallback") is False, "CONTROL42_FREE_ONLY_FENCE_WEAKENED")
    require(errors, hard42.get("together_forbidden") is True, "CONTROL42_TOGETHER_FENCE_WEAKENED")

    require(errors, c43.get("base_control_blob_sha") == blob41, "CONTROL43_BASE_BLOB_MISMATCH")
    require(errors, c43.get("execution_boundary_addendum_path") == CONTROL42, "CONTROL43_EXEC_PATH_MISMATCH")
    require(errors, c43.get("execution_boundary_addendum_blob_sha") == blob42, "CONTROL43_EXEC_BLOB_MISMATCH")
    hard43 = c43.get("preserved_hard_rules") or {}
    require(errors, hard43.get("free_only") is True and hard43.get("paid_fallback") is False, "CONTROL43_FREE_ONLY_WEAKENED")
    require(errors, hard43.get("together_forbidden_under_current_control") is True, "CONTROL43_TOGETHER_FENCE_WEAKENED")

    require(errors, c44.get("prior_program_authority_addendum_path") == CONTROL43, "CONTROL44_PRIOR_PATH_MISMATCH")
    require(errors, c44.get("prior_program_authority_addendum_blob_sha") == blob43, "CONTROL44_PRIOR_BLOB_MISMATCH")
    require(errors, c44.get("effective_control_version") == LEGACY_EXPECTED_CONTROL, "CONTROL44_EFFECTIVE_VERSION_MISMATCH")
    hard44 = c44.get("preserved_hard_rules") or {}
    require(errors, hard44.get("free_only") is True and hard44.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, hard44.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, hard44.get("vps_testing") is False, "CONTROL44_VPS_TEST_ANCESTRY_CHANGED")


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "inbox": root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
        "manifest": root / "the artefact/manifest.json",
        "provider_admission": root / PROVIDER_ADMISSION,
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
        provider_admission = load_json(paths["provider_admission"])
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}"]}

    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    identity = bootstrap.get("identity") or {}
    require(errors, identity.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_TEMP_WORKER_ROLE_MISMATCH")
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, bootstrap.get("free_only") is True and bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_FREE_ONLY_MISMATCH")
    require(errors, "FORBIDDEN" in str(bootstrap.get("together_api", "")), "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")
    require(errors, _quarantined(bootstrap.get("execution_surface")), "BOOTSTRAP_PROVIDER_QUARANTINE_MISSING")

    require(errors, program.get("program_id") == "entityos-hcu" and program.get("status") == "ACTIVE", "PROGRAM_ID_OR_STATUS_MISMATCH")
    require(errors, program.get("stage") == CURRENT_STAGE and program.get("current_stage") == CURRENT_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("product") == CURRENT_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(errors, program.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH")
    pauthority = program.get("authority") or {}
    require(errors, pauthority.get("external_effects") == "EffectGate+EffectJournal", "PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    require(errors, pauthority.get("second_persistent_identity") == "FORBIDDEN", "PROGRAM_SECOND_IDENTITY_NOT_FORBIDDEN")
    require(errors, pauthority.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN", "PROGRAM_SECOND_AUTHORITY_NOT_FORBIDDEN")
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_EXECUTION_MISMATCH")
    require(errors, execution.get("authorized_zero_cost_local_normal_user_execution") is True, "PROGRAM_LOCAL_ZERO_COST_AUTHORITY_MISSING")
    require(errors, execution.get("authorized_clay_direct_dev_vps_sandbox_execution") is True, "PROGRAM_CLAY_DIRECT_DEV_AUTHORITY_MISSING")
    require(errors, execution.get("local_root_or_sudo_new_authority_implied") is False, "PROGRAM_LOCAL_ROOT_SCOPE_WEAKENED")
    require(errors, execution.get("unrelated_vps_host_changes_allowed") is False, "PROGRAM_UNRELATED_VPS_SCOPE_WEAKENED")
    require(errors, execution.get("new_external_production_effects_separately_gated") is True, "PROGRAM_PRODUCTION_EFFECT_GATE_MISSING")
    require(errors, execution.get("production_host_testing_forbidden") is True, "PROGRAM_PRODUCTION_TEST_FENCE_WEAKENED")
    require(errors, execution.get("together_general_inference_and_fallback_forbidden") is True, "PROGRAM_TOGETHER_INFERENCE_FENCE_MISSING")
    require(errors, execution.get("current_supervisor_together_training_forbidden") is True, "PROGRAM_TOGETHER_TRAINING_FENCE_MISSING")
    require(errors, execution.get("other_paid_fallback") is False, "PROGRAM_OTHER_PAID_FALLBACK_WEAKENED")
    require(errors, execution.get("current_provider_runtime_credit") == 0, "PROGRAM_PROVIDER_CREDIT_NONZERO")
    require(errors, _quarantined(execution.get("current_provider_runtime_inventory")), "PROGRAM_PROVIDER_QUARANTINE_MISSING")
    require(errors, execution.get("environment_attestation_is_authority") is False, "PROGRAM_ENV_ATTESTATION_SELF_AUTHORITY")
    credit = program.get("runtime_credit") or {}
    require(errors, credit.get("entityos_hcu_whole_runtime_credit") == 0, "PROGRAM_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("hcu_full_runtime_credit") == 0, "PROGRAM_HCU_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("jspace_model_runtime_credit") == 0, "PROGRAM_JSPACE_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("training_credit") == 0, "PROGRAM_TRAINING_CREDIT_NONZERO")
    require(errors, credit.get("external_provider_worker_runtime_credit") == 0, "PROGRAM_EXTERNAL_PROVIDER_RUNTIME_CREDIT_NONZERO")
    require(errors, credit.get("whole_product_pass") is False, "PROGRAM_WHOLE_PASS_PREMATURE")

    require(errors, manifest.get("artifact") == CURRENT_PRODUCT, "MANIFEST_ARTIFACT_MISMATCH")
    require(errors, manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "MANIFEST_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors, manifest.get("stage") == CURRENT_STAGE, "MANIFEST_STAGE_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    mexec = manifest.get("execution_policy") or {}
    require(errors, mexec.get("active_supervisor_free_only") is True, "MANIFEST_FREE_ONLY_EXECUTION_MISMATCH")
    require(errors, mexec.get("authorized_zero_cost_local_normal_user_execution") is True, "MANIFEST_LOCAL_ZERO_COST_AUTHORITY_MISSING")
    require(errors, mexec.get("authorized_clay_direct_dev_vps_sandbox_execution") is True, "MANIFEST_CLAY_DIRECT_DEV_AUTHORITY_MISSING")
    require(errors, mexec.get("local_root_or_sudo_new_authority_implied") is False, "MANIFEST_LOCAL_ROOT_SCOPE_WEAKENED")
    require(errors, mexec.get("unrelated_vps_host_changes_allowed") is False, "MANIFEST_UNRELATED_VPS_SCOPE_WEAKENED")
    require(errors, mexec.get("new_external_production_effects_separately_gated") is True, "MANIFEST_PRODUCTION_EFFECT_GATE_MISSING")
    require(errors, mexec.get("production_host_testing_forbidden") is True, "MANIFEST_PRODUCTION_TEST_FENCE_WEAKENED")
    require(errors, mexec.get("together_general_inference_and_fallback_forbidden") is True, "MANIFEST_TOGETHER_INFERENCE_FENCE_MISSING")
    require(errors, "FORBIDDEN" in str(mexec.get("current_supervisor_together_training", "")), "MANIFEST_TOGETHER_TRAINING_FENCE_MISSING")
    require(errors, mexec.get("other_paid_fallback") is False, "MANIFEST_OTHER_PAID_FALLBACK_WEAKENED")
    require(errors, _quarantined(mexec.get("external_llm_provider_execution")), "MANIFEST_PROVIDER_QUARANTINE_MISSING")
    mcredit = manifest.get("runtime_credit") or {}
    require(errors, mcredit.get("entityos_hcu_whole_runtime_credit") == 0, "MANIFEST_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("hcu_full_runtime_credit") == 0, "MANIFEST_HCU_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("jspace_model_runtime_credit") == 0, "MANIFEST_JSPACE_RUNTIME_CREDIT_NONZERO")
    require(errors, mcredit.get("training_credit") == 0, "MANIFEST_TRAINING_CREDIT_NONZERO")
    require(errors, mcredit.get("external_provider_worker_runtime_credit") == 0, "MANIFEST_EXTERNAL_PROVIDER_RUNTIME_CREDIT_NONZERO")
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

    owner_values = {
        "bootstrap": bootstrap.get("active_owner_authority"),
        "program": program.get("active_owner_authority"),
    }
    require(errors, all(isinstance(v, str) and v for v in owner_values.values()), "OWNER_AUTHORITY_POINTER_MISSING")
    require(errors, len(set(owner_values.values())) == 1, "OWNER_AUTHORITY_POINTER_SPLIT_BRAIN")

    supervisor = None
    expected_version = None
    if authority_path is not None:
        expected_version = _authority_version_from_path(authority_path)
        supervisor_file = root / authority_path
        require(errors, supervisor_file.is_file(), "AUTHORITY_TARGET_MISSING")
        if supervisor_file.is_file():
            try:
                supervisor = load_json(supervisor_file)
            except (OSError, json.JSONDecodeError):
                errors.append("AUTHORITY_TARGET_JSON_LOAD_ERROR")

    if supervisor is not None and authority_path is not None and expected_version is not None:
        require(errors, str(supervisor.get("schema_version")) == expected_version, "AUTHORITY_FILENAME_SCHEMA_MISMATCH")
        require(errors, str(inbox.get("schema_version")) == expected_version, "SUPERVISOR_INBOX_SCHEMA_MISMATCH")
        require(errors, str(program.get("schema_version")) == expected_version, "PROGRAM_SCHEMA_NOT_SUPERVISOR_SUCCESSOR")
        require(errors, str(mexec.get("active_supervisor_epoch")) == expected_version, "MANIFEST_SUPERVISOR_EPOCH_MISMATCH")
        observed_program = supervisor.get("active_program", supervisor.get("program"))
        require(errors, observed_program == CURRENT_PROGRAM, "SUPERVISOR_PROGRAM_MISMATCH")
        require(errors, supervisor.get("product") == CURRENT_PRODUCT, "SUPERVISOR_PRODUCT_MISMATCH")
        observed_arch = supervisor.get("integrated_cognition_compute_architecture", supervisor.get("compute_architecture"))
        require(errors, observed_arch == CURRENT_COMPUTE_ARCHITECTURE, "SUPERVISOR_COMPUTE_ARCHITECTURE_MISMATCH")
        free = supervisor.get("free_only") or supervisor.get("free_only_policy") or {}
        mode_free = supervisor.get("mode") == "FREE_ONLY" or free.get("enabled") is True
        require(errors, mode_free, "SUPERVISOR_MODE_NOT_FREE_ONLY")
        require(errors, free.get("no_paid_fallback") is True, "SUPERVISOR_PAID_FALLBACK_WEAKENED")
        require(errors, free.get("together_forbidden") is True or free.get("together_general_inference") == "FORBIDDEN", "SUPERVISOR_TOGETHER_FENCE_MISSING")
        require(errors, _quarantined(free.get("external_llm_provider_execution")), "SUPERVISOR_PROVIDER_QUARANTINE_MISSING")
        promotion = supervisor.get("promotion_state") or supervisor.get("promotion") or {}
        require(errors, promotion.get("entityos_whole_runtime_pass") is False, "SUPERVISOR_WHOLE_PASS_PREMATURE")
        require(errors, promotion.get("hcu_full_runtime_pass") is False, "SUPERVISOR_HCU_PASS_PREMATURE")
        require(errors, promotion.get("training_credit") == 0, "SUPERVISOR_TRAINING_CREDIT_NONZERO")
        require(errors, promotion.get("provider_runtime_credit", 0) == 0, "SUPERVISOR_PROVIDER_CREDIT_NONZERO")

        require(errors, provider_admission.get("schema") == PROVIDER_SCHEMA, "PROVIDER_ADMISSION_SCHEMA_MISMATCH")
        require(errors, str(provider_admission.get("authority_epoch")) == expected_version, "PROVIDER_ADMISSION_EPOCH_MISMATCH")
        require(errors, provider_admission.get("mode") == "FREE_ONLY", "PROVIDER_ADMISSION_MODE_MISMATCH")
        require(errors, provider_admission.get("product") == CURRENT_PRODUCT, "PROVIDER_ADMISSION_PRODUCT_MISMATCH")
        require(errors, provider_admission.get("compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROVIDER_ADMISSION_ARCHITECTURE_MISMATCH")
        providers = provider_admission.get("providers") or {}
        expected_providers = set(str(x) for x in bootstrap.get("free_provider_allowlist_current") or [])
        require(errors, bool(expected_providers), "BOOTSTRAP_FREE_PROVIDER_ALLOWLIST_EMPTY")
        require(errors, expected_providers.issubset(set(providers)), "PROVIDER_ADMISSION_ALLOWLIST_INCOMPLETE")
        for name in sorted(expected_providers):
            record = providers.get(name) or {}
            if record.get("admitted") is True:
                require(errors, record.get("cost_class") == "FREE", f"PROVIDER_ADMISSION_NONFREE_SELF_ADMIT:{name}")
        require(errors, provider_admission.get("runtime_provider_credit") == 0, "PROVIDER_ADMISSION_RUNTIME_CREDIT_NONZERO")
        require(errors, _quarantined(provider_admission.get("execution_state")), "PROVIDER_ADMISSION_EXECUTION_QUARANTINE_MISSING")

        root_text = paths["repo_claude"].read_text(encoding="utf-8")
        require(errors, PurePosixPath(authority_path).name in root_text, "ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING")
        current_protocol = bootstrap.get("all_worker_protocol")
        require(errors, isinstance(current_protocol, str) and current_protocol in root_text, "ROOT_CLAUDE_CURRENT_WORKER_DIRECTIVE_MISSING")

    _validate_legacy_safety_ancestry(errors, root)

    architecture = paths["architecture"].read_text(encoding="utf-8").upper()
    readme = paths["readme"].read_text(encoding="utf-8").upper()
    require(errors, "ENTITYOS" in architecture[:3000] and "HCU" in architecture[:3000], "ARCHITECTURE_ENTITYOS_HCU_MISSING")
    require(errors, "CLAYVERSE IS THE PRODUCT ENDPOINT" not in architecture[:3000], "ARCHITECTURE_STALE_CLAYVERSE_PRODUCT_AUTHORITY")
    require(errors, "ENTITYOS" in readme[:3000] and "HCU" in readme[:3000], "README_ENTITYOS_HCU_MISSING")

    return {
        "schema": CURRENT_SCHEMA,
        "pass": not errors,
        "errors": errors,
        "resolved_authority": authority_path,
        "resolved_authority_schema": supervisor.get("schema_version") if supervisor else None,
        "resolved_owner_authority": next(iter(owner_values.values())) if len(set(owner_values.values())) == 1 else None,
        "provider_admission_epoch": provider_admission.get("authority_epoch"),
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
