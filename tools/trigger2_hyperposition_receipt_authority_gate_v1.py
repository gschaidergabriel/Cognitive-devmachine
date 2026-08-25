#!/usr/bin/env python3
"""Deterministic receipt-authority successor for the Trigger-2 Hyperposition pilot.

This gate closes a narrow P0 left by the current generation+epistemic+state-history
composition: discriminator receipts must not gain authority from row-carried booleans such
as ``executed`` or ``admissible``. For the currently admitted deterministic pilot this gate
recomputes the discriminator execution receipt from exact generation-proven world/state/event
subjects, binds the current event to world + ordered-history identity, then delegates to the
retained epistemic/state-history proof lane.

Scope is deliberately bounded to the trusted pilot's empty pre-event history. Extending to
multi-event histories requires the generator authority to bind those history subjects too.
PASS is candidate pre-admission component evidence only and mints zero dataset/training/
runtime/J-Space/HCU/EntityOS/truth/effect credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_RECEIPT_AUTHORITY_GATE/v1"
EVENT_BINDING_SCHEMA = "XENO_WORLD_HISTORY_SCOPED_EVENT_BINDING/v1"
PRODUCER_SCHEMA = "CLAY_TRIGGER2_DETERMINISTIC_DISCRIMINATOR_RECEIPT_PRODUCER/v1"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generation = _load_sibling(
    "trigger2_generation_provenance_gate_v1.py",
    "trigger2_generation_provenance_for_receipt_authority_v1",
)
epistemic = _load_sibling(
    "trigger2_hyperposition_epistemic_preupdate_guard_v1.py",
    "trigger2_epistemic_preupdate_for_receipt_authority_v1",
)
history = _load_sibling(
    "trigger2_hyperposition_state_history_proof_gate_v1.py",
    "trigger2_state_history_for_receipt_authority_v1",
)


def _digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _source_sha256() -> str:
    return sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "row_carried_executed_boolean_is_authority": False,
        "row_carried_admissible_boolean_is_authority": False,
        "producer_reconstruction_required": True,
        "scope": "TRUSTED_EMPTY_HISTORY_PILOT_ONLY",
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
    }
    out.update(extra)
    return out


def _world_history_binding(world: Any, history_events: Any, event: Any) -> dict[str, Any]:
    if not isinstance(world, dict) or not isinstance(history_events, list) or not isinstance(event, dict):
        raise ValueError("WORLD_HISTORY_EVENT_OBJECTS_REQUIRED")
    event_digest = history.event_semantic_sha256(event)
    if not isinstance(event_digest, str):
        raise ValueError("EVENT_SEMANTIC_DIGEST_REQUIRED")
    world_digest = history._world_sha256(world)
    ordered_history = []
    for idx, prior in enumerate(history_events):
        prior_digest = history.event_semantic_sha256(prior)
        if not isinstance(prior_digest, str):
            raise ValueError(f"HISTORY_EVENT_SEMANTIC_DIGEST_REQUIRED:{idx}")
        ordered_history.append({"index": idx, "event_id": prior.get("event_id"), "event_semantic_sha256": prior_digest})
    history_digest = _digest(ordered_history)
    preimage = {
        "world_sha256": world_digest,
        "ordered_history_sha256": history_digest,
        "event_semantic_sha256": event_digest,
    }
    return {
        "schema": EVENT_BINDING_SCHEMA,
        "event_id": event.get("event_id"),
        "event_semantic_sha256": event_digest,
        "world_sha256": world_digest,
        "ordered_history_sha256": history_digest,
        "scoped_event_id": "t2scope:" + _digest(preimage),
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def derive_current_discriminator_receipt(world: Any, state_before: Any, event: Any, event_binding: Any) -> dict[str, Any]:
    if not isinstance(world, dict) or not isinstance(state_before, dict) or not isinstance(event, dict):
        raise ValueError("WORLD_STATE_EVENT_OBJECTS_REQUIRED")
    if not isinstance(event_binding, dict) or event_binding.get("schema") != EVENT_BINDING_SCHEMA:
        raise ValueError("WORLD_HISTORY_EVENT_BINDING_REQUIRED")
    test_id = event.get("test_id")
    if not isinstance(test_id, str) or not test_id:
        raise ValueError("EVENT_TEST_ID_REQUIRED")

    ordering = history.lab.u_test_order(world, state_before, [test_id])
    if not isinstance(ordering, dict) or not ordering.get("pass"):
        raise ValueError("DISCRIMINATOR_ORDER_RECOMPUTE_REJECTED")
    rows = ordering.get("ordering")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("DISCRIMINATOR_ORDER_RESULT_INVALID")
    item = rows[0]
    separated = item.get("separated_live_pairs")
    full_coverage = item.get("separates_all_live_pairs")
    if not isinstance(separated, int) or separated <= 0:
        raise ValueError("DISCRIMINATOR_DOES_NOT_SEPARATE_LIVE_PAIR")
    if full_coverage is not True:
        raise ValueError("DISCRIMINATOR_INCOMPLETE_LIVE_PAIR_COVERAGE")

    producer_binding = {
        "schema": PRODUCER_SCHEMA,
        "producer_source_sha256": _source_sha256(),
        "world_scoped_event_id": event_binding.get("scoped_event_id"),
        "world_sha256": event_binding.get("world_sha256"),
        "ordered_history_sha256": event_binding.get("ordered_history_sha256"),
        "state_before_sha256": _digest(state_before),
        "test_id": test_id,
        "ordering_result_sha256": _digest(ordering),
    }
    execution_receipt_id = "t2disc:" + _digest(producer_binding)
    return {
        "schema": history.DISCRIMINATOR_RECEIPT_SCHEMA,
        "event_id": event.get("event_id"),
        "test_id": test_id,
        "observed_outcome": deepcopy(event.get("observed_outcome")),
        "event_semantic_sha256": event_binding.get("event_semantic_sha256"),
        "world_sha256": event_binding.get("world_sha256"),
        "admissible": True,
        "executed": True,
        "execution_receipt_id": execution_receipt_id,
        "separated_live_pairs": separated,
        "separates_all_live_pairs": True,
        "producer": producer_binding,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])

    failures: list[str] = []
    generation_result = None
    epistemic_result = None
    derived_receipt = None
    event_binding = None

    try:
        generation_result = generation.adjudicate(row)
    except Exception as exc:
        failures.append("GENERATION_PROVENANCE_EXCEPTION:" + type(exc).__name__)
    else:
        if not isinstance(generation_result, dict) or not generation_result.get("pass"):
            failures.extend("GENERATION:" + str(x) for x in (generation_result.get("failures", []) if isinstance(generation_result, dict) else ["RESULT_INVALID"]))

    history_events = row.get("synthetic_event_history_evaluator_only")
    if history_events != []:
        failures.append("RECEIPT_AUTHORITY_V1_REQUIRES_GENERATION_BOUND_EMPTY_HISTORY")
    supplied_before = row.get("hyperposition_state_before_evaluator_only")
    genesis = row.get("hyperposition_genesis_state_evaluator_only")
    if isinstance(supplied_before, dict) and genesis != supplied_before:
        failures.append("EMPTY_HISTORY_GENESIS_MUST_EQUAL_STATE_BEFORE")

    if not failures:
        world = row.get("formal_task_world_evaluator_only")
        event = row.get("synthetic_test_event_evaluator_only")
        try:
            event_binding = _world_history_binding(world, history_events, event)
            derived_receipt = derive_current_discriminator_receipt(world, supplied_before, event, event_binding)
        except Exception as exc:
            failures.append("DETERMINISTIC_RECEIPT_RECONSTRUCTION_FAILED:" + type(exc).__name__ + ":" + str(exc))

    sanitized = None
    if not failures and isinstance(derived_receipt, dict):
        claimed_receipts = row.get("discriminator_execution_receipts_evaluator_only")
        if claimed_receipts not in (None, [], [derived_receipt]):
            failures.append("ROW_CARRIED_DISCRIMINATOR_RECEIPT_DIFFERS_FROM_RECONSTRUCTION")
        claimed_binding = row.get("world_history_scoped_event_binding_evaluator_only")
        if claimed_binding not in (None, event_binding):
            failures.append("ROW_CARRIED_WORLD_HISTORY_EVENT_BINDING_DIFFERS_FROM_RECONSTRUCTION")
        sanitized = deepcopy(row)
        sanitized["discriminator_execution_receipts_evaluator_only"] = [deepcopy(derived_receipt)]
        sanitized["world_history_scoped_event_binding_evaluator_only"] = deepcopy(event_binding)

    if not failures and isinstance(sanitized, dict):
        try:
            epistemic_result = epistemic.adjudicate(sanitized)
        except Exception as exc:
            failures.append("EPISTEMIC_STATE_HISTORY_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(epistemic_result, dict) or not epistemic_result.get("pass"):
                failures.extend("EPISTEMIC_STATE_HISTORY:" + str(x) for x in (epistemic_result.get("failures", []) if isinstance(epistemic_result, dict) else ["RESULT_INVALID"]))

    return _result(
        failures,
        generation_provenance=generation_result,
        world_history_scoped_event_binding=event_binding,
        reconstructed_discriminator_receipt=derived_receipt,
        epistemic_state_history_proof=epistemic_result,
        exact_order=[
            "GENERATION_PROVENANCE",
            "WORLD_HISTORY_EVENT_SCOPE_BINDING",
            "DETERMINISTIC_DISCRIMINATOR_EXECUTION_RECONSTRUCTION",
            "EPISTEMIC_PREUPDATE_ADMISSION",
            "REPLAY_STATE_HISTORY_PROOF",
        ],
        observation_receipt_status="NOT_APPLICABLE_TO_CURRENT_SYNTHETIC_PROOF_PILOT",
        positive_D_E_promotion_ready=False,
        remaining_p0=[
            "multi-event history subjects need trusted generation authority before this receipt producer can expand beyond the empty-history pilot",
            "OBSERVED events require producer-authenticated observation receipts rather than row-carried source assertions",
            "exact-current admitted execution and final rendered nuisance/family/tokenizer/checkpoint gates remain required",
        ],
    )
