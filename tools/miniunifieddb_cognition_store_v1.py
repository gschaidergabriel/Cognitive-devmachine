#!/usr/bin/env python3
"""Versioned cognition-object and turn-binding store inside canonical MiniUnifiedDB.

All records live in the existing MiniUnifiedDB. They are identity/provenance admission
records only: no model output becomes truth and no direct real-effect authority is granted.
Read paths re-derive stored digests so a mutated row cannot keep using an old identity.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from typing import Any, Mapping

SCHEMA = "MINIUNIFIEDDB_COGNITION_STORE/v1"
BOOT_BINDING_SCHEMA = "MINIUNIFIEDDB_COGNITION_BOOT_BINDING/v1"
TURN_BINDING_SCHEMA = "MINIUNIFIEDDB_COGNITION_TURN_BINDING/v1"
OBJECT_KINDS = {
    "ZERO_IDENTITY", "GRF", "HYPERPOSITION", "BUNDLED_MANIFEST",
    "LOCAL_MODEL_CHECKPOINT", "TOKENIZER", "JSPACE_PROFILE",
    "JACOBIAN_LENS_PROFILE", "WORKSPACE_CALIBRATION", "BOOT_SOURCE_LOCK",
    "POLICY_AUTHORITY",
}
DIGEST_BASES = {"CANONICAL_JSON", "EXTERNAL_BYTES"}
BOOT_FIELD_KINDS = {
    "zero_identity_digest": "ZERO_IDENTITY",
    "grf_digest": "GRF",
    "hyperposition_digest": "HYPERPOSITION",
    "bundled_manifest_digest": "BUNDLED_MANIFEST",
    "local_model_digest": "LOCAL_MODEL_CHECKPOINT",
    "tokenizer_digest": "TOKENIZER",
    "jspace_profile_digest": "JSPACE_PROFILE",
    "jacobian_lens_digest": "JACOBIAN_LENS_PROFILE",
    "workspace_calibration_digest": "WORKSPACE_CALIBRATION",
    "boot_source_lock_digest": "BOOT_SOURCE_LOCK",
    "policy_authority_digest": "POLICY_AUTHORITY",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CognitionStoreError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitionStoreError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_obj(value: Any) -> str:
    return sha256_text(canonical_json(value))


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(len(set(value)) > 1, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _refs(value: Any, name: str) -> list[str]:
    _need(type(value) is list, f"{name}:LIST_REQUIRED")
    refs = [_text(item, name) for item in value]
    _need(len(refs) == len(set(refs)), f"{name}:DUPLICATE")
    return refs


def _json_refs(raw: Any, name: str) -> list[str]:
    try:
        parsed = json.loads(str(raw))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CognitionStoreError(f"{name}:JSON_INVALID") from exc
    return _refs(parsed, name)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _current_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise CognitionStoreError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    generation = row[0]
    _need(type(generation) is int and generation >= 0, "ENTITY_GENERATION_INVALID")
    return generation


def install_schema(db: sqlite3.Connection) -> None:
    """Install cognition tables inside the caller transaction without implicit commit."""
    _current_generation(db)
    # SQLite foreign-key enforcement is connection-local and cannot be switched on safely
    # after a transaction has started. The canonical runtime must enable it on connection
    # open; fail closed here rather than silently installing an enforcement-disabled schema.
    fk_row = db.execute("PRAGMA foreign_keys").fetchone()
    _need(fk_row is not None and int(fk_row[0]) == 1, "FOREIGN_KEYS_REQUIRED_BEFORE_TRANSACTION")
    # Never use executescript(): Python's sqlite3 wrapper commits a pending transaction
    # before executing it, which would split the runtime's BEGIN IMMEDIATE bootstrap.
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_objects(
          object_kind TEXT NOT NULL, object_version TEXT NOT NULL, object_digest TEXT NOT NULL,
          digest_basis TEXT NOT NULL CHECK(digest_basis IN ('CANONICAL_JSON','EXTERNAL_BYTES')),
          payload_json TEXT NOT NULL, payload_digest TEXT NOT NULL,
          provenance_refs_json TEXT NOT NULL, created_at TEXT NOT NULL,
          PRIMARY KEY(object_kind,object_version,object_digest))"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_object_admissions(
          object_kind TEXT NOT NULL, object_version TEXT NOT NULL, object_digest TEXT NOT NULL,
          admitted_generation INTEGER NOT NULL, admission_receipt_digest TEXT NOT NULL,
          admitted_at TEXT NOT NULL,
          PRIMARY KEY(object_kind,object_version,object_digest,admitted_generation),
          FOREIGN KEY(object_kind,object_version,object_digest)
            REFERENCES mini_cognition_objects(object_kind,object_version,object_digest))"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_boot_bindings(
          binding_digest TEXT PRIMARY KEY, schema TEXT NOT NULL, entity_generation INTEGER NOT NULL,
          zero_identity_digest TEXT NOT NULL, grf_digest TEXT NOT NULL,
          hyperposition_digest TEXT NOT NULL, bundled_manifest_digest TEXT NOT NULL,
          local_model_digest TEXT NOT NULL, tokenizer_digest TEXT NOT NULL,
          jspace_profile_digest TEXT NOT NULL, jacobian_lens_digest TEXT NOT NULL,
          workspace_calibration_digest TEXT NOT NULL, boot_source_lock_digest TEXT NOT NULL,
          policy_authority_digest TEXT NOT NULL, provenance_refs_json TEXT NOT NULL,
          created_at TEXT NOT NULL, UNIQUE(entity_generation))"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_turn_bindings(
          entity_generation INTEGER NOT NULL, causal_turn_id TEXT NOT NULL,
          binding_digest TEXT NOT NULL, schema TEXT NOT NULL, boot_binding_digest TEXT NOT NULL,
          task_sha256 TEXT NOT NULL, workspace_digest TEXT NOT NULL,
          selected_workspace_slots_json TEXT NOT NULL, contradiction_state TEXT NOT NULL,
          provenance_refs_json TEXT NOT NULL, required_zero_mode TEXT NOT NULL,
          created_at TEXT NOT NULL, PRIMARY KEY(entity_generation,causal_turn_id),
          UNIQUE(binding_digest),
          FOREIGN KEY(boot_binding_digest) REFERENCES mini_cognition_boot_bindings(binding_digest))"""
    )


