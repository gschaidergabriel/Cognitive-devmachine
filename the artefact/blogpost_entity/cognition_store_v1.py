from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any, Iterable, Mapping

SCHEMA = "MINI_ENTITY_COGNITION_STORE/v1"


class CognitionStoreError(RuntimeError):
    pass


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_entity_state(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entity_state'"
    ).fetchone()
    if row is None:
        raise CognitionStoreError("MINIUNIFIEDDB_ENTITY_STATE_REQUIRED")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(entity_state)").fetchall()}
    if not {"singleton", "generation"}.issubset(cols):
        raise CognitionStoreError("BAD_ENTITY_STATE_SCHEMA")


def _current_generation(conn: sqlite3.Connection) -> int:
    _require_entity_state(conn)
    row = conn.execute(
        "SELECT generation FROM entity_state WHERE singleton=1"
    ).fetchone()
    if row is None:
        raise CognitionStoreError("ENTITY_STATE_ROW_REQUIRED")
    return int(row[0])


def install_schema(conn: sqlite3.Connection) -> None:
    """Install cognition tables inside the existing MiniUnifiedDB authority.

    This function deliberately does not create entity_state or any alternative generation
    authority. The caller must pass the canonical MiniUnifiedDB connection.
    """
    _require_entity_state(conn)
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS mini_cognition_objects(
              object_kind TEXT NOT NULL,
              object_id TEXT NOT NULL,
              version INTEGER NOT NULL CHECK(version >= 1),
              body_json TEXT NOT NULL,
              object_sha256 TEXT NOT NULL,
              provenance_json TEXT NOT NULL,
              created_at REAL NOT NULL DEFAULT (unixepoch('subsec')),
              PRIMARY KEY(object_kind, object_id, version)
            );

            CREATE TABLE IF NOT EXISTS mini_cognition_bindings(
              role TEXT NOT NULL,
              generation INTEGER NOT NULL CHECK(generation >= 0),
              object_kind TEXT NOT NULL,
              object_id TEXT NOT NULL,
              object_version INTEGER NOT NULL,
              object_sha256 TEXT NOT NULL,
              causal_id TEXT NOT NULL,
              source_lock_digest TEXT NOT NULL,
              bound_at REAL NOT NULL DEFAULT (unixepoch('subsec')),
              PRIMARY KEY(role, generation),
              FOREIGN KEY(object_kind, object_id, object_version)
                REFERENCES mini_cognition_objects(object_kind, object_id, version)
            );
            CREATE INDEX IF NOT EXISTS mini_cognition_bindings_object_idx
              ON mini_cognition_bindings(object_kind, object_id, object_version);
            """
        )


def put_object(
    conn: sqlite3.Connection,
    *,
    object_kind: str,
    object_id: str,
    version: int,
    body: Mapping[str, Any],
    provenance: Mapping[str, Any],
) -> str:
    if not object_kind or not object_id or int(version) < 1:
        raise CognitionStoreError("BAD_OBJECT_IDENTITY")
    body_json = _canon(dict(body))
    provenance_json = _canon(dict(provenance))
    digest = _digest_text(
        _canon(
            {
                "body": json.loads(body_json),
                "provenance": json.loads(provenance_json),
            }
        )
    )
    with conn:
        existing = conn.execute(
            "SELECT body_json, object_sha256, provenance_json FROM mini_cognition_objects "
            "WHERE object_kind=? AND object_id=? AND version=?",
            (object_kind, object_id, int(version)),
        ).fetchone()
        if existing is not None:
            if tuple(existing) != (body_json, digest, provenance_json):
                raise CognitionStoreError("IMMUTABLE_OBJECT_CONFLICT")
            return digest
        conn.execute(
            "INSERT INTO mini_cognition_objects("
            "object_kind,object_id,version,body_json,object_sha256,provenance_json) "
            "VALUES(?,?,?,?,?,?)",
            (object_kind, object_id, int(version), body_json, digest, provenance_json),
        )
    return digest


def bind_role(
    conn: sqlite3.Connection,
    *,
    role: str,
    generation: int,
    object_kind: str,
    object_id: str,
    object_version: int,
    causal_id: str,
    source_lock_digest: str,
) -> str:
    if not role or not causal_id or not source_lock_digest:
        raise CognitionStoreError("BAD_BINDING_IDENTITY")
    current = _current_generation(conn)
    if int(generation) != current:
        raise CognitionStoreError("STALE_GENERATION")
    row = conn.execute(
        "SELECT body_json, provenance_json, object_sha256 FROM mini_cognition_objects "
        "WHERE object_kind=? AND object_id=? AND version=?",
        (object_kind, object_id, int(object_version)),
    ).fetchone()
    if row is None:
        raise CognitionStoreError("OBJECT_NOT_FOUND")
    observed = _digest_text(
        _canon(
            {
                "body": json.loads(str(row[0])),
                "provenance": json.loads(str(row[1])),
            }
        )
    )
    if observed != str(row[2]):
        raise CognitionStoreError("OBJECT_DIGEST_MISMATCH")
    object_sha = str(row[2])
    desired = (
        object_kind,
        object_id,
        int(object_version),
        object_sha,
        causal_id,
        source_lock_digest,
    )
    with conn:
        existing = conn.execute(
            "SELECT object_kind,object_id,object_version,object_sha256,causal_id,source_lock_digest "
            "FROM mini_cognition_bindings WHERE role=? AND generation=?",
            (role, int(generation)),
        ).fetchone()
        if existing is not None:
            if tuple(existing) != desired:
                raise CognitionStoreError("IMMUTABLE_BINDING_CONFLICT")
            return object_sha
        conn.execute(
            "INSERT INTO mini_cognition_bindings("
            "role,generation,object_kind,object_id,object_version,object_sha256,causal_id,source_lock_digest) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (role, int(generation), *desired),
        )
    return object_sha


def load_snapshot(
    conn: sqlite3.Connection,
    *,
    generation: int,
    required_roles: Iterable[str],
    causal_id: str,
) -> dict[str, Any]:
    current = _current_generation(conn)
    if int(generation) != current:
        raise CognitionStoreError("STALE_GENERATION")
    roles = tuple(dict.fromkeys(str(r) for r in required_roles if str(r)))
    if not roles:
        raise CognitionStoreError("REQUIRED_ROLES_EMPTY")
    bindings: dict[str, dict[str, Any]] = {}
    for role in roles:
        row = conn.execute(
            "SELECT b.object_kind,b.object_id,b.object_version,b.object_sha256,b.causal_id,b.source_lock_digest,"
            "o.body_json,o.provenance_json,o.object_sha256 "
            "FROM mini_cognition_bindings b JOIN mini_cognition_objects o "
            "ON o.object_kind=b.object_kind AND o.object_id=b.object_id AND o.version=b.object_version "
            "WHERE b.role=? AND b.generation=?",
            (role, int(generation)),
        ).fetchone()
        if row is None:
            raise CognitionStoreError("MISSING_ROLE:" + role)
        if str(row[4]) != causal_id:
            raise CognitionStoreError("CAUSAL_ID_MISMATCH:" + role)
        observed = _digest_text(
            _canon(
                {
                    "body": json.loads(str(row[6])),
                    "provenance": json.loads(str(row[7])),
                }
            )
        )
        if str(row[3]) != str(row[8]) or observed != str(row[8]):
            raise CognitionStoreError("OBJECT_DIGEST_MISMATCH:" + role)
        bindings[role] = {
            "object_kind": str(row[0]),
            "object_id": str(row[1]),
            "version": int(row[2]),
            "sha256": str(row[3]),
            "source_lock_digest": str(row[5]),
            "body": json.loads(str(row[6])),
            "provenance": json.loads(str(row[7])),
        }
    payload = {
        "schema": SCHEMA,
        "generation": int(generation),
        "causal_id": causal_id,
        "roles": bindings,
    }
    payload["snapshot_digest"] = _digest_text(_canon(payload))
    return payload
