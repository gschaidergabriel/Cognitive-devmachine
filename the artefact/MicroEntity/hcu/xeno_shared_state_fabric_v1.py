from __future__ import annotations

"""Deterministic Xeno/HCU shared-state control primitive.

Implements the first owner-locked Xeno/HCU path without creating a second truth store:
autonomous node boot/read, deterministic work selection, ephemeral NODE_RESULT packets,
deterministic GRID_COORDINATOR_LEASE selection, and coordinator-only compare-and-swap
updates to noncanonical S1 cognitive state.

S1 remains noncanonical cognition/workspace state. Nothing here grants S0 truth, effect,
security, secret, or canonical durable-state authority.
"""

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

S1_SNAPSHOT_SCHEMA = "ENTITYOS_HCU_S1_SNAPSHOT/v1"
NODE_SESSION_SCHEMA = "ENTITYOS_HCU_XENO_NODE_SESSION/v1"
WORK_SELECTION_SCHEMA = "ENTITYOS_HCU_WORK_SELECTION/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
COORDINATOR_LEASE_SCHEMA = "GRID_COORDINATOR_LEASE/v1"
S1_COMMIT_RECEIPT_SCHEMA = "ENTITYOS_HCU_S1_COMMIT_RECEIPT/v1"

MAX_SAFE_INT = 9_007_199_254_740_991
WORK_STATES = {"READY", "CLAIMED", "DONE", "BLOCKED"}
BRANCH_STATES = {"UNRESOLVED", "RESOLVED"}


class SharedStateError(ValueError):
    pass


