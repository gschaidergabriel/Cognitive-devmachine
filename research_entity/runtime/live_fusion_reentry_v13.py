from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import threading
from typing import Iterable

from live_fusion_reentry_v1 import (
    APPLICABILITY,
    AUTHORITY,
    LiveFusionBus as DurableLogBus,
    _digest,
)

DELIVERY_INTERRUPT = "INTERRUPT_NEXT_SAFE_POINT"
DELIVERY_CHECKPOINT = "NEXT_CHECKPOINT"
DELIVERY_INDEX = "INDEX_ONLY"
RESOLUTION_DECISIONS = frozenset({"ACCEPT", "REPLAN", "NO_CHANGE", "CONFLICT", "DEFER"})
TERMINAL_RESOLUTIONS = frozenset({"ACCEPT", "REPLAN", "NO_CHANGE"})
ROUTING_VERSION = "v1.3"


@dataclass(frozen=True)
class LiveDelta:
    event_id: str
    source: str
    source_seq: int
    source_epoch: str
    semantic_keys: tuple[str, ...]
    affected_branches: tuple[str, ...]
    novelty: str
    impact: float
    urgency: float
    conflict: bool
    payload: dict
    provenance_refs: tuple[str, ...] = ()
    payload_hash: str = ""
    causal_origin_epoch: str = ""
    arrival_epoch: str = ""
    causal_origin_refs: tuple[str, ...] = ()
    applicability: str = "UNKNOWN"
    affected_work: tuple[str, ...] = ()
    affected_claims: tuple[str, ...] = ()

    def normalized(self) -> "LiveDelta":
        if not self.event_id:
            raise ValueError("event_id required")
        if self.source_seq < 0:
            raise ValueError("source_seq must be non-negative")
        if not self.source or not self.source_epoch:
            raise ValueError("source and source_epoch required")
        if not (self.semantic_keys or self.affected_branches or self.affected_work or self.affected_claims):
            raise ValueError("at least one semantic/branch/work/claim target required")
        if not 0.0 <= self.impact <= 1.0 or not 0.0 <= self.urgency <= 1.0:
            raise ValueError("impact/urgency must be within [0,1]")
        if self.applicability not in APPLICABILITY:
            raise ValueError("invalid applicability")
        computed_hash = _digest(self.payload)
        if self.payload_hash and self.payload_hash != computed_hash:
            raise ValueError("payload_hash does not match payload")
        return LiveDelta(
            event_id=self.event_id,
            source=self.source,
            source_seq=self.source_seq,
            source_epoch=self.source_epoch,
            semantic_keys=tuple(sorted(set(self.semantic_keys))),
            affected_branches=tuple(sorted(set(self.affected_branches))),
            novelty=self.novelty,
            impact=self.impact,
            urgency=self.urgency,
            conflict=self.conflict,
            payload=self.payload,
            provenance_refs=tuple(sorted(set(self.provenance_refs))),
            payload_hash=computed_hash,
            causal_origin_epoch=self.causal_origin_epoch or self.source_epoch,
            arrival_epoch=self.arrival_epoch,
            causal_origin_refs=tuple(sorted(set(self.causal_origin_refs))),
            applicability=self.applicability,
            affected_work=tuple(sorted(set(self.affected_work))),
            affected_claims=tuple(sorted(set(self.affected_claims))),
        )


@dataclass(frozen=True)
class WorkerView:
    worker_id: str
    branches: tuple[str, ...]
    active_keys: tuple[str, ...]
    active_work: tuple[str, ...] = ()
    active_claims: tuple[str, ...] = ()
    subscription_revision: str = "r1"
    plan_revision: str = "plan-unknown"

    def normalized(self) -> "WorkerView":
        if not self.worker_id:
            raise ValueError("worker_id required")
        if not self.subscription_revision:
            raise ValueError("subscription_revision required")
        return WorkerView(
            worker_id=self.worker_id,
            branches=tuple(sorted(set(self.branches))),
            active_keys=tuple(sorted(set(self.active_keys))),
            active_work=tuple(sorted(set(self.active_work))),
            active_claims=tuple(sorted(set(self.active_claims))),
            subscription_revision=self.subscription_revision,
            plan_revision=self.plan_revision,
        )


