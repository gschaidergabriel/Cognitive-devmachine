#!/usr/bin/env python3
"""Deterministic S1 shared-state / autonomous-boot component for EntityOS/HCU Xeno.

Component scope only. S1 is noncanonical cognitive workspace state. This module
never grants S0 truth/effect/security authority and never performs model/provider I/O.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

S1_SCHEMA = "ENTITYOS_HCU_S1_STATE/v1"
BOOT_SCHEMA = "XENO_AUTONOMOUS_BOOT/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
COORDINATOR_LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v1"

FORBIDDEN_S1_ROOTS = frozenset({"s0", "canonical", "truth", "effects", "effect_journal", "secrets", "permissions"})


class SharedStateError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    """Stable component encoding; reject non-JSON values and non-finite floats."""
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise SharedStateError(f"NONCANONICAL_STATE:{exc}") from exc
    return text.encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SharedStateError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _capabilities(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise SharedStateError("capabilities:SEQUENCE_REQUIRED")
    out = tuple(sorted({_nonempty(v, "capability") for v in values}))
    if len(out) != len(values):
        raise SharedStateError("capabilities:DUPLICATE_FORBIDDEN")
    return out


@dataclass(frozen=True)
class NodeDescriptor:
    node_id: str
    capabilities: tuple[str, ...]
    healthy: bool = True
    load_milli: int = 0

    @classmethod
    def admit(cls, node_id: str, capabilities: Sequence[str], *, healthy: bool = True, load_milli: int = 0) -> "NodeDescriptor":
        node_id = _nonempty(node_id, "node_id")
        if not isinstance(healthy, bool):
            raise SharedStateError("healthy:BOOL_REQUIRED")
        if isinstance(load_milli, bool) or not isinstance(load_milli, int) or load_milli < 0:
            raise SharedStateError("load_milli:NONNEGATIVE_INT_REQUIRED")
        return cls(node_id=node_id, capabilities=_capabilities(capabilities), healthy=healthy, load_milli=load_milli)


@dataclass(frozen=True)
class SharedStateSnapshot:
    schema: str
    epoch: int
    digest: str
    state: Mapping[str, Any]


@dataclass(frozen=True)
class BootSession:
    schema: str
    node_id: str
    role: str
    state_epoch: int
    state_digest: str
    selected_task_id: str | None
    selection_reason: str


@dataclass(frozen=True)
class NodeResult:
    schema: str
    result_id: str
    node_id: str
    task_id: str
    state_epoch: int
    state_digest: str
    payload_ref: str
    payload_sha256: str


@dataclass(frozen=True)
class CoordinatorLease:
    schema: str
    lease_id: str
    node_id: str
    scope: tuple[str, ...]
    state_epoch: int
    state_digest: str


class S1StateFabric:
    """Request/component-scoped S1 fabric with fail-closed coordinator-only writes."""

    def __init__(self, initial_state: Mapping[str, Any]):
        if not isinstance(initial_state, Mapping):
            raise SharedStateError("initial_state:MAPPING_REQUIRED")
        self._epoch = 0
        self._state = self._validated_state(initial_state)
        self._digest = self._state_digest(self._epoch, self._state)

    @staticmethod
    def _validated_state(state: Mapping[str, Any]) -> dict[str, Any]:
        roots = set(state)
        forbidden = roots & FORBIDDEN_S1_ROOTS
        if forbidden:
            raise SharedStateError(f"S1_FORBIDDEN_ROOT:{','.join(sorted(forbidden))}")
        copied = copy.deepcopy(dict(state))
        _canonical_bytes(copied)
        tasks = copied.get("tasks", [])
        if not isinstance(tasks, list):
            raise SharedStateError("tasks:LIST_REQUIRED")
        seen: set[str] = set()
        for task in tasks:
            if not isinstance(task, Mapping):
                raise SharedStateError("task:MAPPING_REQUIRED")
            task_id = _nonempty(task.get("task_id"), "task_id")
            if task_id in seen:
                raise SharedStateError("task_id:DUPLICATE")
            seen.add(task_id)
            priority = task.get("priority", 0)
            if isinstance(priority, bool) or not isinstance(priority, int):
                raise SharedStateError("task.priority:INT_REQUIRED")
            _capabilities(task.get("required_capabilities", []))
            status = task.get("status", "PENDING")
            if status not in {"PENDING", "IN_FLIGHT", "DONE", "BLOCKED"}:
                raise SharedStateError("task.status:UNSUPPORTED")
            claimed_by = task.get("claimed_by")
            if claimed_by is not None:
                _nonempty(claimed_by, "task.claimed_by")
        return copied

    @staticmethod
    def _state_digest(epoch: int, state: Mapping[str, Any]) -> str:
        return _sha256({"schema": S1_SCHEMA, "epoch": epoch, "state": state})

    def read_snapshot(self) -> SharedStateSnapshot:
        return SharedStateSnapshot(S1_SCHEMA, self._epoch, self._digest, copy.deepcopy(self._state))

    def autonomous_boot(self, node: NodeDescriptor, *, admitted_capabilities: Sequence[str]) -> BootSession:
        if not isinstance(node, NodeDescriptor):
            raise SharedStateError("node:NODE_DESCRIPTOR_REQUIRED")
        if not node.healthy:
            raise SharedStateError("NODE_UNHEALTHY")
        authority_caps = set(_capabilities(admitted_capabilities))
        if not set(node.capabilities) <= authority_caps:
            raise SharedStateError("NODE_CAPABILITY_NOT_ADMITTED")
        snap = self.read_snapshot()
        candidates: list[tuple[int, str]] = []
        node_caps = set(node.capabilities)
        for raw in snap.state.get("tasks", []):
            required = set(raw.get("required_capabilities", []))
            if raw.get("status", "PENDING") != "PENDING" or raw.get("claimed_by") is not None:
                continue
            if not required <= node_caps:
                continue
            candidates.append((-int(raw.get("priority", 0)), str(raw["task_id"])))
        candidates.sort()
        selected = candidates[0][1] if candidates else None
        reason = "HIGHEST_PRIORITY_CAPABLE_UNCLAIMED" if selected else "NO_CAPABLE_UNCLAIMED_TASK"
        return BootSession(BOOT_SCHEMA, node.node_id, "ORDINARY", snap.epoch, snap.digest, selected, reason)

    def emit_node_result(self, boot: BootSession, *, task_id: str, payload_ref: str, payload: Any) -> NodeResult:
        if boot.role != "ORDINARY":
            raise SharedStateError("NODE_RESULT_REQUIRES_ORDINARY_BOOT")
        task_id = _nonempty(task_id, "task_id")
        payload_ref = _nonempty(payload_ref, "payload_ref")
        payload_sha = _sha256(payload)
        result_id = _sha256({
            "schema": NODE_RESULT_SCHEMA,
            "node_id": boot.node_id,
            "task_id": task_id,
            "state_epoch": boot.state_epoch,
            "state_digest": boot.state_digest,
            "payload_ref": payload_ref,
            "payload_sha256": payload_sha,
        })
        return NodeResult(NODE_RESULT_SCHEMA, result_id, boot.node_id, task_id, boot.state_epoch, boot.state_digest, payload_ref, payload_sha)

    def validate_result_current(self, result: NodeResult) -> None:
        if result.state_epoch != self._epoch or result.state_digest != self._digest:
            raise SharedStateError("STALE_NODE_RESULT")

    @staticmethod
    def select_coordinator(nodes: Sequence[NodeDescriptor], *, required_capability: str = "S1_COORDINATE") -> NodeDescriptor:
        required_capability = _nonempty(required_capability, "required_capability")
        eligible = [n for n in nodes if n.healthy and required_capability in n.capabilities]
        if not eligible:
            raise SharedStateError("NO_ELIGIBLE_COORDINATOR")
        return sorted(eligible, key=lambda n: (n.load_milli, n.node_id))[0]

    def issue_coordinator_lease(self, node: NodeDescriptor, *, nodes: Sequence[NodeDescriptor], scope: Sequence[str]) -> CoordinatorLease:
        winner = self.select_coordinator(nodes)
        if winner.node_id != node.node_id:
            raise SharedStateError("NODE_NOT_DETERMINISTIC_COORDINATOR")
        normalized_scope = _capabilities(scope)
        if not normalized_scope:
            raise SharedStateError("scope:NONEMPTY_REQUIRED")
        if any(root in FORBIDDEN_S1_ROOTS for root in normalized_scope):
            raise SharedStateError("LEASE_SCOPE_CANNOT_GRANT_S0_AUTHORITY")
        lease_id = _sha256({
            "schema": COORDINATOR_LEASE_SCHEMA,
            "node_id": node.node_id,
            "scope": list(normalized_scope),
            "state_epoch": self._epoch,
            "state_digest": self._digest,
        })
        return CoordinatorLease(COORDINATOR_LEASE_SCHEMA, lease_id, node.node_id, normalized_scope, self._epoch, self._digest)

    def publish_from_ordinary(self, *_: Any, **__: Any) -> None:
        raise SharedStateError("ORDINARY_NODE_S1_WRITE_FORBIDDEN")

    def publish_delta(self, lease: CoordinatorLease, *, node_id: str, delta: Mapping[str, Any]) -> SharedStateSnapshot:
        node_id = _nonempty(node_id, "node_id")
        if lease.schema != COORDINATOR_LEASE_SCHEMA:
            raise SharedStateError("COORDINATOR_LEASE_SCHEMA_UNSUPPORTED")
        if lease.node_id != node_id:
            raise SharedStateError("COORDINATOR_LEASE_NODE_MISMATCH")
        if lease.state_epoch != self._epoch or lease.state_digest != self._digest:
            raise SharedStateError("STALE_COORDINATOR_LEASE")
        if not isinstance(delta, Mapping) or not delta:
            raise SharedStateError("delta:NONEMPTY_MAPPING_REQUIRED")
        roots = set(delta)
        if roots & FORBIDDEN_S1_ROOTS:
            raise SharedStateError("S1_DELTA_ATTEMPTS_S0_AUTHORITY")
        unauthorized = roots - set(lease.scope)
        if unauthorized:
            raise SharedStateError(f"S1_DELTA_OUT_OF_SCOPE:{','.join(sorted(unauthorized))}")
        next_state = copy.deepcopy(self._state)
        for key, value in delta.items():
            next_state[key] = copy.deepcopy(value)
        next_state = self._validated_state(next_state)
        self._epoch += 1
        self._state = next_state
        self._digest = self._state_digest(self._epoch, self._state)
        return self.read_snapshot()
