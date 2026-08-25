#!/usr/bin/env python3
"""Authority-bindable deterministic discriminator producer for Trigger-2 A02.

This module is deliberately a pure synthetic producer.  It receives generation-bound
world/state/event subjects plus an authority-selected policy object, recomputes the retained
``u_test_order`` discriminator result, and emits one deterministic execution receipt.  It
does not read row-carried ``admissible``/``executed`` flags and cannot mint canonical truth,
effects, runtime, J-Space, HCU, EntityOS, dataset, or training credit.

The companion producer-auth gate verifies this file's exact repository identity and policy
manifest before invoking ``produce``.
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


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


history = _load_sibling(
    "trigger2_hyperposition_state_history_proof_gate_v1.py",
    "trigger2_history_for_a02_discriminator_producer_v1",
)
generation = _load_sibling(
    "trigger2_generation_provenance_gate_v1.py",
    "trigger2_generation_for_a02_discriminator_producer_v1",
)


def _jcs_sha256(value: Any) -> str:
    return generation._jcs_sha256(value)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _policy_without_digest(policy: dict[str, Any]) -> dict[str, Any]:
    return {k: deepcopy(v) for k, v in policy.items() if k != "formal_spec_jcs_sha256"}


def validate_policy(policy: Any, case_id: str, world: Any, event: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(policy, dict):
        return ["POLICY_OBJECT_REQUIRED"]
    required = {
        "policy_id",
        "policy_version",
        "allowed_case_id",
        "required_epistemic_type",
        "allowed_test_ids",
        "require_full_live_pair_coverage",
        "ordering_function",
        "formal_spec",
        "formal_spec_jcs_sha256",
    }
    if not required.issubset(policy):
        return ["POLICY_FIELDS_MISSING"]
    if not _nonempty(policy.get("policy_id")) or not _nonempty(policy.get("policy_version")):
        failures.append("POLICY_ID_OR_VERSION_INVALID")
    if policy.get("allowed_case_id") != case_id:
        failures.append("POLICY_CASE_NOT_AUTHORIZED")
    if policy.get("ordering_function") != "u_test_order":
        failures.append("POLICY_ORDERING_FUNCTION_MISMATCH")
    if policy.get("require_full_live_pair_coverage") is not True:
        failures.append("POLICY_MUST_REQUIRE_FULL_LIVE_PAIR_COVERAGE")
    if not isinstance(world, dict) or not isinstance(event, dict):
        failures.append("WORLD_EVENT_OBJECT_REQUIRED")
        return sorted(set(failures))
    if event.get("epistemic_type") != policy.get("required_epistemic_type"):
        failures.append("POLICY_EPISTEMIC_TYPE_MISMATCH")
    allowed_test_ids = policy.get("allowed_test_ids")
    if not isinstance(allowed_test_ids, list) or event.get("test_id") not in allowed_test_ids:
        failures.append("POLICY_TEST_NOT_AUTHORIZED")
    formal_spec = policy.get("formal_spec")
    if not isinstance(formal_spec, dict):
        failures.append("POLICY_FORMAL_SPEC_OBJECT_REQUIRED")
    else:
        test_id = event.get("test_id")
        expected = {
            "test_id": test_id,
            **deepcopy(world.get("tests", {}).get(test_id, {})),
        }
        if formal_spec != expected:
            failures.append("POLICY_FORMAL_SPEC_NOT_EXACT_WORLD_TEST")
        try:
            digest = _jcs_sha256(formal_spec)
        except Exception as exc:
            failures.append("POLICY_FORMAL_SPEC_JCS_FAILED:" + type(exc).__name__)
        else:
            if digest != policy.get("formal_spec_jcs_sha256"):
                failures.append("POLICY_FORMAL_SPEC_DIGEST_MISMATCH")
    return sorted(set(failures))


def produce(
    *,
    case_id: str,
    world: dict[str, Any],
    state_before: dict[str, Any],
    event: dict[str, Any],
    producer_binding: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Derive one synthetic execution receipt from bound subjects and policy.

    The caller is expected to be the companion auth gate after generation provenance passes.
    Row-carried receipt fields never participate in this derivation.
    """
    failures = validate_policy(policy, case_id, world, event)
    if failures:
        raise ValueError("POLICY_REJECTED:" + ",".join(failures))
    if not isinstance(producer_binding, dict):
        raise ValueError("PRODUCER_BINDING_REQUIRED")
    required_binding = {
        "repo_path",
        "source_sha256",
        "git_commit_sha",
        "producer_schema_or_version",
    }
    if not required_binding.issubset(producer_binding):
        raise ValueError("PRODUCER_BINDING_FIELDS_MISSING")
    if producer_binding.get("producer_schema_or_version") != PRODUCER_SCHEMA:
        raise ValueError("PRODUCER_SCHEMA_BINDING_MISMATCH")

    test_id = event.get("test_id")
    observed_outcome = event.get("observed_outcome")
    formal_spec = policy["formal_spec"]
    if observed_outcome not in formal_spec.get("allowed_outcomes", []):
        raise ValueError("OBSERVED_OUTCOME_NOT_IN_BOUND_FORMAL_SPEC")

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
    if policy.get("require_full_live_pair_coverage") is True and full_coverage is not True:
        raise ValueError("DISCRIMINATOR_INCOMPLETE_LIVE_PAIR_COVERAGE")

    event_semantic_sha256 = history.event_semantic_sha256(event)
    if not _nonempty(event_semantic_sha256):
        raise ValueError("EVENT_SEMANTIC_DIGEST_REQUIRED")
    world_sha256 = history._world_sha256(world)
    if not _nonempty(world_sha256):
        raise ValueError("WORLD_DIGEST_REQUIRED")
    pre_state_jcs_sha256 = _jcs_sha256(state_before)
    world_scoped_event_jcs_sha256 = _jcs_sha256({
        "world_id": world.get("world_id"),
        "event_semantic_sha256": event_semantic_sha256,
        "test_id": test_id,
        "observed_outcome": observed_outcome,
    })
    policy_jcs_sha256 = _jcs_sha256(_policy_without_digest(policy))
    ordering_result_jcs_sha256 = _jcs_sha256(ordering)

    producer_result = {
        "producer_schema": PRODUCER_SCHEMA,
        "case_id": case_id,
        "policy_jcs_sha256": policy_jcs_sha256,
        "formal_discriminator_spec_jcs_sha256": policy["formal_spec_jcs_sha256"],
        "world_sha256": world_sha256,
        "pre_state_jcs_sha256": pre_state_jcs_sha256,
        "world_scoped_event_jcs_sha256": world_scoped_event_jcs_sha256,
        "event_semantic_sha256": event_semantic_sha256,
        "test_id": test_id,
        "observed_outcome": deepcopy(observed_outcome),
        "ordering_result_jcs_sha256": ordering_result_jcs_sha256,
        "separated_live_pairs": separated,
        "separates_all_live_pairs": bool(full_coverage),
        "admissible": True,
        "executed": True,
    }
    producer_result_jcs_sha256 = _jcs_sha256(producer_result)
    receipt_preimage = {
        "producer_binding": deepcopy(producer_binding),
        "producer_result_jcs_sha256": producer_result_jcs_sha256,
    }
    execution_receipt_id = "t2disc:" + _jcs_sha256(receipt_preimage)

    return {
        "schema": RECEIPT_SCHEMA,
        "execution_receipt_id": execution_receipt_id,
        "event_id": event.get("event_id"),
        "test_id": test_id,
        "observed_outcome": deepcopy(observed_outcome),
        "event_semantic_sha256": event_semantic_sha256,
        "world_sha256": world_sha256,
        "admissible": True,
        "executed": True,
        "separated_live_pairs": separated,
        "separates_all_live_pairs": bool(full_coverage),
        "producer": deepcopy(producer_binding),
        "policy": {
            "policy_id": policy["policy_id"],
            "policy_version": policy["policy_version"],
            "policy_jcs_sha256": policy_jcs_sha256,
            "formal_discriminator_spec_jcs_sha256": policy["formal_spec_jcs_sha256"],
        },
        "pre_state_jcs_sha256": pre_state_jcs_sha256,
        "world_scoped_event_jcs_sha256": world_scoped_event_jcs_sha256,
        "ordering_result_jcs_sha256": ordering_result_jcs_sha256,
        "producer_result_jcs_sha256": producer_result_jcs_sha256,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }
