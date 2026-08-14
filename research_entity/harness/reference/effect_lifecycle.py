from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Optional

from effect_authority import ConfirmationReceipt, EffectAuthorityGate, EffectDecision, EffectRequest


class LifecycleState(str, Enum):
    RESERVED = "RESERVED"
    COMMITTING = "COMMITTING"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    OUTCOME_SUCCEEDED = "OUTCOME_SUCCEEDED"
    OUTCOME_FAILED = "OUTCOME_FAILED"
    REENTERED = "REENTERED"
    ROLLED_BACK = "ROLLED_BACK"


class RecoveryClass(str, Enum):
    SAFE_TO_START = "SAFE_TO_START"
    SAFE_TO_RETRY_SAME_IDEMPOTENCY_KEY = "SAFE_TO_RETRY_SAME_IDEMPOTENCY_KEY"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    REENTRY_PENDING = "REENTRY_PENDING"
    COMPLETE = "COMPLETE"
    COMPLETE_ROLLED_BACK = "COMPLETE_ROLLED_BACK"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReservationResult:
    admitted: bool
    reason: str
    effect_id: Optional[str] = None
    state: Optional[LifecycleState] = None


@dataclass(frozen=True)
class TransitionResult:
    changed: bool
    reason: str
    effect_id: str
    state: LifecycleState


def _utc_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()


