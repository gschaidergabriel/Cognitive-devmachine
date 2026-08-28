#!/usr/bin/env python3
"""GRID10 unified cognitive runtime v7: durable attempt identity + crash-window reconciliation.

v7 is a narrow wrapper around v6. It does not create another Agency, wake, control,
GWT, truth, effect or completion authority. Before entering v6 it records one durable
attempt row for the tick. The v6/V4 path remains unchanged. On normal return the attempt
is closed against the already-persisted v6 receipt.

The purpose of the extra attempt row is recovery observability. If a process disappears
after V4 committed the Agency/cognitive-cycle row but before v6 could persist its closure,
a later v7 re-entry can prove that exact asymmetry and write a typed recovery receipt with
cognitive outcome UNKNOWN. It never replays the same tick and never upgrades the recovered
row to model/runtime/completion credit.

Fresh PREPARED attempts are not auto-reconciled because another process may still own them.
Only attempts older than ``recovery_stale_after_seconds`` are eligible for background
reconciliation; the current caller may force reconciliation after an exception because it
knows its own call has already terminated.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
import hashlib
import json
import sqlite3
import time

from grid10_cognitive_unified_runtime_v6 import (
    UnifiedCognitiveRuntimeV6,
    UnifiedCycleResultV6,
    build_unified_cognitive_runtime_v6,
)
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceResult

SCHEMA = "GRID10_UNIFIED_COGNITIVE_RUNTIME/v7"
ATTEMPT_SCHEMA = "GRID10_V7_COGNITIVE_ATTEMPT/v1"
RECOVERY_SCHEMA = "GRID10_V7_RECOVERY_CLOSURE/v1"


class CognitiveAttemptConflict(RuntimeError):
    """The tick already has a v7 attempt identity and may not be replayed."""


class CognitiveAttemptRecoveryError(RuntimeError):
    """A v7 attempt could not be closed or reconciled fail-closed."""


@dataclass(frozen=True)
class RecoveryClosure:
    tick_id: str
    status: str
    closure_kind: str
    receipt_digest: str | None
    receipt: Mapping[str, Any] | None


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


def _init_v7_schema(path: Path) -> None:
    con = _connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS grid10_v7_cycle_attempts(
              tick_id TEXT PRIMARY KEY,
              attempt_schema TEXT NOT NULL,
              status TEXT NOT NULL,
              agency_epoch_at_prepare INTEGER NOT NULL,
              prepared_ts REAL NOT NULL,
              closed_ts REAL,
              closure_kind TEXT,
              inner_receipt_digest TEXT,
              recovery_receipt_json TEXT,
              recovery_receipt_digest TEXT
            )
            """
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_grid10_v7_attempt_status_ts "
            "ON grid10_v7_cycle_attempts(status,prepared_ts)"
        )
    finally:
        con.close()


