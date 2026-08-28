#!/usr/bin/env python3
"""Crash-window reconciliation for GRID10 V4->V6 cognitive cycle closure.

This module closes an observability/recovery gap without pretending that V4 Agency commit
and V6 candidate-cognition receipt are already one atomic transaction.

Protocol:
1. persist a PREPARED intent before entering the V4 tick;
2. V4 may atomically commit the Agency/cycle transition;
3. V6 cognition may run and then persist its receipt;
4. the caller marks the intent CLOSED in the *same SQLite transaction* as the V6 receipt;
5. after restart, classify any surviving PREPARED intent by exact DB evidence.

A PREPARED intent plus a committed V4 cycle and no V6 closure is explicitly
RECOVERY_REQUIRED_POST_V4_COMMIT. Provider-call state is UNKNOWN and same-tick retry is
not authorized. This module does not mint canonical truth, effects, completion, or model
runtime credit.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import hashlib
import json
import sqlite3
import time

SCHEMA = "GRID10_V6_CRASH_RECONCILIATION/v1"
INTENT_TABLE = "grid10_v6_cycle_intents"
STATUS_PREPARED = "PREPARED"
STATUS_CLOSED = "CLOSED"
STATUS_RECOVERY_REQUIRED = "RECOVERY_REQUIRED_POST_V4_COMMIT"
STATUS_ABORTED_BEFORE_V4_COMMIT = "ABORTED_BEFORE_V4_COMMIT"
STATUS_INCONSISTENT = "INCONSISTENT_EVIDENCE"


class CrashReconciliationError(RuntimeError):
    pass


class DuplicateCycleIntent(CrashReconciliationError):
    pass


class RecoveryMutationNotAuthorized(CrashReconciliationError):
    pass


@dataclass(frozen=True)
class CycleIntentClassification:
    tick_id: str
    status: str
    v4_cycle_present: bool
    v6_closure_present: bool
    provider_calls_status: str
    same_tick_retry_authorized: bool
    reason: str
    evidence: Mapping[str, Any]
    digest: str


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None, timeout=10.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def install_reconciliation_schema(path: Path) -> None:
    con = _connect(Path(path))
    try:
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {INTENT_TABLE}(
              tick_id TEXT PRIMARY KEY,
              schema TEXT NOT NULL,
              expected_agency_epoch INTEGER NOT NULL,
              control_epoch INTEGER NOT NULL,
              control_snapshot_digest TEXT NOT NULL,
              status TEXT NOT NULL,
              prepared_ts REAL NOT NULL,
              terminal_ts REAL,
              classification_json TEXT,
              classification_digest TEXT,
              closure_receipt_digest TEXT
            )
            """
        )
    finally:
        con.close()


def prepare_cycle_intent(
    path: Path,
    *,
    tick_id: str,
    expected_agency_epoch: int,
    control_epoch: int,
    control_snapshot_digest: str,
    prepared_ts: float | None = None,
) -> None:
    """Persist a create-once PREPARED record before V4 can commit the tick."""
    install_reconciliation_schema(path)
    con = _connect(Path(path))
    try:
        con.execute("BEGIN IMMEDIATE")
        try:
            con.execute(
                f"INSERT INTO {INTENT_TABLE} VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    tick_id,
                    SCHEMA,
                    int(expected_agency_epoch),
                    int(control_epoch),
                    str(control_snapshot_digest),
                    STATUS_PREPARED,
                    time.time() if prepared_ts is None else float(prepared_ts),
                    None,
                    None,
                    None,
                    None,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateCycleIntent(f"DUPLICATE_CYCLE_INTENT:{tick_id}") from exc
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()


def mark_intent_closed_in_transaction(
    con: sqlite3.Connection,
    *,
    tick_id: str,
    closure_receipt_digest: str,
    terminal_ts: float | None = None,
) -> None:
    """Mark CLOSED using the caller's existing transaction.

    The V6 receipt INSERT and this UPDATE must share one transaction. If either fails,
    both must roll back. This helper intentionally never commits on its own.
    """
    changed = con.execute(
        f"""UPDATE {INTENT_TABLE}
            SET status=?,terminal_ts=?,closure_receipt_digest=?
            WHERE tick_id=? AND status=?""",
        (
            STATUS_CLOSED,
            time.time() if terminal_ts is None else float(terminal_ts),
            str(closure_receipt_digest),
            tick_id,
            STATUS_PREPARED,
        ),
    ).rowcount
    if changed != 1:
        row = con.execute(
            f"SELECT status,closure_receipt_digest FROM {INTENT_TABLE} WHERE tick_id=?",
            (tick_id,),
        ).fetchone()
        if row is not None and row["status"] == STATUS_CLOSED and row["closure_receipt_digest"] == str(closure_receipt_digest):
            return
        raise CrashReconciliationError(f"INTENT_CLOSE_CONFLICT:{tick_id}")


def _row_or_none(con: sqlite3.Connection, sql: str, args: tuple[Any, ...]) -> sqlite3.Row | None:
    try:
        return con.execute(sql, args).fetchone()
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc).lower():
            return None
        raise


