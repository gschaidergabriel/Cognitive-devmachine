#!/usr/bin/env python3
"""Thin read-only binding from ProfilePipelineRuntime payloads to the one canonical UCF compositor.

This module intentionally owns no cognition semantics. It verifies that the profile carried
by the Clay phase is the exact active MiniUnifiedDB profile plus the runtime-owned snapshot
metadata emitted by ``_pipeline_profile_read``, opens the canonical database read-only, and
delegates pre-inference admission to tools/pipeline_cognitive_fabric_admission_v1.py.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

import pipeline_cognitive_fabric_admission_v1 as canonical_admission

BINDING_VERSION = "profile-runtime-cognitive-fabric-binding/v1"
_RUNTIME_PROFILE_SNAPSHOT = "_runtime_profile_snapshot"


class ProfileRuntimeCognitiveFabricBindingError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ProfileRuntimeCognitiveFabricBindingError(message)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ProfileRuntimeCognitiveFabricBindingError("NONCANONICAL_JSON") from exc


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _split_runtime_profile(profile: Mapping[str, Any]) -> tuple[dict[str, Any], Mapping[str, Any]]:
    """Separate persisted profile bytes from runtime-owned snapshot metadata.

    ``ProfilePipelineRuntime._pipeline_profile_read`` adds exactly one ephemeral field after
    validating the stored profile hash. Treating that field as persisted profile data would
    make the real Clay path reject every legitimate loaded profile, while accepting profiles
    without the snapshot would remove the intended read->admit continuity fence.
    """
    carried = dict(profile)
    snapshot = carried.pop(_RUNTIME_PROFILE_SNAPSHOT, None)
    _need(isinstance(snapshot, Mapping), "RUNTIME_PROFILE_SNAPSHOT_REQUIRED")
    _need(
        set(snapshot) == {"profile_id", "profile_hash"},
        "RUNTIME_PROFILE_SNAPSHOT_FIELDS_MISMATCH",
    )
    return carried, snapshot


def admit_profile_runtime_payload(
    runtime: Any,
    payload: Mapping[str, Any],
    *,
    compositor_module: Any | None = None,
) -> dict[str, Any]:
    """Validate one runtime phase payload and delegate to the canonical admission compositor.

    The MiniUnifiedDB handle is opened through ``runtime._read_only_db`` so this pre-inference
    bridge cannot itself mutate canonical state. The active profile is re-read from the same
    database. The carried profile body must equal the stored profile exactly, and its ephemeral
    runtime snapshot must bind the same active profile id + persisted-byte hash.
    """
    _need(isinstance(payload, Mapping), "PAYLOAD_OBJECT_REQUIRED")
    entity_db = payload.get("entity_db")
    profile = payload.get("profile")
    data = payload.get("data")
    _need(type(entity_db) is str and bool(entity_db.strip()), "ENTITY_DB_REQUIRED")
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")
    _need(isinstance(data, Mapping), "DATA_OBJECT_REQUIRED")

    compiled = data.get("compiled")
    prompt = data.get("prompt")
    invocation = data.get("invocation")
    _need(isinstance(compiled, Mapping), "COMPILED_OBJECT_REQUIRED")
    _need(isinstance(prompt, Mapping), "PROMPT_OBJECT_REQUIRED")
    _need(isinstance(invocation, Mapping), "INVOCATION_OBJECT_REQUIRED")
    carried_profile, runtime_snapshot = _split_runtime_profile(profile)

    db = runtime._read_only_db(entity_db)
    try:
        state = db.execute(
            "SELECT generation,active_profile FROM entity_state WHERE id=1"
        ).fetchone()
        _need(state is not None, "ENTITY_STATE_MISSING")
        generation = int(state["generation"])
        active_profile = state["active_profile"]
        _need(type(active_profile) is str and bool(active_profile), "ACTIVE_PROFILE_MISSING")

        row = db.execute(
            "SELECT profile_json,profile_sha256 FROM profiles WHERE profile_id=?",
            (active_profile,),
        ).fetchone()
        _need(row is not None, "ACTIVE_PROFILE_ROW_MISSING")
        profile_json = str(row["profile_json"])
        profile_sha256 = str(row["profile_sha256"])
        _need(_sha256_text(profile_json) == profile_sha256, "ACTIVE_PROFILE_HASH_MISMATCH")
        _need(
            runtime_snapshot.get("profile_id") == active_profile,
            "RUNTIME_PROFILE_SNAPSHOT_ID_MISMATCH",
        )
        _need(
            runtime_snapshot.get("profile_hash") == profile_sha256,
            "RUNTIME_PROFILE_SNAPSHOT_HASH_MISMATCH",
        )

        try:
            stored_profile = json.loads(profile_json)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ProfileRuntimeCognitiveFabricBindingError("ACTIVE_PROFILE_JSON_INVALID") from exc
        _need(isinstance(stored_profile, dict), "ACTIVE_PROFILE_OBJECT_REQUIRED")
        _need(
            _canonical_json(carried_profile) == _canonical_json(stored_profile),
            "RUNTIME_PROFILE_NOT_ACTIVE_MINIUNIFIEDDB_PROFILE",
        )

        compositor = compositor_module or canonical_admission
        result = compositor.build_pre_inference_admission(
            db,
            entity_generation=generation,
            invocation=invocation,
            compiled=compiled,
            prompt=prompt,
            profile=stored_profile,
            origin=BINDING_VERSION,
        )
        _need(type(result) is dict and result.get("ok") is True, "CANONICAL_ADMISSION_FAILED")
        _need(result.get("generation") == generation, "ADMISSION_GENERATION_DRIFT")
        return result
    finally:
        db.close()


__all__ = [
    "BINDING_VERSION",
    "ProfileRuntimeCognitiveFabricBindingError",
    "admit_profile_runtime_payload",
]