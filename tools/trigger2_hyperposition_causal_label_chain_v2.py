#!/usr/bin/env python3
"""Converged deterministic Hyperposition causal-label chain for Trigger-2.

Formal synthetic world + global event registry -> mechanically derived event/dependence
identity -> branch relations/targets -> current Hyperposition v2 state transition -> task-local
resolution.

The caller cannot supply relation, target, winner, independence-group, payload-key or
correlation-ancestry labels. Those are derived from typed synthetic structures.

SOURCE/CURRICULUM ONLY. No canonical truth/effect/runtime/J-Space/HCU/training credit.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from tools import trigger2_hyperposition_reference_labelers_v2 as lab

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_CAUSAL_LABEL_CHAIN/v2"
WORLD_SCHEMA = "CLAY_TRIGGER2_FORMAL_SYNTHETIC_TASK_WORLD/v2"
EVENT_REGISTRY_SCHEMA = "CLAY_TRIGGER2_FORMAL_SYNTHETIC_EVENT_REGISTRY/v1"
RECEIPT_SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_DERIVATION_RECEIPT/v2"

TEST_MODES = {"EXACT_FOR_SCOPE", "NONDECISIVE_SIGNAL"}
UNKNOWN_OUTCOME = "__UNKNOWN__"
ALLOWED_CONTEXT = {"APPLIES", "DOES_NOT_APPLY", "UNKNOWN"}
FULL_CARRIER_FIELDS = {
    "branch_id", "v", "K", "E_plus", "E_minus", "F", "T", "A", "sigma",
    "projection_visibility",
}
FORBIDDEN_EVENT_LABEL_FIELDS = {
    "relation", "branch_relations", "target_branch_ids", "decision_role",
    "winner_branch_id", "resolved_branch", "resolution", "correlation_ancestry_id",
    "causal_ancestry_id", "independence_group", "independence_qualified", "payload_key",
}


class DerivationError(ValueError):
    pass


def _stable_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_stable_bytes(value)).hexdigest()


def _required(obj: dict[str, Any], fields: tuple[str, ...], where: str) -> None:
    missing = [f for f in fields if f not in obj]
    if missing:
        raise DerivationError(f"{where}: missing {missing}")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise DerivationError("state: object required")
    branches = state.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        raise DerivationError("state: at least two branches required")
    ids: list[str] = []
    for branch in branches:
        if not isinstance(branch, dict):
            raise DerivationError("state.branch: object required")
        if not FULL_CARRIER_FIELDS.issubset(branch):
            raise DerivationError("state.branch: full v/K/E+/E-/F/T/A/sigma carrier required")
        bid = branch.get("branch_id")
        if not _nonempty(bid):
            raise DerivationError("state.branch: branch_id required")
        ids.append(bid)
        if branch.get("K") not in ALLOWED_CONTEXT:
            raise DerivationError(f"state.branch:{bid}: K invalid")
        if not isinstance(branch.get("E_plus"), list) or not isinstance(branch.get("E_minus"), list):
            raise DerivationError(f"state.branch:{bid}: E_plus/E_minus lists required")
        if not isinstance(branch.get("F"), list):
            raise DerivationError(f"state.branch:{bid}: F list required")
    if len(ids) != len(set(ids)):
        raise DerivationError("state: duplicate branch_id")
    return state


def _validate_world(world: Any) -> dict[str, Any]:
    if not isinstance(world, dict) or world.get("schema") != WORLD_SCHEMA:
        raise DerivationError("world: schema mismatch")
    _required(world, ("world_id", "branches", "tests"), "world")
    if not _nonempty(world["world_id"]):
        raise DerivationError("world: world_id required")
    branches = world["branches"]
    tests = world["tests"]
    if not isinstance(branches, list) or len(branches) < 2:
        raise DerivationError("world: at least two branches required")
    if not isinstance(tests, list) or not tests:
        raise DerivationError("world: tests required")

    test_ids: set[str] = set()
    for test in tests:
        if not isinstance(test, dict):
            raise DerivationError("world.test: object required")
        _required(test, ("test_id", "mode", "outcome_domain"), "world.test")
        tid = test["test_id"]
        if not _nonempty(tid) or tid in test_ids:
            raise DerivationError("world.test: unique nonempty test_id required")
        test_ids.add(tid)
        if test["mode"] not in TEST_MODES:
            raise DerivationError(f"world.test:{tid}: mode invalid")
        domain = test["outcome_domain"]
        if not isinstance(domain, list) or len(domain) < 2:
            raise DerivationError(f"world.test:{tid}: outcome_domain >=2 required")
        serialized = [_stable_bytes(x) for x in domain]
        if len(serialized) != len(set(serialized)):
            raise DerivationError(f"world.test:{tid}: outcome_domain duplicates")

    branch_ids: set[str] = set()
    test_by_id = {t["test_id"]: t for t in tests}
    for branch in branches:
        if not isinstance(branch, dict):
            raise DerivationError("world.branch: object required")
        _required(
            branch,
            ("branch_id", "semantic_value", "K", "T", "predicted_outcomes"),
            "world.branch",
        )
        bid = branch["branch_id"]
        if not _nonempty(bid) or bid in branch_ids:
            raise DerivationError("world.branch: unique nonempty branch_id required")
        branch_ids.add(bid)
        if branch["K"] not in ALLOWED_CONTEXT:
            raise DerivationError(f"world.branch:{bid}: K invalid")
        predictions = branch["predicted_outcomes"]
        if not isinstance(predictions, dict):
            raise DerivationError(f"world.branch:{bid}: predicted_outcomes object required")
        if not set(predictions).issubset(test_ids):
            raise DerivationError(f"world.branch:{bid}: unknown test prediction")
        for tid, prediction in predictions.items():
            if prediction not in test_by_id[tid]["outcome_domain"]:
                raise DerivationError(
                    f"world.branch:{bid}: prediction outside outcome domain for {tid}"
                )
    return world


def _root_event_ids(registry: dict[str, Any], event_id: str) -> tuple[str, ...]:
    events = registry["events"]
    visiting: set[str] = set()
    memo: dict[str, tuple[str, ...]] = {}

    def visit(eid: str) -> tuple[str, ...]:
        if eid in memo:
            return memo[eid]
        if eid in visiting:
            raise DerivationError("event_registry: dependency cycle")
        visiting.add(eid)
        parents = events[eid]["depends_on_event_ids"]
        if not parents:
            roots = (eid,)
        else:
            all_roots: set[str] = set()
            for parent in parents:
                all_roots.update(visit(parent))
            roots = tuple(sorted(all_roots))
        visiting.remove(eid)
        memo[eid] = roots
        return roots

    if event_id not in events:
        raise DerivationError("event_registry: unknown event_id")
    return visit(event_id)


def _validate_registry(registry: Any, world: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(registry, dict) or registry.get("schema") != EVENT_REGISTRY_SCHEMA:
        raise DerivationError("event_registry: schema mismatch")
    _required(registry, ("world_id", "events"), "event_registry")
    if registry["world_id"] != world["world_id"]:
        raise DerivationError("event_registry: world_id mismatch")
    events = registry["events"]
    if not isinstance(events, dict) or not events:
        raise DerivationError("event_registry: nonempty events object required")
    tests = {t["test_id"]: t for t in world["tests"]}

    for event_id, event in events.items():
        if not _nonempty(event_id) or not isinstance(event, dict):
            raise DerivationError("event_registry: event id/object invalid")
        forbidden = FORBIDDEN_EVENT_LABEL_FIELDS & set(event)
        if forbidden:
            raise DerivationError(
                f"event:{event_id}: asserted label/identity fields forbidden:{sorted(forbidden)}"
            )
        _required(
            event,
            ("test_id", "observed_outcome", "source_id", "depends_on_event_ids"),
            f"event:{event_id}",
        )
        if event["test_id"] not in tests:
            raise DerivationError(f"event:{event_id}: unknown test_id")
        if event["observed_outcome"] not in tests[event["test_id"]]["outcome_domain"]:
            raise DerivationError(f"event:{event_id}: observed_outcome outside domain")
        if not _nonempty(event["source_id"]):
            raise DerivationError(f"event:{event_id}: source_id required")
        parents = event["depends_on_event_ids"]
        if not isinstance(parents, list) or any(not _nonempty(x) for x in parents):
            raise DerivationError(f"event:{event_id}: dependency ids invalid")
        if event_id in parents:
            raise DerivationError(f"event:{event_id}: self dependency forbidden")
        unknown = set(parents) - set(events)
        if unknown:
            raise DerivationError(f"event:{event_id}: unknown dependency parents {sorted(unknown)}")

    for event_id in events:
        _root_event_ids(registry, event_id)
    return registry


def _derive_event_identity(
    world: dict[str, Any], registry: dict[str, Any], event_id: str
) -> dict[str, Any]:
    event = registry["events"][event_id]
    roots = _root_event_ids(registry, event_id)
    root_payloads = [
        {
            "event_id": rid,
            "test_id": registry["events"][rid]["test_id"],
            "observed_outcome": registry["events"][rid]["observed_outcome"],
            "source_id": registry["events"][rid]["source_id"],
        }
        for rid in roots
    ]
    ancestry_material = {"world_id": world["world_id"], "root_event_ids": list(roots)}
    payload_material = {"world_id": world["world_id"], "root_payloads": root_payloads}
    ancestry = "SYNTHETIC_DEPENDENCE:" + _digest(ancestry_material)[:32]
    payload_key = "SYNTHETIC_ROOT_PAYLOAD:" + _digest(payload_material)[:32]
    return {
        "evidence_event_id": event_id,
        "correlation_ancestry_id": ancestry,
        "independence_group": ancestry,
        "payload_key": payload_key,
        "independence_qualified": not bool(event["depends_on_event_ids"]),
        "root_event_ids": list(roots),
        "causal_source_id": event["source_id"],
        "provenance": f"synthetic:{world['world_id']}:event:{event_id}:source:{event['source_id']}",
    }


def _validate_alignment(state: dict[str, Any], world: dict[str, Any]) -> None:
    state_by_id = {b["branch_id"]: b for b in state["branches"]}
    world_by_id = {b["branch_id"]: b for b in world["branches"]}
    if set(state_by_id) != set(world_by_id):
        raise DerivationError("state/world branch ids mismatch")
    for bid in sorted(state_by_id):
        sb, wb = state_by_id[bid], world_by_id[bid]
        if str(sb["v"]) != str(wb["semantic_value"]):
            raise DerivationError(f"state/world semantic value mismatch for {bid}")
        if sb["K"] != wb["K"]:
            raise DerivationError(f"state/world K mismatch for {bid}")
        if sb["T"] != wb["T"]:
            raise DerivationError(f"state/world T mismatch for {bid}")


def _derive_relations(
    world: dict[str, Any], registry: dict[str, Any], event_id: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    event = registry["events"][event_id]
    tests = {t["test_id"]: t for t in world["tests"]}
    test = tests[event["test_id"]]
    observed = event["observed_outcome"]
    rows: list[dict[str, Any]] = []

    for branch in world["branches"]:
        bid = branch["branch_id"]
        if branch["K"] == "DOES_NOT_APPLY":
            relation, predicted = "IRRELEVANT", None
        elif branch["K"] == "UNKNOWN":
            relation, predicted = "UNKNOWN_RELATION", None
        else:
            predicted = branch["predicted_outcomes"].get(event["test_id"], UNKNOWN_OUTCOME)
            if predicted == UNKNOWN_OUTCOME:
                relation = "UNKNOWN_RELATION"
            elif predicted == observed:
                relation = "SUPPORTS"
            elif test["mode"] == "EXACT_FOR_SCOPE":
                relation = "FALSIFIES"
            else:
                relation = "COUNTERS"
        rows.append(
            {
                "branch_id": bid,
                "predicted_outcome": predicted,
                "observed_outcome": observed,
                "relation": relation,
            }
        )
    rows.sort(key=lambda row: row["branch_id"])
    return rows, test


def _labeler_observations(
    relation_rows: list[dict[str, Any]], identity: dict[str, Any]
) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for row in relation_rows:
        if row["relation"] in {"SUPPORTS", "COUNTERS", "FALSIFIES"}:
            grouped.setdefault(row["relation"], []).append(row["branch_id"])
    out: list[dict[str, Any]] = []
    for relation in sorted(grouped):
        out.append(
            {
                "evidence_event_id": identity["evidence_event_id"],
                "correlation_ancestry_id": identity["correlation_ancestry_id"],
                "independence_group": identity["independence_group"],
                "payload_key": identity["payload_key"],
                "provenance": identity["provenance"],
                "relation": relation,
                "target_branch_ids": sorted(grouped[relation]),
                "independence_qualified": identity["independence_qualified"],
                "derived_by": SCHEMA,
            }
        )
    return out


def _canonical_state_for_hash(state: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(state)
    out["branches"] = sorted(out.get("branches", []), key=lambda b: b["branch_id"])
    return out


def derive_label_chain(
    state_before: Any, world: Any, event_registry: Any, event_id: str
) -> dict[str, Any]:
    """Derive and apply one synthetic event through the current Hyperposition v2 labeler."""
    state_before = _validate_state(deepcopy(state_before))
    world = _validate_world(deepcopy(world))
    event_registry = _validate_registry(deepcopy(event_registry), world)
    if event_id not in event_registry["events"]:
        raise DerivationError("event_registry: unknown event_id")
    _validate_alignment(state_before, world)

    relation_rows, test = _derive_relations(world, event_registry, event_id)
    identity = _derive_event_identity(world, event_registry, event_id)
    observations = _labeler_observations(relation_rows, identity)

    state_after = deepcopy(state_before)
    for observation in observations:
        state_after = lab.u_state(state_after, observation)
    resolution = lab.d_resolve(state_after)
    state_resolved = lab.apply_resolution(state_after, resolution)

    receipt_core = {
        "schema": RECEIPT_SCHEMA,
        "world_id": world["world_id"],
        "event_id": event_id,
        "test_id": event_registry["events"][event_id]["test_id"],
        "test_mode": test["mode"],
        "event_identity": identity,
        "branch_relations": relation_rows,
        "derived_labeler_observations": observations,
        "resolution": resolution,
        "world_sha256": _digest(world),
        "event_registry_sha256": _digest(event_registry),
        "state_before_sha256": _digest(_canonical_state_for_hash(state_before)),
        "state_after_sha256": _digest(_canonical_state_for_hash(state_after)),
        "state_resolved_sha256": _digest(_canonical_state_for_hash(state_resolved)),
        "reference_labeler_schema": lab.SCHEMA,
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
    }
    receipt = {**receipt_core, "semantic_receipt_sha256": _digest(receipt_core)}
    return {
        "schema": SCHEMA,
        "state_after": state_after,
        "resolution": resolution,
        "state_resolved": state_resolved,
        "derivation_receipt": receipt,
        "source_design_only": True,
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
    }