def register_object(db: sqlite3.Connection, *, object_kind: str, object_version: str,
                    object_digest: str, digest_basis: str, payload: Mapping[str, Any],
                    provenance_refs: list[str]) -> dict[str, Any]:
    _current_generation(db)
    _need(object_kind in OBJECT_KINDS, "OBJECT_KIND_UNSUPPORTED")
    object_version = _text(object_version, "object_version")
    object_digest = _digest(object_digest, "object_digest")
    _need(digest_basis in DIGEST_BASES, "DIGEST_BASIS_UNSUPPORTED")
    _need(isinstance(payload, Mapping), "PAYLOAD_OBJECT_REQUIRED")
    refs = _refs(provenance_refs, "provenance_refs")
    _need(bool(refs), "PROVENANCE_REQUIRED")
    payload_json = canonical_json(dict(payload))
    payload_digest = sha256_text(payload_json)
    if digest_basis == "CANONICAL_JSON":
        _need(object_digest == payload_digest, "OBJECT_DIGEST_PAYLOAD_MISMATCH")
    record = (object_kind, object_version, object_digest, digest_basis,
              payload_json, payload_digest, canonical_json(refs))
    row = db.execute(
        """SELECT object_kind,object_version,object_digest,digest_basis,payload_json,
                  payload_digest,provenance_refs_json FROM mini_cognition_objects
             WHERE object_kind=? AND object_version=? AND object_digest=?""",
        (object_kind, object_version, object_digest),
    ).fetchone()
    if row is not None:
        _need(tuple(row) == record, "IMMUTABLE_OBJECT_COLLISION")
        return {"ok": True, "idempotent": True, "object_digest": object_digest}
    db.execute(
        "INSERT INTO mini_cognition_objects VALUES(?,?,?,?,?,?,?,?)",
        (*record, _utc_now()),
    )
    return {"ok": True, "idempotent": False, "object_digest": object_digest}


