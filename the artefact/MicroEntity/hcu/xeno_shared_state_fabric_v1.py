#!/usr/bin/env python3
"""Deterministic S1 shared-state bootstrap for the EntityOS/HCU Xeno fabric.

This module implements the first executable owner-target path:

    AUTONOMOUS_BOOT -> S1 read-only -> NODE_RESULT/v1
    -> GRID_COORDINATOR_LEASE/v1 -> coordinator-only S1 commit

It is deterministic control/state plumbing, not cognition and not S0 truth/effect/security
authority. Ordinary nodes receive no S1 mutation primitive. Coordinator write authority is
accepted only when a lease is bound to an externally supplied canonical lease-authority
digest, the current S1 epoch/digest, node identity, and scope.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

S1_SNAPSHOT_SCHEMA = "ENTITYOS_HCU_S1_SNAPSHOT/v1"
NODE_BINDING_SCHEMA = "ENTITYOS_HCU_NODE_IDENTITY_BINDING/v1"
AUTONOMOUS_BOOT_SCHEMA = "ENTITYOS_HCU_AUTONOMOUS_BOOT/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
COORDINATOR_LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v1"
S1_DELTA_SCHEMA = "ENTITYOS_HCU_S1_DELTA/v1"
S1_COMMIT_SCHEMA = "ENTITYOS_HCU_S1_COMMIT/v1"

OPEN_WORK_STATUSES = {"OPEN", "READY"}
TERMINAL_WORK_STATUSES = {"DONE", "CANCELLED", "REJECTED"}
TRACE_BINDING_FIELDS = {
    "inference_receipt_sha256",
    "gwt_trace_sha256",
    "jspace_trace_sha256",
    "hyperposition_trace_sha256",
}


class SharedStateFabricError(ValueError):
    pass


@dataclass(frozen=True)
class S1Snapshot:
    schema: str
    fabric_id: str
    entity_generation: int
    epoch: int
    policy_version: str
    state: Mapping[str, Any]
    digest_sha256: str


@dataclass(frozen=True)
class AutonomousBoot:
    schema: str
    fabric_id: str
    entity_generation: int
    snapshot_epoch: int
    snapshot_digest_sha256: str
    policy_version: str
    node_id: str
    node_binding_sha256: str
    capabilities: tuple[str, ...]
    runtime_role: str
    selected_task_id: str | None
    selected_scope: str | None
    boot_sha256: str


@dataclass(frozen=True)
class NodeResult:
    schema: str
    fabric_id: str
    entity_generation: int
    snapshot_epoch: int
    snapshot_digest_sha256: str
    node_id: str
    node_binding_sha256: str
    task_id: str
    scope: str
    result_kind: str
    payload_ref: str
    payload_sha256: str
    trace_bindings: tuple[tuple[str, str], ...]
    result_sha256: str


@dataclass(frozen=True)
class CoordinatorCandidate:
    node_id: str
    node_binding_sha256: str
    health: str = "HEALTHY"
    load: int = 0


@dataclass(frozen=True)
class CoordinatorLease:
    schema: str
    fabric_id: str
    entity_generation: int
    scope: str
    holder_node_id: str
    holder_node_binding_sha256: str
    issued_for_epoch: int
    valid_through_epoch: int
    snapshot_digest_sha256: str
    policy_version: str
    lease_authority_binding_sha256: str
    lease_sha256: str


@dataclass(frozen=True)
class S1Commit:
    schema: str
    previous_epoch: int
    previous_digest_sha256: str
    new_snapshot: S1Snapshot
    lease_sha256: str
    accepted_result_sha256: tuple[str, ...]
    delta_sha256: str


def _identity_sha256(value: Any, field: str) -> str:
    try:
        encoded = canonicalize(value)
    except CanonicalizationError as exc:
        raise SharedStateFabricError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(encoded).hexdigest()


def _text(value: Any, field: str, *, optional: bool = False, max_len: int = 512) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise SharedStateFabricError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise SharedStateFabricError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise SharedStateFabricError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise SharedStateFabricError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SharedStateFabricError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise SharedStateFabricError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _capabilities(value: Any, field: str = "capabilities") -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise SharedStateFabricError(f"{field}:SEQUENCE_REQUIRED")
    normalized: list[str] = []
    for item in value:
        text = _text(item, field)
        assert text is not None
        normalized.append(text)
    if len(normalized) != len(set(normalized)):
        raise SharedStateFabricError(f"{field}:DUPLICATE_FORBIDDEN")
    return tuple(sorted(normalized))


def _json_clone(value: Any, field: str) -> Any:
    """Detach caller-owned mutable containers after checking canonicalizability."""
    try:
        encoded = canonicalize(value)
        return json.loads(encoded.decode("utf-8"))
    except (CanonicalizationError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SharedStateFabricError(f"{field}:CANONICAL_JSON_REQUIRED:{exc}") from exc


def _snapshot_identity(*, fabric_id: str, entity_generation: int, epoch: int,
                       policy_version: str, state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": S1_SNAPSHOT_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "fabric_id": fabric_id,
        "entity_generation": entity_generation,
        "epoch": epoch,
        "policy_version": policy_version,
        "state": state,
    }


def build_s1_snapshot(*, fabric_id: str, entity_generation: int, epoch: int,
                      policy_version: str, state: Mapping[str, Any]) -> S1Snapshot:
    fabric_id = _text(fabric_id, "fabric_id")
    policy_version = _text(policy_version, "policy_version")
    generation = _nonnegative_int(entity_generation, "entity_generation")
    epoch = _nonnegative_int(epoch, "epoch")
    if not isinstance(state, Mapping):
        raise SharedStateFabricError("state:MAPPING_REQUIRED")
    cloned = _json_clone(state, "state")
    assert isinstance(cloned, dict)
    assert fabric_id and policy_version
    digest = _identity_sha256(
        _snapshot_identity(
            fabric_id=fabric_id,
            entity_generation=generation,
            epoch=epoch,
            policy_version=policy_version,
            state=cloned,
        ),
        "S1_SNAPSHOT",
    )
    return S1Snapshot(
        schema=S1_SNAPSHOT_SCHEMA,
        fabric_id=fabric_id,
        entity_generation=generation,
        epoch=epoch,
        policy_version=policy_version,
        state=cloned,
        digest_sha256=digest,
    )


def admit_s1_snapshot(raw: Mapping[str, Any], *, current_generation: int,
                      expected_fabric_id: str, expected_policy_version: str) -> S1Snapshot:
    """Admit a versioned S1 view; digest mismatch, stale generation, or policy drift fails closed."""
    if not isinstance(raw, Mapping):
        raise SharedStateFabricError("S1_SNAPSHOT_MAPPING_REQUIRED")
    allowed = {"schema", "fabric_id", "entity_generation", "epoch", "policy_version", "state", "digest_sha256"}
    unknown = set(raw) - allowed
    if unknown:
        raise SharedStateFabricError(f"S1_SNAPSHOT_UNKNOWN_FIELDS:{','.join(sorted(unknown))}")
    if raw.get("schema") != S1_SNAPSHOT_SCHEMA:
        raise SharedStateFabricError("S1_SNAPSHOT_SCHEMA_UNSUPPORTED")
    generation = _nonnegative_int(raw.get("entity_generation"), "entity_generation")
    current_generation = _nonnegative_int(current_generation, "current_generation")
    if generation != current_generation:
        raise SharedStateFabricError("STALE_ENTITY_GENERATION")
    expected_fabric_id = _text(expected_fabric_id, "expected_fabric_id")
    expected_policy_version = _text(expected_policy_version, "expected_policy_version")
    if raw.get("fabric_id") != expected_fabric_id:
        raise SharedStateFabricError("S1_FABRIC_ID_MISMATCH")
    if raw.get("policy_version") != expected_policy_version:
        raise SharedStateFabricError("S1_POLICY_VERSION_MISMATCH")
    built = build_s1_snapshot(
        fabric_id=raw.get("fabric_id"),
        entity_generation=generation,
        epoch=raw.get("epoch"),
        policy_version=raw.get("policy_version"),
        state=raw.get("state"),
    )
    supplied = _sha256(raw.get("digest_sha256"), "digest_sha256")
    if supplied != built.digest_sha256:
        raise SharedStateFabricError("S1_DIGEST_MISMATCH")
    return built


def snapshot_to_wire(snapshot: S1Snapshot) -> dict[str, Any]:
    if not isinstance(snapshot, S1Snapshot):
        raise SharedStateFabricError("S1_SNAPSHOT_REQUIRED")
    return {
        "schema": snapshot.schema,
        "fabric_id": snapshot.fabric_id,
        "entity_generation": snapshot.entity_generation,
        "epoch": snapshot.epoch,
        "policy_version": snapshot.policy_version,
        "state": _json_clone(snapshot.state, "state"),
        "digest_sha256": snapshot.digest_sha256,
    }


def derive_node_binding_sha256(*, node_id: str, capabilities: Sequence[str],
                               entity_generation: int, policy_version: str) -> str:
    node_id = _text(node_id, "node_id")
    policy_version = _text(policy_version, "policy_version")
    caps = _capabilities(capabilities)
    generation = _nonnegative_int(entity_generation, "entity_generation")
    assert node_id and policy_version
    return _identity_sha256(
        {
            "schema": NODE_BINDING_SCHEMA,
            "canonicalization_schema": CANONICALIZATION_SCHEMA,
            "node_id": node_id,
            "capabilities": list(caps),
            "entity_generation": generation,
            "policy_version": policy_version,
        },
        "NODE_BINDING",
    )


def _active_nodes(snapshot: S1Snapshot) -> dict[str, tuple[str, ...]]:
    raw = snapshot.state.get("active_nodes", [])
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise SharedStateFabricError("S1_ACTIVE_NODES_SEQUENCE_REQUIRED")
    nodes: dict[str, tuple[str, ...]] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise SharedStateFabricError("S1_ACTIVE_NODE_MAPPING_REQUIRED")
        unknown = set(item) - {"node_id", "capabilities"}
        if unknown:
            raise SharedStateFabricError(f"S1_ACTIVE_NODE_UNKNOWN_FIELDS:{','.join(sorted(unknown))}")
        node_id = _text(item.get("node_id"), "active_node.node_id")
        assert node_id
        if node_id in nodes:
            raise SharedStateFabricError("S1_ACTIVE_NODE_DUPLICATE")
        nodes[node_id] = _capabilities(item.get("capabilities"), "active_node.capabilities")
    return nodes


def _work_items(snapshot: S1Snapshot) -> list[dict[str, Any]]:
    raw = snapshot.state.get("work_items", [])
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise SharedStateFabricError("S1_WORK_ITEMS_SEQUENCE_REQUIRED")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    allowed = {"task_id", "scope", "status", "required_capabilities", "claimed_by"}
    for item in raw:
        if not isinstance(item, Mapping):
            raise SharedStateFabricError("S1_WORK_ITEM_MAPPING_REQUIRED")
        unknown = set(item) - allowed
        if unknown:
            raise SharedStateFabricError(f"S1_WORK_ITEM_UNKNOWN_FIELDS:{','.join(sorted(unknown))}")
        task_id = _text(item.get("task_id"), "work_item.task_id")
        scope = _text(item.get("scope"), "work_item.scope")
        status = _text(item.get("status"), "work_item.status")
        claimed_by = _text(item.get("claimed_by"), "work_item.claimed_by", optional=True)
        assert task_id and scope and status
        if task_id in seen:
            raise SharedStateFabricError("S1_WORK_ITEM_DUPLICATE")
        seen.add(task_id)
        items.append({
            "task_id": task_id,
            "scope": scope,
            "status": status,
            "required_capabilities": _capabilities(item.get("required_capabilities", ()), "work_item.required_capabilities"),
            "claimed_by": claimed_by,
        })
    return items


def _rendezvous_owner(snapshot: S1Snapshot, item: Mapping[str, Any],
                      nodes: Mapping[str, tuple[str, ...]]) -> str | None:
    required = set(item["required_capabilities"])
    eligible = [node_id for node_id, caps in nodes.items() if required.issubset(set(caps))]
    if not eligible:
        return None
    task_id = item["task_id"]
    return max(
        eligible,
        key=lambda node_id: hashlib.sha256(
            f"{snapshot.digest_sha256}|{task_id}|{node_id}".encode("utf-8")
        ).digest(),
    )


def autonomous_boot(*, snapshot: S1Snapshot, node_id: str, capabilities: Sequence[str],
                    expected_node_binding_sha256: str) -> AutonomousBoot:
    """Bind a node to current S1 and deterministically select useful open work.

    The runtime role is always ORDINARY at boot. Coordinator authority can only be added
    later by a separately admitted GRID_COORDINATOR_LEASE/v1.
    """
    if not isinstance(snapshot, S1Snapshot):
        raise SharedStateFabricError("S1_SNAPSHOT_REQUIRED")
    node_id = _text(node_id, "node_id")
    assert node_id
    caps = _capabilities(capabilities)
    expected = _sha256(expected_node_binding_sha256, "expected_node_binding_sha256")
    actual = derive_node_binding_sha256(
        node_id=node_id,
        capabilities=caps,
        entity_generation=snapshot.entity_generation,
        policy_version=snapshot.policy_version,
    )
    if actual != expected:
        raise SharedStateFabricError("NODE_IDENTITY_BINDING_MISMATCH")
    nodes = _active_nodes(snapshot)
    if node_id not in nodes:
        raise SharedStateFabricError("NODE_NOT_ADMITTED_IN_S1")
    if nodes[node_id] != caps:
        raise SharedStateFabricError("NODE_CAPABILITY_VIEW_MISMATCH")

    candidates: list[dict[str, Any]] = []
    for item in _work_items(snapshot):
        if item["status"] not in OPEN_WORK_STATUSES or item["claimed_by"] is not None:
            continue
        if not set(item["required_capabilities"]).issubset(set(caps)):
            continue
        if _rendezvous_owner(snapshot, item, nodes) == node_id:
            candidates.append(item)
    candidates.sort(key=lambda item: _identity_sha256(
        {"snapshot": snapshot.digest_sha256, "node_id": node_id, "task_id": item["task_id"]},
        "WORK_SELECTION",
    ))
    selected = candidates[0] if candidates else None
    identity = {
        "schema": AUTONOMOUS_BOOT_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "fabric_id": snapshot.fabric_id,
        "entity_generation": snapshot.entity_generation,
        "snapshot_epoch": snapshot.epoch,
        "snapshot_digest_sha256": snapshot.digest_sha256,
        "policy_version": snapshot.policy_version,
        "node_id": node_id,
        "node_binding_sha256": actual,
        "capabilities": list(caps),
        "runtime_role": "ORDINARY",
        "selected_task_id": selected["task_id"] if selected else None,
        "selected_scope": selected["scope"] if selected else None,
    }
    return AutonomousBoot(
        schema=AUTONOMOUS_BOOT_SCHEMA,
        fabric_id=snapshot.fabric_id,
        entity_generation=snapshot.entity_generation,
        snapshot_epoch=snapshot.epoch,
        snapshot_digest_sha256=snapshot.digest_sha256,
        policy_version=snapshot.policy_version,
        node_id=node_id,
        node_binding_sha256=actual,
        capabilities=caps,
        runtime_role="ORDINARY",
        selected_task_id=selected["task_id"] if selected else None,
        selected_scope=selected["scope"] if selected else None,
        boot_sha256=_identity_sha256(identity, "AUTONOMOUS_BOOT"),
    )


def make_node_result(*, boot: AutonomousBoot, task_id: str, scope: str,
                     result_kind: str, payload_ref: str, payload_sha256: str,
                     trace_bindings: Mapping[str, str] | None = None) -> NodeResult:
    """Emit an ephemeral typed result. This function has no S1 mutation capability."""
    if not isinstance(boot, AutonomousBoot):
        raise SharedStateFabricError("AUTONOMOUS_BOOT_REQUIRED")
    if boot.runtime_role != "ORDINARY":
        raise SharedStateFabricError("NODE_RESULT_REQUIRES_ORDINARY_BOOT")
    task_id = _text(task_id, "task_id")
    scope = _text(scope, "scope")
    result_kind = _text(result_kind, "result_kind")
    payload_ref = _text(payload_ref, "payload_ref")
    payload_sha256 = _sha256(payload_sha256, "payload_sha256")
    assert task_id and scope and result_kind and payload_ref
    if boot.selected_task_id is not None and task_id != boot.selected_task_id:
        raise SharedStateFabricError("NODE_RESULT_TASK_NOT_SELECTED")
    if boot.selected_scope is not None and scope != boot.selected_scope:
        raise SharedStateFabricError("NODE_RESULT_SCOPE_NOT_SELECTED")
    raw_traces = trace_bindings or {}
    if not isinstance(raw_traces, Mapping):
        raise SharedStateFabricError("trace_bindings:MAPPING_REQUIRED")
    unknown = set(raw_traces) - TRACE_BINDING_FIELDS
    if unknown:
        raise SharedStateFabricError(f"TRACE_BINDING_UNKNOWN_FIELDS:{','.join(sorted(unknown))}")
    traces = tuple(sorted((field, _sha256(value, field)) for field, value in raw_traces.items()))
    identity = {
        "schema": NODE_RESULT_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "fabric_id": boot.fabric_id,
        "entity_generation": boot.entity_generation,
        "snapshot_epoch": boot.snapshot_epoch,
        "snapshot_digest_sha256": boot.snapshot_digest_sha256,
        "node_id": boot.node_id,
        "node_binding_sha256": boot.node_binding_sha256,
        "task_id": task_id,
        "scope": scope,
        "result_kind": result_kind,
        "payload_ref": payload_ref,
        "payload_sha256": payload_sha256,
        "trace_bindings": dict(traces),
    }
    return NodeResult(
        schema=NODE_RESULT_SCHEMA,
        fabric_id=boot.fabric_id,
        entity_generation=boot.entity_generation,
        snapshot_epoch=boot.snapshot_epoch,
        snapshot_digest_sha256=boot.snapshot_digest_sha256,
        node_id=boot.node_id,
        node_binding_sha256=boot.node_binding_sha256,
        task_id=task_id,
        scope=scope,
        result_kind=result_kind,
        payload_ref=payload_ref,
        payload_sha256=payload_sha256,
        trace_bindings=traces,
        result_sha256=_identity_sha256(identity, "NODE_RESULT"),
    )


def issue_coordinator_lease(*, snapshot: S1Snapshot, scope: str,
                           candidates: Sequence[CoordinatorCandidate],
                           lease_authority_binding_sha256: str,
                           valid_epoch_span: int = 1) -> CoordinatorLease:
    """Controller-side deterministic lease construction.

    `lease_authority_binding_sha256` is an externally admitted S0/control-plane binding;
    this module never derives authority from model output or the S1 packet itself.
    """
    if not isinstance(snapshot, S1Snapshot):
        raise SharedStateFabricError("S1_SNAPSHOT_REQUIRED")
    scope = _text(scope, "scope")
    authority = _sha256(lease_authority_binding_sha256, "lease_authority_binding_sha256")
    span = _nonnegative_int(valid_epoch_span, "valid_epoch_span")
    if span != 1:
        raise SharedStateFabricError("valid_epoch_span:MUST_EQUAL_ONE_FOR_DIGEST_BOUND_LEASE")
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence) or not candidates:
        raise SharedStateFabricError("COORDINATOR_CANDIDATES_REQUIRED")
    active = _active_nodes(snapshot)
    admitted: list[CoordinatorCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, CoordinatorCandidate):
            raise SharedStateFabricError("COORDINATOR_CANDIDATE_REQUIRED")
        node_id = _text(candidate.node_id, "candidate.node_id")
        assert node_id
        if node_id in seen:
            raise SharedStateFabricError("COORDINATOR_CANDIDATE_DUPLICATE")
        seen.add(node_id)
        if candidate.health != "HEALTHY":
            continue
        load = _nonnegative_int(candidate.load, "candidate.load")
        if node_id not in active:
            continue
        expected_binding = derive_node_binding_sha256(
            node_id=node_id,
            capabilities=active[node_id],
            entity_generation=snapshot.entity_generation,
            policy_version=snapshot.policy_version,
        )
        if _sha256(candidate.node_binding_sha256, "candidate.node_binding_sha256") != expected_binding:
            continue
        admitted.append(CoordinatorCandidate(node_id=node_id, node_binding_sha256=expected_binding,
                                                health="HEALTHY", load=load))
    if not admitted:
        raise SharedStateFabricError("NO_ADMITTED_COORDINATOR_CANDIDATE")
    assert scope
    holder = min(
        admitted,
        key=lambda candidate: (
            candidate.load,
            _identity_sha256(
                {"snapshot": snapshot.digest_sha256, "scope": scope, "node_id": candidate.node_id},
                "COORDINATOR_SELECTION",
            ),
        ),
    )
    valid_through = snapshot.epoch + span - 1
    if valid_through > 9_007_199_254_740_991:
        raise SharedStateFabricError("LEASE_EPOCH_OVERFLOW")
    identity = {
        "schema": COORDINATOR_LEASE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "fabric_id": snapshot.fabric_id,
        "entity_generation": snapshot.entity_generation,
        "scope": scope,
        "holder_node_id": holder.node_id,
        "holder_node_binding_sha256": holder.node_binding_sha256,
        "issued_for_epoch": snapshot.epoch,
        "valid_through_epoch": valid_through,
        "snapshot_digest_sha256": snapshot.digest_sha256,
        "policy_version": snapshot.policy_version,
        "lease_authority_binding_sha256": authority,
    }
    return CoordinatorLease(
        schema=COORDINATOR_LEASE_SCHEMA,
        fabric_id=snapshot.fabric_id,
        entity_generation=snapshot.entity_generation,
        scope=scope,
        holder_node_id=holder.node_id,
        holder_node_binding_sha256=holder.node_binding_sha256,
        issued_for_epoch=snapshot.epoch,
        valid_through_epoch=valid_through,
        snapshot_digest_sha256=snapshot.digest_sha256,
        policy_version=snapshot.policy_version,
        lease_authority_binding_sha256=authority,
        lease_sha256=_identity_sha256(identity, "COORDINATOR_LEASE"),
    )


def _coordinator_lease_identity(lease: CoordinatorLease) -> dict[str, Any]:
    return {
        "schema": COORDINATOR_LEASE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "fabric_id": lease.fabric_id,
        "entity_generation": lease.entity_generation,
        "scope": lease.scope,
        "holder_node_id": lease.holder_node_id,
        "holder_node_binding_sha256": lease.holder_node_binding_sha256,
        "issued_for_epoch": lease.issued_for_epoch,
        "valid_through_epoch": lease.valid_through_epoch,
        "snapshot_digest_sha256": lease.snapshot_digest_sha256,
        "policy_version": lease.policy_version,
        "lease_authority_binding_sha256": lease.lease_authority_binding_sha256,
    }


def _node_result_identity(result: NodeResult) -> dict[str, Any]:
    return {
        "schema": NODE_RESULT_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "fabric_id": result.fabric_id,
        "entity_generation": result.entity_generation,
        "snapshot_epoch": result.snapshot_epoch,
        "snapshot_digest_sha256": result.snapshot_digest_sha256,
        "node_id": result.node_id,
        "node_binding_sha256": result.node_binding_sha256,
        "task_id": result.task_id,
        "scope": result.scope,
        "result_kind": result.result_kind,
        "payload_ref": result.payload_ref,
        "payload_sha256": result.payload_sha256,
        "trace_bindings": dict(result.trace_bindings),
    }


def validate_coordinator_lease(*, snapshot: S1Snapshot, lease: CoordinatorLease,
                               caller_node_id: str, expected_scope: str,
                               expected_lease_authority_binding_sha256: str) -> None:
    if not isinstance(snapshot, S1Snapshot):
        raise SharedStateFabricError("S1_SNAPSHOT_REQUIRED")
    if not isinstance(lease, CoordinatorLease):
        raise SharedStateFabricError("GRID_COORDINATOR_LEASE_REQUIRED")
    caller_node_id = _text(caller_node_id, "caller_node_id")
    expected_scope = _text(expected_scope, "expected_scope")
    expected_authority = _sha256(
        expected_lease_authority_binding_sha256,
        "expected_lease_authority_binding_sha256",
    )
    assert caller_node_id and expected_scope
    if lease.schema != COORDINATOR_LEASE_SCHEMA:
        raise SharedStateFabricError("COORDINATOR_LEASE_SCHEMA_UNSUPPORTED")
    if _identity_sha256(_coordinator_lease_identity(lease), "COORDINATOR_LEASE") != lease.lease_sha256:
        raise SharedStateFabricError("COORDINATOR_LEASE_DIGEST_MISMATCH")
    if lease.lease_authority_binding_sha256 != expected_authority:
        raise SharedStateFabricError("COORDINATOR_LEASE_AUTHORITY_MISMATCH")
    if lease.fabric_id != snapshot.fabric_id or lease.entity_generation != snapshot.entity_generation:
        raise SharedStateFabricError("COORDINATOR_LEASE_FABRIC_OR_GENERATION_MISMATCH")
    if lease.policy_version != snapshot.policy_version:
        raise SharedStateFabricError("COORDINATOR_LEASE_POLICY_MISMATCH")
    if lease.scope != expected_scope:
        raise SharedStateFabricError("COORDINATOR_LEASE_SCOPE_MISMATCH")
    if lease.holder_node_id != caller_node_id:
        raise SharedStateFabricError("COORDINATOR_LEASE_NOT_HELD_BY_CALLER")
    if lease.issued_for_epoch > snapshot.epoch or snapshot.epoch > lease.valid_through_epoch:
        raise SharedStateFabricError("STALE_OR_NOT_YET_VALID_COORDINATOR_LEASE")
    if lease.issued_for_epoch == snapshot.epoch and lease.snapshot_digest_sha256 != snapshot.digest_sha256:
        raise SharedStateFabricError("COORDINATOR_LEASE_SNAPSHOT_MISMATCH")
    active = _active_nodes(snapshot)
    if caller_node_id not in active:
        raise SharedStateFabricError("COORDINATOR_HOLDER_NOT_ACTIVE")
    expected_holder_binding = derive_node_binding_sha256(
        node_id=caller_node_id,
        capabilities=active[caller_node_id],
        entity_generation=snapshot.entity_generation,
        policy_version=snapshot.policy_version,
    )
    if lease.holder_node_binding_sha256 != expected_holder_binding:
        raise SharedStateFabricError("COORDINATOR_HOLDER_BINDING_MISMATCH")


def _validate_result_against_snapshot(snapshot: S1Snapshot, result: NodeResult, scope: str) -> None:
    if not isinstance(result, NodeResult):
        raise SharedStateFabricError("NODE_RESULT_REQUIRED")
    if result.schema != NODE_RESULT_SCHEMA:
        raise SharedStateFabricError("NODE_RESULT_SCHEMA_UNSUPPORTED")
    if _identity_sha256(_node_result_identity(result), "NODE_RESULT") != result.result_sha256:
        raise SharedStateFabricError("NODE_RESULT_DIGEST_MISMATCH")
    if result.fabric_id != snapshot.fabric_id or result.entity_generation != snapshot.entity_generation:
        raise SharedStateFabricError("NODE_RESULT_FABRIC_OR_GENERATION_MISMATCH")
    if result.snapshot_epoch != snapshot.epoch or result.snapshot_digest_sha256 != snapshot.digest_sha256:
        raise SharedStateFabricError("STALE_NODE_RESULT")
    if result.scope != scope:
        raise SharedStateFabricError("NODE_RESULT_SCOPE_MISMATCH")
    active = _active_nodes(snapshot)
    if result.node_id not in active:
        raise SharedStateFabricError("NODE_RESULT_NODE_NOT_ACTIVE")
    expected_binding = derive_node_binding_sha256(
        node_id=result.node_id,
        capabilities=active[result.node_id],
        entity_generation=snapshot.entity_generation,
        policy_version=snapshot.policy_version,
    )
    if result.node_binding_sha256 != expected_binding:
        raise SharedStateFabricError("NODE_RESULT_NODE_BINDING_MISMATCH")
    work = {item["task_id"]: item for item in _work_items(snapshot)}
    item = work.get(result.task_id)
    if item is None:
        raise SharedStateFabricError("NODE_RESULT_TASK_UNKNOWN")
    if item["scope"] != scope:
        raise SharedStateFabricError("NODE_RESULT_TASK_SCOPE_MISMATCH")
    if item["status"] in TERMINAL_WORK_STATUSES:
        raise SharedStateFabricError("NODE_RESULT_TASK_ALREADY_TERMINAL")
    if item["status"] in OPEN_WORK_STATUSES and item["claimed_by"] is None:
        owner = _rendezvous_owner(snapshot, item, active)
        if owner != result.node_id:
            raise SharedStateFabricError("NODE_RESULT_NOT_DETERMINISTIC_WORK_OWNER")
    elif item["claimed_by"] is not None and item["claimed_by"] != result.node_id:
        raise SharedStateFabricError("NODE_RESULT_NOT_CLAIM_OWNER")


def commit_s1_delta(*, snapshot: S1Snapshot, caller_node_id: str,
                    lease: CoordinatorLease | None,
                    expected_lease_authority_binding_sha256: str,
                    node_results: Sequence[NodeResult], next_state: Mapping[str, Any]) -> S1Commit:
    """The sole model-originated S1 write primitive in this component.

    Missing/forged/stale/out-of-scope lease fails closed. Inputs are epoch/digest bound and
    duplicate results are rejected. The return value is another S1 snapshot only: it grants
    no S0 truth, effect, security, recovery, or permission authority.
    """
    if lease is None:
        raise SharedStateFabricError("NO_VALID_COORDINATOR_LEASE_NO_S1_WRITE")
    if not isinstance(lease, CoordinatorLease):
        raise SharedStateFabricError("GRID_COORDINATOR_LEASE_REQUIRED")
    validate_coordinator_lease(
        snapshot=snapshot,
        lease=lease,
        caller_node_id=caller_node_id,
        expected_scope=lease.scope,
        expected_lease_authority_binding_sha256=expected_lease_authority_binding_sha256,
    )
    if isinstance(node_results, (str, bytes)) or not isinstance(node_results, Sequence):
        raise SharedStateFabricError("node_results:SEQUENCE_REQUIRED")
    result_ids: set[str] = set()
    node_tasks: set[tuple[str, str]] = set()
    accepted: list[str] = []
    for result in node_results:
        _validate_result_against_snapshot(snapshot, result, lease.scope)
        if result.result_sha256 in result_ids:
            raise SharedStateFabricError("DUPLICATE_NODE_RESULT")
        result_ids.add(result.result_sha256)
        key = (result.node_id, result.task_id)
        if key in node_tasks:
            raise SharedStateFabricError("DUPLICATE_NODE_TASK_RESULT")
        node_tasks.add(key)
        accepted.append(result.result_sha256)
    if not isinstance(next_state, Mapping):
        raise SharedStateFabricError("next_state:MAPPING_REQUIRED")
    # Node identity/capability admission is a deterministic control-plane projection, not
    # coordinator-owned cognition. A coordinator may not self-grant or rewrite that view.
    current_active_nodes = _json_clone(snapshot.state.get("active_nodes", []), "state.active_nodes")
    next_active_nodes = _json_clone(next_state.get("active_nodes", []), "next_state.active_nodes")
    if next_active_nodes != current_active_nodes:
        raise SharedStateFabricError("COORDINATOR_MAY_NOT_MUTATE_ACTIVE_NODE_AUTHORITY_VIEW")
    if snapshot.epoch == 9_007_199_254_740_991:
        raise SharedStateFabricError("S1_EPOCH_OVERFLOW")
    new_snapshot = build_s1_snapshot(
        fabric_id=snapshot.fabric_id,
        entity_generation=snapshot.entity_generation,
        epoch=snapshot.epoch + 1,
        policy_version=snapshot.policy_version,
        state=next_state,
    )
    delta_identity = {
        "schema": S1_DELTA_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "fabric_id": snapshot.fabric_id,
        "entity_generation": snapshot.entity_generation,
        "scope": lease.scope,
        "previous_epoch": snapshot.epoch,
        "previous_digest_sha256": snapshot.digest_sha256,
        "new_epoch": new_snapshot.epoch,
        "new_digest_sha256": new_snapshot.digest_sha256,
        "lease_sha256": lease.lease_sha256,
        "accepted_result_sha256": sorted(accepted),
    }
    return S1Commit(
        schema=S1_COMMIT_SCHEMA,
        previous_epoch=snapshot.epoch,
        previous_digest_sha256=snapshot.digest_sha256,
        new_snapshot=new_snapshot,
        lease_sha256=lease.lease_sha256,
        accepted_result_sha256=tuple(sorted(accepted)),
        delta_sha256=_identity_sha256(delta_identity, "S1_DELTA"),
    )
