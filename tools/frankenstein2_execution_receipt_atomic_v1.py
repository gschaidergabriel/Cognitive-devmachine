#!/usr/bin/env python3
"""Atomic Frankenstein 2.0 ExecutionReceipt + v2 metadata writer.

This module closes one narrow post-dispatch crash window without introducing another
state store or effect authority.  It writes the existing ``execution_receipts`` and
``execution_v2_metadata`` rows through the existing EffectLifecycleStore SQLite
connection in ONE ``BEGIN IMMEDIATE`` transaction.

The dispatch callback has already returned when this writer is called.  Therefore any
persistence failure remains outcome-unknown at the dispatch boundary; this module never
retries an external effect and never mints completion.
"""
from __future__ import annotations

import sqlite3
import time
from typing import Any

try:  # package import
    from .frankenstein2_effect_lifecycle_v1 import (
        EffectLifecycleError,
        PendingEffectState,
    )
except ImportError:  # direct tools/PYTHONPATH execution
    from frankenstein2_effect_lifecycle_v1 import (
        EffectLifecycleError,
        PendingEffectState,
    )


SCHEMA = "FRANKENSTEIN2_EXECUTION_RECEIPT_ATOMIC/v1"


def _require_text(name: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise EffectLifecycleError(f"MISSING_{name}")
    return text


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
) -> str:
    """Persist both logical execution records atomically in the existing lifecycle DB.

    Test doubles or future stores may expose a native ``record_execution_bundle_v2``
    method.  The canonical v1 lifecycle store currently exposes its writer primitives
    rather than this method; for that store this function deliberately reuses ``_con``,
    ``_require_request`` and ``_event`` so the existing SQLite authority remains the
    only state boundary.

    Returns the request digest that was bound to the committed bundle.
    """
    invocation_id = _require_text("INVOCATION_ID", invocation_id)
    executable_id = _require_text("EXECUTABLE_ID", executable_id)
    command_digest = _require_text("COMMAND_DIGEST", command_digest)
    environment_id = _require_text("ENVIRONMENT_ID", environment_id)
    result_digest = _require_text("RESULT_DIGEST", result_digest)
    source_digest = _require_text("EXECUTION_SOURCE_DIGEST", source_digest)
    duplicate_state = _require_text("EXECUTION_DUPLICATE_STATE", duplicate_state)
    status = _require_text("EXECUTION_STATUS", status)
    exit_code = int(exit_code)
    if status == "SUCCEEDED" and exit_code != 0:
        raise EffectLifecycleError("SUCCEEDED_STATUS_CONTRADICTS_NONZERO_EXIT")

    native_bundle_writer = getattr(store, "record_execution_bundle_v2", None)
    if callable(native_bundle_writer):
        return str(
            native_bundle_writer(
                invocation_id,
                executable_id=executable_id,
                command_digest=command_digest,
                environment_id=environment_id,
                exit_code=exit_code,
                result_digest=result_digest,
                source_digest=source_digest,
                duplicate_state=duplicate_state,
                status=status,
                now_ts=now_ts,
            )
            or ""
        )

    required = ("_con", "_require_request", "_event")
    if any(not callable(getattr(store, name, None)) for name in required):
        raise EffectLifecycleError("ATOMIC_EXECUTION_WRITER_UNAVAILABLE")

    ts = time.time() if now_ts is None else float(now_ts)
    con = store._con()
    try:
        con.execute("BEGIN IMMEDIATE")
        req = store._require_request(con, invocation_id)
        if req["pending_state"] != PendingEffectState.SUBMITTED.value:
            raise EffectLifecycleError("EXECUTION_BUNDLE_REQUIRES_SUBMITTED")

        base_existing = con.execute(
            "SELECT 1 FROM execution_receipts WHERE invocation_id=?",
            (invocation_id,),
        ).fetchone()
        v2_existing = con.execute(
            "SELECT 1 FROM execution_v2_metadata WHERE invocation_id=?",
            (invocation_id,),
        ).fetchone()
        if base_existing is not None or v2_existing is not None:
            # Never silently finish or normalize a legacy partial receipt.  That state
            # requires explicit recovery/reconciliation because the external effect has
            # already crossed the submission boundary.
            raise EffectLifecycleError("EXECUTION_BUNDLE_ALREADY_FINAL_OR_PARTIAL")

        request_digest = str(req["request_digest"])
        generation = int(req["generation"])
        con.execute(
            "INSERT INTO execution_receipts VALUES(?,?,?,?,?,?,?,?)",
            (
                invocation_id,
                request_digest,
                executable_id,
                command_digest,
                environment_id,
                exit_code,
                result_digest,
                ts,
            ),
        )
        store._event(
            con,
            invocation_id,
            "EXECUTION_RECORDED",
            {
                "exit_code": exit_code,
                "result_digest": result_digest,
                "atomic_bundle_schema": SCHEMA,
            },
            ts,
        )

        # This is the second logical insert and the intentional injected-failure point
        # used by the deterministic regression.  Both this row AND the prior base row
        # must disappear on any exception before COMMIT.
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
        store._event(
            con,
            invocation_id,
            "EXECUTION_BUNDLE_RECORDED",
            {
                "schema": SCHEMA,
                "request_digest": request_digest,
                "source_digest": source_digest,
                "generation": generation,
                "status": status,
                "duplicate_state": duplicate_state,
                "result_digest": result_digest,
                "base_and_v2_same_transaction": True,
            },
            ts,
        )

        base = con.execute(
            "SELECT request_digest,result_digest,exit_code FROM execution_receipts WHERE invocation_id=?",
            (invocation_id,),
        ).fetchone()
        meta = con.execute(
            "SELECT source_digest,duplicate_state,status FROM execution_v2_metadata WHERE invocation_id=?",
            (invocation_id,),
        ).fetchone()
        if base is None or meta is None:
            raise EffectLifecycleError("EXECUTION_BUNDLE_POSTCONDITION_MISSING_ROW")
        if str(base["request_digest"]) != request_digest:
            raise EffectLifecycleError("EXECUTION_BUNDLE_REQUEST_DIGEST_MISMATCH")
        if str(base["result_digest"]) != result_digest or int(base["exit_code"]) != exit_code:
            raise EffectLifecycleError("EXECUTION_BUNDLE_BASE_POSTCONDITION_MISMATCH")
        if (
            str(meta["source_digest"]) != source_digest
            or str(meta["duplicate_state"]) != duplicate_state
            or str(meta["status"]) != status
        ):
            raise EffectLifecycleError("EXECUTION_BUNDLE_METADATA_POSTCONDITION_MISMATCH")

        con.execute("COMMIT")
        return request_digest
    except sqlite3.IntegrityError as exc:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise EffectLifecycleError("EXECUTION_BUNDLE_ATOMIC_WRITE_FAILED") from exc
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()


__all__ = ["SCHEMA", "record_execution_bundle_atomic"]