def _validate_registered_object(db: sqlite3.Connection, object_kind: str,
                                object_version: str, object_digest: str) -> None:
    row = db.execute(
        """SELECT digest_basis,payload_json,payload_digest,provenance_refs_json
             FROM mini_cognition_objects WHERE object_kind=? AND object_version=? AND object_digest=?""",
        (object_kind, object_version, object_digest),
    ).fetchone()
    _need(row is not None, "OBJECT_NOT_REGISTERED")
    _need(row[0] in DIGEST_BASES, "DIGEST_BASIS_UNSUPPORTED")
    _need(sha256_text(str(row[1])) == _digest(row[2], "payload_digest"), "OBJECT_PAYLOAD_DIGEST_MISMATCH")
    _json_refs(row[3], "provenance_refs")
    if row[0] == "CANONICAL_JSON":
        _need(object_digest == row[2], "OBJECT_DIGEST_PAYLOAD_MISMATCH")


def admit_object(db: sqlite3.Connection, *, object_kind: str, object_version: str,
                 object_digest: str, entity_generation: int,
                 admission_receipt_digest: str) -> dict[str, Any]:
    live = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live, "STALE_GENERATION")
    _need(object_kind in OBJECT_KINDS, "OBJECT_KIND_UNSUPPORTED")
    object_version = _text(object_version, "object_version")
    object_digest = _digest(object_digest, "object_digest")
    receipt = _digest(admission_receipt_digest, "admission_receipt_digest")
    _validate_registered_object(db, object_kind, object_version, object_digest)
    row = db.execute(
        """SELECT admission_receipt_digest FROM mini_cognition_object_admissions
             WHERE object_kind=? AND object_version=? AND object_digest=? AND admitted_generation=?""",
        (object_kind, object_version, object_digest, entity_generation),
    ).fetchone()
    if row is not None:
        _need(row[0] == receipt, "ADMISSION_RECEIPT_CONFLICT")
        return {"ok": True, "idempotent": True}
    db.execute(
        "INSERT INTO mini_cognition_object_admissions VALUES(?,?,?,?,?,?)",
        (object_kind, object_version, object_digest, entity_generation, receipt, _utc_now()),
    )
    return {"ok": True, "idempotent": False}


def _require_admitted_digest(db: sqlite3.Connection, *, object_kind: str,
                             object_digest: str, entity_generation: int) -> None:
    row = db.execute(
        """SELECT o.object_version,a.admission_receipt_digest
             FROM mini_cognition_objects o JOIN mini_cognition_object_admissions a
               ON a.object_kind=o.object_kind AND a.object_version=o.object_version
              AND a.object_digest=o.object_digest
            WHERE o.object_kind=? AND o.object_digest=? AND a.admitted_generation=?
            ORDER BY o.object_version DESC LIMIT 1""",
        (object_kind, object_digest, entity_generation),
    ).fetchone()
    _need(row is not None, f"COGNITION_OBJECT_NOT_ADMITTED:{object_kind}")
    _digest(row[1], "admission_receipt_digest")
    _validate_registered_object(db, object_kind, row[0], object_digest)


