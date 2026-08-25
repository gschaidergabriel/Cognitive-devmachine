#!/usr/bin/env python3
"""Executable model-free ClayCode cognitive packet roundtrip gate.

Scope: CLAYCODE_COGNITIVE_PROTOCOL_COMPONENT_ONLY.

The discriminator binds the exact owner-aligned ClayCode protocol source to the current
V18 frontend/grammar identity, materializes typed work/result/Claude bridge packets from
a generation-bound S0 snapshot, roundtrips them deterministically, and routes the same
semantic work through the retained restart/resize DB fixture while changing physical N.

No model, Claude Code, provider, network, training, J-Space intervention, or real effect
execution occurs. Candidate/model/workspace outputs never receive canonical authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from claycode_base_frontend import compile_frontend
from zero_entityos_restart_resize_db_smoke_v1 import (
    CanonicalStateAuthority,
    CognitiveGridRuntime,
    GridConfig,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "research_entity/claycode/contracts/ZERO_ENTITYOS_COGNITIVE_PROTOCOL_V1.clay"
PROTOCOL_CONTRACT_PATH = ROOT / "research_entity/global/CLAYCODE_COGNITIVE_PROTOCOL_v1.json"
GRAMMAR_PATH = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
RECEIPT_SCHEMA = "CLAYCODE_COGNITIVE_PACKET_ROUNDTRIP_RESTART_RESIZE/v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest(value: Any) -> str:
    return sha256_text(canonical_json(value))


def json_roundtrip(value: Any) -> tuple[Any, str, str]:
    encoded = canonical_json(value)
    decoded = json.loads(encoded)
    return decoded, sha256_text(encoded), sha256_text(canonical_json(decoded))


def validate_protocol_binding() -> dict[str, Any]:
    source = PROTOCOL_PATH.read_text(encoding="utf-8")
    grammar = GRAMMAR_PATH.read_text(encoding="utf-8")
    contract = json.loads(PROTOCOL_CONTRACT_PATH.read_text(encoding="utf-8"))
    compiled = compile_frontend(source, grammar, strict=True)

    expected_source = contract["protocol_source"]["sha256"]
    expected_semantic = contract["protocol_source"]["frontend_semantic_sha256"]
    expected_contract = contract["protocol_source"]["frontend_contract_sha256"]
    expected_grammar = contract["grammar_dependency"]["sha256"]

    checks = {
        "protocol_source_sha_bound": sha256_text(source) == expected_source == compiled["source_sha256"],
        "grammar_sha_bound": sha256_text(grammar) == expected_grammar == compiled["grammar_sha256"],
        "frontend_semantic_sha_bound": compiled["semantic_hash"] == expected_semantic,
        "frontend_contract_sha_bound": compiled["contract_hash"] == expected_contract,
        "frontend_surface_v18": compiled["surface"] == "BASE_D_V18_REWARD_RELATIONS",
        "strict_parse_enabled": compiled["strict"] is True,
    }
    return {
        "checks": checks,
        "source_sha256": compiled["source_sha256"],
        "grammar_sha256": compiled["grammar_sha256"],
        "semantic_hash": compiled["semantic_hash"],
        "contract_hash": compiled["contract_hash"],
        "frontend_schema": compiled["frontend_schema"],
        "surface": compiled["surface"],
    }


def _db_state_ref(authority: CanonicalStateAuthority, key: str) -> dict[str, Any]:
    row = authority.get(key)
    if row is None:
        raise RuntimeError("DB_STATE_REF_SOURCE_MISSING")
    return {
        "ref_id": f"dbref:{row['value_digest'][:24]}",
        "store": "S0_CANONICAL_SQLITE",
        "snapshot_or_epoch": row["epoch"],
        "object_key": row["object_key"],
        "digest": row["value_digest"],
        "provenance": row["provenance"],
        "mutability": "READ_ONLY_TO_COGNITION",
    }


def _epistemic_item(claim_ref: str, evidence_ref: str) -> dict[str, Any]:
    return {
        "epistemic_class": "OBSERVED_REFERENCE",
        "claim_ref": claim_ref,
        "evidence_refs": [evidence_ref],
    }


def make_work_packet(*, db_ref: dict[str, Any], generation: int, available_n: int) -> dict[str, Any]:
    return {
        "schema": "COGNITIVE_WORK_PACKET/v1",
        "causal_event_id": "event:ccp-roundtrip:0001",
        "admission_id": "admission:ccp-roundtrip:0001",
        "generation": generation,
        "work_id": "work:ccp-roundtrip:0001",
        "process_id": "ZECP03",
        "parent_work_ids": [],
        "workspace_epoch": 1,
        "state_snapshot_ref": db_ref,
        "input_refs": ["input:ccp-roundtrip:0001"],
        "epistemic_inputs": [_epistemic_item("goal", "evidence/ref")],
        "capability_scope_ref": "capability:read-state-and-propose-only",
        "resource_budget_ref": "budget:zero-network-component",
        "requested_N": 1,
        "available_N": available_n,
        "route_policy_ref": "route:deterministic-fixture",
        "completion_contract_ref": "completion:typed-candidate-only",
    }


def semantic_core(packet: dict[str, Any]) -> dict[str, Any]:
    """Execution placement is deliberately excluded from semantic work identity."""
    return {
        key: value
        for key, value in packet.items()
        if key not in {"requested_N", "available_N"}
    }


def make_result_packet(
    *,
    work: dict[str, Any],
    runtime_result: dict[str, Any],
    n: int,
) -> dict[str, Any]:
    binding = {
        "grid_instance_id": f"grid:ccp:N{n}",
        "requested_N": work["requested_N"],
        "available_N": n,
        "executor_id": runtime_result["executor_id"],
        "lease_id": f"lease:fixture:N{n}",
        "process_id": work["process_id"],
        "runtime_identity": "ZERO_ENTITYOS_RESTART_RESIZE_DB_SMOKE/v1",
    }
    payload = {
        "runtime_result_id": runtime_result["result_id"],
        "runtime_semantic_identity": runtime_result["semantic_identity"],
        "candidate_only": True,
    }
    return {
        "schema": "COGNITIVE_RESULT_PACKET/v1",
        "causal_event_id": work["causal_event_id"],
        "admission_id": work["admission_id"],
        "generation": work["generation"],
        "work_id": work["work_id"],
        "process_id": work["process_id"],
        "executor_binding": binding,
        "result_id": runtime_result["result_id"],
        "result_class": "CANDIDATE",
        "result_payload_ref": f"payload:{digest(payload)}",
        "result_digest": digest(payload),
        "evidence_refs": [work["state_snapshot_ref"]["ref_id"]],
        "unknowns": ["MODEL_RUNTIME_NOT_EXECUTED", "JSPACE_CAUSALITY_NOT_TESTED"],
        "db_write_proposals": [],
        "effect_request_candidates": [],
        "workspace_reentry": None,
        "runtime_receipt_ref": None,
    }


def make_claude_bridge_packet(work: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "candidate_result_ref": result["result_id"],
        "instruction": "MODEL_FREE_OBSERVABLE_INTERFACE_FIXTURE_ONLY",
    }
    return {
        "bridge_id": "bridge:ccp-roundtrip:0001",
        "direction": "GRID_TO_CLAUDE_CODE_CANDIDATE",
        "causal_event_id": work["causal_event_id"],
        "work_id": work["work_id"],
        "workspace_epoch": work["workspace_epoch"],
        "interface_class": "STRUCTURED_TEXT_PACKET",
        "payload_ref": f"payload:{digest(payload)}",
        "payload_digest": digest(payload),
        "state_refs": [work["state_snapshot_ref"]],
        "tool_scope_ref": "tool-scope:NO_INVOCATION",
        "request_or_result_identity": "NOT_INVOKED",
        "activation_access_observed": False,
    }


def run_roundtrip_smoke(db_path: Path) -> dict[str, Any]:
    binding = validate_protocol_binding()
    checks: dict[str, bool] = dict(binding["checks"])

    authority = CanonicalStateAuthority(db_path)
    try:
        generation = 7
        authority.seed("goal", {"goal": "typed-roundtrip-restart-resize"}, provenance="fixture:admitted", generation=generation, epoch=1)
        authority.seed("evidence/ref", "evidence:ccp:0001", provenance="fixture:observed", generation=generation, epoch=1)
        s0_before = authority.snapshot_digest()
        db_ref = _db_state_ref(authority, "goal")

        work_n1 = make_work_packet(db_ref=db_ref, generation=generation, available_n=1)
        work_n1_rt, work_hash_before, work_hash_after = json_roundtrip(work_n1)
        checks["work_packet_json_roundtrip_identity"] = work_n1 == work_n1_rt and work_hash_before == work_hash_after

        grid1 = CognitiveGridRuntime(db_path, GridConfig(n=1, generation=generation))
        try:
            runtime_work1 = grid1.enqueue(work_n1["process_id"], semantic_core(work_n1))
            runtime_result1 = grid1.execute(runtime_work1)
            result_n1 = make_result_packet(work=work_n1, runtime_result=runtime_result1, n=1)
            result_n1_rt, result_hash_before, result_hash_after = json_roundtrip(result_n1)
            checks["result_packet_json_roundtrip_identity"] = (
                result_n1 == result_n1_rt and result_hash_before == result_hash_after
            )
            checks["result_candidate_only_n1"] = (
                result_n1["result_class"] == "CANDIDATE"
                and runtime_result1["canonical_truth"] is False
                and runtime_result1["effect_authority"] is False
            )
            checks["direct_s0_write_rejected_n1"] = grid1.attempt_direct_s0_write(
                "illegal/ccp/n1", {"x": 1}
            )
            effect_candidate = grid1.propose_effect(runtime_result1, {"kind": "fixture-noop"})
            checks["effect_is_candidate_only"] = effect_candidate.startswith("efp-")
        finally:
            grid1.close()

        s0_after_n1 = authority.snapshot_digest()
        checks["candidate_paths_do_not_mutate_s0"] = s0_after_n1 == s0_before

        work_n20 = make_work_packet(db_ref=db_ref, generation=generation, available_n=20)
        checks["semantic_core_stable_across_n_change"] = semantic_core(work_n1) == semantic_core(work_n20)
        checks["state_ref_stable_across_n_change"] = work_n1["state_snapshot_ref"] == work_n20["state_snapshot_ref"]

        grid20 = CognitiveGridRuntime(db_path, GridConfig(n=20, generation=generation))
        try:
            checks["s1_restart_is_empty"] = all(value == 0 for value in grid20.s1_counts().values())
            runtime_work20 = grid20.enqueue(work_n20["process_id"], semantic_core(work_n20))
            runtime_result20 = grid20.execute(runtime_work20)
            result_n20 = make_result_packet(work=work_n20, runtime_result=runtime_result20, n=20)
            checks["runtime_semantic_identity_stable_across_n_change"] = (
                runtime_result1["semantic_identity"] == runtime_result20["semantic_identity"]
            )
            checks["process_identity_stable_across_n_change"] = (
                result_n1["process_id"] == result_n20["process_id"] == "ZECP03"
            )
            checks["physical_binding_reflects_n_change"] = (
                result_n1["executor_binding"]["available_N"] == 1
                and result_n20["executor_binding"]["available_N"] == 20
                and result_n1["executor_binding"]["grid_instance_id"] != result_n20["executor_binding"]["grid_instance_id"]
            )
            checks["result_candidate_only_n20"] = (
                result_n20["result_class"] == "CANDIDATE"
                and runtime_result20["canonical_truth"] is False
                and runtime_result20["effect_authority"] is False
            )
            checks["direct_s0_write_rejected_n20"] = grid20.attempt_direct_s0_write(
                "illegal/ccp/n20", {"x": 20}
            )

            claude_packet = make_claude_bridge_packet(work_n20, result_n20)
            claude_rt, claude_hash_before, claude_hash_after = json_roundtrip(claude_packet)
            checks["claude_bridge_packet_roundtrip_identity"] = (
                claude_packet == claude_rt and claude_hash_before == claude_hash_after
            )
            checks["claude_bridge_has_no_activation_or_runtime_claim"] = (
                claude_packet["activation_access_observed"] is False
                and claude_packet["request_or_result_identity"] == "NOT_INVOKED"
            )
        finally:
            grid20.close()

        checks["s0_stable_after_restart_resize_candidates"] = authority.snapshot_digest() == s0_before
        passed = all(checks.values())
        return {
            "schema": RECEIPT_SCHEMA,
            "status": "PASS_CLAYCODE_COGNITIVE_PROTOCOL_COMPONENT_ONLY" if passed else "FAIL",
            "checks": checks,
            "counts": {"passed": sum(bool(v) for v in checks.values()), "total": len(checks)},
            "protocol_binding": binding,
            "evidence": {
                "N_before": 1,
                "N_after": 20,
                "s0_digest": s0_before,
                "work_packet_digest_n1": digest(work_n1),
                "work_packet_digest_n20": digest(work_n20),
                "semantic_core_digest": digest(semantic_core(work_n1)),
                "result_packet_digest_n1": digest(result_n1),
                "result_packet_digest_n20": digest(result_n20),
                "runtime_semantic_identity": runtime_result1["semantic_identity"],
            },
            "execution": {
                "network_calls": 0,
                "provider_model_calls": 0,
                "claude_code_calls": 0,
                "jspace_interventions": 0,
                "real_effects": 0,
            },
            "credit_boundary": {
                "claycode_protocol_source_contract": 1,
                "claycode_protocol_component_runtime": 1 if passed else 0,
                "restart_resize_db_boundary_component_dependency": 1 if passed else 0,
                "trained_08b_variable_grid_runtime": 0,
                "claude_code_bridge_runtime": 0,
                "global_jspace_causal_runtime": 0,
                "whole_entityos_hcu_runtime": 0,
                "training": 0,
                "whole_product_pass": False,
            },
        }
    finally:
        authority.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--db", type=Path)
    args = parser.parse_args()

    if args.db:
        receipt = run_roundtrip_smoke(args.db)
    else:
        with tempfile.TemporaryDirectory() as td:
            receipt = run_roundtrip_smoke(Path(td) / "canonical-s0.sqlite3")

    if args.json:
        print(json.dumps(receipt, sort_keys=True, indent=2))
    else:
        print(receipt["status"], f"{receipt['counts']['passed']}/{receipt['counts']['total']}")
    return 0 if receipt["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
