#!/usr/bin/env python3
"""Trusted deterministic Trigger-2 Hyperposition provenance pilot generator v1.

This generator produces evaluator-only synthetic subjects for one bounded provenance pilot.
It does not derive training labels and does not mint canonical truth/effect/runtime/J-Space/
HCU/EntityOS/training credit. Its purpose is to let a retained gate reconstruct the exact
formal world, dependence registry, event, and pre-event Hyperposition state from a fixed
case identity plus deterministic parameters instead of trusting row-supplied evaluator data.

Two authorized cases:
  T2_GP_PILOT_DB_MATCH_V1       - single current event, empty genesis/history (Phase 2 lane).
  T2_GP_PILOT_HIST_CHAIN_V1     - a clean genesis plus a one-event ordered history plus a
                                   current event, for immutable genesis/ordered-history
                                   producer-authority closure (Phase 3 lane). Both cases share
                                   this one generator/authority; no second authority is created.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Any

GENERATOR_SCHEMA = "CLAY_TRIGGER2_TRUSTED_HYPERPOSITION_PILOT_GENERATOR/v1"
CASE_ID = "T2_GP_PILOT_DB_MATCH_V1"
HIST_CHAIN_CASE_ID = "T2_GP_PILOT_HIST_CHAIN_V1"
PARAMETER_SCHEMA = "CLAY_TRIGGER2_TRUSTED_HYPERPOSITION_PILOT_PARAMETERS/v1"
WORLD_SCHEMA = "XENO_HYPERPOSITION_FORMAL_TASK_WORLD/v1"
STATE_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_STATE/v3"
EVENT_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_EVENT/v3"
DEPENDENCE_SCHEMA = "XENO_SYNTHETIC_EVENT_DEPENDENCE_REGISTRY/v1"
_BASE_GATE_FILENAME = "trigger2_hyperposition_derivation_bound_gate_v2.py"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _event_semantic_payload(event: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "schema", "event_id", "correlation_ancestry_id", "independence_group",
        "payload_key", "provenance", "epistemic_type", "test_id", "observed_outcome",
        "canonical_truth_allowed", "direct_effect_authority",
    )
    return {k: deepcopy(event[k]) for k in keys}


def _event_semantic_sha256(event: dict[str, Any]) -> str:
    import json
    from hashlib import sha256
    payload = _event_semantic_payload(event)
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _decorate(state: dict[str, Any], event_id: str, digest: str) -> None:
    for branch in state.get("branches", []) or []:
        if not isinstance(branch, dict):
            continue
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for rec in branch.get(field, []) or []:
                if isinstance(rec, dict) and rec.get("event_id") == event_id:
                    rec["event_sha256"] = digest


def _replay_one_step(world: dict[str, Any], state_before: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Apply one event using the same retained v3 labeler + independence deriver every gate
    uses (trigger2_hyperposition_derivation_bound_gate_v2.py), then decorate the resulting
    records with the event's semantic digest exactly like the replay-bound proof gate does.
    This keeps the generator's precomputed state_before byte-identical to what any correct
    gate-side replay independently recomputes -- no separate semantic authority is created."""
    base = _load_sibling(_BASE_GATE_FILENAME, "trigger2_hp_derivation_gate_v2_for_generator")
    independence = base.derive_independence(world, state_before, event)
    event_for_lab = deepcopy(event)
    event_for_lab["independence_qualified"] = bool(independence.get("derived_independence_qualified", False))
    update = base.lab.u_state(world, state_before, event_for_lab)
    if not update.get("pass"):
        raise ValueError("HIST_CHAIN_GENERATOR_REPLAY_STEP_REJECTED:" + str(update.get("failure")))
    state_after = deepcopy(update["state_after"])
    _decorate(state_after, event["event_id"], _event_semantic_sha256(event))
    return state_after


def default_parameters() -> dict[str, Any]:
    return {
        "schema": PARAMETER_SCHEMA,
        "case_variant": "DB_MATCH",
        "world_scope": "synthetic_generation_provenance_pilot",
    }


def hist_chain_parameters() -> dict[str, Any]:
    return {
        "schema": PARAMETER_SCHEMA,
        "case_variant": "HIST_CHAIN",
        "world_scope": "synthetic_generation_provenance_hist_chain_pilot",
    }


def _branch(branch_id: str, semantic_value: str, case_id: str, predictions: dict[str, str]) -> dict[str, Any]:
    return {
        "branch_id": branch_id,
        "v": semantic_value,
        "K": "ALWAYS",
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": {"scope": "synthetic"},
        "A": {"origin": GENERATOR_SCHEMA, "case_id": case_id},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": dict(predictions),
    }


