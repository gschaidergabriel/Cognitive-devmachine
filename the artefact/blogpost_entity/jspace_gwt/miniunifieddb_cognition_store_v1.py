#!/usr/bin/env python3
"""Reference binding API for MINIUNIFIEDDB_COGNITION_SCHEMA/v1.

This module operates on the caller's existing MiniUnifiedDB connection. It is not a
second state store, truth authority, effect authority, or runtime identity. The intended
integration point is pipeline/bootstrap write responsibility; observational read phases
must not call install_schema().
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA_ID = "MINIUNIFIEDDB_COGNITION_SCHEMA/v1"
OBJECT_SCHEMA = "MINIUNIFIEDDB_COGNITION_OBJECT/v1"
HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "MINIUNIFIEDDB_COGNITION_SCHEMA_V1.sql"


class CognitionStoreFault(RuntimeError):
    pass


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
        raise CognitionStoreFault("COGNITION_NON_CANONICAL_JSON") from exc


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_hex_digest(name: str, value: str) -> str:
    text = str(value)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise CognitionStoreFault(f"{name}_BAD_DIGEST")
    return text


def _live_generation(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    if row is None:
        raise CognitionStoreFault("COGNITION_ENTITY_STATE_MISSING")
    generation = int(row[0])
    if generation < 0:
        raise CognitionStoreFault("COGNITION_BAD_GENERATION")
    return generation


def install_schema(conn: sqlite3.Connection) -> None:
    """Install the schema during the canonical write/bootstrap phase only."""
    if conn.in_transaction:
        raise CognitionStoreFault("COGNITION_SCHEMA_TRANSACTION_ALREADY_ACTIVE")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def put_object(
    conn: sqlite3.Connection,
    *,
    object_kind: str,
    schema_version: str,
    payload: Any,
    provenance: Any,
    generation: int,
    causal_id: str,
    created_at: str,
) -> str:
    """Persist an immutable provenance-bound cognition object in MiniUnifiedDB.

    Object creation is serialized with BEGIN IMMEDIATE and must match the live canonical
    generation. Re-inserting the exact same object is idempotent; a digest collision with
    different bytes fails closed.
    """
    if conn.in_transaction:
        raise CognitionStoreFault("COGNITION_OBJECT_TRANSACTION_ALREADY_ACTIVE")
    generation = int(generation)
    object_kind = str(object_kind)
    schema_version = str(schema_version)
    causal_id = str(causal_id)
    created_at = str(created_at)
    if not object_kind or not schema_version or not causal_id or not created_at:
        raise CognitionStoreFault("COGNITION_OBJECT_REQUIRED_FIELD_EMPTY")

    provenance_json = canonical_json(provenance)
    provenance_sha256 = sha256_text(provenance_json)
    envelope = {
        "schema": OBJECT_SCHEMA,
        "object_kind": object_kind,
        "schema_version": schema_version,
        "payload": payload,
        "provenance": provenance,
        "created_generation": generation,
        "created_causal_id": causal_id,
        "created_at": created_at,
        "truth_authority": False,
        "effect_authority": False,
    }
    object_json = canonical_json(envelope)
    object_digest = sha256_text(object_json)

    try:
        conn.execute("BEGIN IMMEDIATE")
        live = _live_generation(conn)
        if generation != live:
            raise CognitionStoreFault("COGNITION_OBJECT_STALE_GENERATION")
        conn.execute(
            """
            INSERT OR IGNORE INTO cognition_objects(
              object_digest,object_kind,schema_version,object_json,object_sha256,
              provenance_json,provenance_sha256,created_generation,created_causal_id,
              created_at,truth_authority,effect_authority
            ) VALUES(?,?,?,?,?,?,?,?,?,?,0,0)
            """,
            (
                object_digest,
                object_kind,
                schema_version,
                object_json,
                object_digest,
                provenance_json,
                provenance_sha256,
                generation,
                causal_id,
                created_at,
            ),
        )
        row = conn.execute(
            """
            SELECT object_kind,schema_version,object_json,object_sha256,provenance_json,
                   provenance_sha256,created_generation,created_causal_id,created_at,
                   truth_authority,effect_authority
            FROM cognition_objects WHERE object_digest=?
            """,
            (object_digest,),
        ).fetchone()
        expected = (
            object_kind,
            schema_version,
            object_json,
            object_digest,
            provenance_json,
            provenance_sha256,
            generation,
            causal_id,
            created_at,
            0,
            0,
        )
        if row is None or tuple(row) != expected:
            raise CognitionStoreFault("COGNITION_OBJECT_DIGEST_COLLISION_OR_DRIFT")
        conn.commit()
        return object_digest
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise


def bind_object(
    conn: sqlite3.Connection,
    *,
    binding_name: str,
    object_digest: str,
    generation: int,
    semantic_class: str,
    causal_id: str,
    receipt_digest: str,
    status: str,
    bound_at: str,
    workspace_digest: str | None = None,
    profile_id: str | None = None,
    profile_sha256: str | None = None,
) -> None:
    """Append one generation-fenced binding to an immutable cognition object.

    Bindings never carry truth/effect authority. A new generation creates a new row;
    mutation or deletion of an existing generation binding is forbidden by schema.
    """
    if conn.in_transaction:
        raise CognitionStoreFault("COGNITION_BIND_TRANSACTION_ALREADY_ACTIVE")
    binding_name = str(binding_name)
    semantic_class = str(semantic_class)
    causal_id = str(causal_id)
    status = str(status)
    bound_at = str(bound_at)
    object_digest = _require_hex_digest("COGNITION_OBJECT", object_digest)
    receipt_digest = _require_hex_digest("COGNITION_RECEIPT", receipt_digest)
    if workspace_digest is not None:
        workspace_digest = _require_hex_digest("COGNITION_WORKSPACE", workspace_digest)
    if profile_sha256 is not None:
        profile_sha256 = _require_hex_digest("COGNITION_PROFILE", profile_sha256)
    if (profile_id is None) != (profile_sha256 is None):
        raise CognitionStoreFault("COGNITION_PROFILE_BINDING_INCOMPLETE")
    if not binding_name or not semantic_class or not causal_id or not bound_at:
        raise CognitionStoreFault("COGNITION_BIND_REQUIRED_FIELD_EMPTY")

    generation = int(generation)
    try:
        conn.execute("BEGIN IMMEDIATE")
        live = _live_generation(conn)
        if generation != live:
            raise CognitionStoreFault("COGNITION_BINDING_STALE_GENERATION")
        obj = conn.execute(
            "SELECT created_generation FROM cognition_objects WHERE object_digest=?",
            (object_digest,),
        ).fetchone()
        if obj is None:
            raise CognitionStoreFault("COGNITION_OBJECT_MISSING")
        if int(obj[0]) > generation:
            raise CognitionStoreFault("COGNITION_OBJECT_FROM_FUTURE")
        conn.execute(
            """
            INSERT INTO cognition_bindings(
              binding_name,entity_generation,object_digest,semantic_class,causal_id,
              workspace_digest,profile_id,profile_sha256,receipt_digest,status,bound_at,
              truth_authority,effect_authority
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,0,0)
            """,
            (
                binding_name,
                generation,
                object_digest,
                semantic_class,
                causal_id,
                workspace_digest,
                profile_id,
                profile_sha256,
                receipt_digest,
                status,
                bound_at,
            ),
        )
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise


def read_binding(
    conn: sqlite3.Connection,
    *,
    binding_name: str,
    expected_generation: int,
) -> dict[str, Any]:
    """Read and cryptographically re-check the exact current-generation binding."""
    live = _live_generation(conn)
    expected_generation = int(expected_generation)
    if expected_generation != live:
        raise CognitionStoreFault("COGNITION_READ_STALE_GENERATION")
    cursor = conn.execute(
        """
        SELECT b.binding_name,b.entity_generation,b.object_digest,b.semantic_class,
               b.causal_id,b.workspace_digest,b.profile_id,b.profile_sha256,
               b.receipt_digest,b.status,b.bound_at,
               b.truth_authority AS binding_truth_authority,
               b.effect_authority AS binding_effect_authority,
               o.object_kind,o.schema_version,o.object_json,o.object_sha256,
               o.provenance_json,o.provenance_sha256,o.created_generation,o.created_causal_id,
               o.created_at,
               o.truth_authority AS object_truth_authority,
               o.effect_authority AS object_effect_authority
        FROM cognition_bindings b
        JOIN cognition_objects o ON o.object_digest=b.object_digest
        WHERE b.binding_name=? AND b.entity_generation=?
        """,
        (str(binding_name), expected_generation),
    )
    row = cursor.fetchone()
    if row is None:
        raise CognitionStoreFault("COGNITION_BINDING_MISSING")
    columns = [description[0] for description in cursor.description]
    data = dict(zip(columns, row))

    if data["object_digest"] != sha256_text(data["object_json"]):
        raise CognitionStoreFault("COGNITION_OBJECT_HASH_MISMATCH")
    if data["object_sha256"] != data["object_digest"]:
        raise CognitionStoreFault("COGNITION_OBJECT_DIGEST_METADATA_MISMATCH")
    if data["provenance_sha256"] != sha256_text(data["provenance_json"]):
        raise CognitionStoreFault("COGNITION_PROVENANCE_HASH_MISMATCH")
    if int(data["binding_truth_authority"]) != 0 or int(data["binding_effect_authority"]) != 0:
        raise CognitionStoreFault("COGNITION_BINDING_AUTHORITY_ESCALATION")
    if int(data["object_truth_authority"]) != 0 or int(data["object_effect_authority"]) != 0:
        raise CognitionStoreFault("COGNITION_OBJECT_AUTHORITY_ESCALATION")

    try:
        envelope = json.loads(data["object_json"])
        stored_provenance = json.loads(data["provenance_json"])
    except json.JSONDecodeError as exc:
        raise CognitionStoreFault("COGNITION_OBJECT_JSON_INVALID") from exc
    if canonical_json(envelope) != data["object_json"]:
        raise CognitionStoreFault("COGNITION_OBJECT_NOT_CANONICAL")
    if canonical_json(stored_provenance) != data["provenance_json"]:
        raise CognitionStoreFault("COGNITION_PROVENANCE_NOT_CANONICAL")
    if envelope.get("schema") != OBJECT_SCHEMA:
        raise CognitionStoreFault("COGNITION_OBJECT_SCHEMA_MISMATCH")
    if envelope.get("object_kind") != data["object_kind"]:
        raise CognitionStoreFault("COGNITION_OBJECT_KIND_MISMATCH")
    if envelope.get("schema_version") != data["schema_version"]:
        raise CognitionStoreFault("COGNITION_OBJECT_VERSION_MISMATCH")
    if envelope.get("created_generation") != data["created_generation"]:
        raise CognitionStoreFault("COGNITION_OBJECT_GENERATION_MISMATCH")
    if envelope.get("created_causal_id") != data["created_causal_id"]:
        raise CognitionStoreFault("COGNITION_OBJECT_CAUSAL_MISMATCH")
    if envelope.get("created_at") != data["created_at"]:
        raise CognitionStoreFault("COGNITION_OBJECT_TIME_MISMATCH")
    if envelope.get("provenance") != stored_provenance:
        raise CognitionStoreFault("COGNITION_OBJECT_PROVENANCE_MISMATCH")
    if envelope.get("truth_authority") is not False or envelope.get("effect_authority") is not False:
        raise CognitionStoreFault("COGNITION_OBJECT_ENVELOPE_AUTHORITY_ESCALATION")
    return data
