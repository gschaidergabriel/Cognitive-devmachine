#!/usr/bin/env python3
"""Versioned cognition-object and turn-binding store inside MiniUnifiedDB.

This module adds no second state authority. It stores immutable cognition-object identities,
explicit admissions, one generation-bound boot binding, and exact causal-turn bindings in
the same SQLite MiniUnifiedDB used by the Mini Entity pipeline.

It intentionally does not fabricate missing model/J-Space/boot identities. If an exact
admitted object or current-generation binding is unavailable, callers must fail closed or
typed-abstain before model inference.
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
    "ZERO_IDENTITY",
    "GRF",
    "HYPERPOSITION",
    "BUNDLED_MANIFEST",
    "LOCAL_MODEL_CHECKPOINT",
    "TOKENIZER",
    "JSPACE_PROFILE",
    "JACOBIAN_LENS_PROFILE",
    "WORKSPACE_CALIBRATION",
    "BOOT_SOURCE_LOCK",
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
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


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
    """Install cognition tables without committing caller-owned bootstrap state."""
    _current_generation(db)
    # sqlite3.Connection.executescript() implicitly commits any pending transaction before
    # executing its script. The retained runtime owns one BEGIN IMMEDIATE bootstrap
    # transaction, so schema installation must use individual DDL statements and join that
    # transaction rather than silently breaking its atomicity.
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_objects(
          object_kind TEXT NOT NULL,
          object_version TEXT NOT NULL,
          object_digest TEXT NOT NULL,
          digest_basis TEXT NOT NULL CHECK(digest_basis IN ('CANONICAL_JSON','EXTERNAL_BYTES')),
          payload_json TEXT NOT NULL,
          payload_digest TEXT NOT NULL,
          provenance_refs_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY(object_kind,object_version,object_digest)
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_object_admissions(
          object_kind TEXT NOT NULL,
          object_version TEXT NOT NULL,
          object_digest TEXT NOT NULL,
          admitted_generation INTEGER NOT NULL,
          admission_receipt_digest TEXT NOT NULL,
          admitted_at TEXT NOT NULL,
          PRIMARY KEY(object_kind,object_version,object_digest,admitted_generation),
          FOREIGN KEY(object_kind,object_version,object_digest)
            REFERENCES mini_cognition_objects(object_kind,object_version,object_digest)
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_boot_bindings(
          binding_digest TEXT PRIMARY KEY,
          schema TEXT NOT NULL,
          entity_generation INTEGER NOT NULL,
          zero_identity_digest TEXT NOT NULL,
          grf_digest TEXT NOT NULL,
          hyperposition_digest TEXT NOT NULL,
          bundled_manifest_digest TEXT NOT NULL,
          local_model_digest TEXT NOT NULL,
          tokenizer_digest TEXT NOT NULL,
          jspace_profile_digest TEXT NOT NULL,
          jacobian_lens_digest TEXT NOT NULL,
          workspace_calibration_digest TEXT NOT NULL,
          boot_source_lock_digest TEXT NOT NULL,
          policy_authority_digest TEXT NOT NULL,
          provenance_refs_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE(entity_generation)
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS mini_cognition_turn_bindings(
          entity_generation INTEGER NOT NULL,
          causal_turn_id TEXT NOT NULL,
          binding_digest TEXT NOT NULL,
          schema TEXT NOT NULL,
          boot_binding_digest TEXT NOT NULL,
          task_sha256 TEXT NOT NULL,
          workspace_digest TEXT NOT NULL,
          selected_workspace_slots_json TEXT NOT NULL,
          contradiction_state TEXT NOT NULL,
          provenance_refs_json TEXT NOT NULL,
          required_zero_mode TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY(entity_generation,causal_turn_id),
          UNIQUE(binding_digest),
          FOREIGN KEY(boot_binding_digest) REFERENCES mini_cognition_boot_bindings(binding_digest)
        )"""
    )


