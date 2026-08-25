#!/usr/bin/env python3
"""Deterministic S1 shared-state / autonomous-boot component for EntityOS/HCU Xeno.

Component scope only. S1 is noncanonical cognitive workspace state. This module
never grants S0 truth/effect/security authority and never performs model/provider I/O.

The module deliberately reuses the repository RFC8785/JCS canonicalizer rather than
creating a second digest authority. Ordinary nodes are read-only. A selected task
must be coordinator-claimed in S1 before a node may emit NODE_RESULT/v1. Coordinator
writes require a deterministic lease bound to externally admitted capability policy,
current S1 epoch, and current S1 digest.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
from pathlib import Path
import sys
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

HCU_DIR = Path(__file__).resolve().parent
if str(HCU_DIR) not in sys.path:
    sys.path.insert(0, str(HCU_DIR))


def _import_exact_repo_module(name: str, expected_path: Path):
    module = importlib.import_module(name)
    raw_path = getattr(module, "__file__", None)
    if not raw_path:
        raise RuntimeError(f"XENO_S1_AUTHORITY_MODULE_PATH_MISSING:{name}")
    loaded = Path(raw_path).resolve()
    expected = expected_path.resolve()
    if loaded != expected:
        raise RuntimeError(f"XENO_S1_AUTHORITY_MODULE_SHADOWED:{name}:{loaded}:{expected}")
    return module


_canonicalization = _import_exact_repo_module(
    "entry_canonicalization_v1", HCU_DIR / "entry_canonicalization_v1.py"
)
canonicalize = _canonicalization.canonicalize
CanonicalizationError = _canonicalization.CanonicalizationError

S1_SCHEMA = "ENTITYOS_HCU_S1_STATE/v1"
BOOT_SCHEMA = "XENO_AUTONOMOUS_BOOT/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
COORDINATOR_LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v1"
COORDINATOR_POLICY_VERSION = "XENO_COORDINATOR_POLICY/v1"

# Normalized (lowercase, underscores/hyphens removed) authority-bearing keys.
FORBIDDEN_S1_KEYS = frozenset(
    {
        "s0",
        "canonical",
        "canonicaltruth",
        "truth",
        "effect",
        "effects",
        "effectauthority",
        "effectjournal",
        "effectgate",
        "secret",
        "secrets",
        "credential",
        "credentials",
        "permission",
        "permissions",
        "security",
    }
)


class SharedStateError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    """Use the exact repository RFC8785/JCS canonicalizer for component identity."""
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise SharedStateError(f"NONCANONICAL_STATE:{exc}") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SharedStateError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _hex_digest(value: Any, field: str) -> str:
    text = _nonempty(value, field)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise SharedStateError(f"{field}:SHA256_HEX_REQUIRED")
    return text


def _capabilities(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise SharedStateError("capabilities:SEQUENCE_REQUIRED")
    rows = [_nonempty(v, "capability") for v in values]
    out = tuple(sorted(set(rows)))
    if len(out) != len(rows):
        raise SharedStateError("capabilities:DUPLICATE_FORBIDDEN")
    return out


def _normalize_authority_key(value: Any) -> str:
    return str(value).lower().replace("_", "").replace("-", "")


def _find_forbidden_authority_field(value: Any, path: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _normalize_authority_key(key) in FORBIDDEN_S1_KEYS:
                return f"{path}.{key}"
            nested = _find_forbidden_authority_field(item, f"{path}.{key}")
            if nested:
                return nested
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested = _find_forbidden_authority_field(item, f"{path}[{index}]")
            if nested:
                return nested
    return None


def _normalize_admitted_capabilities(
    admitted_capabilities_by_node: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, ...]]:
    if not isinstance(admitted_capabilities_by_node, Mapping):
        raise SharedStateError("admitted_capabilities_by_node:MAPPING_REQUIRED")
    normalized: dict[str, tuple[str, ...]] = {}
    for raw_node_id, raw_caps in admitted_capabilities_by_node.items():
        node_id = _nonempty(raw_node_id, "admitted.node_id")
        if node_id in normalized:
            raise SharedStateError("admitted.node_id:DUPLICATE")
        normalized[node_id] = _capabilities(raw_caps)
    return normalized


def capability_authority_binding(
    admitted_capabilities_by_node: Mapping[str, Sequence[str]],
    *,
    policy_version: str = COORDINATOR_POLICY_VERSION,
) -> str:
    policy_version = _nonempty(policy_version, "policy_version")
    normalized = _normalize_admitted_capabilities(admitted_capabilities_by_node)
    return _sha256(
        {
            "schema": "XENO_CAPABILITY_AUTHORITY_BINDING/v1",
            "policy_version": policy_version,
            "admitted_capabilities_by_node": {
                node_id: list(caps) for node_id, caps in sorted(normalized.items())
            },
        }
    )


@dataclass(frozen=True)
class NodeDescriptor:
    node_id: str
    capabilities: tuple[str, ...]
    healthy: bool = True
    load_milli: int = 0

    @classmethod
    def admit(
        cls,
        node_id: str,
        capabilities: Sequence[str],
        *,
        healthy: bool = True,
        load_milli: int = 0,
    ) -> "NodeDescriptor":
        node_id = _nonempty(node_id, "node_id")
        if not isinstance(healthy, bool):
            raise SharedStateError("healthy:BOOL_REQUIRED")
        if isinstance(load_milli, bool) or not isinstance(load_milli, int) or load_milli < 0:
            raise SharedStateError("load_milli:NONNEGATIVE_INT_REQUIRED")
        return cls(
            node_id=node_id,
            capabilities=_capabilities(capabilities),
            healthy=healthy,
            load_milli=load_milli,
        )


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
    policy_version: str
    authority_binding_sha256: str


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
        copied = copy.deepcopy(dict(state))
        forbidden = _find_forbidden_authority_field(copied)
        if forbidden:
            raise SharedStateError(f"S1_FORBIDDEN_AUTHORITY_FIELD:{forbidden}")
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
            if status == "PENDING" and claimed_by is not None:
                raise SharedStateError("PENDING_TASK_CANNOT_BE_CLAIMED")
            if status == "IN_FLIGHT" and claimed_by is None:
                raise SharedStateError("IN_FLIGHT_TASK_REQUIRES_CLAIMED_BY")
        return copied

    @staticmethod
    def _state_digest(epoch: int, state: Mapping[str, Any]) -> str:
        return _sha256({"schema": S1_SCHEMA, "epoch": epoch, "state": state})

    def read_snapshot(self) -> SharedStateSnapshot:
        return SharedStateSnapshot(
            S1_SCHEMA,
            self._epoch,
            self._digest,
            copy.deepcopy(self._state),
        )

    def autonomous_boot(
        self,
        node: NodeDescriptor,
        *,
        admitted_capabilities: Sequence[str],
    ) -> BootSession:
        if not isinstance(node, NodeDescriptor):
            raise SharedStateError("node:NODE_DESCRIPTOR_REQUIRED")
        if not node.healthy:
            raise SharedStateError("NODE_UNHEALTHY")
        authority_caps = set(_capabilities(admitted_capabilities))
        if not set(node.capabilities) <= authority_caps:
            raise SharedStateError("NODE_CAPABILITY_NOT_ADMITTED")
        snap = self.read_snapshot()
        node_caps = set(node.capabilities)

        # Rejoin/restart first: resume already coordinator-claimed work for this node.
        resumable: list[tuple[int, str]] = []
        for raw in snap.state.get("tasks", []):
            required = set(raw.get("required_capabilities", []))
            if (
                raw.get("status") == "IN_FLIGHT"
                and raw.get("claimed_by") == node.node_id
                and required <= node_caps
            ):
                resumable.append((-int(raw.get("priority", 0)), str(raw["task_id"])))
        resumable.sort()
        if resumable:
            return BootSession(
                BOOT_SCHEMA,
                node.node_id,
                "ORDINARY",
                snap.epoch,
                snap.digest,
                resumable[0][1],
                "RESUME_OWN_COORDINATOR_CLAIM",
            )

        candidates: list[tuple[int, str]] = []
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
        return BootSession(
            BOOT_SCHEMA,
            node.node_id,
            "ORDINARY",
            snap.epoch,
            snap.digest,
            selected,
            reason,
        )

    def emit_node_result(
        self,
        boot: BootSession,
        *,
        task_id: str,
        payload_ref: str,
        payload: Any,
    ) -> NodeResult:
        if boot.schema != BOOT_SCHEMA or boot.role != "ORDINARY":
            raise SharedStateError("NODE_RESULT_REQUIRES_ORDINARY_BOOT")
        task_id = _nonempty(task_id, "task_id")
        payload_ref = _nonempty(payload_ref, "payload_ref")
        if boot.selected_task_id is None or task_id != boot.selected_task_id:
            raise SharedStateError("NODE_RESULT_TASK_MUST_MATCH_BOOT_SELECTION")
        if boot.state_epoch != self._epoch or boot.state_digest != self._digest:
            raise SharedStateError("STALE_BOOT_SESSION")
        matching = [
            raw
            for raw in self._state.get("tasks", [])
            if raw.get("task_id") == task_id
        ]
        if len(matching) != 1:
            raise SharedStateError("NODE_RESULT_TASK_NOT_FOUND")
        task = matching[0]
        if task.get("status") != "IN_FLIGHT" or task.get("claimed_by") != boot.node_id:
            raise SharedStateError("NODE_RESULT_REQUIRES_COORDINATOR_ADMITTED_CLAIM")
        payload_sha = _sha256(payload)
        result_id = _sha256(
            {
                "schema": NODE_RESULT_SCHEMA,
                "node_id": boot.node_id,
                "task_id": task_id,
                "state_epoch": boot.state_epoch,
                "state_digest": boot.state_digest,
                "payload_ref": payload_ref,
                "payload_sha256": payload_sha,
                "canonical_truth": False,
                "effect_authority": False,
            }
        )
        return NodeResult(
            NODE_RESULT_SCHEMA,
            result_id,
            boot.node_id,
            task_id,
            boot.state_epoch,
            boot.state_digest,
            payload_ref,
            payload_sha,
        )

    def validate_result_current(self, result: NodeResult) -> None:
        if result.state_epoch != self._epoch or result.state_digest != self._digest:
            raise SharedStateError("STALE_NODE_RESULT")

    @staticmethod
    def select_coordinator(
        nodes: Sequence[NodeDescriptor],
        *,
        admitted_capabilities_by_node: Mapping[str, Sequence[str]],
        required_capability: str = "S1_COORDINATE",
    ) -> NodeDescriptor:
        required_capability = _nonempty(required_capability, "required_capability")
        admitted = _normalize_admitted_capabilities(admitted_capabilities_by_node)
        eligible: list[NodeDescriptor] = []
        for node in nodes:
            authority_caps = set(admitted.get(node.node_id, ()))
            if not set(node.capabilities) <= authority_caps:
                continue
            if node.healthy and required_capability in authority_caps:
                eligible.append(node)
        if not eligible:
            raise SharedStateError("NO_ELIGIBLE_COORDINATOR")
        return sorted(eligible, key=lambda n: (n.load_milli, n.node_id))[0]

    def issue_coordinator_lease(
        self,
        node: NodeDescriptor,
        *,
        nodes: Sequence[NodeDescriptor],
        scope: Sequence[str],
        admitted_capabilities_by_node: Mapping[str, Sequence[str]],
        authority_binding_sha256: str,
        policy_version: str = COORDINATOR_POLICY_VERSION,
    ) -> CoordinatorLease:
        policy_version = _nonempty(policy_version, "policy_version")
        expected_binding = capability_authority_binding(
            admitted_capabilities_by_node,
            policy_version=policy_version,
        )
        observed_binding = _hex_digest(
            authority_binding_sha256,
            "authority_binding_sha256",
        )
        if observed_binding != expected_binding:
            raise SharedStateError("COORDINATOR_AUTHORITY_BINDING_MISMATCH")
        winner = self.select_coordinator(
            nodes,
            admitted_capabilities_by_node=admitted_capabilities_by_node,
        )
        if winner.node_id != node.node_id:
            raise SharedStateError("NODE_NOT_DETERMINISTIC_COORDINATOR")
        normalized_scope = _capabilities(scope)
        if not normalized_scope:
            raise SharedStateError("scope:NONEMPTY_REQUIRED")
        if any(_normalize_authority_key(root) in FORBIDDEN_S1_KEYS for root in normalized_scope):
            raise SharedStateError("LEASE_SCOPE_CANNOT_GRANT_S0_AUTHORITY")
        lease_id = _sha256(
            {
                "schema": COORDINATOR_LEASE_SCHEMA,
                "node_id": node.node_id,
                "scope": list(normalized_scope),
                "state_epoch": self._epoch,
                "state_digest": self._digest,
                "policy_version": policy_version,
                "authority_binding_sha256": observed_binding,
            }
        )
        return CoordinatorLease(
            COORDINATOR_LEASE_SCHEMA,
            lease_id,
            node.node_id,
            normalized_scope,
            self._epoch,
            self._digest,
            policy_version,
            observed_binding,
        )

    def publish_from_ordinary(self, *_: Any, **__: Any) -> None:
        raise SharedStateError("ORDINARY_NODE_S1_WRITE_FORBIDDEN")

    def publish_delta(
        self,
        lease: CoordinatorLease,
        *,
        node_id: str,
        delta: Mapping[str, Any],
        expected_authority_binding_sha256: str,
    ) -> SharedStateSnapshot:
        node_id = _nonempty(node_id, "node_id")
        expected_binding = _hex_digest(
            expected_authority_binding_sha256,
            "expected_authority_binding_sha256",
        )
        if lease.schema != COORDINATOR_LEASE_SCHEMA:
            raise SharedStateError("COORDINATOR_LEASE_SCHEMA_UNSUPPORTED")
        if lease.node_id != node_id:
            raise SharedStateError("COORDINATOR_LEASE_NODE_MISMATCH")
        if lease.authority_binding_sha256 != expected_binding:
            raise SharedStateError("COORDINATOR_LEASE_AUTHORITY_BINDING_MISMATCH")
        if lease.state_epoch != self._epoch or lease.state_digest != self._digest:
            raise SharedStateError("STALE_COORDINATOR_LEASE")
        if not isinstance(delta, Mapping) or not delta:
            raise SharedStateError("delta:NONEMPTY_MAPPING_REQUIRED")
        forbidden = _find_forbidden_authority_field(delta)
        if forbidden:
            raise SharedStateError(f"S1_DELTA_ATTEMPTS_S0_AUTHORITY:{forbidden}")
        roots = set(delta)
        unauthorized = roots - set(lease.scope)
        if unauthorized:
            raise SharedStateError(
                f"S1_DELTA_OUT_OF_SCOPE:{','.join(sorted(unauthorized))}"
            )
        next_state = copy.deepcopy(self._state)
        for key, value in delta.items():
            next_state[key] = copy.deepcopy(value)
        next_state = self._validated_state(next_state)
        self._epoch += 1
        self._state = next_state
        self._digest = self._state_digest(self._epoch, self._state)
        return self.read_snapshot()
