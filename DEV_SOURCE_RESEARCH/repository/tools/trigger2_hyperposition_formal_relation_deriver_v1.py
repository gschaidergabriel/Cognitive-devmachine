#!/usr/bin/env python3
"""Deterministic formal-world relation derivation for Trigger-2 Hyperposition.

This is an upstream label primitive for the current
trigger2_hyperposition_reference_labelers_v1 lane. It converts a formal synthetic
world plus an observed test outcome into branch_relations, evidence decision_role,
resolve context, and discriminator separation metadata.

It is evaluator/generator-side only. None of the formal-world metadata may be
rendered as a model-visible shortcut. It cannot mint canonical truth or runtime/
training credit.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_FORMAL_RELATION_DERIVER/v1"
WORLD_SCHEMA = "XENO_HYPERPOSITION_FORMAL_WORLD/v1"
TEST_SCHEMA = "XENO_HYPERPOSITION_FORMAL_TEST/v1"
BRANCH_SCHEMA = "XENO_HYPERPOSITION_BRANCH/v1"
OBS_SCHEMA = "XENO_HYPERPOSITION_OBSERVATION/v1"
DISCRIMINATOR_SCHEMA = "XENO_HYPERPOSITION_DISCRIMINATOR/v1"
RESOLUTION_SCOPE = "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"


class DerivationError(ValueError):
    pass


def _canonical_hash(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _require_dict(x: Any, name: str) -> dict[str, Any]:
    if not isinstance(x, dict):
        raise DerivationError(f"{name}: object required")
    return x


def _validate_branch_set(branches: Any) -> list[dict[str, Any]]:
    if not isinstance(branches, list) or len(branches) < 2:
        raise DerivationError("branch_set: at least two branches required")
    seen = set()
    for b in branches:
        _require_dict(b, "branch")
        if b.get("schema") != BRANCH_SCHEMA:
            raise DerivationError("branch: schema mismatch")
        bid = b.get("branch_id")
        if not isinstance(bid, str) or not bid or bid in seen:
            raise DerivationError("branch: invalid/duplicate branch_id")
        seen.add(bid)
    return branches


def _validate_world(world: Any, branches: list[dict[str, Any]]) -> dict[str, Any]:
    world = _require_dict(world, "world")
    if world.get("schema") != WORLD_SCHEMA:
        raise DerivationError("world: schema mismatch")
    if world.get("canonical_truth_allowed") is not False:
        raise DerivationError("world: canonical_truth_allowed must be false")
    if world.get("direct_effect_authority") is not False:
        raise DerivationError("world: direct_effect_authority must be false")
    if world.get("model_visible") is not False:
        raise DerivationError("world: must be evaluator-only")
    tests = world.get("tests")
    if not isinstance(tests, list) or not tests:
        raise DerivationError("world: tests required")
    by_test = {}
    branch_ids = {b["branch_id"] for b in branches}
    for t in tests:
        _require_dict(t, "test")
        if t.get("schema") != TEST_SCHEMA:
            raise DerivationError("test: schema mismatch")
        tid = t.get("test_id")
        if not isinstance(tid, str) or not tid or tid in by_test:
            raise DerivationError("test: invalid/duplicate test_id")
        preds = t.get("predicted_outcome_by_branch")
        if not isinstance(preds, dict) or set(preds) != branch_ids:
            raise DerivationError("test: predicted_outcome_by_branch must cover exact branch set")
        if any(not isinstance(v, str) or not v for v in preds.values()):
            raise DerivationError("test: predicted outcomes must be nonempty strings")
        if not isinstance(t.get("independence_group"), str) or not t["independence_group"]:
            raise DerivationError("test: independence_group required")
        if not isinstance(t.get("cost_units"), int) or t["cost_units"] < 0:
            raise DerivationError("test: cost_units must be nonnegative int")
        if not isinstance(t.get("admissible"), bool) or not isinstance(t.get("observable"), bool):
            raise DerivationError("test: admissible/observable booleans required")
        if t.get("deterministic_total") is not True:
            raise DerivationError("test: v1 only supports deterministic_total=true")
        by_test[tid] = t
    return world


def _test(world: dict[str, Any], test_id: str) -> dict[str, Any]:
    for t in world["tests"]:
        if t["test_id"] == test_id:
            return t
    raise DerivationError("unknown test_id")


def derive_outcome(
    branch_set: Any,
    world: Any,
    *,
    test_id: str,
    observed_outcome: str,
    evidence_id: str,
) -> dict[str, Any]:
    """Mechanically derive relations/decision role/context from formal predictions."""
    branches = _validate_branch_set(branch_set)
    world = _validate_world(world, branches)
    test = _test(world, test_id)
    if not isinstance(observed_outcome, str) or not observed_outcome:
        raise DerivationError("observed_outcome required")
    if not isinstance(evidence_id, str) or not evidence_id:
        raise DerivationError("evidence_id required")

    predictions = test["predicted_outcome_by_branch"]
    matching = sorted(bid for bid, pred in predictions.items() if pred == observed_outcome)
    branch_relations: dict[str, str] = {}
    for bid, pred in predictions.items():
        branch_relations[bid] = "SUPPORT" if pred == observed_outcome else "FALSIFY"

    executed_and_admissible = bool(test["admissible"] and test["observable"])
    if executed_and_admissible and len(matching) == 1:
        decision_role = "DECISIVE_SUPPORT"
    elif executed_and_admissible and len(matching) == 0:
        decision_role = "DECISIVE_CONTRADICTION"
    else:
        decision_role = "NONDECISIVE"

    world_sha = _canonical_hash(world)
    evidence = {
        "evidence_id": evidence_id,
        "provenance_ancestry_id": f"formal-world:{world_sha}:test:{test_id}",
        "independence_group": test["independence_group"],
        "decision_role": decision_role,
    }
    observation = {
        "schema": OBS_SCHEMA,
        "evidence": evidence,
        "branch_relations": branch_relations,
    }
    resolve_context = {
        "context_id": f"{world.get('world_id','world')}:{test_id}:{evidence_id}",
        "discriminator_executed": True,
        "discriminator_admissible": bool(test["admissible"]),
        "resolution_scope": RESOLUTION_SCOPE,
        "all_other_branches_explicitly_falsified": bool(executed_and_admissible and len(matching) == 1),
    }
    receipt_core = {
        "schema": SCHEMA,
        "formal_world_sha256": world_sha,
        "test_id": test_id,
        "observed_outcome": observed_outcome,
        "matching_branch_ids": matching,
        "observation": observation,
        "resolve_context": resolve_context,
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
        "training_credit_minted": False,
        "model_visible": False,
    }
    receipt = dict(receipt_core)
    receipt["derivation_sha256"] = _canonical_hash(receipt_core)
    return receipt


def derive_discriminator_metadata(
    branch_set: Any,
    world: Any,
    *,
    seen_independence_groups: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Derive pair separation and independence novelty from predicted outcomes."""
    branches = _validate_branch_set(branch_set)
    world = _validate_world(world, branches)
    seen_groups = seen_independence_groups or set()
    out = []
    ids = sorted(b["branch_id"] for b in branches if b.get("validity") == "LIVE")
    for t in world["tests"]:
        preds = t["predicted_outcome_by_branch"]
        pairs = []
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                if preds[a] != preds[b]:
                    pairs.append([a, b])
        out.append({
            "schema": DISCRIMINATOR_SCHEMA,
            "test_id": t["test_id"],
            "admissible": t["admissible"],
            "observable": t["observable"],
            "separates_branch_pairs": pairs,
            "novel_independence_groups": 0 if t["independence_group"] in seen_groups else 1,
            "cost_units": t["cost_units"],
            "derivation_rule": "PAIR_SEPARATED_IFF_PREDICTED_OUTCOMES_DIFFER",
            "formal_world_sha256": _canonical_hash(world),
            "model_visible": False,
        })
    return out