def _hash(material: Any, field: str = "material") -> str:
    try:
        return hashlib.sha256(canonicalize(material)).hexdigest()
    except CanonicalizationError as exc:
        raise SharedStateError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _text(value: Any, field: str, *, max_bytes: int = 512) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SharedStateError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value.encode("utf-8", "strict")) > max_bytes:
        raise SharedStateError(f"{field}:TOO_LONG")
    return value


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        raise SharedStateError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if any(ch not in "0123456789abcdef" for ch in value):
        raise SharedStateError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _uint(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > MAX_SAFE_INT:
        raise SharedStateError(f"{field}:JCS_SAFE_NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _strings(values: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise SharedStateError(f"{field}:SEQUENCE_REQUIRED")
    out = tuple(sorted(_text(v, field) for v in values))
    if len(out) != len(set(out)):
        raise SharedStateError(f"{field}:DUPLICATE_FORBIDDEN")
    return out


@dataclass(frozen=True)
class WorkItem:
    task_id: str
    branch_id: str
    priority: int
    payload_ref: str
    payload_sha256: str
    state: str = "READY"
    claimed_by: str | None = None


@dataclass(frozen=True)
class HyperpositionBranchRef:
    branch_id: str
    evidence_sha256: str
    state: str = "UNRESOLVED"


@dataclass(frozen=True)
class GWTBroadcastRef:
    broadcast_id: str
    trace_sha256: str
    uptake_node_ids: tuple[str, ...] = ()
    reentry_node_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class S1Snapshot:
    schema: str
    canonicalization_schema: str
    generation: int
    epoch: int
    policy_sha256: str
    previous_snapshot_sha256: str | None
    work_items: tuple[WorkItem, ...]
    hyperposition_branches: tuple[HyperpositionBranchRef, ...]
    gwt_broadcasts: tuple[GWTBroadcastRef, ...]
    snapshot_sha256: str


@dataclass(frozen=True)
class NodeSession:
    schema: str
    node_id: str
    generation: int
    capability_binding_sha256: str
    capabilities: tuple[str, ...]
    snapshot_epoch: int
    snapshot_sha256: str
    session_sha256: str


@dataclass(frozen=True)
class WorkSelection:
    schema: str
    node_id: str
    generation: int
    snapshot_epoch: int
    snapshot_sha256: str
    task_id: str
    branch_id: str
    payload_ref: str
    payload_sha256: str
    selection_sha256: str


@dataclass(frozen=True)
class NodeResult:
    schema: str
    node_id: str
    generation: int
    snapshot_epoch: int
    snapshot_sha256: str
    task_id: str
    branch_id: str
    payload_ref: str
    payload_sha256: str
    evidence_refs: tuple[str, ...]
    result_sha256: str


@dataclass(frozen=True)
class CoordinatorLease:
    schema: str
    node_id: str
    scope: str
    generation: int
    state_epoch: int
    state_sha256: str
    policy_sha256: str
    valid_through_epoch: int
    lease_sha256: str


@dataclass(frozen=True)
class S1CommitReceipt:
    schema: str
    coordinator_node_id: str
    lease_sha256: str
    previous_epoch: int
    previous_snapshot_sha256: str
    new_epoch: int
    new_snapshot_sha256: str
    consumed_result_sha256: tuple[str, ...]
    receipt_sha256: str


def _work_material(item: WorkItem) -> dict[str, Any]:
    if not isinstance(item, WorkItem):
        raise SharedStateError("WORK_ITEM_REQUIRED")
    state = _text(item.state, "work.state")
    if state not in WORK_STATES:
        raise SharedStateError("WORK_STATE_UNSUPPORTED")
    claimed_by = item.claimed_by
    if claimed_by is not None:
        claimed_by = _text(claimed_by, "work.claimed_by")
    if state == "CLAIMED" and claimed_by is None:
        raise SharedStateError("CLAIMED_WORK_REQUIRES_CLAIMANT")
    if state == "READY" and claimed_by is not None:
        raise SharedStateError("READY_WORK_CANNOT_HAVE_CLAIMANT")
    return {
        "task_id": _text(item.task_id, "work.task_id"),
        "branch_id": _text(item.branch_id, "work.branch_id"),
        "priority": _uint(item.priority, "work.priority"),
        "payload_ref": _text(item.payload_ref, "work.payload_ref"),
        "payload_sha256": _sha(item.payload_sha256, "work.payload_sha256"),
        "state": state,
        "claimed_by": claimed_by,
    }


def _branch_material(item: HyperpositionBranchRef) -> dict[str, Any]:
    if not isinstance(item, HyperpositionBranchRef):
        raise SharedStateError("HYPERPOSITION_BRANCH_REQUIRED")
    state = _text(item.state, "branch.state")
    if state not in BRANCH_STATES:
        raise SharedStateError("HYPERPOSITION_BRANCH_STATE_UNSUPPORTED")
    return {
        "branch_id": _text(item.branch_id, "branch.branch_id"),
        "evidence_sha256": _sha(item.evidence_sha256, "branch.evidence_sha256"),
        "state": state,
    }


def _broadcast_material(item: GWTBroadcastRef) -> dict[str, Any]:
    if not isinstance(item, GWTBroadcastRef):
        raise SharedStateError("GWT_BROADCAST_REQUIRED")
    return {
        "broadcast_id": _text(item.broadcast_id, "broadcast.broadcast_id"),
        "trace_sha256": _sha(item.trace_sha256, "broadcast.trace_sha256"),
        "uptake_node_ids": list(_strings(item.uptake_node_ids, "broadcast.uptake_node_ids")),
        "reentry_node_ids": list(_strings(item.reentry_node_ids, "broadcast.reentry_node_ids")),
    }


def _snapshot_material(
    *,
    generation: int,
    epoch: int,
    policy_sha256: str,
    previous_snapshot_sha256: str | None,
    work_items: Sequence[WorkItem],
    hyperposition_branches: Sequence[HyperpositionBranchRef],
    gwt_broadcasts: Sequence[GWTBroadcastRef],
) -> dict[str, Any]:
    generation = _uint(generation, "snapshot.generation")
    epoch = _uint(epoch, "snapshot.epoch")
    policy_sha256 = _sha(policy_sha256, "snapshot.policy_sha256")
    if previous_snapshot_sha256 is not None:
        previous_snapshot_sha256 = _sha(previous_snapshot_sha256, "snapshot.previous_snapshot_sha256")
    work = sorted((_work_material(x) for x in work_items), key=lambda x: x["task_id"])
    branches = sorted((_branch_material(x) for x in hyperposition_branches), key=lambda x: x["branch_id"])
    broadcasts = sorted((_broadcast_material(x) for x in gwt_broadcasts), key=lambda x: x["broadcast_id"])
    for values, key, code in (
        (work, "task_id", "WORK_TASK_ID_DUPLICATE"),
        (branches, "branch_id", "HYPERPOSITION_BRANCH_ID_DUPLICATE"),
        (broadcasts, "broadcast_id", "GWT_BROADCAST_ID_DUPLICATE"),
    ):
        ids = [v[key] for v in values]
        if len(ids) != len(set(ids)):
            raise SharedStateError(code)
    return {
        "schema": S1_SNAPSHOT_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": generation,
        "epoch": epoch,
        "policy_sha256": policy_sha256,
        "previous_snapshot_sha256": previous_snapshot_sha256,
        "work_items": work,
        "hyperposition_branches": branches,
        "gwt_broadcasts": broadcasts,
    }


def make_snapshot(
    *,
    generation: int,
    epoch: int,
    policy_sha256: str,
    previous_snapshot_sha256: str | None = None,
    work_items: Sequence[WorkItem] = (),
    hyperposition_branches: Sequence[HyperpositionBranchRef] = (),
    gwt_broadcasts: Sequence[GWTBroadcastRef] = (),
) -> S1Snapshot:
    material = _snapshot_material(
        generation=generation,
        epoch=epoch,
        policy_sha256=policy_sha256,
        previous_snapshot_sha256=previous_snapshot_sha256,
        work_items=work_items,
        hyperposition_branches=hyperposition_branches,
        gwt_broadcasts=gwt_broadcasts,
    )
    digest = _hash(material, "snapshot")
    return S1Snapshot(
        schema=S1_SNAPSHOT_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        generation=material["generation"],
        epoch=material["epoch"],
        policy_sha256=material["policy_sha256"],
        previous_snapshot_sha256=material["previous_snapshot_sha256"],
        work_items=tuple(sorted(work_items, key=lambda x: x.task_id)),
        hyperposition_branches=tuple(sorted(hyperposition_branches, key=lambda x: x.branch_id)),
        gwt_broadcasts=tuple(sorted(gwt_broadcasts, key=lambda x: x.broadcast_id)),
        snapshot_sha256=digest,
    )


def validate_snapshot(snapshot: S1Snapshot) -> str:
    if not isinstance(snapshot, S1Snapshot) or snapshot.schema != S1_SNAPSHOT_SCHEMA:
        raise SharedStateError("S1_SNAPSHOT_REQUIRED")
    if snapshot.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise SharedStateError("S1_CANONICALIZATION_SCHEMA_MISMATCH")
    material = _snapshot_material(
        generation=snapshot.generation,
        epoch=snapshot.epoch,
        policy_sha256=snapshot.policy_sha256,
        previous_snapshot_sha256=snapshot.previous_snapshot_sha256,
        work_items=snapshot.work_items,
        hyperposition_branches=snapshot.hyperposition_branches,
        gwt_broadcasts=snapshot.gwt_broadcasts,
    )
    expected = _hash(material, "snapshot")
    if _sha(snapshot.snapshot_sha256, "snapshot.snapshot_sha256") != expected:
        raise SharedStateError("S1_SNAPSHOT_DIGEST_MISMATCH")
    return expected


def boot_node(
    snapshot: S1Snapshot,
    *,
    node_id: str,
    current_generation: int,
    capability_binding_sha256: str,
    admitted_capabilities_by_node: Mapping[str, Sequence[str]],
) -> NodeSession:
    validate_snapshot(snapshot)
    node_id = _text(node_id, "node_id")
    if snapshot.generation != _uint(current_generation, "current_generation"):
        raise SharedStateError("NODE_BOOT_STALE_GENERATION")
    if not isinstance(admitted_capabilities_by_node, Mapping):
        raise SharedStateError("NODE_CAPABILITY_AUTHORITY_MAPPING_REQUIRED")
    admitted = admitted_capabilities_by_node.get(node_id)
    if admitted is None:
        raise SharedStateError("NODE_NOT_ADMITTED")
    capabilities = _strings(tuple(admitted), "node.capabilities")
    if "hcu.s1.read" not in capabilities:
        raise SharedStateError("NODE_S1_READ_CAPABILITY_REQUIRED")
    binding = _sha(capability_binding_sha256, "node.capability_binding_sha256")
    material = {
        "schema": NODE_SESSION_SCHEMA,
        "node_id": node_id,
        "generation": snapshot.generation,
        "capability_binding_sha256": binding,
        "capabilities": list(capabilities),
        "snapshot_epoch": snapshot.epoch,
        "snapshot_sha256": snapshot.snapshot_sha256,
    }
    return NodeSession(
        schema=NODE_SESSION_SCHEMA,
        node_id=node_id,
        generation=snapshot.generation,
        capability_binding_sha256=binding,
        capabilities=capabilities,
        snapshot_epoch=snapshot.epoch,
        snapshot_sha256=snapshot.snapshot_sha256,
        session_sha256=_hash(material, "node_session"),
    )


def _validate_session(session: NodeSession, snapshot: S1Snapshot) -> None:
    validate_snapshot(snapshot)
    if not isinstance(session, NodeSession) or session.schema != NODE_SESSION_SCHEMA:
        raise SharedStateError("NODE_SESSION_REQUIRED")
    if session.generation != snapshot.generation:
        raise SharedStateError("NODE_SESSION_STALE_GENERATION")
    if session.snapshot_epoch != snapshot.epoch or session.snapshot_sha256 != snapshot.snapshot_sha256:
        raise SharedStateError("NODE_SESSION_STALE_S1_VIEW")
    material = {
        "schema": NODE_SESSION_SCHEMA,
        "node_id": _text(session.node_id, "session.node_id"),
        "generation": _uint(session.generation, "session.generation"),
        "capability_binding_sha256": _sha(session.capability_binding_sha256, "session.capability_binding_sha256"),
        "capabilities": list(_strings(session.capabilities, "session.capabilities")),
        "snapshot_epoch": _uint(session.snapshot_epoch, "session.snapshot_epoch"),
        "snapshot_sha256": _sha(session.snapshot_sha256, "session.snapshot_sha256"),
    }
    if _hash(material, "node_session") != _sha(session.session_sha256, "session.session_sha256"):
        raise SharedStateError("NODE_SESSION_DIGEST_MISMATCH")
    if "hcu.s1.read" not in session.capabilities:
        raise SharedStateError("NODE_SESSION_S1_READ_CAPABILITY_REQUIRED")


def select_work(snapshot: S1Snapshot, session: NodeSession) -> WorkSelection:
    _validate_session(session, snapshot)
    ready = [w for w in snapshot.work_items if w.state == "READY" and w.claimed_by is None]
    if not ready:
        raise SharedStateError("NO_READY_WORK")
    chosen = sorted(ready, key=lambda w: (-w.priority, w.task_id))[0]
    material = {
        "schema": WORK_SELECTION_SCHEMA,
        "node_id": session.node_id,
        "generation": snapshot.generation,
        "snapshot_epoch": snapshot.epoch,
        "snapshot_sha256": snapshot.snapshot_sha256,
        "task_id": chosen.task_id,
        "branch_id": chosen.branch_id,
        "payload_ref": chosen.payload_ref,
        "payload_sha256": chosen.payload_sha256,
    }
    return WorkSelection(selection_sha256=_hash(material, "work_selection"), **material)


def emit_node_result(
    snapshot: S1Snapshot,
    session: NodeSession,
    selection: WorkSelection,
    *,
    payload_ref: str,
    payload_sha256: str,
    evidence_refs: Sequence[str] = (),
) -> NodeResult:
    _validate_session(session, snapshot)
    if not isinstance(selection, WorkSelection) or selection.schema != WORK_SELECTION_SCHEMA:
        raise SharedStateError("WORK_SELECTION_REQUIRED")
    if selection.node_id != session.node_id or selection.snapshot_sha256 != snapshot.snapshot_sha256:
        raise SharedStateError("WORK_SELECTION_SESSION_BINDING_MISMATCH")
    evidence = tuple(sorted(_sha(x, "result.evidence_ref") for x in evidence_refs))
    if len(evidence) != len(set(evidence)):
        raise SharedStateError("NODE_RESULT_EVIDENCE_DUPLICATE")
    material = {
        "schema": NODE_RESULT_SCHEMA,
        "node_id": session.node_id,
        "generation": snapshot.generation,
        "snapshot_epoch": snapshot.epoch,
        "snapshot_sha256": snapshot.snapshot_sha256,
        "task_id": _text(selection.task_id, "result.task_id"),
        "branch_id": _text(selection.branch_id, "result.branch_id"),
        "payload_ref": _text(payload_ref, "result.payload_ref"),
        "payload_sha256": _sha(payload_sha256, "result.payload_sha256"),
        "evidence_refs": list(evidence),
    }
    return NodeResult(
        result_sha256=_hash(material, "node_result"),
        evidence_refs=evidence,
        **{k: v for k, v in material.items() if k != "evidence_refs"},
    )


def validate_node_result(result: NodeResult, snapshot: S1Snapshot) -> str:
    validate_snapshot(snapshot)
    if not isinstance(result, NodeResult) or result.schema != NODE_RESULT_SCHEMA:
        raise SharedStateError("NODE_RESULT_REQUIRED")
    if result.generation != snapshot.generation:
        raise SharedStateError("NODE_RESULT_STALE_GENERATION")
    if result.snapshot_epoch != snapshot.epoch or result.snapshot_sha256 != snapshot.snapshot_sha256:
        raise SharedStateError("NODE_RESULT_STALE_S1_VIEW")
    material = {
        "schema": NODE_RESULT_SCHEMA,
        "node_id": _text(result.node_id, "result.node_id"),
        "generation": _uint(result.generation, "result.generation"),
        "snapshot_epoch": _uint(result.snapshot_epoch, "result.snapshot_epoch"),
        "snapshot_sha256": _sha(result.snapshot_sha256, "result.snapshot_sha256"),
        "task_id": _text(result.task_id, "result.task_id"),
        "branch_id": _text(result.branch_id, "result.branch_id"),
        "payload_ref": _text(result.payload_ref, "result.payload_ref"),
        "payload_sha256": _sha(result.payload_sha256, "result.payload_sha256"),
        "evidence_refs": list(_strings(result.evidence_refs, "result.evidence_refs")),
    }
    expected = _hash(material, "node_result")
    if _sha(result.result_sha256, "result.result_sha256") != expected:
        raise SharedStateError("NODE_RESULT_DIGEST_MISMATCH")
    return expected


def grant_coordinator_lease(
    snapshot: S1Snapshot,
    candidate_sessions: Sequence[NodeSession],
    *,
    scope: str,
    policy_sha256: str,
    valid_for_epochs: int = 1,
) -> CoordinatorLease:
    validate_snapshot(snapshot)
    scope = _text(scope, "lease.scope")
    policy = _sha(policy_sha256, "lease.policy_sha256")
    if policy != snapshot.policy_sha256:
        raise SharedStateError("LEASE_POLICY_SNAPSHOT_MISMATCH")
    span = _uint(valid_for_epochs, "lease.valid_for_epochs")
    if span < 1:
        raise SharedStateError("LEASE_VALID_FOR_EPOCHS_POSITIVE_REQUIRED")
    eligible: list[NodeSession] = []
    seen: set[str] = set()
    for session in candidate_sessions:
        _validate_session(session, snapshot)
        if session.node_id in seen:
            raise SharedStateError("LEASE_CANDIDATE_NODE_DUPLICATE")
        seen.add(session.node_id)
        if "hcu.coordinate.eligible" in session.capabilities:
            eligible.append(session)
    if not eligible:
        raise SharedStateError("NO_ELIGIBLE_COORDINATOR")

    def rank_material(session: NodeSession) -> dict[str, Any]:
        return {
            "schema": COORDINATOR_LEASE_SCHEMA,
            "selection": "DETERMINISTIC_HASH_RANK/v1",
            "node_id": session.node_id,
            "scope": scope,
            "generation": snapshot.generation,
            "state_epoch": snapshot.epoch,
            "state_sha256": snapshot.snapshot_sha256,
            "policy_sha256": policy,
        }

    selected = min(eligible, key=lambda s: (_hash(rank_material(s), "coordinator_rank"), s.node_id))
    valid_through = snapshot.epoch + span - 1
    if valid_through > MAX_SAFE_INT:
        raise SharedStateError("LEASE_VALID_THROUGH_EPOCH_OVERFLOW")
    material = {
        "schema": COORDINATOR_LEASE_SCHEMA,
        "node_id": selected.node_id,
        "scope": scope,
        "generation": snapshot.generation,
        "state_epoch": snapshot.epoch,
        "state_sha256": snapshot.snapshot_sha256,
        "policy_sha256": policy,
        "valid_through_epoch": valid_through,
    }
    return CoordinatorLease(lease_sha256=_hash(material, "coordinator_lease"), **material)


def _validate_lease(lease: CoordinatorLease, actor: NodeSession, snapshot: S1Snapshot) -> None:
    _validate_session(actor, snapshot)
    if not isinstance(lease, CoordinatorLease) or lease.schema != COORDINATOR_LEASE_SCHEMA:
        raise SharedStateError("VALID_COORDINATOR_LEASE_REQUIRED")
    if lease.node_id != actor.node_id:
        raise SharedStateError("COORDINATOR_LEASE_ACTOR_MISMATCH")
    if "hcu.coordinate.eligible" not in actor.capabilities:
        raise SharedStateError("COORDINATOR_ACTOR_NOT_ELIGIBLE")
    if lease.generation != snapshot.generation:
        raise SharedStateError("COORDINATOR_LEASE_STALE_GENERATION")
    if lease.state_epoch != snapshot.epoch or lease.state_sha256 != snapshot.snapshot_sha256:
        raise SharedStateError("COORDINATOR_LEASE_STALE_S1_VIEW")
    if snapshot.epoch > lease.valid_through_epoch:
        raise SharedStateError("COORDINATOR_LEASE_EXPIRED")
    if lease.policy_sha256 != snapshot.policy_sha256:
        raise SharedStateError("COORDINATOR_LEASE_POLICY_MISMATCH")
    material = {
        "schema": COORDINATOR_LEASE_SCHEMA,
        "node_id": _text(lease.node_id, "lease.node_id"),
        "scope": _text(lease.scope, "lease.scope"),
        "generation": _uint(lease.generation, "lease.generation"),
        "state_epoch": _uint(lease.state_epoch, "lease.state_epoch"),
        "state_sha256": _sha(lease.state_sha256, "lease.state_sha256"),
        "policy_sha256": _sha(lease.policy_sha256, "lease.policy_sha256"),
        "valid_through_epoch": _uint(lease.valid_through_epoch, "lease.valid_through_epoch"),
    }
    if _hash(material, "coordinator_lease") != _sha(lease.lease_sha256, "lease.lease_sha256"):
        raise SharedStateError("COORDINATOR_LEASE_DIGEST_MISMATCH")


def commit_s1_delta(
    snapshot: S1Snapshot,
    actor: NodeSession,
    lease: CoordinatorLease | None,
    *,
    consumed_results: Sequence[NodeResult] = (),
    work_updates: Sequence[WorkItem] = (),
    hyperposition_updates: Sequence[HyperpositionBranchRef] = (),
    gwt_broadcasts: Sequence[GWTBroadcastRef] = (),
) -> tuple[S1Snapshot, S1CommitReceipt]:
    if lease is None:
        raise SharedStateError("NO_VALID_COORDINATOR_LEASE_NO_S1_WRITE")
    _validate_lease(lease, actor, snapshot)

    result_hashes = [validate_node_result(result, snapshot) for result in consumed_results]
    if len(result_hashes) != len(set(result_hashes)):
        raise SharedStateError("DUPLICATE_NODE_RESULT_REJECTED")

    current_work = {w.task_id: w for w in snapshot.work_items}
    for update in work_updates:
        mat = _work_material(update)
        existing = current_work.get(mat["task_id"])
        if existing is None:
            raise SharedStateError("S1_WORK_UPDATE_UNKNOWN_TASK")
        old = _work_material(existing)
        for immutable in ("task_id", "branch_id", "priority", "payload_ref", "payload_sha256"):
            if mat[immutable] != old[immutable]:
                raise SharedStateError(f"S1_WORK_IMMUTABLE_FIELD_CHANGED:{immutable}")
        current_work[update.task_id] = update

    current_branches = {b.branch_id: b for b in snapshot.hyperposition_branches}
    for update in hyperposition_updates:
        _branch_material(update)
        existing = current_branches.get(update.branch_id)
        if existing is not None and existing.state == "RESOLVED" and update.state == "UNRESOLVED":
            raise SharedStateError("HYPERPOSITION_RESOLUTION_REVERSAL_REQUIRES_NEW_BRANCH")
        current_branches[update.branch_id] = update

    current_broadcasts = {b.broadcast_id: b for b in snapshot.gwt_broadcasts}
    for broadcast in gwt_broadcasts:
        _broadcast_material(broadcast)
        if broadcast.broadcast_id in current_broadcasts:
            raise SharedStateError("GWT_BROADCAST_DUPLICATE")
        current_broadcasts[broadcast.broadcast_id] = broadcast

    new_epoch = snapshot.epoch + 1
    if new_epoch > MAX_SAFE_INT:
        raise SharedStateError("S1_EPOCH_OVERFLOW")
    new_snapshot = make_snapshot(
        generation=snapshot.generation,
        epoch=new_epoch,
        policy_sha256=snapshot.policy_sha256,
        previous_snapshot_sha256=snapshot.snapshot_sha256,
        work_items=tuple(current_work.values()),
        hyperposition_branches=tuple(current_branches.values()),
        gwt_broadcasts=tuple(current_broadcasts.values()),
    )
    receipt_material = {
        "schema": S1_COMMIT_RECEIPT_SCHEMA,
        "coordinator_node_id": actor.node_id,
        "lease_sha256": lease.lease_sha256,
        "previous_epoch": snapshot.epoch,
        "previous_snapshot_sha256": snapshot.snapshot_sha256,
        "new_epoch": new_snapshot.epoch,
        "new_snapshot_sha256": new_snapshot.snapshot_sha256,
        "consumed_result_sha256": sorted(result_hashes),
    }
    receipt = S1CommitReceipt(
        schema=S1_COMMIT_RECEIPT_SCHEMA,
        coordinator_node_id=actor.node_id,
        lease_sha256=lease.lease_sha256,
        previous_epoch=snapshot.epoch,
        previous_snapshot_sha256=snapshot.snapshot_sha256,
        new_epoch=new_snapshot.epoch,
        new_snapshot_sha256=new_snapshot.snapshot_sha256,
        consumed_result_sha256=tuple(sorted(result_hashes)),
        receipt_sha256=_hash(receipt_material, "s1_commit_receipt"),
    )
    return new_snapshot, receipt
