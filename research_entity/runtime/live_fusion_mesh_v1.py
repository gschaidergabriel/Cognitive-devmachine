from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Iterable, Optional

SCHEMA = r'''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS fusion_event_ingest(
  event_id TEXT PRIMARY KEY,
  event_hash TEXT NOT NULL,
  kind TEXT NOT NULL,
  semantic_key TEXT,
  actor TEXT NOT NULL,
  source_epoch INTEGER,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS fusion_deltas(
  delta_id TEXT PRIMARY KEY,
  semantic_key TEXT NOT NULL UNIQUE,
  content_hash TEXT NOT NULL,
  ancestry_hash TEXT,
  evidence_class TEXT NOT NULL,
  source_epoch INTEGER,
  payload_json TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS fusion_routes(
  delta_id TEXT NOT NULL,
  target TEXT NOT NULL,
  required_ack INTEGER NOT NULL DEFAULT 1,
  delivery_state TEXT NOT NULL DEFAULT 'PENDING',
  ack_event_id TEXT,
  ack_at REAL,
  PRIMARY KEY(delta_id,target),
  FOREIGN KEY(delta_id) REFERENCES fusion_deltas(delta_id)
);
CREATE TABLE IF NOT EXISTS premise_invalidations(
  invalidation_id TEXT PRIMARY KEY,
  premise_key TEXT NOT NULL,
  min_spec_rev INTEGER,
  invalidation_epoch INTEGER NOT NULL,
  reason_json TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_premise_invalidations_key
  ON premise_invalidations(premise_key,invalidation_epoch);
CREATE TABLE IF NOT EXISTS work_lease_heads(
  work_id TEXT PRIMARY KEY,
  fence_epoch INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS work_leases(
  lease_token TEXT PRIMARY KEY,
  work_id TEXT NOT NULL,
  spec_rev INTEGER NOT NULL,
  holder TEXT NOT NULL,
  fence_epoch INTEGER NOT NULL,
  acquired_at REAL NOT NULL,
  expires_at REAL NOT NULL,
  released_at REAL,
  UNIQUE(work_id, fence_epoch)
);
CREATE INDEX IF NOT EXISTS idx_work_leases_active
  ON work_leases(work_id,expires_at,released_at);
CREATE TABLE IF NOT EXISTS effect_receipts(
  effect_key TEXT PRIMARY KEY,
  work_id TEXT NOT NULL,
  spec_rev INTEGER NOT NULL,
  lease_token TEXT NOT NULL,
  fence_epoch INTEGER NOT NULL,
  result_hash TEXT NOT NULL,
  success INTEGER NOT NULL,
  created_at REAL NOT NULL
);
'''


