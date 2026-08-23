#!/usr/bin/env python3
"""MiniUnifiedDB-resident cognition object/bundle binding store v1.

This module stores versioned cognition configuration objects in the SAME MiniUnifiedDB
used by the canonical reference runtime. It creates no second DB, truth ledger, effect
path, recovery ledger, or model authority.

Runtime cognition admission may resolve a bundle only when every required object is
present, digest-valid, and the active bundle is bound to the exact current entity
generation. Stale/missing/malformed bindings fail closed.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_ENTITY_COGNITION_BINDING_STORE/v1"
BUNDLE_SCHEMA = "MINI_ENTITY_COGNITION_BUNDLE/v1"
OBJECT_TYPES = (
    "ZERO_IDENTITY",
    "GRF",
    "HYPERPOSITION",
    "LOCAL_MODEL",
    "JACOBIAN_LENS",
    "WORKSPACE",
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CognitionBindingError(ValueError):
    pass


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise CognitionBindingError(msg)


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
        raise CognitionBindingError("NON_CANONICAL_JSON") from exc


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _digest(value: Any, field: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{field}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{field}:PLACEHOLDER_REJECTED")
    return value


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Install only tables inside the caller-supplied canonical MiniUnifiedDB."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS cognition_objects(
             object_type TEXT NOT NULL,
             object_digest TEXT NOT NULL,
             object_json TEXT NOT NULL,
             created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
             PRIMARY KEY(object_type, object_digest))"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS cognition_bundles(
             singleton INTEGER PRIMARY KEY CHECK(singleton=1),
             schema TEXT NOT NULL,
             entity_generation INTEGER NOT NULL,
             bundle_json TEXT NOT NULL,
             bundle_digest TEXT NOT NULL,
             updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"""
    )


def put_object(conn: sqlite3.Connection, object_type: str, value: Mapping[str, Any]) -> str:
    _need(object_type in OBJECT_TYPES, "OBJECT_TYPE_UNSUPPORTED")
    _need(isinstance(value, Mapping), "OBJECT_MAPPING_REQUIRED")
    normalized = json.loads(canonical_json(dict(value)))
    raw = canonical_json(normalized)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    conn.execute(
        """INSERT OR IGNORE INTO cognition_objects(object_type,object_digest,object_json)
           VALUES(?,?,?)""",
        (object_type, digest, raw),
    )
    row = conn.execute(
        "SELECT object_json FROM cognition_objects WHERE object_type=? AND object_digest=?",
        (object_type, digest),
    ).fetchone()
    _need(row is not None and str(row[0]) == raw, "OBJECT_DIGEST_COLLISION_OR_DRIFT")
    return digest


def _current_generation(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise CognitionBindingError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_MISSING")
    generation = row[0]
    _need(type(generation) is int and generation >= 0, "ENTITY_GENERATION_INVALID")
    return generation


def bind_bundle(
    conn: sqlite3.Connection,
    *,
    expected_generation: int,
    object_digests: Mapping[str, str],
) -> dict[str, Any]:
    """CAS-bind one complete cognition bundle to the exact live entity generation."""
    current = _current_generation(conn)
    _need(type(expected_generation) is int and expected_generation >= 0, "EXPECTED_GENERATION_INVALID")
    _need(current == expected_generation, "STALE_GENERATION")
    _need(isinstance(object_digests, Mapping), "OBJECT_DIGESTS_MAPPING_REQUIRED")
    _need(set(object_digests) == set(OBJECT_TYPES), "COGNITION_BUNDLE_INCOMPLETE")

    normalized: dict[str, str] = {}
    for object_type in OBJECT_TYPES:
        digest = _digest(object_digests[object_type], object_type)
        row = conn.execute(
            "SELECT object_json FROM cognition_objects WHERE object_type=? AND object_digest=?",
            (object_type, digest),
        ).fetchone()
        _need(row is not None, f"COGNITION_OBJECT_MISSING:{object_type}")
        try:
            parsed = json.loads(str(row[0]))
        except json.JSONDecodeError as exc:
            raise CognitionBindingError(f"COGNITION_OBJECT_JSON_INVALID:{object_type}") from exc
        _need(sha256_json(parsed) == digest, f"COGNITION_OBJECT_DIGEST_MISMATCH:{object_type}")
        normalized[object_type] = digest

    doc = {
        "schema": BUNDLE_SCHEMA,
        "entity_generation": expected_generation,
        "objects": normalized,
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "truth": "MiniUnifiedDB deterministic gates",
            "effects": "EffectGate",
            "model_output": "CANDIDATE_ONLY",
        },
    }
    bundle_digest = sha256_json(doc)
    raw = canonical_json(doc)
    conn.execute(
        """INSERT INTO cognition_bundles(singleton,schema,entity_generation,bundle_json,bundle_digest)
           VALUES(1,?,?,?,?)
           ON CONFLICT(singleton) DO UPDATE SET
             schema=excluded.schema,
             entity_generation=excluded.entity_generation,
             bundle_json=excluded.bundle_json,
             bundle_digest=excluded.bundle_digest,
             updated_at=CURRENT_TIMESTAMP""",
        (BUNDLE_SCHEMA, expected_generation, raw, bundle_digest),
    )
    return {"ok": True, "schema": BUNDLE_SCHEMA, "generation": expected_generation, "bundle_digest": bundle_digest}


