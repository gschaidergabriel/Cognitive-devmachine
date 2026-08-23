#!/usr/bin/env python3
"""Versioned MiniUnifiedDB cognition-object/binding store.

This module is a deterministic state/configuration primitive for the active Mini Entity
pipeline. It does not execute inference, mint semantic truth, perform effects, or grant
J-Space/GWT/runtime credit.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from collections.abc import Mapping, Sequence
from typing import Any

SCHEMA_VERSION = "MINI_COGNITION_STORE/v1"
OBJECT_SCHEMA = "MINI_COGNITION_OBJECT/v1"
BINDING_SCHEMA = "MINI_COGNITION_BINDING/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_BINDING_KINDS = (
    "ZERO_IDENTITY",
    "GRF",
    "HYPERPOSITION",
    "WORKSPACE",
    "BUNDLED_MANIFEST",
    "JSPACE_PROFILE",
    "WORKSPACE_CALIBRATION",
    "BOOT_BINDING_RECEIPT",
)
OPTIONAL_BINDING_KINDS = ("LENS_PROFILE",)
ALL_BINDING_KINDS = frozenset(REQUIRED_BINDING_KINDS + OPTIONAL_BINDING_KINDS)


class CognitionStoreError(ValueError):
    pass


def _need(cond: bool, error: str) -> None:
    if not cond:
        raise CognitionStoreError(error)


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CognitionStoreError("NONCANONICAL_JSON") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hex64(value: Any, name: str) -> str:
    _need(type(value) is str and HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:TEXT_REQUIRED")
    return value.strip()


def _generation(value: Any) -> int:
    _need(type(value) is int and value >= 0, "GENERATION_INVALID")
    return value


def _provenance(refs: Sequence[str]) -> list[str]:
    _need(isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)), "PROVENANCE_LIST_REQUIRED")
    clean = [_text(x, "PROVENANCE_REF") for x in refs]
    _need(bool(clean), "PROVENANCE_REQUIRED")
    _need(len(clean) == len(set(clean)), "PROVENANCE_DUPLICATE")
    return clean


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ensure_schema(db: sqlite3.Connection) -> None:
    """Create only cognition tables/indexes inside the existing MiniUnifiedDB."""
    db.execute(
        """CREATE TABLE IF NOT EXISTS cognition_objects(
             object_id TEXT PRIMARY KEY,
             schema TEXT NOT NULL,
             kind TEXT NOT NULL,
             version TEXT NOT NULL,
             payload_json TEXT NOT NULL,
             payload_sha256 TEXT NOT NULL,
             provenance_json TEXT NOT NULL,
             created_at TEXT NOT NULL)"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS cognition_bindings(
             binding_digest TEXT PRIMARY KEY,
             schema TEXT NOT NULL,
             generation INTEGER NOT NULL,
             objects_json TEXT NOT NULL,
             created_at TEXT NOT NULL,
             retired_at TEXT)"""
    )
    db.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS cognition_bindings_one_active
           ON cognition_bindings((1)) WHERE retired_at IS NULL"""
    )


