#!/usr/bin/env python3
"""Fail-closed source validator for AGENT_ZERO_DISTRIBUTED_COGNITIVE_PROCESS_CENSUS/v1.

This validates the census contract only. PASS does not grant EntityOS/HCU runtime,
model, J-Space, training, distributed-execution, or final-acceptance credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "AGENT_ZERO_DISTRIBUTED_COGNITIVE_PROCESS_CENSUS/v1"
OWNER_TARGET = "UNBOUNDED_AGENT_ZERO_COGNITIVE_GRID"
DIMENSIONS = set(range(1, 15))
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


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CensusValidationError(f"CENSUS_READ_OR_JSON_FAILED:{exc}") from exc
    need(isinstance(value, dict), "CENSUS_OBJECT_REQUIRED")
    return value


def validate(value: dict[str, Any]) -> dict[str, Any]:
    need(value.get("schema") == SCHEMA, "SCHEMA_MISMATCH")
    need(value.get("status") == "CANDIDATE_SOURCE_CONTRACT_NOT_RUNTIME_CREDIT", "STATUS_MUST_DENY_RUNTIME_CREDIT")

    authority = value.get("authority")
    need(isinstance(authority, dict), "AUTHORITY_OBJECT_REQUIRED")
    need(authority.get("owner_target") == OWNER_TARGET, "OWNER_TARGET_MISMATCH")
    need(authority.get("grid_size_law") == "SIZE_INDEPENDENT_DYNAMIC_N_GRID10_TEST_FIXTURE_ONLY", "GRID_SIZE_LAW_MISMATCH")
    base = authority.get("base_main_sha")
    need(isinstance(base, str) and len(base) == 40 and all(c in "0123456789abcdef" for c in base), "BASE_MAIN_SHA_REQUIRED")

    definition = value.get("definition")
    need(isinstance(definition, dict), "DEFINITION_REQUIRED")
    need("not persistent agents or personalities" in definition.get("identity_rule", ""), "PROCESS_NOT_AGENT_IDENTITY_RULE_REQUIRED")
    need("independent of physical node identity and grid size" in definition.get("scale_rule", ""), "SIZE_INDEPENDENCE_RULE_REQUIRED")

    declared_dimensions = value.get("acceptance_dimensions")
    need(isinstance(declared_dimensions, dict), "ACCEPTANCE_DIMENSIONS_OBJECT_REQUIRED")
    need({int(k) for k in declared_dimensions} == DIMENSIONS, "OWNER_ACCEPTANCE_DIMENSIONS_1_TO_14_REQUIRED")

    processes = value.get("processes")
    need(isinstance(processes, list) and processes, "PROCESS_LIST_REQUIRED")
    ids: list[str] = []
    names: list[str] = []
    covered: set[int] = set()
    sole_effect_paths: list[str] = []
    optional_jspace = False

    for process in processes:
        need(isinstance(process, dict), "PROCESS_OBJECT_REQUIRED")
        missing = REQUIRED_FIELDS - set(process)
        need(not missing, f"PROCESS_FIELDS_MISSING:{sorted(missing)}")
        pid = process["id"]
        name = process["name"]
        need(isinstance(pid, str) and pid.startswith("AZP") and pid[3:].isdigit(), "PROCESS_ID_INVALID")
        need(isinstance(name, str) and name, f"{pid}:PROCESS_NAME_REQUIRED")
        ids.append(pid); names.append(name)
        for field in ("triggers", "inputs", "outputs", "legacy_sources", "evidence_class", "acceptance_dimensions"):
            need(isinstance(process[field], list) and process[field], f"{pid}:{field}:NONEMPTY_LIST_REQUIRED")
        need(isinstance(process["state_access"], dict), f"{pid}:STATE_ACCESS_OBJECT_REQUIRED")
        need(set(process["state_access"]) == {"S0", "S1", "S2"}, f"{pid}:S0_S1_S2_ACCESS_REQUIRED")
        need(isinstance(process["falsifier"], str) and len(process["falsifier"].strip()) >= 24, f"{pid}:FALSIFIER_REQUIRED")
        dims = set(process["acceptance_dimensions"])
        need(dims <= DIMENSIONS, f"{pid}:UNKNOWN_ACCEPTANCE_DIMENSION")
        covered |= dims
        if process["effect_authority"] == "SOLE_REAL_EFFECT_PATH":
            sole_effect_paths.append(pid)
            need(process["layer"] == "DETERMINISTIC_BOUNDARY", f"{pid}:REAL_EFFECT_PATH_MUST_BE_DETERMINISTIC_BOUNDARY")
        elif process["layer"].startswith("AGENT_ZERO_SEMANTIC"):
            need(process["effect_authority"] in {"NONE", "PROPOSE_ONLY"}, f"{pid}:COGNITIVE_PROCESS_HAS_EFFECT_AUTHORITY")
        if process["name"] == "JSPACE_MEASUREMENT_CONTROL_RESEARCH":
            optional_jspace = process["layer"] == "AGENT_ZERO_SEMANTIC_OPTIONAL" and 8 in dims

    need(len(ids) == len(set(ids)), "DUPLICATE_PROCESS_ID")
    need(len(names) == len(set(names)), "DUPLICATE_PROCESS_NAME")
    need(covered == DIMENSIONS, f"UNCOVERED_OWNER_DIMENSIONS:{sorted(DIMENSIONS - covered)}")
    need(sole_effect_paths == ["AZP12"], f"SOLE_EFFECT_PATH_MUST_BE_AZP12:{sole_effect_paths}")
    need(optional_jspace, "JSPACE_MUST_REMAIN_OPTIONAL_AND_CAUSAL_GATED")
    need(value.get("next_owner_gate") == "COGNITIVE_PROCESS_ABI", "NEXT_OWNER_GATE_MISMATCH")

    return {
        "ok": True,
        "schema": SCHEMA,
        "process_count": len(processes),
        "covered_acceptance_dimensions": sorted(covered),
        "sole_real_effect_process": sole_effect_paths[0],
        "next_owner_gate": value["next_owner_gate"],
        "credit_scope": "CENSUS_SOURCE_CONTRACT_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="research_entity/global/AGENT_ZERO_DISTRIBUTED_COGNITIVE_PROCESS_CENSUS_v1.json")
    args = parser.parse_args()
    try:
        result = validate(load(Path(args.path)))
    except CensusValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
