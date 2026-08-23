#!/usr/bin/env python3
"""Versioned cognition-object bindings inside the canonical MiniUnifiedDB authority.

This module is intentionally narrow: it stores immutable, content-addressed cognition
configuration/evidence objects and atomically binds named roles to those objects using
MiniUnifiedDB's existing entity_state.generation as the sole write fence.

It does not create a second identity, truth store, effect path, or model authority.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = "MINIUNIFIEDDB_COGNITION_BINDINGS/v1"
OBJECT_SCHEMA = "MINIUNIFIEDDB_COGNITION_OBJECT/v1"
SNAPSHOT_SCHEMA = "MINIUNIFIEDDB_COGNITION_BINDING_SNAPSHOT/v1"

ROLE_KINDS = {
    "ZERO_IDENTITY": "ZERO_IDENTITY",
    "GRF": "GRF",
    "HYPERPOSITION": "HYPERPOSITION",
    "BUNDLED_COGNITION_MANIFEST": "BUNDLED_COGNITION_MANIFEST",
    "JSPACE_ADAPTER": "JSPACE_ADAPTER",
    "WORKSPACE_CALIBRATION": "WORKSPACE_CALIBRATION",
}

_SECRET_VALUE_KEYS = {
    "api_key",
    "api_token",
    "access_token",
    "secret_value",
    "password",
    "private_key",
    "client_secret",
    "bearer_token",
    "refresh_token",
    "auth_token",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CognitionStoreError(RuntimeError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CognitionStoreError(f"{name}_REQUIRED")
    return value.strip()


def _forbid_embedded_secret_values(value: Any, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child = f"{path}.{key_text}" if path else key_text
            if key_text.lower() in _SECRET_VALUE_KEYS and item not in (None, "", [], {}):
                raise CognitionStoreError("COGNITION_OBJECT_CONTAINS_SECRET_VALUE:" + child)
            _forbid_embedded_secret_values(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _forbid_embedded_secret_values(item, f"{path}[{index}]")


def _require_entity_state(conn: sqlite3.Connection) -> int:
    table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entity_state'"
    ).fetchone()
    if table is None:
        raise CognitionStoreError("ENTITY_STATE_REQUIRED")
    cols = {str(row[1]) for row in conn.execute("PRAGMA table_info(entity_state)")}
    if not {"id", "generation"}.issubset(cols):
        raise CognitionStoreError("ENTITY_STATE_SCHEMA_INVALID")
    row = conn.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    if row is None:
        raise CognitionStoreError("ENTITY_STATE_SINGLETON_REQUIRED")
    generation = int(row[0])
    if generation < 0:
        raise CognitionStoreError("ENTITY_GENERATION_INVALID")
    return generation


def init_schema(conn: sqlite3.Connection) -> dict[str, Any]:
    """Create only cognition tables; never mint or replace entity_state authority."""
    _require_entity_state(conn)
    # Deliberately use individual DDL statements rather than executescript(): this function
    # must be safe when called from the canonical runtime's existing BEGIN IMMEDIATE
    # bootstrap transaction and must never commit that caller-owned transaction.
    conn.execute(
        """CREATE TABLE IF NOT EXISTS cognition_objects(
             object_digest TEXT PRIMARY KEY,
             object_kind TEXT NOT NULL,
             object_version TEXT NOT NULL,
             payload_json TEXT NOT NULL,
             provenance_json TEXT NOT NULL,
             envelope_json TEXT NOT NULL,
             created_at TEXT NOT NULL)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS cognition_bindings(
             role TEXT PRIMARY KEY,
             object_digest TEXT NOT NULL REFERENCES cognition_objects(object_digest),
             changed_generation INTEGER NOT NULL,
             changed_at TEXT NOT NULL)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS cognition_binding_snapshots(
             entity_generation INTEGER PRIMARY KEY,
             snapshot_digest TEXT NOT NULL UNIQUE,
             bindings_json TEXT NOT NULL,
             created_at TEXT NOT NULL)"""
    )
    return {"ok": True, "schema": SCHEMA_VERSION}


def put_object(
    conn: sqlite3.Connection,
    *,
    object_kind: str,
    object_version: str,
    payload: Mapping[str, Any],
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Idempotently persist immutable content-addressed cognition bytes."""
    _require_entity_state(conn)
    object_kind = _nonempty(object_kind, "OBJECT_KIND")
    object_version = _nonempty(object_version, "OBJECT_VERSION")
    if not isinstance(payload, Mapping):
        raise CognitionStoreError("PAYLOAD_OBJECT_REQUIRED")
    if not isinstance(provenance, Mapping):
        raise CognitionStoreError("PROVENANCE_OBJECT_REQUIRED")
    payload_obj = json.loads(_canonical_json(dict(payload)))
    provenance_obj = json.loads(_canonical_json(dict(provenance)))
    _forbid_embedded_secret_values(payload_obj)
    _forbid_embedded_secret_values(provenance_obj)
    envelope = {
        "schema": OBJECT_SCHEMA,
        "object_kind": object_kind,
        "object_version": object_version,
        "payload": payload_obj,
        "provenance": provenance_obj,
        "authority": {
            "canonical_container": "MiniUnifiedDB",
            "truth_authority": False,
            "effect_authority": False,
            "model_output_authority": False,
        },
    }
    envelope_json = _canonical_json(envelope)
    digest = _sha256_text(envelope_json)
    now = _utc_now()
    if conn.in_transaction:
        raise CognitionStoreError("CALLER_TRANSACTION_ACTIVE")
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            """INSERT OR IGNORE INTO cognition_objects(
                   object_digest,object_kind,object_version,payload_json,provenance_json,envelope_json,created_at)
               VALUES(?,?,?,?,?,?,?)""",
            (
                digest,
                object_kind,
                object_version,
                _canonical_json(payload_obj),
                _canonical_json(provenance_obj),
                envelope_json,
                now,
            ),
        )
        row = conn.execute(
            "SELECT envelope_json FROM cognition_objects WHERE object_digest=?", (digest,)
        ).fetchone()
        if row is None or str(row[0]) != envelope_json:
            raise CognitionStoreError("OBJECT_DIGEST_COLLISION_OR_CORRUPTION")
        conn.commit()
        return {"ok": True, "object_digest": digest, "schema": OBJECT_SCHEMA}
    except Exception:
        conn.rollback()
        raise