class UnifiedCognitiveRuntimeV7:
    """Add durable attempt/recovery identity around the existing v6 runtime."""

    def __init__(
        self,
        runtime_v6: UnifiedCognitiveRuntimeV6,
        *,
        recovery_stale_after_seconds: float = 60.0,
    ):
        self.runtime_v6 = runtime_v6
        self.runtime_v4 = runtime_v6.runtime_v4
        self.agency = runtime_v6.agency
        self.control_plane = runtime_v6.control_plane
        self.inference_fn = runtime_v6.inference_fn
        self.cognitive_config = runtime_v6.cognitive_config
        self.unified_db = Path(runtime_v6.unified_db)
        self.recovery_stale_after_seconds = max(0.0, float(recovery_stale_after_seconds))
        _init_v7_schema(self.unified_db)
        self.last_recovery_closures = self.reconcile_pending_attempts()

    def _prepare_attempt(self, *, tick_id: str) -> None:
        con = _connect(self.unified_db)
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT state_epoch FROM agency_meta WHERE singleton=1").fetchone()
            if row is None:
                raise CognitiveAttemptRecoveryError("MISSING_AGENCY_META_AT_V7_PREPARE")
            try:
                con.execute(
                    "INSERT INTO grid10_v7_cycle_attempts VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        tick_id,
                        ATTEMPT_SCHEMA,
                        "PREPARED",
                        int(row["state_epoch"]),
                        time.time(),
                        None,
                        None,
                        None,
                        None,
                        None,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise CognitiveAttemptConflict(f"V7_TICK_ALREADY_ATTEMPTED:{tick_id}") from exc
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def _close_from_existing_v6_receipt(
        self,
        *,
        tick_id: str,
        status: str,
        closure_kind: str,
    ) -> RecoveryClosure | None:
        con = _connect(self.unified_db)
        try:
            con.execute("BEGIN IMMEDIATE")
            attempt = con.execute(
                "SELECT status FROM grid10_v7_cycle_attempts WHERE tick_id=?",
                (tick_id,),
            ).fetchone()
            if attempt is None:
                raise CognitiveAttemptRecoveryError(f"MISSING_V7_ATTEMPT:{tick_id}")
            if attempt["status"] != "PREPARED":
                con.execute("COMMIT")
                return None
            v6 = con.execute(
                "SELECT receipt_digest FROM grid10_v6_control_bound_receipts WHERE tick_id=?",
                (tick_id,),
            ).fetchone()
            if v6 is None:
                con.execute("ROLLBACK")
                return None
            changed = con.execute(
                """UPDATE grid10_v7_cycle_attempts
                   SET status=?,closed_ts=?,closure_kind=?,inner_receipt_digest=?
                   WHERE tick_id=? AND status='PREPARED'""",
                (status, time.time(), closure_kind, str(v6["receipt_digest"]), tick_id),
            ).rowcount
            con.execute("COMMIT")
            if changed != 1:
                return None
            return RecoveryClosure(
                tick_id=tick_id,
                status=status,
                closure_kind=closure_kind,
                receipt_digest=str(v6["receipt_digest"]),
                receipt=None,
            )
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def _reconcile_attempt(self, *, tick_id: str, force: bool = False, now_ts: float | None = None) -> RecoveryClosure | None:
        now = time.time() if now_ts is None else float(now_ts)
        con = _connect(self.unified_db)
        try:
            con.execute("BEGIN IMMEDIATE")
            attempt = con.execute(
                "SELECT * FROM grid10_v7_cycle_attempts WHERE tick_id=?",
                (tick_id,),
            ).fetchone()
            if attempt is None or attempt["status"] != "PREPARED":
                con.execute("COMMIT")
                return None
            age = max(0.0, now - float(attempt["prepared_ts"]))
            if not force and age < self.recovery_stale_after_seconds:
                con.execute("COMMIT")
                return None

            v6 = con.execute(
                "SELECT receipt_digest FROM grid10_v6_control_bound_receipts WHERE tick_id=?",
                (tick_id,),
            ).fetchone()
            if v6 is not None:
                status = "RECOVERED_FROM_EXISTING_V6_RECEIPT"
                closure_kind = "V6_RECEIPT_ALREADY_DURABLE"
                changed = con.execute(
                    """UPDATE grid10_v7_cycle_attempts
                       SET status=?,closed_ts=?,closure_kind=?,inner_receipt_digest=?
                       WHERE tick_id=? AND status='PREPARED'""",
                    (status, now, closure_kind, str(v6["receipt_digest"]), tick_id),
                ).rowcount
                con.execute("COMMIT")
                if changed != 1:
                    return None
                return RecoveryClosure(
                    tick_id=tick_id,
                    status=status,
                    closure_kind=closure_kind,
                    receipt_digest=str(v6["receipt_digest"]),
                    receipt=None,
                )

            v4 = con.execute(
                """SELECT agency_epoch_before,agency_epoch_after,assurance_mode,next_action,
                          woken_goal_ids_json,checkpoint_json,next_tick_not_before
                   FROM grid10_cognitive_cycles WHERE tick_id=?""",
                (tick_id,),
            ).fetchone()
            current_agency = con.execute(
                "SELECT state_epoch FROM agency_meta WHERE singleton=1"
            ).fetchone()
            current_agency_epoch = int(current_agency["state_epoch"]) if current_agency is not None else None

            if v4 is not None:
                checkpoint = json.loads(v4["checkpoint_json"])
                receipt = {
                    "schema": RECOVERY_SCHEMA,
                    "runtime_schema": SCHEMA,
                    "tick_id": tick_id,
                    "reason": "V4_COMMIT_PRESENT_V6_CLOSURE_ABSENT_ON_RECONCILIATION",
                    "closure_kind": "POST_V4_COMMIT_COGNITIVE_OUTCOME_UNKNOWN",
                    "agency_epoch_at_prepare": int(attempt["agency_epoch_at_prepare"]),
                    "agency_epoch_before_v4": int(v4["agency_epoch_before"]),
                    "agency_epoch_after_v4": int(v4["agency_epoch_after"]),
                    "agency_epoch_current": current_agency_epoch,
                    "assurance_mode": str(v4["assurance_mode"]),
                    "next_action": str(v4["next_action"]),
                    "woken_goal_ids": json.loads(v4["woken_goal_ids_json"]),
                    "next_tick_not_before": float(v4["next_tick_not_before"]),
                    "v4_checkpoint_digest": _digest(checkpoint),
                    "v4_control_snapshot": checkpoint.get("control_snapshot"),
                    "cognitive_outcome": "UNKNOWN",
                    "provider_calls": None,
                    "provider_calls_status": "UNKNOWN_AFTER_PROCESS_OR_RECEIPT_GAP",
                    "same_tick_retry_authorized": False,
                    "canonical_truth_minted": False,
                    "external_effect_executed": False,
                    "completion_minted": False,
                }
                status = "RECOVERED_POST_V4_COMMIT_UNKNOWN"
                closure_kind = "POST_V4_COMMIT_V6_RECEIPT_MISSING"
            else:
                possible_precycle_agency_mutation = (
                    current_agency_epoch is not None
                    and current_agency_epoch != int(attempt["agency_epoch_at_prepare"])
                )
                receipt = {
                    "schema": RECOVERY_SCHEMA,
                    "runtime_schema": SCHEMA,
                    "tick_id": tick_id,
                    "reason": "V7_PREPARED_BUT_NO_V4_CYCLE_ROW_ON_RECONCILIATION",
                    "closure_kind": "PRE_V4_CYCLE_COMMIT_OUTCOME_UNKNOWN",
                    "agency_epoch_at_prepare": int(attempt["agency_epoch_at_prepare"]),
                    "agency_epoch_current": current_agency_epoch,
                    "possible_precycle_agency_mutation": possible_precycle_agency_mutation,
                    "cognitive_outcome": "NOT_ESTABLISHED",
                    "provider_calls": None,
                    "provider_calls_status": "NO_V6_RECEIPT",
                    "same_tick_retry_authorized": False,
                    "canonical_truth_minted": False,
                    "external_effect_executed": False,
                    "completion_minted": False,
                }
                status = "RECOVERED_PRE_V4_CYCLE_COMMIT_UNKNOWN"
                closure_kind = "NO_V4_CYCLE_ROW"

            receipt_digest = _digest(receipt)
            receipt["receipt_digest"] = receipt_digest
            changed = con.execute(
                """UPDATE grid10_v7_cycle_attempts
                   SET status=?,closed_ts=?,closure_kind=?,recovery_receipt_json=?,recovery_receipt_digest=?
                   WHERE tick_id=? AND status='PREPARED'""",
                (
                    status,
                    now,
                    closure_kind,
                    _canon(receipt),
                    receipt_digest,
                    tick_id,
                ),
            ).rowcount
            con.execute("COMMIT")
            if changed != 1:
                return None
            return RecoveryClosure(
                tick_id=tick_id,
                status=status,
                closure_kind=closure_kind,
                receipt_digest=receipt_digest,
                receipt=receipt,
            )
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def reconcile_pending_attempts(
        self,
        *,
        force: bool = False,
        now_ts: float | None = None,
    ) -> tuple[RecoveryClosure, ...]:
        now = time.time() if now_ts is None else float(now_ts)
        con = _connect(self.unified_db)
        try:
            rows = con.execute(
                "SELECT tick_id FROM grid10_v7_cycle_attempts WHERE status='PREPARED' ORDER BY prepared_ts,tick_id"
            ).fetchall()
        finally:
            con.close()
        closures = []
        for row in rows:
            closure = self._reconcile_attempt(
                tick_id=str(row["tick_id"]),
                force=force,
                now_ts=now,
            )
            if closure is not None:
                closures.append(closure)
        return tuple(closures)

    def tick_once(
        self,
        *,
        tick_id: str,
        interval: float | None = None,
        hold_interval: float | None = None,
        now_ts: float | None = None,
        observed_events: Iterable[str] = (),
        trusted_axes: Mapping[str, Any] | None = None,
        extra_variables: Mapping[str, Any] | None = None,
        cognitive_context: Mapping[str, Any] | None = None,
    ) -> UnifiedCycleResultV6:
        self._prepare_attempt(tick_id=tick_id)
        try:
            result = self.runtime_v6.tick_once(
                tick_id=tick_id,
                interval=interval,
                hold_interval=hold_interval,
                now_ts=now_ts,
                observed_events=observed_events,
                trusted_axes=trusted_axes,
                extra_variables=extra_variables,
                cognitive_context=cognitive_context,
            )
        except BaseException as exc:
            # For ordinary exceptions this provides immediate closure. SIGKILL/process death
            # cannot execute this block; the durable PREPARED row is intentionally left for
            # stale re-entry reconciliation.
            try:
                self._reconcile_attempt(tick_id=tick_id, force=True)
            except Exception as recovery_exc:
                raise CognitiveAttemptRecoveryError(
                    f"V7_EXCEPTION_AND_RECOVERY_FAILED:{tick_id}:{type(recovery_exc).__name__}"
                ) from exc
            raise

        closed = self._close_from_existing_v6_receipt(
            tick_id=tick_id,
            status="CLOSED_SUCCESS",
            closure_kind="V6_RECEIPT_DURABLE",
        )
        if closed is None:
            raise CognitiveAttemptRecoveryError(f"V7_SUCCESS_WITHOUT_CLOSABLE_V6_RECEIPT:{tick_id}")
        return result


def build_unified_cognitive_runtime_v7(
    unified_db: Path,
    *,
    allow_regulator_writes: bool = False,
    inference_fn: Callable[..., GLMInferenceResult] | None = None,
    cognitive_config: CognitiveCycleConfig = CognitiveCycleConfig(),
    recovery_stale_after_seconds: float = 60.0,
):
    fabric, heartbeat_store, agency, runtime_v6, fingerprint = build_unified_cognitive_runtime_v6(
        Path(unified_db),
        allow_regulator_writes=allow_regulator_writes,
        inference_fn=inference_fn,
        cognitive_config=cognitive_config,
    )
    runtime = UnifiedCognitiveRuntimeV7(
        runtime_v6,
        recovery_stale_after_seconds=recovery_stale_after_seconds,
    )
    return fabric, heartbeat_store, agency, runtime, fingerprint


__all__ = [
    "ATTEMPT_SCHEMA",
    "RECOVERY_SCHEMA",
    "CognitiveAttemptConflict",
    "CognitiveAttemptRecoveryError",
    "RecoveryClosure",
    "UnifiedCognitiveRuntimeV7",
    "build_unified_cognitive_runtime_v7",
]
