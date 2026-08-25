#!/usr/bin/env python3
"""Formal synthetic-world relation derivation for Trigger-2 Hyperposition training.

This is an upstream *reference-label derivation primitive*, not a model, runtime or
truth authority. It closes the circular-label failure in which SUPPORTS/COUNTERS/
FALSIFIES, independence qualification, or discriminator utility are merely supplied
by a generator and then treated as ground truth.

Scope is deliberately small and exact: finite synthetic worlds whose branches are
conjunctions of typed atom=value claims and whose discriminators declare per-branch
predicted outcomes. Rich natural-language interpretation stays outside this module.
A future converged Hyperposition labeler/gate may consume the derived receipts.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

SCHEMA = "CLAY_TRIGGER2_FORMAL_WORLD_RELATION_DERIVER/v1"
WORLD_SCHEMA = "CLAY_TRIGGER2_FINITE_SYNTHETIC_WORLD/v1"
OBS_SCHEMA = "CLAY_TRIGGER2_FINITE_SYNTHETIC_OBSERVATION/v1"
TEST_OBS_SCHEMA = "CLAY_TRIGGER2_FINITE_SYNTHETIC_TEST_OBSERVATION/v1"

RELATIONS = {"SUPPORTS", "COUNTERS", "FALSIFIES", "IRRELEVANT"}
LIVE_SIGMA = {"LIVE_UNRESOLVED", "SUPPORTED_UNRESOLVED", "WEAKENED_UNRESOLVED", "RESOLVED_PASS"}


class DerivationError(ValueError):
    pass


def _canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha(x: Any) -> str:
    return hashlib.sha256(_canon(x).encode("utf-8")).hexdigest()


def _require_bool_false(obj: dict[str, Any], key: str, where: str) -> None:
    if obj.get(key) is not False:
        raise DerivationError(f"{where}: {key} must be false")


def _validate_world(world: Any) -> dict[str, Any]:
    if not isinstance(world, dict) or world.get("schema") != WORLD_SCHEMA:
        raise DerivationError("world: schema mismatch")
    _require_bool_false(world, "canonical_truth_allowed", "world")
    _require_bool_false(world, "direct_effect_authority", "world")
    if not isinstance(world.get("world_id"), str) or not world["world_id"]:
        raise DerivationError("world: world_id required")
    branches = world.get("branches")
    if not isinstance(branches, dict) or len(branches) < 2:
        raise DerivationError("world: at least two branch specifications required")
    for bid, spec in branches.items():
        if not isinstance(bid, str) or not bid or not isinstance(spec, dict):
            raise DerivationError("world: invalid branch specification")
        atoms = spec.get("claims")
        if not isinstance(atoms, dict) or not atoms:
            raise DerivationError(f"world: branch {bid} claims required")
        if any(not isinstance(k, str) or not k for k in atoms):
            raise DerivationError(f"world: branch {bid} invalid atom id")
        falsifiers = spec.get("falsifier_atoms", [])
        if not isinstance(falsifiers, list) or any(x not in atoms for x in falsifiers):
            raise DerivationError(f"world: branch {bid} falsifier_atoms must reference claims")
    tests = world.get("tests", {})
    if not isinstance(tests, dict):
        raise DerivationError("world: tests must be object")
    for tid, test in tests.items():
        if not isinstance(tid, str) or not tid or not isinstance(test, dict):
            raise DerivationError("world: invalid test specification")
        if test.get("admissible") not in {True, False}:
            raise DerivationError(f"world: test {tid} admissible must be boolean")
        outcomes = test.get("predicted_outcomes")
        if not isinstance(outcomes, dict) or set(outcomes) != set(branches):
            raise DerivationError(f"world: test {tid} must predict every branch outcome")
    return world


def _state_live_ids(state: Any, world: dict[str, Any]) -> list[str]:
    if not isinstance(state, dict) or not isinstance(state.get("branches"), list):
        raise DerivationError("state: branches required")
    ids = []
    seen = set()
    for branch in state["branches"]:
        if not isinstance(branch, dict) or not isinstance(branch.get("branch_id"), str):
            raise DerivationError("state: branch_id required")
        bid = branch["branch_id"]
        if bid in seen:
            raise DerivationError("state: duplicate branch id")
        seen.add(bid)
        if bid not in world["branches"]:
            raise DerivationError(f"state: branch {bid} absent from formal world")
        if branch.get("K") != "DOES_NOT_APPLY" and branch.get("sigma") in LIVE_SIGMA:
            ids.append(bid)
    return sorted(ids)


def _iter_state_evidence(state: dict[str, Any]):
    for branch in state.get("branches", []):
        for field in ("E_plus", "E_minus", "F", "pending_falsifiers", "correlated_observations"):
            for ev in branch.get(field, []) or []:
                if isinstance(ev, dict):
                    yield ev


def _event_digest(observation: dict[str, Any]) -> str:
    payload = {
        "evidence_event_id": observation.get("evidence_event_id"),
        "correlation_ancestry_id": observation.get("correlation_ancestry_id"),
        "independence_group": observation.get("independence_group"),
        "provenance": observation.get("provenance"),
        "atoms": observation.get("atoms"),
    }
    return _sha(payload)


def derive_independence(state: dict[str, Any], observation: dict[str, Any], event_registry: Any = None) -> dict[str, Any]:
    """Derive replay/correlation credit instead of trusting an independence flag.

    Same event id with a different immutable event digest is a hard failure. A distinct
    event sharing either correlation ancestry or declared independence group is retained
    but receives no independent evidence credit.
    """
    eid = observation.get("evidence_event_id")
    anc = observation.get("correlation_ancestry_id")
    group = observation.get("independence_group")
    if not all(isinstance(x, str) and x for x in (eid, anc, group)):
        raise DerivationError("observation: event, ancestry and independence-group ids required")
    digest = _event_digest(observation)
    registry = event_registry or {}
    if not isinstance(registry, dict):
        raise DerivationError("event_registry must be object")
    if eid in registry:
        if registry[eid] != digest:
            raise DerivationError("same evidence_event_id has different immutable digest")
        return {
            "exact_replay": True,
            "independence_qualified": False,
            "event_digest": digest,
            "reason": "EXACT_EVENT_REPLAY_IDEMPOTENT",
        }
    prior = list(_iter_state_evidence(state))
    same_ancestry = any(str(e.get("correlation_ancestry_id", "")) == anc for e in prior)
    same_group = any(str(e.get("independence_group", "")) == group for e in prior)
    return {
        "exact_replay": False,
        "independence_qualified": not same_ancestry and not same_group,
        "event_digest": digest,
        "reason": "CORRELATED_OR_SHARED_DEPENDENCE_GROUP" if same_ancestry or same_group else "NOVEL_CAUSAL_DEPENDENCE_GROUP",
    }


def _relation(branch_spec: dict[str, Any], atoms: dict[str, Any]) -> dict[str, Any]:
    claims = branch_spec["claims"]
    overlap = sorted(set(claims) & set(atoms))
    if not overlap:
        return {"relation": "IRRELEVANT", "matched_atoms": [], "contradicted_atoms": []}
    matched = [k for k in overlap if atoms[k] == claims[k]]
    contradicted = [k for k in overlap if atoms[k] != claims[k]]
    if contradicted:
        falsifier_set = set(branch_spec.get("falsifier_atoms", []))
        decisive = sorted(set(contradicted) & falsifier_set)
        return {
            "relation": "FALSIFIES" if decisive else "COUNTERS",
            "matched_atoms": matched,
            "contradicted_atoms": contradicted,
            "triggered_falsifier_atoms": decisive,
        }
    return {"relation": "SUPPORTS", "matched_atoms": matched, "contradicted_atoms": []}


def derive_observation(world: Any, state: Any, observation: Any, *, event_registry: Any = None) -> dict[str, Any]:
    """Derive per-branch relations from formal branch claims and observed atoms."""
    world = _validate_world(world)
    if not isinstance(observation, dict) or observation.get("schema") != OBS_SCHEMA:
        raise DerivationError("observation: schema mismatch")
    _require_bool_false(observation, "canonical_truth_allowed", "observation")
    _require_bool_false(observation, "direct_effect_authority", "observation")
    atoms = observation.get("atoms")
    if not isinstance(atoms, dict) or not atoms:
        raise DerivationError("observation: atoms required")
    live_ids = _state_live_ids(state, world)
    indep = derive_independence(state, observation, event_registry)
    rows = []
    for bid in live_ids:
        rel = _relation(world["branches"][bid], atoms)
        rows.append({"branch_id": bid, **rel})

    survivors = [r["branch_id"] for r in rows if r["relation"] != "FALSIFIES"]
    for r in rows:
        if r["relation"] == "FALSIFIES":
            r["decision_role"] = "DECISIVE_CONTRADICTION"
        elif r["relation"] == "SUPPORTS" and len(survivors) == 1 and survivors[0] == r["branch_id"] and any(x["relation"] == "FALSIFIES" for x in rows):
            r["decision_role"] = "DECISIVE_SUPPORT"
        else:
            r["decision_role"] = "NONDECISIVE"

    labeler_observations = []
    for relation in sorted(RELATIONS):
        targets = [r["branch_id"] for r in rows if r["relation"] == relation]
        if not targets or relation == "IRRELEVANT":
            continue
        labeler_observations.append({
            "relation": relation,
            "target_branch_ids": targets,
            "evidence_event_id": observation["evidence_event_id"],
            "correlation_ancestry_id": observation["correlation_ancestry_id"],
            "independence_group": observation["independence_group"],
            "provenance": observation.get("provenance", "SYNTHETIC_FORMAL_WORLD"),
            "independence_qualified": indep["independence_qualified"],
            "event_digest": indep["event_digest"],
        })

    receipt = {
        "schema": SCHEMA,
        "derivation_kind": "FINITE_ATOM_OBSERVATION",
        "world_id": world["world_id"],
        "world_sha256": _sha(world),
        "state_sha256": _sha(state),
        "observation_sha256": _sha(observation),
        "event_identity": indep,
        "branch_relations": rows,
        "surviving_live_branch_ids": survivors,
        "labeler_observations": labeler_observations,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "training_credit_minted": False,
    }
    receipt["receipt_sha256"] = _sha(receipt)
    return receipt


def derive_discriminator(world: Any, state: Any, test_observation: Any) -> dict[str, Any]:
    """Derive a test outcome partition and adequacy from formal predicted outcomes."""
    world = _validate_world(world)
    if not isinstance(test_observation, dict) or test_observation.get("schema") != TEST_OBS_SCHEMA:
        raise DerivationError("test observation: schema mismatch")
    _require_bool_false(test_observation, "canonical_truth_allowed", "test observation")
    _require_bool_false(test_observation, "direct_effect_authority", "test observation")
    tid = test_observation.get("test_id")
    if tid not in world["tests"]:
        raise DerivationError("test observation: unknown test_id")
    observed = test_observation.get("observed_outcome")
    test = world["tests"][tid]
    live_ids = _state_live_ids(state, world)
    predicted = {bid: test["predicted_outcomes"][bid] for bid in live_ids}
    matches = sorted([bid for bid, outcome in predicted.items() if outcome == observed])
    partition: dict[str, list[str]] = {}
    for bid, outcome in predicted.items():
        partition.setdefault(_canon(outcome), []).append(bid)
    partition_rows = [sorted(v) for _, v in sorted(partition.items())]
    adequate_unique = bool(test["admissible"] and observed is not None and len(matches) == 1 and len(predicted) == len(live_ids))
    branch_relations = [
        {
            "branch_id": bid,
            "predicted_outcome": predicted[bid],
            "relation": "SUPPORTS" if bid in matches else "FALSIFIES",
            "decision_role": "DECISIVE_SUPPORT" if adequate_unique and bid in matches else "DECISIVE_CONTRADICTION" if adequate_unique else "NONDECISIVE",
        }
        for bid in live_ids
    ]
    receipt = {
        "schema": SCHEMA,
        "derivation_kind": "FINITE_DISCRIMINATOR_OUTCOME",
        "world_id": world["world_id"],
        "world_sha256": _sha(world),
        "state_sha256": _sha(state),
        "test_observation_sha256": _sha(test_observation),
        "test_id": tid,
        "test_admissible": bool(test["admissible"]),
        "test_executed": True,
        "predicted_outcomes": predicted,
        "outcome_partition": partition_rows,
        "observed_outcome": observed,
        "matching_live_branch_ids": matches,
        "adequate_unique_resolution": adequate_unique,
        "branch_relations": branch_relations,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "training_credit_minted": False,
    }
    receipt["receipt_sha256"] = _sha(receipt)
    return receipt


def verify_receipt(receipt: Any) -> bool:
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        return False
    claimed = receipt.get("receipt_sha256")
    body = deepcopy(receipt)
    body.pop("receipt_sha256", None)
    return isinstance(claimed, str) and claimed == _sha(body)
