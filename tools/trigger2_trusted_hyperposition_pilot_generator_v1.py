#!/usr/bin/env python3
"""Trusted deterministic Trigger-2 Hyperposition provenance pilot generator v1.

This generator produces evaluator-only synthetic subjects for one bounded provenance pilot.
It does not derive training labels and does not mint canonical truth/effect/runtime/J-Space/
HCU/EntityOS/training credit. Its purpose is to let a retained gate reconstruct the exact
formal world, dependence registry, event, and pre-event Hyperposition state from a fixed
case identity plus deterministic parameters instead of trusting row-supplied evaluator data.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

GENERATOR_SCHEMA = "CLAY_TRIGGER2_TRUSTED_HYPERPOSITION_PILOT_GENERATOR/v1"
CASE_ID = "T2_GP_PILOT_DB_MATCH_V1"
PARAMETER_SCHEMA = "CLAY_TRIGGER2_TRUSTED_HYPERPOSITION_PILOT_PARAMETERS/v1"
WORLD_SCHEMA = "XENO_HYPERPOSITION_FORMAL_TASK_WORLD/v1"
STATE_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_STATE/v3"
EVENT_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_EVENT/v3"
DEPENDENCE_SCHEMA = "XENO_SYNTHETIC_EVENT_DEPENDENCE_REGISTRY/v1"


def default_parameters() -> dict[str, Any]:
    return {
        "schema": PARAMETER_SCHEMA,
        "case_variant": "DB_MATCH",
        "world_scope": "synthetic_generation_provenance_pilot",
    }


def _branch(branch_id: str, semantic_value: str, prediction: str) -> dict[str, Any]:
    return {
        "branch_id": branch_id,
        "v": semantic_value,
        "K": "ALWAYS",
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": {"scope": "synthetic"},
        "A": {"origin": GENERATOR_SCHEMA, "case_id": CASE_ID},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": {"db_probe": prediction},
    }


def build_subjects(case_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    if case_id != CASE_ID:
        raise ValueError("UNKNOWN_GENERATION_CASE_ID")
    if parameters != default_parameters():
        raise ValueError("GENERATION_PARAMETERS_MISMATCH")

    event = {
        "schema": EVENT_SCHEMA,
        "event_id": "t2gp:event:db-match:v1",
        "correlation_ancestry_id": "t2gp:ancestry:db-match:v1",
        "independence_group": "t2gp:independence:db-match:v1",
        "payload_key": "t2gp:payload:db-match:v1",
        "provenance": GENERATOR_SCHEMA + ":" + CASE_ID,
        "epistemic_type": "SYNTHETIC_PROOF",
        "test_id": "db_probe",
        "observed_outcome": "MATCH",
        # Deliberately non-authoritative. Retained gate must derive this value.
        "independence_qualified": False,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    registry = {
        "schema": DEPENDENCE_SCHEMA,
        "events": {
            event["event_id"]: {
                "correlation_ancestry_id": event["correlation_ancestry_id"],
                "independence_group": event["independence_group"],
                "payload_key": event["payload_key"],
                "provenance": event["provenance"],
                "test_id": event["test_id"],
                "observed_outcome": event["observed_outcome"],
                "depends_on_event_ids": [],
            }
        },
    }
    world = {
        "schema": WORLD_SCHEMA,
        "world_id": "t2gp:world:db-match:v1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"scope": parameters["world_scope"]},
        "tests": {
            "db_probe": {
                "allowed_outcomes": ["MATCH", "MISSING"],
                "mismatch_effect": "FALSIFIES",
                "risk_rank": 0,
                "cost_rank": 0,
                "coordination_rank": 0,
            }
        },
        "merge_policy": "NONE",
        "branch_birth_rules": [],
        "event_dependence_registry": deepcopy(registry),
    }
    genesis = {
        "schema": STATE_SCHEMA,
        "query_id": "t2gp:query:db-match:v1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [
            _branch("db-backed", "USE_PROVENANCE_BOUND_DATABASE_STATE", "MATCH"),
            _branch("guess", "RECONSTRUCT_DURABLE_STATE_FROM_MODEL_GUESS", "MISSING"),
        ],
    }
    return {
        "schema": "XENO_SYNTHETIC_GENERATION_SUBJECT_BUNDLE/v1",
        "generator_schema": GENERATOR_SCHEMA,
        "generation_case_id": CASE_ID,
        "parameters": deepcopy(parameters),
        "formal_world": world,
        "event_dependence_registry": registry,
        "event": event,
        "state_before": genesis,
        "genesis_state": deepcopy(genesis),
        "event_history": [],
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
    }


def main() -> None:
    import json
    print(json.dumps(build_subjects(CASE_ID, default_parameters()), sort_keys=True, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
