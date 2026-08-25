#!/usr/bin/env python3
"""Fail-closed Trigger-2 Hyperposition candidate gate v4.

Converges the retained derivation-bound v2 lane with four missing proof boundaries:
(1) replay-proven state_before, (2) immutable event-id/content identity, (3) typed
admitted+executed discriminator receipts with complete live-branch coverage, and (4)
typed evidence for epistemic promotion to OBSERVED.

Synthetic candidate pre-admission only. This module cannot mint canonical truth/effects,
dataset tokens, runtime/J-Space/HCU/EntityOS credit, or training credit.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_SINGLE_GATE/v4"
HISTORY_SCHEMA = "XENO_HYPERPOSITION_HISTORY_PROOF/v1"
EVENT_INTEGRITY_SCHEMA = "XENO_SYNTHETIC_EVENT_INTEGRITY_REGISTRY/v1"
DISCRIMINATOR_REGISTRY_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_PROOF_REGISTRY/v1"
DISCRIMINATOR_RECEIPT_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_RECEIPT/v1"
OBSERVATION_RECEIPT_SCHEMA = "XENO_TYPED_OBSERVATION_EVIDENCE_RECEIPT/v1"
BASE_FILENAME = "trigger2_hyperposition_derivation_bound_gate_v2.py"
BASE_REPO_PATH = "tools/" + BASE_FILENAME
IMMUTABLE_EVENT_FIELDS = (
    "event_id", "correlation_ancestry_id", "independence_group", "payload_key",
    "provenance", "epistemic_type", "test_id", "observed_outcome",
)


def _load(filename: str, name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = _load(BASE_FILENAME, "trigger2_hp_derivation_bound_gate_v2_for_v4")
lab = base.lab


def _digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _nonempty(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _self_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def immutable_event_payload(x: Any) -> dict[str, Any] | None:
    if not isinstance(x, dict) or any(k not in x for k in IMMUTABLE_EVENT_FIELDS):
        return None
    out = {k: deepcopy(x[k]) for k in IMMUTABLE_EVENT_FIELDS}
    ids = ("event_id", "correlation_ancestry_id", "independence_group", "payload_key", "provenance", "epistemic_type", "test_id")
    return out if all(_nonempty(out[k]) for k in ids) else None


def immutable_event_sha256(x: Any) -> str | None:
    payload = immutable_event_payload(x)
    return _digest(payload) if payload is not None else None


def _records(state: Any) -> list[dict[str, Any]]:
    out = []
    if not isinstance(state, dict):
        return out
    for b in state.get("branches", []) or []:
        if isinstance(b, dict):
            for f in ("E_plus", "E_minus", "F", "correlated_observations"):
                out.extend(x for x in (b.get(f, []) or []) if isinstance(x, dict))
    return out


def validate_event_integrity(world: Any, state_before: Any, event: Any) -> dict[str, Any]:
    failures = []
    event_sha = immutable_event_sha256(event)
    if event_sha is None:
        return {"pass": False, "failures": ["IMMUTABLE_EVENT_PAYLOAD_INVALID"], "event_sha256": None}
    registry = world.get("event_integrity_registry") if isinstance(world, dict) else None
    entries = registry.get("events") if isinstance(registry, dict) and registry.get("schema") == EVENT_INTEGRITY_SCHEMA else None
    if not isinstance(entries, dict):
        failures.append("EVENT_INTEGRITY_REGISTRY_REQUIRED")
        entry = None
    else:
        entry = entries.get(event.get("event_id"))
    if not isinstance(entry, dict):
        failures.append("EVENT_INTEGRITY_ENTRY_REQUIRED")
    else:
        if entry.get("event_id") != event.get("event_id"):
            failures.append("EVENT_INTEGRITY_ID_MISMATCH")
        if entry.get("event_sha256") != event_sha:
            failures.append("EVENT_INTEGRITY_DIGEST_MISMATCH")
    prior = [x for x in _records(state_before) if x.get("event_id") == event.get("event_id")]
    prior_sha = []
    for old in prior:
        digest = immutable_event_sha256(old)
        if digest is None:
            failures.append("PRIOR_EVENT_RECORD_MISSING_IMMUTABLE_IDENTITY")
        else:
            prior_sha.append(digest)
            if digest != event_sha:
                failures.append("EVENT_ID_DIGEST_CONFLICT")
    return {
        "pass": not failures, "failures": sorted(set(failures)), "event_sha256": event_sha,
        "same_id_prior_record_count": len(prior), "prior_event_sha256": sorted(set(prior_sha)),
        "caller_independence_flag_part_of_event_identity": False,
    }


def _branch_sig(branch: dict[str, Any]) -> str:
    return _digest({k: deepcopy(branch.get(k)) for k in ("v", "K", "T", "predictions")})


def discriminator_contract(world: Any, state_before: Any, event: Any) -> dict[str, Any]:
    failures = []
    tests = world.get("tests") if isinstance(world, dict) else None
    test_id = event.get("test_id") if isinstance(event, dict) else None
    if not isinstance(tests, dict) or test_id not in tests:
        return {"pass": False, "failures": ["DISCRIMINATOR_TEST_NOT_IN_FORMAL_WORLD"]}
    projection = lab.project_state(world, state_before)
    if not projection.get("pass"):
        return {"pass": False, "failures": ["PROJECT_STATE_REJECTED:" + str(projection.get("failure"))]}
    by_id = {b.get("branch_id"): b for b in state_before.get("branches", []) if isinstance(b, dict)}
    live = [by_id[i] for i in projection.get("visible_branch_ids", []) if i in by_id and by_id[i].get("sigma") != "FALSIFIED"]
    rows = []
    for b in live:
        preds = b.get("predictions")
        if not isinstance(preds, dict) or test_id not in preds:
            failures.append("DISCRIMINATOR_DOES_NOT_COVER_LIVE_APPLICABLE_BRANCH:" + str(b.get("branch_id")))
        else:
            rows.append({"semantic_signature_sha256": _branch_sig(b), "predicted_outcome": deepcopy(preds[test_id])})
    rows.sort(key=lambda x: (x["semantic_signature_sha256"], json.dumps(x["predicted_outcome"], sort_keys=True)))
    spec = tests[test_id]
    payload = {
        "world_id": world.get("world_id"), "test_id": test_id,
        "allowed_outcomes": deepcopy(spec.get("allowed_outcomes")), "mismatch_effect": spec.get("mismatch_effect"),
        "risk_rank": spec.get("risk_rank"), "cost_rank": spec.get("cost_rank"),
        "coordination_rank": spec.get("coordination_rank"), "live_applicable_semantic_predictions": rows,
    }
    return {"pass": not failures, "failures": sorted(set(failures)), "contract_sha256": _digest(payload),
            "required_live_applicable_branch_ids": sorted(str(b.get("branch_id")) for b in live)}


def discriminator_receipt_sha256(receipt: Any) -> str | None:
    return _digest({k: deepcopy(v) for k, v in receipt.items() if k != "receipt_sha256"}) if isinstance(receipt, dict) else None


def make_discriminator_receipt(world: Any, state_before: Any, event: Any, *, execution_id: str, provenance: str,
                               admission_status: str = "ADMITTED", execution_status: str = "EXECUTED",
                               covered_branch_ids: list[str] | None = None) -> dict[str, Any]:
    contract = discriminator_contract(world, state_before, event)
    if not contract.get("pass"):
        raise ValueError(contract)
    receipt = {
        "schema": DISCRIMINATOR_RECEIPT_SCHEMA, "event_id": event.get("event_id"),
        "event_sha256": immutable_event_sha256(event), "test_id": event.get("test_id"),
        "admission_status": admission_status, "execution_status": execution_status,
        "execution_id": execution_id, "observed_outcome": deepcopy(event.get("observed_outcome")),
        "covered_branch_ids": sorted(covered_branch_ids if covered_branch_ids is not None else contract["required_live_applicable_branch_ids"]),
        "contract_sha256": contract["contract_sha256"], "provenance": provenance,
    }
    receipt["receipt_sha256"] = discriminator_receipt_sha256(receipt)
    return receipt


def validate_discriminator_proof(world: Any, state_before: Any, event: Any) -> dict[str, Any]:
    failures = []
    contract = discriminator_contract(world, state_before, event)
    failures.extend(contract.get("failures", []))
    registry = world.get("discriminator_proof_registry") if isinstance(world, dict) else None
    entries = registry.get("events") if isinstance(registry, dict) and registry.get("schema") == DISCRIMINATOR_REGISTRY_SCHEMA else None
    receipt = entries.get(event.get("event_id")) if isinstance(entries, dict) and isinstance(event, dict) else None
    if not isinstance(receipt, dict) or receipt.get("schema") != DISCRIMINATOR_RECEIPT_SCHEMA:
        failures.append("TYPED_DISCRIMINATOR_RECEIPT_REQUIRED")
    else:
        checks = (
            (receipt.get("event_id") == event.get("event_id"), "DISCRIMINATOR_RECEIPT_EVENT_ID_MISMATCH"),
            (receipt.get("event_sha256") == immutable_event_sha256(event), "DISCRIMINATOR_RECEIPT_EVENT_DIGEST_MISMATCH"),
            (receipt.get("test_id") == event.get("test_id"), "DISCRIMINATOR_RECEIPT_TEST_ID_MISMATCH"),
            (receipt.get("observed_outcome") == event.get("observed_outcome"), "DISCRIMINATOR_RECEIPT_OUTCOME_MISMATCH"),
            (receipt.get("admission_status") == "ADMITTED", "DISCRIMINATOR_NOT_ADMITTED"),
            (receipt.get("execution_status") == "EXECUTED", "DISCRIMINATOR_NOT_EXECUTED"),
            (_nonempty(receipt.get("execution_id")), "DISCRIMINATOR_EXECUTION_ID_REQUIRED"),
            (_nonempty(receipt.get("provenance")), "DISCRIMINATOR_PROVENANCE_REQUIRED"),
            (receipt.get("contract_sha256") == contract.get("contract_sha256"), "DISCRIMINATOR_CONTRACT_DIGEST_MISMATCH"),
            (isinstance(receipt.get("covered_branch_ids"), list) and sorted(receipt["covered_branch_ids"]) == sorted(contract.get("required_live_applicable_branch_ids", [])), "DISCRIMINATOR_COVERAGE_INCOMPLETE_OR_MISMATCHED"),
            (receipt.get("receipt_sha256") == discriminator_receipt_sha256(receipt), "DISCRIMINATOR_RECEIPT_DIGEST_MISMATCH"),
        )
        failures.extend(code for ok, code in checks if not ok)
    return {"pass": not failures, "failures": sorted(set(failures)), "contract_sha256": contract.get("contract_sha256"),
            "required_live_applicable_branch_ids": contract.get("required_live_applicable_branch_ids", []),
            "receipt_sha256": receipt.get("receipt_sha256") if isinstance(receipt, dict) else None,
            "admissibility_required": True, "execution_required": True, "full_live_applicable_coverage_required": True}


def canonical_history_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict) or not isinstance(state.get("branches"), list):
        return {"pass": False, "failure": "STATE_AND_BRANCHES_REQUIRED"}
    rows = []
    for b in state["branches"]:
        if not isinstance(b, dict):
            return {"pass": False, "failure": "BRANCH_OBJECT_REQUIRED"}
        rows.append({"semantic_signature_sha256": _branch_sig(b), "A_sha256": _digest(b.get("A")),
                     "sigma": b.get("sigma"), "projection_visibility": b.get("projection_visibility"),
                     **{f: sorted(_digest(x) for x in (b.get(f, []) or []) if isinstance(x, dict)) for f in ("E_plus", "E_minus", "F", "correlated_observations")}})
    rows.sort(key=lambda x: (x["semantic_signature_sha256"], x["A_sha256"], str(x["sigma"]), str(x["projection_visibility"])))
    payload = {"schema": state.get("schema"), "query_id": state.get("query_id"),
               "canonical_truth_allowed": state.get("canonical_truth_allowed"), "direct_effect_authority": state.get("direct_effect_authority"),
               "branches": rows}
    return {"pass": True, "canonical_state_sha256": _digest(payload), "branch_id_and_order_excluded": True,
            "evidence_and_correlation_history_included": True}


def history_proof_sha256(proof: Any) -> str | None:
    return _digest({k: deepcopy(v) for k, v in proof.items() if k != "history_sha256"}) if isinstance(proof, dict) else None


def make_history_proof(genesis_state: Any, ordered_events: list[dict[str, Any]]) -> dict[str, Any]:
    proof = {"schema": HISTORY_SCHEMA, "genesis_state": deepcopy(genesis_state),
             "ordered_event_ids": [x["event_id"] for x in ordered_events],
             "events": {x["event_id"]: deepcopy(x) for x in ordered_events}}
    proof["history_sha256"] = history_proof_sha256(proof)
    return proof


def replay_history(world: Any, proof: Any, supplied_state_before: Any) -> dict[str, Any]:
    failures, steps = [], []
    if not isinstance(proof, dict) or proof.get("schema") != HISTORY_SCHEMA:
        return {"pass": False, "failures": ["HISTORY_PROOF_REQUIRED"]}
    if proof.get("history_sha256") != history_proof_sha256(proof):
        failures.append("HISTORY_PROOF_DIGEST_MISMATCH")
    ids, events = proof.get("ordered_event_ids"), proof.get("events")
    if not isinstance(ids, list) or not all(_nonempty(x) for x in ids):
        failures.append("HISTORY_ORDERED_EVENT_IDS_REQUIRED"); ids = []
    if len(set(ids)) != len(ids): failures.append("HISTORY_DUPLICATE_EVENT_ID_FORBIDDEN")
    if not isinstance(events, dict) or set(ids) != set(events): failures.append("HISTORY_EVENT_MAP_ORDER_SET_MISMATCH"); events = {}
    state = deepcopy(proof.get("genesis_state"))
    for index, event_id in enumerate(ids):
        if failures: break
        ev = deepcopy(events[event_id])
        if ev.get("event_id") != event_id: failures.append("HISTORY_EVENT_ID_KEY_MISMATCH"); break
        integrity = validate_event_integrity(world, state, ev)
        discriminator = validate_discriminator_proof(world, state, ev)
        independence = base.derive_independence(world, state, ev)
        failures.extend("HISTORY_EVENT_INTEGRITY:" + x for x in integrity.get("failures", []))
        failures.extend("HISTORY_DISCRIMINATOR:" + x for x in discriminator.get("failures", []))
        failures.extend("HISTORY_INDEPENDENCE:" + x for x in independence.get("failures", []))
        if failures: break
        ev2 = deepcopy(ev); ev2["independence_qualified"] = bool(independence["derived_independence_qualified"])
        update = lab.u_state(world, state, ev2)
        if not update.get("pass"): failures.append("HISTORY_UPDATE_REJECTED:" + str(update.get("failure"))); break
        state = update["state_after"]
        steps.append({"index": index, "event_id": event_id, "event_sha256": integrity.get("event_sha256"),
                      "discriminator_receipt_sha256": discriminator.get("receipt_sha256"),
                      "state_after_sha256": canonical_history_state(state).get("canonical_state_sha256")})
    replayed, supplied = canonical_history_state(state), canonical_history_state(supplied_state_before)
    if not supplied.get("pass"): failures.append("SUPPLIED_STATE_BEFORE_INVALID")
    if replayed.get("pass") and supplied.get("pass") and replayed.get("canonical_state_sha256") != supplied.get("canonical_state_sha256"):
        failures.append("STATE_BEFORE_NOT_REPLAY_PROVEN")
    return {"pass": not failures, "failures": sorted(set(failures)), "history_sha256": proof.get("history_sha256"),
            "replayed_state_sha256": replayed.get("canonical_state_sha256"), "supplied_state_before_sha256": supplied.get("canonical_state_sha256"),
            "step_receipts": steps, "replay_event_count": len(steps), "state_before_reconstructed_from_genesis": not failures}


def observation_receipt_sha256(receipt: Any) -> str | None:
    return _digest({k: deepcopy(v) for k, v in receipt.items() if k != "receipt_sha256"}) if isinstance(receipt, dict) else None


def adjudicate_epistemic_transition(source_type: Any, requested_target_type: Any, *, observation_receipt: Any = None) -> dict[str, Any]:
    failures = []
    if source_type not in lab.ALLOWED_EPISTEMIC or requested_target_type not in lab.ALLOWED_EPISTEMIC:
        failures.append("EPISTEMIC_TYPE_INVALID")
    needs = source_type in {"UNKNOWN", "MEASUREMENT_ERROR", "PREDICTION", "CONTRADICTION", "HYPOTHESIS", "COUNTERHYPOTHESIS"} and requested_target_type == "OBSERVED"
    if needs:
        r = observation_receipt
        if not isinstance(r, dict) or r.get("schema") != OBSERVATION_RECEIPT_SCHEMA:
            failures.append("TYPED_OBSERVATION_RECEIPT_REQUIRED")
        else:
            checks = ((r.get("status") == "VERIFIED_OBSERVATION", "OBSERVATION_RECEIPT_NOT_VERIFIED"),
                      (_nonempty(r.get("event_id")), "OBSERVATION_RECEIPT_EVENT_ID_REQUIRED"),
                      (_nonempty(r.get("event_sha256")), "OBSERVATION_RECEIPT_EVENT_DIGEST_REQUIRED"),
                      (_nonempty(r.get("provenance")), "OBSERVATION_RECEIPT_PROVENANCE_REQUIRED"),
                      (r.get("source_type") == source_type, "OBSERVATION_RECEIPT_SOURCE_TYPE_MISMATCH"),
                      (r.get("target_type") == requested_target_type, "OBSERVATION_RECEIPT_TARGET_TYPE_MISMATCH"),
                      (r.get("receipt_sha256") == observation_receipt_sha256(r), "OBSERVATION_RECEIPT_DIGEST_MISMATCH"))
            failures.extend(code for ok, code in checks if not ok)
    return {"schema": SCHEMA, "pass": not failures, "transition_allowed": not failures, "failures": sorted(set(failures)),
            "typed_observation_receipt_required": needs, "naked_evidence_qualified_boolean_accepted": False,
            "canonical_truth_minted": False, "direct_effect_authority_minted": False, "training_credit_minted": 0}


def adjudicate(row: Any) -> dict[str, Any]:
    failures = []
    if not isinstance(row, dict):
        return {"schema": SCHEMA, "pass": False, "failures": ["ROW_OBJECT_REQUIRED"]}
    world, before, event = row.get("formal_task_world_evaluator_only"), row.get("hyperposition_state_before_evaluator_only"), row.get("synthetic_test_event_evaluator_only")
    replay = replay_history(world, row.get("history_proof_evaluator_only"), before)
    integrity = validate_event_integrity(world, before, event)
    discriminator = validate_discriminator_proof(world, before, event)
    failures += ["HISTORY:" + x for x in replay.get("failures", [])]
    failures += ["CURRENT_EVENT:" + x for x in integrity.get("failures", [])]
    failures += ["CURRENT_DISCRIMINATOR:" + x for x in discriminator.get("failures", [])]
    epistemic = None
    if row.get("epistemic_transition_evaluator_only") is not None:
        tr = row["epistemic_transition_evaluator_only"]
        if not isinstance(tr, dict): failures.append("EPISTEMIC_TRANSITION_OBJECT_REQUIRED")
        else:
            epistemic = adjudicate_epistemic_transition(tr.get("source_type"), tr.get("requested_target_type"), observation_receipt=tr.get("observation_receipt"))
            failures += ["EPISTEMIC:" + x for x in epistemic.get("failures", [])]
    predecessor = base.adjudicate(row)
    failures += ["BASE:" + x for x in predecessor.get("failures", [])]
    failures = sorted(set(failures))
    return {"schema": SCHEMA, "pass": not failures, "candidate_pre_admission_pass": not failures, "failures": failures,
            "single_gate_source": {"path": "tools/trigger2_hyperposition_single_gate_v4.py", "sha256": _self_sha256(),
                                   "base_gate_path": BASE_REPO_PATH, "base_gate_schema": base.SCHEMA, "labeler_schema": lab.SCHEMA},
            "history_replay": replay, "current_event_integrity": integrity, "current_discriminator_proof": discriminator,
            "base_derivation_bound_result": predecessor, "epistemic_transition": epistemic,
            "canonical_dataset_admission": False, "accepted_dataset_tokens_minted": 0, "training_credit_minted": 0,
            "runtime_credit_minted": 0, "jspace_runtime_credit_minted": 0, "full_hcu_runtime_credit_minted": 0,
            "whole_entityos_runtime_credit_minted": 0, "canonical_truth_minted": False, "direct_effect_authority_minted": False,
            "evidence_boundary": "synthetic exact-source candidate pre-admission only"}
