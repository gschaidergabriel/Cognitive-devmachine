#!/usr/bin/env python3
"""Deterministic InferencePacket binding for a ZERO_WORKSPACE_CAPSULE/v1.

This is an admission envelope only. It grants no truth, state, effect, model-runtime,
J-Space, GWT, or product credit.
"""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any
import zero_workspace_capsule_v1 as capsule_v1

SCHEMA = "ZERO_INFERENCE_PACKET/v1"
COMPILER_VERSION = "zero-inference-packet/1.0"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TARGETS = {"CLAUDE_CODE", "BUNDLED_LOCAL_08B", "ADAPTIVE_BACKEND", "NO_MODEL_REQUIRED"}
JSPACE_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY", "COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}
ENGINE_TO_UCF = {"CLAUDE_CODE":"claude_code", "BUNDLED_LOCAL_08B":"local_08b", "ADAPTIVE_BACKEND":"adaptive_backend"}

class PacketError(ValueError): pass

def _need(cond: bool, msg: str) -> None:
    if not cond: raise PacketError(msg)

def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(len(set(value)) > 1, f"{name}:PLACEHOLDER_REJECTED")
    return value

def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
def sha256_obj(value: Any) -> str: return hashlib.sha256(canonical_json(value)).hexdigest()

def compile_packet(capsule: dict[str, Any], *, target_engine_class: str, jspace_mode: str) -> dict[str, Any]:
    capsule_v1.validate(capsule)
    _need(target_engine_class in TARGETS, "TARGET_ENGINE_UNSUPPORTED")
    _need(jspace_mode in JSPACE_MODES, "JSPACE_MODE_UNSUPPORTED")
    mode = capsule["mode"]
    if mode == "ABSTAINED":
        _need(target_engine_class == "NO_MODEL_REQUIRED", "ABSTENTION_REQUIRES_NO_MODEL")
        _need(jspace_mode == "PLAIN_COMPATIBILITY", "ABSTENTION_JSPACE_MODE_INVALID")
    else:
        _need(target_engine_class != "NO_MODEL_REQUIRED", "WORKSPACE_BOUND_REQUIRES_ENGINE")
        if target_engine_class == "CLAUDE_CODE": _need(jspace_mode == "COMPILED_EXTERNAL", "CLAUDE_MUST_BE_COMPILED_EXTERNAL")
        if target_engine_class == "BUNDLED_LOCAL_08B": _need(jspace_mode in {"FULL_LOCAL_LATENT","LOCAL_OBSERVE_ONLY"}, "LOCAL_08B_JSPACE_MODE_INVALID")
    binding = {
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
    }
    packet_id = hashlib.sha256(b"ZERO_PACKET_ID/v1\0" + canonical_json(binding)).hexdigest()
    doc = {
        "schema": SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "packet_id": packet_id,
        **binding,
        "authority": {
            "structural_authority": "NONE",
            "candidate_only": True,
            "direct_state_authority": False,
            "direct_effect_authority": False,
        },
    }
    doc["packet_digest"] = sha256_obj(doc)
    validate(doc, capsule)
    return doc