@dataclass(frozen=True)
class Delivery:
    delivery_id: str
    event_id: str
    worker_id: str
    subscription_revision: str
    bus_seq: int
    delivery_class: str
    relevance: float
    reason: str
    routing_version: str = ROUTING_VERSION
    authority: str = AUTHORITY


@dataclass(frozen=True)
class DeliveryAck:
    ack_id: str
    delivery_id: str
    event_id: str
    worker_id: str
    subscription_revision: str
    note: str = ""


@dataclass(frozen=True)
class Resolution:
    resolution_id: str
    event_id: str
    worker_id: str
    subscription_revision: str
    decision: str
    prior_plan_revision: str
    new_plan_revision: str
    basis_event_ids: tuple[str, ...]
    plan_state_hash: str
    note: str = ""

    def normalized(self) -> "Resolution":
        if not self.resolution_id:
            raise ValueError("resolution_id required")
        if self.decision not in RESOLUTION_DECISIONS:
            raise ValueError("invalid resolution decision")
        basis = tuple(sorted(set(self.basis_event_ids)))
        if self.decision in TERMINAL_RESOLUTIONS:
            if self.event_id not in basis:
                raise ValueError("terminal resolution must bind its event in basis_event_ids")
            if not self.new_plan_revision or not self.plan_state_hash:
                raise ValueError("terminal resolution requires new_plan_revision and plan_state_hash")
            if self.decision == "REPLAN" and self.new_plan_revision == self.prior_plan_revision:
                raise ValueError("REPLAN requires a new plan revision")
        return Resolution(
            resolution_id=self.resolution_id,
            event_id=self.event_id,
            worker_id=self.worker_id,
            subscription_revision=self.subscription_revision,
            decision=self.decision,
            prior_plan_revision=self.prior_plan_revision,
            new_plan_revision=self.new_plan_revision,
            basis_event_ids=basis,
            plan_state_hash=self.plan_state_hash,
            note=self.note,
        )


@dataclass(frozen=True)
class SubscriptionSnapshot:
    worker_id: str
    subscription_revision: str
    cut_bus_seq: int
    pending_delivery_ids: tuple[str, ...]


