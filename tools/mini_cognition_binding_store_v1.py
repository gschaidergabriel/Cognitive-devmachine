#!/usr/bin/env python3
"""Versioned cognition-object/binding store inside the canonical MiniUnifiedDB.

This module creates no second state authority. Objects and the active cognition binding
live in the same SQLite database and activation is fenced by entity_state.generation.
All model/J-Space/GRF/Zero values remain identities/configuration/evidence, never truth.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sqlite3
import time
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_COGNITION_BINDING_STORE/v1"
OBJECT_SCHEMA = "MINI_COGNITION_OBJECT/v1"
BINDING_SCHEMA = "MINI_COGNITION_BINDING/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
OBJECT_KINDS = {
    "ZERO_IDENTITY",
    "GRF",
    "HYPERPOSITION",
    "BUNDLED_MODEL",
    "JACOBIAN_LENS",
    "WORKSPACE_CALIBRATION",
}
REQUIRED_BINDING_KINDS = (
    "ZERO_IDENTITY",
    "GRF",
    "HYPERPOSITION",
    "BUNDLED_MODEL",
    "JACOBIAN_LENS",
    "WORKSPACE_CALIBRATION",
)


class CognitionBindingError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitionBindingError(message)


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
        raise CognitionBindingError(f"NON_CANONICAL_JSON:{type(exc).__name__}") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _digest(value: Any, field: str) -> str:
    _need(type(value) is str and HEX64.fullmatch(value) is not None, f"{field}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{field}:PLACEHOLDER_FORBIDDEN")
    return value


def _text(value: Any, field: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{field}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def install_schema(db: sqlite3.Connection) -> None:
    """Install tables in the existing MiniUnifiedDB transaction domain."""
    db.execute(
        """CREATE TABLE IF NOT EXISTS cognition_objects(
             object_id TEXT PRIMARY KEY,
             object_kind TEXT NOT NULL,
             object_version TEXT NOT NULL,
             subject_sha256 TEXT NOT NULL,
             object_json TEXT NOT NULL,
             object_sha256 TEXT NOT NULL,
             provenance_json TEXT NOT NULL,
             created_at REAL NOT NULL)"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS cognition_bindings(
             binding_id TEXT PRIMARY KEY,
             binding_json TEXT NOT NULL,
             binding_sha256 TEXT NOT NULL,
             activated_generation INTEGER,
             created_at REAL NOT NULL)"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS cognition_binding_state(
             singleton INTEGER PRIMARY KEY CHECK(singleton=1),
             active_binding_id TEXT,
             updated_at REAL NOT NULL)"""
    )
    db.execute(
        "INSERT OR IGNORE INTO cognition_binding_state(singleton,active_binding_id,updated_at) VALUES(1,NULL,0)"
    )


def put_object(
    db: sqlite3.Connection,
    *,
    kind: str,
    version: str,
    subject_sha256: str,
    payload: Mapping[str, Any],
    provenance_refs: list[str],
) -> dict[str, Any]:
    """Insert one immutable cognition object; byte-identical reinsertion is idempotent."""
    kind = _text(kind, "kind")
    _need(kind in OBJECT_KINDS, "OBJECT_KIND_UNSUPPORTED")
    version = _text(version, "version")
    subject_sha256 = _digest(subject_sha256, "subject_sha256")
    _need(isinstance(payload, Mapping), "payload:OBJECT_REQUIRED")
    _need(
        type(provenance_refs) is list
        and bool(provenance_refs)
        and all(type(x) is str and bool(x.strip()) for x in provenance_refs),
        "provenance_refs:NONEMPTY_TEXT_LIST_REQUIRED",
    )
    refs = [x.strip() for x in provenance_refs]
    _need(len(refs) == len(set(refs)), "provenance_refs:DUPLICATE")
    envelope = {
        "schema": OBJECT_SCHEMA,
        "kind": kind,
        "version": version,
        "subject_sha256": subject_sha256,
        "payload": copy.deepcopy(dict(payload)),
        "provenance_refs": refs,
        "authority": "MiniUnifiedDB",
        "structural_authority": "IDENTITY_CONFIGURATION_ONLY",
    }
    object_sha256 = _sha256(envelope)
    object_id = hashlib.sha256(
        b"MINI_COGNITION_OBJECT_ID/v1\0" + _canonical_bytes([kind, version, subject_sha256, object_sha256])
    ).hexdigest()
    raw = _canonical_bytes(envelope).decode("utf-8")
    provenance_raw = _canonical_bytes(refs).decode("utf-8")
    existing = db.execute(
        "SELECT object_json,object_sha256 FROM cognition_objects WHERE object_id=?", (object_id,)
    ).fetchone()
    if existing is not None:
        _need(existing[0] == raw and existing[1] == object_sha256, "OBJECT_ID_COLLISION")
    else:
        db.execute(
            """INSERT INTO cognition_objects(
                   object_id,object_kind,object_version,subject_sha256,object_json,
                   object_sha256,provenance_json,created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (object_id, kind, version, subject_sha256, raw, object_sha256, provenance_raw, time.time()),
        )
    return {
        "schema": OBJECT_SCHEMA,
        "object_id": object_id,
        "object_kind": kind,
        "subject_sha256": subject_sha256,
        "object_sha256": object_sha256,
    }


