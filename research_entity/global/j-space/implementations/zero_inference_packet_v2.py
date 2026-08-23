#!/usr/bin/env python3
"""Deterministic ZERO InferencePacket v2 with exact downstream-context binding.

This packet is an admission envelope only. It grants no truth, state, effect,
model-runtime, J-Space, GWT, or product credit.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

import zero_workspace_capsule_v1 as capsule_v1

SCHEMA = "ZERO_INFERENCE_PACKET/v2"
COMPILER_VERSION = "zero-inference-packet/2.0"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TARGETS = {"CLAUDE_CODE", "BUNDLED_LOCAL_08B", "ADAPTIVE_BACKEND", "NO_MODEL_REQUIRED"}
JSPACE_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY", "COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}
ENGINE_TO_UCF = {
    "CLAUDE_CODE": "claude_code",
    "BUNDLED_LOCAL_08B": "local_08b",
    "ADAPTIVE_BACKEND": "adaptive_backend",
}
PACKET_KEYS = {
    "schema", "compiler_version", "packet_id", "entity_generation", "causal_turn_id",
    "workspace_capsule_digest", "task_sha256", "zero_identity_digest", "grf_digest",
    "workspace_digest", "capsule_mode", "required_zero_mode", "target_engine_class",
    "jspace_mode", "inference_config_digest", "system_context_digest",
    "user_context_digest", "admitted_context_digest", "authority", "packet_digest",
}
_MISSING = object()


class PacketError(ValueError):
    pass


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise PacketError(msg)


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PacketError("NONCANONICAL_JSON_CONTEXT") from exc


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def sha256_text(value: str) -> str:
    _need(type(value) is str, "CONTEXT_TEXT_REQUIRED")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def context_digests(
    inference: Mapping[str, Any],
    system: str,
    user: str,
) -> dict[str, str]:
    _need(isinstance(inference, Mapping), "INFERENCE_CONFIG_OBJECT_REQUIRED")
    config_digest = sha256_obj(dict(inference))
    system_digest = sha256_text(system)
    user_digest = sha256_text(user)
    admitted_digest = sha256_obj(
        {
            "inference_config_digest": config_digest,
            "system_context_digest": system_digest,
            "user_context_digest": user_digest,
        }
    )
    return {
        "inference_config_digest": config_digest,
        "system_context_digest": system_digest,
        "user_context_digest": user_digest,
        "admitted_context_digest": admitted_digest,
    }


def _identity_binding(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "entity_generation": packet.get("entity_generation"),
        "causal_turn_id": packet.get("causal_turn_id"),
        "workspace_capsule_digest": packet.get("workspace_capsule_digest"),
        "task_sha256": packet.get("task_sha256"),
        "zero_identity_digest": packet.get("zero_identity_digest"),
        "grf_digest": packet.get("grf_digest"),
        "workspace_digest": packet.get("workspace_digest"),
        "capsule_mode": packet.get("capsule_mode"),
        "required_zero_mode": packet.get("required_zero_mode"),
        "target_engine_class": packet.get("target_engine_class"),
        "jspace_mode": packet.get("jspace_mode"),
        "inference_config_digest": packet.get("inference_config_digest"),
        "system_context_digest": packet.get("system_context_digest"),
        "user_context_digest": packet.get("user_context_digest"),
        "admitted_context_digest": packet.get("admitted_context_digest"),
    }


def compile_packet(
    capsule: dict[str, Any],
    *,
    target_engine_class: str,
    jspace_mode: str,
    inference: Mapping[str, Any] | None,
    system: str | None,
    user: str | None,
) -> dict[str, Any]:
    capsule_v1.validate(capsule)
    _need(target_engine_class in TARGETS, "TARGET_ENGINE_UNSUPPORTED")
    _need(jspace_mode in JSPACE_MODES, "JSPACE_MODE_UNSUPPORTED")
    mode = capsule["mode"]

    if mode == "ABSTAINED":
        _need(target_engine_class == "NO_MODEL_REQUIRED", "ABSTENTION_REQUIRES_NO_MODEL")
        _need(jspace_mode == "PLAIN_COMPATIBILITY", "ABSTENTION_JSPACE_MODE_INVALID")
        _need(inference is None and system is None and user is None, "ABSTENTION_CONTEXT_FORBIDDEN")
        context = {
            "inference_config_digest": None,
            "system_context_digest": None,
            "user_context_digest": None,
            "admitted_context_digest": None,
        }
    else:
        _need(target_engine_class != "NO_MODEL_REQUIRED", "WORKSPACE_BOUND_REQUIRES_ENGINE")
        _need(inference is not None and system is not None and user is not None, "WORKSPACE_BOUND_CONTEXT_REQUIRED")
        if target_engine_class == "CLAUDE_CODE":
            _need(jspace_mode == "COMPILED_EXTERNAL", "CLAUDE_MUST_BE_COMPILED_EXTERNAL")
        if target_engine_class == "BUNDLED_LOCAL_08B":
            _need(
                jspace_mode in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"},
                "LOCAL_08B_JSPACE_MODE_INVALID",
            )
        context = context_digests(inference, system, user)

    doc = {
        "schema": SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "packet_id": "",
        "entity_generation": capsule["entity_generation"],
        "causal_turn_id": capsule["causal_turn_id"],
        "workspace_capsule_digest": capsule["capsule_digest"],
        "task_sha256": capsule["task"]["sha256"],
        "zero_identity_digest": capsule.get("zero_identity_digest"),
        "grf_digest": capsule.get("grf_digest"),
        "workspace_digest": capsule.get("workspace_digest"),
        "capsule_mode": mode,
        "required_zero_mode": capsule["required_zero_mode"],
        "target_engine_class": target_engine_class,
        "jspace_mode": jspace_mode,
        **context,
        "authority": {
            "structural_authority": "NONE",
            "candidate_only": True,
            "direct_state_authority": False,
            "direct_effect_authority": False,
        },
    }
    doc["packet_id"] = hashlib.sha256(
        b"ZERO_PACKET_ID/v2\0" + canonical_json(_identity_binding(doc))
    ).hexdigest()
    doc["packet_digest"] = sha256_obj(doc)
    validate(
        doc,
        capsule,
        inference=inference,
        system=system,
        user=user,
        require_context=True,
    )
    return doc


def validate(
    packet: dict[str, Any],
    capsule: dict[str, Any] | None = None,
    *,
    inference: Any = _MISSING,
    system: Any = _MISSING,
    user: Any = _MISSING,
    require_context: bool = False,
) -> dict[str, Any]:
    _need(type(packet) is dict, "PACKET_OBJECT_REQUIRED")
    _need(set(packet) == PACKET_KEYS, "PACKET_FIELDS_MISMATCH")
    _need(packet.get("schema") == SCHEMA, "SCHEMA_MISMATCH")
    _need(packet.get("compiler_version") == COMPILER_VERSION, "COMPILER_VERSION_MISMATCH")
    _digest(packet.get("packet_id"), "packet_id")

    generation = packet.get("entity_generation")
    _need(type(generation) is int and generation >= 0, "GENERATION_INVALID")
    _need(
        type(packet.get("causal_turn_id")) is str and bool(packet["causal_turn_id"].strip()),
        "CAUSAL_TURN_ID_REQUIRED",
    )
    _digest(packet.get("workspace_capsule_digest"), "workspace_capsule_digest")
    _digest(packet.get("task_sha256"), "task_sha256")

    mode = packet.get("capsule_mode")
    _need(mode in {"WORKSPACE_BOUND", "ABSTAINED"}, "CAPSULE_MODE_INVALID")
    target = packet.get("target_engine_class")
    jspace_mode = packet.get("jspace_mode")
    _need(target in TARGETS, "TARGET_ENGINE_UNSUPPORTED")
    _need(jspace_mode in JSPACE_MODES, "JSPACE_MODE_UNSUPPORTED")
    required_zero_mode = packet.get("required_zero_mode")
    _need(
        type(required_zero_mode) is str and bool(required_zero_mode.strip()),
        "REQUIRED_ZERO_MODE_REQUIRED",
    )
    _need(
        packet.get("authority")
        == {
            "structural_authority": "NONE",
            "candidate_only": True,
            "direct_state_authority": False,
            "direct_effect_authority": False,
        },
        "AUTHORITY_CONTRACT_MISMATCH",
    )

    if mode == "WORKSPACE_BOUND":
        _digest(packet.get("zero_identity_digest"), "zero_identity_digest")
        _digest(packet.get("grf_digest"), "grf_digest")
        _digest(packet.get("workspace_digest"), "workspace_digest")
        _need(target != "NO_MODEL_REQUIRED", "WORKSPACE_BOUND_REQUIRES_ENGINE")
        if target == "CLAUDE_CODE":
            _need(jspace_mode == "COMPILED_EXTERNAL", "CLAUDE_MUST_BE_COMPILED_EXTERNAL")
        if target == "BUNDLED_LOCAL_08B":
            _need(
                jspace_mode in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"},
                "LOCAL_08B_JSPACE_MODE_INVALID",
            )
        for name in (
            "inference_config_digest",
            "system_context_digest",
            "user_context_digest",
            "admitted_context_digest",
        ):
            _digest(packet.get(name), name)
    else:
        _need(target == "NO_MODEL_REQUIRED", "ABSTENTION_REQUIRES_NO_MODEL")
        _need(jspace_mode == "PLAIN_COMPATIBILITY", "ABSTENTION_JSPACE_MODE_INVALID")
        _need(required_zero_mode == "ABSTAIN", "ABSTENTION_ZERO_MODE_INVALID")
        _need(packet.get("workspace_digest") is None, "ABSTENTION_WORKSPACE_DIGEST_MUST_BE_NULL")
        for name in ("inference_config_digest", "system_context_digest", "user_context_digest", "admitted_context_digest"):
            _need(packet.get(name) is None, f"ABSTENTION_{name.upper()}_MUST_BE_NULL")
        for name in ("zero_identity_digest", "grf_digest"):
            value = packet.get(name)
            if value is not None:
                _digest(value, name)

    expected_packet_id = hashlib.sha256(
        b"ZERO_PACKET_ID/v2\0" + canonical_json(_identity_binding(packet))
    ).hexdigest()
    _need(packet.get("packet_id") == expected_packet_id, "PACKET_ID_BINDING_MISMATCH")

    unsigned = dict(packet)
    observed = unsigned.pop("packet_digest", None)
    _digest(observed, "packet_digest")
    _need(observed == sha256_obj(unsigned), "PACKET_DIGEST_MISMATCH")

    if capsule is not None:
        capsule_v1.validate(capsule)
        pairs = (
            ("entity_generation", "entity_generation"),
            ("causal_turn_id", "causal_turn_id"),
            ("workspace_capsule_digest", "capsule_digest"),
            ("zero_identity_digest", "zero_identity_digest"),
            ("grf_digest", "grf_digest"),
            ("workspace_digest", "workspace_digest"),
            ("capsule_mode", "mode"),
            ("required_zero_mode", "required_zero_mode"),
        )
        for pkey, ckey in pairs:
            _need(packet.get(pkey) == capsule.get(ckey), f"CAPSULE_BINDING_MISMATCH:{pkey}")
        _need(
            packet.get("task_sha256") == capsule["task"]["sha256"],
            "CAPSULE_BINDING_MISMATCH:task_sha256",
        )

    supplied = (inference is not _MISSING, system is not _MISSING, user is not _MISSING)
    _need(not any(supplied) or all(supplied), "DOWNSTREAM_CONTEXT_ALL_OR_NONE")
    if require_context:
        _need(all(supplied), "DOWNSTREAM_CONTEXT_REQUIRED")

    if all(supplied):
        if mode == "ABSTAINED":
            _need(inference is None and system is None and user is None, "ABSTENTION_CONTEXT_FORBIDDEN")
        else:
            _need(inference is not None and system is not None and user is not None, "WORKSPACE_BOUND_CONTEXT_REQUIRED")
            expected = context_digests(inference, system, user)
            checks = {
                "inference_config_digest": "DOWNSTREAM_INFERENCE_CONFIG_DIGEST_MISMATCH",
                "system_context_digest": "DOWNSTREAM_SYSTEM_CONTEXT_DIGEST_MISMATCH",
                "user_context_digest": "DOWNSTREAM_USER_CONTEXT_DIGEST_MISMATCH",
                "admitted_context_digest": "DOWNSTREAM_ADMITTED_CONTEXT_DIGEST_MISMATCH",
            }
            for key, error in checks.items():
                _need(packet.get(key) == expected[key], error)

    return {
        "ok": True,
        "schema": SCHEMA,
        "packet_digest": observed,
        "admitted_context_digest": packet.get("admitted_context_digest"),
        "runtime_credit": "ZERO",
        "truth_credit": "ZERO",
        "effect_credit": "ZERO",
    }
