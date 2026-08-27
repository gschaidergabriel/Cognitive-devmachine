#!/usr/bin/env python3
"""Generation-scoped active-turn pointer for the existing MiniUnifiedDB cognition store.

The underlying causal-turn binding remains owned by miniunifieddb_cognition_store_v1.
This module only selects exactly one already-bound turn for a live entity generation and
retains the exact task text whose SHA-256 is already committed by that binding. It never
creates a second turn ledger, truth authority, effect path, or generated causal identity.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from typing import Any

SCHEMA = "MINIUNIFIEDDB_ACTIVE_COGNITION_TURN/v1"
_ACTIVE_TURN_COLUMNS = (
    "entity_generation",
    "causal_turn_id",
    "turn_binding_digest",
    "task_text",
    "task_sha256",
    "activation_digest",
    "provenance_refs_json",
    "activated_at",
)


class ActiveTurnError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ActiveTurnError(message)


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _refs(value: Any) -> list[str]:
    _need(type(value) is list, "PROVENANCE_REFS_LIST_REQUIRED")
    refs = [_text(item, "provenance_ref") for item in value]
    _need(bool(refs), "PROVENANCE_REFS_REQUIRED")
    _need(len(refs) == len(set(refs)), "PROVENANCE_REFS_DUPLICATE")
    return refs


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ActiveTurnError("NON_CANONICAL_JSON") from exc


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise ActiveTurnError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    generation = row[0]
    _need(type(generation) is int and generation >= 0, "ENTITY_GENERATION_INVALID")
    return generation


def _require_bound_turn_table(db: sqlite3.Connection) -> None:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='mini_cognition_turn_bindings'"
    ).fetchone()
    _need(row is not None, "COGNITION_TURN_BINDING_STORE_REQUIRED")


def _require_active_turn_schema(db: sqlite3.Connection) -> None:
    """Verify the activation pointer using read-only catalog operations only."""
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='mini_cognition_active_turns'"
    ).fetchone()
    _need(row is not None, "ACTIVE_TURN_SCHEMA_REQUIRED")
    columns = tuple(
        str(item[1]) for item in db.execute("PRAGMA table_info(mini_cognition_active_turns)").fetchall()
    )
    _need(columns == _ACTIVE_TURN_COLUMNS, "ACTIVE_TURN_SCHEMA_INVALID")


def install_schema(db: sqlite3.Connection) -> None:
    """Install one activation pointer table inside an initialized MiniUnifiedDB."""
    _current_generation(db)
    _require_bound_turn_table(db)
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_active_turns(
             entity_generation INTEGER PRIMARY KEY,
             causal_turn_id TEXT NOT NULL,
             turn_binding_digest TEXT NOT NULL,
             task_text TEXT NOT NULL,
             task_sha256 TEXT NOT NULL,
             activation_digest TEXT NOT NULL UNIQUE,
             provenance_refs_json TEXT NOT NULL,
             activated_at TEXT NOT NULL)"""
    )


