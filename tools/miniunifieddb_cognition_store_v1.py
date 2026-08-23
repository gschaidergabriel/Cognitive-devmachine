#!/usr/bin/env python3
"""Read-integrity hardened facade for the canonical MiniUnifiedDB cognition store.

The landed v1 implementation is retained byte-for-byte in
miniunifieddb_cognition_store_v1_base.py.  This module re-exports that API and replaces
only resolve_prepare_binding with fail-closed digest reconstruction on every read.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

import miniunifieddb_cognition_store_v1_base as _base
from miniunifieddb_cognition_store_v1_base import *


def _json_list(raw: Any, name: str) -> list[str]:
    if type(raw) is not str:
        raise CognitionStoreError(f"{name}:JSON_TEXT_REQUIRED")
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise CognitionStoreError(f"{name}:MALFORMED_JSON") from exc
    return _base._refs(value, name)


def _validate_boot_row(db: sqlite3.Connection, row: sqlite3.Row | tuple[Any, ...], generation: int) -> dict[str, Any]:
    (
        binding_digest,
        schema,
        entity_generation,
        zero_identity_digest,
        grf_digest,
        hyperposition_digest,
        bundled_manifest_digest,
        local_model_digest,
        tokenizer_digest,
        jspace_profile_digest,
        jacobian_lens_digest,
        workspace_calibration_digest,
        boot_source_lock_digest,
        policy_authority_digest,
        provenance_refs_json,
    ) = tuple(row)
    _base._need(schema == BOOT_BINDING_SCHEMA, "BOOT_BINDING_SCHEMA_MISMATCH")
    _base._need(type(entity_generation) is int and entity_generation == generation, "BOOT_BINDING_STALE_GENERATION")
    refs = _json_list(provenance_refs_json, "boot_provenance_refs")
    _base._need(bool(refs), "PROVENANCE_REQUIRED")
    fields = {
        "zero_identity_digest": _base._digest(zero_identity_digest, "zero_identity_digest"),
        "grf_digest": _base._digest(grf_digest, "grf_digest"),
        "hyperposition_digest": _base._digest(hyperposition_digest, "hyperposition_digest"),
        "bundled_manifest_digest": _base._digest(bundled_manifest_digest, "bundled_manifest_digest"),
        "local_model_digest": _base._digest(local_model_digest, "local_model_digest"),
        "tokenizer_digest": _base._digest(tokenizer_digest, "tokenizer_digest"),
        "jspace_profile_digest": _base._digest(jspace_profile_digest, "jspace_profile_digest"),
        "jacobian_lens_digest": _base._digest(jacobian_lens_digest, "jacobian_lens_digest"),
        "workspace_calibration_digest": _base._digest(workspace_calibration_digest, "workspace_calibration_digest"),
        "boot_source_lock_digest": _base._digest(boot_source_lock_digest, "boot_source_lock_digest"),
        "policy_authority_digest": _base._digest(policy_authority_digest, "policy_authority_digest"),
    }
    material = {
        "schema": BOOT_BINDING_SCHEMA,
        "entity_generation": generation,
        **fields,
        "provenance_refs": refs,
    }
    expected = _base.sha256_obj(material)
    _base._need(binding_digest == expected, "BOOT_BINDING_DIGEST_MISMATCH")
    for field_name, object_kind in BOOT_FIELD_KINDS.items():
        _base._require_admitted_digest(
            db,
            object_kind=object_kind,
            object_digest=fields[field_name],
            entity_generation=generation,
        )
    return {
        "binding_digest": binding_digest,
        **fields,
        "provenance_refs": refs,
    }


def resolve_prepare_binding(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    causal_turn_id: str,
    task_text: str,
) -> dict[str, Any]:
    """Resolve exact current-generation prepare material and revalidate stored digests."""
    live_generation = _base._current_generation(db)
    _base._need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _base._need(entity_generation == live_generation, "STALE_GENERATION")
    causal_turn_id = _base._text(causal_turn_id, "causal_turn_id")
    _base._need(type(task_text) is str, "TASK_TEXT_REQUIRED")

    turn = db.execute(
        """SELECT binding_digest,schema,boot_binding_digest,task_sha256,workspace_digest,
                  selected_workspace_slots_json,contradiction_state,provenance_refs_json,
                  required_zero_mode
             FROM mini_cognition_turn_bindings
            WHERE entity_generation=? AND causal_turn_id=?""",
        (entity_generation, causal_turn_id),
    ).fetchone()
    _base._need(turn is not None, "TURN_BINDING_UNAVAILABLE")
    (
        turn_digest,
        turn_schema,
        boot_binding_digest,
        task_sha256,
        workspace_digest,
        slots_json,
        contradiction_state,
        turn_refs_json,
        required_zero_mode,
    ) = tuple(turn)
    _base._need(turn_schema == TURN_BINDING_SCHEMA, "TURN_BINDING_SCHEMA_MISMATCH")
    boot_binding_digest = _base._digest(boot_binding_digest, "boot_binding_digest")
    task_sha256 = _base._digest(task_sha256, "task_sha256")
    workspace_digest = _base._digest(workspace_digest, "workspace_digest")
    slots = _json_list(slots_json, "selected_workspace_slots")
    turn_refs = _json_list(turn_refs_json, "turn_provenance_refs")
    _base._need(bool(turn_refs), "PROVENANCE_REQUIRED")
    contradiction_state = _base._text(contradiction_state, "contradiction_state")
    required_zero_mode = _base._text(required_zero_mode, "required_zero_mode")

    expected_task = hashlib.sha256(task_text.encode("utf-8")).hexdigest()
    _base._need(task_sha256 == expected_task, "TURN_TASK_BINDING_MISMATCH")
    turn_material = {
        "schema": TURN_BINDING_SCHEMA,
        "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "boot_binding_digest": boot_binding_digest,
        "task_sha256": task_sha256,
        "workspace_digest": workspace_digest,
        "selected_workspace_slots": slots,
        "contradiction_state": contradiction_state,
        "provenance_refs": turn_refs,
        "required_zero_mode": required_zero_mode,
    }
    _base._need(turn_digest == _base.sha256_obj(turn_material), "TURN_BINDING_DIGEST_MISMATCH")

    boot = db.execute(
        """SELECT binding_digest,schema,entity_generation,zero_identity_digest,grf_digest,
                  hyperposition_digest,bundled_manifest_digest,local_model_digest,tokenizer_digest,
                  jspace_profile_digest,jacobian_lens_digest,workspace_calibration_digest,
                  boot_source_lock_digest,policy_authority_digest,provenance_refs_json
             FROM mini_cognition_boot_bindings
            WHERE binding_digest=? AND entity_generation=?""",
        (boot_binding_digest, entity_generation),
    ).fetchone()
    _base._need(boot is not None, "BOOT_BINDING_UNAVAILABLE")
    boot_fields = _validate_boot_row(db, boot, entity_generation)

    return {
        "ok": True,
        "schema": SCHEMA,
        "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": turn_digest,
        "boot_binding_digest": boot_fields["binding_digest"],
        "task_sha256": task_sha256,
        "workspace_digest": workspace_digest,
        "selected_workspace_slots": slots,
        "contradiction_state": contradiction_state,
        "turn_provenance_refs": turn_refs,
        "required_zero_mode": required_zero_mode,
        "zero_identity_digest": boot_fields["zero_identity_digest"],
        "grf_digest": boot_fields["grf_digest"],
        "hyperposition_digest": boot_fields["hyperposition_digest"],
        "bundled_manifest_digest": boot_fields["bundled_manifest_digest"],
        "local_model_digest": boot_fields["local_model_digest"],
        "tokenizer_digest": boot_fields["tokenizer_digest"],
        "jspace_profile_digest": boot_fields["jspace_profile_digest"],
        "jacobian_lens_digest": boot_fields["jacobian_lens_digest"],
        "workspace_calibration_digest": boot_fields["workspace_calibration_digest"],
        "boot_source_lock_digest": boot_fields["boot_source_lock_digest"],
        "policy_authority_digest": boot_fields["policy_authority_digest"],
        "boot_provenance_refs": boot_fields["provenance_refs"],
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
    }


__all__ = list(getattr(_base, "__all__", []))
if "resolve_prepare_binding" not in __all__:
    __all__.append("resolve_prepare_binding")
