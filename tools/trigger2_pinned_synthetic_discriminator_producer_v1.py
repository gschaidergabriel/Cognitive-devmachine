#!/usr/bin/env python3
"""Authority-driven deterministic discriminator producer for one Trigger-2 synthetic pilot.

The producer does not accept row assertions as evidence authority. It delegates discriminator
ordering semantics to the retained Trigger-2 v3 reference labeler, while deriving a deterministic
synthetic execution receipt from authority-pinned policy plus exact world/state/event identities.

SOURCE/CANDIDATE PRE-ADMISSION ONLY. It mints zero canonical truth/effect/runtime/J-Space/HCU/
EntityOS/dataset-token/training credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

PRODUCER_SCHEMA = "CLAY_TRIGGER2_PINNED_SYNTHETIC_DISCRIMINATOR_PRODUCER/v1"
RECEIPT_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_EXECUTION_RECEIPT/v1"
POLICY_SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_DISCRIMINATOR_POLICY/v1"
REFERENCE_LABELER_FILENAME = "trigger2_hyperposition_reference_labelers_v3.py"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


labeler = _load_sibling(
    REFERENCE_LABELER_FILENAME,
    "trigger2_reference_labeler_for_discriminator_producer_v1",
)


def _digest(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _event_semantic_payload(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError("EVENT_OBJECT_REQUIRED")
    keys = (
        "schema",
        "event_id",
        "correlation_ancestry_id",
        "independence_group",
        "payload_key",
        "provenance",
        "epistemic_type",
        "test_id",
        "observed_outcome",
        "canonical_truth_allowed",
        "direct_effect_authority",
    )
    if any(key not in event for key in keys):
        raise ValueError("EVENT_SEMANTIC_FIELDS_REQUIRED")
    return {key: deepcopy(event[key]) for key in keys}


def _subject_match(policy: dict[str, Any], key: str, value: Any) -> None:
    expected = policy.get("expected_" + key)
    if expected != value:
        raise ValueError("POLICY_SUBJECT_MISMATCH:" + key)


def produce(
    world: Any,
    state_before: Any,
    event: Any,
    *,
    case_id: str,
    policy: Any,
    producer_binding: Any,
    labeler_binding: Any,
) -> dict[str, Any]:
    """Return the exact deterministic synthetic discriminator receipt for the pinned case."""
    if not isinstance(world, dict) or not isinstance(state_before, dict) or not isinstance(event, dict):
        raise ValueError("WORLD_STATE_EVENT_OBJECTS_REQUIRED")
    if not isinstance(policy, dict) or policy.get("schema") != POLICY_SCHEMA:
        raise ValueError("DISCRIMINATOR_POLICY_SCHEMA_MISMATCH")
    if not isinstance(producer_binding, dict):
        raise ValueError("PRODUCER_BINDING_REQUIRED")
    if not isinstance(labeler_binding, dict):
        raise ValueError("LABELER_BINDING_REQUIRED")

    _subject_match(policy, "generation_case_id", case_id)
    _subject_match(policy, "world_id", world.get("world_id"))
    _subject_match(policy, "query_id", state_before.get("query_id"))
    _subject_match(policy, "event_id", event.get("event_id"))
    _subject_match(policy, "test_id", event.get("test_id"))
    _subject_match(policy, "observed_outcome", event.get("observed_outcome"))
    _subject_match(policy, "epistemic_type", event.get("epistemic_type"))

    if world.get("canonical_truth_allowed") is not False or world.get("direct_effect_authority") is not False:
        raise ValueError("WORLD_AUTHORITY_FENCE_INVALID")
    if state_before.get("canonical_truth_allowed") is not False or state_before.get("direct_effect_authority") is not False:
        raise ValueError("STATE_AUTHORITY_FENCE_INVALID")
    if event.get("canonical_truth_allowed") is not False or event.get("direct_effect_authority") is not False:
        raise ValueError("EVENT_AUTHORITY_FENCE_INVALID")

    test_id = event.get("test_id")
    tests = world.get("tests")
    if not isinstance(tests, dict) or test_id not in tests or not isinstance(tests[test_id], dict):
        raise ValueError("FORMAL_DISCRIMINATOR_SPEC_REQUIRED")
    formal_spec = tests[test_id]
    formal_spec_sha256 = _digest(formal_spec)
    if formal_spec_sha256 != policy.get("formal_discriminator_spec_sha256"):
        raise ValueError("FORMAL_DISCRIMINATOR_SPEC_DIGEST_MISMATCH")

    state_before_sha256 = _digest(state_before)
    if state_before_sha256 != policy.get("state_before_sha256"):
        raise ValueError("STATE_BEFORE_DIGEST_MISMATCH")

    ordering = labeler.u_test_order(world, state_before, [test_id])
    if not isinstance(ordering, dict) or ordering.get("pass") is not True:
        raise ValueError("DISCRIMINATOR_ORDER_RECOMPUTE_REJECTED")
    rows = ordering.get("ordering")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("DISCRIMINATOR_ORDER_RESULT_INVALID")
    item = rows[0]

    separated = item.get("separated_live_pairs")
    full_coverage = item.get("separates_all_live_pairs")
    if policy.get("require_at_least_one_live_pair") is True:
        if not isinstance(separated, int) or separated <= 0:
            raise ValueError("DISCRIMINATOR_MUST_SEPARATE_AT_LEAST_ONE_LIVE_PAIR")
    if policy.get("require_full_live_pair_separation") is True and full_coverage is not True:
        raise ValueError("DISCRIMINATOR_INCOMPLETE_LIVE_PAIR_COVERAGE")

    event_semantic_sha256 = _digest(_event_semantic_payload(event))
    world_sha256 = _digest(world)
    world_scoped_event_sha256 = _digest(
        {
            "world_id": world.get("world_id"),
            "world_sha256": world_sha256,
            "event_semantic_sha256": event_semantic_sha256,
            "test_id": test_id,
            "observed_outcome": event.get("observed_outcome"),
        }
    )
    policy_sha256 = _digest(policy)

    execution_preimage = {
        "producer": deepcopy(producer_binding),
        "labeler": deepcopy(labeler_binding),
        "policy_sha256": policy_sha256,
        "generation_case_id": case_id,
        "world_sha256": world_sha256,
        "state_before_sha256": state_before_sha256,
        "world_scoped_event_sha256": world_scoped_event_sha256,
        "formal_discriminator_spec_sha256": formal_spec_sha256,
        "ordering_result_sha256": _digest(ordering),
        "separated_live_pairs": separated,
        "separates_all_live_pairs": full_coverage,
    }
    execution_receipt_id = "t2dp:" + _digest(execution_preimage)

    return {
        "schema": RECEIPT_SCHEMA,
        "execution_receipt_id": execution_receipt_id,
        "event_id": event.get("event_id"),
        "test_id": test_id,
        "observed_outcome": deepcopy(event.get("observed_outcome")),
        "event_semantic_sha256": event_semantic_sha256,
        "world_sha256": world_sha256,
        "world_scoped_event_sha256": world_scoped_event_sha256,
        "formal_discriminator_spec_sha256": formal_spec_sha256,
        "state_before_sha256": state_before_sha256,
        "policy_sha256": policy_sha256,
        "producer": deepcopy(producer_binding),
        "ordering_semantics": deepcopy(labeler_binding),
        "admissible": True,
        "executed": True,
        "separated_live_pairs": separated,
        "separates_all_live_pairs": full_coverage,
        "synthetic_noncanonical": True,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "runtime_credit_minted": False,
        "jspace_runtime_credit_minted": False,
        "hcu_runtime_credit_minted": False,
        "entityos_runtime_credit_minted": False,
        "training_credit_minted": False,
    }


if __name__ == "__main__":
    print(
        {
            "schema": PRODUCER_SCHEMA,
            "status": "SOURCE_ONLY_DETERMINISTIC_SYNTHETIC_PRODUCER",
            "training_credit_minted": False,
        }
    )
