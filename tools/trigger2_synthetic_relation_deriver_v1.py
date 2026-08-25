#!/usr/bin/env python3
"""Deterministic Trigger-2 synthetic-world relation/discriminator deriver v1.

This primitive addresses the current D/E label circularity blocker by deriving branch
relations from branch predictions plus an observed discriminator outcome. The caller is
not allowed to provide SUPPORTS/COUNTERS/FALSIFIES as a target label.

Scope is deliberately narrow: exact or soft synthetic discriminator episodes whose live
branches already contain explicit predictions for a versioned test. Branch birth and
model/world-fact authority are out of scope. This source never mints canonical truth,
real-effect authority, model/J-Space/HCU/EntityOS runtime credit, accepted-dataset credit,
or training credit.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Dict, Iterable

SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_RELATION_DERIVER/v1"
DERIVATION_RECEIPT_SCHEMA = "CLAY_TRIGGER2_DERIVATION_RECEIPT/v1"
RESOLUTION_RECEIPT_SCHEMA = "CLAY_TRIGGER2_DISCRIMINATOR_RESOLUTION_RECEIPT/v1"

BRANCH_FIELDS = (
    "branch_id",
    "v",
    "K",
    "E_plus",
    "E_minus",
    "F",
    "T",
    "A",
    "sigma",
    "projection_visibility",
    "predictions",
)
ALLOWED_CONTEXT = {"APPLIES", "UNKNOWN", "DOES_NOT_APPLY"}
ALLOWED_SIGMA = {
    "LIVE_UNRESOLVED",
    "SUPPORTED_UNRESOLVED",
    "WEAKENED_UNRESOLVED",
    "FALSIFIED",
    "RESOLVED_PASS",
}


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _event_id(evidence: Dict[str, Any]) -> str:
    return str(evidence.get("evidence_event_id") or "")


def _event_digest_from_observation(observation: Dict[str, Any]) -> str:
    immutable = {
        "evidence_event_id": observation.get("evidence_event_id"),
        "correlation_ancestry_id": observation.get("correlation_ancestry_id"),
        "independence_group": observation.get("independence_group"),
        "provenance": observation.get("provenance"),
        "test_id": observation.get("test_id"),
        "observed_outcome": observation.get("observed_outcome"),
    }
    return _canonical_digest(immutable)


def _iter_evidence(branches: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for branch in branches:
        for field in ("E_plus", "E_minus", "F", "pending_falsifiers", "correlated_observations"):
            values = branch.get(field, []) or []
            if not isinstance(values, list):
                continue
            for item in values:
                if isinstance(item, dict):
                    yield item


def _validate_branch(branch: Any) -> Dict[str, Any]:
    if not isinstance(branch, dict):
        raise ValueError("branch object required")
    for field in BRANCH_FIELDS:
        if field not in branch:
            raise ValueError(f"branch missing mandatory field: {field}")
    if not _nonempty(branch.get("branch_id")):
        raise ValueError("branch_id required")
    if branch.get("K") not in ALLOWED_CONTEXT:
        raise ValueError("invalid branch K context state")
    if branch.get("sigma") not in ALLOWED_SIGMA:
        raise ValueError("invalid branch sigma")
    for field in ("E_plus", "E_minus", "F"):
        if not isinstance(branch.get(field), list):
            raise ValueError(f"branch {field} must be list")
    if not isinstance(branch.get("predictions"), dict):
        raise ValueError("branch predictions must be object")
    return branch


def _validate_state(state: Any) -> list[Dict[str, Any]]:
    if not isinstance(state, dict):
        raise ValueError("state object required")
    if state.get("canonical_truth_allowed") is not False:
        raise ValueError("canonical_truth_allowed must be false")
    if state.get("direct_effect_authority") is not False:
        raise ValueError("direct_effect_authority must be false")
    branches = state.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        raise ValueError("at least two branches required")
    seen: set[str] = set()
    for raw in branches:
        branch = _validate_branch(raw)
        bid = branch["branch_id"]
        if bid in seen:
            raise ValueError("duplicate branch_id")
        seen.add(bid)
    catalog = state.get("discriminator_catalog")
    if not isinstance(catalog, dict):
        raise ValueError("discriminator_catalog object required")
    return branches


def _validate_observation(observation: Any) -> Dict[str, Any]:
    if not isinstance(observation, dict):
        raise ValueError("observation object required")
    if "relation" in observation or "winner_branch_id" in observation:
        raise ValueError("caller-supplied relation/winner labels are forbidden")
    if "new_branch_payload" in observation or "branch_creation_warranted" in observation:
        raise ValueError("branch birth is not admitted by relation deriver v1")
    for field in (
        "evidence_event_id",
        "correlation_ancestry_id",
        "independence_group",
        "provenance",
        "test_id",
        "observed_outcome",
    ):
        if field not in observation:
            raise ValueError(f"observation missing field: {field}")
    for field in ("evidence_event_id", "correlation_ancestry_id", "independence_group", "test_id"):
        if not _nonempty(observation.get(field)):
            raise ValueError(f"observation field must be nonempty string: {field}")
    return observation


def _validate_test(test_id: str, catalog: Dict[str, Any]) -> Dict[str, Any]:
    test = catalog.get(test_id)
    if not isinstance(test, dict):
        raise ValueError("test_id absent from discriminator_catalog")
    if test.get("test_id") not in (None, test_id):
        raise ValueError("catalog test_id mismatch")
    if not isinstance(test.get("admissible"), bool):
        raise ValueError("catalog test admissible must be bool")
    if not isinstance(test.get("exact_outcome_discriminator"), bool):
        raise ValueError("catalog exact_outcome_discriminator must be bool")
    return test


def _existing_event_index(branches: Iterable[Dict[str, Any]]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in _iter_evidence(branches):
        event_id = _event_id(item)
        if not event_id:
            continue
        digest = item.get("event_digest")
        if not _nonempty(digest):
            raise ValueError(f"existing evidence event lacks immutable event_digest: {event_id}")
        previous = result.get(event_id)
        if previous is not None and previous != digest:
            raise ValueError(f"existing evidence_event_id identity conflict: {event_id}")
        result[event_id] = digest
    return result


def _prior_dependence(branches: Iterable[Dict[str, Any]]) -> tuple[set[str], set[str]]:
    ancestries: set[str] = set()
    groups: set[str] = set()
    for item in _iter_evidence(branches):
        ancestry = item.get("correlation_ancestry_id")
        group = item.get("independence_group")
        if _nonempty(ancestry):
            ancestries.add(ancestry)
        if _nonempty(group):
            groups.add(group)
    return ancestries, groups


def _record(
    observation: Dict[str, Any],
    *,
    event_digest: str,
    relation: str,
    independent_credit: bool,
    target_branch_id: str,
) -> Dict[str, Any]:
    return {
        "evidence_event_id": observation["evidence_event_id"],
        "event_digest": event_digest,
        "correlation_ancestry_id": observation["correlation_ancestry_id"],
        "independence_group": observation["independence_group"],
        "provenance": deepcopy(observation["provenance"]),
        "test_id": observation["test_id"],
        "observed_outcome": deepcopy(observation["observed_outcome"]),
        "relation": relation,
        "independent_credit": bool(independent_credit),
        "target_branch_id": target_branch_id,
    }


def derive_relation(predicted_outcome: Any, observed_outcome: Any, *, exact: bool) -> str:
    if predicted_outcome == "UNKNOWN" or predicted_outcome is None:
        return "UNKNOWN_RELATION"
    if predicted_outcome == observed_outcome:
        return "SUPPORTS"
    return "FALSIFIES" if exact else "COUNTERS"


def derive(state: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
    """Derive branch relations, state transition and bounded resolution from inputs."""
    branches_before = _validate_state(state)
    observation = _validate_observation(observation)
    test_id = observation["test_id"]
    test = _validate_test(test_id, state["discriminator_catalog"])

    event_digest = _event_digest_from_observation(observation)
    existing_events = _existing_event_index(branches_before)
    event_id = observation["evidence_event_id"]
    if event_id in existing_events:
        if existing_events[event_id] != event_digest:
            raise ValueError(f"same evidence_event_id with mutated immutable payload: {event_id}")
        return {
            "schema": SCHEMA,
            "status": "EXACT_REPLAY_IDEMPOTENT",
            "state_after": deepcopy(state),
            "relations": {},
            "resolution": {"status": "UNRESOLVED", "resolved_branch_id": None},
            "canonical_truth_minted": False,
            "direct_effect_authority_minted": False,
            "training_credit_minted": False,
        }

    prior_ancestries, prior_groups = _prior_dependence(branches_before)
    independent_credit = (
        observation["correlation_ancestry_id"] not in prior_ancestries
        and observation["independence_group"] not in prior_groups
    )

    out = deepcopy(state)
    branches_after = out["branches"]
    relations: Dict[str, str] = {}
    predictions: Dict[str, Any] = {}
    for branch in branches_after:
        bid = branch["branch_id"]
        if branch["K"] == "DOES_NOT_APPLY":
            branch["projection_visibility"] = "FILTERED_CONTEXT"
            relations[bid] = "OUT_OF_CONTEXT"
            continue
        prediction = branch["predictions"].get(test_id, "UNKNOWN")
        predictions[bid] = deepcopy(prediction)
        relation = derive_relation(
            prediction,
            observation["observed_outcome"],
            exact=bool(test["exact_outcome_discriminator"]),
        )
        relations[bid] = relation
        if relation == "UNKNOWN_RELATION":
            continue
        record = _record(
            observation,
            event_digest=event_digest,
            relation=relation,
            independent_credit=independent_credit,
            target_branch_id=bid,
        )
        if relation == "SUPPORTS":
            branch["E_plus"].append(record)
            if branch["sigma"] != "FALSIFIED":
                branch["sigma"] = "SUPPORTED_UNRESOLVED"
        elif relation == "COUNTERS":
            branch["E_minus"].append(record)
            if branch["sigma"] != "FALSIFIED":
                branch["sigma"] = "WEAKENED_UNRESOLVED"
        elif relation == "FALSIFIES":
            branch["F"].append(record)
            branch["sigma"] = "FALSIFIED"

    resolution = {"status": "UNRESOLVED", "resolved_branch_id": None}
    discriminator_evaluation: Dict[str, Any] | None = None
    live_context_unknown = [
        branch["branch_id"]
        for branch in branches_before
        if branch["K"] == "UNKNOWN" and branch["sigma"] != "FALSIFIED"
    ]
    applicable_before = [branch for branch in branches_before if branch["K"] == "APPLIES"]
    applicable_predictions = {
        branch["branch_id"]: branch["predictions"].get(test_id, "UNKNOWN")
        for branch in applicable_before
    }
    predictions_complete = bool(applicable_before) and all(
        value != "UNKNOWN" and value is not None for value in applicable_predictions.values()
    )
    matching = sorted(
        bid for bid, value in applicable_predictions.items() if value == observation["observed_outcome"]
    )
    can_resolve = (
        bool(test["admissible"])
        and bool(test["exact_outcome_discriminator"])
        and not live_context_unknown
        and predictions_complete
        and len(matching) == 1
    )
    if can_resolve:
        winner = matching[0]
        resolution = {"status": "RESOLVED", "resolved_branch_id": winner}
        for branch in branches_after:
            if branch["branch_id"] == winner:
                branch["sigma"] = "RESOLVED_PASS"
        discriminator_evaluation = {
            "schema": RESOLUTION_RECEIPT_SCHEMA,
            "discriminator_id": test_id,
            "admissible": True,
            "exact_outcome_discriminator": True,
            "observed_outcome_id": event_id,
            "observed_outcome": deepcopy(observation["observed_outcome"]),
            "branch_predictions": deepcopy(applicable_predictions),
            "winner_branch_id": winner,
            "separation_derived": True,
            "self_asserted_winner": False,
        }

    input_digest = _canonical_digest({"state": state, "observation": observation})
    output_digest = _canonical_digest(
        {
            "state_after": out,
            "relations": relations,
            "resolution": resolution,
            "discriminator_evaluation": discriminator_evaluation,
        }
    )
    derivation_receipt = {
        "schema": DERIVATION_RECEIPT_SCHEMA,
        "kind": "VERIFIED_DISCRIMINATOR_OUTCOME" if can_resolve else "EXECUTABLE_TASK_WORLD_RELATION",
        "evaluator_id": "trigger2_synthetic_relation_deriver_v1",
        "input_digest": input_digest,
        "output_digest": output_digest,
        "event_digest": event_digest,
        "self_asserted_label": False,
    }

    return {
        "schema": SCHEMA,
        "status": "DERIVED",
        "state_after": out,
        "relations": relations,
        "independent_credit": independent_credit,
        "resolution": resolution,
        "discriminator_evaluation": discriminator_evaluation,
        "derivation_receipt": derivation_receipt,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "model_runtime_credit_minted": False,
        "jspace_credit_minted": False,
        "hcu_credit_minted": False,
        "entityos_credit_minted": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
    }
