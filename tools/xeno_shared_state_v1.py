#!/usr/bin/env python3
"""Deterministic Xeno/HCU S1 boundary primitives.

This module is NOT a durable truth store. It validates and binds a caller-supplied S1
(shared cognitive workspace) snapshot, lets a Xeno autonomously select useful work from
that snapshot, emits typed NODE_RESULT/v1 packets, deterministically leases a coordinator,
and authorizes only lease-scoped CAS S1 candidate writes. It never writes S0 and never
creates truth/effect/security authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence

S1_SCHEMA = "XENO_S1_SNAPSHOT/v1"
BOOT_SCHEMA = "XENO_AUTONOMOUS_BOOT_PLAN/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v1"
WRITE_AUTH_SCHEMA = "XENO_S1_WRITE_AUTHORIZATION/v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class XenoSharedStateError(ValueError):
    pass


def _need(ok: bool, code: str) -> None:
    if not ok:
        raise XenoSharedStateError(code)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _text(value: Any, code: str) -> str:
    _need(type(value) is str and bool(value.strip()), code)
    return value.strip()


def _digest(value: Any, code: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, code)
    return value


def _strings(value: Any, code: str) -> set[str]:
    _need(isinstance(value, list), code)
    values = [_text(v, code) for v in value]
    _need(len(values) == len(set(values)), code + "_DUPLICATE")
    return set(values)


def _without(obj: Mapping[str, Any], key: str) -> dict[str, Any]:
    return {k: v for k, v in dict(obj).items() if k != key}


def build_snapshot(*, epoch: int, generation: int, scope: str,
                   tasks: list[dict[str, Any]], claims: list[dict[str, Any]] | None = None,
                   hyperposition_branches: list[dict[str, Any]] | None = None,
                   gwt_broadcasts: list[dict[str, Any]] | None = None,
                   provenance_refs: list[str]) -> dict[str, Any]:
    material = {
        "schema": S1_SCHEMA,
        "epoch": epoch,
        "generation": generation,
        "scope": scope,
        "tasks": tasks,
        "claims": claims or [],
        "hyperposition_branches": hyperposition_branches or [],
        "gwt_broadcasts": gwt_broadcasts or [],
        "provenance_refs": provenance_refs,
    }
    value = {**material, "state_digest": sha256_obj(material)}
    return validate_snapshot(value)


def validate_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    _need(isinstance(snapshot, Mapping), "S1_OBJECT_REQUIRED")
    obj = dict(snapshot)
    _need(obj.get("schema") == S1_SCHEMA, "S1_SCHEMA_MISMATCH")
    _need(type(obj.get("epoch")) is int and obj["epoch"] >= 0, "S1_EPOCH_INVALID")
    _need(type(obj.get("generation")) is int and obj["generation"] >= 0, "S1_GENERATION_INVALID")
    _text(obj.get("scope"), "S1_SCOPE_REQUIRED")
    for field in ("tasks", "claims", "hyperposition_branches", "gwt_broadcasts", "provenance_refs"):
        _need(isinstance(obj.get(field), list), "S1_" + field.upper() + "_LIST_REQUIRED")
    _need(bool(obj["provenance_refs"]), "S1_PROVENANCE_REQUIRED")
    digest = _digest(obj.get("state_digest"), "S1_DIGEST_REQUIRED")
    _need(sha256_obj(_without(obj, "state_digest")) == digest, "S1_DIGEST_MISMATCH")

    task_ids: set[str] = set()
    for task in obj["tasks"]:
        _need(isinstance(task, Mapping), "TASK_OBJECT_REQUIRED")
        task_id = _text(task.get("task_id"), "TASK_ID_REQUIRED")
        _need(task_id not in task_ids, "TASK_ID_DUPLICATE")
        task_ids.add(task_id)
        _need(type(task.get("priority")) is int, "TASK_PRIORITY_INT_REQUIRED")
        _strings(task.get("required_capabilities", []), "TASK_CAPABILITIES_INVALID")
        _need(task.get("status") in {"OPEN", "CLAIMED", "DONE", "BLOCKED"}, "TASK_STATUS_INVALID")

    claimed: set[str] = set()
    for claim in obj["claims"]:
        _need(isinstance(claim, Mapping), "CLAIM_OBJECT_REQUIRED")
        task_id = _text(claim.get("task_id"), "CLAIM_TASK_ID_REQUIRED")
        _need(task_id in task_ids, "CLAIM_UNKNOWN_TASK")
        _need(task_id not in claimed, "CLAIM_DUPLICATE_TASK")
        claimed.add(task_id)
        _text(claim.get("node_id"), "CLAIM_NODE_ID_REQUIRED")
    return obj


def _validate_lease(snapshot: Mapping[str, Any], lease: Mapping[str, Any], *, now_tick: int,
                    expected_holder: str | None = None) -> dict[str, Any]:
    _need(isinstance(lease, Mapping), "LEASE_OBJECT_REQUIRED")
    obj = dict(lease)
    _need(obj.get("schema") == LEASE_SCHEMA, "LEASE_SCHEMA_MISMATCH")
    digest = _digest(obj.get("lease_digest"), "LEASE_DIGEST_REQUIRED")
    _need(sha256_obj(_without(obj, "lease_digest")) == digest, "LEASE_DIGEST_MISMATCH")
    if expected_holder is not None:
        _need(obj.get("holder_node_id") == expected_holder, "LEASE_HOLDER_MISMATCH")
    _need(obj.get("scope") == snapshot["scope"], "LEASE_SCOPE_MISMATCH")
    _need(obj.get("bound_generation") == snapshot["generation"], "LEASE_GENERATION_STALE")
    _need(obj.get("bound_epoch") == snapshot["epoch"], "LEASE_EPOCH_STALE")
    _need(obj.get("bound_state_digest") == snapshot["state_digest"], "LEASE_STATE_STALE")
    _need(type(obj.get("not_before_tick")) is int and type(obj.get("expires_tick")) is int, "LEASE_TIME_INVALID")
    _need(obj["not_before_tick"] <= now_tick < obj["expires_tick"], "LEASE_NOT_CURRENT")
    return obj


def autonomous_boot(snapshot: Mapping[str, Any], *, node_id: str, capabilities: list[str],
                    now_tick: int, coordinator_lease: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Read exact S1 and choose the highest-priority eligible unclaimed task, without mutation."""
    snap = validate_snapshot(snapshot)
    node_id = _text(node_id, "NODE_ID_REQUIRED")
    caps = _strings(capabilities, "NODE_CAPABILITIES_INVALID")
    _need(type(now_tick) is int and now_tick >= 0, "NOW_TICK_INVALID")
    claimed = {str(c["task_id"]) for c in snap["claims"]}
    eligible = []
    for task in snap["tasks"]:
        required = _strings(task.get("required_capabilities", []), "TASK_CAPABILITIES_INVALID")
        if task["status"] == "OPEN" and task["task_id"] not in claimed and required <= caps:
            eligible.append(task)
    eligible.sort(key=lambda t: (-int(t["priority"]), str(t["task_id"])))
    selected = eligible[0]["task_id"] if eligible else None

    lease_id = None
    role = "ORDINARY"
    access = "READ_ONLY"
    if coordinator_lease is not None:
        lease = _validate_lease(snap, coordinator_lease, now_tick=now_tick, expected_holder=node_id)
        lease_id = lease["lease_id"]
        role = "COORDINATOR"
        access = "LEASE_SCOPED_WRITE_VIA_GATE_ONLY"

    material = {
        "schema": BOOT_SCHEMA,
        "node_id": node_id,
        "role": role,
        "capabilities": sorted(caps),
        "scope": snap["scope"],
        "bound_generation": snap["generation"],
        "bound_epoch": snap["epoch"],
        "bound_state_digest": snap["state_digest"],
        "selected_task_id": selected,
        "coordinator_lease_id": lease_id,
        "s1_access": access,
    }
    return {**material, "boot_plan_digest": sha256_obj(material)}


