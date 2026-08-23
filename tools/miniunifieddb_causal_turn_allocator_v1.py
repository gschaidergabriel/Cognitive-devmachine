#!/usr/bin/env python3
"""Canonical causal-turn event allocation inside MiniUnifiedDB.

The allocator creates event identity only. Turn material, truth, model output and effects
remain owned by their existing canonical boundaries. A new allocation is always a new
causal event; retries must reuse the previously returned causal_turn_id.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from typing import Any

SCHEMA = "MINIUNIFIEDDB_CAUSAL_TURN_ALLOCATION/v1"
ID_PREFIX = "ct1:"
_TABLE = "mini_cognition_turn_allocations"
_ID_RE = re.compile(r"^ct1:([1-9][0-9]*)$")


class CausalTurnAllocationError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CausalTurnAllocationError(message)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _refs(value: Any) -> list[str]:
    _need(type(value) is list, "PROVENANCE_REFS_LIST_REQUIRED")
    refs: list[str] = []
    for item in value:
        _need(type(item) is str and bool(item.strip()), "PROVENANCE_REF_NONEMPTY_REQUIRED")
        refs.append(item.strip())
    _need(bool(refs), "PROVENANCE_REQUIRED")
    _need(len(refs) == len(set(refs)), "PROVENANCE_REF_DUPLICATE")
    return refs


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise CausalTurnAllocationError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    generation = row[0]
    _need(type(generation) is int and not isinstance(generation, bool) and generation >= 0,
          "ENTITY_GENERATION_INVALID")
    return generation


def install_schema(db: sqlite3.Connection) -> None:
    """Install allocator rows inside the caller-owned MiniUnifiedDB transaction."""
    _current_generation(db)
    db.execute(
        f"""CREATE TABLE IF NOT EXISTS {_TABLE}(
              allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
              entity_generation INTEGER NOT NULL,
              provenance_refs_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            )"""
    )
    db.execute(
        f"""CREATE TRIGGER IF NOT EXISTS mini_cognition_turn_allocations_no_update
            BEFORE UPDATE ON {_TABLE}
            BEGIN SELECT RAISE(ABORT,'CAUSAL_TURN_ALLOCATION_IMMUTABLE'); END"""
    )
    db.execute(
        f"""CREATE TRIGGER IF NOT EXISTS mini_cognition_turn_allocations_no_delete
            BEFORE DELETE ON {_TABLE}
            BEGIN SELECT RAISE(ABORT,'CAUSAL_TURN_ALLOCATION_IMMUTABLE'); END"""
    )


def _causal_turn_id(allocation_id: int) -> str:
    _need(type(allocation_id) is int and allocation_id > 0, "ALLOCATION_ID_INVALID")
    return f"{ID_PREFIX}{allocation_id}"


def _parse_causal_turn_id(causal_turn_id: Any) -> int:
    _need(type(causal_turn_id) is str, "CAUSAL_TURN_ID_INVALID")
    match = _ID_RE.fullmatch(causal_turn_id)
    _need(match is not None, "CAUSAL_TURN_ID_INVALID")
    return int(match.group(1))


def _allocation_digest(*, allocation_id: int, entity_generation: int,
                       provenance_refs: list[str]) -> str:
    material = {
        "schema": SCHEMA,
        "allocation_id": allocation_id,
        "entity_generation": entity_generation,
        "provenance_refs": provenance_refs,
    }
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def allocate_causal_turn(db: sqlite3.Connection, *, entity_generation: int,
                         provenance_refs: list[str]) -> dict[str, Any]:
    """Allocate one new event identity; identical material intentionally allocates anew."""
    live = _current_generation(db)
    _need(type(entity_generation) is int and not isinstance(entity_generation, bool)
          and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live, "STALE_GENERATION")
    refs = _refs(provenance_refs)
    cursor = db.execute(
        f"INSERT INTO {_TABLE}(entity_generation,provenance_refs_json,created_at) VALUES(?,?,?)",
        (entity_generation, _canonical_json(refs), _utc_now()),
    )
    allocation_id = int(cursor.lastrowid)
    causal_turn_id = _causal_turn_id(allocation_id)
    return {
        "ok": True,
        "schema": SCHEMA,
        "allocation_id": allocation_id,
        "causal_turn_id": causal_turn_id,
        "entity_generation": entity_generation,
        "allocation_digest": _allocation_digest(
            allocation_id=allocation_id,
            entity_generation=entity_generation,
            provenance_refs=refs,
        ),
        "authority": "EVENT_IDENTITY_ONLY",
    }


def resolve_allocation(db: sqlite3.Connection, *, causal_turn_id: str,
                       entity_generation: int) -> dict[str, Any]:
    """Resolve an allocated id under the live generation fence."""
    live = _current_generation(db)
    _need(type(entity_generation) is int and not isinstance(entity_generation, bool)
          and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live, "STALE_GENERATION")
    allocation_id = _parse_causal_turn_id(causal_turn_id)
    row = db.execute(
        f"SELECT entity_generation,provenance_refs_json FROM {_TABLE} WHERE allocation_id=?",
        (allocation_id,),
    ).fetchone()
    _need(row is not None, "CAUSAL_TURN_ALLOCATION_UNAVAILABLE")
    _need(type(row[0]) is int and row[0] == entity_generation,
          "CAUSAL_TURN_ALLOCATION_GENERATION_MISMATCH")
    try:
        refs = _refs(json.loads(str(row[1])))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CausalTurnAllocationError("CAUSAL_TURN_ALLOCATION_PROVENANCE_INVALID") from exc
    return {
        "ok": True,
        "schema": SCHEMA,
        "allocation_id": allocation_id,
        "causal_turn_id": causal_turn_id,
        "entity_generation": entity_generation,
        "provenance_refs": refs,
        "allocation_digest": _allocation_digest(
            allocation_id=allocation_id,
            entity_generation=entity_generation,
            provenance_refs=refs,
        ),
        "authority": "EVENT_IDENTITY_ONLY",
    }


__all__ = [
    "SCHEMA",
    "CausalTurnAllocationError",
    "install_schema",
    "allocate_causal_turn",
    "resolve_allocation",
]
