#!/usr/bin/env python3
"""Trigger-2 executable cognitive-transition pilot.

This is a source-design / candidate-eval pilot for issue #2022. It replaces
meta-rule narration with concrete, machine-adjudicable COGNITIVE_RESULT_PACKET/v1
targets plus explicit state_before -> decisive_delta -> expected_state_after
transitions.

It is deliberately NOT training-admitted. It cannot mint canonical truth,
database/effect authority, accepted dataset tokens, model/J-Space credit, HCU
runtime credit, or training credit.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
ABI_PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
CENSUS_PATH = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"

ROW_SCHEMA = "TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_CANDIDATE/v1"
AUDIT_SCHEMA = "TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_AUDIT/v1"
TARGET_KIND = "COGNITIVE_RESULT_PACKET/v1"
ALLOWED_MODEL_IMPLEMENTATION_CLASSES = {"SIMULATE_ON_GRID", "EXTERNAL_STRONG_MODEL_BRIDGE"}

SOURCE_BINDINGS = {
    "abi_path": "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json",
    "census_path": "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json",
    "course_path": "research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md",
    "issue": 2022,
}

def cj(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def dg(value: Any) -> str:
    return hashlib.sha256(cj(value).encode("utf-8")).hexdigest()

def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"OBJECT_REQUIRED:{path}")
    return value

def _state_ref(name: str, epoch: int, digest: str) -> dict[str, Any]:
    return {
        "ref_id": name,
        "store": "UnifiedDB",
        "snapshot_or_epoch": epoch,
        "object_key": name,
        "digest": digest,
        "provenance": "DETERMINISTIC_BOUND_STATE",
        "mutability": "IMMUTABLE_SNAPSHOT",
    }

def _reentry(result_id: str, process_id: str, causal_event_id: str, from_epoch: int, to_epoch: int) -> dict[str, Any]:
    body = {
        "source_result_id": result_id,
        "source_process_id": process_id,
        "causal_event_id": causal_event_id,
        "from_workspace_epoch": from_epoch,
        "to_workspace_epoch": to_epoch,
        "reentry_payload_ref": f"candidate:{result_id}",
        "observed_downstream_change": "UNKNOWN",
        "acceptance": "CANDIDATE_ONLY",
    }
    body["reentry_digest"] = dg(body)
    return body

def _case(
    *,
    case_id: str,
    process_id: str,
    implementation_class: str,
    state_before: dict[str, Any],
    decisive_delta: dict[str, Any],
    result_payload: dict[str, Any],
    state_after: dict[str, Any],
    evidence_refs: list[str] | None = None,
    unknowns: list[str] | None = None,
    db_write_proposals: list[dict[str, Any]] | None = None,
    effect_request_candidates: list[dict[str, Any]] | None = None,
    workspace_epoch: int = 40,
) -> dict[str, Any]:
    evidence_refs = list(evidence_refs or [])
    unknowns = list(unknowns or [])
    db_write_proposals = copy.deepcopy(db_write_proposals or [])
    effect_request_candidates = copy.deepcopy(effect_request_candidates or [])
    causal_event_id = f"ce-{case_id.lower()}"
    admission_id = f"adm-{case_id.lower()}"
    work_id = f"work-{case_id.lower()}"
    result_id = f"result-{case_id.lower()}"
    result_digest = dg(result_payload)
    target = {
        "schema": TARGET_KIND,
        "causal_event_id": causal_event_id,
        "admission_id": admission_id,
        "generation": 7,
        "work_id": work_id,
        "process_id": process_id,
        "executor_binding": {
            "grid_instance_id": "grid-variable-pilot",
            "requested_N": 10,
            "available_N": 10,
            "executor_id": "executor-interchangeable",
            "lease_id": "lease-evaluator-bound",
            "process_id": process_id,
            "runtime_identity": "SOURCE_DESIGN_ONLY_NO_MODEL_RUNTIME",
            "started_at": "UNKNOWN",
            "ended_at": "UNKNOWN",
        },
        "result_id": result_id,
        "result_class": "CANDIDATE",
        "result_payload_ref": {"encoding": "DETERMINISTIC_JSON_V1", "payload": result_payload},
        "result_digest": result_digest,
        "evidence_refs": evidence_refs,
        "unknowns": unknowns,
        "db_write_proposals": db_write_proposals,
        "effect_request_candidates": effect_request_candidates,
        "workspace_reentry": _reentry(result_id, process_id, causal_event_id, workspace_epoch, workspace_epoch + 1),
        "runtime_receipt": {
            "status": "SOURCE_DESIGN_ONLY",
            "model_runtime_observed": False,
            "canonical_truth_minted": False,
            "effect_executed": False,
        },
    }
    row = {
        "schema": ROW_SCHEMA,
        "case_id": case_id,
        "status": "CANDIDATE_EVAL_ONLY_NOT_TRAINING_ELIGIBLE",
        "process_id_evaluator_only": process_id,
        "implementation_class_evaluator_only": implementation_class,
        "state_before": state_before,
        "state_before_digest": dg(state_before),
        "decisive_semantic_delta": decisive_delta,
        "target": target,
        "expected_state_after": state_after,
        "expected_state_after_digest": dg(state_after),
        "required_unknowns_preserved": unknowns,
        "source_bindings": SOURCE_BINDINGS,
        "model_visible_fields": ["state_before", "decisive_semantic_delta"],
        "target_visible_only_during_supervision": True,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }
    row["transition_semantic_digest"] = dg({
        "process_id": process_id,
        "state_before_digest": row["state_before_digest"],
        "decisive_semantic_delta": decisive_delta,
        "result_digest": result_digest,
        "expected_state_after_digest": row["expected_state_after_digest"],
    })
    return row

def rows() -> list[dict[str, Any]]:
    goal_ref = _state_ref("goal:preserve-evidence", 11, "goal-digest-11")
    evidence_ref = _state_ref("evidence:counterexample-2", 11, "evidence-digest-2")
    return [
        _case(case_id="ECT01_WORKING_STATE", process_id="ZECP03", implementation_class="SIMULATE_ON_GRID",
              state_before={"goal_ref": goal_ref, "operator_preference": "UNKNOWN", "working_state": None},
              decisive_delta={"retrieval": "GOAL_REF_RESOLVED", "missing": ["operator_preference"]},
              result_payload={"working_state_candidate": {"goal_ref": goal_ref["ref_id"], "operator_preference": "UNKNOWN"}, "missing_state_questions": ["operator_preference"]},
              state_after={"goal_ref": goal_ref, "operator_preference": "UNKNOWN", "working_state": {"goal_ref": goal_ref["ref_id"]}},
              evidence_refs=[goal_ref["ref_id"]], unknowns=["operator_preference"]),
        _case(case_id="ECT02_ATTENTION", process_id="ZECP04", implementation_class="SIMULATE_ON_GRID",
              state_before={"active_evidence": ["ev-support", evidence_ref["ref_id"]], "capacity": 1, "uncertainty": ["claim-X"]},
              decisive_delta={"budget_change": "ACTIVE_SLICE_ONE_ITEM", "counterevidence_still_retrievable": True},
              result_payload={"attention_slice": ["ev-support"], "deferred_refs": [evidence_ref["ref_id"]], "uncertainty_set": ["claim-X"]},
              state_after={"active_evidence": ["ev-support"], "deferred_refs": [evidence_ref["ref_id"]], "uncertainty": ["claim-X"]},
              evidence_refs=["ev-support", evidence_ref["ref_id"]], unknowns=["claim-X"]),
        _case(case_id="ECT03_GOAL", process_id="ZECP05", implementation_class="SIMULATE_ON_GRID",
              state_before={"durable_goal_ref": goal_ref["ref_id"], "temporary_preference": "finish-fast", "subgoal": None},
              decisive_delta={"conflict": "TEMPORARY_PREFERENCE_WOULD_REPLACE_DURABLE_GOAL"},
              result_payload={"goal_state_candidate": {"durable_goal_ref": goal_ref["ref_id"], "subgoal": "prepare-evidence-bounded-candidate"}, "completion_tests": ["provenance-bound", "no-truth-mint"]},
              state_after={"durable_goal_ref": goal_ref["ref_id"], "temporary_preference": "finish-fast", "subgoal": "prepare-evidence-bounded-candidate"}, evidence_refs=[goal_ref["ref_id"]]),
        _case(case_id="ECT04_REPLAN", process_id="ZECP06", implementation_class="SIMULATE_ON_GRID",
              state_before={"work_units": {"u1": "DONE", "u2": "READY", "u3": "BLOCKED_ON_u2"}, "prereq_u2": True},
              decisive_delta={"new_evidence": "PREREQ_u2_FALSE", "evidence_ref": evidence_ref["ref_id"]},
              result_payload={"work_graph_candidate": {"u1": "DONE", "u2": "BLOCKED", "u3": "BLOCKED"}, "work_units": ["u2-repair-prerequisite"], "replan_conditions": ["only-release-u2-after-current-evidence"]},
              state_after={"work_units": {"u1": "DONE", "u2": "BLOCKED", "u3": "BLOCKED"}, "prereq_u2": False}, evidence_refs=[evidence_ref["ref_id"]]),
        _case(case_id="ECT05_HYPERPOSITION", process_id="ZECP07", implementation_class="SIMULATE_ON_GRID",
              state_before={"alternatives": ["A", "B"], "votes": {"A": 8, "B": 2}, "discriminator": None},
              decisive_delta={"new_discriminator_evidence": False, "majority_only": True},
              result_payload={"alternative_set": ["A", "B"], "uncertainty_readout": "UNRESOLVED", "discriminator_candidates": ["measure-causal-difference-A-vs-B"]},
              state_after={"alternatives": ["A", "B"], "resolution": "UNRESOLVED", "next": "measure-causal-difference-A-vs-B"}, unknowns=["which-alternative-is-true"]),
        _case(case_id="ECT06_INFERENCE", process_id="ZECP08", implementation_class="SIMULATE_ON_GRID",
              state_before={"observed": {"a": 2, "b": 3}, "query": "a+b", "authority": "CANDIDATE_ONLY"},
              decisive_delta={"operation": "BOUNDED_ARITHMETIC_INFERENCE"}, result_payload={"candidate_result": 5, "candidate_action": None, "confidence_readout": 1.0},
              state_after={"candidate_result": 5, "authority": "CANDIDATE_ONLY"}),
        _case(case_id="ECT07_CRITIQUE", process_id="ZECP09", implementation_class="SIMULATE_ON_GRID",
              state_before={"candidate": {"claim": "X", "status": "CANONICAL_BECAUSE_CONFIDENT"}, "evidence_for_X": []},
              decisive_delta={"authority_check": "NO_CANONICAL_ADMISSION_RECEIPT"},
              result_payload={"quality_readout": "FAIL_SCOPE", "contradiction_flags": ["UNSUPPORTED_AUTHORITY"], "revision_request": "downgrade-to-candidate-and-seek-evidence"},
              state_after={"candidate": {"claim": "X", "status": "CANDIDATE"}, "needs_evidence": True}, unknowns=["truth-of-X"]),
        _case(case_id="ECT08_WORKSPACE", process_id="ZECP10", implementation_class="SIMULATE_ON_GRID",
              state_before={"workspace_epoch": 40, "winner": "r-17", "broadcast": True, "downstream_use": "UNKNOWN"},
              decisive_delta={"broadcast_observed": True, "causal_uptake_observed": False},
              result_payload={"workspace_selection": "r-17", "broadcast_packet": {"ref": "r-17"}, "reentry_refs": ["r-17"], "causal_credit": 0},
              state_after={"workspace_epoch": 41, "reentry_candidate": "r-17", "causal_uptake": "UNKNOWN"}, evidence_refs=["r-17"], unknowns=["causal-uptake"], workspace_epoch=40),
        _case(case_id="ECT09_COMPRESSION", process_id="ZECP12", implementation_class="SIMULATE_ON_GRID",
              state_before={"branches": ["A", "B"], "unknowns": ["u1"], "evidence_refs": ["ev-A", "ev-B"], "budget": 512},
              decisive_delta={"new_budget": 128, "must_preserve": ["branches", "unknowns", "evidence_refs"]},
              result_payload={"compressed_state_packet": {"branches": ["A", "B"], "unknowns": ["u1"], "evidence_refs": ["ev-A", "ev-B"]}, "loss_manifest": ["surface-wording"], "reentry_binding": "compress-09"},
              state_after={"branches": ["A", "B"], "unknowns": ["u1"], "evidence_refs": ["ev-A", "ev-B"], "budget": 128}, evidence_refs=["ev-A", "ev-B"], unknowns=["u1"]),
        _case(case_id="ECT10_CLAUDE_HANDOFF", process_id="ZECP13", implementation_class="EXTERNAL_STRONG_MODEL_BRIDGE",
              state_before={"work_ref": "work-claude-10", "state_refs": ["s1"], "tool_scope_ref": "tool-scope-readonly", "activation_access": "UNKNOWN"},
              decisive_delta={"need_strong_model": True, "exposed_interface": "TOOL_PROTOCOL"},
              result_payload={"claude_handoff_packet": {"direction": "GRID_TO_CLAUDE", "interface_class": "TOOL_PROTOCOL", "work_ref": "work-claude-10", "state_refs": ["s1"], "tool_scope_ref": "tool-scope-readonly"}, "bridge_request_receipt": "candidate-request-10"},
              state_after={"handoff_candidate": "candidate-request-10", "activation_access": "UNKNOWN"}, evidence_refs=["s1"], unknowns=["claude-hidden-activation-access"]),
        _case(case_id="ECT11_CLAUDE_RETURN", process_id="ZECP14", implementation_class="EXTERNAL_STRONG_MODEL_BRIDGE",
              state_before={"request_receipt": "candidate-request-10", "claude_assertion": "claim-C", "tool_result_ref": "tool-result-11"},
              decisive_delta={"tool_result_observed": True, "model_assertion_is_fact": False},
              result_payload={"bridge_return_packet": {"request_receipt": "candidate-request-10", "tool_result_ref": "tool-result-11"}, "evidence_candidates": [{"ref": "tool-result-11", "class": "OBSERVED"}, {"claim": "claim-C", "class": "HYPOTHESIS"}], "workspace_reentry_candidate": "return-11"},
              state_after={"observed_evidence": ["tool-result-11"], "candidate_claims": ["claim-C"], "canonical_truth_from_claude": False}, evidence_refs=["candidate-request-10", "tool-result-11"]),
        _case(case_id="ECT12_MEMORY_PROPOSAL", process_id="ZECP15", implementation_class="SIMULATE_ON_GRID",
              state_before={"verified_outcome_ref": "outcome-12", "memory_state": "old"}, decisive_delta={"verified_outcome_supports_update": True},
              result_payload={"state_update_proposal": {"from": "old", "to": "candidate-new", "status": "CANDIDATE_ONLY"}, "memory_update_proposal": {"value": "candidate-new", "commit": False}, "provenance_refs": ["outcome-12"]},
              state_after={"memory_state": "old", "pending_memory_proposal": "candidate-new"}, evidence_refs=["outcome-12"],
              db_write_proposals=[{"proposal_id": "dbp-12", "status": "CANDIDATE_ONLY", "commit": False, "provenance_refs": ["outcome-12"]}]),
        _case(case_id="ECT13_EFFECT_PROPOSAL", process_id="ZECP16", implementation_class="SIMULATE_ON_GRID",
              state_before={"candidate_action": "tool-call-X", "capability_scope_ref": "cap-scope-13", "effect_executed": False},
              decisive_delta={"preconditions_present": True, "execution_authority": "EFFECTGATE_ONLY"},
              result_payload={"effect_request_candidate": {"action": "tool-call-X", "capability_scope_ref": "cap-scope-13", "status": "CANDIDATE_ONLY"}, "precondition_refs": ["pre-13"]},
              state_after={"candidate_action": "tool-call-X", "pending_effect_request": "eff-13", "effect_executed": False}, evidence_refs=["cap-scope-13", "pre-13"],
              effect_request_candidates=[{"request_id": "eff-13", "status": "CANDIDATE_ONLY", "executed": False, "capability_scope_ref": "cap-scope-13"}]),
        _case(case_id="ECT14_RECOVERY", process_id="ZECP18", implementation_class="SIMULATE_ON_GRID",
              state_before={"effect_receipt": {"outcome": "UNKNOWN"}, "grid_N_before": 10, "grid_N_after": 7, "pending_work": ["verify-effect"]},
              decisive_delta={"executor_loss": True, "effect_outcome_verified": False},
              result_payload={"reconciled_state_candidate": {"effect_outcome": "UNKNOWN"}, "next_work_units": ["verify-effect-before-retry"], "rejoin_plan": {"preserve_process_identity": True, "new_N": 7}},
              state_after={"effect_outcome": "UNKNOWN", "grid_N": 7, "next_work": "verify-effect-before-retry", "blind_replay": False}, unknowns=["effect-outcome"]),
    ]

def _census_map(census: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    processes = census.get("processes")
    if not isinstance(processes, list):
        raise ValueError("CENSUS_PROCESSES_REQUIRED")
    return {p["id"]: p for p in processes if isinstance(p, dict) and "id" in p}

def _find_key(value: Any, forbidden: set[str], path: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for k, v in value.items():
            if str(k).lower() in forbidden:
                return f"{path}.{k}"
            got = _find_key(v, forbidden, f"{path}.{k}")
            if got:
                return got
    elif isinstance(value, list):
        for i, v in enumerate(value):
            got = _find_key(v, forbidden, f"{path}[{i}]")
            if got:
                return got
    return None

def audit(generated: list[dict[str, Any]], abi: dict[str, Any] | None = None, census: dict[str, Any] | None = None) -> dict[str, Any]:
    abi = abi or _load(ABI_PATH)
    census = census or _load(CENSUS_PATH)
    failures: list[str] = []
    if abi.get("schema") != "COGNITIVE_PROCESS_ABI/v1": failures.append("ABI_SCHEMA_DRIFT")
    if census.get("schema") != "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1": failures.append("CENSUS_SCHEMA_DRIFT")
    result_contract = abi.get("packet_types", {}).get(TARGET_KIND, {})
    required = result_contract.get("required", [])
    allowed_result_classes = set(result_contract.get("allowed_result_class", []))
    cmap = _census_map(census)
    seen_classes: set[str] = set()
    for row in generated:
        rid = row.get("case_id", "UNKNOWN")
        if row.get("schema") != ROW_SCHEMA: failures.append("ROW_SCHEMA_DRIFT:" + rid)
        if row.get("training_eligible") is not False or row.get("accepted_dataset_tokens_minted") != 0: failures.append("TRAINING_ADMISSION_LEAK:" + rid)
        if row.get("canonical_truth_allowed") is not False or row.get("direct_effect_authority") is not False: failures.append("ROW_AUTHORITY_LEAK:" + rid)
        if dg(row.get("state_before")) != row.get("state_before_digest"): failures.append("STATE_BEFORE_DIGEST_MISMATCH:" + rid)
        if dg(row.get("expected_state_after")) != row.get("expected_state_after_digest"): failures.append("STATE_AFTER_DIGEST_MISMATCH:" + rid)
        pid = row.get("process_id_evaluator_only")
        proc = cmap.get(pid)
        if proc is None:
            failures.append("UNKNOWN_PROCESS:" + rid); continue
        expected_class = proc.get("implementation_class"); seen_classes.add(str(expected_class))
        if row.get("implementation_class_evaluator_only") != expected_class: failures.append("IMPLEMENTATION_CLASS_MISMATCH:" + rid)
        if expected_class not in ALLOWED_MODEL_IMPLEMENTATION_CLASSES: failures.append("NONMODEL_AUTHORITY_PROCESS_TARGETED:" + rid)
        target = row.get("target")
        if type(target) is not dict:
            failures.append("TARGET_EXACT_DICT_REQUIRED:" + rid); continue
        missing = [f for f in required if f not in target]
        if missing: failures.append("TARGET_REQUIRED_FIELDS_MISSING:" + rid + ":" + ",".join(missing))
        if target.get("schema") != TARGET_KIND: failures.append("TARGET_SCHEMA_DRIFT:" + rid)
        if target.get("process_id") != pid: failures.append("TARGET_PROCESS_MISMATCH:" + rid)
        if target.get("result_class") not in allowed_result_classes: failures.append("TARGET_RESULT_CLASS_INVALID:" + rid)
        if target.get("result_class") == "EFFECT_RECEIPT": failures.append("MODEL_EFFECT_RECEIPT_FORBIDDEN:" + rid)
        payload_ref = target.get("result_payload_ref"); payload = payload_ref.get("payload") if isinstance(payload_ref, dict) else None
        if payload is None or dg(payload) != target.get("result_digest"): failures.append("RESULT_DIGEST_MISMATCH:" + rid)
        if _find_key(target, {"rule", "emit"}) is not None: failures.append("META_RULE_NARRATION_TARGET:" + rid)
        runtime = target.get("runtime_receipt")
        if not isinstance(runtime, dict) or runtime.get("model_runtime_observed") is not False: failures.append("RUNTIME_RECEIPT_SCOPE_FAIL:" + rid)
        if isinstance(runtime, dict) and (runtime.get("canonical_truth_minted") is not False or runtime.get("effect_executed") is not False): failures.append("TARGET_RUNTIME_AUTHORITY_LEAK:" + rid)
        if not set(row.get("required_unknowns_preserved") or []).issubset(set(target.get("unknowns") or [])): failures.append("UNKNOWN_COLLAPSE:" + rid)
        for p in target.get("db_write_proposals") or []:
            if p.get("status") != "CANDIDATE_ONLY" or p.get("commit") is not False: failures.append("DB_AUTHORITY_SELF_MINT:" + rid)
        for p in target.get("effect_request_candidates") or []:
            if p.get("status") != "CANDIDATE_ONLY" or p.get("executed") is not False: failures.append("EFFECT_AUTHORITY_SELF_MINT:" + rid)
        expected_transition_digest = dg({"process_id": pid, "state_before_digest": row.get("state_before_digest"), "decisive_semantic_delta": row.get("decisive_semantic_delta"), "result_digest": target.get("result_digest"), "expected_state_after_digest": row.get("expected_state_after_digest")})
        if row.get("transition_semantic_digest") != expected_transition_digest: failures.append("TRANSITION_SEMANTIC_DIGEST_MISMATCH:" + rid)
    missing_classes = ALLOWED_MODEL_IMPLEMENTATION_CLASSES - seen_classes
    if missing_classes: failures.append("TRAINABLE_IMPLEMENTATION_CLASS_COVERAGE_MISSING:" + ",".join(sorted(missing_classes)))
    return {
        "schema": AUDIT_SCHEMA, "pass": not failures, "rows": len(generated),
        "model_implementation_classes_covered": sorted(seen_classes & ALLOWED_MODEL_IMPLEMENTATION_CLASSES),
        "model_implementation_classes_required": sorted(ALLOWED_MODEL_IMPLEMENTATION_CLASSES),
        "meta_rule_targets": 0 if not any(x.startswith("META_RULE_NARRATION_TARGET:") for x in failures) else "FAIL",
        "machine_adjudicable_transition_targets": True,
        "claycode_roundtrip_status": "NOT_EXERCISED_BY_THIS_JSON_ONLY_PILOT_REQUIRES_BOUND_ADAPTER_BEFORE_PROMOTION",
        "training_eligible": False, "accepted_dataset_tokens_minted": 0, "training_credit_minted": 0,
        "failures": sorted(set(failures)),
    }

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path); ap.add_argument("--audit-out", type=Path); args = ap.parse_args()
    generated = rows(); result = audit(generated)
    if args.out:
        args.out.write_text("".join(cj(r) + "\n" for r in generated), encoding="utf-8"); result["dataset_sha256"] = hashlib.sha256(args.out.read_bytes()).hexdigest()
    if args.audit_out: args.audit_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["pass"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