def build_subjects(case_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
    if case_id == CASE_ID:
        return _build_db_match_subjects(parameters)
    if case_id == HIST_CHAIN_CASE_ID:
        return _build_hist_chain_subjects(parameters)
    raise ValueError("UNKNOWN_GENERATION_CASE_ID")


# Pinned model-visible prompt text per authorized generation_case_id. Added 2026-08-26
# alongside tools/trigger2_prompt_content_binding_gate_v1.py to close a gap where a
# row's model_visible 'prompt' field was not bound to any generator authority and
# could be swapped after row assembly with zero detection by any of the previously
# wired v4 per-row checks. Same recompute-don't-trust pattern as A02's producer.produce().
_PROMPT_TEXT_BY_CASE_ID = {
    CASE_ID: (
        "DB_MATCH gold-pilot candidate: canonical database fact must win over a "
        "contradicting simulation."
    ),
}


def render_prompt(case_id: str, parameters: dict[str, Any]) -> str:
    """Deterministically render the authorized model-visible prompt for case_id.

    Pure function of (case_id, parameters); raises ValueError for any case_id/parameters
    pair this authority does not explicitly pin a prompt for -- fail-closed, no fallback
    to caller-supplied text.
    """
    if case_id == CASE_ID:
        if parameters != default_parameters():
            raise ValueError("PARAMETERS_NOT_AUTHORIZED_FOR_CASE_ID")
        return _PROMPT_TEXT_BY_CASE_ID[CASE_ID]
    raise ValueError("NO_PINNED_PROMPT_FOR_GENERATION_CASE_ID")


def _build_db_match_subjects(parameters: dict[str, Any]) -> dict[str, Any]:
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
            _branch("db-backed", "USE_PROVENANCE_BOUND_DATABASE_STATE", CASE_ID, {"db_probe": "MATCH"}),
            _branch("guess", "RECONSTRUCT_DURABLE_STATE_FROM_MODEL_GUESS", CASE_ID, {"db_probe": "MISSING"}),
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


def _build_hist_chain_subjects(parameters: dict[str, Any]) -> dict[str, Any]:
    if parameters != hist_chain_parameters():
        raise ValueError("GENERATION_PARAMETERS_MISMATCH")

    step1 = {
        "schema": EVENT_SCHEMA,
        "event_id": "t2gp:event:hist-chain:step1:v1",
        "correlation_ancestry_id": "t2gp:ancestry:hist-chain:step1:v1",
        "independence_group": "t2gp:independence:hist-chain:step1:v1",
        "payload_key": "t2gp:payload:hist-chain:step1:v1",
        "provenance": GENERATOR_SCHEMA + ":" + HIST_CHAIN_CASE_ID,
        "epistemic_type": "SYNTHETIC_PROOF",
        "test_id": "t1",
        "observed_outcome": "B",
        "independence_qualified": False,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    step2 = {
        "schema": EVENT_SCHEMA,
        "event_id": "t2gp:event:hist-chain:step2:v1",
        "correlation_ancestry_id": "t2gp:ancestry:hist-chain:step2:v1",
        "independence_group": "t2gp:independence:hist-chain:step2:v1",
        "payload_key": "t2gp:payload:hist-chain:step2:v1",
        "provenance": GENERATOR_SCHEMA + ":" + HIST_CHAIN_CASE_ID,
        "epistemic_type": "SYNTHETIC_PROOF",
        "test_id": "t2",
        "observed_outcome": "P",
        "independence_qualified": False,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    registry = {
        "schema": DEPENDENCE_SCHEMA,
        "events": {
            step1["event_id"]: {
                "correlation_ancestry_id": step1["correlation_ancestry_id"],
                "independence_group": step1["independence_group"],
                "payload_key": step1["payload_key"],
                "provenance": step1["provenance"],
                "test_id": step1["test_id"],
                "observed_outcome": step1["observed_outcome"],
                "depends_on_event_ids": [],
            },
            step2["event_id"]: {
                "correlation_ancestry_id": step2["correlation_ancestry_id"],
                "independence_group": step2["independence_group"],
                "payload_key": step2["payload_key"],
                "provenance": step2["provenance"],
                "test_id": step2["test_id"],
                "observed_outcome": step2["observed_outcome"],
                "depends_on_event_ids": [],
            },
        },
    }
    world = {
        "schema": WORLD_SCHEMA,
        "world_id": "t2gp:world:hist-chain:v1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"scope": parameters["world_scope"]},
        "tests": {
            "t1": {
                "allowed_outcomes": ["A", "B"],
                "mismatch_effect": "FALSIFIES",
                "risk_rank": 0,
                "cost_rank": 0,
                "coordination_rank": 0,
            },
            "t2": {
                "allowed_outcomes": ["P", "Q"],
                "mismatch_effect": "FALSIFIES",
                "risk_rank": 0,
                "cost_rank": 0,
                "coordination_rank": 0,
            },
        },
        "merge_policy": "NONE",
        "branch_birth_rules": [],
        "event_dependence_registry": deepcopy(registry),
    }
    genesis = {
        "schema": STATE_SCHEMA,
        "query_id": "t2gp:query:hist-chain:v1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [
            _branch("b1", "HIST_CHAIN_BRANCH_ONE", HIST_CHAIN_CASE_ID, {"t1": "A", "t2": "P"}),
            _branch("b2", "HIST_CHAIN_BRANCH_TWO", HIST_CHAIN_CASE_ID, {"t1": "B", "t2": "P"}),
            _branch("b3", "HIST_CHAIN_BRANCH_THREE", HIST_CHAIN_CASE_ID, {"t1": "B", "t2": "Q"}),
        ],
    }
    # state_before is the post-genesis+history replay state, computed the same way any
    # correct gate-side replay recomputes it -- not hand-authored -- so the authority-pinned
    # subject hash is guaranteed to match a real replay, never a fabricated shortcut.
    state_before = _replay_one_step(world, genesis, step1)
    return {
        "schema": "XENO_SYNTHETIC_GENERATION_SUBJECT_BUNDLE/v1",
        "generator_schema": GENERATOR_SCHEMA,
        "generation_case_id": HIST_CHAIN_CASE_ID,
        "parameters": deepcopy(parameters),
        "formal_world": world,
        "event_dependence_registry": registry,
        "event": step2,
        "state_before": state_before,
        "genesis_state": deepcopy(genesis),
        "event_history": [step1],
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
    }


def main() -> None:
    import json
    print(json.dumps(build_subjects(CASE_ID, default_parameters()), sort_keys=True, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