def _read_current_bindings(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        "SELECT role,object_digest FROM cognition_bindings ORDER BY role"
    ).fetchall()
    return {str(row[0]): str(row[1]) for row in rows}


def _write_snapshot(conn: sqlite3.Connection, generation: int) -> dict[str, Any]:
    bindings = _read_current_bindings(conn)
    snapshot = {
        "schema": SNAPSHOT_SCHEMA,
        "entity_generation": generation,
        "bindings": bindings,
        "authority": {
            "canonical_state": "MiniUnifiedDB.entity_state.generation",
            "truth_authority": "DETERMINISTIC_GATES_ONLY",
            "effect_authority": "EffectGate_ONLY",
        },
    }
    snapshot_json = _canonical_json(snapshot)
    digest = _sha256_text(snapshot_json)
    conn.execute(
        """INSERT INTO cognition_binding_snapshots(
               entity_generation,snapshot_digest,bindings_json,created_at)
           VALUES(?,?,?,?)""",
        (generation, digest, snapshot_json, _utc_now()),
    )
    return {"snapshot_digest": digest, "bindings": bindings}


def activate_binding(
    conn: sqlite3.Connection,
    *,
    role: str,
    object_digest: str,
    expected_generation: int,
) -> dict[str, Any]:
    """Atomically activate one role and bump the sole MiniUnifiedDB generation CAS."""
    role = _nonempty(role, "ROLE")
    expected_kind = ROLE_KINDS.get(role)
    if expected_kind is None:
        raise CognitionStoreError("ROLE_NOT_ADMITTED:" + role)
    if not isinstance(expected_generation, int) or isinstance(expected_generation, bool) or expected_generation < 0:
        raise CognitionStoreError("EXPECTED_GENERATION_INVALID")
    if not isinstance(object_digest, str) or _HEX64.fullmatch(object_digest) is None:
        raise CognitionStoreError("OBJECT_DIGEST_INVALID")
    if conn.in_transaction:
        raise CognitionStoreError("CALLER_TRANSACTION_ACTIVE")

    conn.execute("BEGIN IMMEDIATE")
    try:
        current_generation = _require_entity_state(conn)
        if current_generation != expected_generation:
            raise CognitionStoreError("STALE_GENERATION")
        row = conn.execute(
            "SELECT object_kind FROM cognition_objects WHERE object_digest=?", (object_digest,)
        ).fetchone()
        if row is None:
            raise CognitionStoreError("OBJECT_NOT_FOUND")
        if str(row[0]) != expected_kind:
            raise CognitionStoreError("ROLE_OBJECT_KIND_MISMATCH")

        next_generation = expected_generation + 1
        update = conn.execute(
            "UPDATE entity_state SET generation=? WHERE id=1 AND generation=?",
            (next_generation, expected_generation),
        )
        if update.rowcount != 1:
            raise CognitionStoreError("STALE_GENERATION_CAS")
        conn.execute(
            """INSERT INTO cognition_bindings(role,object_digest,changed_generation,changed_at)
               VALUES(?,?,?,?)
               ON CONFLICT(role) DO UPDATE SET
                 object_digest=excluded.object_digest,
                 changed_generation=excluded.changed_generation,
                 changed_at=excluded.changed_at""",
            (role, object_digest, next_generation, _utc_now()),
        )
        snapshot = _write_snapshot(conn, next_generation)
        conn.commit()
        return {
            "ok": True,
            "role": role,
            "object_digest": object_digest,
            "generation": next_generation,
            **snapshot,
        }
    except Exception:
        conn.rollback()
        raise