def classify_cycle_intent(path: Path, *, tick_id: str) -> CycleIntentClassification:
    """Read exact V4/V6 evidence and classify one prepared/closed intent.

    This function is read-only. It does not assume the current process owns recovery.
    """
    con = _connect(Path(path))
    try:
        intent = con.execute(
            f"SELECT * FROM {INTENT_TABLE} WHERE tick_id=?",
            (tick_id,),
        ).fetchone()
        if intent is None:
            raise CrashReconciliationError(f"MISSING_CYCLE_INTENT:{tick_id}")
        base = _row_or_none(
            con,
            "SELECT agency_epoch_before,agency_epoch_after FROM grid10_cognitive_cycles WHERE tick_id=?",
            (tick_id,),
        )
        closure = _row_or_none(
            con,
            "SELECT agency_epoch_after,control_epoch,control_snapshot_digest,receipt_digest FROM grid10_v6_control_bound_receipts WHERE tick_id=?",
            (tick_id,),
        )
    finally:
        con.close()

    v4 = base is not None
    v6 = closure is not None
    mismatches: list[str] = []
    if base is not None and int(base["agency_epoch_before"]) != int(intent["expected_agency_epoch"]):
        mismatches.append("V4_AGENCY_EPOCH_BEFORE_MISMATCH")
    if closure is not None and base is not None and int(closure["agency_epoch_after"]) != int(base["agency_epoch_after"]):
        mismatches.append("V4_V6_AGENCY_EPOCH_AFTER_MISMATCH")
    if closure is not None and int(closure["control_epoch"]) != int(intent["control_epoch"]):
        mismatches.append("CONTROL_EPOCH_MISMATCH")
    if closure is not None and str(closure["control_snapshot_digest"]) != str(intent["control_snapshot_digest"]):
        mismatches.append("CONTROL_SNAPSHOT_DIGEST_MISMATCH")
    if intent["status"] == STATUS_CLOSED:
        if closure is None:
            mismatches.append("INTENT_CLOSED_WITHOUT_V6_CLOSURE")
        elif intent["closure_receipt_digest"] != closure["receipt_digest"]:
            mismatches.append("INTENT_CLOSURE_DIGEST_MISMATCH")

    if mismatches or (v6 and not v4):
        status = STATUS_INCONSISTENT
        reason = "EVIDENCE_MISMATCH_OR_CLOSURE_WITHOUT_V4"
        provider_calls_status = "UNKNOWN"
    elif v4 and v6:
        status = STATUS_CLOSED
        reason = "V4_AND_MATCHING_V6_CLOSURE_PRESENT"
        provider_calls_status = "BOUNDED_BY_V6_RECEIPT"
    elif v4 and not v6:
        status = STATUS_RECOVERY_REQUIRED
        reason = "V4_COMMITTED_BUT_V6_CLOSURE_ABSENT"
        provider_calls_status = "UNKNOWN_AFTER_PROCESS_INTERRUPTION"
    else:
        status = STATUS_ABORTED_BEFORE_V4_COMMIT
        reason = "NO_V4_COMMIT_OBSERVED_FOR_PREPARED_INTENT"
        provider_calls_status = "ZERO_BY_ORDERING_IF_PROTOCOL_WAS_FOLLOWED"

    evidence = {
        "schema": SCHEMA,
        "tick_id": tick_id,
        "intent_status": intent["status"],
        "expected_agency_epoch": int(intent["expected_agency_epoch"]),
        "control_epoch": int(intent["control_epoch"]),
        "control_snapshot_digest": str(intent["control_snapshot_digest"]),
        "v4_cycle_present": v4,
        "v4_agency_epoch_before": None if base is None else int(base["agency_epoch_before"]),
        "v4_agency_epoch_after": None if base is None else int(base["agency_epoch_after"]),
        "v6_closure_present": v6,
        "v6_agency_epoch_after": None if closure is None else int(closure["agency_epoch_after"]),
        "v6_control_epoch": None if closure is None else int(closure["control_epoch"]),
        "v6_control_snapshot_digest": None if closure is None else str(closure["control_snapshot_digest"]),
        "v6_receipt_digest": None if closure is None else str(closure["receipt_digest"]),
        "mismatches": mismatches,
        "provider_calls_status": provider_calls_status,
        "same_tick_retry_authorized": False,
        "canonical_truth_minted": False,
        "external_effect_executed": False,
        "completion_minted": False,
    }
    return CycleIntentClassification(
        tick_id=tick_id,
        status=status,
        v4_cycle_present=v4,
        v6_closure_present=v6,
        provider_calls_status=provider_calls_status,
        same_tick_retry_authorized=False,
        reason=reason,
        evidence=evidence,
        digest=_digest(evidence),
    )