class LiveFusionBus(DurableLogBus):
    """V1.3 causal worker re-entry layered on the crash-safe V1 durability lane.

    Delivery is at-least-once. DeliveryAck proves only transport receipt. A terminal Resolution
    bound to the current subscription and exact event basis is required before an intersecting
    high-impact effect is released. Worker subscription revisions re-route unresolved history.
    """

    def __init__(self, log_path: str | Path | None = None):
        super().__init__(log_path)
        self.deltas: dict[str, LiveDelta] = {}
        self.workers: dict[str, WorkerView] = {}
        self.deliveries: dict[tuple[str, str], Delivery] = {}
        self.delivery_history: dict[str, Delivery] = {}
        self.restored_delivery_ids: set[str] = set()
        self.delivery_acks: dict[str, DeliveryAck] = {}
        self.delivery_ack_by_delivery: dict[str, str] = {}
        self.resolutions: dict[tuple[str, str], list[Resolution]] = {}
        self.resolution_ids: set[str] = set()
        self.subscription_snapshots: list[SubscriptionSnapshot] = []
        self.payload_provenance: dict[str, set[str]] = {}
        self.max_source_seq: dict[str, int] = {}
        self.event_bus_seq: dict[str, int] = {}
        self._next_bus_seq = 1
        self._lock = threading.RLock()

    def register_worker(self, worker: WorkerView, *, persist: bool = True) -> SubscriptionSnapshot:
        worker = worker.normalized()
        with self._lock:
            previous = self.workers.get(worker.worker_id)
            if previous and previous.subscription_revision == worker.subscription_revision and previous != worker:
                raise ValueError("worker profile changed without subscription_revision change")
            self.workers[worker.worker_id] = worker
            if persist:
                self._append("WORKER_REGISTER_V13", asdict(worker))
            for delta in self.deltas.values():
                self._route_one(delta, worker, persist=persist)
            cut = self._next_bus_seq - 1
            pending_ids = tuple(d.delivery_id for d in self.pending(worker.worker_id, include_index_only=True))
            snapshot = SubscriptionSnapshot(worker.worker_id, worker.subscription_revision, cut, pending_ids)
            if persist:
                self.subscription_snapshots.append(snapshot)
                self._append("SUBSCRIPTION_SNAPSHOT_V13", asdict(snapshot))
            return snapshot

    def ingest(self, delta: LiveDelta, *, persist: bool = True) -> str:
        delta = delta.normalized()
        with self._lock:
            existing = self.deltas.get(delta.event_id)
            if existing:
                if existing == delta:
                    return "DEDUPED_EVENT_ID"
                raise ValueError("event_id collision with different event content")
            prev = self.max_source_seq.get(delta.source)
            if prev is not None and delta.source_seq < prev:
                status = "INGESTED_LATE"
            else:
                status = "INGESTED"
                self.max_source_seq[delta.source] = delta.source_seq
            self.deltas[delta.event_id] = delta
            self.event_bus_seq[delta.event_id] = self._next_bus_seq
            self._next_bus_seq += 1
            self.payload_provenance.setdefault(delta.payload_hash, set()).update(delta.provenance_refs)
            if persist:
                self._append("DELTA_INGEST_V13", asdict(delta))
            for worker in self.workers.values():
                self._route_one(delta, worker, persist=persist)
            return status

    @staticmethod
    def _score(delta: LiveDelta, worker: WorkerView) -> tuple[float, str]:
        branch_overlap = set(delta.affected_branches) & set(worker.branches)
        key_overlap = set(delta.semantic_keys) & set(worker.active_keys)
        work_overlap = set(delta.affected_work) & set(worker.active_work)
        claim_overlap = set(delta.affected_claims) & set(worker.active_claims)
        if not (branch_overlap or key_overlap or work_overlap or claim_overlap):
            return 0.0, "no semantic/branch/work/claim overlap"
        overlap = min(
            1.0,
            0.30 * bool(branch_overlap)
            + 0.40 * bool(key_overlap)
            + 0.45 * bool(work_overlap)
            + 0.45 * bool(claim_overlap),
        )
        score = min(1.0, 0.45 * overlap + 0.35 * delta.impact + 0.20 * delta.urgency)
        reason = (
            f"branch_overlap={sorted(branch_overlap)} key_overlap={sorted(key_overlap)} "
            f"work_overlap={sorted(work_overlap)} claim_overlap={sorted(claim_overlap)} "
            f"impact={delta.impact:.2f} urgency={delta.urgency:.2f} applicability={delta.applicability}"
        )
        return score, reason

    def _route_one(self, delta: LiveDelta, worker: WorkerView, *, persist: bool) -> Delivery:
        key = (delta.event_id, worker.worker_id)
        existing = self.deliveries.get(key)
        if existing and existing.subscription_revision == worker.subscription_revision:
            return existing
        relevance, reason = self._score(delta, worker)
        if relevance == 0.0 or delta.applicability == "HISTORICALLY_VALID_ONLY":
            delivery_class = DELIVERY_INDEX
        elif delta.conflict and delta.impact >= 0.70 and relevance >= 0.45:
            delivery_class = DELIVERY_INTERRUPT
        else:
            delivery_class = DELIVERY_CHECKPOINT
        delivery = Delivery(
            delivery_id="delivery-" + _digest([delta.event_id, worker.worker_id, worker.subscription_revision])[:20],
            event_id=delta.event_id,
            worker_id=worker.worker_id,
            subscription_revision=worker.subscription_revision,
            bus_seq=self.event_bus_seq[delta.event_id],
            delivery_class=delivery_class,
            relevance=relevance,
            reason=reason,
        )
        self.deliveries[key] = delivery
        self.delivery_history[delivery.delivery_id] = delivery
        if persist:
            self._append("DELIVERY_V13", asdict(delivery))
        return delivery

    def _restore_delivery(self, payload: dict) -> Delivery:
        payload = dict(payload)
        payload.setdefault("routing_version", ROUTING_VERSION)
        delivery = Delivery(**payload)
        delta = self.deltas.get(delivery.event_id)
        worker = self.workers.get(delivery.worker_id)
        if not delta:
            raise ValueError("recorded delivery references unknown event")
        if not worker or worker.subscription_revision != delivery.subscription_revision:
            raise ValueError("recorded delivery references unknown/stale subscription")
        if self.event_bus_seq.get(delivery.event_id) != delivery.bus_seq:
            raise ValueError("recorded delivery bus_seq mismatch")
        if delivery.authority != AUTHORITY:
            raise ValueError("recorded delivery authority mismatch")
        existing = self.delivery_history.get(delivery.delivery_id)
        if delivery.delivery_id in self.restored_delivery_ids and existing != delivery:
            raise ValueError("recorded delivery_id collision")
        self.restored_delivery_ids.add(delivery.delivery_id)
        self.delivery_history[delivery.delivery_id] = delivery
        self.deliveries[(delivery.event_id, delivery.worker_id)] = delivery
        return delivery

    def _restore_subscription_snapshot(self, payload: dict) -> SubscriptionSnapshot:
        payload = dict(payload)
        payload["pending_delivery_ids"] = tuple(payload.get("pending_delivery_ids", ()))
        snapshot = SubscriptionSnapshot(**payload)
        worker = self.workers.get(snapshot.worker_id)
        if not worker or worker.subscription_revision != snapshot.subscription_revision:
            raise ValueError("snapshot references unknown/stale subscription")
        self.subscription_snapshots.append(snapshot)
        return snapshot

    def current_delivery(self, event_id: str, worker_id: str) -> Delivery:
        return self.deliveries[(event_id, worker_id)]

    def ack_delivery(self, ack: DeliveryAck, *, persist: bool = True) -> str:
        with self._lock:
            if not ack.ack_id or not ack.delivery_id:
                raise ValueError("ack_id and delivery_id required")
            delivery = self.deliveries.get((ack.event_id, ack.worker_id))
            if not delivery or delivery.delivery_id != ack.delivery_id:
                raise KeyError("unknown or stale delivery")
            if delivery.subscription_revision != ack.subscription_revision:
                raise ValueError("delivery ACK subscription revision mismatch")
            previous_ack_id = self.delivery_ack_by_delivery.get(ack.delivery_id)
            if previous_ack_id:
                existing = self.delivery_acks[previous_ack_id]
                if existing == ack:
                    return "ACK_IDEMPOTENT"
                raise ValueError("conflicting ACK for delivery")
            if ack.ack_id in self.delivery_acks:
                raise ValueError("ack_id already used")
            self.delivery_acks[ack.ack_id] = ack
            self.delivery_ack_by_delivery[ack.delivery_id] = ack.ack_id
            if persist:
                self._append("DELIVERY_ACK_V13", asdict(ack))
            return "ACKED"

    def resolve(self, resolution: Resolution, *, persist: bool = True) -> str:
        resolution = resolution.normalized()
        with self._lock:
            if resolution.resolution_id in self.resolution_ids:
                for rows in self.resolutions.values():
                    for existing in rows:
                        if existing.resolution_id == resolution.resolution_id:
                            if existing == resolution:
                                return "RESOLUTION_IDEMPOTENT"
                            raise ValueError("resolution_id collision")
            delivery = self.deliveries.get((resolution.event_id, resolution.worker_id))
            if not delivery:
                raise KeyError("unknown event/worker delivery")
            if delivery.subscription_revision != resolution.subscription_revision:
                raise ValueError("resolution subscription revision is stale")
            self.resolution_ids.add(resolution.resolution_id)
            self.resolutions.setdefault((resolution.event_id, resolution.worker_id), []).append(resolution)
            if persist:
                self._append("RESOLUTION_V13", asdict(resolution))
            return "RESOLVED" if resolution.decision in TERMINAL_RESOLUTIONS else "RECORDED_OPEN"

    def _terminal_resolution_for(self, delivery: Delivery) -> Resolution | None:
        for row in reversed(self.resolutions.get((delivery.event_id, delivery.worker_id), [])):
            if row.subscription_revision != delivery.subscription_revision:
                continue
            if row.decision in TERMINAL_RESOLUTIONS and delivery.event_id in row.basis_event_ids:
                return row
        return None

    def pending(self, worker_id: str, *, include_index_only: bool = False) -> list[Delivery]:
        pending: list[Delivery] = []
        for delivery in self.deliveries.values():
            if delivery.worker_id != worker_id or self._terminal_resolution_for(delivery):
                continue
            if not include_index_only and delivery.delivery_class == DELIVERY_INDEX:
                continue
            pending.append(delivery)
        priority = {DELIVERY_INTERRUPT: 0, DELIVERY_CHECKPOINT: 1, DELIVERY_INDEX: 2}
        return sorted(pending, key=lambda d: (priority[d.delivery_class], d.bus_seq, d.event_id))

    def effect_guard(
        self,
        worker_id: str,
        effect_keys: Iterable[str] = (),
        effect_work: Iterable[str] = (),
        effect_claims: Iterable[str] = (),
    ) -> tuple[bool, list[str]]:
        key_scope, work_scope, claim_scope = set(effect_keys), set(effect_work), set(effect_claims)
        blockers = []
        for delivery in self.pending(worker_id):
            if delivery.delivery_class != DELIVERY_INTERRUPT:
                continue
            delta = self.deltas[delivery.event_id]
            if (
                key_scope & set(delta.semantic_keys)
                or work_scope & set(delta.affected_work)
                or claim_scope & set(delta.affected_claims)
            ):
                blockers.append(delta.event_id)
        return not blockers, sorted(blockers)

    @classmethod
    def replay(cls, log_path: str | Path) -> "LiveFusionBus":
        bus = cls(log_path)
        rows, recovery = cls._decode_log(Path(log_path))
        bus.recovery_events.extend(recovery)
        for row in rows:
            kind, payload = row["kind"], row["payload"]
            if kind == "WORKER_REGISTER_V13":
                for name in ("branches", "active_keys", "active_work", "active_claims"):
                    payload[name] = tuple(payload.get(name, ()))
                bus.register_worker(WorkerView(**payload), persist=False)
            elif kind == "DELTA_INGEST_V13":
                for name in (
                    "semantic_keys", "affected_branches", "provenance_refs", "causal_origin_refs",
                    "affected_work", "affected_claims",
                ):
                    payload[name] = tuple(payload.get(name, ()))
                bus.ingest(LiveDelta(**payload), persist=False)
            elif kind == "DELIVERY_V13":
                bus._restore_delivery(payload)
            elif kind == "SUBSCRIPTION_SNAPSHOT_V13":
                bus._restore_subscription_snapshot(payload)
            elif kind == "DELIVERY_ACK_V13":
                bus.ack_delivery(DeliveryAck(**payload), persist=False)
            elif kind == "RESOLUTION_V13":
                payload["basis_event_ids"] = tuple(payload.get("basis_event_ids", ()))
                bus.resolve(Resolution(**payload), persist=False)
        return bus