def read_snapshot(
    conn: sqlite3.Connection,
    *,
    expected_generation: int,
    required_roles: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Read the current exact generation + active object set and fail closed on drift."""
    if not isinstance(expected_generation, int) or isinstance(expected_generation, bool) or expected_generation < 0:
        raise CognitionStoreError("EXPECTED_GENERATION_INVALID")
    current_generation = _require_entity_state(conn)
    if current_generation != expected_generation:
        raise CognitionStoreError("STALE_GENERATION")
    bindings = _read_current_bindings(conn)
    required = [_nonempty(role, "REQUIRED_ROLE") for role in required_roles]
    unknown = [role for role in required if role not in ROLE_KINDS]
    if unknown:
        raise CognitionStoreError("REQUIRED_ROLE_NOT_ADMITTED:" + unknown[0])
    missing = [role for role in required if role not in bindings]
    if missing:
        raise CognitionStoreError("REQUIRED_BINDING_MISSING:" + missing[0])

    objects: dict[str, Any] = {}
    for role in required:
        digest = bindings[role]
        row = conn.execute(
            "SELECT object_kind,object_version,payload_json,provenance_json,envelope_json "
            "FROM cognition_objects WHERE object_digest=?",
            (digest,),
        ).fetchone()
        if row is None:
            raise CognitionStoreError("BOUND_OBJECT_MISSING:" + role)
        envelope_json = str(row[4])
        if _sha256_text(envelope_json) != digest:
            raise CognitionStoreError("BOUND_OBJECT_DIGEST_MISMATCH:" + role)
        if str(row[0]) != ROLE_KINDS[role]:
            raise CognitionStoreError("BOUND_OBJECT_KIND_MISMATCH:" + role)
        objects[role] = {
            "object_digest": digest,
            "object_kind": str(row[0]),
            "object_version": str(row[1]),
            "payload": json.loads(str(row[2])),
            "provenance": json.loads(str(row[3])),
        }

    snapshot = {
        "schema": SNAPSHOT_SCHEMA,
        "entity_generation": current_generation,
        "bindings": bindings,
        "authority": {
            "canonical_state": "MiniUnifiedDB.entity_state.generation",
            "truth_authority": "DETERMINISTIC_GATES_ONLY",
            "effect_authority": "EffectGate_ONLY",
        },
    }
    snapshot_digest = _sha256_text(_canonical_json(snapshot))
    return {
        "ok": True,
        "generation": current_generation,
        "snapshot_digest": snapshot_digest,
        "bindings": bindings,
        "objects": objects,
    }


__all__ = [
    "SCHEMA_VERSION",
    "OBJECT_SCHEMA",
    "SNAPSHOT_SCHEMA",
    "ROLE_KINDS",
    "CognitionStoreError",
    "init_schema",
    "put_object",
    "activate_binding",
    "read_snapshot",
]