def make_node_result(boot_plan: Mapping[str, Any], *, result_id: str, payload_ref: str,
                     payload_digest: str, evidence_refs: list[str]) -> dict[str, Any]:
    _need(boot_plan.get("schema") == BOOT_SCHEMA, "BOOT_PLAN_SCHEMA_MISMATCH")
    digest = _digest(boot_plan.get("boot_plan_digest"), "BOOT_PLAN_DIGEST_REQUIRED")
    _need(sha256_obj(_without(boot_plan, "boot_plan_digest")) == digest, "BOOT_PLAN_DIGEST_MISMATCH")
    result_id = _text(result_id, "RESULT_ID_REQUIRED")
    payload_ref = _text(payload_ref, "PAYLOAD_REF_REQUIRED")
    payload_digest = _digest(payload_digest, "PAYLOAD_DIGEST_REQUIRED")
    refs = sorted(_strings(evidence_refs, "RESULT_EVIDENCE_INVALID"))
    _need(bool(refs), "RESULT_EVIDENCE_REQUIRED")
    material = {
        "schema": NODE_RESULT_SCHEMA,
        "result_id": result_id,
        "source_node_id": boot_plan["node_id"],
        "source_role": boot_plan["role"],
        "scope": boot_plan["scope"],
        "bound_generation": boot_plan["bound_generation"],
        "bound_epoch": boot_plan["bound_epoch"],
        "bound_state_digest": boot_plan["bound_state_digest"],
        "task_id": boot_plan.get("selected_task_id"),
        "payload_ref": payload_ref,
        "payload_digest": payload_digest,
        "evidence_refs": refs,
    }
    return {**material, "result_digest": sha256_obj(material)}