def canon(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256(value) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else str(value).encode()
    return hashlib.sha256(raw).hexdigest()


def semantic_key(subject: str, payload, ancestry_hash: str = "") -> str:
    return sha256(canon({"subject": subject, "payload": payload, "ancestry": ancestry_hash}))


@dataclass(frozen=True)
class Lease:
    token: str
    work_id: str
    spec_rev: int
    holder: str
    fence_epoch: int
    acquired_at: float
    expires_at: float


class LiveFusionMesh:
    """Additive candidate for targeted live knowledge fusion and fenced work effects.

    This module never authorizes effects. It only provides transport/state invariants:
    semantic de-duplication, targeted acknowledgements, premise invalidation records,
    leases/fencing, and idempotent effect receipt keys. Clay authority boundaries remain
    external and must be checked by callers.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.db = conn
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    @classmethod
    def memory(cls):
        return cls(sqlite3.connect(":memory:"))

    def _ingest_event(
        self,
        *,
        event_id: str,
        kind: str,
        actor: str,
        semantic_key_: Optional[str],
        source_epoch: Optional[int],
        payload,
        created_at: float,
    ) -> bool:
        digest = sha256(
            canon(
                {
                    "kind": kind,
                    "actor": actor,
                    "semantic_key": semantic_key_,
                    "source_epoch": source_epoch,
                    "payload": payload,
                    "created_at": created_at,
                }
            )
        )
        row = self.db.execute(
            "SELECT event_hash FROM fusion_event_ingest WHERE event_id=?", (event_id,)
        ).fetchone()
        if row:
            if row["event_hash"] != digest:
                raise ValueError("event_id collision with different content")
            return False
        self.db.execute(
            "INSERT INTO fusion_event_ingest VALUES(?,?,?,?,?,?,?)",
            (event_id, digest, kind, semantic_key_, actor, source_epoch, created_at),
        )
        return True

    def publish_delta(
        self,
        *,
        subject: str,
        payload,
        targets: Iterable[str],
        actor: str,
        evidence_class: str,
        source_epoch: Optional[int] = None,
        ancestry_hash: str = "",
        event_id: Optional[str] = None,
        created_at: Optional[float] = None,
    ):
        ts = time.time() if created_at is None else created_at
        sk = semantic_key(subject, payload, ancestry_hash)
        eid = event_id or f"delta:{uuid.uuid4().hex}"
        event_payload = {
            "subject": subject,
            "payload": payload,
            "targets": sorted(set(targets)),
            "evidence_class": evidence_class,
            "ancestry_hash": ancestry_hash,
        }
        fresh = self._ingest_event(
            event_id=eid,
            kind="DELTA_PUBLISH",
            actor=actor,
            semantic_key_=sk,
            source_epoch=source_epoch,
            payload=event_payload,
            created_at=ts,
        )
        if not fresh:
            row = self.db.execute(
                "SELECT delta_id FROM fusion_deltas WHERE semantic_key=?", (sk,)
            ).fetchone()
            return {
                "created": False,
                "delta_id": row["delta_id"] if row else None,
                "semantic_key": sk,
            }

        content_hash = sha256(canon(payload))
        row = self.db.execute(
            "SELECT delta_id,content_hash FROM fusion_deltas WHERE semantic_key=?", (sk,)
        ).fetchone()
        if row:
            if row["content_hash"] != content_hash:
                raise ValueError("semantic key collision")
            delta_id = row["delta_id"]
            created = False
        else:
            delta_id = f"delta:{uuid.uuid4().hex}"
            self.db.execute(
                "INSERT INTO fusion_deltas VALUES(?,?,?,?,?,?,?,?)",
                (
                    delta_id,
                    sk,
                    content_hash,
                    ancestry_hash or None,
                    evidence_class,
                    source_epoch,
                    canon(payload),
                    ts,
                ),
            )
            created = True

        for target in sorted(set(targets)):
            self.db.execute(
                "INSERT OR IGNORE INTO fusion_routes(delta_id,target,required_ack) VALUES(?,?,1)",
                (delta_id, target),
            )
        self.db.commit()
        return {"created": created, "delta_id": delta_id, "semantic_key": sk}

    def ack_delta(
        self,
        *,
        delta_id: str,
        target: str,
        actor: str,
        event_id: Optional[str] = None,
        created_at: Optional[float] = None,
    ) -> bool:
        ts = time.time() if created_at is None else created_at
        eid = event_id or f"ack:{uuid.uuid4().hex}"
        fresh = self._ingest_event(
            event_id=eid,
            kind="DELTA_ACK",
            actor=actor,
            semantic_key_=delta_id,
            source_epoch=None,
            payload={"delta_id": delta_id, "target": target},
            created_at=ts,
        )
        if not fresh:
            return False
        cur = self.db.execute(
            "UPDATE fusion_routes SET delivery_state='ACKED',ack_event_id=?,ack_at=? "
            "WHERE delta_id=? AND target=?",
            (eid, ts, delta_id, target),
        )
        self.db.commit()
        return cur.rowcount == 1

    def pending_targets(self, delta_id: str):
        return [
            row["target"]
            for row in self.db.execute(
                "SELECT target FROM fusion_routes WHERE delta_id=? AND required_ack=1 "
                "AND delivery_state!='ACKED' ORDER BY target",
                (delta_id,),
            )
        ]

    def invalidate_premise(
        self,
        *,
        premise_key: str,
        invalidation_epoch: int,
        reason,
        actor: str,
        min_spec_rev: Optional[int] = None,
        event_id: Optional[str] = None,
        created_at: Optional[float] = None,
    ) -> bool:
        ts = time.time() if created_at is None else created_at
        eid = event_id or f"invalidate:{uuid.uuid4().hex}"
        payload = {
            "premise_key": premise_key,
            "invalidation_epoch": invalidation_epoch,
            "min_spec_rev": min_spec_rev,
            "reason": reason,
        }
        fresh = self._ingest_event(
            event_id=eid,
            kind="PREMISE_INVALIDATE",
            actor=actor,
            semantic_key_=premise_key,
            source_epoch=invalidation_epoch,
            payload=payload,
            created_at=ts,
        )
        if not fresh:
            return False
        self.db.execute(
            "INSERT INTO premise_invalidations VALUES(?,?,?,?,?,?)",
            (eid, premise_key, min_spec_rev, invalidation_epoch, canon(reason), ts),
        )
        self.db.commit()
        return True

    def claim(
        self,
        *,
        work_id: str,
        spec_rev: int,
        holder: str,
        ttl_s: float = 30.0,
        now: Optional[float] = None,
    ) -> Optional[Lease]:
        ts = time.time() if now is None else now
        self.db.execute(
            "INSERT OR IGNORE INTO work_lease_heads(work_id,fence_epoch) VALUES(?,0)",
            (work_id,),
        )
        active = self.db.execute(
            "SELECT * FROM work_leases WHERE work_id=? AND released_at IS NULL "
            "AND expires_at>? ORDER BY fence_epoch DESC LIMIT 1",
            (work_id, ts),
        ).fetchone()
        if active:
            return None

        self.db.execute(
            "UPDATE work_lease_heads SET fence_epoch=fence_epoch+1 WHERE work_id=?", (work_id,)
        )
        fence_epoch = int(
            self.db.execute(
                "SELECT fence_epoch FROM work_lease_heads WHERE work_id=?", (work_id,)
            ).fetchone()["fence_epoch"]
        )
        token = f"lease:{work_id}:{fence_epoch}:{uuid.uuid4().hex}"
        expires_at = ts + ttl_s
        self.db.execute(
            "INSERT INTO work_leases VALUES(?,?,?,?,?,?,?,NULL)",
            (token, work_id, spec_rev, holder, fence_epoch, ts, expires_at),
        )
        self.db.commit()
        return Lease(token, work_id, spec_rev, holder, fence_epoch, ts, expires_at)

    def release(self, lease: Lease, now: Optional[float] = None) -> bool:
        ts = time.time() if now is None else now
        cur = self.db.execute(
            "UPDATE work_leases SET released_at=? WHERE lease_token=? AND released_at IS NULL",
            (ts, lease.token),
        )
        self.db.commit()
        return cur.rowcount == 1

    def effect_receipt(
        self,
        *,
        effect_key: str,
        lease: Lease,
        current_spec_rev: int,
        result,
        success: bool,
        now: Optional[float] = None,
    ):
        ts = time.time() if now is None else now
        if lease.spec_rev != current_spec_rev:
            return {"accepted": False, "reason": "STALE_SPEC_REV"}

        row = self.db.execute(
            "SELECT * FROM work_leases WHERE lease_token=?", (lease.token,)
        ).fetchone()
        if not row or row["released_at"] is not None or row["expires_at"] <= ts:
            return {"accepted": False, "reason": "LEASE_INACTIVE"}

        head = self.db.execute(
            "SELECT fence_epoch FROM work_lease_heads WHERE work_id=?", (lease.work_id,)
        ).fetchone()
        if not head or int(head["fence_epoch"]) != lease.fence_epoch:
            return {"accepted": False, "reason": "FENCED"}

        result_hash = sha256(canon(result))
        prior = self.db.execute(
            "SELECT result_hash,success FROM effect_receipts WHERE effect_key=?", (effect_key,)
        ).fetchone()
        if prior:
            if prior["result_hash"] != result_hash or bool(prior["success"]) != bool(success):
                return {"accepted": False, "reason": "IDEMPOTENCY_CONFLICT"}
            return {"accepted": True, "duplicate": True, "reason": "IDEMPOTENT_REPLAY"}

        self.db.execute(
            "INSERT INTO effect_receipts VALUES(?,?,?,?,?,?,?,?)",
            (
                effect_key,
                lease.work_id,
                lease.spec_rev,
                lease.token,
                lease.fence_epoch,
                result_hash,
                1 if success else 0,
                ts,
            ),
        )
        self.db.commit()
        return {"accepted": True, "duplicate": False, "reason": "COMMITTED"}
