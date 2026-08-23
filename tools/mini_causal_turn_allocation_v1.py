#!/usr/bin/env python3
"""MiniUnifiedDB-owned causal turn allocation for Mini Entity cognition.

A causal turn is an event identity, not a content digest.  Two deliberately separate
turns may have byte-identical task/workspace material and still require different
causal ids.  This module therefore allocates ids monotonically inside the same
MiniUnifiedDB and delegates immutable material binding to the canonical cognition store.

No model, J-Space, GWT, HCU, truth, or effect authority is created here.
"""
from __future__ import annotations

import sqlite3
import time
from typing import Any

import miniunifieddb_cognition_store_v1 as cognition_store

SCHEMA = "MINI_ENTITY_CAUSAL_TURN_ALLOCATION/v1"
ID_PREFIX = "ct1"
_SAVEPOINT = "mini_causal_turn_allocate_v1"


class CausalTurnAllocationError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CausalTurnAllocationError(message)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _live_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise CausalTurnAllocationError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    generation = row[0]
    _need(type(generation) is int and not isinstance(generation, bool) and generation >= 0,
          "ENTITY_GENERATION_INVALID")
    return generation


def _require_cognition_store(db: sqlite3.Connection) -> None:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='mini_cognition_turn_bindings'"
    ).fetchone()
    _need(row is not None, "COGNITION_STORE_SCHEMA_REQUIRED")


