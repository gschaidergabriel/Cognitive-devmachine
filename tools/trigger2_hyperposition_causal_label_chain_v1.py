#!/usr/bin/env python3
"""Deterministic causal derivation chain for Trigger-2 Hyperposition training labels.

Formal synthetic task-world predictions + an observed synthetic test outcome are converted
mechanically into branch relations, evidence decision role, discriminator coverage and the
resolve context consumed by the existing Hyperposition reference labeler.

The model never supplies these labels. Free text is never parsed to derive them.
SOURCE-DESIGN ONLY: no canonical truth/effect/runtime/J-Space/training credit is minted.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from itertools import combinations
from typing import Any

from tools import trigger2_hyperposition_reference_labelers_v1 as lab

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_CAUSAL_LABEL_CHAIN/v1"
WORLD_SCHEMA = "CLAY_TRIGGER2_FORMAL_SYNTHETIC_TASK_WORLD/v1"
EVENT_SCHEMA = "CLAY_TRIGGER2_FORMAL_SYNTHETIC_TEST_EVENT/v1"
RECEIPT_SCHEMA = "CLAY_TRIGGER2_RELATION_DERIVATION_RECEIPT/v1"

TEST_MODES = {"EXACT_FOR_SCOPE", "NONDECISIVE_SIGNAL"}
UNKNOWN_OUTCOME = "__UNKNOWN__"
RESOLUTION_SCOPE = "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"


class DerivationError(ValueError):
    pass


def _required(obj: dict[str, Any], keys: tuple[str, ...], where: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise DerivationError(f"{where}: missing {missing}")


def _stable_sha(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_world(world: dict[str, Any]) -> None:
    _required(world, ("schema", "world_id", "branches", "tests"), "world")
    if world["schema"] != WORLD_SCHEMA:
        raise DerivationError("world: schema mismatch")
    if not isinstance(world["world_id"], str) or not world["world_id"]:
        raise DerivationError("world: world_id required")
    branches, tests = world["branches"], world["tests"]
    if not isinstance(branches, list) or len(branches) < 2:
        raise DerivationError("world: at least two branches required")
    if not isinstance(tests, list) or not tests:
        raise DerivationError("world: tests required")
    branch_ids: set[str] = set()
    for b in branches:
        _required(b, ("branch_id", "semantic_value", "predicted_outcomes"), "world.branch")
        if b["branch_id"] in branch_ids:
            raise DerivationError("world: duplicate branch_id")
        branch_ids.add(b["branch_id"])
        if not isinstance(b["predicted_outcomes"], dict):
            raise DerivationError("world.branch: predicted_outcomes must be object")
    test_ids: set[str] = set()
    for t in tests:
        _required(t, ("test_id", "mode", "admissible", "outcome_domain"), "world.test")
        if t["test_id"] in test_ids:
            raise DerivationError("world: duplicate test_id")
        test_ids.add(t["test_id"])
        if t["mode"] not in TEST_MODES:
            raise DerivationError("world.test: invalid mode")
        if not isinstance(t["admissible"], bool):
            raise DerivationError("world.test: admissible must be bool")
        domain = t["outcome_domain"]
        if not isinstance(domain, list) or len(domain) < 2 or len(set(map(str, domain))) != len(domain):
            raise DerivationError("world.test: outcome_domain requires >=2 unique outcomes")
    for b in branches:
        unknown = set(b["predicted_outcomes"]) - test_ids
        if unknown:
            raise DerivationError(f"world.branch: unknown test ids {sorted(unknown)}")


def _validate_event(event: dict[str, Any], world: dict[str, Any]) -> dict[str, Any]:
    _required(event, (
        "schema", "event_id", "world_id", "test_id", "execution_status",
        "observed_outcome", "causal_source_id", "independence_group", "payload_key",
    ), "event")
    if event["schema"] != EVENT_SCHEMA:
        raise DerivationError("event: schema mismatch")
    if event["world_id"] != world["world_id"]:
        raise DerivationError("event: world_id mismatch")
    if event["execution_status"] != "EXECUTED_SYNTHETIC":
        raise DerivationError("event: only EXECUTED_SYNTHETIC is accepted")
    tests = {t["test_id"]: t for t in world["tests"]}
    if event["test_id"] not in tests:
        raise DerivationError("event: unknown test_id")
    test = tests[event["test_id"]]
    if event["observed_outcome"] not in test["outcome_domain"]:
        raise DerivationError("event: observed_outcome outside declared domain")
    for key in ("event_id", "causal_source_id", "independence_group", "payload_key"):
        if not isinstance(event[key], str) or not event[key]:
            raise DerivationError(f"event: {key} must be nonempty string")
    return test


def _branch_predictions(world: dict[str, Any], test_id: str) -> dict[str, str]:
    return {
        b["branch_id"]: str(b["predicted_outcomes"].get(test_id, UNKNOWN_OUTCOME))
        for b in world["branches"]
    }


def _separated_pairs(predictions: dict[str, str]) -> list[list[str]]:
    pairs: list[list[str]] = []
    for a, b in combinations(sorted(predictions), 2):
        oa, ob = predictions[a], predictions[b]
        if oa != UNKNOWN_OUTCOME and ob != UNKNOWN_OUTCOME and oa != ob:
            pairs.append([a, b])
    return pairs


def _canonical_evidence(event: dict[str, Any], decision_role: str) -> dict[str, Any]:
    semantic_key = {
        "independence_group": event["independence_group"],
        "payload_key": event["payload_key"],
    }
    eid = "SEMANTIC_EVIDENCE:" + _stable_sha(semantic_key)[:24]
    return {
        "evidence_id": eid,
        "provenance_ancestry_id": "DEPENDENCE_GROUP:" + event["independence_group"],
        "independence_group": event["independence_group"],
        "decision_role": decision_role,
        "payload_key": event["payload_key"],
        "source_event_id": event["event_id"],
        "raw_causal_source_id": event["causal_source_id"],
    }


def derive_relation_receipt(world: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Derive decisive label inputs from formal task-world semantics, never free text."""
    _validate_world(world)
    test = _validate_event(event, world)
    predictions = _branch_predictions(world, event["test_id"])
    observed, mode = str(event["observed_outcome"]), test["mode"]
    matching = sorted(bid for bid, pred in predictions.items() if pred == observed)
    known = sorted(bid for bid, pred in predictions.items() if pred != UNKNOWN_OUTCOME)
    complete = len(known) == len(predictions)
    decisive = mode == "EXACT_FOR_SCOPE" and test["admissible"] is True and complete and len(matching) == 1

    relations: dict[str, str] = {}
    for bid, pred in predictions.items():
        if pred == UNKNOWN_OUTCOME:
            relations[bid] = "NO_EFFECT"
        elif pred == observed:
            relations[bid] = "SUPPORT"
        elif mode == "EXACT_FOR_SCOPE":
            relations[bid] = "FALSIFY"
        else:
            relations[bid] = "COUNTER"

    if decisive:
        role = "DECISIVE_SUPPORT"
    elif mode == "EXACT_FOR_SCOPE" and not matching and complete:
        role = "DECISIVE_CONTRADICTION"
    else:
        role = "NONDECISIVE"

    winner = matching[0] if decisive else None
    all_other_falsified = bool(
        winner is not None and all(relations[bid] == "FALSIFY" for bid in relations if bid != winner)
    )
    canonical_evidence = _canonical_evidence(event, role)
    semantic_receipt = {
        "schema": RECEIPT_SCHEMA,
        "world_id": world["world_id"],
        "test_id": event["test_id"],
        "test_mode": mode,
        "test_admissible": test["admissible"],
        "observed_outcome": observed,
        "predicted_outcomes": predictions,
        "branch_relations": relations,
        "decision_role": role,
        "winner_branch_id": winner,
        "complete_prediction_coverage": complete,
        "separated_branch_pairs": _separated_pairs(predictions),
        "all_other_branches_explicitly_falsified": all_other_falsified,
        "canonical_evidence_identity": {
            "evidence_id": canonical_evidence["evidence_id"],
            "provenance_ancestry_id": canonical_evidence["provenance_ancestry_id"],
            "independence_group": canonical_evidence["independence_group"],
            "payload_key": canonical_evidence["payload_key"],
        },
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
    }
    semantic_receipt["semantic_receipt_sha256"] = _stable_sha(semantic_receipt)
    return {
        **semantic_receipt,
        "source_event_id": event["event_id"],
        "raw_causal_source_id": event["causal_source_id"],
        "canonical_evidence": canonical_evidence,
    }


