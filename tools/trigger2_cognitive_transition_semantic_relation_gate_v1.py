#!/usr/bin/env python3
"""Semantic-relation gate for Trigger-2 executable cognitive-transition pilot v2.

The v2 pilot already proves structural/digest/ClayCode self-consistency. This gate adds
an independent semantic acceptance layer so a target + expected_state_after + oracle
packet cannot be changed together into a self-consistent but cognitively wrong example.

All rows remain candidate evaluation data. PASS mints zero dataset/training/runtime credit.
"""
from __future__ import annotations

import copy
import json
from typing import Any, Callable

from trigger2_cognitive_process_executable_transition_pilot_v2 import (
    TRAINABLE_PROCESS_IDS,
    RESULT_SCHEMA,
    materialize_result_packet,
    roundtrip,
    rows,
    validate_row,
)

GATE_SCHEMA = "TRIGGER2_COGNITIVE_TRANSITION_SEMANTIC_RELATION_GATE/v1"


def _need(cond: bool, code: str) -> None:
    if not cond:
        raise ValueError(code)


def _target(row: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any], list[Any]]:
    pid = str(row.get("process_id_evaluator_only"))
    target = row.get("supervision_target")
    _need(pid in TRAINABLE_PROCESS_IDS, "SEMANTIC_PROCESS_NOT_TRAINABLE:" + pid)
    _need(isinstance(target, dict), "SEMANTIC_TARGET_REQUIRED:" + pid)
    payload = target.get("candidate_payload")
    state = target.get("expected_state_after")
    unknowns = target.get("unknowns")
    _need(isinstance(payload, dict), "SEMANTIC_PAYLOAD_REQUIRED:" + pid)
    _need(isinstance(state, dict), "SEMANTIC_STATE_AFTER_REQUIRED:" + pid)
    _need(isinstance(unknowns, list), "SEMANTIC_UNKNOWNS_REQUIRED:" + pid)
    return pid, payload, state, unknowns