def _load_boot(db: sqlite3.Connection, binding_digest: str,
               entity_generation: int) -> dict[str, Any]:
    binding_digest = _digest(binding_digest, "boot_binding_digest")
    row = db.execute(
        """SELECT schema,entity_generation,zero_identity_digest,grf_digest,hyperposition_digest,
                  bundled_manifest_digest,local_model_digest,tokenizer_digest,jspace_profile_digest,
                  jacobian_lens_digest,workspace_calibration_digest,boot_source_lock_digest,
                  policy_authority_digest,provenance_refs_json FROM mini_cognition_boot_bindings
             WHERE binding_digest=? AND entity_generation=?""",
        (binding_digest, entity_generation),
    ).fetchone()
    _need(row is not None, "BOOT_BINDING_UNAVAILABLE")
    _need(row[0] == BOOT_BINDING_SCHEMA, "BOOT_BINDING_SCHEMA_MISMATCH")
    _need(type(row[1]) is int and row[1] == entity_generation, "BOOT_BINDING_STALE_GENERATION")
    fields = {name: _digest(row[index], name)
              for index, name in enumerate(BOOT_FIELD_KINDS, start=2)}
    refs = _json_refs(row[13], "boot_provenance_refs")
    material = {"schema": BOOT_BINDING_SCHEMA, "entity_generation": entity_generation,
                **fields, "provenance_refs": refs}
    _need(sha256_obj(material) == binding_digest, "BOOT_BINDING_DIGEST_MISMATCH")
    for name, kind in BOOT_FIELD_KINDS.items():
        _require_admitted_digest(db, object_kind=kind, object_digest=fields[name],
                                 entity_generation=entity_generation)
    return {**material, "binding_digest": binding_digest}


