#!/usr/bin/env python3
"""Fail-closed validation for the current Zero/EntityOS cognitive census + ABI source contracts.

This validates source-contract invariants only. It grants no variable-grid runtime,
Claude Code bridge, Global J-Space causal, whole EntityOS/HCU, or training credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_OWNER = "research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md"
EXPECTED_CENSUS = "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1"
EXPECTED_ABI = "COGNITIVE_PROCESS_ABI/v1"
EXPECTED_PROCESS_IDS = {f"ZECP{i:02d}" for i in range(1, 21)}
ALLOWED_CLASSES = {
    "SIMULATE_ON_GRID",
    "STORE_IN_DB",
    "DETERMINISTIC_BOUNDARY",
    "EXTERNAL_STRONG_MODEL_BRIDGE",
    "OPTIONAL_CAUSAL_RESEARCH",
}


def load(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def validate(census: dict, abi: dict) -> None:
    require(census.get("schema") == EXPECTED_CENSUS, "wrong census schema")
    require(abi.get("schema") == EXPECTED_ABI, "wrong ABI schema")
    require(census.get("authority", {}).get("owner_target_path") == EXPECTED_OWNER, "census owner authority drift")
    require(abi.get("authority", {}).get("owner_target_path") == EXPECTED_OWNER, "ABI owner authority drift")
    require(census.get("authority", {}).get("base_main_sha") == abi.get("authority", {}).get("base_main_sha"), "census/ABI base main mismatch")

    processes = census.get("processes")
    require(isinstance(processes, list), "processes must be a list")
    ids = [p.get("id") for p in processes if isinstance(p, dict)]
    require(set(ids) == EXPECTED_PROCESS_IDS and len(ids) == 20, "process IDs must be exactly ZECP01..ZECP20")
    require(len(ids) == len(set(ids)), "duplicate process id")

    dims = census.get("acceptance_dimensions")
    require(isinstance(dims, dict) and set(dims.keys()) == {str(i) for i in range(1, 11)}, "current owner acceptance dimensions must be exactly 1..10")
    covered = set()
    for p in processes:
        require(p.get("implementation_class") in ALLOWED_CLASSES, f"invalid implementation class for {p.get('id')}")
        pdims = p.get("acceptance_dimensions")
        require(isinstance(pdims, list) and pdims, f"missing acceptance coverage for {p.get('id')}")
        require(all(isinstance(x, int) and 1 <= x <= 10 for x in pdims), f"invalid acceptance dimension for {p.get('id')}")
        covered.update(pdims)
        require(p.get("inputs") and p.get("outputs"), f"empty typed surface for {p.get('id')}")
        require(p.get("falsifier"), f"missing falsifier for {p.get('id')}")
    require(covered == set(range(1, 11)), "all current owner acceptance dimensions must be covered")

    by_id = {p["id"]: p for p in processes}
    require(by_id["ZECP02"]["implementation_class"] == "STORE_IN_DB", "durable retrieval must remain DB-bound")
    require(by_id["ZECP13"]["implementation_class"] == "EXTERNAL_STRONG_MODEL_BRIDGE", "Claude handoff class drift")
    require(by_id["ZECP14"]["implementation_class"] == "EXTERNAL_STRONG_MODEL_BRIDGE", "Claude return class drift")
    require(by_id["ZECP17"]["authority"] == "REAL_EFFECT_AUTHORITY_ONLY", "ZECP17 effect authority drift")
    require(all(p["authority"] != "REAL_EFFECT_AUTHORITY_ONLY" for p in processes if p["id"] != "ZECP17"), "second real-effect authority detected")
    require(by_id["ZECP20"]["implementation_class"] == "OPTIONAL_CAUSAL_RESEARCH", "J-Space must remain evidence-gated")

    laws = census.get("laws", {})
    require(laws.get("grid_size") == "N_IS_RUNTIME_PARAMETER_GRID10_ONLY_OPTIONAL_BENCHMARK", "fixed-N regression")
    require(laws.get("durability") == "SIMULATE_COGNITION_STORE_DURABLE_DATA", "DB/simulation boundary drift")
    require("actually" in laws.get("jspace", "").lower(), "J-Space evidence-boundary wording missing")

    packet_types = abi.get("packet_types")
    require(isinstance(packet_types, dict), "ABI packet_types missing")
    for required in (
        "COGNITIVE_WORK_PACKET/v1",
        "COGNITIVE_RESULT_PACKET/v1",
        "DB_STATE_REF/v1",
        "WORKSPACE_REENTRY/v1",
        "CLAUDE_CODE_BRIDGE_PACKET/v1",
        "GRID_EXECUTOR_BINDING/v1",
    ):
        require(required in packet_types, f"missing ABI packet type {required}")
        require(packet_types[required].get("required"), f"missing required fields for {required}")

    result_classes = set(packet_types["COGNITIVE_RESULT_PACKET/v1"].get("allowed_result_class", []))
    require({"CANDIDATE", "PROJECTION", "MEASUREMENT", "DETERMINISTIC_CONTROL_RESULT", "EFFECT_RECEIPT"} <= result_classes, "result class fence incomplete")
    iface = set(packet_types["CLAUDE_CODE_BRIDGE_PACKET/v1"].get("allowed_interface_class", []))
    require("SESSION_STATE_EXPOSED" in iface and "TOOL_PROTOCOL" in iface, "Claude exposed-interface classes incomplete")

    boundary = abi.get("db_vs_simulation_boundary", {})
    require(boundary.get("store_in_db_when") and boundary.get("simulate_on_grid_when") and boundary.get("never_simulate_as_authority"), "DB-vs-simulation boundary incomplete")
    discriminators = {d.get("id") for d in abi.get("acceptance_discriminators", []) if isinstance(d, dict)}
    require(discriminators == {"ABI-D1-N-INVARIANCE", "ABI-D2-DB-FACT-FENCE", "ABI-D3-EFFECT-FENCE", "ABI-D4-CLAUDE-REENTRY", "ABI-D5-JSPACE-EVIDENCE"}, "ABI discriminator set drift")

    for obj, label in ((census, "census"), (abi, "abi")):
        credits = obj.get("credit_boundary", {})
        runtimeish = [k for k in credits if k not in {"census_source_contract", "abi_source_contract"}]
        require(all(credits[k] == 0 for k in runtimeish), f"{label} source contract inflated runtime/training credit")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", default="research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json")
    parser.add_argument("--abi", default="research_entity/global/COGNITIVE_PROCESS_ABI_v1.json")
    args = parser.parse_args()
    census = load(Path(args.census))
    abi = load(Path(args.abi))
    validate(census, abi)
    print("PASS: ZERO_ENTITYOS_COGNITIVE_CONTRACT_SOURCE_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
