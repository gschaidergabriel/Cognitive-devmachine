#!/usr/bin/env python3
"""Versioned cognition-object bindings inside the canonical MiniUnifiedDB.

This module is a deterministic authority-preserving storage mechanism. It does not
create a second database, model authority, truth authority, or effect path. Objects
are immutable versioned bytes; active slot selection is generation-fenced against
MiniUnifiedDB.entity_state.generation; every read re-hashes object and provenance
bytes and cross-checks the bound object hash before returning a snapshot.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from typing import Any, Iterable

SCHEMA = "MINI_COGNITION_OBJECT_STORE/v1"
SNAPSHOT_SCHEMA = "MINI_COGNITION_BINDING_SNAPSHOT/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SLOT = re.compile(r"^[A-Z][A-Z0-9_]{1,95}$")
KIND = re.compile(r"^[A-Z][A-Z0-9_]{1,95}$")
OBJECT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,191}$")


class CognitionStoreError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitionStoreError(message)


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CognitionStoreError("NON_CANONICAL_JSON") from exc


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(len(set(value)) > 1, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _generation(value: Any, name: str = "generation") -> int:
    _need(type(value) is int and value >= 0, f"{name}:NONNEGATIVE_INT_REQUIRED")
    return value


def _validate_slot(value: Any) -> str:
    _need(type(value) is str and SLOT.fullmatch(value) is not None, "SLOT_INVALID")
    return value


def _validate_kind(value: Any) -> str:
    _need(type(value) is str and KIND.fullmatch(value) is not None, "OBJECT_KIND_INVALID")
    return value


def _validate_object_id(value: Any) -> str:
    _need(type(value) is str and OBJECT_ID.fullmatch(value) is not None, "OBJECT_ID_INVALID")
    return value


def install_schema(db: sqlite3.Connection) -> None:
    """Install cognition tables into the same MiniUnifiedDB connection.

    Caller owns transaction policy. The existing entity_state table is intentionally
    not created here: absence of the canonical generation authority is an error.
    """
    _require_entity_state(db)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS cognition_objects(
          object_kind TEXT NOT NULL,
          object_id TEXT NOT NULL,
          object_version INTEGER NOT NULL CHECK(object_version >= 1),
          object_json TEXT NOT NULL,
          object_sha256 TEXT NOT NULL,
          provenance_json TEXT NOT NULL,
          provenance_sha256 TEXT NOT NULL,
          created_generation INTEGER NOT NULL CHECK(created_generation >= 0),
          PRIMARY KEY(object_kind, object_id, object_version)
        );
        CREATE TABLE IF NOT EXISTS cognition_bindings(
          slot TEXT PRIMARY KEY,
          object_kind TEXT NOT NULL,
          object_id TEXT NOT NULL,
          object_version INTEGER NOT NULL CHECK(object_version >= 1),
          object_sha256 TEXT NOT NULL,
          bound_generation INTEGER NOT NULL CHECK(bound_generation >= 0),
          binding_sha256 TEXT NOT NULL,
          FOREIGN KEY(object_kind, object_id, object_version)
            REFERENCES cognition_objects(object_kind, object_id, object_version)
        );
        """
    )


def _require_entity_state(db: sqlite3.Connection) -> int:
    row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    _need(row is not None, "ENTITY_STATE_MISSING")
    return _generation(int(row[0]), "entity_generation")


