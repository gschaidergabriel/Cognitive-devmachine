#!/usr/bin/env python3
"""Successor-aware fail-closed authority guard for current EntityOS + HCU.

Compatibility filename retained for existing callers. Current authority is resolved from
canonical pointers instead of a frozen supervisor minor version. Historical ClayVerse-era
controls are checked only as immutable safety/provenance ancestry; they are never revived as
current product or execution-selection authority.
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
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v4"
AUTHORITY_RE = re.compile(r"^research_entity/claycode/autonomous/SUPERVISOR_STEERING_(\d+)_(\d+)\.json$")
OWNER_RE = re.compile(r"^governance/[A-Za-z0-9._/-]+\.md$")
PROVIDER_ADMISSION = "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
ROOT_CLAUDE = "CLAUDE.md"
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


def _safe_repo_path(value: object, pattern: re.Pattern[str]) -> str | None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        return None
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts:
        return None
    return value


def _authority_version_from_path(path: str) -> str:
    match = AUTHORITY_RE.fullmatch(path)
    assert match
    return f"{int(match.group(1))}.{int(match.group(2)):02d}"


def _credit_zero(errors: list[str], obj: dict, prefix: str) -> None:
    for key in ("entityos_hcu_whole_runtime_credit", "hcu_full_runtime_credit", "jspace_model_runtime_credit", "training_credit"):
        require(errors, obj.get(key, 0) == 0, f"{prefix}_{key.upper()}_NONZERO")
    require(errors, obj.get("whole_product_pass", False) is False, f"{prefix}_WHOLE_PASS_PREMATURE")


def _validate_legacy_safety_ancestry(errors: list[str], root: Path) -> None:
    """Check historical bytes/fences as provenance, not current execution authority."""
    paths = {"c41": root / CONTROL41, "c42": root / CONTROL42, "c43": root / CONTROL43, "c44": root / CONTROL44}
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING_LEGACY:{name}")
    if any(not p.is_file() for p in paths.values()):
        return
    try:
        c41, c42, c43, c44 = (load_json(paths[k]) for k in ("c41", "c42", "c43", "c44"))
    except (OSError, json.JSONDecodeError):
        errors.append("LEGACY_JSON_LOAD_ERROR")
        return

    require(errors, c41.get("schema_version") == "4.1", "CONTROL41_VERSION_MISMATCH")
    require(errors, c41.get("status") == "ACTIVE" and c41.get("mode") == "FREE_ONLY", "CONTROL41_FREE_ONLY_WEAKENED")
    cycle41 = c41.get("cycle_policy") or {}
    require(errors, cycle41.get("paid_fallback") is False, "CONTROL41_PAID_FALLBACK_WEAKENED")
    require(errors, cycle41.get("automatic_subscription_upgrade") is False, "CONTROL41_AUTO_UPGRADE_WEAKENED")

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
    hard44 = c44.get("preserved_hard_rules") or {}
    require(errors, hard44.get("free_only") is True and hard44.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, hard44.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    override = c44.get("program_identity_override") or {}
    require(errors, override.get("product_endpoint") == "ClayVerse", "CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH")


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "inbox": root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
        "manifest": root / "the artefact/manifest.json",
        "provider_admission": root / PROVIDER_ADMISSION,
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

    # Identity/product/effect invariants.
    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    identity = bootstrap.get("identity") or {}
    require(errors, identity.get("persistent_research_entity") == "Clay", "BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors, identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "BOOTSTRAP_TEMP_WORKER_ROLE_MISMATCH")
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "BOOTSTRAP_HCU_MISMATCH")
    require(errors, bootstrap.get("free_only") is True, "BOOTSTRAP_FREE_ONLY_MISSING")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_WEAKENED")
    require(errors, "FORBIDDEN" in str(bootstrap.get("together_api", "")), "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")

    require(errors, program.get("program_id") == "entityos-hcu" and program.get("status") == "ACTIVE", "PROGRAM_ID_OR_STATUS_MISMATCH")
    require(errors, program.get("stage") == CURRENT_STAGE and program.get("current_stage") == CURRENT_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("product") == CURRENT_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(errors, program.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROGRAM_HCU_MISMATCH")
    pauthority = program.get("authority") or {}
    require(errors, pauthority.get("external_effects") == "EffectGate+EffectJournal", "PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    require(errors, pauthority.get("second_persistent_identity") == "FORBIDDEN", "PROGRAM_SECOND_IDENTITY_NOT_FORBIDDEN")
    require(errors, pauthority.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN", "PROGRAM_SECOND_AUTHORITY_NOT_FORBIDDEN")

    # Successor-dynamic supervisor pointer consensus.
    raw_pointers = {
        "bootstrap": bootstrap.get("authority_correction"),
        "program": program.get("authority_correction"),
        "manifest": manifest.get("authority_correction"),
        "inbox": inbox.get("steering"),
    }
    pointers = {name: _safe_repo_path(value, AUTHORITY_RE) for name, value in raw_pointers.items()}
    for name, value in pointers.items():
        require(errors, value is not None, f"AUTHORITY_POINTER_INVALID:{name}")
    valid = [value for value in pointers.values() if value is not None]
    authority_path = valid[0] if valid else None
    require(errors, len(valid) == len(pointers) and len(set(valid)) == 1, "AUTHORITY_POINTER_SPLIT_BRAIN")

    supervisor = None
    expected_version = None
    if authority_path is not None:
        target = root / authority_path
        require(errors, target.is_file(), "AUTHORITY_TARGET_MISSING")
        if target.is_file():
            try:
                supervisor = load_json(target)
            except (OSError, json.JSONDecodeError):
                errors.append("AUTHORITY_TARGET_JSON_LOAD_ERROR")
    if supervisor is not None and authority_path is not None:
        expected_version = _authority_version_from_path(authority_path)
        require(errors, str(supervisor.get("schema_version")) == expected_version, "AUTHORITY_FILENAME_SCHEMA_MISMATCH")
        require(errors, (supervisor.get("active_program") or supervisor.get("program")) == CURRENT_PROGRAM, "SUPERVISOR_PROGRAM_MISMATCH")
        require(errors, supervisor.get("product") == CURRENT_PRODUCT, "SUPERVISOR_PRODUCT_MISMATCH")
        require(errors, supervisor.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "SUPERVISOR_HCU_MISMATCH")
        free = supervisor.get("free_only") or supervisor.get("free_only_policy") or {}
        require(errors, free.get("enabled", True) is True, "SUPERVISOR_FREE_ONLY_DISABLED")
        require(errors, free.get("no_paid_fallback") is True, "SUPERVISOR_PAID_FALLBACK_WEAKENED")
        require(errors, free.get("together_forbidden") is True or free.get("together_general_inference") == "FORBIDDEN", "SUPERVISOR_TOGETHER_FENCE_MISSING")
        promotion = supervisor.get("promotion") or supervisor.get("promotion_state") or {}
        require(errors, promotion.get("entityos_whole_runtime_pass", False) is False, "SUPERVISOR_WHOLE_PASS_PREMATURE")
        require(errors, promotion.get("hcu_full_runtime_pass", False) is False, "SUPERVISOR_HCU_PASS_PREMATURE")
        require(errors, promotion.get("training_credit", 0) == 0, "SUPERVISOR_TRAINING_CREDIT_NONZERO")
    else:
        free = {}

    # Explicit owner authority consensus. Manifest is included only when it carries a pointer.
    inbox_exec = inbox.get("execution_authority") or {}
    raw_owner = {
        "bootstrap": bootstrap.get("active_owner_authority"),
        "program": program.get("active_owner_authority"),
        "inbox": inbox_exec.get("active_owner_authority"),
    }
    if manifest.get("active_owner_authority") is not None:
        raw_owner["manifest"] = manifest.get("active_owner_authority")
    owner_paths = {name: _safe_repo_path(value, OWNER_RE) for name, value in raw_owner.items()}
    for name, value in owner_paths.items():
        require(errors, value is not None, f"OWNER_POINTER_INVALID:{name}")
    owner_valid = [value for value in owner_paths.values() if value is not None]
    owner_path = owner_valid[0] if owner_valid else None
    require(errors, len(owner_valid) == len(owner_paths) and len(set(owner_valid)) == 1, "OWNER_POINTER_SPLIT_BRAIN")
    if owner_path is not None:
        owner_file = root / owner_path
        require(errors, owner_file.is_file(), "OWNER_AUTHORITY_TARGET_MISSING")
        if owner_file.is_file():
            owner_text = owner_file.read_text(encoding="utf-8").upper()
            require(errors, "STATUS: ACTIVE USER AUTHORITY" in owner_text, "OWNER_AUTHORITY_NOT_ACTIVE")
            require(errors, "CLAY-DIRECT-DEV" in owner_text and "LOCAL" in owner_text, "OWNER_DUAL_MACHINE_AUTHORITY_MISSING")

    # Current dual-machine + provider-gated execution semantics.
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(errors, execution.get("authorized_zero_cost_local_normal_user_execution") is True, "PROGRAM_LOCAL_ZERO_COST_AUTHORITY_MISSING")
    require(errors, execution.get("authorized_clay_direct_dev_vps_sandbox_execution") is True, "PROGRAM_CLAY_DIRECT_DEV_AUTHORITY_MISSING")
    require(errors, execution.get("local_root_or_sudo_new_authority_implied") is False, "PROGRAM_ROOT_AUTHORITY_WEAKENED")
    require(errors, execution.get("unrelated_vps_host_changes_allowed") is False, "PROGRAM_VPS_HOST_BOUNDARY_WEAKENED")
    require(errors, execution.get("production_host_testing_forbidden") is True, "PROGRAM_PRODUCTION_TEST_FENCE_MISSING")
    require(errors, execution.get("other_paid_fallback") is False, "PROGRAM_PAID_FALLBACK_WEAKENED")
    provider_rule = str(execution.get("external_provider_admission_rule", ""))
    require(errors, "ADMITTED_TRUE" in provider_rule and "COST_CLASS_FREE" in provider_rule and "SECRET" in provider_rule and "NETWORK" in provider_rule, "PROGRAM_PROVIDER_PREIO_GATE_MISSING")
    _credit_zero(errors, program.get("runtime_credit") or {}, "PROGRAM")

    require(errors, manifest.get("artifact") == CURRENT_PRODUCT and manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_MISMATCH")
    require(errors, manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "MANIFEST_HCU_MISMATCH")
    require(errors, manifest.get("stage") == CURRENT_STAGE, "MANIFEST_STAGE_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    mexec = manifest.get("execution_policy") or {}
    require(errors, mexec.get("active_supervisor_free_only") is True or mexec.get("free_only_default") is True, "MANIFEST_FREE_ONLY_MISSING")
    require(errors, mexec.get("authorized_zero_cost_local_normal_user_execution") is True, "MANIFEST_LOCAL_ZERO_COST_AUTHORITY_MISSING")
    require(errors, mexec.get("authorized_clay_direct_dev_vps_sandbox_execution") is True, "MANIFEST_CLAY_DIRECT_DEV_AUTHORITY_MISSING")
    require(errors, mexec.get("production_host_testing_forbidden") is True, "MANIFEST_PRODUCTION_TEST_FENCE_MISSING")
    require(errors, mexec.get("other_paid_fallback") is False, "MANIFEST_PAID_FALLBACK_WEAKENED")
    _credit_zero(errors, manifest.get("runtime_credit") or {}, "MANIFEST")

    # Canonical typed FREE-provider admission must match current authority and allowlist.
    require(errors, provider_admission.get("schema") == "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1", "PROVIDER_ADMISSION_SCHEMA_MISMATCH")
    require(errors, provider_admission.get("mode") == "FREE_ONLY", "PROVIDER_ADMISSION_MODE_MISMATCH")
    if expected_version is not None:
        require(errors, str(provider_admission.get("authority_epoch")) == expected_version, "PROVIDER_ADMISSION_AUTHORITY_DRIFT")
    providers = provider_admission.get("providers") or {}
    allowlist = bootstrap.get("free_provider_allowlist_current") or []
    require(errors, set(providers) == set(allowlist), "PROVIDER_ADMISSION_ALLOWLIST_SPLIT")
    for provider, row in providers.items():
        require(errors, isinstance(row, dict), f"PROVIDER_ROW_INVALID:{provider}")
        if isinstance(row, dict):
            cost = row.get("cost_class")
            admitted = row.get("admitted")
            require(errors, cost in {"FREE", "UNKNOWN", "PAID", "SUBSCRIPTION"}, f"PROVIDER_COST_CLASS_INVALID:{provider}")
            require(errors, not admitted or cost == "FREE", f"PROVIDER_SELF_ADMISSION_NOT_FREE:{provider}")
    quarantine = str(free.get("external_llm_provider_execution", ""))
    if "QUARANTINED" in quarantine:
        require(errors, "QUARANTINED" in str(provider_admission.get("execution_state", "")), "PROVIDER_QUARANTINE_STATE_MISMATCH")

    _validate_legacy_safety_ancestry(errors, root)

    # Current-facing orientation must follow successor authority and owner law.
    readme = paths["readme"].read_text(encoding="utf-8")
    claude = paths["repo_claude"].read_text(encoding="utf-8")
    if authority_path is not None:
        basename = PurePosixPath(authority_path).name
        require(errors, basename in readme, "README_CURRENT_SUPERVISOR_MISSING")
        require(errors, basename.replace(".json", "") in claude, "ROOT_CLAUDE_CURRENT_SUPERVISOR_MISSING")
    for name, text in (("README", readme), ("ROOT_CLAUDE", claude)):
        upper = text.upper()
        require(errors, "ENTITYOS" in upper and "HCU" in upper and "FREE_ONLY" in upper, f"{name}_CURRENT_IDENTITY_MISSING")
        require(errors, "CLAY-DIRECT-DEV" in upper, f"{name}_CLAY_DIRECT_DEV_AUTHORITY_MISSING")
        require(errors, "VPS/SELF-HOSTED/PRODUCTION-HOST TESTING IS FORBIDDEN UNDER CURRENT CONTROL" not in upper, f"{name}_STALE_BLANKET_VPS_BAN")
        require(errors, "VPS, SELF-HOSTED AND PRODUCTION-HOST TESTING ARE FORBIDDEN" not in upper, f"{name}_STALE_BLANKET_VPS_BAN")

    return {
        "schema": CURRENT_SCHEMA,
        "pass": not errors,
        "errors": errors,
        "resolved": {
            "supervisor": authority_path,
            "supervisor_version": expected_version,
            "owner_authority": owner_path,
            "provider_admission": PROVIDER_ADMISSION,
        },
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
