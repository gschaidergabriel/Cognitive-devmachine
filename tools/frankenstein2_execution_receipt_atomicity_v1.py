#!/usr/bin/env python3
"""Atomic persistence for Frankenstein 2.0 execution receipt identity bundles.

The existing effect lifecycle owns the SQLite store and effect identity. This helper does
not create a second store or effect authority. Production calls delegate to the lifecycle's
native atomic execution-bundle writer; the private-SQL fallback exists only for compatible
stores and the deterministic injected-failure regression seam.

A failure after the first logical insert must roll back both logical records. The optional
injected-failure flag exists only as a deterministic regression seam; production callers
must leave it false.
"""
from __future__ import annotations

import sqlite3
import time
from typing import Any

try:
    from .frankenstein2_effect_lifecycle_v1 import EffectLifecycleError, PendingEffectState
except ImportError:
    from frankenstein2_effect_lifecycle_v1 import EffectLifecycleError, PendingEffectState

SCHEMA = "FRANKENSTEIN2_EXECUTION_RECEIPT_ATOMICITY/v1"


def _require_text(name: str, value: str) -> str:
    value = str(value or "").strip()
    if not value:
        raise EffectLifecycleError(f"MISSING_{name.upper()}")
    return value


def record_execution_bundle_atomic(
    store: Any,
    invocation_id: str,
    *,
    executable_id: str,
    command_digest: str,
    environment_id: str,
    exit_code: int,
    result_digest: str,
    source_digest: str,
    duplicate_state: str,
    status: str,
    now_ts: float | None = None,
    _inject_failure_after_base_insert: bool = False,
) -> None:
    """Commit base ExecutionReceipt and v2 metadata as one identity bundle.

    Real ``EffectLifecycleStore`` instances expose ``record_execution_bundle`` and are
    delegated to directly, preserving one production writer authority. A compatible fake
    may expose the same method. The lower private-SQL path is retained only for legacy
    compatible stores and for deterministic failure injection, where it proves SQLite
    rollback across the two logical inserts without invoking an external effect twice.
    """
    invocation_id = _require_text("invocation_id", invocation_id)
    executable_id = _require_text("executable_id", executable_id)
    command_digest = _require_text("command_digest", command_digest)
    environment_id = _require_text("environment_id", environment_id)
    result_digest = _require_text("result_digest", result_digest)
    source_digest = _require_text("execution_source_digest", source_digest)
    duplicate_state = _require_text("execution_duplicate_state", duplicate_state)
    status = _require_text("execution_status", status)
    ts = time.time() if now_ts is None else float(now_ts)

    if status == "SUCCEEDED" and int(exit_code) != 0:
        raise EffectLifecycleError("SUCCEEDED_STATUS_CONTRADICTS_NONZERO_EXIT")

    native_bundle_writer = getattr(store, "record_execution_bundle", None)
    if callable(native_bundle_writer) and not _inject_failure_after_base_insert:
        native_bundle_writer(
            invocation_id,
            executable_id=executable_id,
            command_digest=command_digest,
            environment_id=environment_id,
            exit_code=int(exit_code),
            result_digest=result_digest,
            source_digest=source_digest,
            duplicate_state=duplicate_state,
            status=status,
            now_ts=now_ts,
        )
        return

    native_atomic_writer = getattr(store, "record_execution_bundle_atomic", None)
    if callable(native_atomic_writer):
        native_atomic_writer(
            invocation_id,
            executable_id=executable_id,
            command_digest=command_digest,
            environment_id=environment_id,
            exit_code=int(exit_code),
            result_digest=result_digest,
            source_digest=source_digest,
            duplicate_state=duplicate_state,
            status=status,
            now_ts=now_ts,
            _inject_failure_after_base_insert=_inject_failure_after_base_insert,
        )
        return

    if not hasattr(store, "_con") or not hasattr(store, "_require_request") or not hasattr(store, "_event"):
        raise EffectLifecycleError("ATOMIC_EXECUTION_BUNDLE_REQUIRES_LIFECYCLE_STORE")

    con = store._con()
    try:
        con.execute("BEGIN IMMEDIATE")
        req = store._require_request(con, invocation_id)
        if req["pending_state"] != PendingEffectState.SUBMITTED.value:
            raise EffectLifecycleError("EXECUTION_RECEIPT_REQUIRES_SUBMITTED")

        base = con.execute(
            "SELECT request_digest FROM execution_receipts WHERE invocation_id=?",
            (invocation_id,),
        ).fetchone()
        meta = con.execute(
            "SELECT source_digest FROM execution_v2_metadata WHERE invocation_id=?",
            (invocation_id,),
        ).fetchone()
        if base is not None or meta is not None:
            if (base is None) != (meta is None):
                raise EffectLifecycleError("PARTIAL_EXECUTION_BUNDLE_STATE")
            raise EffectLifecycleError("EXECUTION_BUNDLE_ALREADY_FINAL")

        con.execute(
            "INSERT INTO execution_receipts VALUES(?,?,?,?,?,?,?,?)",
            (
                invocation_id,
                req["request_digest"],
                executable_id,
                command_digest,
                environment_id,
                int(exit_code),
                result_digest,
                ts,
            ),
        )
        store._event(
            con,
            invocation_id,
            "EXECUTION_RECORDED",
            {
                "exit_code": int(exit_code),
                "result_digest": result_digest,
                "atomic_bundle_schema": SCHEMA,
            },
            ts,
        )

        if _inject_failure_after_base_insert:
            raise EffectLifecycleError("INJECTED_FAILURE_AFTER_BASE_EXECUTION_RECEIPT")

        con.execute(
            "INSERT INTO execution_v2_metadata VALUES(?,?,?,?,?)",
            (invocation_id, source_digest, duplicate_state, status, ts),
        )
        store._event(
            con,
            invocation_id,
            "EXECUTION_V2_METADATA_RECORDED",
            {
                "source_digest": source_digest,
                "duplicate_state": duplicate_state,
                "status": status,
                "atomic_bundle_schema": SCHEMA,
            },
            ts,
        )
        con.execute("COMMIT")
    except sqlite3.IntegrityError as exc:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise EffectLifecycleError("EXECUTION_BUNDLE_IDENTITY_CONFLICT") from exc
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()


__all__ = ["SCHEMA", "record_execution_bundle_atomic"]