def put_object(
    db: sqlite3.Connection,
    *,
    object_kind: str,
    object_id: str,
    object_version: int,
    payload: Any,
    provenance: Any,
    expected_generation: int,
) -> dict[str, Any]:
    """Insert one immutable versioned cognition object.

    Re-inserting byte-identical material is idempotent. A different payload or
    provenance under the same (kind,id,version) is rejected instead of overwritten.
    """
    kind = _validate_kind(object_kind)
    oid = _validate_object_id(object_id)
    _need(type(object_version) is int and object_version >= 1, "OBJECT_VERSION_INVALID")
    expected = _generation(expected_generation, "expected_generation")
    live = _require_entity_state(db)
    _need(live == expected, "GENERATION_MISMATCH")

    object_json = canonical_json(payload)
    object_sha256 = sha256_text(object_json)
    provenance_json = canonical_json(provenance)
    provenance_sha256 = sha256_text(provenance_json)

    existing = db.execute(
        """SELECT object_json,object_sha256,provenance_json,provenance_sha256,created_generation
           FROM cognition_objects
           WHERE object_kind=? AND object_id=? AND object_version=?""",
        (kind, oid, object_version),
    ).fetchone()
    if existing is not None:
        _need(
            tuple(existing)
            == (object_json, object_sha256, provenance_json, provenance_sha256, expected),
            "IMMUTABLE_OBJECT_VERSION_CONFLICT",
        )
        return {
            "ok": True,
            "idempotent": True,
            "object_kind": kind,
            "object_id": oid,
            "object_version": object_version,
            "object_sha256": object_sha256,
            "provenance_sha256": provenance_sha256,
        }

    db.execute(
        """INSERT INTO cognition_objects(
             object_kind,object_id,object_version,object_json,object_sha256,
             provenance_json,provenance_sha256,created_generation)
           VALUES(?,?,?,?,?,?,?,?)""",
        (
            kind,
            oid,
            object_version,
            object_json,
            object_sha256,
            provenance_json,
            provenance_sha256,
            expected,
        ),
    )
    return {
        "ok": True,
        "idempotent": False,
        "object_kind": kind,
        "object_id": oid,
        "object_version": object_version,
        "object_sha256": object_sha256,
        "provenance_sha256": provenance_sha256,
    }


def bind_slot(
    db: sqlite3.Connection,
    *,
    slot: str,
    object_kind: str,
    object_id: str,
    object_version: int,
    expected_generation: int,
) -> dict[str, Any]:
    """Generation-fenced active selection of an immutable cognition object."""
    slot_name = _validate_slot(slot)
    kind = _validate_kind(object_kind)
    oid = _validate_object_id(object_id)
    _need(type(object_version) is int and object_version >= 1, "OBJECT_VERSION_INVALID")
    expected = _generation(expected_generation, "expected_generation")
    live = _require_entity_state(db)
    _need(live == expected, "GENERATION_MISMATCH")

    row = db.execute(
        """SELECT object_sha256,provenance_sha256
           FROM cognition_objects
           WHERE object_kind=? AND object_id=? AND object_version=?""",
        (kind, oid, object_version),
    ).fetchone()
    _need(row is not None, "OBJECT_NOT_FOUND")
    object_sha256 = _digest(str(row[0]), "object_sha256")
    provenance_sha256 = _digest(str(row[1]), "provenance_sha256")
    binding_material = {
        "schema": SCHEMA,
        "slot": slot_name,
        "object_kind": kind,
        "object_id": oid,
        "object_version": object_version,
        "object_sha256": object_sha256,
        "provenance_sha256": provenance_sha256,
        "bound_generation": expected,
    }
    binding_sha256 = sha256_text(canonical_json(binding_material))
    db.execute(
        """INSERT INTO cognition_bindings(
             slot,object_kind,object_id,object_version,object_sha256,bound_generation,binding_sha256)
           VALUES(?,?,?,?,?,?,?)
           ON CONFLICT(slot) DO UPDATE SET
             object_kind=excluded.object_kind,
             object_id=excluded.object_id,
             object_version=excluded.object_version,
             object_sha256=excluded.object_sha256,
             bound_generation=excluded.bound_generation,
             binding_sha256=excluded.binding_sha256""",
        (
            slot_name,
            kind,
            oid,
            object_version,
            object_sha256,
            expected,
            binding_sha256,
        ),
    )
    return {
        "ok": True,
        "slot": slot_name,
        "object_sha256": object_sha256,
        "binding_sha256": binding_sha256,
    }


