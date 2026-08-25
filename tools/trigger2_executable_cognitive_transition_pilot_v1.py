#!/usr/bin/env python3
"""Trigger-2 executable cognitive-transition pilot for issue #2022.

Source/generator validation only. This file does not admit dataset rows, execute
training, grant canonical truth/effect authority, or mint runtime/J-Space credit.

The pilot replaces meta-rule narration with concrete, machine-adjudicable
state_before -> semantic_delta -> CognitiveResultPacket -> state_after examples.
Every expected result packet is also round-tripped through the existing
BASE-D V18 ClayCode cognitive protocol adapter.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from claycode_cognitive_protocol_adapter_v1 import (
    ClayCodeCognitiveProtocolError,
    roundtrip,
    validate_packet,
)

SCHEMA = "CLAY_TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_PILOT/v1"
ROW_SCHEMA = "ENTITYOS_HCU_EXECUTABLE_TRANSITION_CANDIDATE/v1"
WORK_KIND = "COGNITIVE_WORK_PACKET/v1"
RESULT_KIND = "COGNITIVE_RESULT_PACKET/v1"

SOURCE_BINDINGS = {
    "census_path": "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json",
    "census_blob_sha1": "ceeb9efc04ef6fdc2ae061c72575f9f49834f2fa",
    "abi_path": "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json",
    "abi_blob_sha1": "f6eab6f097cdabb6f297b110b980fb7e07aad5dd",
    "claycode_protocol_path": "research_entity/global/CLAYCODE_COGNITIVE_PROTOCOL_v1.json",
    "claycode_protocol_blob_sha1": "ab9bd965fe3412788a813699c93fe7de6f8e2732",
    "claycode_adapter_path": "tools/claycode_cognitive_protocol_adapter_v1.py",
    "claycode_adapter_blob_sha1": "d9691c89c29114063cc73880b5dfe73513080b61",
    "predecessor_generator_path": "tools/trigger2_cognitive_process_trajectory_generator_v1.py",
    "predecessor_generator_blob_sha1": "06efd3cd992fd9d38337b9f4d45b0d746ccb684d",
    "coordination_issue": 2022,
}

TRAINABLE_IMPLEMENTATION_CLASSES = {
    "SIMULATE_ON_GRID",
    "EXTERNAL_STRONG_MODEL_BRIDGE",
    "OPTIONAL_CAUSAL_RESEARCH",
}
ORACLE_ONLY_IMPLEMENTATION_CLASSES = {"STORE_IN_DB", "DETERMINISTIC_BOUNDARY"}

PROCESS_CLASS = {
    "ZECP03": "SIMULATE_ON_GRID",
    "ZECP07": "SIMULATE_ON_GRID",
    "ZECP13": "EXTERNAL_STRONG_MODEL_BRIDGE",
    "ZECP16": "SIMULATE_ON_GRID",
    "ZECP18": "SIMULATE_ON_GRID",
    "ZECP19": "SIMULATE_ON_GRID",
    "ZECP20": "OPTIONAL_CAUSAL_RESEARCH",
}

FORBIDDEN_TARGET_KEYS = {
    "rule",
    "canonical_commit",
    "capability_grant",
    "effect_receipt_minted_by_model",
    "verified_external_outcome",
    "scheduler_lease_minted_by_model",
    "admission_id_minted_by_model",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def ref(ref_id: str, digest: str, provenance: str) -> dict[str, Any]:
    return {"ref_id": ref_id, "digest": digest, "provenance": provenance}


def work_packet(
    process_id: str,
    case_id: str,
    *,
    epistemic_inputs: list[dict[str, Any]],
    input_refs: list[dict[str, Any]],
    state_snapshot_ref: str = "dbsnap://s1/epoch-42/digest-a42",
    requested_n: int = 10,
    available_n: int = 10,
) -> dict[str, Any]:
    return {
        "schema": WORK_KIND,
        "causal_event_id": f"ce-{case_id}",
        "admission_id": f"adm-observed-{case_id}",
        "generation": 7,
        "work_id": f"work-{case_id}",
        "process_id": process_id,
        "parent_work_ids": [],
        "workspace_epoch": 42,
        "state_snapshot_ref": state_snapshot_ref,
        "input_refs": input_refs,
        "epistemic_inputs": epistemic_inputs,
        "capability_scope_ref": "capref://readonly-cognition-v1",
        "resource_budget": {"max_output_tokens": 192, "deadline_class": "BOUNDED"},
        "grid_runtime": {"requested_N": requested_n, "observed_available_N": available_n},
        "route_policy_ref": "policy://variable-n-role-flex-v1",
        "completion_contract": {"status": "MACHINE_ADJUDICABLE", "require_exact_semantics": True},
    }


def result_packet(
    work: dict[str, Any],
    case_id: str,
    payload: dict[str, Any],
    *,
    evidence_refs: list[str],
    unknowns: list[str],
    db_write_proposals: list[dict[str, Any]] | None = None,
    effect_request_candidates: list[dict[str, Any]] | None = None,
    workspace_reentry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload_digest = sha256_value(payload)
    return {
        "schema": RESULT_KIND,
        "causal_event_id": work["causal_event_id"],
        "admission_id": work["admission_id"],
        "generation": work["generation"],
        "work_id": work["work_id"],
        "process_id": work["process_id"],
        "executor_binding": {
            "grid_instance_id": "grid-pilot-a",
            "requested_N": work["grid_runtime"]["requested_N"],
            "available_N": work["grid_runtime"]["observed_available_N"],
            "executor_id": "executor-role-flex",
            "lease_id": "oracle-lease-observed",
            "process_id": work["process_id"],
            "runtime_identity": "SOURCE_PILOT_NO_MODEL_RUNTIME",
            "started_at": "UNKNOWN",
            "ended_at": "UNKNOWN",
        },
        "result_id": f"result-{case_id}",
        "result_class": "CANDIDATE" if work["process_id"] != "ZECP20" else "MEASUREMENT",
        "result_payload_ref": f"inline-sha256:{payload_digest}",
        "result_digest": payload_digest,
        "evidence_refs": evidence_refs,
        "unknowns": unknowns,
        "db_write_proposals": db_write_proposals or [],
        "effect_request_candidates": effect_request_candidates or [],
        "workspace_reentry": workspace_reentry or {
            "source_result_id": f"result-{case_id}",
            "target_workspace_epoch": 43,
            "causal_event_id": work["causal_event_id"],
            "acceptance": "CANDIDATE_ONLY_NOT_ADMITTED",
        },
        "runtime_receipt": {
            "status": "SOURCE_PILOT_ONLY",
            "model_runtime_identity": "UNKNOWN_NOT_EXECUTED",
            "tool_runtime_identity": "NONE",
        },
    }


def case(
    row_id: str,
    process_id: str,
    state_before: dict[str, Any],
    semantic_delta: str,
    expected_payload: dict[str, Any],
    expected_result: dict[str, Any],
    state_after: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": ROW_SCHEMA,
        "row_id": row_id,
        "evidence_class": "METHOD_ONLY",
        "training_eligible": False,
        "accepted_dataset_credit": 0,
        "implementation_class_evaluator_only": PROCESS_CLASS[process_id],
        "process_id_evaluator_only": process_id,
        "provenance_ancestry_id": f"trigger2-executable-transition-pilot-{row_id.lower()}",
        "state_before": state_before,
        "decisive_semantic_delta": semantic_delta,
        "expected_payload": expected_payload,
        "expected_result_packet": expected_result,
        "expected_state_after": state_after,
        "semantic_digest": sha256_value({
            "process_id": process_id,
            "state_before": state_before,
            "decisive_semantic_delta": semantic_delta,
            "expected_payload": expected_payload,
            "expected_result_packet": expected_result,
            "expected_state_after": state_after,
        }),
        "authority_boundary": {
            "model_may_mint_canonical_fact": False,
            "model_may_mint_capability": False,
            "model_may_mint_effect_receipt": False,
            "deterministic_store_boundary_is_oracle_input": True,
        },
        "source_bindings": SOURCE_BINDINGS,
    }


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    w = work_packet(
        "ZECP03", "working-state-missing",
        epistemic_inputs=[
            {"status": "OBSERVED", "claim": "durable goal is preserve evidence boundaries", "ref": "dbref://goal/17"},
            {"status": "UNKNOWN", "claim": "owner_deadline", "ref": "NONE"},
        ],
        input_refs=[ref("dbref://goal/17", "sha256:goal17", "ZECP02_RETRIEVAL_RECEIPT")],
    )
    p = {
        "working_state_candidate": {"active_goal_ref": "dbref://goal/17", "owner_deadline": "UNKNOWN"},
        "missing_state_questions": ["owner_deadline"],
    }
    r = result_packet(w, "working-state-missing", p, evidence_refs=["dbref://goal/17"], unknowns=["owner_deadline"])
    cases.append(case("T2XTR01", "ZECP03", w, "OWNER_DEADLINE_MISSING", p, r,
                      {"workspace_candidate": p, "canonical_state_changed": False}))

    w = work_packet(
        "ZECP07", "hyperposition-no-discriminator",
        epistemic_inputs=[
            {"status": "HYPOTHESIS", "claim": "A explains failure", "ref": "hyp://A"},
            {"status": "HYPOTHESIS", "claim": "B explains failure", "ref": "hyp://B"},
            {"status": "OBSERVED", "claim": "8 of 10 modules prefer A", "ref": "obs://vote/8of10"},
        ],
        input_refs=[ref("obs://vote/8of10", "sha256:votes", "WORKSPACE_MEASUREMENT")],
    )
    p = {
        "alternative_set": [
            {"id": "A", "status": "UNRESOLVED", "evidence_refs": ["obs://vote/8of10"]},
            {"id": "B", "status": "UNRESOLVED", "evidence_refs": []},
        ],
        "uncertainty_readout": "UNRESOLVED_NO_CAUSAL_DISCRIMINATOR",
        "discriminator_candidates": ["probe://distinguish-A-vs-B"],
    }
    r = result_packet(w, "hyperposition-no-discriminator", p, evidence_refs=["obs://vote/8of10"], unknowns=["truth_of_A", "truth_of_B"])
    cases.append(case("T2XTR02", "ZECP07", w, "MAJORITY_WITHOUT_CAUSAL_DISCRIMINATOR", p, r,
                      {"hyperposition": ["A", "B"], "collapsed": False, "canonical_state_changed": False}))

    w = work_packet(
        "ZECP13", "claude-handoff-exposed-interface",
        epistemic_inputs=[
            {"status": "OBSERVED", "claim": "Claude bridge exposes structured text/tool protocol", "ref": "bridgecap://structured-tool"},
            {"status": "UNKNOWN", "claim": "Claude hidden activations are exposed", "ref": "NONE"},
        ],
        input_refs=[ref("bridgecap://structured-tool", "sha256:bridgecap", "BRIDGE_CAPABILITY_RECEIPT")],
    )
    p = {
        "claude_handoff_packet": {
            "direction": "GRID_TO_CLAUDE",
            "interface_class": "TOOL_PROTOCOL",
            "work_id": w["work_id"],
            "state_refs": ["dbsnap://s1/epoch-42/digest-a42"],
            "tool_scope_ref": "toolscope://bounded-code-read",
        },
        "bridge_request_receipt": "UNKNOWN_UNTIL_DETERMINISTIC_BRIDGE_SUBMISSION",
        "activation_access": "UNKNOWN_NOT_CLAIMED",
    }
    r = result_packet(w, "claude-handoff-exposed-interface", p, evidence_refs=["bridgecap://structured-tool"], unknowns=["hidden_activation_access"])
    cases.append(case("T2XTR03", "ZECP13", w, "EXPOSED_BRIDGE_ONLY", p, r,
                      {"bridge_candidate": p["claude_handoff_packet"], "canonical_state_changed": False}))

    w = work_packet(
        "ZECP16", "effect-proposal-only",
        epistemic_inputs=[
            {"status": "OBSERVED", "claim": "capability reference permits proposal construction only", "ref": "capref://effect-proposal"},
        ],
        input_refs=[ref("capref://effect-proposal", "sha256:cap-proposal", "ZECP01_ORACLE")],
    )
    effect_candidate = {
        "schema": "EFFECT_REQUEST_CANDIDATE/v1",
        "action": "WRITE_CANDIDATE_ARTIFACT",
        "capability_scope_ref": "capref://effect-proposal",
        "precondition_refs": ["dbsnap://s1/epoch-42/digest-a42"],
        "execution_status": "NOT_EXECUTED",
    }
    p = {"effect_request_candidate": effect_candidate, "authority": "CANDIDATE_ONLY"}
    r = result_packet(w, "effect-proposal-only", p, evidence_refs=["capref://effect-proposal"], unknowns=[],
                      effect_request_candidates=[effect_candidate])
    cases.append(case("T2XTR04", "ZECP16", w, "COGNITIVE_INTENT_TO_EFFECT_PROPOSAL", p, r,
                      {"effect_candidate": effect_candidate, "real_effect_executed": False}))

    w = work_packet(
        "ZECP18", "unknown-effect-outcome",
        epistemic_inputs=[
            {"status": "OBSERVED", "claim": "submission may have been accepted before timeout", "ref": "effectreceipt://timeout-55"},
            {"status": "UNKNOWN", "claim": "provider side effect occurred", "ref": "effectreceipt://timeout-55"},
        ],
        input_refs=[ref("effectreceipt://timeout-55", "sha256:receipt55", "ZECP17_ORACLE")],
    )
    p = {
        "reconciled_state_candidate": {"external_outcome": "UNKNOWN"},
        "next_work_units": [{"kind": "VERIFY_OUTCOME", "ref": "effectreceipt://timeout-55"}],
        "rejoin_plan": {"blind_replay": False, "resume_after": "VERIFIED_OUTCOME_OR_EXPLICIT_POLICY"},
    }
    r = result_packet(w, "unknown-effect-outcome", p, evidence_refs=["effectreceipt://timeout-55"], unknowns=["external_outcome"])
    cases.append(case("T2XTR05", "ZECP18", w, "AMBIGUOUS_EXTERNAL_EFFECT_OUTCOME", p, r,
                      {"outcome": "UNKNOWN", "blind_replay": False, "canonical_state_changed": False}))

    w = work_packet(
        "ZECP19", "claycode-transform",
        epistemic_inputs=[
            {"status": "OBSERVED", "claim": "typed packet must preserve semantic identity across ClayCode envelope roundtrip", "ref": "protocol://v18"},
        ],
        input_refs=[ref("protocol://v18", "sha256:a788d13c", "CLAYCODE_COGNITIVE_PROTOCOL_V1")],
        requested_n=1,
        available_n=1,
    )
    p = {
        "claycode_packet": "DERIVED_BY_BOUND_V18_ADAPTER_FROM_RESULT_PACKET",
        "transform_receipt": {"semantic_identity": "MUST_EQUAL_JSON_PACKET_SEMANTICS", "authority": "NONE"},
    }
    r = result_packet(w, "claycode-transform", p, evidence_refs=["protocol://v18"], unknowns=[])
    cases.append(case("T2XTR06", "ZECP19", w, "JSON_TO_CLAYCODE_SEMANTIC_IDENTITY", p, r,
                      {"roundtrip_required": True, "canonical_state_changed": False}))

    w = work_packet(
        "ZECP20", "jspace-evidence-ceiling",
        epistemic_inputs=[
            {"status": "OBSERVED", "claim": "behavioral output changed under a probe", "ref": "probe://behavioral-1"},
            {"status": "UNKNOWN", "claim": "intended hidden representation caused the change", "ref": "NONE"},
        ],
        input_refs=[ref("probe://behavioral-1", "sha256:behavior1", "JSPACE_DIAGNOSTIC")],
    )
    p = {
        "jspace_measurement": {"behavioral_effect": "OBSERVED", "representation_causality": "UNKNOWN"},
        "causal_probe_receipt": "REQUIRES_EXACT_MODEL_SPECIFIC_CONTROLLED_RUNTIME",
        "credit_scope": "BEHAVIORAL_ONLY_NO_POSITIVE_CAUSAL_STEERING_LABEL",
    }
    r = result_packet(w, "jspace-evidence-ceiling", p, evidence_refs=["probe://behavioral-1"], unknowns=["representation_causality"])
    cases.append(case("T2XTR07", "ZECP20", w, "BEHAVIORAL_EFFECT_WITHOUT_REPRESENTATION_CAUSAL_PROOF", p, r,
                      {"jspace_causal_credit": 0, "representation_causality": "UNKNOWN"}))

    return cases


def adjudicate(case_row: dict[str, Any], candidate: dict[str, Any]) -> tuple[bool, str]:
    if type(candidate) is not dict:
        return False, "CANDIDATE_OBJECT_REQUIRED"
    if any(k in candidate for k in FORBIDDEN_TARGET_KEYS):
        return False, "FORBIDDEN_META_OR_AUTHORITY_KEY"
    if set(candidate) != {"expected_payload", "expected_result_packet", "expected_state_after"}:
        return False, "EXECUTABLE_TARGET_SHAPE_REQUIRED"

    packet = candidate["expected_result_packet"]
    try:
        validate_packet(RESULT_KIND, packet)
    except ClayCodeCognitiveProtocolError as exc:
        return False, f"RESULT_PACKET_INVALID:{exc}"

    if sha256_value(candidate["expected_payload"]) != packet["result_digest"]:
        return False, "PAYLOAD_RESULT_DIGEST_MISMATCH"
    if packet["result_payload_ref"] != f"inline-sha256:{packet['result_digest']}":
        return False, "PAYLOAD_REF_DIGEST_MISMATCH"

    expected = {
        "expected_payload": case_row["expected_payload"],
        "expected_result_packet": case_row["expected_result_packet"],
        "expected_state_after": case_row["expected_state_after"],
    }
    if sha256_value(candidate) != sha256_value(expected):
        return False, "SEMANTIC_TRANSITION_MISMATCH"

    envelope, decoded = roundtrip(RESULT_KIND, packet)
    if sha256_value(decoded) != sha256_value(packet):
        return False, "CLAYCODE_ROUNDTRIP_SEMANTIC_MISMATCH"
    if not envelope.clay_semantic_hash or not envelope.clay_grammar_sha256:
        return False, "CLAYCODE_V18_IDENTITY_MISSING"
    return True, "PASS_EXECUTABLE_TRANSITION_SOURCE_ONLY"


def mutation_suite(row: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    good = {
        "expected_payload": copy.deepcopy(row["expected_payload"]),
        "expected_result_packet": copy.deepcopy(row["expected_result_packet"]),
        "expected_state_after": copy.deepcopy(row["expected_state_after"]),
    }
    out: list[tuple[str, dict[str, Any]]] = []

    meta = {"rule": "describe what to do", "emit": ["some_fields"], "status": "PROCEED"}
    out.append(("META_RULE_NARRATION_SUBSTITUTE", meta))

    wrong_unknown = copy.deepcopy(good)
    if wrong_unknown["expected_result_packet"]["unknowns"]:
        wrong_unknown["expected_result_packet"]["unknowns"] = []
    else:
        wrong_unknown["expected_state_after"]["fabricated_unknown_resolution"] = "TRUE"
    out.append(("UNKNOWN_COLLAPSE_OR_FABRICATION", wrong_unknown))

    wrong_ref = copy.deepcopy(good)
    wrong_ref["expected_result_packet"]["generation"] += 1
    out.append(("GENERATION_IDENTITY_DRIFT", wrong_ref))

    authority = copy.deepcopy(good)
    authority["expected_result_packet"]["canonical_truth"] = True
    out.append(("MODEL_SELF_MINTS_CANONICAL_TRUTH", authority))

    effect = copy.deepcopy(good)
    effect["expected_result_packet"]["result_class"] = "EFFECT_RECEIPT"
    out.append(("NON_ZECP17_EFFECT_RECEIPT", effect))

    state_after = copy.deepcopy(good)
    state_after["expected_state_after"]["canonical_state_changed"] = True
    out.append(("DIRECT_CANONICAL_STATE_CHANGE", state_after))
    return out


def audit() -> dict[str, Any]:
    rows = build_cases()
    failures: list[str] = []
    mutation_rejections = 0
    roundtrip_passes = 0
    classes = {r["implementation_class_evaluator_only"] for r in rows}

    for row in rows:
        validate_packet(WORK_KIND, row["state_before"])
        expected = {
            "expected_payload": row["expected_payload"],
            "expected_result_packet": row["expected_result_packet"],
            "expected_state_after": row["expected_state_after"],
        }
        ok, reason = adjudicate(row, expected)
        if not ok:
            failures.append(f"{row['row_id']}:GOOD_TARGET_REJECTED:{reason}")
        else:
            roundtrip_passes += 1
        if "rule" in expected:
            failures.append(f"{row['row_id']}:META_RULE_KEY_PRESENT")

        for mutation_id, mutated in mutation_suite(row):
            accepted, mutation_reason = adjudicate(row, mutated)
            if accepted:
                failures.append(f"{row['row_id']}:MUTATION_ACCEPTED:{mutation_id}")
            else:
                mutation_rejections += 1

    missing_classes = TRAINABLE_IMPLEMENTATION_CLASSES - classes
    if missing_classes:
        failures.append("TRAINABLE_IMPLEMENTATION_CLASS_COVERAGE_MISSING:" + ",".join(sorted(missing_classes)))
    if classes & ORACLE_ONLY_IMPLEMENTATION_CLASSES:
        failures.append("ORACLE_ONLY_CLASS_SUPERVISED_AS_MODEL_TARGET")

    return {
        "schema": SCHEMA,
        "status": "PASS_SOURCE_PILOT_ONLY" if not failures else "FAIL",
        "rows": len(rows),
        "processes_covered": sorted(r["process_id_evaluator_only"] for r in rows),
        "trainable_implementation_classes_covered": sorted(classes),
        "oracle_only_classes_supervised": [],
        "concrete_transition_targets": len(rows),
        "claycode_v18_roundtrip_passes": roundtrip_passes,
        "adversarial_mutations_rejected": mutation_rejections,
        "meta_rule_targets": 0,
        "accepted_dataset_tokens_minted": 0,
        "training_executed": False,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_positive_causal_credit_minted": 0,
        "independent_replication_credit_minted": 0,
        "review_semantics": "SAME_MODEL_MULTI_LENS_REVIEW_NOT_INDEPENDENT_EVIDENCE",
        "failures": failures,
        "source_bindings": SOURCE_BINDINGS,
    }


if __name__ == "__main__":
    print(canonical_json(audit()))