def register_object(
    db: sqlite3.Connection,
    *,
    object_kind: str,
    object_version: str,
    object_digest: str,
    digest_basis: str,
    payload: Mapping[str, Any],
    provenance_refs: list[str],
) -> dict[str, Any]:
    """Register immutable cognition-object metadata without admitting it for runtime use."""
    _current_generation(db)
    _need(object_kind in OBJECT_KINDS, "OBJECT_KIND_UNSUPPORTED")
    object_version = _text(object_version, "object_version")
    object_digest = _digest(object_digest, "object_digest")
    _need(digest_basis in DIGEST_BASES, "DIGEST_BASIS_UNSUPPORTED")
    _need(isinstance(payload, Mapping), "PAYLOAD_OBJECT_REQUIRED")
    refs = _refs(provenance_refs, "provenance_refs")
    _need(bool(refs), "PROVENANCE_REQUIRED")

    payload_obj = dict(payload)
    payload_json = canonical_json(payload_obj)
    payload_digest = sha256_text(payload_json)
    if digest_basis == "CANONICAL_JSON":
        _need(object_digest == payload_digest, "OBJECT_DIGEST_PAYLOAD_MISMATCH")

    record = (
        object_kind,
        object_version,
        object_digest,
        digest_basis,
        payload_json,
        payload_digest,
        canonical_json(refs),
    )
    existing = db.execute(
        """SELECT object_kind,object_version,object_digest,digest_basis,payload_json,
                  payload_digest,provenance_refs_json
             FROM mini_cognition_objects
            WHERE object_kind=? AND object_version=? AND object_digest=?""",
        (object_kind, object_version, object_digest),
    ).fetchone()
    if existing is not None:
        _need(tuple(existing) == record, "IMMUTABLE_OBJECT_COLLISION")
        return {"ok": True, "idempotent": True, "object_digest": object_digest}

    db.execute(
        """INSERT INTO mini_cognition_objects(
             object_kind,object_version,object_digest,digest_basis,payload_json,payload_digest,
             provenance_refs_json,created_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        (*record, _utc_now()),
    )
    return {"ok": True, "idempotent": False, "object_digest": object_digest}


def admit_object(
    db: sqlite3.Connection,
    *,
    object_kind: str,
    object_version: str,
    object_digest: str,
    entity_generation: int,
    admission_receipt_digest: str,
) -> dict[str, Any]:
    """Admit one already-registered object at the exact current entity generation."""
    live_generation = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live_generation, "STALE_GENERATION")
    _need(object_kind in OBJECT_KINDS, "OBJECT_KIND_UNSUPPORTED")
    object_version = _text(object_version, "object_version")
    object_digest = _digest(object_digest, "object_digest")
    admission_receipt_digest = _digest(admission_receipt_digest, "admission_receipt_digest")

    exists = db.execute(
        """SELECT 1 FROM mini_cognition_objects
            WHERE object_kind=? AND object_version=? AND object_digest=?""",
        (object_kind, object_version, object_digest),
    ).fetchone()
    _need(exists is not None, "OBJECT_NOT_REGISTERED")

    existing = db.execute(
        """SELECT admission_receipt_digest FROM mini_cognition_object_admissions
            WHERE object_kind=? AND object_version=? AND object_digest=? AND admitted_generation=?""",
        (object_kind, object_version, object_digest, entity_generation),
    ).fetchone()
    if existing is not None:
        _need(existing[0] == admission_receipt_digest, "ADMISSION_RECEIPT_CONFLICT")
        return {"ok": True, "idempotent": True}

    db.execute(
        """INSERT INTO mini_cognition_object_admissions(
             object_kind,object_version,object_digest,admitted_generation,
             admission_receipt_digest,admitted_at)
           VALUES(?,?,?,?,?,?)""",
        (
            object_kind,
            object_version,
            object_digest,
            entity_generation,
            admission_receipt_digest,
            _utc_now(),
        ),
    )
    return {"ok": True, "idempotent": False}


def _require_admitted_digest(
    db: sqlite3.Connection,
    *,
    object_kind: str,
    object_digest: str,
    entity_generation: int,
) -> None:
    row = db.execute(
        """SELECT o.object_version,MAX(a.admitted_generation)
             FROM mini_cognition_objects o
             JOIN mini_cognition_object_admissions a
               ON a.object_kind=o.object_kind
              AND a.object_version=o.object_version
              AND a.object_digest=o.object_digest
            WHERE o.object_kind=? AND o.object_digest=? AND a.admitted_generation<=?
            GROUP BY o.object_version
            ORDER BY MAX(a.admitted_generation) DESC, o.object_version DESC
            LIMIT 1""",
        (object_kind, object_digest, entity_generation),
    ).fetchone()
    _need(row is not None, f"COGNITION_OBJECT_NOT_ADMITTED:{object_kind}")


def admit_boot_binding(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    zero_identity_digest: str,
    grf_digest: str,
    hyperposition_digest: str,
    bundled_manifest_digest: str,
    local_model_digest: str,
    tokenizer_digest: str,
    jspace_profile_digest: str,
    jacobian_lens_digest: str,
    workspace_calibration_digest: str,
    boot_source_lock_digest: str,
    policy_authority_digest: str,
    provenance_refs: list[str],
) -> dict[str, Any]:
    """Create the sole exact cognition boot binding for the current entity generation."""
    live_generation = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live_generation, "STALE_GENERATION")
    refs = _refs(provenance_refs, "provenance_refs")
    _need(bool(refs), "PROVENANCE_REQUIRED")

    fields: dict[str, str] = {}
    for field_name in BOOT_FIELD_KINDS:
        fields[field_name] = _digest(locals()[field_name], field_name)
        _require_admitted_digest(
            db,
            object_kind=BOOT_FIELD_KINDS[field_name],
            object_digest=fields[field_name],
            entity_generation=entity_generation,
        )

    material = {
        "schema": BOOT_BINDING_SCHEMA,
        "entity_generation": entity_generation,
        **fields,
        "provenance_refs": refs,
    }
    binding_digest = sha256_obj(material)

    existing = db.execute(
        """SELECT binding_digest FROM mini_cognition_boot_bindings
            WHERE entity_generation=?""",
        (entity_generation,),
    ).fetchone()
    if existing is not None:
        _need(existing[0] == binding_digest, "BOOT_BINDING_GENERATION_CONFLICT")
        return {"ok": True, "idempotent": True, "binding_digest": binding_digest}

    db.execute(
        """INSERT INTO mini_cognition_boot_bindings(
             binding_digest,schema,entity_generation,zero_identity_digest,grf_digest,
             hyperposition_digest,bundled_manifest_digest,local_model_digest,tokenizer_digest,
             jspace_profile_digest,jacobian_lens_digest,workspace_calibration_digest,
             boot_source_lock_digest,policy_authority_digest,provenance_refs_json,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            binding_digest,
            BOOT_BINDING_SCHEMA,
            entity_generation,
            fields["zero_identity_digest"],
            fields["grf_digest"],
            fields["hyperposition_digest"],
            fields["bundled_manifest_digest"],
            fields["local_model_digest"],
            fields["tokenizer_digest"],
            fields["jspace_profile_digest"],
            fields["jacobian_lens_digest"],
            fields["workspace_calibration_digest"],
            fields["boot_source_lock_digest"],
            fields["policy_authority_digest"],
            canonical_json(refs),
            _utc_now(),
        ),
    )
    return {"ok": True, "idempotent": False, "binding_digest": binding_digest}


