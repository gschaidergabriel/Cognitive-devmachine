#!/usr/bin/env python3
"""Atomic cognition-schema bootstrap for the canonical MiniUnifiedDB runtime.

This helper creates no second durable authority. It prepares SQLite foreign-key
 enforcement before the caller begins its bootstrap transaction, then installs the
 existing cognition-store and active-turn schemas inside that same caller-owned
 transaction. It never commits or rolls back on the caller's behalf.
"""
from __future__ import annotations

import sqlite3
from typing import Any

SCHEMA = "MINIUNIFIEDDB_COGNITION_BOOTSTRAP/v1"
_REQUIRED_TABLES = (
    "mini_cognition_objects",
    "mini_cognition_object_admissions",
    "mini_cognition_boot_bindings",
    "mini_cognition_turn_bindings",
    "mini_cognition_active_turns",
)


class CognitionBootstrapError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitionBootstrapError(message)


def _foreign_keys_enabled(db: sqlite3.Connection) -> bool:
    row = db.execute("PRAGMA foreign_keys").fetchone()
    return row is not None and int(row[0]) == 1


def prepare_connection(db: sqlite3.Connection) -> dict[str, Any]:
    """Enable FK enforcement before the caller opens its bootstrap transaction."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(not db.in_transaction, "FOREIGN_KEY_BOOTSTRAP_MUST_PRECEDE_TRANSACTION")
    db.execute("PRAGMA foreign_keys=ON")
    _need(_foreign_keys_enabled(db), "FOREIGN_KEYS_ENABLE_FAILED")
    return {
        "ok": True,
        "schema": SCHEMA,
        "foreign_keys": True,
        "transaction_open": False,
    }


def install_cognition_schema(
    db: sqlite3.Connection,
    *,
    store_module: Any | None = None,
    active_turn_module: Any | None = None,
) -> dict[str, Any]:
    """Install existing cognition schemas without taking transaction ownership."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(_foreign_keys_enabled(db), "FOREIGN_KEYS_REQUIRED")
    _need(db.in_transaction, "CALLER_BOOTSTRAP_TRANSACTION_REQUIRED")

    row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    _need(row is not None, "ENTITY_STATE_REQUIRED")
    generation = row[0]
    _need(type(generation) is int and generation >= 0, "ENTITY_GENERATION_INVALID")

    if store_module is None:
        import miniunifieddb_cognition_store_v1 as store_module  # type: ignore[no-redef]
    if active_turn_module is None:
        import miniunifieddb_active_turn_v1 as active_turn_module  # type: ignore[no-redef]

    store_module.install_schema(db)
    _need(db.in_transaction, "COGNITION_STORE_BROKE_CALLER_TRANSACTION")
    active_turn_module.install_schema(db)
    _need(db.in_transaction, "ACTIVE_TURN_STORE_BROKE_CALLER_TRANSACTION")

    found = {
        str(row[0])
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mini_cognition_%'"
        ).fetchall()
    }
    missing = [name for name in _REQUIRED_TABLES if name not in found]
    _need(not missing, "COGNITION_SCHEMA_INCOMPLETE:" + ",".join(missing))

    return {
        "ok": True,
        "schema": SCHEMA,
        "entity_generation": generation,
        "foreign_keys": True,
        "caller_transaction_preserved": True,
        "installed_tables": list(_REQUIRED_TABLES),
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "creates_second_state_authority": False,
            "creates_effect_authority": False,
        },
    }


__all__ = [
    "SCHEMA",
    "CognitionBootstrapError",
    "prepare_connection",
    "install_cognition_schema",
]
