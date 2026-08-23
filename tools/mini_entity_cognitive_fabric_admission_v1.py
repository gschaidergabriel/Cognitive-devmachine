#!/usr/bin/env python3
"""Pre-inference Cognitive Fabric admission for the canonical Mini Entity pipeline.

This module composes the existing MiniUnifiedDB cognition binding store with the
existing ZERO_WORKSPACE_CAPSULE/v1 and ZERO_INFERENCE_PACKET/v1 chain. It creates
candidate-inference provenance only. Truth/state remain MiniUnifiedDB-authorized and
real effects remain behind deterministic EffectGate contracts.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import miniunifieddb_cognition_store_v1 as cognition_store

_IMPL = (
    Path(__file__).resolve().parents[1]
    / "research_entity"
    / "global"
    / "j-space"
    / "implementations"
)
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

import zero_inference_packet_v1 as packet_v1
import zero_workspace_capsule_v1 as capsule_v1

ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
RECEIPT_SCHEMA = "MINI_ENTITY_COGNITIVE_FABRIC_ADMISSION_RECEIPT/v1"
VERSION = "mini-entity-cognitive-fabric-admission/1.0"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_API_KINDS = {
    "openai_style_chat_json",
    "openai_compatible_chat_json",
    "json_chat",
}


class CognitiveFabricAdmissionError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitiveFabricAdmissionError(message)


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CognitiveFabricAdmissionError("NONCANONICAL_JSON") from exc


def sha256_text(value: str) -> str:
    _need(type(value) is str, "TEXT_REQUIRED_FOR_DIGEST")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_obj(value: Any) -> str:
    return sha256_text(canonical_json(value))


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _profile_snapshot(profile: Mapping[str, Any]) -> tuple[str, str]:
    snapshot = profile.get("_runtime_profile_snapshot")
    _need(isinstance(snapshot, Mapping), "PROFILE_SNAPSHOT_MISSING")
    profile_id = snapshot.get("profile_id")
    profile_hash = snapshot.get("profile_hash")
    _need(type(profile_id) is str and bool(profile_id), "PROFILE_ID_MISSING")
    return profile_id, _digest(profile_hash, "profile_hash")


def _compiled_hashes(compiled: Mapping[str, Any]) -> tuple[str, str]:
    return (
        _digest(compiled.get("canonical_state_hash"), "canonical_state_hash"),
        _digest(compiled.get("packet_hash"), "packet_hash"),
    )


def derive_turn_identity(
    profile: Mapping[str, Any],
    previous: Mapping[str, Any],
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive deterministic turn identity from exact canonical pre-inference bytes."""
    generation = previous.get("generation")
    _need(type(generation) is int and generation >= 0, "MISSING_GENERATION")
    profile_id, profile_hash = _profile_snapshot(profile)
    canonical_hash, packet_hash = _compiled_hashes(compiled)
    system = prompt.get("system")
    user = prompt.get("user")
    _need(type(system) is str and type(user) is str, "PROMPT_CONTEXT_INVALID")
    identity = {
        "schema": "MINI_ENTITY_CAUSAL_TURN_ID/v1",
        "generation": generation,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "canonical_state_hash": canonical_hash,
        "packet_hash": packet_hash,
        "system_context_digest": sha256_text(system),
        "user_context_digest": sha256_text(user),
    }
    return {
        "causal_turn_id": "turn-" + sha256_obj(identity),
        "task_text": user,
        "identity_material": identity,
    }