def bind_turn(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    causal_turn_id: str,
    boot_binding_digest: str,
    task_text: str,
    workspace_digest: str,
    selected_workspace_slots: list[str],
    contradiction_state: str,
    provenance_refs: list[str],
    required_zero_mode: str,
) -> dict[str, Any]:
    """Bind one causal turn to the admitted boot identity and exact workspace state."""
    live_generation = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live_generation, "STALE_GENERATION")
    causal_turn_id = _text(causal_turn_id, "causal_turn_id")
    boot_binding_digest = _digest(boot_binding_digest, "boot_binding_digest")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    workspace_digest = _digest(workspace_digest, "workspace_digest")
    slots = _refs(selected_workspace_slots, "selected_workspace_slots")
    refs = _refs(provenance_refs, "provenance_refs")
    _need(bool(refs), "PROVENANCE_REQUIRED")
    contradiction_state = _text(contradiction_state, "contradiction_state")
    required_zero_mode = _text(required_zero_mode, "required_zero_mode")

    boot = db.execute(
        """SELECT entity_generation FROM mini_cognition_boot_bindings
            WHERE binding_digest=?""",
        (boot_binding_digest,),
    ).fetchone()
    _need(boot is not None, "BOOT_BINDING_UNAVAILABLE")
    _need(boot[0] == entity_generation, "BOOT_BINDING_STALE_GENERATION")

    material = {
        "schema": TURN_BINDING_SCHEMA,
        "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "boot_binding_digest": boot_binding_digest,
        "task_sha256": hashlib.sha256(task_text.encode("utf-8")).hexdigest(),
        "workspace_digest": workspace_digest,
        "selected_workspace_slots": slots,
        "contradiction_state": contradiction_state,
        "provenance_refs": refs,
        "required_zero_mode": required_zero_mode,
    }
    binding_digest = sha256_obj(material)

    existing = db.execute(
        """SELECT binding_digest FROM mini_cognition_turn_bindings
            WHERE entity_generation=? AND causal_turn_id=?""",
        (entity_generation, causal_turn_id),
    ).fetchone()
    if existing is not None:
        _need(existing[0] == binding_digest, "TURN_BINDING_CONFLICT")
        return {"ok": True, "idempotent": True, "binding_digest": binding_digest}

    db.execute(
        """INSERT INTO mini_cognition_turn_bindings(
             entity_generation,causal_turn_id,binding_digest,schema,boot_binding_digest,
             task_sha256,workspace_digest,selected_workspace_slots_json,contradiction_state,
             provenance_refs_json,required_zero_mode,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            entity_generation,
            causal_turn_id,
            binding_digest,
            TURN_BINDING_SCHEMA,
            boot_binding_digest,
            material["task_sha256"],
            workspace_digest,
            canonical_json(slots),
            contradiction_state,
            canonical_json(refs),
            required_zero_mode,
            _utc_now(),
        ),
    )
    return {"ok": True, "idempotent": False, "binding_digest": binding_digest}


def resolve_prepare_binding(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    causal_turn_id: str,
    task_text: str,
) -> dict[str, Any]:
    """Resolve exact pre-inference binding material or fail closed."""
    live_generation = _current_generation(db)
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(entity_generation == live_generation, "STALE_GENERATION")
    causal_turn_id = _text(causal_turn_id, "causal_turn_id")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")

    turn = db.execute(
        """SELECT binding_digest,boot_binding_digest,task_sha256,workspace_digest,
                  selected_workspace_slots_json,contradiction_state,provenance_refs_json,
                  required_zero_mode
             FROM mini_cognition_turn_bindings
            WHERE entity_generation=? AND causal_turn_id=?""",
        (entity_generation, causal_turn_id),
    ).fetchone()
    _need(turn is not None, "TURN_BINDING_UNAVAILABLE")
    expected_task = hashlib.sha256(task_text.encode("utf-8")).hexdigest()
    _need(turn[2] == expected_task, "TURN_TASK_BINDING_MISMATCH")

    boot = db.execute(
        """SELECT binding_digest,zero_identity_digest,grf_digest,hyperposition_digest,
                  bundled_manifest_digest,local_model_digest,tokenizer_digest,jspace_profile_digest,
                  jacobian_lens_digest,workspace_calibration_digest,boot_source_lock_digest,
                  policy_authority_digest,provenance_refs_json
             FROM mini_cognition_boot_bindings
            WHERE binding_digest=? AND entity_generation=?""",
        (turn[1], entity_generation),
    ).fetchone()
    _need(boot is not None, "BOOT_BINDING_UNAVAILABLE")

    return {
        "ok": True,
        "schema": SCHEMA,
        "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": turn[0],
        "boot_binding_digest": boot[0],
        "task_sha256": turn[2],
        "workspace_digest": turn[3],
        "selected_workspace_slots": json.loads(turn[4]),
        "contradiction_state": turn[5],
        "turn_provenance_refs": json.loads(turn[6]),
        "required_zero_mode": turn[7],
        "zero_identity_digest": boot[1],
        "grf_digest": boot[2],
        "hyperposition_digest": boot[3],
        "bundled_manifest_digest": boot[4],
        "local_model_digest": boot[5],
        "tokenizer_digest": boot[6],
        "jspace_profile_digest": boot[7],
        "jacobian_lens_digest": boot[8],
        "workspace_calibration_digest": boot[9],
        "boot_source_lock_digest": boot[10],
        "policy_authority_digest": boot[11],
        "boot_provenance_refs": json.loads(boot[12]),
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
    }
