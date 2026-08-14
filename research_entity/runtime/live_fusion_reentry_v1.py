from __future__ import annotations

from dataclasses import asdict, dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

DELIVERY_INTERRUPT = "INTERRUPT_NEXT_SAFE_POINT"
DELIVERY_CHECKPOINT = "NEXT_CHECKPOINT"
DELIVERY_INDEX = "INDEX_ONLY"
ACK_DECISIONS = frozenset({"ACCEPT", "REPLAN", "NO_CHANGE", "CONFLICT", "DEFER"})
APPLICABILITY = frozenset({"CURRENT_MATERIAL", "HISTORICALLY_VALID_ONLY", "UNKNOWN"})
AUTHORITY = "COORDINATION_SIGNAL_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY"
LOG_SCHEMA_VERSION = "1.1"


def _stable(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value) -> str:
    return hashlib.sha256(_stable(value).encode("utf-8")).hexdigest()


def _record(kind: str, payload: dict) -> dict:
    body = {"kind": kind, "payload": payload}
    return {
        "schema_version": LOG_SCHEMA_VERSION,
        **body,
        "record_hash": _digest(body),
    }


def _semantic_ack(ack: "Ack") -> tuple[str, str, str]:
    return ack.decision, ack.plan_revision, ack.note


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

    def normalized(self) -> "LiveDelta":
        if not self.event_id:
            raise ValueError("event_id required")
        if self.source_seq < 0:
            raise ValueError("source_seq must be non-negative")
        if not self.source or not self.source_epoch:
            raise ValueError("source and source_epoch required")
        if not self.semantic_keys and not self.affected_branches:
            raise ValueError("at least one semantic key or branch required")
        if not 0.0 <= self.impact <= 1.0 or not 0.0 <= self.urgency <= 1.0:
            raise ValueError("impact/urgency must be within [0,1]")
        if self.applicability not in APPLICABILITY:
            raise ValueError("invalid applicability")
        ph = self.payload_hash or _digest(self.payload)
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
            payload_hash=ph,
            causal_origin_epoch=self.causal_origin_epoch or self.source_epoch,
            arrival_epoch=self.arrival_epoch,
            causal_origin_refs=tuple(sorted(set(self.causal_origin_refs))),
            applicability=self.applicability,
        )


@dataclass(frozen=True)
class WorkerView:
    worker_id: str
    branches: tuple[str, ...]
    active_keys: tuple[str, ...]
    last_checkpoint_seq: int = 0


@dataclass(frozen=True)
class Delivery:
    delivery_id: str
    event_id: str
    worker_id: str
    delivery_class: str
    relevance: float
    reason: str
    authority: str = AUTHORITY


@dataclass(frozen=True)
class Ack:
    ack_id: str
    event_id: str
    worker_id: str
    decision: str
    plan_revision: str
    note: str = ""


