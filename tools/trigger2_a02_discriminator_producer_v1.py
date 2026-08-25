#!/usr/bin/env python3
"""Authority-bound deterministic A02 discriminator producer for Trigger-2.

This producer is deliberately narrow. It does not create semantic labels, canonical truth,
effects, runtime credit, dataset admission, or training credit. It derives one synthetic
discriminator execution receipt from a repository-pinned policy and the already reconstructed
formal world/pre-state/event, while delegating test-order semantics to the retained v3
Hyperposition reference labeler.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

PRODUCER_SCHEMA = "CLAY_TRIGGER2_A02_DISCRIMINATOR_PRODUCER/v1"
RECEIPT_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_EXECUTION_RECEIPT/v1"
CANONICALIZER_PATH = "the artefact/MicroEntity/hcu/entry_canonicalization_v1.py"
LABELER_FILENAME = "trigger2_hyperposition_reference_labelers_v3.py"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _jcs_module():
    return _load_module(
        _repo_root() / CANONICALIZER_PATH,
        "trigger2_jcs_for_a02_discriminator_producer",
    )


def _jcs_sha256(value: Any) -> str:
    return sha256(_jcs_module().canonicalize(value)).hexdigest()


def _compact_sha256(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _producer_source_sha256() -> str:
    return sha256(Path(__file__).read_bytes()).hexdigest()


def _event_semantic_payload(event: dict[str, Any]) -> dict[str, Any]:
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
    if any(k not in event for k in keys):
        raise ValueError("EVENT_SEMANTIC_IDENTITY_INVALID")
    return {k: deepcopy(event[k]) for k in keys}


def _policy_fields(policy: Any) -> tuple[str, str, str, dict[str, Any]]:
    if not isinstance(policy, dict):
        raise ValueError("A02_POLICY_OBJECT_REQUIRED")
    policy_id = policy.get("policy_id")
    policy_version = policy.get("policy_version")
    case_id = policy.get("allowed_case_id")
    formal_spec = policy.get("formal_discriminator_spec")
    if not all(isinstance(x, str) and x for x in (policy_id, policy_version, case_id)):
        raise ValueError("A02_POLICY_IDENTITY_INVALID")
    if not isinstance(formal_spec, dict):
        raise ValueError("A02_FORMAL_DISCRIMINATOR_SPEC_REQUIRED")
    return policy_id, policy_version, case_id, formal_spec


def produce(
    *,
    world: Any,
    pre_state: Any,
    event: Any,
    generation_case_id: str,
    policy: Any,
) -> dict[str, Any]:
    """Deterministically reconstruct the one authority-scoped synthetic receipt."""
    policy_id, policy_version, allowed_case_id, formal_spec = _policy_fields(policy)
    if generation_case_id != allowed_case_id:
        raise ValueError("A02_CASE_NOT_AUTHORIZED")
    if not isinstance(world, dict) or not isinstance(pre_state, dict) or not isinstance(event, dict):
        raise ValueError("A02_SUBJECT_OBJECT_REQUIRED")

    expected_world_id = policy.get("world_id")
    expected_query_id = policy.get("query_id")
    expected_test_id = policy.get("test_id")
    expected_epistemic_type = policy.get("epistemic_type")
    if world.get("world_id") != expected_world_id:
        raise ValueError("A02_WORLD_ID_NOT_AUTHORIZED")
    if pre_state.get("query_id") != expected_query_id:
        raise ValueError("A02_QUERY_ID_NOT_AUTHORIZED")
    if event.get("test_id") != expected_test_id:
        raise ValueError("A02_TEST_ID_NOT_AUTHORIZED")
    if event.get("epistemic_type") != expected_epistemic_type:
        raise ValueError("A02_EPISTEMIC_TYPE_NOT_AUTHORIZED")

    tests = world.get("tests")
    if not isinstance(tests, dict) or expected_test_id not in tests:
        raise ValueError("A02_FORMAL_TEST_MISSING")
    if tests[expected_test_id] != formal_spec:
        raise ValueError("A02_FORMAL_DISCRIMINATOR_SPEC_MISMATCH")

    formal_spec_digest = _jcs_sha256(formal_spec)
    if formal_spec_digest != policy.get("formal_discriminator_spec_jcs_sha256"):
        raise ValueError("A02_FORMAL_DISCRIMINATOR_SPEC_DIGEST_MISMATCH")
    allowed_outcomes = formal_spec.get("allowed_outcomes")
    if not isinstance(allowed_outcomes, list) or event.get("observed_outcome") not in allowed_outcomes:
        raise ValueError("A02_OUTCOME_NOT_ADMISSIBLE")

    labeler_path = Path(__file__).resolve().with_name(LABELER_FILENAME)
    lab = _load_module(labeler_path, "trigger2_labeler_for_a02_discriminator_producer")
    ordering = lab.u_test_order(world, pre_state, [expected_test_id])
    if not isinstance(ordering, dict) or not ordering.get("pass"):
        failure = ordering.get("failure") if isinstance(ordering, dict) else "INVALID_RESULT"
        raise ValueError("A02_TEST_ORDER_REJECTED:" + str(failure))
    rows = ordering.get("ordering")
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("A02_TEST_ORDER_CARDINALITY_INVALID")
    row = rows[0]

    event_semantic_sha256 = _compact_sha256(_event_semantic_payload(event))
    world_sha256 = _compact_sha256(world)
    world_jcs_sha256 = _jcs_sha256(world)
    prestate_jcs_sha256 = _jcs_sha256(pre_state)
    world_scoped_event = {
        "world_id": world["world_id"],
        "event_semantic_sha256": event_semantic_sha256,
        "test_id": event["test_id"],
        "observed_outcome": deepcopy(event["observed_outcome"]),
    }
    world_scoped_event_jcs_sha256 = _jcs_sha256(world_scoped_event)

    producer_result = {
        "test_id": expected_test_id,
        "observed_outcome": deepcopy(event["observed_outcome"]),
        "separated_live_pairs": row.get("separated_live_pairs"),
        "separates_all_live_pairs": row.get("separates_all_live_pairs"),
        "ordinal_rank": row.get("ordinal_rank"),
        "ordering_rule": ordering.get("rule"),
    }
    producer_result_jcs_sha256 = _jcs_sha256(producer_result)
    producer_source_sha256 = _producer_source_sha256()

    receipt_preimage = {
        "producer_schema_or_version": PRODUCER_SCHEMA,
        "producer_source_sha256": producer_source_sha256,
        "policy_id": policy_id,
        "policy_version": policy_version,
        "formal_discriminator_spec_jcs_sha256": formal_spec_digest,
        "generation_case_id": generation_case_id,
        "world_jcs_sha256": world_jcs_sha256,
        "prestate_jcs_sha256": prestate_jcs_sha256,
        "world_scoped_event_jcs_sha256": world_scoped_event_jcs_sha256,
        "producer_result_jcs_sha256": producer_result_jcs_sha256,
    }
    execution_receipt_id = "t2a02:" + _jcs_sha256(receipt_preimage)

    return {
        "schema": RECEIPT_SCHEMA,
        "event_id": event["event_id"],
        "test_id": event["test_id"],
        "observed_outcome": deepcopy(event["observed_outcome"]),
        "event_semantic_sha256": event_semantic_sha256,
        "world_sha256": world_sha256,
        "admissible": True,
        "executed": True,
        "execution_receipt_id": execution_receipt_id,
        "separated_live_pairs": row.get("separated_live_pairs"),
        "separates_all_live_pairs": row.get("separates_all_live_pairs"),
        "producer": {
            "repo_path": "tools/trigger2_a02_discriminator_producer_v1.py",
            "source_sha256": producer_source_sha256,
            "producer_schema_or_version": PRODUCER_SCHEMA,
        },
        "policy": {
            "policy_id": policy_id,
            "policy_version": policy_version,
        },
        "formal_discriminator_spec_jcs_sha256": formal_spec_digest,
        "generation_case_id": generation_case_id,
        "world_jcs_sha256": world_jcs_sha256,
        "prestate_jcs_sha256": prestate_jcs_sha256,
        "world_scoped_event_jcs_sha256": world_scoped_event_jcs_sha256,
        "producer_result_jcs_sha256": producer_result_jcs_sha256,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }


if __name__ == "__main__":
    print({
        "schema": PRODUCER_SCHEMA,
        "status": "SOURCE_ONLY_SYNTHETIC_PROOF_PRODUCER",
        "canonical_truth_allowed": False,
        "training_eligible": False,
    })
