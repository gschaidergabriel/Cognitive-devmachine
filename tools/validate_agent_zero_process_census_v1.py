#!/usr/bin/env python3
"""Fail-closed composite validator for the current Zero+EntityOS cognitive census.

The historical 20-process Agent-Zero census is treated as a structural donor.
Current authority is supplied only by ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_OVERLAY/v1.

PASS is source-contract evidence only. It grants no distributed runtime, HCU,
EntityOS, J-Space-model, Claude latent-access, training, provider, or whole-product credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BASE_SCHEMA = "AGENT_ZERO_DISTRIBUTED_COGNITIVE_PROCESS_CENSUS/v1"
OVERLAY_SCHEMA = "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_OVERLAY/v1"
COMPOSITE_SCHEMA = "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1"
OWNER_COMMIT = "bdf2b44548a924bbf1c89a8dab26903db0a71cd0"
OWNER_PATH = "research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md"
GRID_LAW = "VARIABLE_N_RUNTIME_PARAMETER_GRID10_OPTIONAL_BENCHMARK_CONFIGURATION"
FUNCTIONAL_DIMS = set(range(1, 15))
CURRENT_OWNER_ACCEPTANCE = set(range(1, 11))
BASE_IDS = {f"AZP{i:02d}" for i in range(1, 21)}
DELTA_IDS = {"AZP21", "AZP22"}
ALL_IDS = BASE_IDS | DELTA_IDS
REQUIRED_FIELDS = {
    "id", "name", "layer", "role", "triggers", "inputs", "outputs",
    "state_access", "effect_authority", "distribution", "legacy_sources",
    "evidence_class", "acceptance_dimensions", "falsifier",
}


class CensusValidationError(ValueError):
    pass


def need(ok: bool, message: str) -> None:
    if not ok:
        raise CensusValidationError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CensusValidationError(f"READ_OR_JSON_FAILED:{path}:{exc}") from exc
    need(isinstance(value, dict), f"OBJECT_REQUIRED:{path}")
    return value


def validate_process(process: dict[str, Any], allowed_ids: set[str]) -> set[int]:
    need(isinstance(process, dict), "PROCESS_OBJECT_REQUIRED")
    missing = REQUIRED_FIELDS - set(process)
    need(not missing, f"PROCESS_FIELDS_MISSING:{sorted(missing)}")
    pid = process["id"]
    need(pid in allowed_ids, f"PROCESS_ID_INVALID:{pid}")
    need(isinstance(process["name"], str) and process["name"], f"{pid}:PROCESS_NAME_REQUIRED")
    for field in ("triggers", "inputs", "outputs", "legacy_sources",
                  "evidence_class", "acceptance_dimensions"):
        need(isinstance(process[field], list) and process[field],
             f"{pid}:{field}:NONEMPTY_LIST_REQUIRED")
    need(isinstance(process["state_access"], dict) and
         set(process["state_access"]) == {"S0", "S1", "S2"},
         f"{pid}:S0_S1_S2_ACCESS_REQUIRED")
    need(isinstance(process["falsifier"], str) and len(process["falsifier"].strip()) >= 32,
         f"{pid}:FALSIFIER_REQUIRED")
    dims = set(process["acceptance_dimensions"])
    need(dims <= FUNCTIONAL_DIMS, f"{pid}:UNKNOWN_FUNCTIONAL_DIMENSION")
    return dims


def validate(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    # Structural donor only: its stale owner pointer is deliberately not current authority.
    need(base.get("schema") == BASE_SCHEMA, "BASE_SCHEMA_MISMATCH")
    need(base.get("status") == "CANDIDATE_SOURCE_CONTRACT_NOT_RUNTIME_CREDIT",
         "BASE_STATUS_MUST_DENY_RUNTIME_CREDIT")
    base_processes = base.get("processes")
    need(isinstance(base_processes, list), "BASE_PROCESS_LIST_REQUIRED")
    base_ids: list[str] = []
    base_names: list[str] = []
    covered: set[int] = set()
    sole_effect_paths: list[str] = []
    for process in base_processes:
        covered |= validate_process(process, BASE_IDS)
        base_ids.append(process["id"])
        base_names.append(process["name"])
        if process["effect_authority"] == "SOLE_REAL_EFFECT_PATH":
            sole_effect_paths.append(process["id"])
            need(process["layer"] == "DETERMINISTIC_BOUNDARY",
                 f"{process['id']}:REAL_EFFECT_PATH_MUST_BE_DETERMINISTIC_BOUNDARY")
    need(set(base_ids) == BASE_IDS, "BASE_PROCESS_ID_SET_MISMATCH")
    need(len(base_ids) == len(set(base_ids)), "DUPLICATE_BASE_PROCESS_ID")
    need(len(base_names) == len(set(base_names)), "DUPLICATE_BASE_PROCESS_NAME")
    need(covered == FUNCTIONAL_DIMS, "BASE_FUNCTIONAL_DIMENSION_COVERAGE_INCOMPLETE")
    need(sole_effect_paths == ["AZP12"], f"SOLE_EFFECT_PATH_MUST_BE_AZP12:{sole_effect_paths}")
    jspace = next(p for p in base_processes if p["id"] == "AZP09")
    need("OPTIONAL" in jspace["layer"], "JSPACE_MUST_REMAIN_OPTIONAL_AND_CAUSAL_GATED")

    # Current owner authority lives only in the overlay.
    need(overlay.get("schema") == OVERLAY_SCHEMA, "OVERLAY_SCHEMA_MISMATCH")
    need(overlay.get("composite_schema") == COMPOSITE_SCHEMA, "COMPOSITE_SCHEMA_MISMATCH")
    need(overlay.get("status") == "CURRENT_OWNER_COMPOSITE_SOURCE_CONTRACT_NOT_RUNTIME_CREDIT",
         "OVERLAY_STATUS_MUST_DENY_RUNTIME_CREDIT")
    base_ref = overlay.get("base_census")
    need(isinstance(base_ref, dict), "BASE_CENSUS_REF_REQUIRED")
    need(base_ref.get("schema") == BASE_SCHEMA, "BASE_CENSUS_REF_SCHEMA_MISMATCH")
    need("STALE OWNER POINTER IS NOT CURRENT AUTHORITY" in base_ref.get("role", ""),
         "BASE_STALE_AUTHORITY_MUST_BE_EXPLICIT")

    authority = overlay.get("authority")
    need(isinstance(authority, dict), "CURRENT_AUTHORITY_OBJECT_REQUIRED")
    need(authority.get("owner_target_commit") == OWNER_COMMIT, "OWNER_COMMIT_MISMATCH")
    need(authority.get("owner_target_path") == OWNER_PATH, "OWNER_PATH_MISMATCH")
    need(authority.get("grid_size_law") == GRID_LAW, "GRID_SIZE_LAW_MISMATCH")
    need(authority.get("database_boundary_rule") == "SIMULATE_COGNITION_STORE_DURABLE_DATA",
         "DATABASE_BOUNDARY_RULE_MISMATCH")
    need(authority.get("strong_model_rule") ==
         "CLAUDE_CODE_REMAINS_MAIN_STRONG_MODEL_TOOL_CODE_PARTNER",
         "CLAUDE_CODE_ROLE_MISMATCH")
    need(authority.get("latent_access_rule") ==
         "NO_UNPROVEN_CLAUDE_CODE_ACTIVATION_ACCESS_CLAIM",
         "CLAUDE_LATENT_ACCESS_RULE_MISMATCH")

    delta = overlay.get("delta_processes")
    need(isinstance(delta, list), "DELTA_PROCESS_LIST_REQUIRED")
    delta_ids: list[str] = []
    delta_names: list[str] = []
    for process in delta:
        validate_process(process, DELTA_IDS)
        delta_ids.append(process["id"])
        delta_names.append(process["name"])
        need(process["effect_authority"] != "SOLE_REAL_EFFECT_PATH",
             f"{process['id']}:DELTA_CANNOT_CREATE_SECOND_REAL_EFFECT_PATH")
    need(set(delta_ids) == DELTA_IDS, "DELTA_PROCESS_ID_SET_MISMATCH")
    need(len(delta_ids) == len(set(delta_ids)), "DUPLICATE_DELTA_PROCESS_ID")
    need(len(delta_names) == len(set(delta_names)), "DUPLICATE_DELTA_PROCESS_NAME")

    db_boundary = next(p for p in delta if p["id"] == "AZP21")
    need(db_boundary["name"] == "DURABLE_DATA_SIMULATION_BOUNDARY",
         "AZP21_DB_BOUNDARY_NAME_REQUIRED")
    need(db_boundary["layer"] == "DETERMINISTIC_BOUNDARY",
         "AZP21_DB_BOUNDARY_MUST_BE_DETERMINISTIC")
    need(db_boundary["effect_authority"] == "NONE",
         "AZP21_DB_BOUNDARY_CANNOT_GAIN_EFFECT_AUTHORITY")

    bridge = next(p for p in delta if p["id"] == "AZP22")
    need(bridge["name"] == "CLAUDE_CODE_WORKSPACE_BRIDGE",
         "AZP22_CLAUDE_BRIDGE_NAME_REQUIRED")
    need(bridge["effect_authority"] == "PROPOSE_ONLY",
         "AZP22_CLAUDE_BRIDGE_MUST_REMAIN_CANDIDATE_ONLY")
    need("NO_HIDDEN_STATE_AUTHORITY" in bridge["distribution"],
         "CLAUDE_BRIDGE_MUST_DENY_HIDDEN_STATE_AUTHORITY")
    need("exposed_interface_descriptor" in bridge["inputs"],
         "CLAUDE_BRIDGE_EXPOSED_INTERFACE_DESCRIPTOR_REQUIRED")

    current = overlay.get("current_owner_acceptance")
    need(isinstance(current, dict), "CURRENT_OWNER_ACCEPTANCE_OBJECT_REQUIRED")
    need({int(k) for k in current} == CURRENT_OWNER_ACCEPTANCE,
         "CURRENT_OWNER_ACCEPTANCE_1_TO_10_REQUIRED")
    for key, item in current.items():
        need(isinstance(item, dict), f"CURRENT_ACCEPTANCE_{key}:OBJECT_REQUIRED")
        refs = item.get("process_ids")
        need(isinstance(refs, list) and refs, f"CURRENT_ACCEPTANCE_{key}:PROCESS_IDS_REQUIRED")
        need(set(refs) <= ALL_IDS, f"CURRENT_ACCEPTANCE_{key}:UNKNOWN_PROCESS_REF")
    need("AZP21" in current["3"]["process_ids"], "OWNER_ACCEPTANCE_3_REQUIRES_DB_BOUNDARY")
    need("AZP21" in current["4"]["process_ids"], "OWNER_ACCEPTANCE_4_REQUIRES_DB_BOUNDARY")
    need("AZP22" in current["5"]["process_ids"], "OWNER_ACCEPTANCE_5_REQUIRES_CLAUDE_BRIDGE")
    need("AZP22" in current["6"]["process_ids"], "OWNER_ACCEPTANCE_6_REQUIRES_CLAUDE_BRIDGE")
    need({"AZP08", "AZP22"} <= set(current["7"]["process_ids"]),
         "OWNER_ACCEPTANCE_7_REQUIRES_WORKSPACE_AND_CLAUDE_REENTRY")
    need({"AZP09", "AZP22"} <= set(current["8"]["process_ids"]),
         "OWNER_ACCEPTANCE_8_REQUIRES_JSPACE_AND_INTERFACE_LIMITS")
    need("AZP20" in current["9"]["process_ids"], "OWNER_ACCEPTANCE_9_REQUIRES_END_TO_END_GATE")
    need({"AZP06", "AZP20"} <= set(current["10"]["process_ids"]),
         "OWNER_ACCEPTANCE_10_REQUIRES_08B_AND_PROTECTED_ACCEPTANCE")

    neg = overlay.get("negative_evidence")
    need(isinstance(neg, dict), "NEGATIVE_EVIDENCE_REQUIRED")
    need(neg.get("frozen_qwen06_structural_native_v1") ==
         "INTERNAL_STATE_TRANSPORT_PASS_ABSTRACT_BEHAVIORAL_CONTROL_FAIL",
         "FROZEN_V1_RESULT_MUST_BE_PRESERVED")
    need(neg.get("promotion_credit") == 0, "FROZEN_V1_MUST_NOT_MINT_PROMOTION_CREDIT")
    need(overlay.get("next_owner_gate") == "COGNITIVE_PROCESS_ABI",
         "NEXT_OWNER_GATE_MISMATCH")
    need(overlay.get("credit_scope") == "CENSUS_SOURCE_CONTRACT_ONLY",
         "CREDIT_SCOPE_MUST_REMAIN_SOURCE_ONLY")

    return {
        "ok": True,
        "schema": COMPOSITE_SCHEMA,
        "process_count": 22,
        "covered_functional_dimensions": sorted(covered),
        "covered_current_owner_acceptance": sorted(int(k) for k in current),
        "sole_real_effect_process": "AZP12",
        "database_boundary_process": "AZP21",
        "claude_code_bridge_process": "AZP22",
        "next_owner_gate": "COGNITIVE_PROCESS_ABI",
        "credit_scope": "CENSUS_SOURCE_CONTRACT_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        default="research_entity/global/AGENT_ZERO_DISTRIBUTED_COGNITIVE_PROCESS_CENSUS_v1.json",
    )
    parser.add_argument(
        "--overlay",
        default="research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_CURRENT_OWNER_OVERLAY_v1.json",
    )
    args = parser.parse_args()
    try:
        result = validate(read_json(Path(args.base)), read_json(Path(args.overlay)))
    except CensusValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
