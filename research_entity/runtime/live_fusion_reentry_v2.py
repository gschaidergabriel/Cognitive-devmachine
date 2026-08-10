from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path
from contextlib import contextmanager
import sqlite3
from typing import Iterable

DELIVERY_INTERRUPT = "INTERRUPT_NEXT_SAFE_POINT"
DELIVERY_CHECKPOINT = "NEXT_CHECKPOINT"
DELIVERY_INDEX = "INDEX_ONLY"
ACK_DECISIONS = frozenset({"ACCEPT", "REPLAN", "NO_CHANGE", "CONFLICT", "DEFER"})
APPLICABILITY = frozenset({"CURRENT_MATERIAL", "HISTORICALLY_VALID_ONLY", "UNKNOWN"})
AUTHORITY = "COORDINATION_SIGNAL_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY"


def _stable(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value) -> str:
    return hashlib.sha256(_stable(value).encode("utf-8")).hexdigest()


def _jtuple(values: Iterable[str]) -> str:
    return _stable(sorted(set(values)))


def _tuple(value: str) -> tuple[str, ...]:
    return tuple(json.loads(value))


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
    affected_work: tuple[str, ...] = ()
    affected_claims: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    evidence_class: str = "UNKNOWN"
    payload_hash: str = ""
    causal_origin_epoch: str = ""
    arrival_epoch: str = ""
    causal_origin_refs: tuple[str, ...] = ()
    applicability: str = "UNKNOWN"

    def normalized(self) -> "LiveDelta":
        if not self.event_id or not self.source or not self.source_epoch:
            raise ValueError("event_id/source/source_epoch required")
        if self.source_seq < 0:
            raise ValueError("source_seq must be non-negative")
        if not (self.semantic_keys or self.affected_branches or self.affected_work or self.affected_claims):
            raise ValueError("delta must address at least one semantic/work/claim scope")
        if not 0.0 <= self.impact <= 1.0 or not 0.0 <= self.urgency <= 1.0:
            raise ValueError("impact/urgency must be within [0,1]")
        if self.applicability not in APPLICABILITY:
            raise ValueError("invalid applicability")
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
            conflict=bool(self.conflict),
            payload=self.payload,
            affected_work=tuple(sorted(set(self.affected_work))),
            affected_claims=tuple(sorted(set(self.affected_claims))),
            provenance_refs=tuple(sorted(set(self.provenance_refs))),
            evidence_class=self.evidence_class or "UNKNOWN",
            payload_hash=self.payload_hash or _digest(self.payload),
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
    active_work: tuple[str, ...] = ()
    active_claims: tuple[str, ...] = ()
    plan_revision: str = "UNKNOWN"
    lease_id: str = "NO_LEASE"
    lease_epoch: str = "UNKNOWN"
    last_checkpoint_seq: int = 0

    def normalized(self) -> "WorkerView":
        if not self.worker_id or not self.plan_revision or not self.lease_id:
            raise ValueError("worker_id/plan_revision/lease_id required")
        return WorkerView(
            worker_id=self.worker_id,
            branches=tuple(sorted(set(self.branches))),
            active_keys=tuple(sorted(set(self.active_keys))),
            active_work=tuple(sorted(set(self.active_work))),
            active_claims=tuple(sorted(set(self.active_claims))),
            plan_revision=self.plan_revision,
            lease_id=self.lease_id,
            lease_epoch=self.lease_epoch,
            last_checkpoint_seq=int(self.last_checkpoint_seq),
        )


@dataclass(frozen=True)
class Delivery:
    delivery_id: str
    event_id: str
    worker_id: str
    plan_revision: str
    lease_id: str
    delivery_class: str
    relevance: float
    reason: str
    authority: str = AUTHORITY