def resolve_bundle(conn: sqlite3.Connection, *, expected_generation: int) -> dict[str, Any]:
    """Resolve exact active cognition objects or fail closed before inference."""
    current = _current_generation(conn)
    _need(type(expected_generation) is int and expected_generation >= 0, "EXPECTED_GENERATION_INVALID")
    _need(current == expected_generation, "STALE_GENERATION")
    try:
        row = conn.execute(
            "SELECT schema,entity_generation,bundle_json,bundle_digest FROM cognition_bundles WHERE singleton=1"
        ).fetchone()
    except sqlite3.Error as exc:
        raise CognitionBindingError("COGNITION_BINDING_SCHEMA_UNAVAILABLE") from exc
    _need(row is not None, "COGNITION_BUNDLE_MISSING")
    _need(str(row[0]) == BUNDLE_SCHEMA, "COGNITION_BUNDLE_SCHEMA_MISMATCH")
    _need(type(row[1]) is int and int(row[1]) == expected_generation, "COGNITION_BUNDLE_STALE")
    try:
        bundle = json.loads(str(row[2]))
    except json.JSONDecodeError as exc:
        raise CognitionBindingError("COGNITION_BUNDLE_JSON_INVALID") from exc
    observed_bundle_digest = _digest(str(row[3]), "bundle_digest")
    _need(sha256_json(bundle) == observed_bundle_digest, "COGNITION_BUNDLE_DIGEST_MISMATCH")
    _need(bundle.get("schema") == BUNDLE_SCHEMA, "COGNITION_BUNDLE_SCHEMA_MISMATCH")
    _need(bundle.get("entity_generation") == expected_generation, "COGNITION_BUNDLE_GENERATION_MISMATCH")
    objects = bundle.get("objects")
    _need(type(objects) is dict and set(objects) == set(OBJECT_TYPES), "COGNITION_BUNDLE_INCOMPLETE")

    resolved: dict[str, Any] = {}
    for object_type in OBJECT_TYPES:
        digest = _digest(objects[object_type], object_type)
        objrow = conn.execute(
            "SELECT object_json FROM cognition_objects WHERE object_type=? AND object_digest=?",
            (object_type, digest),
        ).fetchone()
        _need(objrow is not None, f"COGNITION_OBJECT_MISSING:{object_type}")
        try:
            value = json.loads(str(objrow[0]))
        except json.JSONDecodeError as exc:
            raise CognitionBindingError(f"COGNITION_OBJECT_JSON_INVALID:{object_type}") from exc
        _need(sha256_json(value) == digest, f"COGNITION_OBJECT_DIGEST_MISMATCH:{object_type}")
        resolved[object_type] = {"digest": digest, "value": value}

    return {
        "ok": True,
        "schema": SCHEMA,
        "generation": expected_generation,
        "bundle_digest": observed_bundle_digest,
        "objects": resolved,
        "authority": "MiniUnifiedDB",
        "runtime_credit": "ZERO_UNTIL_ADMITTED_EXECUTION",
    }


__all__ = [
    "SCHEMA", "BUNDLE_SCHEMA", "OBJECT_TYPES", "CognitionBindingError",
    "canonical_json", "sha256_json", "ensure_schema", "put_object",
    "bind_bundle", "resolve_bundle",
]