def _route(profile: Mapping[str, Any], runtime: Any) -> tuple[dict[str, Any], str, str]:
    inference_value = profile.get("inference")
    _need(isinstance(inference_value, Mapping), "PROFILE_BAD_INFERENCE")
    inference = json.loads(json.dumps(dict(inference_value)))
    kind = str(inference.get("kind", "")).strip()
    _need(bool(kind), "PROFILE_BAD_INFERENCE")

    forbidden_provider_text = " ".join(
        str(inference.get(key, ""))
        for key in ("endpoint", "base_url", "provider", "service")
    ).lower()
    _need("together" not in forbidden_provider_text, "TOGETHER_PROVIDER_FORBIDDEN")

    config = profile.get("cognitive_fabric", {})
    _need(isinstance(config, Mapping), "COGNITIVE_FABRIC_CONFIG_INVALID")
    explicit_target = config.get("target_engine_class")
    explicit_mode = config.get("jspace_mode")

    if kind == "mock":
        _need(getattr(runtime, "provider_override", None) is not None, "MOCK_PROVIDER_NOT_ADMITTED")
        target, mode = "ADAPTIVE_BACKEND", "PLAIN_COMPATIBILITY"
    elif kind in _API_KINDS:
        target, mode = "ADAPTIVE_BACKEND", "PLAIN_COMPATIBILITY"
    elif kind == "local_exec":
        target = "BUNDLED_LOCAL_08B"
        _need(
            explicit_mode in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"},
            "LOCAL_JSPACE_MODE_MUST_BE_EXPLICIT",
        )
        mode = str(explicit_mode)
    elif kind == "claude_code":
        target, mode = "CLAUDE_CODE", "COMPILED_EXTERNAL"
    else:
        raise CognitiveFabricAdmissionError("UNADMITTED_INFERENCE_ENGINE:" + kind)

    if explicit_target is not None:
        _need(str(explicit_target) == target, "INFERENCE_ENGINE_CLASS_MISMATCH")
    if explicit_mode is not None:
        _need(str(explicit_mode) == mode, "JSPACE_MODE_PROFILE_MISMATCH")
    return inference, target, mode


def _receipt_material(
    *,
    generation: int,
    causal_turn_id: str,
    profile_id: str,
    profile_hash: str,
    canonical_state_hash: str,
    packet_hash: str,
    system: str,
    user: str,
    inference: Mapping[str, Any],
    target_engine_class: str,
    jspace_mode: str,
    binding: Mapping[str, Any],
    capsule_digest: str,
    inference_packet_digest: str,
) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "version": VERSION,
        "generation": generation,
        "causal_turn_id": causal_turn_id,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "canonical_state_hash": canonical_state_hash,
        "source_packet_hash": packet_hash,
        "system_context_digest": sha256_text(system),
        "user_context_digest": sha256_text(user),
        "inference_config_digest": sha256_obj(dict(inference)),
        "target_engine_class": target_engine_class,
        "jspace_mode": jspace_mode,
        "turn_binding_digest": binding["turn_binding_digest"],
        "boot_binding_digest": binding["boot_binding_digest"],
        "zero_identity_digest": binding["zero_identity_digest"],
        "grf_digest": binding["grf_digest"],
        "hyperposition_digest": binding["hyperposition_digest"],
        "bundled_manifest_digest": binding["bundled_manifest_digest"],
        "local_model_digest": binding["local_model_digest"],
        "tokenizer_digest": binding["tokenizer_digest"],
        "jspace_profile_digest": binding["jspace_profile_digest"],
        "jacobian_lens_digest": binding["jacobian_lens_digest"],
        "workspace_calibration_digest": binding["workspace_calibration_digest"],
        "workspace_digest": binding["workspace_digest"],
        "boot_source_lock_digest": binding["boot_source_lock_digest"],
        "policy_authority_digest": binding["policy_authority_digest"],
        "zero_workspace_capsule_digest": capsule_digest,
        "inference_packet_digest": inference_packet_digest,
        "authority": {
            "candidate_inference_only": True,
            "canonical_truth_write": False,
            "canonical_state_write": False,
            "external_effect_executed": False,
            "direct_effect_authority": False,
        },
    }


