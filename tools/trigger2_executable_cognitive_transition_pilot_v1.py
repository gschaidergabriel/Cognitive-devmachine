#!/usr/bin/env python3
"""Trigger-2 executable cognitive-transition pilot for issue #2022.

This is a quarantined source/generator pilot, not admitted training data.
It supervises instantiated state transitions rather than English meta-rules and
keeps DB, scheduler, capability and EffectGate authority outside model targets.

The target packet is validated against COGNITIVE_PROCESS_ABI/v1 and round-tripped
through the bound BASE-D V18 ClayCode cognitive protocol adapter. Passing this
module is component/source evidence only; it mints no model, runtime, J-Space,
training or whole-system credit.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from claycode_cognitive_protocol_adapter_v1 import (  # noqa: E402
    ClayCodeCognitiveProtocolError,
    load_abi,
    roundtrip,
    validate_packet,
)

SCHEMA = "CLAY_TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_PILOT/v1"
ROW_SCHEMA = "ENTITYOS_HCU_EXECUTABLE_TRANSITION_CANDIDATE/v1"
WORK_KIND = "COGNITIVE_WORK_PACKET/v1"
RESULT_KIND = "COGNITIVE_RESULT_PACKET/v1"
CENSUS_PATH = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"

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
MODEL_IMPLEMENTATION_CLASSES = {"SIMULATE_ON_GRID", "EXTERNAL_STRONG_MODEL_BRIDGE"}
NONMODEL_AUTHORITY_CLASSES = {"STORE_IN_DB", "DETERMINISTIC_BOUNDARY"}
FORBIDDEN_META_KEYS = {"rule", "positive_rule", "negative_rule"}
FORBIDDEN_AUTHORITY_KEYS = {
    "canonical_truth",
    "canonical_commit",
    "capability_grant",
    "capability_authority",
    "direct_s0_write",
    "real_effect_executed",
    "verified_external_outcome",
    "effect_receipt_minted_by_model",
    "scheduler_lease_minted_by_model",
    "admission_id_minted_by_model",
}


def cj(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def dg(value: Any) -> str:
    return hashlib.sha256(cj(value).encode("utf-8")).hexdigest()


def _load_census() -> dict[str, Any]:
    return json.loads(CENSUS_PATH.read_text(encoding="utf-8"))


def _work(process_id: str, row_id: str, epistemic: list[dict[str, Any]], refs: list[str]) -> dict[str, Any]:
    return {
        "schema": WORK_KIND,
        "causal_event_id": f"ce-{row_id.lower()}",
        "admission_id": f"adm-observed-{row_id.lower()}",
        "generation": 7,
        "work_id": f"work-{row_id.lower()}",
        "process_id": process_id,
        "parent_work_ids": [],
        "workspace_epoch": 42,
        "state_snapshot_ref": "dbsnap://s1/epoch-42/digest-a42",
        "input_refs": [{"ref_id": x, "digest": "sha256:bound-fixture", "provenance": "ORACLE_INPUT"} for x in refs],
        "epistemic_inputs": epistemic,
        "capability_scope_ref": "capref://readonly-cognition-v1",
        "resource_budget": {"max_output_tokens": 192, "deadline_class": "BOUNDED"},
        "grid_runtime": {"requested_N": 10, "observed_available_N": 10},
        "route_policy_ref": "policy://variable-n-role-flex-v1",
        "completion_contract": {"status": "MACHINE_ADJUDICABLE", "require_exact_semantics": True},
    }


def _target(
    work: Mapping[str, Any],
    row_id: str,
    payload: dict[str, Any],
    *,
    evidence_refs: list[str],
    unknowns: list[str],
    effect_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload_digest = dg(payload)
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
            "lease_id": "ORACLE_OBSERVED_NOT_MODEL_MINTED",
            "process_id": work["process_id"],
            "runtime_identity": "SOURCE_PILOT_NO_MODEL_RUNTIME",
            "started_at": "UNKNOWN",
            "ended_at": "UNKNOWN",
        },
        "result_id": f"result-{row_id.lower()}",
        "result_class": "CANDIDATE",
        "result_payload_ref": {
            "encoding": "INLINE_PILOT_PAYLOAD_NOT_CANONICAL_STORE",
            "payload": payload,
        },
        "result_digest": payload_digest,
        "evidence_refs": evidence_refs,
        "unknowns": unknowns,
        "db_write_proposals": [],
        "effect_request_candidates": effect_candidates or [],
        "workspace_reentry": {
            "source_result_id": f"result-{row_id.lower()}",
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


def _row(
    row_id: str,
    process_id: str,
    implementation_class: str,
    state_before: dict[str, Any],
    semantic_delta: str,
    payload: dict[str, Any],
    state_after: dict[str, Any],
    *,
    evidence_refs: list[str],
    unknowns: list[str] | None = None,
    required_unknowns: list[str] | None = None,
    effect_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    target = _target(
        state_before,
        row_id,
        payload,
        evidence_refs=evidence_refs,
        unknowns=unknowns or [],
        effect_candidates=effect_candidates,
    )
    state_before_digest = dg(state_before)
    state_after_digest = dg(state_after)
    transition_digest = dg({
        "process_id": process_id,
        "state_before_digest": state_before_digest,
        "decisive_semantic_delta": semantic_delta,
        "result_digest": target["result_digest"],
        "expected_state_after_digest": state_after_digest,
    })
    return {
        "schema": ROW_SCHEMA,
        "row_id": row_id,
        "evidence_class": "METHOD_ONLY",
        "training_eligible": False,
        "accepted_dataset_credit": 0,
        "process_id_evaluator_only": process_id,
        "implementation_class_evaluator_only": implementation_class,
        "provenance_ancestry_id": f"trigger2-executable-transition-pilot-{row_id.lower()}",
        "state_before": state_before,
        "state_before_digest": state_before_digest,
        "decisive_semantic_delta": semantic_delta,
        "target": target,
        "expected_state_after": state_after,
        "expected_state_after_digest": state_after_digest,
        "required_unknowns_evaluator_only": required_unknowns or [],
        "transition_semantic_digest": transition_digest,
        "source_bindings": SOURCE_BINDINGS,
        "authority_boundary": {
            "canonical_truth_minted": False,
            "capability_minted": False,
            "effect_receipt_minted": False,
            "deterministic_store_scheduler_effect_boundaries_are_oracle_inputs": True,
        },
    }


def rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    w = _work("ZECP03", "ECT01_WORKING_STATE", [
        {"status": "OBSERVED", "claim": "goal_ref is durable", "ref": "dbref://goal/17"},
        {"status": "UNKNOWN", "claim": "owner_deadline", "ref": "NONE"},
    ], ["dbref://goal/17"])
    out.append(_row("ECT01_WORKING_STATE", "ZECP03", "SIMULATE_ON_GRID", w, "OWNER_DEADLINE_MISSING",
        {"working_state_candidate": {"active_goal_ref": "dbref://goal/17", "owner_deadline": "UNKNOWN"},
         "missing_state_questions": ["owner_deadline"]},
        {"active_goal_ref": "dbref://goal/17", "owner_deadline": "UNKNOWN", "canonical_state_changed": False},
        evidence_refs=["dbref://goal/17"], unknowns=["owner_deadline"], required_unknowns=["owner_deadline"]))

    w = _work("ZECP04", "ECT02_ATTENTION", [
        {"status": "OBSERVED", "claim": "major evidence is relevant", "ref": "ev://major"},
        {"status": "OBSERVED", "claim": "minority counterevidence remains unresolved", "ref": "ev://minority"},
    ], ["ev://major", "ev://minority"])
    out.append(_row("ECT02_ATTENTION", "ZECP04", "SIMULATE_ON_GRID", w, "CAPACITY_TIGHT_COUNTEREVIDENCE_MUST_REMAIN_RETRIEVABLE",
        {"attention_slice": ["ev://major"], "deferred_refs": ["ev://minority"], "uncertainty_set": ["ev://minority"]},
        {"active_refs": ["ev://major"], "deferred_refs": ["ev://minority"], "canonical_state_changed": False},
        evidence_refs=["ev://major", "ev://minority"]))

    w = _work("ZECP05", "ECT03_GOAL_STATE", [
        {"status": "OBSERVED", "claim": "durable goal requires evidence boundaries", "ref": "goal://durable/1"},
        {"status": "INFERRED", "claim": "faster temporary objective is attractive", "ref": "candidate://temp-goal"},
    ], ["goal://durable/1"])
    out.append(_row("ECT03_GOAL_STATE", "ZECP05", "SIMULATE_ON_GRID", w, "TEMPORARY_PREFERENCE_CANNOT_REPLACE_DURABLE_GOAL",
        {"goal_state_candidate": {"durable_goal_ref": "goal://durable/1", "subgoal": "prepare bounded candidate"},
         "completion_tests": ["preserve_evidence_boundary", "no_canonical_self_write"]},
        {"durable_goal_ref": "goal://durable/1", "replacement": False, "canonical_state_changed": False},
        evidence_refs=["goal://durable/1"]))

    w = _work("ZECP06", "ECT04_REPLAN", [
        {"status": "OBSERVED", "claim": "prerequisite u2 is falsified", "ref": "ev://prereq-u2-false"},
    ], ["ev://prereq-u2-false"])
    out.append(_row("ECT04_REPLAN", "ZECP06", "SIMULATE_ON_GRID", w, "PREREQUISITE_U2_FALSIFIED",
        {"work_graph_candidate": {"u1": "DONE", "u2": "BLOCKED", "u3": "WAITING"},
         "work_units": ["u3"], "replan_conditions": ["replace_u2_or_resolve_prerequisite"]},
        {"prereq_u2": False, "u2_status": "BLOCKED", "old_plan_preserved_by_ref": True, "canonical_state_changed": False},
        evidence_refs=["ev://prereq-u2-false"]))

    w = _work("ZECP07", "ECT05_HYPERPOSITION", [
        {"status": "HYPOTHESIS", "claim": "A explains failure", "ref": "hyp://A"},
        {"status": "HYPOTHESIS", "claim": "B explains failure", "ref": "hyp://B"},
        {"status": "OBSERVED", "claim": "8/10 modules prefer A", "ref": "obs://majority"},
    ], ["obs://majority"])
    out.append(_row("ECT05_HYPERPOSITION", "ZECP07", "SIMULATE_ON_GRID", w, "MAJORITY_WITHOUT_CAUSAL_DISCRIMINATOR",
        {"alternative_set": [{"id": "A", "status": "UNRESOLVED"}, {"id": "B", "status": "UNRESOLVED"}],
         "uncertainty_readout": "UNRESOLVED", "discriminator_candidates": ["probe://A-vs-B"]},
        {"alternatives_live": ["A", "B"], "collapsed": False, "canonical_state_changed": False},
        evidence_refs=["obs://majority"], unknowns=["truth_A", "truth_B"], required_unknowns=["truth_A", "truth_B"]))

    w = _work("ZECP08", "ECT06_INFERENCE", [
        {"status": "OBSERVED", "claim": "bounded work unit requests comparison", "ref": "workinput://6"},
    ], ["workinput://6"])
    out.append(_row("ECT06_INFERENCE", "ZECP08", "SIMULATE_ON_GRID", w, "BOUNDED_COGNITIVE_TRANSFORM",
        {"candidate_result": {"comparison": "A_GT_B", "basis_refs": ["workinput://6"]},
         "candidate_action": "REQUEST_DISCRIMINATOR_IF_MATERIAL", "confidence_readout": "MEDIUM"},
        {"candidate_only": True, "canonical_fact": "UNMINTED", "canonical_state_changed": False},
        evidence_refs=["workinput://6"]))

    w = _work("ZECP09", "ECT07_CRITIQUE", [
        {"status": "INFERRED", "claim": "candidate says stale evidence is current", "ref": "candidate://7"},
        {"status": "OBSERVED", "claim": "snapshot digest differs", "ref": "obs://digest-mismatch"},
    ], ["candidate://7", "obs://digest-mismatch"])
    out.append(_row("ECT07_CRITIQUE", "ZECP09", "SIMULATE_ON_GRID", w, "STALE_EVIDENCE_AND_AUTHORITY_OVERCLAIM",
        {"quality_readout": "REVISION_REQUIRED", "contradiction_flags": ["STALE_SNAPSHOT", "UNSUPPORTED_CURRENTNESS"],
         "revision_request": "rebind_to_exact_observation_identity_or_preserve_UNKNOWN"},
        {"revision_required": True, "stale_claim_promoted": False, "canonical_state_changed": False},
        evidence_refs=["obs://digest-mismatch"]))

    w = _work("ZECP10", "ECT08_WORKSPACE", [
        {"status": "OBSERVED", "claim": "candidate c1 wins salience competition", "ref": "workspace://selection/c1"},
        {"status": "UNKNOWN", "claim": "broadcast caused downstream state change", "ref": "NONE"},
    ], ["workspace://selection/c1"])
    out.append(_row("ECT08_WORKSPACE", "ZECP10", "SIMULATE_ON_GRID", w, "SELECTION_BROADCAST_REENTRY_WITHOUT_TRUTH_PROMOTION",
        {"workspace_selection": "c1", "broadcast_packet": {"candidate_ref": "candidate://c1"},
         "reentry_refs": ["candidate://c1"], "observed_downstream_change": "UNKNOWN"},
        {"workspace_epoch": 43, "selected": "c1", "causal_credit": "UNKNOWN", "canonical_state_changed": False},
        evidence_refs=["workspace://selection/c1"], unknowns=["observed_downstream_change"],
        required_unknowns=["observed_downstream_change"]))

    w = _work("ZECP12", "ECT09_COMPRESSION", [
        {"status": "OBSERVED", "claim": "budget requires compression", "ref": "budget://small"},
        {"status": "OBSERVED", "claim": "minority evidence is decision-relevant", "ref": "ev://minority-9"},
    ], ["budget://small", "ev://minority-9"])
    out.append(_row("ECT09_COMPRESSION", "ZECP12", "SIMULATE_ON_GRID", w, "LOSS_AWARE_COMPRESSION",
        {"compressed_state_packet": {"summary": "bounded", "minority_ref": "ev://minority-9"},
         "loss_manifest": ["surface_detail_dropped"], "reentry_binding": "workspace://epoch-43"},
        {"minority_ref_preserved": True, "loss_declared": True, "canonical_state_changed": False},
        evidence_refs=["ev://minority-9"]))

    w = _work("ZECP13", "ECT10_CLAUDE_HANDOFF", [
        {"status": "OBSERVED", "claim": "bridge exposes TOOL_PROTOCOL", "ref": "bridgecap://tool"},
        {"status": "UNKNOWN", "claim": "hidden activations exposed", "ref": "NONE"},
    ], ["bridgecap://tool"])
    out.append(_row("ECT10_CLAUDE_HANDOFF", "ZECP13", "EXTERNAL_STRONG_MODEL_BRIDGE", w, "EXPOSED_INTERFACE_HANDOFF_ONLY",
        {"claude_handoff_packet": {"direction": "GRID_TO_CLAUDE", "interface_class": "TOOL_PROTOCOL",
                                   "state_refs": ["dbsnap://s1/epoch-42/digest-a42"], "tool_scope_ref": "toolscope://bounded"},
         "bridge_request_receipt": "UNKNOWN_UNTIL_DETERMINISTIC_SUBMISSION", "activation_access": "UNKNOWN_NOT_CLAIMED"},
        {"handoff_candidate_ready": True, "bridge_submitted": "UNKNOWN", "canonical_state_changed": False},
        evidence_refs=["bridgecap://tool"], unknowns=["hidden_activation_access", "bridge_submission"],
        required_unknowns=["hidden_activation_access"]))

    w = _work("ZECP14", "ECT11_CLAUDE_RETURN", [
        {"status": "OBSERVED", "claim": "tool result ref exists", "ref": "toolresult://11"},
        {"status": "INFERRED", "claim": "Claude assertion suggests fix", "ref": "claudeassert://11"},
    ], ["toolresult://11", "claudeassert://11"])
    out.append(_row("ECT11_CLAUDE_RETURN", "ZECP14", "EXTERNAL_STRONG_MODEL_BRIDGE", w, "SEPARATE_TOOL_EVIDENCE_FROM_MODEL_ASSERTION",
        {"bridge_return_packet": {"request_ref": "bridgereq://11", "result_ref": "claudeassert://11"},
         "evidence_candidates": [{"ref": "toolresult://11", "class": "TOOL_EVIDENCE"},
                                 {"ref": "claudeassert://11", "class": "MODEL_ASSERTION_CANDIDATE"}],
         "workspace_reentry_candidate": "workspace://candidate/11"},
        {"tool_evidence_preserved": True, "model_assertion_canonical": False, "canonical_state_changed": False},
        evidence_refs=["toolresult://11", "claudeassert://11"]))

    w = _work("ZECP15", "ECT12_MEMORY_PROPOSAL", [
        {"status": "OBSERVED", "claim": "verified outcome may justify memory update", "ref": "outcome://12"},
    ], ["outcome://12"])
    out.append(_row("ECT12_MEMORY_PROPOSAL", "ZECP15", "SIMULATE_ON_GRID", w, "VERIFIED_OUTCOME_TO_MEMORY_PROPOSAL_NOT_COMMIT",
        {"state_update_proposal": {"field": "lesson", "value": "candidate", "outcome_ref": "outcome://12"},
         "memory_update_proposal": {"status": "AWAIT_DETERMINISTIC_ADMISSION"},
         "provenance_refs": ["outcome://12"]},
        {"proposal_created": True, "canonical_memory_committed": False, "canonical_state_changed": False},
        evidence_refs=["outcome://12"]))

    effect = {"schema": "EFFECT_REQUEST_CANDIDATE/v1", "action": "WRITE_CANDIDATE_ARTIFACT",
              "capability_scope_ref": "capref://proposal-only", "executed": False}
    w = _work("ZECP16", "ECT13_EFFECT_PROPOSAL", [
        {"status": "OBSERVED", "claim": "capability permits proposal construction", "ref": "capref://proposal-only"},
    ], ["capref://proposal-only"])
    out.append(_row("ECT13_EFFECT_PROPOSAL", "ZECP16", "SIMULATE_ON_GRID", w, "INTENT_TO_EFFECT_REQUEST_CANDIDATE",
        {"effect_request_candidate": effect, "authority": "CANDIDATE_ONLY"},
        {"effect_candidate_created": True, "real_effect_executed": False, "canonical_state_changed": False},
        evidence_refs=["capref://proposal-only"], effect_candidates=[effect]))

    w = _work("ZECP18", "ECT14_OUTCOME_RECOVERY", [
        {"status": "OBSERVED", "claim": "submission timed out after possible acceptance", "ref": "effectreceipt://timeout-14"},
        {"status": "UNKNOWN", "claim": "external effect occurred", "ref": "effectreceipt://timeout-14"},
    ], ["effectreceipt://timeout-14"])
    out.append(_row("ECT14_OUTCOME_RECOVERY", "ZECP18", "SIMULATE_ON_GRID", w, "AMBIGUOUS_EFFECT_OUTCOME",
        {"reconciled_state_candidate": {"external_outcome": "UNKNOWN"},
         "next_work_units": [{"kind": "VERIFY_OUTCOME", "ref": "effectreceipt://timeout-14"}],
         "rejoin_plan": {"blind_replay": False}},
        {"external_outcome": "UNKNOWN", "blind_replay": False, "canonical_state_changed": False},
        evidence_refs=["effectreceipt://timeout-14"], unknowns=["external_outcome"], required_unknowns=["external_outcome"]))

    return out


def _contains_key(value: Any, keys: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in keys:
                return True
            if _contains_key(child, keys):
                return True
    elif isinstance(value, list):
        return any(_contains_key(child, keys) for child in value)
    return False


def _process_map(census: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(p["id"]): str(p["implementation_class"])
        for p in census.get("processes", [])
        if isinstance(p, Mapping) and "id" in p and "implementation_class" in p
    }


def audit(
    candidate_rows: list[dict[str, Any]] | None = None,
    *,
    abi: dict[str, Any] | None = None,
    census: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_rows = copy.deepcopy(candidate_rows if candidate_rows is not None else rows())
    abi = copy.deepcopy(abi if abi is not None else load_abi())
    census = copy.deepcopy(census if census is not None else _load_census())
    failures: list[str] = []
    roundtrip_passes = 0
    process_classes = _process_map(census)
    model_classes_covered: set[str] = set()

    expected_row_ids = [f"ECT{i:02d}_" for i in range(1, 15)]
    if len(candidate_rows) != 14:
        failures.append(f"PILOT_ROW_COUNT:{len(candidate_rows)}")
    if len({r.get("row_id") for r in candidate_rows}) != len(candidate_rows):
        failures.append("DUPLICATE_ROW_ID")

    for index, row in enumerate(candidate_rows):
        rid = str(row.get("row_id", f"ROW_{index}"))
        if index < len(expected_row_ids) and not rid.startswith(expected_row_ids[index]):
            failures.append(f"ROW_ORDER_CONTRACT:{rid}")

        pid = str(row.get("process_id_evaluator_only", ""))
        impl = str(row.get("implementation_class_evaluator_only", ""))
        actual_impl = process_classes.get(pid)
        if actual_impl is None:
            failures.append(f"PROCESS_NOT_IN_CENSUS:{rid}:{pid}")
        elif actual_impl != impl:
            failures.append(f"IMPLEMENTATION_CLASS_MISMATCH:{rid}:{impl}!={actual_impl}")
        if impl in NONMODEL_AUTHORITY_CLASSES:
            failures.append(f"NONMODEL_AUTHORITY_PROCESS_TARGETED:{rid}")
        elif impl in MODEL_IMPLEMENTATION_CLASSES:
            model_classes_covered.add(impl)

        if row.get("training_eligible") is not False or row.get("accepted_dataset_credit") != 0:
            failures.append(f"TRAINING_ADMISSION_LEAK:{rid}")

        state_before = row.get("state_before")
        if dg(state_before) != row.get("state_before_digest"):
            failures.append(f"STATE_BEFORE_DIGEST_MISMATCH:{rid}")

        target = row.get("target")
        if not isinstance(target, dict):
            failures.append(f"TARGET_OBJECT_REQUIRED:{rid}")
            continue
        if target.get("process_id") != pid:
            failures.append(f"PROCESS_ID_TARGET_MISMATCH:{rid}")

        contract = abi.get("packet_types", {}).get(RESULT_KIND, {})
        missing = [f for f in contract.get("required", []) if f not in target]
        if missing:
            failures.append(f"RESULT_REQUIRED_FIELDS_MISSING:{rid}:{','.join(missing)}")
        allowed = set(contract.get("allowed_result_class", []))
        if allowed and target.get("result_class") not in allowed:
            failures.append(f"RESULT_CLASS_INVALID:{rid}")

        result_ref = target.get("result_payload_ref")
        payload = result_ref.get("payload") if isinstance(result_ref, dict) else None
        if not isinstance(payload, dict):
            failures.append(f"RESULT_PAYLOAD_OBJECT_REQUIRED:{rid}")
        else:
            if _contains_key(payload, FORBIDDEN_META_KEYS):
                failures.append(f"META_RULE_NARRATION_TARGET:{rid}")
            if _contains_key(payload, FORBIDDEN_AUTHORITY_KEYS):
                failures.append(f"MODEL_AUTHORITY_SELF_MINT:{rid}")
            if dg(payload) != target.get("result_digest"):
                failures.append(f"RESULT_DIGEST_MISMATCH:{rid}")

        required_unknowns = set(row.get("required_unknowns_evaluator_only", []))
        unknowns = set(target.get("unknowns", [])) if isinstance(target.get("unknowns"), list) else set()
        if not required_unknowns.issubset(unknowns):
            failures.append(f"UNKNOWN_COLLAPSE:{rid}")

        for eff in target.get("effect_request_candidates", []) if isinstance(target.get("effect_request_candidates"), list) else []:
            if isinstance(eff, Mapping) and eff.get("executed") is True:
                failures.append(f"EFFECT_AUTHORITY_SELF_MINT:{rid}")

        state_after = row.get("expected_state_after")
        if dg(state_after) != row.get("expected_state_after_digest"):
            failures.append(f"STATE_AFTER_DIGEST_MISMATCH:{rid}")

        expected_transition_digest = dg({
            "process_id": pid,
            "state_before_digest": row.get("state_before_digest"),
            "decisive_semantic_delta": row.get("decisive_semantic_delta"),
            "result_digest": target.get("result_digest"),
            "expected_state_after_digest": row.get("expected_state_after_digest"),
        })
        if expected_transition_digest != row.get("transition_semantic_digest"):
            failures.append(f"TRANSITION_SEMANTIC_DIGEST_MISMATCH:{rid}")

        try:
            validate_packet(RESULT_KIND, target, abi)
            envelope, decoded = roundtrip(RESULT_KIND, target, abi)
            if cj(decoded) != cj(target):
                failures.append(f"CLAYCODE_ROUNDTRIP_SEMANTIC_MISMATCH:{rid}")
            elif not envelope.clay_semantic_hash or not envelope.clay_grammar_sha256:
                failures.append(f"CLAYCODE_V18_IDENTITY_MISSING:{rid}")
            else:
                roundtrip_passes += 1
        except ClayCodeCognitiveProtocolError as exc:
            failures.append(f"CLAYCODE_RESULT_PACKET_REJECTED:{rid}:{exc}")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "status": "PASS_SOURCE_PILOT_ONLY" if not failures else "FAIL",
        "rows": len(candidate_rows),
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_executed": False,
        "training_credit_minted": 0,
        "model_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "jspace_positive_causal_credit_minted": 0,
        "model_implementation_classes_covered": sorted(model_classes_covered),
        "processes_covered": [r.get("process_id_evaluator_only") for r in candidate_rows],
        "claycode_v18_roundtrip_passes": roundtrip_passes,
        "review_semantics": "SOURCE_COMPONENT_SELF_CHECK_NOT_INDEPENDENT_REPLICATION",
        "failures": sorted(set(failures)),
        "source_bindings": SOURCE_BINDINGS,
    }


if __name__ == "__main__":
    print(cj(audit()))