class LiveFusionBus:
    """Append-only, replayable reference bus for targeted Clay worker re-entry.

    Delivery is intentionally at-least-once. event_id dedupe + idempotent ACKs make replay safe.
    Payload equality never erases a newer logical event, preserving ABA/provenance identity.
    Source order/arrival age never overwrites causal origin; late events remain routable.

    The JSONL transport is an Ubuntu-local durability reference lane, not final UnifiedDB
    authority. Linux advisory file locking serializes concurrent writers and fsync makes every
    completed record durable before the caller receives success.
    """

    def __init__(self, log_path: str | Path | None = None):
        self.log_path = Path(log_path) if log_path else None
        self.deltas: dict[str, LiveDelta] = {}
        self.workers: dict[str, WorkerView] = {}
        self.deliveries: dict[tuple[str, str], Delivery] = {}
        self.acks: dict[tuple[str, str], Ack] = {}
        self.payload_provenance: dict[str, set[str]] = {}
        self.max_source_seq: dict[str, int] = {}
        self.recovery_events: list[dict] = []

    def _append(self, kind: str, payload: dict) -> None:
        if not self.log_path:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        data = (_stable(_record(kind, payload)) + "\n").encode("utf-8")
        fd = os.open(self.log_path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            offset = 0
            while offset < len(data):
                written = os.write(fd, data[offset:])
                if written <= 0:
                    raise OSError("short append write")
                offset += written
            os.fsync(fd)
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def register_worker(self, worker: WorkerView, *, persist: bool = True) -> None:
        if not worker.worker_id:
            raise ValueError("worker_id required")
        self.workers[worker.worker_id] = worker
        if persist:
            self._append("WORKER_REGISTER", asdict(worker))
        for delta in self.deltas.values():
            self._route_one(delta, worker, persist=persist)

    def ingest(self, delta: LiveDelta, *, persist: bool = True) -> str:
        delta = delta.normalized()
        existing = self.deltas.get(delta.event_id)
        if existing:
            if existing.source != delta.source or existing.payload_hash != delta.payload_hash:
                raise ValueError("event identity conflict: same event_id with different source/content")
            return "DEDUPED_EVENT_ID"
        prev = self.max_source_seq.get(delta.source)
        if prev is not None and delta.source_seq < prev:
            status = "INGESTED_LATE"
        else:
            status = "INGESTED"
            self.max_source_seq[delta.source] = delta.source_seq
        self.deltas[delta.event_id] = delta
        self.payload_provenance.setdefault(delta.payload_hash, set()).update(delta.provenance_refs)
        if persist:
            self._append("DELTA_INGEST", asdict(delta))
        for worker in self.workers.values():
            self._route_one(delta, worker, persist=persist)
        return status

    @staticmethod
    def _score(delta: LiveDelta, worker: WorkerView) -> tuple[float, str]:
        branch_overlap = set(delta.affected_branches) & set(worker.branches)
        key_overlap = set(delta.semantic_keys) & set(worker.active_keys)
        if not branch_overlap and not key_overlap:
            return 0.0, "no semantic/work overlap"
        overlap = min(1.0, 0.55 * bool(branch_overlap) + 0.65 * bool(key_overlap))
        score = min(1.0, 0.45 * overlap + 0.35 * delta.impact + 0.20 * delta.urgency)
        reason = (
            f"branch_overlap={sorted(branch_overlap)} key_overlap={sorted(key_overlap)} "
            f"impact={delta.impact:.2f} urgency={delta.urgency:.2f} "
            f"applicability={delta.applicability}"
        )
        return score, reason

    def _route_one(self, delta: LiveDelta, worker: WorkerView, *, persist: bool) -> Delivery:
        key = (delta.event_id, worker.worker_id)
        existing = self.deliveries.get(key)
        if existing:
            return existing
        relevance, reason = self._score(delta, worker)
        if relevance == 0.0 or delta.applicability == "HISTORICALLY_VALID_ONLY":
            delivery_class = DELIVERY_INDEX
        elif delta.conflict and delta.impact >= 0.70 and relevance >= 0.45:
            delivery_class = DELIVERY_INTERRUPT
        else:
            delivery_class = DELIVERY_CHECKPOINT
        delivery = Delivery(
            delivery_id="delivery-" + _digest([delta.event_id, worker.worker_id])[:20],
            event_id=delta.event_id,
            worker_id=worker.worker_id,
            delivery_class=delivery_class,
            relevance=relevance,
            reason=reason,
        )
        self.deliveries[key] = delivery
        if persist:
            self._append("DELIVERY", asdict(delivery))
        return delivery

    def ack(self, ack: Ack, *, persist: bool = True) -> str:
        if ack.decision not in ACK_DECISIONS:
            raise ValueError("invalid ack decision")
        if ack.event_id not in self.deltas:
            raise KeyError("unknown event")
        if ack.worker_id not in self.workers:
            raise KeyError("unknown worker")
        key = (ack.event_id, ack.worker_id)
        existing = self.acks.get(key)
        if existing:
            if _semantic_ack(existing) == _semantic_ack(ack):
                return "ACK_IDEMPOTENT"
            raise ValueError("conflicting ACK for event/worker")
        self.acks[key] = ack
        if persist:
            self._append("ACK", asdict(ack))
        return "ACKED"

    def pending(self, worker_id: str, *, include_index_only: bool = False) -> list[Delivery]:
        pending = []
        for key, delivery in self.deliveries.items():
            if delivery.worker_id != worker_id or key in self.acks:
                continue
            if not include_index_only and delivery.delivery_class == DELIVERY_INDEX:
                continue
            pending.append(delivery)
        return sorted(
            pending,
            key=lambda delivery: (
                delivery.delivery_class != DELIVERY_INTERRUPT,
                -delivery.relevance,
                delivery.event_id,
            ),
        )

    def effect_guard(self, worker_id: str, effect_keys: Iterable[str]) -> tuple[bool, list[str]]:
        """Block only on unacked high-impact conflicts intersecting the intended effect."""
        effect_keys = set(effect_keys)
        blockers = []
        for delivery in self.pending(worker_id):
            if delivery.delivery_class != DELIVERY_INTERRUPT:
                continue
            delta = self.deltas[delivery.event_id]
            if effect_keys & set(delta.semantic_keys):
                blockers.append(delta.event_id)
        return not blockers, sorted(blockers)

    @staticmethod
    def _decode_log(path: Path) -> tuple[list[dict], list[dict]]:
        rows: list[dict] = []
        recovery: list[dict] = []
        if not path.exists():
            return rows, recovery
        raw = path.read_bytes()
        if not raw:
            return rows, recovery
        parts = raw.splitlines(keepends=True)
        for index, piece in enumerate(parts):
            is_last = index == len(parts) - 1
            complete = piece.endswith(b"\n")
            candidate = piece.rstrip(b"\r\n")
            if not candidate:
                continue
            if not complete and is_last:
                recovery.append(
                    {
                        "kind": "TORN_TAIL_IGNORED",
                        "byte_count": len(piece),
                        "record_index": index,
                    }
                )
                continue
            try:
                row = json.loads(candidate.decode("utf-8"))
            except Exception as exc:
                if is_last:
                    recovery.append(
                        {
                            "kind": "INVALID_TAIL_IGNORED",
                            "byte_count": len(piece),
                            "record_index": index,
                            "error": type(exc).__name__,
                        }
                    )
                    continue
                raise ValueError(f"corrupt interior log record {index}") from exc
            expected = row.get("record_hash")
            if expected:
                actual = _digest({"kind": row.get("kind"), "payload": row.get("payload")})
                if expected != actual:
                    raise ValueError(f"record hash mismatch at {index}")
            rows.append(row)
        return rows, recovery

    @classmethod
    def replay(cls, log_path: str | Path) -> "LiveFusionBus":
        bus = cls(log_path)
        path = Path(log_path)
        rows, recovery = cls._decode_log(path)
        bus.recovery_events.extend(recovery)
        for row in rows:
            kind, payload = row["kind"], row["payload"]
            if kind == "WORKER_REGISTER":
                payload["branches"] = tuple(payload["branches"])
                payload["active_keys"] = tuple(payload["active_keys"])
                bus.register_worker(WorkerView(**payload), persist=False)
            elif kind == "DELTA_INGEST":
                payload["semantic_keys"] = tuple(payload["semantic_keys"])
                payload["affected_branches"] = tuple(payload["affected_branches"])
                payload["provenance_refs"] = tuple(payload.get("provenance_refs", ()))
                payload["causal_origin_refs"] = tuple(payload.get("causal_origin_refs", ()))
                bus.ingest(LiveDelta(**payload), persist=False)
            elif kind == "ACK":
                bus.ack(Ack(**payload), persist=False)
            elif kind == "DELIVERY":
                continue
        return bus