def z03(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    _need(s.get("resource_ceiling") == "UNKNOWN", "ZECP03_UNKNOWN_RESOURCE_MUST_REMAIN_UNKNOWN")
    _need("resource_ceiling" in u, "ZECP03_UNKNOWN_RESOURCE_MUST_BE_DECLARED")
    _need("resource_ceiling" in p.get("missing_state_questions", []), "ZECP03_MISSING_STATE_QUESTION_REQUIRED")


def z04(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    _need(s.get("minority_erased") is False, "ZECP04_MINORITY_EVIDENCE_ERASURE_FORBIDDEN")
    _need(bool(p.get("deferred_refs")), "ZECP04_DEFERRED_COUNTEREVIDENCE_REQUIRED")
    _need("minority_counterevidence_deferred_not_false" in p.get("uncertainty_set", []), "ZECP04_DEFERRED_IS_NOT_FALSE_REQUIRED")


def z05(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    g = p.get("goal_state_candidate", {})
    _need(s.get("durable_goal_changed") is False, "ZECP05_MODEL_CANNOT_REWRITE_DURABLE_GOAL")
    _need(g.get("conflict") == "TEMPORARY_PREFERENCE_REJECTED", "ZECP05_DURABLE_GOAL_PRECEDENCE_REQUIRED")


def z06(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    units = {x.get("id"): x.get("status") for x in p.get("work_units", []) if isinstance(x, dict)}
    _need(s.get("stale_unit_executed") is False, "ZECP06_STALE_UNIT_EXECUTION_FORBIDDEN")
    _need(units.get("w2") == "BLOCKED" and units.get("w2r") == "CANDIDATE_REPLAN", "ZECP06_BLOCK_AND_REPLAN_RELATION_REQUIRED")


def z07(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    alt = p.get("alternative_set", [])
    ids = {x.get("id") for x in alt if isinstance(x, dict) and x.get("status") == "LIVE"}
    readout = p.get("uncertainty_readout", {})
    _need(ids >= {"A", "B"}, "ZECP07_LIVE_ALTERNATIVES_MUST_BE_PRESERVED")
    _need(readout.get("resolved") is False, "ZECP07_MAJORITY_CANNOT_RESOLVE_WITHOUT_DISCRIMINATOR")
    _need(s.get("resolved_hypothesis") == "UNKNOWN", "ZECP07_UNRESOLVED_HYPOTHESIS_MUST_REMAIN_UNKNOWN")


def z08(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    _need(s.get("canonical_fact_added") is False, "ZECP08_INFERENCE_CANNOT_MINT_CANONICAL_FACT")
    _need(isinstance(p.get("confidence_readout"), (int, float)), "ZECP08_CONFIDENCE_READOUT_REQUIRED")


def z09(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    flags = set(p.get("contradiction_flags", []))
    _need(s.get("unknown_restored") is True, "ZECP09_UNKNOWN_RESTORATION_REQUIRED")
    _need("unknown_collapsed_to_false" in flags and "minority_evidence_conflict" in flags, "ZECP09_CONTRADICTION_RELATION_REQUIRED")


def z10(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    _need(s.get("truth_status") == "UNCHANGED_CANDIDATE_ONLY", "ZECP10_WORKSPACE_WINNER_CANNOT_MINT_TRUTH")
    _need(p.get("broadcast_packet", {}).get("candidate_only") is True, "ZECP10_BROADCAST_MUST_REMAIN_CANDIDATE")


def z12(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    _need(s.get("counterevidence_retrievable") is True, "ZECP12_COMPRESSION_MUST_PRESERVE_COUNTEREVIDENCE_RETRIEVAL")
    _need(bool(p.get("loss_manifest", {}).get("retained_counterevidence")), "ZECP12_COUNTEREVIDENCE_RETENTION_MANIFEST_REQUIRED")


def z13(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    h = p.get("claude_handoff_packet", {})
    _need(h.get("interface_class") == "STRUCTURED_TEXT", "ZECP13_EXPOSED_INTERFACE_CLASS_REQUIRED")
    _need(s.get("hidden_activation_access") == "UNKNOWN" and "hidden_activation_access" in u, "ZECP13_HIDDEN_ACTIVATION_ACCESS_MUST_REMAIN_UNKNOWN")


def z14(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    classes = {x.get("class") for x in p.get("evidence_candidates", []) if isinstance(x, dict)}
    _need(s.get("claude_assertion_canonical") is False, "ZECP14_MODEL_ASSERTION_CANNOT_BECOME_CANONICAL")
    _need({"OBSERVED_TOOL_RESULT", "MODEL_ASSERTION"}.issubset(classes), "ZECP14_TOOL_RESULT_AND_MODEL_ASSERTION_MUST_BE_SEPARATED")


def z15(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    _need(s.get("canonical_memory_changed") is False, "ZECP15_MODEL_CANNOT_COMMIT_MEMORY")


def z16(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    _need(s.get("effect_execution_status") == "NOT_EXECUTED_BY_MODEL", "ZECP16_MODEL_EFFECT_EXECUTION_FORBIDDEN")
    _need(s.get("effect_request_status") == "CANDIDATE", "ZECP16_EFFECT_REQUEST_MUST_REMAIN_CANDIDATE")


def z18(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    r = p.get("reconciled_state_candidate", {})
    plan = p.get("rejoin_plan", {})
    _need(r.get("effect_outcome") == "UNKNOWN" and "effect_outcome" in u, "ZECP18_UNKNOWN_EFFECT_OUTCOME_MUST_REMAIN_UNKNOWN")
    _need(r.get("blind_replay") is False and s.get("replay_allowed") is False, "ZECP18_BLIND_REPLAY_FORBIDDEN")
    _need(s.get("process_identity_preserved") is True, "ZECP18_PROCESS_IDENTITY_MUST_SURVIVE_RESIZE")
    _need(plan.get("requested_N_before") != plan.get("requested_N_after"), "ZECP18_VARIABLE_N_RESIZE_CASE_REQUIRED")


def z19(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    _need(s.get("semantic_identity_preserved") is True, "ZECP19_SEMANTIC_IDENTITY_REQUIRED")
    _need(s.get("representation_authority") is False, "ZECP19_REPRESENTATION_CANNOT_MINT_AUTHORITY")


def z20(p: dict[str, Any], s: dict[str, Any], u: list[Any]) -> None:
    m = p.get("jspace_measurement", {})
    _need(m.get("causal_effect") == "UNKNOWN" and "causal_effect" in u, "ZECP20_CAUSAL_EFFECT_MUST_REMAIN_UNKNOWN")
    _need(p.get("credit_scope") == "NO_CAUSAL_JSPACE_CREDIT", "ZECP20_CAUSAL_JSPACE_CREDIT_FORBIDDEN")
    _need(s.get("causal_status") == "UNKNOWN", "ZECP20_CAUSAL_STATUS_MUST_REMAIN_UNKNOWN")


VALIDATORS: dict[str, Callable[[dict[str, Any], dict[str, Any], list[Any]], None]] = {
    "ZECP03": z03, "ZECP04": z04, "ZECP05": z05, "ZECP06": z06,
    "ZECP07": z07, "ZECP08": z08, "ZECP09": z09, "ZECP10": z10,
    "ZECP12": z12, "ZECP13": z13, "ZECP14": z14, "ZECP15": z15,
    "ZECP16": z16, "ZECP18": z18, "ZECP19": z19, "ZECP20": z20,
}


def validate_semantic_relation(row: dict[str, Any]) -> None:
    pid, payload, state, unknowns = _target(row)
    _need(pid in VALIDATORS, "SEMANTIC_VALIDATOR_MISSING:" + pid)
    VALIDATORS[pid](payload, state, unknowns)


def _rebuild_oracle(row: dict[str, Any]) -> None:
    w = row["model_visible"]["work_packet"]
    target = row["supervision_target"]
    packet = materialize_result_packet(w, target)
    envelope, decoded = roundtrip(RESULT_SCHEMA, packet)
    _need(decoded == packet, "SELFTEST_CLAYCODE_REBUILD_FAILED")
    row["oracle_evaluator_only"]["result_packet"] = packet
    row["oracle_evaluator_only"]["semantic_digest"] = packet["result_digest"]
    row["oracle_evaluator_only"]["claycode_roundtrip"] = {
        "packet_digest": envelope.packet_digest,
        "clay_source_sha256": envelope.clay_source_sha256,
        "clay_semantic_hash": envelope.clay_semantic_hash,
        "clay_grammar_sha256": envelope.clay_grammar_sha256,
    }


def self_test() -> dict[str, Any]:
    cases: dict[str, bool] = {}
    source_rows = rows()
    cases["ALL_16_CURRENT_ROWS_PASS_SEMANTIC_RELATIONS"] = True
    try:
        for row in source_rows:
            validate_semantic_relation(row)
    except ValueError:
        cases["ALL_16_CURRENT_ROWS_PASS_SEMANTIC_RELATIONS"] = False
    by_pid = {r["process_id_evaluator_only"]: r for r in source_rows}

    bad = copy.deepcopy(by_pid["ZECP07"])
    bad["supervision_target"]["candidate_payload"]["uncertainty_readout"] = {"resolved": True, "reason": "MAJORITY"}
    bad["supervision_target"]["expected_state_after"]["resolved_hypothesis"] = "A"
    _rebuild_oracle(bad)
    try:
        validate_row(bad)
        structural_passed = True
    except ValueError:
        structural_passed = False
    cases["SELF_CONSISTENT_MAJORITY_TRUTH_PASSES_OLD_STRUCTURAL_GATE"] = structural_passed
    try:
        validate_semantic_relation(bad)
        cases["SELF_CONSISTENT_MAJORITY_TRUTH_FAILS_SEMANTIC_GATE"] = False
    except ValueError as exc:
        cases["SELF_CONSISTENT_MAJORITY_TRUTH_FAILS_SEMANTIC_GATE"] = "ZECP07_" in str(exc)

    bad = copy.deepcopy(by_pid["ZECP18"])
    bad["supervision_target"]["candidate_payload"]["reconciled_state_candidate"]["blind_replay"] = True
    bad["supervision_target"]["expected_state_after"]["replay_allowed"] = True
    _rebuild_oracle(bad)
    try:
        validate_row(bad)
        structural_passed = True
    except ValueError:
        structural_passed = False
    cases["SELF_CONSISTENT_BLIND_REPLAY_PASSES_OLD_STRUCTURAL_GATE"] = structural_passed
    try:
        validate_semantic_relation(bad)
        cases["SELF_CONSISTENT_BLIND_REPLAY_FAILS_SEMANTIC_GATE"] = False
    except ValueError as exc:
        cases["SELF_CONSISTENT_BLIND_REPLAY_FAILS_SEMANTIC_GATE"] = "ZECP18_" in str(exc)
    return {"pass": all(cases.values()), "cases": cases}


def run() -> dict[str, Any]:
    failures: list[str] = []
    checked: list[str] = []
    for row in rows():
        pid = row["process_id_evaluator_only"]
        try:
            validate_semantic_relation(row)
            checked.append(pid)
        except ValueError as exc:
            failures.append(f"{pid}:{exc}")
    st = self_test()
    if not st["pass"]:
        failures.append("SELF_TEST_FAILED")
    return {
        "schema": GATE_SCHEMA,
        "pass": not failures,
        "failures": failures,
        "semantic_relations_checked": checked,
        "all_trainable_processes_covered": set(checked) == set(TRAINABLE_PROCESS_IDS),
        "self_test": st,
        "accepted_dataset_tokens": 0,
        "training_eligible_rows": 0,
        "training_credit": 0,
        "jspace_causal_credit": 0,
        "whole_hcu_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
        "evidence_boundary": "Process-specific semantic relation gate over synthetic candidate pilot rows only; no dataset admission/model runtime/training credit.",
    }


def main() -> int:
    out = run()
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