def create_binding(
    db: sqlite3.Connection,
    *,
    object_ids: Mapping[str, str],
    boot_binding_receipt_sha256: str,
    policy_authority_sha256: str,
    source_ref: str,
) -> dict[str, Any]:
    """Create immutable, not-yet-active binding over exact admitted object identities."""
    _need(isinstance(object_ids, Mapping), "object_ids:OBJECT_REQUIRED")
    _need(set(object_ids) == set(REQUIRED_BINDING_KINDS), "BINDING_OBJECT_KIND_SET_MISMATCH")
    resolved: dict[str, dict[str, str]] = {}
    for kind in REQUIRED_BINDING_KINDS:
        object_id = _digest(object_ids[kind], f"object_ids.{kind}")
        row = db.execute(
            "SELECT object_kind,subject_sha256,object_sha256 FROM cognition_objects WHERE object_id=?",
            (object_id,),
        ).fetchone()
        _need(row is not None, f"BINDING_OBJECT_MISSING:{kind}")
        _need(row[0] == kind, f"BINDING_OBJECT_KIND_MISMATCH:{kind}")
        resolved[kind] = {
            "object_id": object_id,
            "subject_sha256": _digest(row[1], f"{kind}.subject_sha256"),
            "object_sha256": _digest(row[2], f"{kind}.object_sha256"),
        }
    envelope = {
        "schema": BINDING_SCHEMA,
        "objects": resolved,
        "boot_binding_receipt_sha256": _digest(
            boot_binding_receipt_sha256, "boot_binding_receipt_sha256"
        ),
        "policy_authority_sha256": _digest(policy_authority_sha256, "policy_authority_sha256"),
        "source_ref": _text(source_ref, "source_ref"),
        "authority": "MiniUnifiedDB",
        "candidate_only": True,
        "direct_effect_authority": False,
    }
    binding_sha256 = _sha256(envelope)
    binding_id = hashlib.sha256(
        b"MINI_COGNITION_BINDING_ID/v1\0" + _canonical_bytes(envelope)
    ).hexdigest()
    raw = _canonical_bytes(envelope).decode("utf-8")
    existing = db.execute(
        "SELECT binding_json,binding_sha256 FROM cognition_bindings WHERE binding_id=?", (binding_id,)
    ).fetchone()
    if existing is not None:
        _need(existing[0] == raw and existing[1] == binding_sha256, "BINDING_ID_COLLISION")
    else:
        db.execute(
            """INSERT INTO cognition_bindings(
                   binding_id,binding_json,binding_sha256,activated_generation,created_at)
               VALUES(?,?,?,NULL,?)""",
            (binding_id, raw, binding_sha256, time.time()),
        )
    return {
        "schema": BINDING_SCHEMA,
        "binding_id": binding_id,
        "binding_sha256": binding_sha256,
    }


