#!/usr/bin/env python3
"""Trigger-2 executable cognitive-transition pilot (issue #2022).

This successor is intentionally tiny and quarantined. It replaces meta-rule narration with
machine-adjudicable process-specific cognitive deltas for every currently trainable/non-
deterministic ZECP process class. Deterministic/store/effect authorities (ZECP01, 02, 11, 17)
are input/oracle boundaries and never supervised as model-minted outputs.

Rows are CANDIDATE_DATA_NOT_TRAINING_ELIGIBLE. The deterministic evaluator materializes the
full COGNITIVE_RESULT_PACKET/v1, computes exact result identity, and round-trips it through
the current ClayCode cognitive adapter. A PASS mints no accepted dataset tokens or training
credit.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from claycode_cognitive_protocol_adapter_v1 import roundtrip

ROW_SCHEMA = "TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_PILOT_ROW/v2"
TARGET_SCHEMA = "XENO_COGNITIVE_DELTA/v1"
PILOT_SCHEMA = "TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_PILOT/v2"
RESULT_SCHEMA = "COGNITIVE_RESULT_PACKET/v1"
WORK_SCHEMA = "COGNITIVE_WORK_PACKET/v1"

DETERMINISTIC_OR_STORE_ONLY = {"ZECP01", "ZECP02", "ZECP11", "ZECP17"}
TRAINABLE_PROCESS_IDS = (
    "ZECP03", "ZECP04", "ZECP05", "ZECP06", "ZECP07", "ZECP08", "ZECP09", "ZECP10",
    "ZECP12", "ZECP13", "ZECP14", "ZECP15", "ZECP16", "ZECP18", "ZECP19", "ZECP20",
)
IMPLEMENTATION_CLASS = {
    **{p: "SIMULATE_ON_GRID" for p in ("ZECP03","ZECP04","ZECP05","ZECP06","ZECP07","ZECP08","ZECP09","ZECP10","ZECP12","ZECP15","ZECP16","ZECP18","ZECP19")},
    "ZECP13": "EXTERNAL_STRONG_MODEL_BRIDGE",
    "ZECP14": "EXTERNAL_STRONG_MODEL_BRIDGE",
    "ZECP20": "OPTIONAL_CAUSAL_RESEARCH",
}
OUTPUT_KEYS = {
    "ZECP03": {"working_state_candidate", "missing_state_questions"},
    "ZECP04": {"attention_slice", "deferred_refs", "uncertainty_set"},
    "ZECP05": {"goal_state_candidate", "completion_tests"},
    "ZECP06": {"work_graph_candidate", "work_units", "replan_conditions"},
    "ZECP07": {"alternative_set", "uncertainty_readout", "discriminator_candidates"},
    "ZECP08": {"candidate_result", "candidate_action", "confidence_readout"},
    "ZECP09": {"quality_readout", "contradiction_flags", "revision_request"},
    "ZECP10": {"workspace_selection", "broadcast_packet", "reentry_refs"},
    "ZECP12": {"compressed_state_packet", "loss_manifest", "reentry_binding"},
    "ZECP13": {"claude_handoff_packet"},
    "ZECP14": {"bridge_return_packet", "evidence_candidates", "workspace_reentry_candidate"},
    "ZECP15": {"state_update_proposal", "memory_update_proposal", "provenance_refs"},
    "ZECP16": {"effect_request_candidate", "precondition_refs"},
    "ZECP18": {"reconciled_state_candidate", "next_work_units", "rejoin_plan"},
    "ZECP19": {"typed_cognitive_packet", "transform_spec"},
    "ZECP20": {"jspace_measurement", "causal_probe_request", "credit_scope"},
}
FORBIDDEN_MODEL_AUTHORITY_KEYS = {
    "admission_grant", "capability_grant", "capability_authority", "canonical_commit",
    "canonical_truth", "effect_receipt", "effect_executed", "effect_authority",
    "lease_grant", "scheduler_lease", "verified_external_outcome", "global_jspace_causal_credit",
}

def cj(v: Any) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def dg(v: Any) -> str:
    return hashlib.sha256(cj(v).encode("utf-8")).hexdigest()

def ref(kind: str, name: str, version: int = 1) -> dict[str, Any]:
    payload = {"kind": kind, "name": name, "version": version}
    return {"ref": f"{kind}://{name}@{version}", "digest": dg(payload), "provenance": "SYNTHETIC_PILOT_ORACLE"}

BASE_STATE = {
    "task_ref": ref("task", "trigger2-pilot"),
    "goal_ref": ref("db-goal", "preserve-evidence-boundaries", 12),
    "evidence_ref": ref("evidence", "e-current", 7),
    "counterevidence_ref": ref("evidence", "e-minority", 3),
    "workspace_ref": ref("workspace", "s1", 41),
}

CASES: dict[str, dict[str, Any]] = {
    "ZECP03": {
        "delta": "Durable goal/evidence refs resolve, but resource ceiling is absent.",
        "payload": {
            "working_state_candidate": {"task_status":"READY_WITH_UNKNOWN","goal_ref":BASE_STATE["goal_ref"]["ref"],"evidence_status":"CURRENT"},
            "missing_state_questions": ["resource_ceiling"],
        },
        "unknowns": ["resource_ceiling"],
        "state_after": {"working_state":"RECONSTRUCTED_BOUNDED","resource_ceiling":"UNKNOWN"},
    },
    "ZECP04": {
        "delta": "Capacity admits two items; minority counterevidence does not fit active attention.",
        "payload": {
            "attention_slice":[BASE_STATE["evidence_ref"]["ref"],BASE_STATE["goal_ref"]["ref"]],
            "deferred_refs":[BASE_STATE["counterevidence_ref"]["ref"]],
            "uncertainty_set":["minority_counterevidence_deferred_not_false"],
        },
        "state_after":{"attention_count":2,"deferred_count":1,"minority_erased":False},
    },
    "ZECP05": {
        "delta": "Temporary preference conflicts with the durable evidence-bound goal.",
        "payload": {
            "goal_state_candidate":{"active_goal_ref":BASE_STATE["goal_ref"]["ref"],"subgoal":"prepare_candidate_transition_pilot","conflict":"TEMPORARY_PREFERENCE_REJECTED"},
            "completion_tests":["all_trainable_processes_covered","no_authority_self_mint","claycode_roundtrip"],
        },
        "state_after":{"durable_goal_changed":False,"subgoal_status":"CANDIDATE"},
    },
    "ZECP06": {
        "delta": "Prerequisite for work unit two is falsified before execution.",
        "payload": {
            "work_graph_candidate":{"revision":2,"preserve_prior_branch":True},
            "work_units":[{"id":"w1","status":"KEEP"},{"id":"w2","status":"BLOCKED"},{"id":"w2r","status":"CANDIDATE_REPLAN"}],
            "replan_conditions":["prerequisite_w2_false"],
        },
        "state_after":{"plan_revision":2,"stale_unit_executed":False},
    },
    "ZECP07": {
        "delta": "Alternative A has majority support, but no causal discriminator exists and one source may be stale.",
        "payload": {
            "alternative_set":[{"id":"A","status":"LIVE"},{"id":"B","status":"LIVE"}],
            "uncertainty_readout":{"resolved":False,"reason":"NO_DISCRIMINATOR"},
            "discriminator_candidates":["refresh_stale_source","run_causal_test"],
        },
        "state_after":{"resolved_hypothesis":"UNKNOWN","live_alternatives":["A","B"]},
        "unknowns":["resolved_hypothesis"],
    },
    "ZECP08": {
        "delta": "Typed inference supports one next action, but confidence cannot become authority.",
        "payload": {
            "candidate_result":{"claim":"dependency_x_precedes_y","evidence_ref":BASE_STATE["evidence_ref"]["ref"]},
            "candidate_action":{"type":"VERIFY_DEPENDENCY","target":"x->y"},
            "confidence_readout":0.74,
        },
        "state_after":{"candidate_count":1,"canonical_fact_added":False},
    },
    "ZECP09": {
        "delta": "Candidate conclusion contradicts minority evidence and collapses UNKNOWN into false.",
        "payload": {
            "quality_readout":{"status":"NEEDS_REVISION","coverage":0.67},
            "contradiction_flags":["minority_evidence_conflict","unknown_collapsed_to_false"],
            "revision_request":{"action":"REOPEN_HYPERPOSITION","required_refs":[BASE_STATE["counterevidence_ref"]["ref"]]},
        },
        "state_after":{"candidate_status":"NEEDS_REVISION","unknown_restored":True},
    },
    "ZECP10": {
        "delta": "One candidate wins workspace competition; later uptake is observed but truth is not implied.",
        "payload": {
            "workspace_selection":{"winner":"cand-7","reason":"salience_and_task_fit"},
            "broadcast_packet":{"source":"cand-7","workspace_epoch":42,"candidate_only":True},
            "reentry_refs":["reentry://cand-7@42"],
        },
        "state_after":{"workspace_epoch":42,"truth_status":"UNCHANGED_CANDIDATE_ONLY"},
    },
    "ZECP12": {
        "delta": "State must fit a hard budget while retaining decision-relevant dissent/provenance.",
        "payload": {
            "compressed_state_packet":{"goal_ref":BASE_STATE["goal_ref"]["ref"],"active_evidence":[BASE_STATE["evidence_ref"]["ref"]]},
            "loss_manifest":{"dropped":["verbose_narration"],"retained_counterevidence":[BASE_STATE["counterevidence_ref"]["ref"]]},
            "reentry_binding":{"workspace_ref":BASE_STATE["workspace_ref"]["ref"],"retrieval_available":True},
        },
        "state_after":{"compressed":True,"counterevidence_retrievable":True},
    },
    "ZECP13": {
        "delta": "Claude Code is available only through the exposed structured-text/tool interface.",
        "payload": {
            "claude_handoff_packet":{"bridge_id":"bridge-13","direction":"GRID_TO_CLAUDE","causal_event_id":"__COPY_CAUSAL_EVENT_ID__","work_id":"__COPY_WORK_ID__","workspace_epoch":41,"interface_class":"STRUCTURED_TEXT","payload_ref":"candidate://handoff/13","payload_digest":dg({"payload_ref":"candidate://handoff/13"}),"state_refs":[BASE_STATE["goal_ref"]["ref"],BASE_STATE["evidence_ref"]["ref"]],"tool_scope_ref":"capability://claude-code-readwrite-bounded","request_or_result_identity":"request-candidate-13"}
        },
        "state_after":{"handoff_status":"CANDIDATE_READY","hidden_activation_access":"UNKNOWN"},
        "unknowns":["hidden_activation_access"],
    },
    "ZECP14": {
        "delta": "Claude returns an assertion plus a tool result; only the tool result has external evidence status.",
        "payload": {
            "bridge_return_packet":{"bridge_id":"bridge-13","request_receipt_ref":"oracle://bridge-request/13","assertion_status":"CANDIDATE","tool_result_ref":"tool-result://13"},
            "evidence_candidates":[{"ref":"tool-result://13","class":"OBSERVED_TOOL_RESULT"},{"ref":"claude-assertion://13","class":"MODEL_ASSERTION"}],
            "workspace_reentry_candidate":{"target_epoch":42,"candidate_only":True},
        },
        "state_after":{"tool_evidence_separated":True,"claude_assertion_canonical":False},
    },
    "ZECP15": {
        "delta": "Verified outcome may justify memory update, but model has no commit authority.",
        "payload": {
            "state_update_proposal":{"field":"strategy_hint","value":"prefer_exact_refs"},
            "memory_update_proposal":{"candidate":"exact refs reduced ambiguity","commit_requested":True},
            "provenance_refs":["outcome://verified/15",BASE_STATE["evidence_ref"]["ref"]],
        },
        "db_write_proposals":[{"proposal_id":"db-proposal-15","target":"memory/strategy_hint","value_ref":"candidate://memory/15","status":"PROPOSAL_ONLY"}],
        "state_after":{"canonical_memory_changed":False,"proposal_emitted":True},
    },
    "ZECP16": {
        "delta": "Selected intent needs a bounded external tool request; execution remains behind EffectGate.",
        "payload": {
            "effect_request_candidate":{"tool":"example.read_only_probe","args_ref":"candidate://args/16","capability_scope_ref":"capability://probe/read"},
            "precondition_refs":[BASE_STATE["goal_ref"]["ref"],BASE_STATE["evidence_ref"]["ref"]],
        },
        "effect_request_candidates":[{"proposal_id":"effect-candidate-16","tool":"example.read_only_probe","status":"CANDIDATE_ONLY"}],
        "state_after":{"effect_execution_status":"NOT_EXECUTED_BY_MODEL","effect_request_status":"CANDIDATE"},
    },
    "ZECP18": {
        "delta": "External submission outcome is UNKNOWN and one executor disappeared during resize.",
        "payload": {
            "reconciled_state_candidate":{"effect_outcome":"UNKNOWN","blind_replay":False},
            "next_work_units":[{"id":"verify-outcome","priority":100}],
            "rejoin_plan":{"preserve_work_id":True,"replacement_executor_allowed":True,"requested_N_before":10,"requested_N_after":6},
        },
        "unknowns":["effect_outcome"],
        "state_after":{"effect_outcome":"UNKNOWN","replay_allowed":False,"process_identity_preserved":True},
    },
    "ZECP19": {
        "delta": "A typed cognitive payload must be represented in ClayCode without semantic or authority drift.",
        "payload": {
            "typed_cognitive_packet":{"kind":"CANDIDATE_STATE","value":{"goal_ref":BASE_STATE["goal_ref"]["ref"],"status":"OPEN"}},
            "transform_spec":{"representation":"CLAYCODE_COGNITIVE_ENVELOPE/v1","semantic_identity_required":True},
        },
        "state_after":{"semantic_identity_preserved":True,"representation_authority":False},
    },
    "ZECP20": {
        "delta": "Observable text-level reentry exists, but no model-specific causal intervention receipt is available.",
        "result_class":"MEASUREMENT",
        "payload": {
            "jspace_measurement":{"observable_interface":"TEXT_LEVEL_REENTRY","representation_effect":"UNKNOWN","causal_effect":"UNKNOWN"},
            "causal_probe_request":{"controls":["SIGN_FLIP","LESION","PERMUTED_SAME_NORM","WRONG_LAYER"],"status":"REQUEST_ONLY"},
            "credit_scope":"NO_CAUSAL_JSPACE_CREDIT",
        },
        "unknowns":["representation_effect","causal_effect"],
        "state_after":{"causal_status":"UNKNOWN","credit_decision":"DETERMINISTIC_EVALUATOR_ONLY"},
    },
}

def _find_forbidden(v: Any, path: str = "$") -> str | None:
    if isinstance(v, dict):
        for k, child in v.items():
            if str(k).lower() in FORBIDDEN_MODEL_AUTHORITY_KEYS:
                return f"{path}.{k}"
            hit = _find_forbidden(child, f"{path}.{k}")
            if hit:
                return hit
    elif isinstance(v, list):
        for i, child in enumerate(v):
            hit = _find_forbidden(child, f"{path}[{i}]")
            if hit:
                return hit
    return None

def work_packet(process_id: str, i: int) -> dict[str, Any]:
    return {
        "schema": WORK_SCHEMA,
        "causal_event_id": f"event-pilot-{i:02d}",
        "admission_id": f"admission-pilot-{i:02d}",
        "generation": 9,
        "work_id": f"work-pilot-{i:02d}",
        "process_id": process_id,
        "parent_work_ids": [],
        "workspace_epoch": 41,
        "state_snapshot_ref": "dbsnapshot://pilot@41",
        "input_refs": [BASE_STATE["task_ref"], BASE_STATE["goal_ref"], BASE_STATE["evidence_ref"]],
        "epistemic_inputs": [
            {"ref":BASE_STATE["evidence_ref"]["ref"],"status":"OBSERVED"},
            {"ref":BASE_STATE["counterevidence_ref"]["ref"],"status":"HYPOTHESIS"},
        ],
        "capability_scope_ref": "capability://xeno-cognition/candidate-only",
        "resource_budget": {"token_budget":384,"time_budget_ms":2000},
        "grid_runtime": {"requested_N":10,"observed_available_N":8,"grid_instance_id":"grid-pilot"},
        "route_policy_ref": "route-policy://variable-n/v1",
        "completion_contract": {"success":"machine_adjudicated_transition","failure":"authority_or_semantic_drift","unknown":"preserve_unknown"},
    }

def _bind_input_markers(value: Any, w: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {k:_bind_input_markers(v,w) for k,v in value.items()}
    if isinstance(value, list):
        return [_bind_input_markers(v,w) for v in value]
    if value == "__COPY_CAUSAL_EVENT_ID__":
        return w["causal_event_id"]
    if value == "__COPY_WORK_ID__":
        return w["work_id"]
    return value

def supervision_target(process_id: str, spec: dict[str, Any], w: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": TARGET_SCHEMA,
        "process_id": process_id,
        "result_class": spec.get("result_class","CANDIDATE"),
        "candidate_payload": _bind_input_markers(copy.deepcopy(spec["payload"]), w),
        "unknowns": list(spec.get("unknowns", [])),
        "db_write_proposals": _bind_input_markers(copy.deepcopy(spec.get("db_write_proposals", [])), w),
        "effect_request_candidates": _bind_input_markers(copy.deepcopy(spec.get("effect_request_candidates", [])), w),
        "workspace_reentry_proposal": _bind_input_markers(copy.deepcopy(spec.get("workspace_reentry")), w),
        "expected_state_after": _bind_input_markers(copy.deepcopy(spec["state_after"]), w),
    }

def materialize_result_packet(w: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    semantic_core = {
        "process_id": target["process_id"],
        "result_class": target["result_class"],
        "candidate_payload": target["candidate_payload"],
        "unknowns": target["unknowns"],
        "db_write_proposals": target["db_write_proposals"],
        "effect_request_candidates": target["effect_request_candidates"],
        "workspace_reentry_proposal": target["workspace_reentry_proposal"],
        "expected_state_after": target["expected_state_after"],
    }
    result_digest = dg(semantic_core)
    result_id = "result-" + result_digest[:24]
    proposal = target["workspace_reentry_proposal"]
    target_epoch = w["workspace_epoch"]
    if isinstance(proposal, dict) and isinstance(proposal.get("target_epoch"), int):
        target_epoch = proposal["target_epoch"]
    reentry_core = {
        "source_result_id":result_id,
        "source_process_id":target["process_id"],
        "causal_event_id":w["causal_event_id"],
        "from_workspace_epoch":w["workspace_epoch"],
        "to_workspace_epoch":target_epoch,
        "reentry_payload_ref":"candidate-reentry://sha256/" + result_digest,
        "observed_downstream_change":"UNKNOWN",
    }
    wr = {**reentry_core, "reentry_digest":dg(reentry_core)}
    packet = {
        "schema": RESULT_SCHEMA,
        "causal_event_id": w["causal_event_id"],
        "admission_id": w["admission_id"],
        "generation": w["generation"],
        "work_id": w["work_id"],
        "process_id": target["process_id"],
        "executor_binding": {
            "grid_instance_id":w["grid_runtime"]["grid_instance_id"],
            "requested_N":w["grid_runtime"]["requested_N"],
            "available_N":w["grid_runtime"]["observed_available_N"],
            "executor_id":"executor-pilot",
            "lease_id":"oracle-runtime-lease",
            "process_id":target["process_id"],
            "runtime_identity":"SYNTHETIC_EVALUATOR_ONLY",
            "started_at":"SYNTHETIC",
            "ended_at":"SYNTHETIC",
        },
        "result_id": result_id,
        "result_class": target["result_class"],
        "result_payload_ref": "candidate-payload://sha256/" + result_digest,
        "result_digest": result_digest,
        "evidence_refs": [x["ref"] for x in w["input_refs"] if isinstance(x,dict) and "ref" in x],
        "unknowns": copy.deepcopy(target["unknowns"]),
        "db_write_proposals": copy.deepcopy(target["db_write_proposals"]),
        "effect_request_candidates": copy.deepcopy(target["effect_request_candidates"]),
        "workspace_reentry": wr,
        "runtime_receipt": {"status":"SYNTHETIC_EVALUATOR_ONLY","model_runtime_credit":0},
        "candidate_payload": copy.deepcopy(target["candidate_payload"]),
        "expected_state_after": copy.deepcopy(target["expected_state_after"]),
    }
    return packet

def make_row(process_id: str, i: int) -> dict[str, Any]:
    spec = CASES[process_id]
    w = work_packet(process_id, i)
    t = supervision_target(process_id, spec, w)
    packet = materialize_result_packet(w, t)
    envelope, decoded = roundtrip(RESULT_SCHEMA, packet)
    assert decoded == packet
    return {
        "schema": ROW_SCHEMA,
        "status":"CANDIDATE_DATA_NOT_TRAINING_ELIGIBLE",
        "training_eligible":False,
        "accepted_dataset_tokens":0,
        "process_id_evaluator_only":process_id,
        "implementation_class_evaluator_only":IMPLEMENTATION_CLASS[process_id],
        "model_visible":{
            "work_packet":w,
            "state_before":copy.deepcopy(BASE_STATE),
            "decisive_semantic_delta":spec["delta"],
        },
        "supervision_target":t,
        "oracle_evaluator_only":{
            "result_packet":packet,
            "semantic_digest":packet["result_digest"],
            "claycode_roundtrip":{
                "packet_digest":envelope.packet_digest,
                "clay_source_sha256":envelope.clay_source_sha256,
                "clay_semantic_hash":envelope.clay_semantic_hash,
                "clay_grammar_sha256":envelope.clay_grammar_sha256,
            },
            "authority_fields":"COPY_FROM_BOUND_WORK_PACKET_OR_DETERMINISTIC_ORACLE_ONLY",
        },
        "credit":{
            "training_row_admitted":0,
            "training":0,
            "jspace_causal":0,
            "whole_hcu":0,
            "whole_entityos":0,
        },
    }

def validate_row(row: dict[str, Any]) -> None:
    if row.get("schema") != ROW_SCHEMA or row.get("training_eligible") is not False:
        raise ValueError("ROW_QUARANTINE_REQUIRED")
    pid = row.get("process_id_evaluator_only")
    if pid not in TRAINABLE_PROCESS_IDS or pid in DETERMINISTIC_OR_STORE_ONLY:
        raise ValueError("PROCESS_NOT_TRAINABLE_PILOT:" + str(pid))
    mv = row.get("model_visible")
    target = row.get("supervision_target")
    oracle = row.get("oracle_evaluator_only")
    if not isinstance(mv,dict) or not isinstance(target,dict) or not isinstance(oracle,dict):
        raise ValueError("ROW_SECTIONS_REQUIRED")
    w = mv.get("work_packet")
    if not isinstance(w,dict) or w.get("process_id") != pid or target.get("process_id") != pid:
        raise ValueError("PROCESS_BINDING_MISMATCH:" + pid)
    if target.get("schema") != TARGET_SCHEMA:
        raise ValueError("TARGET_SCHEMA_MISMATCH:" + pid)
    payload = target.get("candidate_payload")
    if not isinstance(payload,dict) or not OUTPUT_KEYS[pid].issubset(payload):
        raise ValueError("EXECUTABLE_OUTPUT_FIELDS_MISSING:" + pid)
    hit = _find_forbidden(target)
    if hit:
        raise ValueError("MODEL_AUTHORITY_SMUGGLING:" + hit)
    if pid != "ZECP16" and target.get("effect_request_candidates"):
        raise ValueError("UNEXPECTED_EFFECT_CANDIDATE:" + pid)
    if pid == "ZECP16" and not target.get("effect_request_candidates"):
        raise ValueError("ZECP16_EFFECT_CANDIDATE_REQUIRED")
    if pid != "ZECP15" and target.get("db_write_proposals"):
        raise ValueError("UNEXPECTED_DB_WRITE_PROPOSAL:" + pid)
    if pid == "ZECP20":
        if target.get("result_class") != "MEASUREMENT":
            raise ValueError("ZECP20_MEASUREMENT_CLASS_REQUIRED")
        if target["candidate_payload"].get("credit_scope") != "NO_CAUSAL_JSPACE_CREDIT":
            raise ValueError("ZECP20_CAUSAL_CREDIT_FORBIDDEN")

    expected = materialize_result_packet(w, target)
    if oracle.get("result_packet") != expected:
        raise ValueError("ORACLE_RESULT_PACKET_MISMATCH:" + pid)
    if oracle.get("semantic_digest") != expected["result_digest"]:
        raise ValueError("ORACLE_SEMANTIC_DIGEST_MISMATCH:" + pid)
    envelope, decoded = roundtrip(RESULT_SCHEMA, expected)
    if decoded != expected:
        raise ValueError("CLAYCODE_ROUNDTRIP_MISMATCH:" + pid)
    recorded = oracle.get("claycode_roundtrip")
    actual = {
        "packet_digest":envelope.packet_digest,
        "clay_source_sha256":envelope.clay_source_sha256,
        "clay_semantic_hash":envelope.clay_semantic_hash,
        "clay_grammar_sha256":envelope.clay_grammar_sha256,
    }
    if recorded != actual:
        raise ValueError("CLAYCODE_ORACLE_IDENTITY_MISMATCH:" + pid)

def rows() -> list[dict[str, Any]]:
    out = [make_row(pid, i) for i,pid in enumerate(TRAINABLE_PROCESS_IDS,1)]
    for row in out:
        validate_row(row)
    return out

def run() -> dict[str, Any]:
    out = rows()
    return {
        "schema":PILOT_SCHEMA,
        "pass":True,
        "row_count":len(out),
        "covered_process_ids":[r["process_id_evaluator_only"] for r in out],
        "deterministic_or_store_only_not_supervised":sorted(DETERMINISTIC_OR_STORE_ONLY),
        "all_trainable_processes_covered":set(r["process_id_evaluator_only"] for r in out) == set(TRAINABLE_PROCESS_IDS),
        "accepted_dataset_tokens":0,
        "training_eligible_rows":0,
        "training_executed":False,
        "training_credit":0,
        "evidence_boundary":"Executable transition donor + deterministic JSON/ClayCode roundtrip component only; no dataset admission/model runtime/J-Space causal/whole-HCU/whole-EntityOS credit.",
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", type=Path)
    args = ap.parse_args()
    out = rows()
    if args.jsonl:
        args.jsonl.parent.mkdir(parents=True, exist_ok=True)
        args.jsonl.write_text("".join(cj(r)+"\n" for r in out), encoding="utf-8")
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