def install_schema(db: sqlite3.Connection) -> None:
    """Install the allocation table in the same DB without implicit commit."""
    _live_generation(db)
    fk_row = db.execute("PRAGMA foreign_keys").fetchone()
    _need(fk_row is not None and int(fk_row[0]) == 1,
          "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION")
    _require_cognition_store(db)
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_turn_allocations(
          allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
          schema TEXT NOT NULL,
          entity_generation INTEGER NOT NULL,
          causal_turn_id TEXT UNIQUE,
          allocated_at TEXT NOT NULL,
          CHECK(schema='MINI_ENTITY_CAUSAL_TURN_ALLOCATION/v1'))"""
    )


def _allocated_row(db: sqlite3.Connection, *, entity_generation: int,
                   causal_turn_id: str) -> tuple[Any, ...] | None:
    return db.execute(
        """SELECT allocation_id,schema,entity_generation,causal_turn_id,allocated_at
             FROM mini_cognition_turn_allocations
            WHERE entity_generation=? AND causal_turn_id=?""",
        (entity_generation, causal_turn_id),
    ).fetchone()


def _begin_atomic(db: sqlite3.Connection) -> bool:
    """Start our transaction, or isolate our work inside a caller-owned transaction."""
    caller_owns_transaction = db.in_transaction
    if caller_owns_transaction:
        db.execute(f"SAVEPOINT {_SAVEPOINT}")
    else:
        db.execute("BEGIN IMMEDIATE")
    return caller_owns_transaction


def _finish_atomic(db: sqlite3.Connection, caller_owns_transaction: bool) -> None:
    if caller_owns_transaction:
        db.execute(f"RELEASE SAVEPOINT {_SAVEPOINT}")
    else:
        db.commit()


def _abort_atomic(db: sqlite3.Connection, caller_owns_transaction: bool) -> None:
    if caller_owns_transaction:
        db.execute(f"ROLLBACK TO SAVEPOINT {_SAVEPOINT}")
        db.execute(f"RELEASE SAVEPOINT {_SAVEPOINT}")
    else:
        db.rollback()


def allocate_and_bind_turn(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    boot_binding_digest: str,
    task_text: str,
    workspace_digest: str,
    selected_workspace_slots: list[str],
    contradiction_state: str,
    provenance_refs: list[str],
    required_zero_mode: str,
) -> dict[str, Any]:
    """Allocate one new event id and bind its immutable turn material atomically.

    Calling this twice means two distinct causal events, even when all supplied content is
    identical.  A retry of an already-admitted event must instead call
    ``bind_existing_turn`` with the previously allocated causal_turn_id.
    """
    live = _live_generation(db)
    _need(type(entity_generation) is int and not isinstance(entity_generation, bool)
          and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live, "STALE_GENERATION")

    caller_owns_transaction = _begin_atomic(db)
    try:
        install_schema(db)
        cursor = db.execute(
            """INSERT INTO mini_cognition_turn_allocations(
                 schema,entity_generation,causal_turn_id,allocated_at)
               VALUES(?,?,NULL,?)""",
            (SCHEMA, entity_generation, _utc_now()),
        )
        allocation_id = cursor.lastrowid
        _need(type(allocation_id) is int and allocation_id > 0, "ALLOCATION_ID_INVALID")
        causal_turn_id = f"{ID_PREFIX}:g{entity_generation}:a{allocation_id}"
        updated = db.execute(
            "UPDATE mini_cognition_turn_allocations SET causal_turn_id=? WHERE allocation_id=?",
            (causal_turn_id, allocation_id),
        )
        _need(updated.rowcount == 1, "ALLOCATION_UPDATE_FAILED")
        bound = cognition_store.bind_turn(
            db,
            entity_generation=entity_generation,
            causal_turn_id=causal_turn_id,
            boot_binding_digest=boot_binding_digest,
            task_text=task_text,
            workspace_digest=workspace_digest,
            selected_workspace_slots=selected_workspace_slots,
            contradiction_state=contradiction_state,
            provenance_refs=provenance_refs,
            required_zero_mode=required_zero_mode,
        )
        _finish_atomic(db, caller_owns_transaction)
        return {
            **bound,
            "causal_turn_id": causal_turn_id,
            "allocation_id": allocation_id,
            "allocation_schema": SCHEMA,
            "new_causal_event": True,
            "authority": "MINIUNIFIEDDB_IDENTITY_ONLY",
            "runtime_credit": "ZERO",
        }
    except Exception:
        _abort_atomic(db, caller_owns_transaction)
        raise


def bind_existing_turn(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    causal_turn_id: str,
    boot_binding_digest: str,
    task_text: str,
    workspace_digest: str,
    selected_workspace_slots: list[str],
    contradiction_state: str,
    provenance_refs: list[str],
    required_zero_mode: str,
) -> dict[str, Any]:
    """Retry an already allocated event atomically without allocating a second identity."""
    live = _live_generation(db)
    _need(type(entity_generation) is int and not isinstance(entity_generation, bool)
          and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live, "STALE_GENERATION")

    caller_owns_transaction = _begin_atomic(db)
    try:
        install_schema(db)
        row = _allocated_row(
            db, entity_generation=entity_generation, causal_turn_id=causal_turn_id
        )
        _need(row is not None, "CAUSAL_TURN_NOT_ALLOCATED")
        _need(row[1] == SCHEMA and row[2] == entity_generation and row[3] == causal_turn_id,
              "CAUSAL_TURN_ALLOCATION_CORRUPT")
        bound = cognition_store.bind_turn(
            db,
            entity_generation=entity_generation,
            causal_turn_id=causal_turn_id,
            boot_binding_digest=boot_binding_digest,
            task_text=task_text,
            workspace_digest=workspace_digest,
            selected_workspace_slots=selected_workspace_slots,
            contradiction_state=contradiction_state,
            provenance_refs=provenance_refs,
            required_zero_mode=required_zero_mode,
        )
        _finish_atomic(db, caller_owns_transaction)
        return {
            **bound,
            "causal_turn_id": causal_turn_id,
            "allocation_id": int(row[0]),
            "allocation_schema": SCHEMA,
            "new_causal_event": False,
            "authority": "MINIUNIFIEDDB_IDENTITY_ONLY",
            "runtime_credit": "ZERO",
        }
    except Exception:
        _abort_atomic(db, caller_owns_transaction)
        raise


__all__ = [
    "SCHEMA",
    "CausalTurnAllocationError",
    "install_schema",
    "allocate_and_bind_turn",
    "bind_existing_turn",
]