def select_coordinator(snapshot: Mapping[str, Any], *, candidates: Sequence[Mapping[str, Any]],
                       required_capabilities: list[str], now_tick: int, lease_ticks: int,
                       lease_id: str) -> dict[str, Any]:
    """Deterministic policy selection: healthy+eligible, minimum load, then node id."""
    snap = validate_snapshot(snapshot)
    required = _strings(required_capabilities, "LEASE_CAPABILITIES_INVALID")
    _need(type(now_tick) is int and now_tick >= 0, "NOW_TICK_INVALID")
    _need(type(lease_ticks) is int and lease_ticks > 0, "LEASE_TICKS_INVALID")
    lease_id = _text(lease_id, "LEASE_ID_REQUIRED")
    eligible: list[tuple[int, str]] = []
    for candidate in candidates:
        _need(isinstance(candidate, Mapping), "COORDINATOR_CANDIDATE_OBJECT_REQUIRED")
        node_id = _text(candidate.get("node_id"), "COORDINATOR_NODE_ID_REQUIRED")
        caps = _strings(candidate.get("capabilities", []), "COORDINATOR_CAPABILITIES_INVALID")
        load = candidate.get("load")
        _need(type(load) is int and load >= 0, "COORDINATOR_LOAD_INVALID")
        if candidate.get("healthy") is True and candidate.get("policy_eligible") is True and required <= caps:
            eligible.append((load, node_id))
    _need(bool(eligible), "NO_ELIGIBLE_COORDINATOR")
    eligible.sort()
    holder = eligible[0][1]
    material = {
        "schema": LEASE_SCHEMA,
        "lease_id": lease_id,
        "holder_node_id": holder,
        "scope": snap["scope"],
        "bound_generation": snap["generation"],
        "bound_epoch": snap["epoch"],
        "bound_state_digest": snap["state_digest"],
        "required_capabilities": sorted(required),
        "not_before_tick": now_tick,
        "expires_tick": now_tick + lease_ticks,
        "selection_rule": "POLICY_ELIGIBLE_HEALTHY_MIN_LOAD_THEN_NODE_ID",
    }
    return {**material, "lease_digest": sha256_obj(material)}