def activate_binding(
    db: sqlite3.Connection,
    *,
    binding_id: str,
    expected_generation: int,
) -> dict[str, Any]:
    """CAS-activate a binding and increment the single MiniUnifiedDB generation exactly once."""
    binding_id = _digest(binding_id, "binding_id")
    _need(type(expected_generation) is int and expected_generation >= 0, "EXPECTED_GENERATION_INVALID")
    db.execute("BEGIN IMMEDIATE")
    try:
        install_schema(db)
        state = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
        _need(state is not None, "ENTITY_STATE_MISSING")
        _need(int(state[0]) == expected_generation, "STALE_GENERATION")
        binding = db.execute(
            "SELECT binding_sha256,activated_generation FROM cognition_bindings WHERE binding_id=?",
            (binding_id,),
        ).fetchone()
        _need(binding is not None, "BINDING_NOT_FOUND")
        _need(binding[1] is None, "BINDING_ALREADY_ACTIVATED")
        new_generation = expected_generation + 1
        now = time.time()
        updated = db.execute(
            "UPDATE entity_state SET generation=?,updated_at=? WHERE id=1 AND generation=?",
            (new_generation, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), expected_generation),
        )
        _need(updated.rowcount == 1, "GENERATION_CAS_FAILED")
        db.execute(
            "UPDATE cognition_bindings SET activated_generation=? WHERE binding_id=? AND activated_generation IS NULL",
            (new_generation, binding_id),
        )
        db.execute(
            "UPDATE cognition_binding_state SET active_binding_id=?,updated_at=? WHERE singleton=1",
            (binding_id, now),
        )
        db.commit()
        return {
            "ok": True,
            "binding_id": binding_id,
            "binding_sha256": _digest(binding[0], "binding_sha256"),
            "generation": new_generation,
        }
    except Exception:
        db.rollback()
        raise


def read_active_binding(db: sqlite3.Connection, *, expected_generation: int) -> dict[str, Any]:
    """Read exact current binding; stale generation or absent/unactivated state fails closed."""
    _need(type(expected_generation) is int and expected_generation >= 0, "EXPECTED_GENERATION_INVALID")
    install_schema(db)
    row = db.execute(
        """SELECT e.generation,s.active_binding_id,b.binding_json,b.binding_sha256,b.activated_generation
           FROM entity_state e
           JOIN cognition_binding_state s ON s.singleton=1
           LEFT JOIN cognition_bindings b ON b.binding_id=s.active_binding_id
           WHERE e.id=1"""
    ).fetchone()
    _need(row is not None, "ENTITY_STATE_MISSING")
    _need(int(row[0]) == expected_generation, "STALE_GENERATION")
    _need(row[1] is not None and row[2] is not None, "ACTIVE_COGNITION_BINDING_MISSING")
    _need(row[4] is not None and int(row[4]) <= expected_generation, "COGNITION_BINDING_NOT_ACTIVE")
    envelope = json.loads(row[2])
    _need(envelope.get("schema") == BINDING_SCHEMA, "BINDING_SCHEMA_MISMATCH")
    observed_sha = _sha256(envelope)
    _need(observed_sha == row[3], "BINDING_HASH_MISMATCH")
    objects = envelope.get("objects")
    _need(type(objects) is dict and set(objects) == set(REQUIRED_BINDING_KINDS), "BINDING_OBJECT_SET_INVALID")
    return {
        "ok": True,
        "schema": SCHEMA,
        "generation": expected_generation,
        "binding_id": row[1],
        "binding_sha256": observed_sha,
        "boot_binding_receipt_sha256": envelope["boot_binding_receipt_sha256"],
        "policy_authority_sha256": envelope["policy_authority_sha256"],
        "zero_identity_digest": objects["ZERO_IDENTITY"]["subject_sha256"],
        "grf_digest": objects["GRF"]["subject_sha256"],
        "hyperposition_digest": objects["HYPERPOSITION"]["subject_sha256"],
        "local_model_digest": objects["BUNDLED_MODEL"]["subject_sha256"],
        "jacobian_lens_digest": objects["JACOBIAN_LENS"]["subject_sha256"],
        "workspace_calibration_digest": objects["WORKSPACE_CALIBRATION"]["subject_sha256"],
        "authority": "MiniUnifiedDB",
        "runtime_credit": "ZERO_UNTIL_EXECUTED",
    }