def resolve_snapshot(
    db: sqlite3.Connection,
    *,
    expected_generation: int,
    required_slots: Iterable[str],
) -> dict[str, Any]:
    """Resolve and re-verify an exact cognition binding snapshot.

    The snapshot is read-only evidence. It grants no model execution, canonical truth
    write, or effect capability. Every required slot must exist and every immutable
    byte/digest/binding relationship must still verify against the live generation.
    """
    expected = _generation(expected_generation, "expected_generation")
    live = _require_entity_state(db)
    _need(live == expected, "GENERATION_MISMATCH")
    slots = [_validate_slot(item) for item in required_slots]
    _need(bool(slots), "REQUIRED_SLOTS_EMPTY")
    _need(len(slots) == len(set(slots)), "REQUIRED_SLOT_DUPLICATE")

    resolved: dict[str, Any] = {}
    for slot_name in sorted(slots):
        row = db.execute(
            """SELECT b.object_kind,b.object_id,b.object_version,b.object_sha256,
                      b.bound_generation,b.binding_sha256,
                      o.object_json,o.object_sha256,o.provenance_json,o.provenance_sha256,
                      o.created_generation
               FROM cognition_bindings b
               JOIN cognition_objects o
                 ON o.object_kind=b.object_kind
                AND o.object_id=b.object_id
                AND o.object_version=b.object_version
               WHERE b.slot=?""",
            (slot_name,),
        ).fetchone()
        _need(row is not None, "MISSING_BINDING:" + slot_name)
        (
            kind,
            oid,
            version,
            bound_object_sha,
            bound_generation,
            binding_sha,
            object_json,
            stored_object_sha,
            provenance_json,
            stored_provenance_sha,
            created_generation,
        ) = tuple(row)
        kind = _validate_kind(str(kind))
        oid = _validate_object_id(str(oid))
        _need(type(version) is int and version >= 1, "OBJECT_VERSION_INVALID")
        bound_generation = _generation(int(bound_generation), "bound_generation")
        created_generation = _generation(int(created_generation), "created_generation")
        _need(bound_generation <= expected, "FUTURE_BINDING")
        _need(created_generation <= bound_generation, "OBJECT_CREATED_AFTER_BINDING")

        stored_object_sha = _digest(str(stored_object_sha), "stored_object_sha256")
        observed_object_sha = sha256_text(str(object_json))
        _need(observed_object_sha == stored_object_sha, "OBJECT_HASH_MISMATCH:" + slot_name)
        bound_object_sha = _digest(str(bound_object_sha), "bound_object_sha256")
        _need(bound_object_sha == stored_object_sha, "BINDING_OBJECT_HASH_MISMATCH:" + slot_name)

        stored_provenance_sha = _digest(str(stored_provenance_sha), "stored_provenance_sha256")
        observed_provenance_sha = sha256_text(str(provenance_json))
        _need(
            observed_provenance_sha == stored_provenance_sha,
            "PROVENANCE_HASH_MISMATCH:" + slot_name,
        )
        binding_material = {
            "schema": SCHEMA,
            "slot": slot_name,
            "object_kind": kind,
            "object_id": oid,
            "object_version": version,
            "object_sha256": stored_object_sha,
            "provenance_sha256": stored_provenance_sha,
            "bound_generation": bound_generation,
        }
        expected_binding_sha = sha256_text(canonical_json(binding_material))
        binding_sha = _digest(str(binding_sha), "binding_sha256")
        _need(binding_sha == expected_binding_sha, "BINDING_DIGEST_MISMATCH:" + slot_name)

        try:
            payload = json.loads(str(object_json))
            provenance = json.loads(str(provenance_json))
        except json.JSONDecodeError as exc:
            raise CognitionStoreError("STORED_JSON_INVALID:" + slot_name) from exc
        _need(canonical_json(payload) == str(object_json), "OBJECT_NOT_CANONICAL_JSON:" + slot_name)
        _need(
            canonical_json(provenance) == str(provenance_json),
            "PROVENANCE_NOT_CANONICAL_JSON:" + slot_name,
        )
        resolved[slot_name] = {
            "object_kind": kind,
            "object_id": oid,
            "object_version": version,
            "object_sha256": stored_object_sha,
            "provenance_sha256": stored_provenance_sha,
            "bound_generation": bound_generation,
            "binding_sha256": binding_sha,
            "payload": payload,
            "provenance": provenance,
        }

    snapshot_core = {
        "schema": SNAPSHOT_SCHEMA,
        "entity_generation": expected,
        "slots": resolved,
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "truth": "NONE_FROM_BINDING_ALONE",
            "model_output": "CANDIDATE_ONLY",
            "effects": "NONE",
        },
    }
    return {
        **snapshot_core,
        "snapshot_sha256": sha256_text(canonical_json(snapshot_core)),
    }