def persist_recovery_classification(
    path: Path,
    *,
    tick_id: str,
    exclusive_recovery_authorized: bool,
    terminal_ts: float | None = None,
) -> CycleIntentClassification:
    """Persist a reconciliation result only under an external exclusive-recovery gate.

    The boolean is deliberately explicit: this module cannot prove process/lease ownership.
    Callers must bind it to the real coordinator/heartbeat lease before using this mutator.
    """
    if not exclusive_recovery_authorized:
        raise RecoveryMutationNotAuthorized("EXCLUSIVE_RECOVERY_AUTHORIZATION_REQUIRED")
    result = classify_cycle_intent(path, tick_id=tick_id)
    con = _connect(Path(path))
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            f"SELECT status FROM {INTENT_TABLE} WHERE tick_id=?",
            (tick_id,),
        ).fetchone()
        if row is None:
            raise CrashReconciliationError(f"MISSING_CYCLE_INTENT:{tick_id}")
        if row["status"] == STATUS_CLOSED and result.status != STATUS_CLOSED:
            raise CrashReconciliationError(f"CLOSED_INTENT_CANNOT_REGRESS:{tick_id}")
        con.execute(
            f"""UPDATE {INTENT_TABLE}
                SET status=?,terminal_ts=?,classification_json=?,classification_digest=?
                WHERE tick_id=?""",
            (
                result.status,
                time.time() if terminal_ts is None else float(terminal_ts),
                _canon(result.evidence),
                result.digest,
                tick_id,
            ),
        )
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()
    return result


__all__ = [
    "CrashReconciliationError",
    "DuplicateCycleIntent",
    "RecoveryMutationNotAuthorized",
    "CycleIntentClassification",
    "SCHEMA",
    "INTENT_TABLE",
    "STATUS_PREPARED",
    "STATUS_CLOSED",
    "STATUS_RECOVERY_REQUIRED",
    "STATUS_ABORTED_BEFORE_V4_COMMIT",
    "STATUS_INCONSISTENT",
    "install_reconciliation_schema",
    "prepare_cycle_intent",
    "mark_intent_closed_in_transaction",
    "classify_cycle_intent",
    "persist_recovery_classification",
]
