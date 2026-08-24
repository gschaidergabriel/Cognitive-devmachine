#!/usr/bin/env python3
"""Successor-aware fail-closed authority guard for current EntityOS + HCU.

The compatibility filename is retained because existing workflows/receipts call it.
Current authority is resolved from pointer consensus instead of a hard-coded supervisor
minor version. Historical ClayVerse controls are ancestry only and cannot restore
obsolete current execution policy.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath

CURRENT_PROGRAM = "ENTITYOS_HCU"
CURRENT_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
CURRENT_PRODUCT = "EntityOS"
CURRENT_COMPUTE_ARCHITECTURE = "HCU"
CURRENT_SCHEMA = "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v4"
AUTHORITY_RE = re.compile(
    r"^research_entity/claycode/autonomous/SUPERVISOR_STEERING_(\d+)_(\d+)\.json$"
)
CANONICAL_PROVIDER_ADMISSION = "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
CONTROL41 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def safe_authority_path(value: object) -> str | None:
    if not isinstance(value, str) or not AUTHORITY_RE.fullmatch(value):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return value


def authority_version(path: str) -> str:
    match = AUTHORITY_RE.fullmatch(path)
    assert match
    return f"{int(match.group(1))}.{int(match.group(2)):02d}"


def _supervisor_program(supervisor: dict):
    return supervisor.get("active_program", supervisor.get("program"))


def _supervisor_free_only(supervisor: dict) -> dict:
    value = supervisor.get("free_only")
    if isinstance(value, dict):
        return value
    value = supervisor.get("free_only_policy")
    return value if isinstance(value, dict) else {}


def _supervisor_promotion(supervisor: dict) -> dict:
    value = supervisor.get("promotion")
    if isinstance(value, dict):
        return value
    value = supervisor.get("promotion_state")
    return value if isinstance(value, dict) else {}


def _validate_legacy_ancestry(errors: list[str], root: Path) -> None:
    """Preserve donor safety ancestry without making legacy VPS/product law current."""
    specs = (
        (CONTROL41, "4.1"),
        (CONTROL42, "4.2-execution-boundary-addendum"),
        (CONTROL43, "4.3-program-authority-addendum"),
        (CONTROL44, "4.4-clayverse-product-authority-addendum"),
    )
    loaded: dict[str, dict] = {}
    for rel, version in specs:
        path = root / rel
        require(errors, path.is_file(), f"LEGACY_MISSING:{rel}")
        if not path.is_file():
            continue
        try:
            obj = load_json(path)
        except (OSError, json.JSONDecodeError):
            errors.append(f"LEGACY_JSON_INVALID:{rel}")
            continue
        loaded[rel] = obj
        require(errors, obj.get("schema_version") == version, f"LEGACY_VERSION:{rel}")

    c41 = loaded.get(CONTROL41, {})
    if c41:
        require(errors, c41.get("mode") == "FREE_ONLY", "LEGACY41_FREE_ONLY_WEAKENED")
        cycle = c41.get("cycle_policy") or {}
        require(errors, cycle.get("paid_fallback") is False, "LEGACY41_PAID_FALLBACK_WEAKENED")
        rules = set(c41.get("authority_rules") or [])
        require(errors, "model_output_is_candidate_not_truth" in rules, "LEGACY41_MODEL_TRUTH_FENCE_MISSING")

    c42 = loaded.get(CONTROL42, {})
    if c42:
        hard = c42.get("preserved_hard_rules") or {}
        require(errors, hard.get("free_only") is True, "LEGACY42_FREE_ONLY_WEAKENED")
        require(errors, hard.get("paid_fallback") is False, "LEGACY42_PAID_FALLBACK_WEAKENED")
        require(errors, hard.get("together_forbidden") is True, "LEGACY42_TOGETHER_WEAKENED")

    c43 = loaded.get(CONTROL43, {})
    if c43:
        hard = c43.get("preserved_hard_rules") or {}
        require(errors, hard.get("free_only") is True, "LEGACY43_FREE_ONLY_WEAKENED")
        require(errors, hard.get("paid_fallback") is False, "LEGACY43_PAID_FALLBACK_WEAKENED")
        require(errors, hard.get("model_output_is_candidate_not_truth") is True, "LEGACY43_MODEL_TRUTH_FENCE_MISSING")

    c44 = loaded.get(CONTROL44, {})
    if c44:
        override = c44.get("program_identity_override") or {}
        require(errors, override.get("product_endpoint") == "ClayVerse", "LEGACY44_PROVENANCE_MISMATCH")
        hard = c44.get("preserved_hard_rules") or {}
        require(errors, hard.get("free_only") is True, "LEGACY44_FREE_ONLY_WEAKENED")
        require(errors, hard.get("paid_fallback") is False, "LEGACY44_PAID_FALLBACK_WEAKENED")
        require(errors, hard.get("together_forbidden") is True, "LEGACY44_TOGETHER_WEAKENED")


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "inbox": root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
        "manifest": root / "the artefact/manifest.json",
        "provider_admission": root / CANONICAL_PROVIDER_ADMISSION,
        "claude": root / "CLAUDE.md",
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}")
    if errors:
        return {"schema": CURRENT_SCHEMA, "pass": False, "errors": errors}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        inbox = load_json(paths["inbox"])
        manifest = load_json(paths["manifest"])
        provider_admission = load_json(paths["provider_admission"])
        claude = paths["claude"].read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        return {
            "schema": CURRENT_SCHEMA,
            "pass": False,
            "errors": [f"CURRENT_SURFACE_LOAD_ERROR:{type(exc).__name__}"],
        }

    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "ENTITY_ID_SPLIT")
    identity = bootstrap.get("identity") or {}
    require(errors, identity.get("persistent_research_entity") == "Clay", "PERSISTENT_ENTITY_MISMATCH")
    require(errors, identity.get("temporary_worker") == "ORGAN_NOT_ENTITY", "WORKER_ROLE_MISMATCH")
    require(errors, bootstrap.get("active_program") == CURRENT_PROGRAM, "BOOTSTRAP_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == CURRENT_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == CURRENT_PRODUCT, "BOOTSTRAP_PRODUCT_MISMATCH")
    require(errors, bootstrap.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "BOOTSTRAP_COMPUTE_MISMATCH")
    require(errors, bootstrap.get("effect_authority") == "EffectGate+EffectJournal", "BOOTSTRAP_EFFECT_MISMATCH")
    require(errors, bootstrap.get("free_only") is True, "BOOTSTRAP_NOT_FREE_ONLY")
    require(errors, bootstrap.get("paid_fallback") == "FORBIDDEN", "BOOTSTRAP_PAID_FALLBACK_WEAKENED")
    require(errors, "FORBIDDEN" in str(bootstrap.get("together_api", "")), "BOOTSTRAP_TOGETHER_WEAKENED")

    require(errors, program.get("program_id") == "entityos-hcu" and program.get("status") == "ACTIVE", "PROGRAM_ID_OR_STATUS_MISMATCH")
    require(errors, program.get("stage") == CURRENT_STAGE and program.get("current_stage") == CURRENT_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("product") == CURRENT_PRODUCT, "PROGRAM_PRODUCT_MISMATCH")
    require(errors, program.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROGRAM_COMPUTE_MISMATCH")
    auth = program.get("authority") or {}
    require(errors, auth.get("external_effects") == "EffectGate+EffectJournal", "PROGRAM_EFFECT_MISMATCH")
    require(errors, auth.get("second_persistent_identity") == "FORBIDDEN", "PROGRAM_SECOND_IDENTITY")
    require(errors, auth.get("second_truth_effect_or_recovery_authority") == "FORBIDDEN", "PROGRAM_SECOND_AUTHORITY")

    pexec = program.get("execution_policy") or {}
    require(errors, pexec.get("free_only") is True, "PROGRAM_NOT_FREE_ONLY")
    require(errors, pexec.get("authorized_zero_cost_local_normal_user_execution") is True, "PROGRAM_LOCAL_NORMAL_USER_EXECUTION_DRIFT")
    require(errors, pexec.get("authorized_clay_direct_dev_vps_sandbox_execution") is True, "PROGRAM_CLAY_DIRECT_DEV_EXECUTION_DRIFT")
    require(errors, pexec.get("local_root_or_sudo_new_authority_implied") is False, "PROGRAM_ROOT_AUTHORITY_WEAKENED")
    require(errors, pexec.get("unrelated_vps_host_changes_allowed") is False, "PROGRAM_UNRELATED_VPS_HOST_WEAKENED")
    require(errors, pexec.get("production_host_testing_forbidden") is True, "PROGRAM_PRODUCTION_HOST_FENCE_WEAKENED")
    require(errors, pexec.get("external_provider_admission_file") == CANONICAL_PROVIDER_ADMISSION, "PROGRAM_PROVIDER_ADMISSION_PATH_DRIFT")
    require(errors, pexec.get("together_general_inference_and_fallback_forbidden") is True, "PROGRAM_TOGETHER_WEAKENED")
    require(errors, pexec.get("other_paid_fallback") is False, "PROGRAM_PAID_FALLBACK_WEAKENED")

    require(errors, manifest.get("artifact") == CURRENT_PRODUCT, "MANIFEST_ARTIFACT_MISMATCH")
    require(errors, manifest.get("product_endpoint") == CURRENT_PRODUCT, "MANIFEST_PRODUCT_MISMATCH")
    require(errors, manifest.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "MANIFEST_COMPUTE_MISMATCH")
    require(errors, manifest.get("effect_authority") == "EffectGate+EffectJournal", "MANIFEST_EFFECT_MISMATCH")
    mexec = manifest.get("execution_policy") or {}
    require(errors, mexec.get("active_supervisor_free_only") is True, "MANIFEST_NOT_FREE_ONLY")
    require(errors, mexec.get("authorized_zero_cost_local_normal_user_execution") is True, "MANIFEST_LOCAL_NORMAL_USER_EXECUTION_DRIFT")
    require(errors, mexec.get("authorized_clay_direct_dev_vps_sandbox_execution") is True, "MANIFEST_CLAY_DIRECT_DEV_EXECUTION_DRIFT")
    require(errors, mexec.get("external_provider_admission_file") == CANONICAL_PROVIDER_ADMISSION, "MANIFEST_PROVIDER_ADMISSION_PATH_DRIFT")
    require(errors, mexec.get("external_llm_provider_execution") == "QUARANTINED_UNTIL_FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT_V1_EXACT_SOURCE_PASS", "MANIFEST_PROVIDER_QUARANTINE_DRIFT")
    require(errors, mexec.get("together_general_inference_and_fallback_forbidden") is True, "MANIFEST_TOGETHER_WEAKENED")
    require(errors, mexec.get("other_paid_fallback") is False, "MANIFEST_PAID_FALLBACK_WEAKENED")

    raw_pointers = {
        "bootstrap": bootstrap.get("authority_correction"),
        "program": program.get("authority_correction"),
        "manifest": manifest.get("authority_correction"),
        "inbox": inbox.get("steering"),
    }
    pointers = {name: safe_authority_path(value) for name, value in raw_pointers.items()}
    for name, value in pointers.items():
        require(errors, value is not None, f"AUTHORITY_POINTER_INVALID:{name}")
    valid = [value for value in pointers.values() if value is not None]
    resolved = valid[0] if valid else None
    require(errors, len(valid) == len(pointers) and len(set(valid)) == 1, "AUTHORITY_POINTER_SPLIT_BRAIN")

    supervisor = None
    version = None
    if resolved is not None:
        version = authority_version(resolved)
        supervisor_path = root / resolved
        require(errors, supervisor_path.is_file(), "AUTHORITY_TARGET_MISSING")
        if supervisor_path.is_file():
            try:
                supervisor = load_json(supervisor_path)
            except (OSError, json.JSONDecodeError):
                errors.append("AUTHORITY_TARGET_JSON_INVALID")

    if supervisor is not None and resolved is not None and version is not None:
        require(errors, str(supervisor.get("schema_version")) == version, "AUTHORITY_FILENAME_SCHEMA_MISMATCH")
        require(errors, _supervisor_program(supervisor) == CURRENT_PROGRAM, "SUPERVISOR_PROGRAM_MISMATCH")
        require(errors, supervisor.get("product") == CURRENT_PRODUCT, "SUPERVISOR_PRODUCT_MISMATCH")
        require(errors, supervisor.get("integrated_cognition_compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "SUPERVISOR_COMPUTE_MISMATCH")
        free = _supervisor_free_only(supervisor)
        require(errors, free.get("enabled") is True or supervisor.get("mode") == "FREE_ONLY", "SUPERVISOR_NOT_FREE_ONLY")
        require(errors, free.get("no_paid_fallback") is True, "SUPERVISOR_PAID_FALLBACK_WEAKENED")
        require(errors, free.get("together_forbidden") is True, "SUPERVISOR_TOGETHER_WEAKENED")
        promotion = _supervisor_promotion(supervisor)
        require(errors, promotion.get("entityos_whole_runtime_pass") is False, "SUPERVISOR_WHOLE_PASS_PREMATURE")
        require(errors, promotion.get("hcu_full_runtime_pass") is False, "SUPERVISOR_HCU_PASS_PREMATURE")
        require(errors, promotion.get("training_credit", 0) == 0, "SUPERVISOR_TRAINING_CREDIT_NONZERO")
        require(errors, promotion.get("provider_runtime_credit", 0) == 0, "SUPERVISOR_PROVIDER_CREDIT_NONZERO")

        basename = PurePosixPath(resolved).stem
        directive = f"CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_{version.replace('.', '_')}.md"
        require(errors, f"AUTONOMOUS_SUPERVISOR={basename}" in claude, "CLAUDE_SUPERVISOR_POINTER_DRIFT")
        require(errors, PurePosixPath(resolved).name in claude, "CLAUDE_STEERING_PATH_DRIFT")
        require(errors, directive in claude, "CLAUDE_WORKER_DIRECTIVE_DRIFT")
        require(errors, "clay-direct-dev" in claude, "CLAUDE_DUAL_MACHINE_AUTHORITY_MISSING")
        require(errors, "QUARANTIN" in claude.upper(), "CLAUDE_PROVIDER_QUARANTINE_MISSING")

        allowlist = bootstrap.get("free_provider_allowlist_current")
        require(errors, isinstance(allowlist, list) and bool(allowlist), "BOOTSTRAP_PROVIDER_ALLOWLIST_MISSING")
        require(errors, provider_admission.get("schema") == "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1", "PROVIDER_ADMISSION_SCHEMA_MISMATCH")
        require(errors, str(provider_admission.get("authority_epoch")) == version, "PROVIDER_ADMISSION_EPOCH_MISMATCH")
        require(errors, provider_admission.get("mode") == "FREE_ONLY", "PROVIDER_ADMISSION_MODE_MISMATCH")
        require(errors, provider_admission.get("product") == CURRENT_PRODUCT, "PROVIDER_ADMISSION_PRODUCT_MISMATCH")
        require(errors, provider_admission.get("compute_architecture") == CURRENT_COMPUTE_ARCHITECTURE, "PROVIDER_ADMISSION_COMPUTE_MISMATCH")
        require(errors, provider_admission.get("source") == "ENTITYOS_HCU_CONTROL_PLANE", "PROVIDER_ADMISSION_SOURCE_MISMATCH")
        providers = provider_admission.get("providers")
        require(errors, isinstance(providers, dict), "PROVIDER_ADMISSION_PROVIDERS_INVALID")
        if isinstance(providers, dict) and isinstance(allowlist, list):
            require(errors, set(providers) == set(allowlist), "PROVIDER_ADMISSION_ALLOWLIST_SPLIT")
        require(errors, provider_admission.get("runtime_provider_credit") == 0, "PROVIDER_ADMISSION_RUNTIME_CREDIT_NONZERO")
        quarantined = "QUARANTIN" in str(free.get("external_llm_provider_execution", "") or provider_admission.get("execution_state", "")).upper()
        if quarantined and isinstance(providers, dict):
            for provider, row in providers.items():
                if not isinstance(row, dict):
                    errors.append(f"PROVIDER_ADMISSION_ROW_INVALID:{provider}")
                    continue
                require(errors, row.get("admitted") is False, f"PROVIDER_SELF_GRANT_WHILE_QUARANTINED:{provider}")
                require(errors, row.get("cost_class") == "UNKNOWN", f"PROVIDER_COST_CLASS_NOT_UNKNOWN_WHILE_QUARANTINED:{provider}")

    for surface, credit in (
        ("program", program.get("runtime_credit") or {}),
        ("manifest", manifest.get("runtime_credit") or {}),
    ):
        prefix = surface.upper()
        require(errors, credit.get("entityos_hcu_whole_runtime_credit") == 0, f"{prefix}_WHOLE_RUNTIME_CREDIT_NONZERO")
        require(errors, credit.get("hcu_full_runtime_credit") == 0, f"{prefix}_HCU_RUNTIME_CREDIT_NONZERO")
        require(errors, credit.get("jspace_model_runtime_credit") == 0, f"{prefix}_JSPACE_RUNTIME_CREDIT_NONZERO")
        require(errors, credit.get("training_credit") == 0, f"{prefix}_TRAINING_CREDIT_NONZERO")
        require(errors, credit.get("whole_product_pass") is False, f"{prefix}_WHOLE_PASS_PREMATURE")

    _validate_legacy_ancestry(errors, root)
    return {
        "schema": CURRENT_SCHEMA,
        "pass": not errors,
        "resolved_authority": resolved,
        "resolved_authority_epoch": version,
        "provider_admission": CANONICAL_PROVIDER_ADMISSION,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = validate(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