def validate(packet: dict[str, Any], capsule: dict[str, Any] | None = None) -> dict[str, Any]:
    _need(type(packet) is dict, "PACKET_OBJECT_REQUIRED")
    _need(packet.get("schema") == SCHEMA, "SCHEMA_MISMATCH")
    _need(packet.get("compiler_version") == COMPILER_VERSION, "COMPILER_VERSION_MISMATCH")
    _digest(packet.get("packet_id"), "packet_id")
    generation = packet.get("entity_generation")
    _need(type(generation) is int and generation >= 0, "GENERATION_INVALID")
    _need(type(packet.get("causal_turn_id")) is str and bool(packet["causal_turn_id"].strip()), "CAUSAL_TURN_ID_REQUIRED")
    _digest(packet.get("workspace_capsule_digest"), "workspace_capsule_digest")
    _digest(packet.get("task_sha256"), "task_sha256")
    mode = packet.get("capsule_mode")
    _need(mode in {"WORKSPACE_BOUND", "ABSTAINED"}, "CAPSULE_MODE_INVALID")
    target = packet.get("target_engine_class"); jspace_mode = packet.get("jspace_mode")
    _need(target in TARGETS, "TARGET_ENGINE_UNSUPPORTED"); _need(jspace_mode in JSPACE_MODES, "JSPACE_MODE_UNSUPPORTED")
    required_zero_mode = packet.get("required_zero_mode")
    _need(type(required_zero_mode) is str and bool(required_zero_mode.strip()), "REQUIRED_ZERO_MODE_REQUIRED")
    authority = packet.get("authority")
    _need(authority == {"structural_authority":"NONE","candidate_only":True,"direct_state_authority":False,"direct_effect_authority":False}, "AUTHORITY_CONTRACT_MISMATCH")
    if mode == "WORKSPACE_BOUND":
        _digest(packet.get("zero_identity_digest"), "zero_identity_digest"); _digest(packet.get("grf_digest"), "grf_digest"); _digest(packet.get("workspace_digest"), "workspace_digest")
        _need(target != "NO_MODEL_REQUIRED", "WORKSPACE_BOUND_REQUIRES_ENGINE")
        if target == "CLAUDE_CODE": _need(jspace_mode == "COMPILED_EXTERNAL", "CLAUDE_MUST_BE_COMPILED_EXTERNAL")
        if target == "BUNDLED_LOCAL_08B": _need(jspace_mode in {"FULL_LOCAL_LATENT","LOCAL_OBSERVE_ONLY"}, "LOCAL_08B_JSPACE_MODE_INVALID")
    else:
        _need(target == "NO_MODEL_REQUIRED", "ABSTENTION_REQUIRES_NO_MODEL"); _need(jspace_mode == "PLAIN_COMPATIBILITY", "ABSTENTION_JSPACE_MODE_INVALID")
        _need(required_zero_mode == "ABSTAIN", "ABSTENTION_ZERO_MODE_INVALID")
        _need(packet.get("workspace_digest") is None, "ABSTENTION_WORKSPACE_DIGEST_MUST_BE_NULL")
        for name in ("zero_identity_digest", "grf_digest"):
            value = packet.get(name)
            if value is not None:
                _digest(value, name)
    identity_binding = {
        "entity_generation": generation,
        "causal_turn_id": packet.get("causal_turn_id"),
        "workspace_capsule_digest": packet.get("workspace_capsule_digest"),
        "task_sha256": packet.get("task_sha256"),
        "zero_identity_digest": packet.get("zero_identity_digest"),
        "grf_digest": packet.get("grf_digest"),
        "workspace_digest": packet.get("workspace_digest"),
        "capsule_mode": mode,
        "required_zero_mode": required_zero_mode,
        "target_engine_class": target,
        "jspace_mode": jspace_mode,
    }
    expected_packet_id = hashlib.sha256(b"ZERO_PACKET_ID/v1\0" + canonical_json(identity_binding)).hexdigest()
    _need(packet.get("packet_id") == expected_packet_id, "PACKET_ID_BINDING_MISMATCH")
    unsigned = dict(packet); observed = unsigned.pop("packet_digest", None); _digest(observed, "packet_digest")
    _need(observed == sha256_obj(unsigned), "PACKET_DIGEST_MISMATCH")
    if capsule is not None:
        capsule_v1.validate(capsule)
        pairs = (
            ("entity_generation", "entity_generation"), ("causal_turn_id", "causal_turn_id"),
            ("workspace_capsule_digest", "capsule_digest"), ("zero_identity_digest", "zero_identity_digest"),
            ("grf_digest", "grf_digest"), ("workspace_digest", "workspace_digest"),
            ("capsule_mode", "mode"), ("required_zero_mode", "required_zero_mode"),
        )
        for pkey, ckey in pairs:
            _need(packet.get(pkey) == capsule.get(ckey), f"CAPSULE_BINDING_MISMATCH:{pkey}")
        _need(packet.get("task_sha256") == capsule["task"]["sha256"], "CAPSULE_BINDING_MISMATCH:task_sha256")
    return {"ok":True,"schema":SCHEMA,"packet_digest":observed,"runtime_credit":"ZERO","truth_credit":"ZERO","effect_credit":"ZERO"}