def admit_boot_binding(db: sqlite3.Connection, *, entity_generation: int,
                       zero_identity_digest: str, grf_digest: str, hyperposition_digest: str,
                       bundled_manifest_digest: str, local_model_digest: str,
                       tokenizer_digest: str, jspace_profile_digest: str,
                       jacobian_lens_digest: str, workspace_calibration_digest: str,
                       boot_source_lock_digest: str, policy_authority_digest: str,
                       provenance_refs: list[str]) -> dict[str, Any]:
    live = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live, "STALE_GENERATION")
    refs = _refs(provenance_refs, "provenance_refs")
    _need(bool(refs), "PROVENANCE_REQUIRED")
    supplied = locals()
    fields = {}
    for name, kind in BOOT_FIELD_KINDS.items():
        fields[name] = _digest(supplied[name], name)
        _require_admitted_digest(db, object_kind=kind, object_digest=fields[name],
                                 entity_generation=entity_generation)
    material = {"schema": BOOT_BINDING_SCHEMA, "entity_generation": entity_generation,
                **fields, "provenance_refs": refs}
    digest = sha256_obj(material)
    row = db.execute("SELECT binding_digest FROM mini_cognition_boot_bindings WHERE entity_generation=?",
                     (entity_generation,)).fetchone()
    if row is not None:
        _load_boot(db, row[0], entity_generation)
        _need(row[0] == digest, "BOOT_BINDING_GENERATION_CONFLICT")
        return {"ok": True, "idempotent": True, "binding_digest": digest}
    db.execute(
        """INSERT INTO mini_cognition_boot_bindings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (digest, BOOT_BINDING_SCHEMA, entity_generation,
         *(fields[name] for name in BOOT_FIELD_KINDS), canonical_json(refs), _utc_now()),
    )
    return {"ok": True, "idempotent": False, "binding_digest": digest}


def _load_turn(db: sqlite3.Connection, entity_generation: int,
               causal_turn_id: str) -> dict[str, Any]:
    row = db.execute(
        """SELECT binding_digest,schema,boot_binding_digest,task_sha256,workspace_digest,
                  selected_workspace_slots_json,contradiction_state,provenance_refs_json,
                  required_zero_mode FROM mini_cognition_turn_bindings
             WHERE entity_generation=? AND causal_turn_id=?""",
        (entity_generation, causal_turn_id),
    ).fetchone()
    _need(row is not None, "TURN_BINDING_UNAVAILABLE")
    digest = _digest(row[0], "turn_binding_digest")
    _need(row[1] == TURN_BINDING_SCHEMA, "TURN_BINDING_SCHEMA_MISMATCH")
    material = {
        "schema": TURN_BINDING_SCHEMA,
        "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "boot_binding_digest": _digest(row[2], "boot_binding_digest"),
        "task_sha256": _digest(row[3], "task_sha256"),
        "workspace_digest": _digest(row[4], "workspace_digest"),
        "selected_workspace_slots": _json_refs(row[5], "selected_workspace_slots"),
        "contradiction_state": _text(row[6], "contradiction_state"),
        "provenance_refs": _json_refs(row[7], "turn_provenance_refs"),
        "required_zero_mode": _text(row[8], "required_zero_mode"),
    }
    _need(sha256_obj(material) == digest, "TURN_BINDING_DIGEST_MISMATCH")
    return {**material, "binding_digest": digest}


def bind_turn(db: sqlite3.Connection, *, entity_generation: int, causal_turn_id: str,
              boot_binding_digest: str, task_text: str, workspace_digest: str,
              selected_workspace_slots: list[str], contradiction_state: str,
              provenance_refs: list[str], required_zero_mode: str) -> dict[str, Any]:
    live = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live, "STALE_GENERATION")
    causal_turn_id = _text(causal_turn_id, "causal_turn_id")
    boot_binding_digest = _digest(boot_binding_digest, "boot_binding_digest")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    workspace_digest = _digest(workspace_digest, "workspace_digest")
    slots = _refs(selected_workspace_slots, "selected_workspace_slots")
    refs = _refs(provenance_refs, "provenance_refs")
    _need(bool(refs), "PROVENANCE_REQUIRED")
    contradiction_state = _text(contradiction_state, "contradiction_state")
    required_zero_mode = _text(required_zero_mode, "required_zero_mode")
    _load_boot(db, boot_binding_digest, entity_generation)
    material = {
        "schema": TURN_BINDING_SCHEMA, "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id, "boot_binding_digest": boot_binding_digest,
        "task_sha256": hashlib.sha256(task_text.encode("utf-8")).hexdigest(),
        "workspace_digest": workspace_digest, "selected_workspace_slots": slots,
        "contradiction_state": contradiction_state, "provenance_refs": refs,
        "required_zero_mode": required_zero_mode,
    }
    digest = sha256_obj(material)
    row = db.execute(
        "SELECT binding_digest FROM mini_cognition_turn_bindings WHERE entity_generation=? AND causal_turn_id=?",
        (entity_generation, causal_turn_id),
    ).fetchone()
    if row is not None:
        _load_turn(db, entity_generation, causal_turn_id)
        _need(row[0] == digest, "TURN_BINDING_CONFLICT")
        return {"ok": True, "idempotent": True, "binding_digest": digest}
    db.execute(
        "INSERT INTO mini_cognition_turn_bindings VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (entity_generation, causal_turn_id, digest, TURN_BINDING_SCHEMA, boot_binding_digest,
         material["task_sha256"], workspace_digest, canonical_json(slots), contradiction_state,
         canonical_json(refs), required_zero_mode, _utc_now()),
    )
    return {"ok": True, "idempotent": False, "binding_digest": digest}


def resolve_prepare_binding(db: sqlite3.Connection, *, entity_generation: int,
                            causal_turn_id: str, task_text: str) -> dict[str, Any]:
    live = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live, "STALE_GENERATION")
    causal_turn_id = _text(causal_turn_id, "causal_turn_id")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    turn = _load_turn(db, entity_generation, causal_turn_id)
    expected = hashlib.sha256(task_text.encode("utf-8")).hexdigest()
    _need(turn["task_sha256"] == expected, "TURN_TASK_BINDING_MISMATCH")
    boot = _load_boot(db, turn["boot_binding_digest"], entity_generation)
    return {
        "ok": True, "schema": SCHEMA, "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id, "turn_binding_digest": turn["binding_digest"],
        "boot_binding_digest": boot["binding_digest"], "task_sha256": turn["task_sha256"],
        "workspace_digest": turn["workspace_digest"],
        "selected_workspace_slots": turn["selected_workspace_slots"],
        "contradiction_state": turn["contradiction_state"],
        "turn_provenance_refs": turn["provenance_refs"],
        "required_zero_mode": turn["required_zero_mode"],
        **{name: boot[name] for name in BOOT_FIELD_KINDS},
        "boot_provenance_refs": boot["provenance_refs"],
        "authority": {"durable_state": "MiniUnifiedDB", "candidate_only": True,
                      "direct_truth_authority": False, "direct_effect_authority": False},
    }