def authorize_s1_write(snapshot: Mapping[str, Any], *, coordinator_node_id: str,
                       lease: Mapping[str, Any], node_results: Sequence[Mapping[str, Any]],
                       expected_epoch: int, expected_state_digest: str, now_tick: int) -> dict[str, Any]:
    """Authorize a candidate S1 CAS write only; the caller remains responsible for actual CAS/persistence."""
    snap = validate_snapshot(snapshot)
    coordinator_node_id = _text(coordinator_node_id, "COORDINATOR_NODE_ID_REQUIRED")
    _need(type(expected_epoch) is int and expected_epoch >= 0, "EXPECTED_EPOCH_INVALID")
    _digest(expected_state_digest, "EXPECTED_STATE_DIGEST_INVALID")
    _need(expected_epoch == snap["epoch"], "S1_CAS_EPOCH_MISMATCH")
    _need(expected_state_digest == snap["state_digest"], "S1_CAS_DIGEST_MISMATCH")
    lease_obj = _validate_lease(snap, lease, now_tick=now_tick, expected_holder=coordinator_node_id)

    seen: set[str] = set()
    accepted: list[str] = []
    for result in node_results:
        _need(isinstance(result, Mapping), "NODE_RESULT_OBJECT_REQUIRED")
        _need(result.get("schema") == NODE_RESULT_SCHEMA, "NODE_RESULT_SCHEMA_MISMATCH")
        result_id = _text(result.get("result_id"), "RESULT_ID_REQUIRED")
        _need(result_id not in seen, "NODE_RESULT_DUPLICATE")
        seen.add(result_id)
        result_digest = _digest(result.get("result_digest"), "RESULT_DIGEST_REQUIRED")
        _need(sha256_obj(_without(result, "result_digest")) == result_digest, "RESULT_DIGEST_MISMATCH")
        _need(result.get("scope") == snap["scope"], "NODE_RESULT_SCOPE_MISMATCH")
        _need(result.get("bound_generation") == snap["generation"], "NODE_RESULT_GENERATION_STALE")
        _need(result.get("bound_epoch") == snap["epoch"], "NODE_RESULT_EPOCH_STALE")
        _need(result.get("bound_state_digest") == snap["state_digest"], "NODE_RESULT_STATE_STALE")
        accepted.append(result_digest)

    material = {
        "schema": WRITE_AUTH_SCHEMA,
        "coordinator_node_id": coordinator_node_id,
        "lease_id": lease_obj["lease_id"],
        "scope": snap["scope"],
        "expected_generation": snap["generation"],
        "expected_epoch": snap["epoch"],
        "expected_state_digest": snap["state_digest"],
        "accepted_result_digests": sorted(accepted),
        "write_class": "S1_CANDIDATE_DELTA_ONLY",
        "s0_truth_effect_security_authority": False,
    }
    return {**material, "authorization_digest": sha256_obj(material)}


def reject_direct_s1_write(boot_plan: Mapping[str, Any]) -> None:
    _need(boot_plan.get("schema") == BOOT_SCHEMA, "BOOT_PLAN_SCHEMA_MISMATCH")
    if boot_plan.get("role") == "ORDINARY":
        raise XenoSharedStateError("ORDINARY_NODE_S1_WRITE_FORBIDDEN")
    raise XenoSharedStateError("DIRECT_S1_WRITE_FORBIDDEN_USE_COORDINATOR_GATE")


__all__ = [
    "S1_SCHEMA", "BOOT_SCHEMA", "NODE_RESULT_SCHEMA", "LEASE_SCHEMA", "WRITE_AUTH_SCHEMA",
    "XenoSharedStateError", "build_snapshot", "validate_snapshot", "autonomous_boot",
    "make_node_result", "select_coordinator", "authorize_s1_write", "reject_direct_s1_write",
]
