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
import re
from collections.abc import Mapping
from typing import Any

import pipeline_cognitive_fabric_admission_v1 as canonical_admission

BINDING_VERSION = "profile-runtime-cognitive-fabric-binding/v1"
ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
_RUNTIME_PROFILE_SNAPSHOT = "_runtime_profile_snapshot"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


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


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _split_runtime_profile(profile: Mapping[str, Any]) -> tuple[dict[str, Any], Mapping[str, Any]]:
    """Separate persisted profile bytes from runtime-owned snapshot metadata."""
    carried = dict(profile)
    snapshot = carried.pop(_RUNTIME_PROFILE_SNAPSHOT, None)
    _need(isinstance(snapshot, Mapping), "RUNTIME_PROFILE_SNAPSHOT_REQUIRED")
    _need(
        set(snapshot) == {"profile_id", "profile_hash"},
        "RUNTIME_PROFILE_SNAPSHOT_FIELDS_MISMATCH",
    )
    return carried, snapshot


def _validate_admission_result(
    result: Any,
    *,
    generation: int,
    canonical_state_hash: str,
    packet_hash: str,
) -> dict[str, Any]:
    _need(type(result) is dict and result.get("ok") is True, "CANONICAL_ADMISSION_FAILED")
    _need(result.get("schema") == ADMISSION_SCHEMA, "ADMISSION_SCHEMA_MISMATCH")
    _need(result.get("generation") == generation, "ADMISSION_GENERATION_DRIFT")
    _need(result.get("canonical_state_hash") == canonical_state_hash, "ADMISSION_CANONICAL_STATE_DRIFT")
    _need(result.get("packet_hash") == packet_hash, "ADMISSION_PACKET_DRIFT")
    _digest(result.get("inference_packet_digest"), "inference_packet_digest")
    _digest(result.get("cognitive_fabric_receipt_digest"), "cognitive_fabric_receipt_digest")
    _need(isinstance(result.get("inference"), Mapping), "ADMITTED_INFERENCE_OBJECT_REQUIRED")
    _need(type(result.get("system")) is str, "ADMITTED_SYSTEM_TEXT_REQUIRED")
    _need(type(result.get("user")) is str, "ADMITTED_USER_TEXT_REQUIRED")

    receipt = result.get("admission_receipt")
    _need(isinstance(receipt, Mapping), "ADMISSION_RECEIPT_OBJECT_REQUIRED")
    _need(receipt.get("authority") == "CANDIDATE_INFERENCE_ONLY", "ADMISSION_AUTHORITY_ESCALATION")
    _need(receipt.get("real_effect_executed") is False, "PREINFERENCE_EFFECT_EXECUTION_FORBIDDEN")
    _need(
        "ucf_runtime_receipt_digest" not in result
        and "ucf_runtime_receipt_digest" not in receipt,
        "PREINFERENCE_FINAL_UCF_RECEIPT_FORBIDDEN",
    )
    return result


def admit_profile_runtime_payload(
    runtime: Any,
    payload: Mapping[str, Any],
    *,
    compositor_module: Any | None = None,
) -> dict[str, Any]:
    """Validate one runtime phase payload and delegate to the canonical admission compositor."""
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
    canonical_state_hash = _digest(compiled.get("canonical_state_hash"), "canonical_state_hash")
    packet_hash = _digest(compiled.get("packet_hash"), "packet_hash")
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

        # The canonical capability router deliberately requires the verified runtime snapshot.
        # Reattach only the values just revalidated against MiniUnifiedDB; never trust a caller
        # to supply additional capability/J-Space authority through ephemeral profile metadata.
        delegated_profile = dict(stored_profile)
        delegated_profile[_RUNTIME_PROFILE_SNAPSHOT] = {
            "profile_id": active_profile,
            "profile_hash": profile_sha256,
        }

        compositor = compositor_module or canonical_admission
        result = compositor.build_pre_inference_admission(
            db,
            entity_generation=generation,
            invocation=invocation,
            compiled=compiled,
            prompt=prompt,
            profile=delegated_profile,
            origin=BINDING_VERSION,
        )
        return _validate_admission_result(
            result,
            generation=generation,
            canonical_state_hash=canonical_state_hash,
            packet_hash=packet_hash,
        )
    finally:
        db.close()


__all__ = [
    "ADMISSION_SCHEMA",
    "BINDING_VERSION",
    "ProfileRuntimeCognitiveFabricBindingError",
    "admit_profile_runtime_payload",
]
