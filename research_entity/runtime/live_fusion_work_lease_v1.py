from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SCHEMA = r'''
PRAGMA foreign_keys=ON;
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
CREATE TABLE IF NOT EXISTS work_effect_intents(
  effect_key TEXT PRIMARY KEY,
  work_id TEXT NOT NULL,
  spec_rev INTEGER NOT NULL,
  lease_token TEXT NOT NULL,
  fence_epoch INTEGER NOT NULL,
  request_hash TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('RESERVED','FINALIZED')),
  result_hash TEXT,
  success INTEGER,
  reserved_at REAL NOT NULL,
  finalized_at REAL
);
'''


def _stable(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value) -> str:
    return hashlib.sha256(_stable(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class WorkLease:
    token: str
    work_id: str
    spec_rev: int
    holder: str
    fence_epoch: int
    acquired_at: float
    expires_at: float


class WorkLeaseFenceStore:
    """Lease/fencing + durable effect reservation extension for PR #156 LiveFusion.

    Call reserve_effect *before* a consequential external effect. Only a newly RESERVED key
    may be executed. If a process dies after reservation, replay returns RECOVERY_REQUIRED
    rather than permission to execute again. finalize_effect records the verified outcome.
    This store never grants truth/effect authority; callers still need Clay authority and the
    parent LiveFusion effect guard.
    """

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = str(db_path) if db_path is not None else ":memory:"
        self.db = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript(SCHEMA)

    def close(self):
        self.db.close()

    def _begin_immediate(self):
        self.db.execute("BEGIN IMMEDIATE")

    def _validate_live_lease(self, lease: WorkLease, current_spec_rev: int, ts: float):
        if lease.spec_rev != current_spec_rev:
            return "STALE_SPEC_REV"
        row = self.db.execute("SELECT * FROM work_leases WHERE lease_token=?", (lease.token,)).fetchone()
        if not row or row["released_at"] is not None or row["expires_at"] <= ts:
            return "LEASE_INACTIVE"
        head = self.db.execute(
            "SELECT fence_epoch FROM work_lease_heads WHERE work_id=?", (lease.work_id,)
        ).fetchone()
        if not head or int(head["fence_epoch"]) != lease.fence_epoch:
            return "FENCED"
        return None

    def claim(self, *, work_id: str, spec_rev: int, holder: str, ttl_s: float = 30.0,
              now: Optional[float] = None) -> Optional[WorkLease]:
        ts = time.time() if now is None else now
        if not work_id or not holder or spec_rev < 1 or ttl_s <= 0:
            raise ValueError("valid work_id, holder, spec_rev>=1 and ttl_s>0 required")
        self._begin_immediate()
        try:
            self.db.execute(
                "INSERT OR IGNORE INTO work_lease_heads(work_id,fence_epoch) VALUES(?,0)", (work_id,)
            )
            active = self.db.execute(
                "SELECT lease_token FROM work_leases WHERE work_id=? AND released_at IS NULL "
                "AND expires_at>? ORDER BY fence_epoch DESC LIMIT 1", (work_id, ts)
            ).fetchone()
            if active:
                self.db.execute("ROLLBACK")
                return None
            self.db.execute(
                "UPDATE work_lease_heads SET fence_epoch=fence_epoch+1 WHERE work_id=?", (work_id,)
            )
            fence = int(self.db.execute(
                "SELECT fence_epoch FROM work_lease_heads WHERE work_id=?", (work_id,)
            ).fetchone()["fence_epoch"])
            token = f"lease:{work_id}:{fence}:{uuid.uuid4().hex}"
            exp = ts + ttl_s
            self.db.execute(
                "INSERT INTO work_leases VALUES(?,?,?,?,?,?,?,NULL)",
                (token, work_id, spec_rev, holder, fence, ts, exp),
            )
            self.db.execute("COMMIT")
            return WorkLease(token, work_id, spec_rev, holder, fence, ts, exp)
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def release(self, lease: WorkLease, now: Optional[float] = None) -> bool:
        ts = time.time() if now is None else now
        self._begin_immediate()
        try:
            cur = self.db.execute(
                "UPDATE work_leases SET released_at=? WHERE lease_token=? AND released_at IS NULL",
                (ts, lease.token),
            )
            self.db.execute("COMMIT")
            return cur.rowcount == 1
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def reserve_effect(self, *, effect_key: str, lease: WorkLease, current_spec_rev: int,
                       request, now: Optional[float] = None) -> dict:
        ts = time.time() if now is None else now
        if not effect_key:
            raise ValueError("effect_key required")
        request_hash = _digest(request)
        self._begin_immediate()
        try:
            prior = self.db.execute(
                "SELECT * FROM work_effect_intents WHERE effect_key=?", (effect_key,)
            ).fetchone()
            if prior:
                same_request = prior["request_hash"] == request_hash and prior["work_id"] == lease.work_id
                if not same_request:
                    self.db.execute("ROLLBACK")
                    return {"reserved": False, "reason": "IDEMPOTENCY_CONFLICT"}
                reason = "RECOVERY_REQUIRED" if prior["state"] == "RESERVED" else "ALREADY_FINALIZED"
                self.db.execute("ROLLBACK")
                return {"reserved": False, "reason": reason}
            reason = self._validate_live_lease(lease, current_spec_rev, ts)
            if reason:
                self.db.execute("ROLLBACK")
                return {"reserved": False, "reason": reason}
            self.db.execute(
                "INSERT INTO work_effect_intents VALUES(?,?,?,?,?,?,'RESERVED',NULL,NULL,?,NULL)",
                (effect_key, lease.work_id, lease.spec_rev, lease.token, lease.fence_epoch, request_hash, ts),
            )
            self.db.execute("COMMIT")
            return {"reserved": True, "reason": "RESERVED"}
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def finalize_effect(self, *, effect_key: str, lease: WorkLease, result, success: bool,
                        now: Optional[float] = None) -> dict:
        ts = time.time() if now is None else now
        result_hash = _digest(result)
        self._begin_immediate()
        try:
            prior = self.db.execute(
                "SELECT * FROM work_effect_intents WHERE effect_key=?", (effect_key,)
            ).fetchone()
            if not prior:
                self.db.execute("ROLLBACK")
                return {"accepted": False, "reason": "NO_RESERVATION"}
            if prior["lease_token"] != lease.token or int(prior["fence_epoch"]) != lease.fence_epoch:
                self.db.execute("ROLLBACK")
                return {"accepted": False, "reason": "RESERVATION_OWNER_MISMATCH"}
            if prior["state"] == "FINALIZED":
                same = prior["result_hash"] == result_hash and bool(prior["success"]) == bool(success)
                self.db.execute("ROLLBACK")
                return ({"accepted": True, "duplicate": True, "reason": "IDEMPOTENT_REPLAY"}
                        if same else {"accepted": False, "reason": "IDEMPOTENCY_CONFLICT"})
            self.db.execute(
                "UPDATE work_effect_intents SET state='FINALIZED',result_hash=?,success=?,finalized_at=? "
                "WHERE effect_key=?",
                (result_hash, 1 if success else 0, ts, effect_key),
            )
            self.db.execute("COMMIT")
            return {"accepted": True, "duplicate": False, "reason": "FINALIZED"}
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def effect_state(self, effect_key: str):
        row = self.db.execute(
            "SELECT * FROM work_effect_intents WHERE effect_key=?", (effect_key,)
        ).fetchone()
        return dict(row) if row else None