def _validate_branch_alignment(branch_set: list[dict[str, Any]], world: dict[str, Any]) -> None:
    lab.validate_branch_set(branch_set)
    w = {b["branch_id"]: b for b in world["branches"]}
    s = {b["branch_id"]: b for b in branch_set}
    if set(w) != set(s):
        raise DerivationError("branch_set/world branch ids mismatch")
    for bid in sorted(w):
        if str(s[bid]["v_semantic_value"]) != str(w[bid]["semantic_value"]):
            raise DerivationError(f"branch_set/world semantic mismatch for {bid}")


def derive_label_chain(branch_set: list[dict[str, Any]], world: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Return exact relation derivation plus existing reference-labeler transition."""
    _validate_world(world)
    _validate_branch_alignment(branch_set, world)
    receipt = derive_relation_receipt(world, event)
    observation = {
        "schema": lab.OBS_SCHEMA,
        "evidence": deepcopy(receipt["canonical_evidence"]),
        "branch_relations": deepcopy(receipt["branch_relations"]),
    }
    resolve_context = {
        "context_id": f"{world['world_id']}:{event['event_id']}",
        "discriminator_executed": event["execution_status"] == "EXECUTED_SYNTHETIC",
        "discriminator_admissible": bool(receipt["test_admissible"]),
        "resolution_scope": RESOLUTION_SCOPE,
        "all_other_branches_explicitly_falsified": bool(receipt["all_other_branches_explicitly_falsified"]),
        "derivation_receipt_sha256": receipt["semantic_receipt_sha256"],
    }
    target = lab.label_transition(branch_set, observation, resolve_context)
    return {
        "schema": SCHEMA,
        "world_schema": WORLD_SCHEMA,
        "event_schema": EVENT_SCHEMA,
        "relation_derivation_receipt": receipt,
        "derived_labeler_observation": observation,
        "derived_resolve_context": resolve_context,
        "reference_labeler_schema": lab.SCHEMA,
        "reference_target": target,
        "source_design_only": True,
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
    }


def discriminator_metadata(world: dict[str, Any], prior_evidence_keys: set[tuple[str, str]] | None = None) -> list[dict[str, Any]]:
    """Derive pair separation from predicted outcomes; never accept claimed separation counts."""
    _validate_world(world)
    prior = prior_evidence_keys or set()
    rows: list[dict[str, Any]] = []
    for test in world["tests"]:
        preds = _branch_predictions(world, test["test_id"])
        payload_key = str(test.get("payload_key", f"TEST:{test['test_id']}"))
        group = str(test.get("independence_group", f"TEST_GROUP:{test['test_id']}"))
        rows.append({
            "schema": lab.TEST_SCHEMA,
            "test_id": test["test_id"],
            "admissible": bool(test["admissible"]),
            "observable": True,
            "separates_branch_pairs": _separated_pairs(preds),
            "novel_independence_groups": int((group, payload_key) not in prior),
            "cost_units": float(test.get("cost_units", 1.0)),
            "derived_predictions": preds,
            "derivation_rule": "PAIR_SEPARATION_FROM_FORMAL_PREDICTED_OUTCOMES",
        })
    return rows