def _validate_prompt_origin(runtime: Any, p: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    profile = p.get("profile")
    previous = p.get("previous")
    data = p.get("data")
    _need(isinstance(profile, Mapping), "PROFILE_REQUIRED")
    _need(isinstance(previous, Mapping), "PREVIOUS_REQUIRED")
    _need(isinstance(data, Mapping), "ADMISSION_DATA_REQUIRED")
    compiled = data.get("compiled")
    prompt = data.get("prompt")
    _need(isinstance(compiled, Mapping), "COMPILED_REQUIRED")
    _need(isinstance(prompt, Mapping), "PROMPT_REQUIRED")

    expected = runtime._pipeline_build_prompt(
        {"profile": profile, "previous": previous, "data": compiled}
    )
    _need(bool(expected.get("ok")), "PROMPT_REBUILD_FAILED")
    _need(
        prompt.get("system") == expected.get("system")
        and prompt.get("user") == expected.get("user"),
        "PROMPT_COMPILED_IDENTITY_MISMATCH",
    )
    return dict(compiled), dict(prompt)


def install_schema(db: Any) -> None:
    cognition_store.install_schema(db)


def stage_turn_binding(
    runtime: Any,
    *,
    entity_db: str,
    profile: Mapping[str, Any],
    previous: Mapping[str, Any],
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
    boot_binding_digest: str,
    workspace_digest: str,
    selected_workspace_slots: list[str],
    contradiction_state: str,
    provenance_refs: list[str],
    required_zero_mode: str,
) -> dict[str, Any]:
    """Trusted setup helper; not exposed as a model/runtime effect."""
    derived = derive_turn_identity(profile, previous, compiled, prompt)
    with runtime._db(entity_db) as db:
        cognition_store.install_schema(db)
        result = cognition_store.bind_turn(
            db,
            entity_generation=int(previous["generation"]),
            causal_turn_id=derived["causal_turn_id"],
            boot_binding_digest=boot_binding_digest,
            task_text=derived["task_text"],
            workspace_digest=workspace_digest,
            selected_workspace_slots=selected_workspace_slots,
            contradiction_state=contradiction_state,
            provenance_refs=provenance_refs,
            required_zero_mode=required_zero_mode,
        )
        db.commit()
    return {**result, **derived}


def admit(runtime: Any, p: Mapping[str, Any]) -> dict[str, Any]:
    compiled, prompt = _validate_prompt_origin(runtime, p)
    profile = p["profile"]
    previous = p["previous"]
    generation = previous.get("generation")
    _need(type(generation) is int and generation >= 0, "MISSING_GENERATION")
    profile_id, profile_hash = _profile_snapshot(profile)
    canonical_hash, packet_hash = _compiled_hashes(compiled)
    system = prompt.get("system")
    user = prompt.get("user")
    _need(type(system) is str and type(user) is str, "PROMPT_CONTEXT_INVALID")
    derived = derive_turn_identity(profile, previous, compiled, prompt)

    with runtime._read_only_db(str(p["entity_db"])) as db:
        binding = cognition_store.resolve_prepare_binding(
            db,
            entity_generation=generation,
            causal_turn_id=derived["causal_turn_id"],
            task_text=derived["task_text"],
        )

    inference, target_engine_class, jspace_mode = _route(profile, runtime)
    provenance = list(
        dict.fromkeys(
            list(binding.get("boot_provenance_refs", []))
            + list(binding.get("turn_provenance_refs", []))
            + [
                "miniunifieddb:boot:" + binding["boot_binding_digest"],
                "miniunifieddb:turn:" + binding["turn_binding_digest"],
            ]
        )
    )
    capsule = capsule_v1.compile_workspace_capsule(
        entity_generation=generation,
        causal_turn_id=derived["causal_turn_id"],
        task_text=derived["task_text"],
        zero_identity_digest=binding["zero_identity_digest"],
        grf_digest=binding["grf_digest"],
        hyperposition_digest=binding["hyperposition_digest"],
        local_model_digest=binding["local_model_digest"],
        jacobian_lens_digest=binding["jacobian_lens_digest"],
        workspace_digest=binding["workspace_digest"],
        selected_workspace_slots=binding["selected_workspace_slots"],
        contradiction_state=binding["contradiction_state"],
        provenance_refs=provenance,
        required_zero_mode=binding["required_zero_mode"],
    )
    packet = packet_v1.compile_packet(
        capsule,
        target_engine_class=target_engine_class,
        jspace_mode=jspace_mode,
    )
    packet_v1.validate(packet, capsule)

    receipt = _receipt_material(
        generation=generation,
        causal_turn_id=derived["causal_turn_id"],
        profile_id=profile_id,
        profile_hash=profile_hash,
        canonical_state_hash=canonical_hash,
        packet_hash=packet_hash,
        system=system,
        user=user,
        inference=inference,
        target_engine_class=target_engine_class,
        jspace_mode=jspace_mode,
        binding=binding,
        capsule_digest=capsule["capsule_digest"],
        inference_packet_digest=packet["packet_digest"],
    )
    receipt_digest = sha256_obj(receipt)
    admitted = {
        "ok": True,
        "schema": ADMISSION_SCHEMA,
        "generation": generation,
        "causal_turn_id": derived["causal_turn_id"],
        "canonical_state_hash": canonical_hash,
        "packet_hash": packet_hash,
        "inference_packet_digest": packet["packet_digest"],
        "cognitive_fabric_receipt_digest": receipt_digest,
        "zero_workspace_capsule_digest": capsule["capsule_digest"],
        "turn_binding_digest": binding["turn_binding_digest"],
        "boot_binding_digest": binding["boot_binding_digest"],
        "inference": inference,
        "system": system,
        "user": user,
        "receipt": receipt,
    }

    registry = getattr(runtime, "_cognitive_admissions", None)
    _need(isinstance(registry, dict), "RUNTIME_ADMISSION_REGISTRY_MISSING")
    _need(receipt_digest not in registry, "DUPLICATE_COGNITIVE_ADMISSION")
    registry[receipt_digest] = {
        "admitted": json.loads(json.dumps(admitted)),
        "used": False,
        "candidate_result_digest": None,
    }
    return admitted


def _registry_entry(runtime: Any, receipt_digest: Any) -> dict[str, Any]:
    digest = _digest(receipt_digest, "cognitive_fabric_receipt_digest")
    registry = getattr(runtime, "_cognitive_admissions", None)
    _need(isinstance(registry, dict), "RUNTIME_ADMISSION_REGISTRY_MISSING")
    entry = registry.get(digest)
    _need(isinstance(entry, dict), "COGNITIVE_ADMISSION_NOT_REGISTERED")
    return entry


def require_inference_admission(runtime: Any, p: Mapping[str, Any]) -> dict[str, Any]:
    entry = _registry_entry(runtime, p.get("cognitive_fabric_receipt_digest"))
    _need(entry.get("used") is False, "COGNITIVE_ADMISSION_ALREADY_USED")
    admitted = entry["admitted"]
    _need(
        p.get("inference_packet_digest") == admitted["inference_packet_digest"],
        "INFERENCE_PACKET_DIGEST_MISMATCH",
    )
    _need(p.get("inference") == admitted["inference"], "DOWNSTREAM_INFERENCE_CONFIG_MISMATCH")
    _need(p.get("system") == admitted["system"], "DOWNSTREAM_SYSTEM_CONTEXT_MISMATCH")
    _need(p.get("user") == admitted["user"], "DOWNSTREAM_USER_CONTEXT_MISMATCH")
    receipt = admitted["receipt"]
    _need(
        admitted["cognitive_fabric_receipt_digest"] == sha256_obj(receipt),
        "COGNITIVE_FABRIC_RECEIPT_DIGEST_MISMATCH",
    )
    entry["used"] = True
    return admitted


def attach_generated(
    runtime: Any,
    p: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    entry = _registry_entry(runtime, p.get("cognitive_fabric_receipt_digest"))
    _need(entry.get("used") is True, "INFERENCE_WITHOUT_CONSUMED_ADMISSION")
    out = dict(result)
    out["inference_packet_digest"] = _digest(
        p.get("inference_packet_digest"), "inference_packet_digest"
    )
    out["cognitive_fabric_receipt_digest"] = _digest(
        p.get("cognitive_fabric_receipt_digest"), "cognitive_fabric_receipt_digest"
    )
    payload = out.get("payload")
    if isinstance(payload, Mapping):
        entry["candidate_result_digest"] = sha256_obj(dict(payload))
    return out


def _validate_admitted_envelope(admitted: Mapping[str, Any]) -> str:
    _need(admitted.get("ok") is True, "COGNITIVE_FABRIC_NOT_ADMITTED")
    _need(admitted.get("schema") == ADMISSION_SCHEMA, "COGNITIVE_FABRIC_SCHEMA_MISMATCH")
    receipt = admitted.get("receipt")
    _need(isinstance(receipt, Mapping), "COGNITIVE_FABRIC_RECEIPT_MISSING")
    digest = _digest(
        admitted.get("cognitive_fabric_receipt_digest"),
        "cognitive_fabric_receipt_digest",
    )
    _need(digest == sha256_obj(dict(receipt)), "COGNITIVE_FABRIC_RECEIPT_DIGEST_MISMATCH")
    _need(
        admitted.get("inference_packet_digest") == receipt.get("inference_packet_digest"),
        "COGNITIVE_FABRIC_PACKET_RECEIPT_MISMATCH",
    )
    return digest


def validate_gate(runtime: Any, p: Mapping[str, Any]) -> None:
    data = p.get("data")
    _need(isinstance(data, Mapping), "GATE_DATA_REQUIRED")
    admitted = data.get("cognitive_fabric")
    generated = data.get("generated")
    compiled = data.get("compiled")
    _need(isinstance(admitted, Mapping), "COGNITIVE_FABRIC_REQUIRED_AT_GATE")
    _need(isinstance(generated, Mapping), "GENERATED_REQUIRED_AT_GATE")
    _need(isinstance(compiled, Mapping), "COMPILED_REQUIRED_AT_GATE")
    digest = _validate_admitted_envelope(admitted)
    entry = _registry_entry(runtime, digest)
    _need(entry.get("used") is True, "GATE_BEFORE_ADMITTED_INFERENCE")
    _need(
        generated.get("cognitive_fabric_receipt_digest") == digest,
        "GENERATED_FABRIC_RECEIPT_MISMATCH",
    )
    _need(
        generated.get("inference_packet_digest") == admitted.get("inference_packet_digest"),
        "GENERATED_INFERENCE_PACKET_MISMATCH",
    )
    canonical_hash, packet_hash = _compiled_hashes(compiled)
    _need(admitted.get("canonical_state_hash") == canonical_hash, "ADMISSION_CANONICAL_HASH_MISMATCH")
    _need(admitted.get("packet_hash") == packet_hash, "ADMISSION_PACKET_HASH_MISMATCH")


def validate_commit(runtime: Any, p: Mapping[str, Any], db: Any) -> str:
    data = p.get("data")
    _need(isinstance(data, Mapping), "COMMIT_DATA_REQUIRED")
    admitted = data.get("cognitive_fabric")
    generated = data.get("generated")
    compiled = data.get("compiled")
    _need(isinstance(admitted, Mapping), "COGNITIVE_FABRIC_REQUIRED_AT_COMMIT")
    _need(isinstance(generated, Mapping), "GENERATED_REQUIRED_AT_COMMIT")
    _need(isinstance(compiled, Mapping), "COMPILED_REQUIRED_AT_COMMIT")
    digest = _validate_admitted_envelope(admitted)
    validate_gate(runtime, p)

    profile = p.get("profile")
    previous = p.get("previous")
    _need(isinstance(profile, Mapping) and isinstance(previous, Mapping), "COMMIT_IDENTITY_REQUIRED")
    generation = previous.get("generation")
    _need(type(generation) is int and generation >= 0, "MISSING_GENERATION")
    profile_id, profile_hash = _profile_snapshot(profile)
    receipt = admitted["receipt"]
    _need(receipt.get("generation") == generation, "ADMISSION_STALE_GENERATION")
    _need(receipt.get("profile_id") == profile_id, "ADMISSION_PROFILE_ID_MISMATCH")
    _need(receipt.get("profile_hash") == profile_hash, "ADMISSION_PROFILE_HASH_MISMATCH")

    derived = derive_turn_identity(profile, previous, compiled, {
        "system": admitted.get("system"),
        "user": admitted.get("user"),
    })
    _need(derived["causal_turn_id"] == admitted.get("causal_turn_id"), "ADMISSION_CAUSAL_TURN_MISMATCH")
    binding = cognition_store.resolve_prepare_binding(
        db,
        entity_generation=generation,
        causal_turn_id=derived["causal_turn_id"],
        task_text=derived["task_text"],
    )
    _need(binding["turn_binding_digest"] == admitted.get("turn_binding_digest"), "TURN_BINDING_CHANGED")
    _need(binding["boot_binding_digest"] == admitted.get("boot_binding_digest"), "BOOT_BINDING_CHANGED")
    _need(binding["workspace_digest"] == receipt.get("workspace_digest"), "WORKSPACE_BINDING_CHANGED")
    return digest


def finalize_admission(runtime: Any, receipt_digest: str) -> None:
    registry = getattr(runtime, "_cognitive_admissions", None)
    if isinstance(registry, dict):
        registry.pop(receipt_digest, None)


__all__ = [
    "ADMISSION_SCHEMA", "RECEIPT_SCHEMA", "VERSION",
    "CognitiveFabricAdmissionError", "canonical_json", "sha256_text", "sha256_obj",
    "derive_turn_identity", "install_schema", "stage_turn_binding", "admit",
    "require_inference_admission", "attach_generated", "validate_gate",
    "validate_commit", "finalize_admission",
]
