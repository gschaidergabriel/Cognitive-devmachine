#!/usr/bin/env python3
"""Trusted deterministic discriminator producer for Trigger-2 bounded synthetic pilot.

The producer is intentionally noncanonical. It recomputes a synthetic discriminator
decision from the formal world, pre-state and event using the retained v3 reference
ordering logic. It never accepts caller-supplied admissible/executed/receipt identifiers.

Its exact source bytes are expected to be pinned by repository authority before use.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

PRODUCER_SCHEMA = "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_PRODUCER/v1"
RECEIPT_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_EXECUTION_RECEIPT/v1"
POLICY_SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_DISCRIMINATOR_POLICY/v1"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_sibling(
    "trigger2_hyperposition_derivation_bound_gate_v2.py",
    "trigger2_derivation_bound_for_trusted_discriminator_v1",
)
lab = base.lab


def _digest(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _event_semantic_payload(event: Any) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
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
        return None
    return {key: event[key] for key in keys}


def event_semantic_sha256(event: Any) -> str | None:
    payload = _event_semantic_payload(event)
    return None if payload is None else _digest(payload)


def _policy_ok(policy: Any) -> bool:
    return isinstance(policy, dict) and policy == {
        "schema": POLICY_SCHEMA,
        "policy_id": "T2_SYNTHETIC_COMPLETE_COMPETITOR_DISCRIMINATOR/v1",
        "required_epistemic_type": "SYNTHETIC_PROOF",
        "require_test_declared_in_world": True,
        "require_allowed_outcome": True,
        "require_complete_live_pair_coverage": True,
        "require_noncanonical_fences": True,
    }


def produce(world: Any, state_before: Any, event: Any, policy: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(world, dict):
        failures.append("WORLD_OBJECT_REQUIRED")
    if not isinstance(state_before, dict):
        failures.append("STATE_BEFORE_OBJECT_REQUIRED")
    if not isinstance(event, dict):
        failures.append("EVENT_OBJECT_REQUIRED")
    if not _policy_ok(policy):
        failures.append("POLICY_NOT_EXACTLY_PINNED")

    event_digest = event_semantic_sha256(event) if isinstance(event, dict) else None
    test_id = event.get("test_id") if isinstance(event, dict) else None
    test_spec = world.get("tests", {}).get(test_id) if isinstance(world, dict) and isinstance(world.get("tests"), dict) else None

    if isinstance(event, dict) and event.get("epistemic_type") != "SYNTHETIC_PROOF":
        failures.append("EPISTEMIC_TYPE_NOT_SYNTHETIC_PROOF")
    if isinstance(world, dict) and (
        world.get("canonical_truth_allowed") is not False
        or world.get("direct_effect_authority") is not False
    ):
        failures.append("WORLD_NONCANONICAL_FENCES_REQUIRED")
    if isinstance(event, dict) and (
        event.get("canonical_truth_allowed") is not False
        or event.get("direct_effect_authority") is not False
    ):
        failures.append("EVENT_NONCANONICAL_FENCES_REQUIRED")
    if not isinstance(test_id, str) or not test_id or not isinstance(test_spec, dict):
        failures.append("TEST_NOT_DECLARED_IN_WORLD")
    elif event.get("observed_outcome") not in (test_spec.get("allowed_outcomes") or []):
        failures.append("OBSERVED_OUTCOME_NOT_ALLOWED")

    ordering_row = None
    if not failures:
        try:
            ordering = lab.u_test_order(world, state_before, [test_id])
        except Exception as exc:
            failures.append("U_TEST_ORDER_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(ordering, dict) or not ordering.get("pass"):
                failures.append("U_TEST_ORDER_REJECTED:" + str(ordering.get("failure") if isinstance(ordering, dict) else None))
            else:
                rows = ordering.get("ordering")
                if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
                    failures.append("U_TEST_ORDER_SINGLE_RESULT_REQUIRED")
                else:
                    ordering_row = rows[0]
                    if not isinstance(ordering_row.get("separated_live_pairs"), int) or ordering_row.get("separated_live_pairs", 0) <= 0:
                        failures.append("DISCRIMINATOR_MUST_SEPARATE_AT_LEAST_ONE_LIVE_PAIR")
                    if ordering_row.get("separates_all_live_pairs") is not True:
                        failures.append("DISCRIMINATOR_COMPLETE_LIVE_PAIR_COVERAGE_REQUIRED")

    failures = sorted(set(failures))
    if failures:
        return {
            "schema": PRODUCER_SCHEMA,
            "pass": False,
            "failures": failures,
            "receipt": None,
            "canonical_truth_minted": False,
            "direct_effect_authority_minted": False,
            "training_credit_minted": 0,
        }

    discriminator_spec = {
        "test_id": test_id,
        "test_spec": test_spec,
        "policy": policy,
    }
    binding = {
        "producer_schema": PRODUCER_SCHEMA,
        "world_id": world.get("world_id"),
        "world_sha256": _digest(world),
        "state_before_sha256": _digest(state_before),
        "event_semantic_sha256": event_digest,
        "discriminator_spec_sha256": _digest(discriminator_spec),
        "observed_outcome": event.get("observed_outcome"),
        "separated_live_pairs": ordering_row["separated_live_pairs"],
        "separates_all_live_pairs": ordering_row["separates_all_live_pairs"],
    }
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "execution_receipt_id": "t2dp:" + _digest(binding),
        "event_id": event.get("event_id"),
        "test_id": test_id,
        "observed_outcome": event.get("observed_outcome"),
        "event_semantic_sha256": event_digest,
        "world_sha256": binding["world_sha256"],
        "admissible": True,
        "executed": True,
        "separated_live_pairs": ordering_row["separated_live_pairs"],
        "separates_all_live_pairs": ordering_row["separates_all_live_pairs"],
        "producer_schema": PRODUCER_SCHEMA,
        "state_before_sha256": binding["state_before_sha256"],
        "discriminator_spec_sha256": binding["discriminator_spec_sha256"],
    }
    return {
        "schema": PRODUCER_SCHEMA,
        "pass": True,
        "failures": [],
        "receipt": receipt,
        "binding": binding,
        "synthetic_execution_only": True,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "training_credit_minted": 0,
    }


if __name__ == "__main__":
    print({
        "schema": PRODUCER_SCHEMA,
        "status": "TRUSTED_SOURCE_CANDIDATE_NONPROMOTING",
    })
