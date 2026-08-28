#!/usr/bin/env python3
"""Canonical Clay work-lease gate for GRID10 V6 post-V4 recovery mutation.

This module does not create, renew, transfer, or release leases. It only verifies an
already-existing lease in the canonical Research-Entity work fabric
(`clay_work_leases`) and uses that proof to authorize persistence of a V6
RECOVERY_REQUIRED_POST_V4_COMMIT classification.

The recovery work identity is deterministic per tick:
    grid10-v6-recovery:<tick_id>

An unrelated valid Clay work lease cannot authorize mutation of another tick.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import hashlib
import json
import sqlite3
import time


SCHEMA = "GRID10_V6_RECOVERY_LEASE_GATE/v1"
ACTIVE_LEASE_STATES = ("CLAIMED", "RUNNING")


class RecoveryLeaseGateError(RuntimeError):
    pass


class RecoveryLeaseNotAuthorized(RecoveryLeaseGateError):
    pass


@dataclass(frozen=True)
class RecoveryLeaseProof:
    tick_id: str
    work_id: str
    spec_rev: int
    executor_node: str
    lease_token_digest: str
    lease_state: str
    claimed_at: str
    expires_at: str
    checked_at: str
    active_same_work_spec_count: int
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


def recovery_work_id_for_tick(tick_id: str) -> str:
    tick = str(tick_id)
    if not tick or "\x00" in tick:
        raise RecoveryLeaseNotAuthorized("INVALID_TICK_ID")
    return f"grid10-v6-recovery:{tick}"


def _require_tables(con: sqlite3.Connection) -> None:
    required = {"clay_work_items", "clay_work_spec_revisions", "clay_work_leases"}
    present = {
        str(row["name"])
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?,?)",
            tuple(sorted(required)),
        )
    }
    missing = sorted(required - present)
    if missing:
        raise RecoveryLeaseNotAuthorized(
            "CANONICAL_WORK_FABRIC_TABLES_MISSING:" + ",".join(missing)
        )


def verify_active_recovery_lease_in_transaction(
    con: sqlite3.Connection,
    *,
    tick_id: str,
    work_id: str,
    spec_rev: int,
    executor_node: str,
    lease_token: str,
    checked_at: str | None = None,
) -> RecoveryLeaseProof:
    """Verify one exact, unique, active canonical work lease.

    The caller must already hold the transaction used for the recovery mutation.
    This verifier never grants authority and never changes lease state.

    `checked_at` exists for deterministic verifier tests and read-only audit callers.
    Mutating recovery persistence must not accept an externally supplied time override.
    """
    _require_tables(con)
    expected_work_id = recovery_work_id_for_tick(tick_id)
    if str(work_id) != expected_work_id:
        raise RecoveryLeaseNotAuthorized(
            f"RECOVERY_WORK_ID_MISMATCH:{work_id}:{expected_work_id}"
        )
    if not str(lease_token):
        raise RecoveryLeaseNotAuthorized("EMPTY_LEASE_TOKEN")
    if not str(executor_node):
        raise RecoveryLeaseNotAuthorized("EMPTY_EXECUTOR_NODE")

    check_ts = checked_at
    if check_ts is None:
        row = con.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ','now') AS ts").fetchone()
        check_ts = str(row["ts"])

    lease = con.execute(
        """SELECT l.lease_id,l.work_id,l.spec_rev,l.executor_node,l.lease_token,
                  l.claimed_at,l.expires_at,l.state,w.terminal_status,s.status AS spec_status
           FROM clay_work_leases l
           JOIN clay_work_items w ON w.work_id=l.work_id
           JOIN clay_work_spec_revisions s ON s.work_id=l.work_id AND s.spec_rev=l.spec_rev
           WHERE l.lease_token=?""",
        (str(lease_token),),
    ).fetchone()
    if lease is None:
        raise RecoveryLeaseNotAuthorized("LEASE_TOKEN_NOT_FOUND")
    if str(lease["work_id"]) != expected_work_id:
        raise RecoveryLeaseNotAuthorized("LEASE_BOUND_TO_DIFFERENT_WORK")
    if int(lease["spec_rev"]) != int(spec_rev):
        raise RecoveryLeaseNotAuthorized("LEASE_SPEC_REV_MISMATCH")
    if str(lease["executor_node"]) != str(executor_node):
        raise RecoveryLeaseNotAuthorized("LEASE_EXECUTOR_MISMATCH")
    if str(lease["state"]) not in ACTIVE_LEASE_STATES:
        raise RecoveryLeaseNotAuthorized(f"LEASE_NOT_ACTIVE_STATE:{lease['state']}")
    if lease["terminal_status"] is not None:
        raise RecoveryLeaseNotAuthorized("WORK_ITEM_TERMINAL")
    if str(lease["spec_status"]) != "READY":
        raise RecoveryLeaseNotAuthorized(f"WORK_SPEC_NOT_READY:{lease['spec_status']}")

    newest = con.execute(
        "SELECT MAX(spec_rev) AS max_rev FROM clay_work_spec_revisions WHERE work_id=?",
        (expected_work_id,),
    ).fetchone()
    if newest is None or newest["max_rev"] is None or int(newest["max_rev"]) != int(spec_rev):
        raise RecoveryLeaseNotAuthorized("LEASE_NOT_ON_NEWEST_SPEC_REV")

    time_check = con.execute(
        """SELECT
             CASE WHEN julianday(?) IS NOT NULL
                       AND julianday(?) IS NOT NULL
                       AND julianday(?) IS NOT NULL
                       AND julianday(?) <= julianday(?)
                       AND julianday(?) > julianday(?)
                  THEN 1 ELSE 0 END AS valid_time""",
        (
            str(lease["claimed_at"]),
            str(lease["expires_at"]),
            str(check_ts),
            str(lease["claimed_at"]),
            str(check_ts),
            str(lease["expires_at"]),
            str(check_ts),
        ),
    ).fetchone()
    if time_check is None or int(time_check["valid_time"]) != 1:
        raise RecoveryLeaseNotAuthorized("LEASE_TIME_WINDOW_INVALID_OR_EXPIRED")

    active_count_row = con.execute(
        """SELECT COUNT(*) AS n
           FROM clay_work_leases
           WHERE work_id=? AND spec_rev=?
             AND state IN ('CLAIMED','RUNNING')
             AND julianday(claimed_at) IS NOT NULL
             AND julianday(expires_at) IS NOT NULL
             AND julianday(claimed_at) <= julianday(?)
             AND julianday(expires_at) > julianday(?)""",
        (expected_work_id, int(spec_rev), str(check_ts), str(check_ts)),
    ).fetchone()
    active_count = 0 if active_count_row is None else int(active_count_row["n"])
    if active_count != 1:
        raise RecoveryLeaseNotAuthorized(
            f"AMBIGUOUS_ACTIVE_LEASE_COUNT:{active_count}"
        )

    evidence: Mapping[str, Any] = {
        "schema": SCHEMA,
        "tick_id": str(tick_id),
        "work_id": expected_work_id,
        "spec_rev": int(spec_rev),
        "executor_node": str(executor_node),
        "lease_token_digest": hashlib.sha256(str(lease_token).encode("utf-8")).hexdigest(),
        "lease_state": str(lease["state"]),
        "claimed_at": str(lease["claimed_at"]),
        "expires_at": str(lease["expires_at"]),
        "checked_at": str(check_ts),
        "active_same_work_spec_count": active_count,
        "lease_authority_created_by_gate": False,
        "lease_state_mutated_by_gate": False,
    }
    return RecoveryLeaseProof(
        tick_id=str(tick_id),
        work_id=expected_work_id,
        spec_rev=int(spec_rev),
        executor_node=str(executor_node),
        lease_token_digest=str(evidence["lease_token_digest"]),
        lease_state=str(lease["state"]),
        claimed_at=str(lease["claimed_at"]),
        expires_at=str(lease["expires_at"]),
        checked_at=str(check_ts),
        active_same_work_spec_count=active_count,
        digest=_digest(evidence),
    )


def persist_recovery_classification_with_canonical_lease(
    path: Path,
    *,
    tick_id: str,
    work_id: str,
    spec_rev: int,
    executor_node: str,
    lease_token: str,
    checked_at: str | None = None,
    terminal_ts: float | None = None,
):
    """Persist V6 recovery classification only under a verified canonical Clay work lease.

    This is intentionally narrower than the legacy boolean-gated mutator. It can persist
    only RECOVERY_REQUIRED_POST_V4_COMMIT and records the lease proof in the classification
    envelope. It never creates or renews a lease.

    A mutating caller may not supply `checked_at`. Lease freshness for persistence is
    evaluated from SQLite/runtime time inside the same writer transaction. This prevents a
    stale or compromised caller from authorizing mutation by replaying a historical time.
    """
    if checked_at is not None:
        raise RecoveryLeaseNotAuthorized("EXTERNAL_CHECKED_AT_OVERRIDE_FORBIDDEN")

    from grid10_v6_crash_reconciliation_v1 import (
        INTENT_TABLE,
        STATUS_RECOVERY_REQUIRED,
        classify_cycle_intent,
    )

    con = _connect(Path(path))
    try:
        con.execute("BEGIN IMMEDIATE")
        proof = verify_active_recovery_lease_in_transaction(
            con,
            tick_id=tick_id,
            work_id=work_id,
            spec_rev=spec_rev,
            executor_node=executor_node,
            lease_token=lease_token,
            checked_at=None,
        )
        # BEGIN IMMEDIATE holds the writer lock while this separate read connection
        # classifies exact committed V4/V6 evidence; competing writers cannot change it.
        result = classify_cycle_intent(Path(path), tick_id=tick_id)
        if result.status != STATUS_RECOVERY_REQUIRED:
            raise RecoveryLeaseNotAuthorized(
                f"RECOVERY_MUTATION_REQUIRES_RECOVERY_REQUIRED:{result.status}"
            )
        row = con.execute(
            f"SELECT status FROM {INTENT_TABLE} WHERE tick_id=?",
            (tick_id,),
        ).fetchone()
        if row is None:
            raise RecoveryLeaseNotAuthorized(f"MISSING_CYCLE_INTENT:{tick_id}")

        envelope = {
            "schema": "GRID10_V6_RECOVERY_CLASSIFICATION_WITH_LEASE/v1",
            "classification": dict(result.evidence),
            "classification_digest": result.digest,
            "lease_proof": {
                "schema": SCHEMA,
                "tick_id": proof.tick_id,
                "work_id": proof.work_id,
                "spec_rev": proof.spec_rev,
                "executor_node": proof.executor_node,
                "lease_token_digest": proof.lease_token_digest,
                "lease_state": proof.lease_state,
                "claimed_at": proof.claimed_at,
                "expires_at": proof.expires_at,
                "checked_at": proof.checked_at,
                "active_same_work_spec_count": proof.active_same_work_spec_count,
                "digest": proof.digest,
            },
            "same_tick_retry_authorized": False,
            "canonical_truth_minted": False,
            "external_effect_executed": False,
            "completion_minted": False,
        }
        envelope_digest = _digest(envelope)
        con.execute(
            f"""UPDATE {INTENT_TABLE}
                SET status=?,terminal_ts=?,classification_json=?,classification_digest=?
                WHERE tick_id=? AND status!='CLOSED'""",
            (
                STATUS_RECOVERY_REQUIRED,
                time.time() if terminal_ts is None else float(terminal_ts),
                _canon(envelope),
                envelope_digest,
                tick_id,
            ),
        )
        if con.total_changes != 1:
            raise RecoveryLeaseNotAuthorized(
                f"RECOVERY_INTENT_UPDATE_CONFLICT:{tick_id}"
            )
        con.execute("COMMIT")
        return result, proof, envelope_digest
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()


__all__ = [
    "RecoveryLeaseGateError",
    "RecoveryLeaseNotAuthorized",
    "RecoveryLeaseProof",
    "SCHEMA",
    "ACTIVE_LEASE_STATES",
    "recovery_work_id_for_tick",
    "verify_active_recovery_lease_in_transaction",
    "persist_recovery_classification_with_canonical_lease",
]