def activate_bound_turn(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    causal_turn_id: str,
    task_text: str,
    expected_turn_binding_digest: str,
    provenance_refs: list[str],
) -> dict[str, Any]:
    """Select one exact existing turn binding for the live generation.

    No turn id is derived here. The caller must provide an already-bound causal_turn_id.
    """
    live_generation = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live_generation, "STALE_GENERATION")
    causal_turn_id = _text(causal_turn_id, "causal_turn_id")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    expected_turn_binding_digest = _text(
        expected_turn_binding_digest, "expected_turn_binding_digest"
    )
    refs = _refs(provenance_refs)
    _require_bound_turn_table(db)
    _require_active_turn_schema(db)

    turn = db.execute(
        """SELECT binding_digest,task_sha256
             FROM mini_cognition_turn_bindings
            WHERE entity_generation=? AND causal_turn_id=?""",
        (entity_generation, causal_turn_id),
    ).fetchone()
    _need(turn is not None, "TURN_BINDING_UNAVAILABLE")
    bound_digest = _text(turn[0], "bound_turn_binding_digest")
    _need(bound_digest == expected_turn_binding_digest, "TURN_BINDING_DIGEST_MISMATCH")

    task_sha256 = _sha256_text(task_text)
    _need(turn[1] == task_sha256, "TURN_TASK_BINDING_MISMATCH")

    material = {
        "schema": SCHEMA,
        "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": bound_digest,
        "task_sha256": task_sha256,
        "provenance_refs": refs,
    }
    activation_digest = _sha256_text(_canonical(material))
    existing = db.execute(
        """SELECT causal_turn_id,turn_binding_digest,task_text,task_sha256,
                  activation_digest,provenance_refs_json
             FROM mini_cognition_active_turns
            WHERE entity_generation=?""",
        (entity_generation,),
    ).fetchone()
    exact = (
        causal_turn_id,
        bound_digest,
        task_text,
        task_sha256,
        activation_digest,
        _canonical(refs),
    )
    if existing is not None:
        _need(tuple(existing) == exact, "ACTIVE_TURN_GENERATION_CONFLICT")
        return {
            "ok": True,
            "schema": SCHEMA,
            "idempotent": True,
            "activation_digest": activation_digest,
            "entity_generation": entity_generation,
            "causal_turn_id": causal_turn_id,
            "turn_binding_digest": bound_digest,
            "task_sha256": task_sha256,
        }

    db.execute(
        """INSERT INTO mini_cognition_active_turns(
             entity_generation,causal_turn_id,turn_binding_digest,task_text,task_sha256,
             activation_digest,provenance_refs_json,activated_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        (
            entity_generation,
            causal_turn_id,
            bound_digest,
            task_text,
            task_sha256,
            activation_digest,
            _canonical(refs),
            _utc_now(),
        ),
    )
    return {
        "ok": True,
        "schema": SCHEMA,
        "idempotent": False,
        "activation_digest": activation_digest,
        "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": bound_digest,
        "task_sha256": task_sha256,
    }


def resolve_active_prepare(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    expected_activation_digest: str | None = None,
    store_module: Any | None = None,
) -> dict[str, Any]:
    """Resolve exact current prepare material without mutating MiniUnifiedDB."""
    live_generation = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live_generation, "STALE_GENERATION")
    _require_bound_turn_table(db)
    _require_active_turn_schema(db)

    row = db.execute(
        """SELECT causal_turn_id,turn_binding_digest,task_text,task_sha256,
                  activation_digest,provenance_refs_json
             FROM mini_cognition_active_turns
            WHERE entity_generation=?""",
        (entity_generation,),
    ).fetchone()
    _need(row is not None, "ACTIVE_TURN_UNAVAILABLE")
    causal_turn_id = _text(row[0], "causal_turn_id")
    turn_binding_digest = _text(row[1], "turn_binding_digest")
    task_text = row[2]
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    task_sha256 = _sha256_text(task_text)
    _need(task_sha256 == row[3], "ACTIVE_TASK_TEXT_HASH_MISMATCH")
    activation_digest = _text(row[4], "activation_digest")
    if expected_activation_digest is not None:
        _need(
            activation_digest == _text(expected_activation_digest, "expected_activation_digest"),
            "ACTIVE_TURN_DIGEST_MISMATCH",
        )
    refs = json.loads(row[5])
    _refs(refs)

    turn = db.execute(
        """SELECT binding_digest,task_sha256
             FROM mini_cognition_turn_bindings
            WHERE entity_generation=? AND causal_turn_id=?""",
        (entity_generation, causal_turn_id),
    ).fetchone()
    _need(turn is not None, "TURN_BINDING_UNAVAILABLE")
    _need(turn[0] == turn_binding_digest, "ACTIVE_TURN_BINDING_DRIFT")
    _need(turn[1] == task_sha256, "ACTIVE_TURN_TASK_DRIFT")

    if store_module is None:
        import miniunifieddb_cognition_store_v1 as store_module  # type: ignore[no-redef]

    resolved = store_module.resolve_prepare_binding(
        db,
        entity_generation=entity_generation,
        causal_turn_id=causal_turn_id,
        task_text=task_text,
    )
    _need(type(resolved) is dict and resolved.get("ok") is True, "PREPARE_RESOLVE_FAILED")
    _need(
        resolved.get("turn_binding_digest") == turn_binding_digest,
        "PREPARE_TURN_BINDING_MISMATCH",
    )
    _need(resolved.get("task_sha256") == task_sha256, "PREPARE_TASK_HASH_MISMATCH")

    result = dict(resolved)
    result.update(
        {
            "active_turn_schema": SCHEMA,
            "activation_digest": activation_digest,
            "task_text": task_text,
            "activation_provenance_refs": refs,
        }
    )
    return result


__all__ = [
    "SCHEMA",
    "ActiveTurnError",
    "install_schema",
    "activate_bound_turn",
    "resolve_active_prepare",
]
