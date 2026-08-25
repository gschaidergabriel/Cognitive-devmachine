#!/usr/bin/env python3
"""Trusted deterministic discriminator producer for Trigger-2 bounded pilot v1.

This producer is a request-scoped synthetic test executor, not a semantic oracle. It receives
only an authority-selected policy plus already generation-bound evaluator subjects and returns
one deterministic SYNTHETIC_PROOF execution result. It cannot mint canonical truth/effects,
dataset admission, runtime/J-Space/HCU/EntityOS credit, or training credit.

The producer deliberately does NOT trust the event's transported observed_outcome. The bounded
fixture result comes from repository-pinned policy material; the caller/gate must independently
compare that result to the generation-bound event and retained Hyperposition semantics.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

PRODUCER_SCHEMA = "CLAY_TRIGGER2_TRUSTED_DISCRIMINATOR_PRODUCER/v1"
POLICY_SCHEMA = "CLAY_TRIGGER2_DISCRIMINATOR_POLICY/v1"
EXECUTION_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_PRODUCER_RESULT/v1"


def execute(
    *,
    case_id: str,
    world: dict[str, Any],
    state_before: dict[str, Any],
    event_binding: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("CASE_ID_REQUIRED")
    if not isinstance(world, dict) or not isinstance(state_before, dict):
        raise ValueError("WORLD_AND_STATE_REQUIRED")
    if not isinstance(event_binding, dict):
        raise ValueError("EVENT_BINDING_REQUIRED")
    if not isinstance(policy, dict) or policy.get("schema") != POLICY_SCHEMA:
        raise ValueError("POLICY_SCHEMA_MISMATCH")
    if policy.get("case_id") != case_id:
        raise ValueError("POLICY_CASE_ID_MISMATCH")

    world_id = world.get("world_id")
    test_id = policy.get("test_id")
    if world_id != policy.get("world_id"):
        raise ValueError("POLICY_WORLD_ID_MISMATCH")
    if not isinstance(test_id, str) or not test_id:
        raise ValueError("POLICY_TEST_ID_REQUIRED")
    tests = world.get("tests")
    if not isinstance(tests, dict) or tests.get(test_id) != policy.get("formal_discriminator_spec"):
        raise ValueError("FORMAL_DISCRIMINATOR_SPEC_MISMATCH")

    scoped_event_id = event_binding.get("world_scoped_event_id")
    if not isinstance(scoped_event_id, str) or not scoped_event_id:
        raise ValueError("WORLD_SCOPED_EVENT_ID_REQUIRED")
    if event_binding.get("world_id") != world_id:
        raise ValueError("EVENT_BINDING_WORLD_ID_MISMATCH")
    if event_binding.get("test_id") != test_id:
        raise ValueError("EVENT_BINDING_TEST_ID_MISMATCH")

    branches = state_before.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        raise ValueError("STATE_REQUIRES_COMPETING_BRANCHES")

    fixture = policy.get("synthetic_fixture")
    if not isinstance(fixture, dict) or fixture.get("schema") != "CLAY_TRIGGER2_SYNTHETIC_DISCRIMINATOR_FIXTURE/v1":
        raise ValueError("SYNTHETIC_FIXTURE_SCHEMA_MISMATCH")
    fixture_id = fixture.get("fixture_id")
    observed_outcome = fixture.get("observed_outcome")
    if not isinstance(fixture_id, str) or not fixture_id:
        raise ValueError("SYNTHETIC_FIXTURE_ID_REQUIRED")

    spec = tests[test_id]
    outcomes = spec.get("allowed_outcomes")
    if not isinstance(outcomes, list) or observed_outcome not in outcomes:
        raise ValueError("FIXTURE_OUTCOME_NOT_ALLOWED_BY_FORMAL_SPEC")

    return {
        "schema": EXECUTION_SCHEMA,
        "producer_schema": PRODUCER_SCHEMA,
        "policy_id": policy.get("policy_id"),
        "case_id": case_id,
        "world_id": world_id,
        "test_id": test_id,
        "world_scoped_event_id": scoped_event_id,
        "fixture": {
            "schema": fixture["schema"],
            "fixture_id": fixture_id,
            "observed_outcome": deepcopy(observed_outcome),
        },
        "observed_outcome": deepcopy(observed_outcome),
        "state_branch_count": len(branches),
        "execution_completed": True,
        "epistemic_type": "SYNTHETIC_PROOF",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
    }


if __name__ == "__main__":
    print({
        "schema": PRODUCER_SCHEMA,
        "status": "TRUSTED_SYNTHETIC_PRODUCER_SOURCE_ONLY",
        "canonical_truth_allowed": False,
        "training_eligible": False,
    })