class EffectLifecycleStore:
    """
    H1 reference state machine for the effect-authority -> reservation -> attempt ->
    outcome -> provenance-bound re-entry boundary.

    Local state can be atomic. External exactly-once execution is *not* claimed:
    once an external attempt has started, crash recovery requires either a downstream
    idempotency key with safe retry semantics or external reconciliation.
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str | Path, *, timeout_seconds: float = 5.0):
        self.db_path = str(db_path)
        self.timeout_seconds = timeout_seconds
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            timeout=self.timeout_seconds,
            isolation_level=None,
            check_same_thread=True,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute(f"PRAGMA busy_timeout={int(self.timeout_seconds * 1000)}")
        return conn

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn:
            # Rollback journal + FULL is deliberately explicit for the H1 reference.
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS effects(
                    effect_id TEXT PRIMARY KEY,
                    request_hash TEXT NOT NULL,
                    effect_class TEXT NOT NULL,
                    target TEXT NOT NULL,
                    action TEXT NOT NULL,
                    state TEXT NOT NULL,
                    confirmation_nonce TEXT,
                    confirmation_receipt_hash TEXT,
                    idempotency_key TEXT,
                    external_idempotent INTEGER NOT NULL DEFAULT 0 CHECK(external_idempotent IN (0,1)),
                    reserved_at TEXT NOT NULL,
                    attempt_id TEXT,
                    attempt_started_at TEXT,
                    outcome_success INTEGER CHECK(outcome_success IN (0,1)),
                    outcome_verified INTEGER CHECK(outcome_verified IN (0,1)),
                    outcome_hash TEXT,
                    outcome_at TEXT,
                    reentry_hash TEXT,
                    reentry_at TEXT,
                    revision INTEGER NOT NULL DEFAULT 1
                );

                CREATE UNIQUE INDEX IF NOT EXISTS effects_idempotency_key_unique
                    ON effects(idempotency_key) WHERE idempotency_key IS NOT NULL;

                CREATE TABLE IF NOT EXISTS confirmation_consumptions(
                    nonce TEXT PRIMARY KEY,
                    request_hash TEXT NOT NULL,
                    receipt_hash TEXT NOT NULL UNIQUE,
                    effect_id TEXT NOT NULL UNIQUE,
                    consumed_at TEXT NOT NULL,
                    FOREIGN KEY(effect_id) REFERENCES effects(effect_id) ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS effect_events(
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    effect_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    state TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(effect_id) REFERENCES effects(effect_id) ON DELETE RESTRICT
                );

                INSERT OR REPLACE INTO schema_meta(key, value)
                    VALUES ('schema_version', '1');
                """
            )

    @staticmethod
    def effect_id_for_confirmed(req: EffectRequest, receipt: ConfirmationReceipt) -> str:
        return sha256(f"confirmed|{req.request_hash()}|{receipt.nonce}".encode()).hexdigest()

    @staticmethod
    def effect_id_for_allowed(req: EffectRequest, reservation_key: str) -> str:
        return sha256(f"allowed|{req.request_hash()}|{reservation_key}".encode()).hexdigest()

    def _append_event(
        self,
        conn: sqlite3.Connection,
        *,
        effect_id: str,
        event_type: str,
        state: LifecycleState,
        payload: dict[str, Any],
        now: datetime,
    ) -> None:
        body = {
            "effect_id": effect_id,
            "event_type": event_type,
            "state": state.value,
            "payload": payload,
            "created_at": _utc_iso(now),
        }
        event_hash = _canonical_hash(body)
        conn.execute(
            """INSERT INTO effect_events(effect_id,event_type,state,event_hash,payload_json,created_at)
               VALUES(?,?,?,?,?,?)""",
            (
                effect_id,
                event_type,
                state.value,
                event_hash,
                json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
                _utc_iso(now),
            ),
        )

    def reserve_confirmed(
        self,
        req: EffectRequest,
        receipt: ConfirmationReceipt,
        *,
        now: datetime,
        idempotency_key: Optional[str] = None,
        external_idempotent: bool = False,
        fault_after_confirmation_insert: bool = False,
    ) -> ReservationResult:
        gate = EffectAuthorityGate()
        validation = gate.validate_confirmation(req, receipt, now=now)
        if validation.decision != EffectDecision.ALLOW:
            return ReservationResult(False, f"gate:{validation.reason}")

        effect_id = self.effect_id_for_confirmed(req, receipt)
        receipt_hash = receipt.receipt_hash()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT effect_id, request_hash, receipt_hash FROM confirmation_consumptions WHERE nonce=?",
                (receipt.nonce,),
            ).fetchone()
            if existing is not None:
                conn.rollback()
                return ReservationResult(False, "durable confirmation replay", str(existing["effect_id"]))

            if idempotency_key is not None:
                duplicate = conn.execute(
                    "SELECT effect_id,state FROM effects WHERE idempotency_key=?",
                    (idempotency_key,),
                ).fetchone()
                if duplicate is not None:
                    conn.rollback()
                    return ReservationResult(False, "duplicate downstream idempotency key", str(duplicate["effect_id"]), LifecycleState(str(duplicate["state"])))

            conn.execute(
                """INSERT INTO effects(
                    effect_id,request_hash,effect_class,target,action,state,
                    confirmation_nonce,confirmation_receipt_hash,idempotency_key,
                    external_idempotent,reserved_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    effect_id,
                    req.request_hash(),
                    req.effect_class.value,
                    req.target,
                    req.action,
                    LifecycleState.RESERVED.value,
                    receipt.nonce,
                    receipt_hash,
                    idempotency_key,
                    int(external_idempotent),
                    _utc_iso(now),
                ),
            )
            conn.execute(
                """INSERT INTO confirmation_consumptions(nonce,request_hash,receipt_hash,effect_id,consumed_at)
                   VALUES(?,?,?,?,?)""",
                (receipt.nonce, req.request_hash(), receipt_hash, effect_id, _utc_iso(now)),
            )
            if fault_after_confirmation_insert:
                raise RuntimeError("fault injection after confirmation insert")
            self._append_event(
                conn,
                effect_id=effect_id,
                event_type="RESERVED_WITH_CONFIRMATION",
                state=LifecycleState.RESERVED,
                payload={
                    "request_hash": req.request_hash(),
                    "confirmation_nonce": receipt.nonce,
                    "confirmation_receipt_hash": receipt_hash,
                    "idempotency_key": idempotency_key,
                    "external_idempotent": external_idempotent,
                },
                now=now,
            )
            conn.commit()
            return ReservationResult(True, "confirmed authority atomically reserved", effect_id, LifecycleState.RESERVED)
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            return ReservationResult(False, f"integrity-conflict:{exc}")
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def reserve_allowed(
        self,
        req: EffectRequest,
        *,
        reservation_key: str,
        now: datetime,
        idempotency_key: Optional[str] = None,
        external_idempotent: bool = False,
    ) -> ReservationResult:
        gate = EffectAuthorityGate()
        base = gate.evaluate(req)
        if base.decision != EffectDecision.ALLOW:
            return ReservationResult(False, f"gate:{base.reason}")
        effect_id = self.effect_id_for_allowed(req, reservation_key)
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute("SELECT state FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
            if existing is not None:
                conn.rollback()
                return ReservationResult(False, "duplicate deterministic reservation", effect_id, LifecycleState(str(existing["state"])))
            if idempotency_key is not None:
                duplicate = conn.execute("SELECT effect_id,state FROM effects WHERE idempotency_key=?", (idempotency_key,)).fetchone()
                if duplicate is not None:
                    conn.rollback()
                    return ReservationResult(False, "duplicate downstream idempotency key", str(duplicate["effect_id"]), LifecycleState(str(duplicate["state"])))
            conn.execute(
                """INSERT INTO effects(
                    effect_id,request_hash,effect_class,target,action,state,
                    idempotency_key,external_idempotent,reserved_at
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    effect_id,
                    req.request_hash(),
                    req.effect_class.value,
                    req.target,
                    req.action,
                    LifecycleState.RESERVED.value,
                    idempotency_key,
                    int(external_idempotent),
                    _utc_iso(now),
                ),
            )
            self._append_event(
                conn,
                effect_id=effect_id,
                event_type="RESERVED_DIRECT_ALLOW",
                state=LifecycleState.RESERVED,
                payload={"request_hash": req.request_hash(), "reservation_key": reservation_key, "idempotency_key": idempotency_key, "external_idempotent": external_idempotent},
                now=now,
            )
            conn.commit()
            return ReservationResult(True, "direct-allow authority atomically reserved", effect_id, LifecycleState.RESERVED)
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            return ReservationResult(False, f"integrity-conflict:{exc}")
        finally:
            conn.close()

    def begin_attempt(self, effect_id: str, *, attempt_id: str, now: datetime) -> TransitionResult:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT state,attempt_id FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
            if row is None:
                conn.rollback()
                raise KeyError(effect_id)
            state = LifecycleState(str(row["state"]))
            if state == LifecycleState.COMMITTING and row["attempt_id"] == attempt_id:
                conn.rollback()
                return TransitionResult(False, "same attempt already started", effect_id, state)
            if state != LifecycleState.RESERVED:
                conn.rollback()
                return TransitionResult(False, f"cannot begin attempt from {state.value}", effect_id, state)
            conn.execute(
                """UPDATE effects SET state=?,attempt_id=?,attempt_started_at=?,revision=revision+1
                   WHERE effect_id=? AND state=?""",
                (LifecycleState.COMMITTING.value, attempt_id, _utc_iso(now), effect_id, LifecycleState.RESERVED.value),
            )
            self._append_event(
                conn,
                effect_id=effect_id,
                event_type="EXTERNAL_ATTEMPT_STARTED",
                state=LifecycleState.COMMITTING,
                payload={"attempt_id": attempt_id},
                now=now,
            )
            conn.commit()
            return TransitionResult(True, "external attempt boundary entered", effect_id, LifecycleState.COMMITTING)
        finally:
            conn.close()

    def record_outcome(
        self,
        effect_id: str,
        *,
        success: bool,
        verified: bool,
        outcome: dict[str, Any],
        now: datetime,
    ) -> TransitionResult:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT state FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
            if row is None:
                conn.rollback()
                raise KeyError(effect_id)
            state = LifecycleState(str(row["state"]))
            if state != LifecycleState.COMMITTING:
                conn.rollback()
                return TransitionResult(False, f"cannot record outcome from {state.value}", effect_id, state)

            if verified:
                new_state = LifecycleState.OUTCOME_SUCCEEDED if success else LifecycleState.OUTCOME_FAILED
            else:
                new_state = LifecycleState.OUTCOME_UNKNOWN
            outcome_hash = _canonical_hash(outcome)
            conn.execute(
                """UPDATE effects SET state=?,outcome_success=?,outcome_verified=?,outcome_hash=?,outcome_at=?,revision=revision+1
                   WHERE effect_id=?""",
                (new_state.value, int(success), int(verified), outcome_hash, _utc_iso(now), effect_id),
            )
            self._append_event(
                conn,
                effect_id=effect_id,
                event_type="OUTCOME_RECORDED",
                state=new_state,
                payload={"success": success, "verified": verified, "outcome_hash": outcome_hash},
                now=now,
            )
            conn.commit()
            return TransitionResult(True, "outcome persisted", effect_id, new_state)
        finally:
            conn.close()

    def record_reentry(self, effect_id: str, *, reentry: dict[str, Any], now: datetime) -> TransitionResult:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT state FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
            if row is None:
                conn.rollback()
                raise KeyError(effect_id)
            state = LifecycleState(str(row["state"]))
            if state not in {LifecycleState.OUTCOME_SUCCEEDED, LifecycleState.OUTCOME_FAILED}:
                conn.rollback()
                return TransitionResult(False, f"reentry requires verified outcome, got {state.value}", effect_id, state)
            reentry_hash = _canonical_hash(reentry)
            conn.execute(
                """UPDATE effects SET state=?,reentry_hash=?,reentry_at=?,revision=revision+1 WHERE effect_id=?""",
                (LifecycleState.REENTERED.value, reentry_hash, _utc_iso(now), effect_id),
            )
            self._append_event(
                conn,
                effect_id=effect_id,
                event_type="PROVENANCE_REENTRY",
                state=LifecycleState.REENTERED,
                payload={"reentry_hash": reentry_hash},
                now=now,
            )
            conn.commit()
            return TransitionResult(True, "verified outcome re-entered", effect_id, LifecycleState.REENTERED)
        finally:
            conn.close()

    def recovery_class(self, effect_id: str) -> RecoveryClass:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT state,external_idempotent,idempotency_key FROM effects WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
            if row is None:
                return RecoveryClass.UNKNOWN
            state = LifecycleState(str(row["state"]))
            external_idempotent = bool(row["external_idempotent"])
            key = row["idempotency_key"]

        if state == LifecycleState.RESERVED:
            return RecoveryClass.SAFE_TO_START
        if state in {LifecycleState.COMMITTING, LifecycleState.OUTCOME_UNKNOWN}:
            if external_idempotent and key:
                return RecoveryClass.SAFE_TO_RETRY_SAME_IDEMPOTENCY_KEY
            return RecoveryClass.RECONCILE_REQUIRED
        if state in {LifecycleState.OUTCOME_SUCCEEDED, LifecycleState.OUTCOME_FAILED}:
            return RecoveryClass.REENTRY_PENDING
        if state == LifecycleState.REENTERED:
            return RecoveryClass.COMPLETE
        if state == LifecycleState.ROLLED_BACK:
            return RecoveryClass.COMPLETE_ROLLED_BACK
        return RecoveryClass.UNKNOWN

    def effect_row(self, effect_id: str) -> Optional[dict[str, Any]]:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
            return dict(row) if row else None

    def confirmation_count(self) -> int:
        with closing(self._connect()) as conn:
            return int(conn.execute("SELECT COUNT(*) FROM confirmation_consumptions").fetchone()[0])

    def event_count(self, effect_id: str) -> int:
        with closing(self._connect()) as conn:
            return int(conn.execute("SELECT COUNT(*) FROM effect_events WHERE effect_id=?", (effect_id,)).fetchone()[0])

    def verify_effect_trace(self, effect_id: str) -> tuple[bool, str]:
        """Verify append-only event hashes, legal lifecycle order and state/event agreement."""
        with closing(self._connect()) as conn:
            effect = conn.execute("SELECT state FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
            if effect is None:
                return False, "effect missing"
            rows = conn.execute(
                "SELECT event_type,state,event_hash,payload_json,created_at FROM effect_events WHERE effect_id=? ORDER BY seq",
                (effect_id,),
            ).fetchall()

        if not rows:
            return False, "event trace empty"

        legal = {
            None: {LifecycleState.RESERVED},
            LifecycleState.RESERVED: {LifecycleState.COMMITTING},
            LifecycleState.COMMITTING: {
                LifecycleState.OUTCOME_UNKNOWN,
                LifecycleState.OUTCOME_SUCCEEDED,
                LifecycleState.OUTCOME_FAILED,
            },
            LifecycleState.OUTCOME_SUCCEEDED: {LifecycleState.REENTERED},
            LifecycleState.OUTCOME_FAILED: {LifecycleState.REENTERED},
            LifecycleState.OUTCOME_UNKNOWN: set(),
            LifecycleState.REENTERED: set(),
            LifecycleState.ROLLED_BACK: set(),
        }
        prev: Optional[LifecycleState] = None
        for row in rows:
            state = LifecycleState(str(row["state"]))
            try:
                payload = json.loads(str(row["payload_json"]))
            except json.JSONDecodeError:
                return False, "event payload malformed"
            body = {
                "effect_id": effect_id,
                "event_type": str(row["event_type"]),
                "state": state.value,
                "payload": payload,
                "created_at": str(row["created_at"]),
            }
            if _canonical_hash(body) != str(row["event_hash"]):
                return False, "event hash mismatch"
            if state not in legal.get(prev, set()):
                return False, f"illegal trace transition {prev}->{state.value}"
            prev = state

        if prev != LifecycleState(str(effect["state"])):
            return False, "effect row state disagrees with final event state"
        return True, "ok"

    def integrity_check(self) -> str:
        with closing(self._connect()) as conn:
            return str(conn.execute("PRAGMA integrity_check").fetchone()[0])
