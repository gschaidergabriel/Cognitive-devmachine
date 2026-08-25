#!/usr/bin/env python3
"""Deterministic synthetic-world relation oracle for Trigger-2 Hyperposition training.

This module closes the upstream label-source gap in the Hyperposition D/E pipeline.
Model/generator-visible examples must not supply branch relations, target branch IDs,
decision roles, winners, or resolved branches as trusted labels. Instead a formal
synthetic world specifies branch predictions and observed test outcomes; this oracle
mechanically derives the typed branch-local observations consumed by the downstream
Hyperposition reference labeler.

SOURCE/CURRICULUM UTILITY ONLY. It cannot mint canonical truth, direct effect authority,
runtime/J-Space/HCU credit, accepted dataset tokens, or training credit.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_HYPERPOSITION_ORACLE/v1"
WORLD_SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_HYPERPOSITION_WORLD/v1"
DERIVATION_SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_HYPERPOSITION_DERIVATION/v1"

FORBIDDEN_PRELABELED_FIELDS = {
    "relation",
    "branch_relations",
    "target_branch_ids",
    "decision_role",
    "winner_branch_id",
    "resolved_branch",
    "resolution",
}
TEST_KIND_MISMATCH_RELATION = {
    "FINITE_OUTCOME_EQUALITY": "FALSIFIES",
    "FINITE_OUTCOME_NOISY_SIGNAL": "COUNTERS",
}
UNKNOWN = "UNKNOWN"


class OracleError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _required(obj: dict[str, Any], keys: tuple[str, ...], where: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise OracleError(f"{where}: missing {missing}")


def _reject_prelabels(obj: Any, where: str) -> None:
    if not isinstance(obj, dict):
        return
    overlap = sorted(FORBIDDEN_PRELABELED_FIELDS & set(obj))
    if overlap:
        raise OracleError(f"{where}: pre-labeled fields forbidden: {overlap}")


def validate_world(world: Any) -> None:
    if not isinstance(world, dict) or world.get("schema") != WORLD_SCHEMA:
        raise OracleError("world: schema mismatch")
    _required(world, ("world_id", "tests", "branch_predictions", "events"), "world")
    if not isinstance(world["world_id"], str) or not world["world_id"]:
        raise OracleError("world: world_id required")
    if not isinstance(world["tests"], dict) or not world["tests"]:
        raise OracleError("world: tests must be nonempty object")
    if not isinstance(world["branch_predictions"], dict) or len(world["branch_predictions"]) < 2:
        raise OracleError("world: at least two branch prediction maps required")
    if not isinstance(world["events"], dict) or not world["events"]:
        raise OracleError("world: events must be nonempty object")

    _reject_prelabels(world, "world")
    for tid, test in world["tests"].items():
        if not isinstance(test, dict):
            raise OracleError(f"test:{tid}: object required")
        _reject_prelabels(test, f"test:{tid}")
        _required(test, ("kind",), f"test:{tid}")
        if test["kind"] not in TEST_KIND_MISMATCH_RELATION:
            raise OracleError(f"test:{tid}: unsupported test kind")

    test_ids = set(world["tests"])
    for bid, predictions in world["branch_predictions"].items():
        if not isinstance(bid, str) or not bid:
            raise OracleError("world: branch id invalid")
        if not isinstance(predictions, dict):
            raise OracleError(f"branch:{bid}: predictions object required")
        _reject_prelabels(predictions, f"branch:{bid}")
        if set(predictions) != test_ids:
            raise OracleError(f"branch:{bid}: predictions must cover exactly all tests")

    for eid, event in world["events"].items():
        if not isinstance(event, dict):
            raise OracleError(f"event:{eid}: object required")
        _reject_prelabels(event, f"event:{eid}")
        _required(
            event,
            (
                "test_id",
                "observed_outcome",
                "source_id",
                "depends_on_event_ids",
                "provenance",
            ),
            f"event:{eid}",
        )
        if event["test_id"] not in world["tests"]:
            raise OracleError(f"event:{eid}: unknown test_id")
        if not isinstance(event["source_id"], str) or not event["source_id"]:
            raise OracleError(f"event:{eid}: source_id required")
        if not isinstance(event["depends_on_event_ids"], list):
            raise OracleError(f"event:{eid}: depends_on_event_ids list required")
        if eid in event["depends_on_event_ids"]:
            raise OracleError(f"event:{eid}: self dependency forbidden")
        unknown_parents = set(event["depends_on_event_ids"]) - set(world["events"])
        if unknown_parents:
            raise OracleError(f"event:{eid}: unknown dependency parents {sorted(unknown_parents)}")


def _root_events(world: dict[str, Any], event_id: str) -> tuple[str, ...]:
    visiting: set[str] = set()
    memo: dict[str, tuple[str, ...]] = {}

    def visit(eid: str) -> tuple[str, ...]:
        if eid in memo:
            return memo[eid]
        if eid in visiting:
            raise OracleError("world: event dependency cycle")
        visiting.add(eid)
        parents = world["events"][eid]["depends_on_event_ids"]
        if not parents:
            roots = (eid,)
        else:
            acc: set[str] = set()
            for parent in parents:
                acc.update(visit(parent))
            roots = tuple(sorted(acc))
        visiting.remove(eid)
        memo[eid] = roots
        return roots

    return visit(event_id)


def _ancestry_id(world_id: str, roots: tuple[str, ...]) -> str:
    material = {"world_id": world_id, "root_event_ids": list(roots)}
    return "syn-anc-" + sha256_json(material)[:24]


def _independence_group(world_id: str, source_id: str, roots: tuple[str, ...]) -> str:
    material = {
        "world_id": world_id,
        "source_id": source_id,
        "root_event_ids": list(roots),
    }
    return "syn-ind-" + sha256_json(material)[:24]


def derive_observations(world: Any, event_id: str) -> dict[str, Any]:
    """Mechanically derive branch-local relations from predictions vs observed outcome.

    No caller-supplied relation/target/winner is accepted. The returned observations
    can be fed sequentially into `trigger2_hyperposition_reference_labelers_v2.u_state`.
    """
    validate_world(world)
    if event_id not in world["events"]:
        raise OracleError("event: unknown event_id")

    event = world["events"][event_id]
    test_id = event["test_id"]
    test = world["tests"][test_id]
    observed = event["observed_outcome"]
    roots = _root_events(world, event_id)
    ancestry = _ancestry_id(world["world_id"], roots)
    independent = len(event["depends_on_event_ids"]) == 0
    independence_group = _independence_group(
        world["world_id"], event["source_id"], roots
    )

    grouped: dict[str, list[str]] = {}
    per_branch: dict[str, str] = {}
    for branch_id in sorted(world["branch_predictions"]):
        predicted = world["branch_predictions"][branch_id][test_id]
        if predicted == UNKNOWN:
            relation = "UNKNOWN_RELATION"
        elif predicted == observed:
            relation = "SUPPORTS"
        else:
            relation = TEST_KIND_MISMATCH_RELATION[test["kind"]]
        grouped.setdefault(relation, []).append(branch_id)
        per_branch[branch_id] = relation

    observations: list[dict[str, Any]] = []
    for relation in sorted(grouped):
        observations.append(
            {
                "evidence_event_id": event_id,
                "correlation_ancestry_id": ancestry,
                "independence_group": independence_group,
                "provenance": event["provenance"],
                "relation": relation,
                "target_branch_ids": grouped[relation],
                "independence_qualified": independent,
                "oracle_schema": SCHEMA,
                "oracle_world_id": world["world_id"],
                "oracle_test_id": test_id,
            }
        )

    basis = {
        "world_id": world["world_id"],
        "event_id": event_id,
        "test_id": test_id,
        "observed_outcome": observed,
        "root_event_ids": list(roots),
        "per_branch_relation": per_branch,
    }
    result = {
        "schema": DERIVATION_SCHEMA,
        "oracle_schema": SCHEMA,
        "world_id": world["world_id"],
        "event_id": event_id,
        "world_sha256": sha256_json(world),
        "event_sha256": sha256_json(event),
        "derivation_basis_sha256": sha256_json(basis),
        "derived_observations": observations,
        "derived_observations_sha256": sha256_json(observations),
        "model_visible_fields": [],
        "evaluator_only": True,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
    }
    return result


def apply_event(state: dict[str, Any], world: Any, event_id: str) -> dict[str, Any]:
    """Apply oracle-derived observations through the current Hyperposition v2 labeler."""
    from tools.trigger2_hyperposition_reference_labelers_v2 import d_resolve, u_state

    derivation = derive_observations(world, event_id)
    after = deepcopy(state)
    for observation in derivation["derived_observations"]:
        after = u_state(after, observation)
    resolution = d_resolve(after)
    return {
        "schema": SCHEMA,
        "world_id": derivation["world_id"],
        "event_id": event_id,
        "state_after": after,
        "resolution": resolution,
        "derivation_receipt": derivation,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
    }
