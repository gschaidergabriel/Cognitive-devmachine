#!/usr/bin/env python3
"""Producer-authenticated successor for Trigger-2 state-history proof v2.

This bounded successor closes T2_PINNED_PILOT_A02 at source level for the already
source-pinned empty-history SYNTHETIC_PROOF pilot.  Candidate rows may carry a cached
synthetic discriminator receipt, but that receipt is never authoritative: the gate resolves
one repository-bound deterministic producer/policy, invokes it on the exact world/pre-state/
event, requires byte-equivalent structured receipt content, then translates the derived
result into the retained v1 state-history gate.

The retained v1 gate remains the semantic/replay authority.  This wrapper introduces no
second labeler, canonical truth store or effect path.  PASS is source/candidate evidence only
and mints zero dataset, runtime, J-Space, HCU, EntityOS or training credit.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_STATE_HISTORY_PRODUCER_BOUND_GATE/v2"
BASE_GATE_FILENAME = "trigger2_hyperposition_state_history_proof_gate_v1.py"
PRODUCER_FILENAME = "trigger2_trusted_discriminator_producer_v1.py"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_sibling(BASE_GATE_FILENAME, "trigger2_state_history_v1_for_producer_bound_v2")
producer = _load_sibling(PRODUCER_FILENAME, "trigger2_discriminator_producer_v1_for_state_history_v2")


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "producer_authenticated_discriminator_required": True,
        "row_carried_admissible_authoritative": False,
        "row_carried_executed_authoritative": False,
        "row_carried_execution_receipt_id_authoritative": False,
        "bounded_empty_history_pilot_only": True,
        "positive_D_E_promotion_ready": False,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "evidence_boundary": "repository-bound synthetic discriminator producer + retained state-history v1 source gate only",
    }
    out.update(extra)
    return out


def _candidate_receipt(row: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    receipts = row.get("discriminator_execution_receipts_evaluator_only")
    if not isinstance(receipts, list):
        return None, ["PRODUCER_BOUND_DISCRIMINATOR_RECEIPTS_LIST_REQUIRED"]
    if len(receipts) != 1 or not isinstance(receipts[0], dict):
        return None, ["PRODUCER_BOUND_PILOT_REQUIRES_EXACTLY_ONE_DISCRIMINATOR_RECEIPT"]
    return receipts[0], []


def _legacy_receipt(world: Any, event: Any, expected: dict[str, Any]) -> dict[str, Any]:
    """Translate the producer-derived v2 receipt into the retained v1 gate ABI.

    No caller-carried boolean/id is consulted here; all fields originate from the exact
    producer result that has already been recomputed from repository authority.
    """
    return {
        "schema": base.DISCRIMINATOR_RECEIPT_SCHEMA,
        "execution_receipt_id": expected["execution_receipt_id"],
        "event_id": expected["event_id"],
        "test_id": expected["test_id"],
        "observed_outcome": expected["observed_outcome"],
        "event_semantic_sha256": base.event_semantic_sha256(event),
        "world_sha256": base._world_sha256(world),
        "admissible": expected["admissible"],
        "executed": expected["executed"],
        "separated_live_pairs": expected["separated_live_pairs"],
        "separates_all_live_pairs": expected["separates_all_live_pairs"],
    }


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"], underlying_gate_called=False)

    failures: list[str] = []
    history = row.get("synthetic_event_history_evaluator_only")
    # A02 deliberately closes only the source-pinned genesis/empty-history pilot.  General
    # non-empty history remains blocked until immutable lineage authority is added.
    if history != []:
        failures.append("PRODUCER_BOUND_V2_ONLY_AUTHORIZES_EMPTY_HISTORY_PILOT")

    world = row.get("formal_task_world_evaluator_only")
    before = row.get("hyperposition_state_before_evaluator_only")
    event = row.get("synthetic_test_event_evaluator_only")
    case_id = row.get("generation_case_id_evaluator_only")

    candidate, candidate_failures = _candidate_receipt(row)
    failures.extend(candidate_failures)

    producer_result = None
    expected = None
    if not failures:
        try:
            producer_result = producer.produce(case_id, world, before, event)
        except Exception as exc:
            failures.append("DISCRIMINATOR_PRODUCER_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(producer_result, dict) or not producer_result.get("pass"):
                if isinstance(producer_result, dict) and isinstance(producer_result.get("failures"), list):
                    failures.extend("DISCRIMINATOR_PRODUCER:" + str(x) for x in producer_result["failures"])
                else:
                    failures.append("DISCRIMINATOR_PRODUCER_REJECTED")
            else:
                expected = producer_result.get("receipt")
                if not isinstance(expected, dict):
                    failures.append("DISCRIMINATOR_PRODUCER_RECEIPT_REQUIRED")

    receipt_exact_match = isinstance(candidate, dict) and isinstance(expected, dict) and candidate == expected
    if isinstance(expected, dict) and not receipt_exact_match:
        failures.append("ROW_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_OUTPUT")

    base_result = None
    if not failures and isinstance(expected, dict):
        sanitized = deepcopy(row)
        sanitized["discriminator_execution_receipts_evaluator_only"] = [
            _legacy_receipt(world, event, expected)
        ]
        try:
            base_result = base.adjudicate(sanitized)
        except Exception as exc:
            failures.append("UNDERLYING_STATE_HISTORY_V1_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(base_result, dict) or not base_result.get("pass"):
                if isinstance(base_result, dict) and isinstance(base_result.get("failures"), list):
                    failures.extend("STATE_HISTORY_V1:" + str(x) for x in base_result["failures"])
                else:
                    failures.append("UNDERLYING_STATE_HISTORY_V1_REJECTED")

    return _result(
        failures,
        underlying_gate_called=base_result is not None,
        underlying_gate_result=base_result,
        discriminator_producer_result=producer_result,
        expected_discriminator_receipt=expected,
        row_receipt_exact_match=receipt_exact_match,
        remaining_p0=[
            "exact-current repository-bound deterministic execution receipt remains required",
            "immutable ordered-history commitment remains required before non-empty-history positive cases",
            "OBSERVED evidence producer authenticity remains required before OBSERVED positive cases",
            "rendered nuisance/family/split/tokenizer ABI gates remain required before dataset admission",
        ],
    )


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_BOUNDED_PILOT_SUCCESSOR",
        "positive_D_E_promotion_ready": False,
    })