@dataclass(frozen=True)
class Ack:
    ack_id: str
    delivery_id: str
    event_id: str
    worker_id: str
    decision: str
    basis_plan_revision: str
    result_plan_revision: str
    lease_id: str
    payload_hash: str
    note: str = ""


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS live_fusion_events(
  event_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  source_seq INTEGER NOT NULL,
  source_epoch TEXT NOT NULL,
  semantic_keys TEXT NOT NULL,
  affected_branches TEXT NOT NULL,
  affected_work TEXT NOT NULL,
  affected_claims TEXT NOT NULL,
  novelty TEXT NOT NULL,
  impact REAL NOT NULL,
  urgency REAL NOT NULL,
  conflict INTEGER NOT NULL,
  payload TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  provenance_refs TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  causal_origin_epoch TEXT NOT NULL,
  arrival_epoch TEXT NOT NULL,
  causal_origin_refs TEXT NOT NULL,
  applicability TEXT NOT NULL,
  late INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS live_fusion_events_source_seq ON live_fusion_events(source,source_seq);
CREATE TABLE IF NOT EXISTS live_fusion_workers(
  worker_id TEXT PRIMARY KEY,
  branches TEXT NOT NULL,
  active_keys TEXT NOT NULL,
  active_work TEXT NOT NULL,
  active_claims TEXT NOT NULL,
  plan_revision TEXT NOT NULL,
  lease_id TEXT NOT NULL,
  lease_epoch TEXT NOT NULL,
  last_checkpoint_seq INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS live_fusion_deliveries(
  delivery_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES live_fusion_events(event_id),
  worker_id TEXT NOT NULL REFERENCES live_fusion_workers(worker_id),
  plan_revision TEXT NOT NULL,
  lease_id TEXT NOT NULL,
  delivery_class TEXT NOT NULL,
  relevance REAL NOT NULL,
  reason TEXT NOT NULL,
  authority TEXT NOT NULL,
  UNIQUE(event_id,worker_id,plan_revision,lease_id)
);
CREATE TABLE IF NOT EXISTS live_fusion_acks(
  ack_id TEXT PRIMARY KEY,
  delivery_id TEXT NOT NULL UNIQUE REFERENCES live_fusion_deliveries(delivery_id),
  event_id TEXT NOT NULL,
  worker_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  basis_plan_revision TEXT NOT NULL,
  result_plan_revision TEXT NOT NULL,
  lease_id TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  note TEXT NOT NULL
);
"""


class LiveFusionBus:
    """SQLite-backed candidate for durable targeted live-fusion worker re-entry.

    Semantic authority remains UnifiedDB/current project evidence. These tables are a
    candidate materialization of the transport/coordination plane only.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as c:
            c.executescript(SCHEMA)
            c.commit()

    def _connect(self):
        c = sqlite3.connect(self.db_path, timeout=5.0)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA busy_timeout=5000")
        c.execute("PRAGMA journal_mode=WAL")
        return c

    @contextmanager
    def _connection(self):
        c = self._connect()
        try:
            yield c
        finally:
            c.close()

    @staticmethod
    def _score(delta: LiveDelta, worker: WorkerView) -> tuple[float, str]:
        branch = set(delta.affected_branches) & set(worker.branches)
        keys = set(delta.semantic_keys) & set(worker.active_keys)
        work = set(delta.affected_work) & set(worker.active_work)
        claims = set(delta.affected_claims) & set(worker.active_claims)
        if not (branch or keys or work or claims):
            return 0.0, "no semantic/work/claim overlap"
        scope = min(
            1.0,
            0.25 * bool(branch)
            + 0.35 * bool(keys)
            + 0.35 * bool(work)
            + 0.20 * bool(claims),
        )
        relevance = min(1.0, 0.50 * scope + 0.30 * delta.impact + 0.20 * delta.urgency)
        reason = (
            f"branch={sorted(branch)} keys={sorted(keys)} work={sorted(work)} claims={sorted(claims)} "
            f"impact={delta.impact:.2f} urgency={delta.urgency:.2f} applicability={delta.applicability}"
        )
        return relevance, reason

    @staticmethod
    def _delivery_class(delta: LiveDelta, relevance: float) -> str:
        if relevance == 0.0 or delta.applicability == "HISTORICALLY_VALID_ONLY":
            return DELIVERY_INDEX
        if delta.conflict and delta.impact >= 0.70 and relevance >= 0.45:
            return DELIVERY_INTERRUPT
        return DELIVERY_CHECKPOINT

    def _event_from_row(self, r: sqlite3.Row) -> LiveDelta:
        return LiveDelta(
            event_id=r["event_id"], source=r["source"], source_seq=r["source_seq"],
            source_epoch=r["source_epoch"], semantic_keys=_tuple(r["semantic_keys"]),
            affected_branches=_tuple(r["affected_branches"]), novelty=r["novelty"],
            impact=r["impact"], urgency=r["urgency"], conflict=bool(r["conflict"]),
            payload=json.loads(r["payload"]), affected_work=_tuple(r["affected_work"]),
            affected_claims=_tuple(r["affected_claims"]), provenance_refs=_tuple(r["provenance_refs"]),
            evidence_class=r["evidence_class"], payload_hash=r["payload_hash"],
            causal_origin_epoch=r["causal_origin_epoch"], arrival_epoch=r["arrival_epoch"],
            causal_origin_refs=_tuple(r["causal_origin_refs"]), applicability=r["applicability"]
        )

    def _worker_from_row(self, r: sqlite3.Row) -> WorkerView:
        return WorkerView(
            worker_id=r["worker_id"], branches=_tuple(r["branches"]), active_keys=_tuple(r["active_keys"]),
            active_work=_tuple(r["active_work"]), active_claims=_tuple(r["active_claims"]),
            plan_revision=r["plan_revision"], lease_id=r["lease_id"], lease_epoch=r["lease_epoch"],
            last_checkpoint_seq=r["last_checkpoint_seq"]
        )

    def _route_one(self, c: sqlite3.Connection, delta: LiveDelta, worker: WorkerView) -> Delivery:
        relevance, reason = self._score(delta, worker)
        cls = self._delivery_class(delta, relevance)
        delivery_id = "delivery-" + _digest(
            [delta.event_id, worker.worker_id, worker.plan_revision, worker.lease_id]
        )[:24]
        c.execute(
            """INSERT OR IGNORE INTO live_fusion_deliveries(
               delivery_id,event_id,worker_id,plan_revision,lease_id,delivery_class,relevance,reason,authority
               ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (delivery_id, delta.event_id, worker.worker_id, worker.plan_revision, worker.lease_id,
             cls, relevance, reason, AUTHORITY),
        )
        row = c.execute("SELECT * FROM live_fusion_deliveries WHERE delivery_id=?", (delivery_id,)).fetchone()
        return Delivery(**dict(row))

    def register_worker(self, worker: WorkerView) -> list[Delivery]:
        worker = worker.normalized()
        with self._connection() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute(
                """INSERT INTO live_fusion_workers(
                   worker_id,branches,active_keys,active_work,active_claims,plan_revision,lease_id,lease_epoch,last_checkpoint_seq
                   ) VALUES(?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(worker_id) DO UPDATE SET
                     branches=excluded.branches,active_keys=excluded.active_keys,active_work=excluded.active_work,
                     active_claims=excluded.active_claims,plan_revision=excluded.plan_revision,lease_id=excluded.lease_id,
                     lease_epoch=excluded.lease_epoch,last_checkpoint_seq=excluded.last_checkpoint_seq""",
                (worker.worker_id, _jtuple(worker.branches), _jtuple(worker.active_keys), _jtuple(worker.active_work),
                 _jtuple(worker.active_claims), worker.plan_revision, worker.lease_id, worker.lease_epoch,
                 worker.last_checkpoint_seq),
            )
            deliveries = []
            for row in c.execute("SELECT * FROM live_fusion_events ORDER BY source,source_seq,event_id"):
                deliveries.append(self._route_one(c, self._event_from_row(row), worker))
            c.commit()
            return deliveries

    def ingest(self, delta: LiveDelta) -> str:
        delta = delta.normalized()
        with self._connection() as c:
            c.execute("BEGIN IMMEDIATE")
            existing = c.execute("SELECT payload_hash FROM live_fusion_events WHERE event_id=?", (delta.event_id,)).fetchone()
            if existing:
                c.rollback()
                if existing["payload_hash"] != delta.payload_hash:
                    raise ValueError("same event_id with different payload identity")
                return "DEDUPED_EVENT_ID"
            prev = c.execute("SELECT MAX(source_seq) AS m FROM live_fusion_events WHERE source=?", (delta.source,)).fetchone()["m"]
            late = int(prev is not None and delta.source_seq < prev)
            c.execute(
                """INSERT INTO live_fusion_events(
                   event_id,source,source_seq,source_epoch,semantic_keys,affected_branches,affected_work,affected_claims,
                   novelty,impact,urgency,conflict,payload,payload_hash,provenance_refs,evidence_class,
                   causal_origin_epoch,arrival_epoch,causal_origin_refs,applicability,late
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (delta.event_id, delta.source, delta.source_seq, delta.source_epoch, _jtuple(delta.semantic_keys),
                 _jtuple(delta.affected_branches), _jtuple(delta.affected_work), _jtuple(delta.affected_claims),
                 delta.novelty, delta.impact, delta.urgency, int(delta.conflict), _stable(delta.payload),
                 delta.payload_hash, _jtuple(delta.provenance_refs), delta.evidence_class, delta.causal_origin_epoch,
                 delta.arrival_epoch, _jtuple(delta.causal_origin_refs), delta.applicability, late),
            )
            for row in c.execute("SELECT * FROM live_fusion_workers ORDER BY worker_id"):
                self._route_one(c, delta, self._worker_from_row(row))
            c.commit()
            return "INGESTED_LATE" if late else "INGESTED"

    def pending(self, worker_id: str, *, include_index_only: bool = False, current_plan_only: bool = True) -> list[Delivery]:
        with self._connection() as c:
            w = c.execute("SELECT * FROM live_fusion_workers WHERE worker_id=?", (worker_id,)).fetchone()
            if not w:
                raise KeyError("unknown worker")
            params: list[object] = [worker_id]
            where = ["d.worker_id=?", "a.delivery_id IS NULL"]
            if current_plan_only:
                where.extend(["d.plan_revision=?", "d.lease_id=?"])
                params.extend([w["plan_revision"], w["lease_id"]])
            if not include_index_only:
                where.append("d.delivery_class<>?")
                params.append(DELIVERY_INDEX)
            rows = c.execute(
                f"""SELECT d.* FROM live_fusion_deliveries d
                    LEFT JOIN live_fusion_acks a ON a.delivery_id=d.delivery_id
                    WHERE {' AND '.join(where)}
                    ORDER BY (d.delivery_class<>?) ASC,d.relevance DESC,d.delivery_id""",
                (*params, DELIVERY_INTERRUPT),
            ).fetchall()
            return [Delivery(**dict(r)) for r in rows]

    def ack(self, ack: Ack) -> str:
        if ack.decision not in ACK_DECISIONS:
            raise ValueError("invalid ack decision")
        with self._connection() as c:
            c.execute("BEGIN IMMEDIATE")
            d = c.execute("SELECT * FROM live_fusion_deliveries WHERE delivery_id=?", (ack.delivery_id,)).fetchone()
            if not d or d["event_id"] != ack.event_id or d["worker_id"] != ack.worker_id:
                c.rollback()
                raise KeyError("delivery/event/worker identity mismatch")
            w = c.execute("SELECT * FROM live_fusion_workers WHERE worker_id=?", (ack.worker_id,)).fetchone()
            e = c.execute("SELECT * FROM live_fusion_events WHERE event_id=?", (ack.event_id,)).fetchone()
            if ack.payload_hash != e["payload_hash"]:
                c.rollback()
                raise ValueError("ack payload hash mismatch")
            if ack.basis_plan_revision != d["plan_revision"] or ack.lease_id != d["lease_id"]:
                c.rollback()
                raise ValueError("ack not bound to delivered plan/lease identity")
            if w["plan_revision"] != ack.basis_plan_revision or w["lease_id"] != ack.lease_id:
                c.rollback()
                raise ValueError("stale ack: worker plan/lease changed; re-delivery required")
            if ack.decision == "REPLAN" and ack.result_plan_revision == ack.basis_plan_revision:
                c.rollback()
                raise ValueError("REPLAN must name a new result_plan_revision")
            prior = c.execute("SELECT * FROM live_fusion_acks WHERE delivery_id=?", (ack.delivery_id,)).fetchone()
            if prior:
                c.rollback()
                return "ACK_IDEMPOTENT" if dict(prior) == asdict(ack) else "ACK_CONFLICT"
            c.execute(
                """INSERT INTO live_fusion_acks(
                   ack_id,delivery_id,event_id,worker_id,decision,basis_plan_revision,result_plan_revision,lease_id,payload_hash,note
                   ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (ack.ack_id, ack.delivery_id, ack.event_id, ack.worker_id, ack.decision, ack.basis_plan_revision,
                 ack.result_plan_revision, ack.lease_id, ack.payload_hash, ack.note),
            )
            c.commit()
            return "ACKED"

    def effect_guard(
        self,
        worker_id: str,
        effect_keys: Iterable[str] = (),
        effect_work: Iterable[str] = (),
        effect_claims: Iterable[str] = (),
    ) -> tuple[bool, list[str]]:
        effect_keys, effect_work, effect_claims = set(effect_keys), set(effect_work), set(effect_claims)
        blockers = []
        with self._connection() as c:
            for d in self.pending(worker_id):
                if d.delivery_class != DELIVERY_INTERRUPT:
                    continue
                e = c.execute("SELECT semantic_keys,affected_work,affected_claims FROM live_fusion_events WHERE event_id=?", (d.event_id,)).fetchone()
                if (
                    effect_keys & set(_tuple(e["semantic_keys"]))
                    or effect_work & set(_tuple(e["affected_work"]))
                    or effect_claims & set(_tuple(e["affected_claims"]))
                ):
                    blockers.append(d.event_id)
        return not blockers, sorted(set(blockers))

    def snapshot(self) -> dict:
        with self._connection() as c:
            return {
                "events": c.execute("SELECT COUNT(*) FROM live_fusion_events").fetchone()[0],
                "workers": c.execute("SELECT COUNT(*) FROM live_fusion_workers").fetchone()[0],
                "deliveries": c.execute("SELECT COUNT(*) FROM live_fusion_deliveries").fetchone()[0],
                "acks": c.execute("SELECT COUNT(*) FROM live_fusion_acks").fetchone()[0],
            }