def install_object(
    db: sqlite3.Connection,
    *,
    kind: str,
    version: str,
    payload: Mapping[str, Any],
    provenance_refs: Sequence[str],
) -> dict[str, Any]:
    """Install an immutable, provenance-bound cognition object idempotently."""
    kind = _text(kind, "KIND")
    _need(kind in ALL_BINDING_KINDS, "KIND_UNSUPPORTED")
    version = _text(version, "VERSION")
    _need(isinstance(payload, Mapping), "PAYLOAD_OBJECT_REQUIRED")
    provenance = _provenance(provenance_refs)
    payload_obj = dict(payload)
    payload_bytes = _canonical_bytes(payload_obj)
    payload_sha = _sha256(payload_bytes)
    envelope = {
        "schema": OBJECT_SCHEMA,
        "kind": kind,
        "version": version,
        "payload_sha256": payload_sha,
        "provenance_refs": provenance,
    }
    object_id = _sha256(_canonical_bytes(envelope))
    payload_json = payload_bytes.decode("utf-8")
    provenance_json = _canonical_bytes(provenance).decode("utf-8")
    now = _utc_now()

    existing = db.execute(
        "SELECT schema,kind,version,payload_json,payload_sha256,provenance_json FROM cognition_objects WHERE object_id=?",
        (object_id,),
    ).fetchone()
    if existing is not None:
        observed = tuple(existing)
        expected = (OBJECT_SCHEMA, kind, version, payload_json, payload_sha, provenance_json)
        _need(observed == expected, "OBJECT_ID_COLLISION_OR_MUTATION")
        return {"ok": True, "object_id": object_id, "payload_sha256": payload_sha, "idempotent": True}

    db.execute(
        """INSERT INTO cognition_objects(
               object_id,schema,kind,version,payload_json,payload_sha256,provenance_json,created_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        (object_id, OBJECT_SCHEMA, kind, version, payload_json, payload_sha, provenance_json, now),
    )
    return {"ok": True, "object_id": object_id, "payload_sha256": payload_sha, "idempotent": False}


def _entity_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise CognitionStoreError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_MISSING")
    return _generation(row[0])


def _validate_object_row(row: sqlite3.Row | tuple[Any, ...] | None, *, expected_kind: str) -> dict[str, Any]:
    _need(row is not None, f"COGNITION_OBJECT_MISSING:{expected_kind}")
    object_id, schema, kind, version, payload_json, payload_sha, provenance_json = tuple(row)
    _hex64(object_id, "OBJECT_ID")
    _need(schema == OBJECT_SCHEMA, "OBJECT_SCHEMA_MISMATCH")
    _need(kind == expected_kind, f"OBJECT_KIND_MISMATCH:{expected_kind}")
    _text(version, "OBJECT_VERSION")
    try:
        payload = json.loads(payload_json)
        provenance = json.loads(provenance_json)
    except json.JSONDecodeError as exc:
        raise CognitionStoreError("OBJECT_JSON_CORRUPT") from exc
    _need(isinstance(payload, dict), "OBJECT_PAYLOAD_NOT_OBJECT")
    _need(_sha256(_canonical_bytes(payload)) == _hex64(payload_sha, "PAYLOAD_SHA256"), "OBJECT_PAYLOAD_DIGEST_MISMATCH")
    provenance_clean = _provenance(provenance)
    envelope = {
        "schema": OBJECT_SCHEMA,
        "kind": kind,
        "version": version,
        "payload_sha256": payload_sha,
        "provenance_refs": provenance_clean,
    }
    _need(_sha256(_canonical_bytes(envelope)) == object_id, "OBJECT_ID_BINDING_MISMATCH")
    return {
        "object_id": object_id,
        "kind": kind,
        "version": version,
        "payload": payload,
        "payload_sha256": payload_sha,
        "provenance_refs": provenance_clean,
    }


def _load_object(db: sqlite3.Connection, object_id: str, expected_kind: str) -> dict[str, Any]:
    object_id = _hex64(object_id, f"{expected_kind}_OBJECT_ID")
    row = db.execute(
        """SELECT object_id,schema,kind,version,payload_json,payload_sha256,provenance_json
           FROM cognition_objects WHERE object_id=?""",
        (object_id,),
    ).fetchone()
    return _validate_object_row(row, expected_kind=expected_kind)


def activate_binding(
    db: sqlite3.Connection,
    *,
    generation: int,
    object_ids: Mapping[str, str | None],
) -> dict[str, Any]:
    """Stage one generation-fenced active binding; caller owns the DB transaction."""
    generation = _generation(generation)
    _need(isinstance(object_ids, Mapping), "OBJECT_BINDINGS_REQUIRED")
    keys = set(object_ids)
    _need(set(REQUIRED_BINDING_KINDS).issubset(keys), "REQUIRED_BINDING_MISSING")
    _need(keys.issubset(ALL_BINDING_KINDS), "UNKNOWN_BINDING_KIND")
    current_generation = _entity_generation(db)
    _need(generation == current_generation, "STALE_GENERATION")

    normalized: dict[str, str | None] = {}
    for kind in REQUIRED_BINDING_KINDS:
        value = object_ids.get(kind)
        _need(value is not None, f"REQUIRED_BINDING_MISSING:{kind}")
        obj = _load_object(db, str(value), kind)
        normalized[kind] = obj["object_id"]
    for kind in OPTIONAL_BINDING_KINDS:
        value = object_ids.get(kind)
        if value is None:
            normalized[kind] = None
        else:
            obj = _load_object(db, str(value), kind)
            normalized[kind] = obj["object_id"]

    binding_material = {
        "schema": BINDING_SCHEMA,
        "generation": generation,
        "objects": normalized,
    }
    binding_digest = _sha256(_canonical_bytes(binding_material))
    objects_json = _canonical_bytes(normalized).decode("utf-8")
    now = _utc_now()

    db.execute(
        "UPDATE cognition_bindings SET retired_at=? WHERE retired_at IS NULL AND binding_digest<>?",
        (now, binding_digest),
    )
    db.execute(
        """INSERT INTO cognition_bindings(
               binding_digest,schema,generation,objects_json,created_at,retired_at)
           VALUES(?,?,?,?,?,NULL)
           ON CONFLICT(binding_digest) DO UPDATE SET retired_at=NULL""",
        (binding_digest, BINDING_SCHEMA, generation, objects_json, now),
    )
    return {"ok": True, "binding_digest": binding_digest, "generation": generation, "objects": normalized}


def load_active_binding(db: sqlite3.Connection, *, expected_generation: int) -> dict[str, Any]:
    """Load and fully revalidate the single active binding for the live generation."""
    expected_generation = _generation(expected_generation)
    live_generation = _entity_generation(db)
    _need(live_generation == expected_generation, "STALE_EXPECTED_GENERATION")
    rows = db.execute(
        """SELECT binding_digest,schema,generation,objects_json
           FROM cognition_bindings WHERE retired_at IS NULL"""
    ).fetchall()
    _need(len(rows) == 1, "ACTIVE_BINDING_COUNT_INVALID")
    binding_digest, schema, generation, objects_json = tuple(rows[0])
    _hex64(binding_digest, "BINDING_DIGEST")
    _need(schema == BINDING_SCHEMA, "BINDING_SCHEMA_MISMATCH")
    _need(_generation(generation) == live_generation, "STALE_ACTIVE_BINDING_GENERATION")
    try:
        object_ids = json.loads(objects_json)
    except json.JSONDecodeError as exc:
        raise CognitionStoreError("BINDING_JSON_CORRUPT") from exc
    _need(type(object_ids) is dict, "BINDING_OBJECT_MAP_REQUIRED")
    _need(set(object_ids) == ALL_BINDING_KINDS, "BINDING_OBJECT_SET_MISMATCH")

    objects: dict[str, Any] = {}
    normalized: dict[str, str | None] = {}
    for kind in REQUIRED_BINDING_KINDS:
        value = object_ids.get(kind)
        _need(value is not None, f"REQUIRED_BINDING_MISSING:{kind}")
        obj = _load_object(db, str(value), kind)
        objects[kind] = obj
        normalized[kind] = obj["object_id"]
    for kind in OPTIONAL_BINDING_KINDS:
        value = object_ids.get(kind)
        if value is None:
            objects[kind] = None
            normalized[kind] = None
        else:
            obj = _load_object(db, str(value), kind)
            objects[kind] = obj
            normalized[kind] = obj["object_id"]

    expected_digest = _sha256(
        _canonical_bytes({"schema": BINDING_SCHEMA, "generation": generation, "objects": normalized})
    )
    _need(binding_digest == expected_digest, "BINDING_DIGEST_MISMATCH")
    return {
        "ok": True,
        "schema": SCHEMA_VERSION,
        "binding_digest": binding_digest,
        "generation": generation,
        "objects": objects,
        "authority": "MINIUNIFIEDDB_CANONICAL_CONFIGURATION_ONLY",
        "truth_credit": "ZERO",
        "effect_credit": "ZERO",
        "runtime_credit": "ZERO",
    }
