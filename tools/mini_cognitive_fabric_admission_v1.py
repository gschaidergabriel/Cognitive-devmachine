#!/usr/bin/env python3
"""Compose the canonical Mini Entity pre-inference Cognitive Fabric admission.

The runtime reads one generation-scoped ACTIVE_COGNITION_TURN from MiniUnifiedDB,
uses the canonical explicit inference-capability binding, and composes the existing
ZERO workspace-capsule and InferencePacket-v2 contracts. It creates no second turn,
state, truth, identity, recovery, inference-capability, or effect authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
_PACKET_TARGETS = {"CLAUDE_CODE", "BUNDLED_LOCAL_08B", "ADAPTIVE_BACKEND"}
_JSPACE_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY", "COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class AdmissionError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise AdmissionError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _default_dependencies():
    import sys
    tools_dir = Path(__file__).resolve().parent
    jspace_dir = tools_dir.parent / "research_entity" / "global" / "j-space" / "implementations"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    if str(jspace_dir) not in sys.path:
        sys.path.insert(0, str(jspace_dir))
    import mini_inference_capability_binding_v1 as capability
    import miniunifieddb_active_turn_v1 as active_turn
    import zero_inference_packet_v2 as packet_v2
    import zero_workspace_capsule_v1 as capsule_v1
    return (
        active_turn.resolve_active_prepare,
        capability.resolve_from_profile,
        capsule_v1.compile_workspace_capsule,
        packet_v2.compile_packet,
    )


def prepare_admission(
    db: Any,
    *,
    profile: Mapping[str, Any],
    previous: Mapping[str, Any],
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
    resolve_active_prepare: Callable[..., dict[str, Any]] | None = None,
    resolve_capability: Callable[..., dict[str, Any]] | None = None,
    compile_workspace_capsule: Callable[..., dict[str, Any]] | None = None,
    compile_packet: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Prepare one candidate envelope through the single retained authority path."""
    _need(isinstance(previous, Mapping), "PREVIOUS_OBJECT_REQUIRED")
    generation = previous.get("generation")
    _need(type(generation) is int and generation >= 0, "PREVIOUS_GENERATION_INVALID")
    _need(isinstance(compiled, Mapping), "COMPILED_OBJECT_REQUIRED")
    canonical_state_hash = _digest(compiled.get("canonical_state_hash"), "canonical_state_hash")
    packet_hash = _digest(compiled.get("packet_hash"), "packet_hash")
    _need(isinstance(prompt, Mapping), "PROMPT_OBJECT_REQUIRED")
    system = _text(prompt.get("system"), "prompt.system")
    user = _text(prompt.get("user"), "prompt.user")

    if any(x is None for x in (resolve_active_prepare, resolve_capability, compile_workspace_capsule, compile_packet)):
        defaults = _default_dependencies()
        resolve_active_prepare = resolve_active_prepare or defaults[0]
        resolve_capability = resolve_capability or defaults[1]
        compile_workspace_capsule = compile_workspace_capsule or defaults[2]
        compile_packet = compile_packet or defaults[3]

    binding = resolve_active_prepare(db, entity_generation=generation)
    _need(isinstance(binding, Mapping) and binding.get("ok") is True, "ACTIVE_PREPARE_BINDING_UNAVAILABLE")
    _need(binding.get("entity_generation") == generation, "ACTIVE_PREPARE_GENERATION_MISMATCH")
    causal_turn_id = _text(binding.get("causal_turn_id"), "causal_turn_id")
    task_text = binding.get("task_text")
    _need(type(task_text) is str, "ACTIVE_TASK_TEXT_REQUIRED")
    _need(binding.get("task_sha256") == hashlib.sha256(task_text.encode("utf-8")).hexdigest(), "ACTIVE_TASK_BINDING_MISMATCH")
    activation_digest = _digest(binding.get("activation_digest"), "activation_digest")
    turn_binding_digest = _digest(binding.get("turn_binding_digest"), "turn_binding_digest")

    route = resolve_capability(profile)
    _need(isinstance(route, Mapping) and route.get("ok") is True, "CAPABILITY_BINDING_UNAVAILABLE")
    target_engine_class = route.get("target_engine_class")
    jspace_mode = route.get("jspace_mode")
    _need(target_engine_class in _PACKET_TARGETS, "CAPABILITY_PACKET_TARGET_INVALID")
    _need(jspace_mode in _JSPACE_MODES, "CAPABILITY_JSPACE_MODE_INVALID")
    capability_binding_digest = _digest(route.get("binding_digest"), "capability_binding_digest")
    capability_receipt_digest = _digest(route.get("capability_receipt_digest"), "capability_receipt_digest")
    adapter_version = _text(route.get("adapter_version"), "adapter_version")

    capsule = compile_workspace_capsule(
        entity_generation=generation,
        causal_turn_id=causal_turn_id,
        task_text=task_text,
        zero_identity_digest=_digest(binding.get("zero_identity_digest"), "zero_identity_digest"),
        grf_digest=_digest(binding.get("grf_digest"), "grf_digest"),
        hyperposition_digest=_digest(binding.get("hyperposition_digest"), "hyperposition_digest"),
        local_model_digest=_digest(binding.get("local_model_digest"), "local_model_digest"),
        jacobian_lens_digest=_digest(binding.get("jacobian_lens_digest"), "jacobian_lens_digest"),
        workspace_digest=_digest(binding.get("workspace_digest"), "workspace_digest"),
        selected_workspace_slots=list(binding.get("selected_workspace_slots") or []),
        contradiction_state=_text(binding.get("contradiction_state"), "contradiction_state"),
        provenance_refs=(list(binding.get("activation_provenance_refs") or []) +
                         list(binding.get("turn_provenance_refs") or []) +
                         list(binding.get("boot_provenance_refs") or [])),
        required_zero_mode=_text(binding.get("required_zero_mode"), "required_zero_mode"),
    )
    _need(isinstance(capsule, Mapping) and capsule.get("mode") == "WORKSPACE_BOUND", "EXECUTABLE_WORKSPACE_CAPSULE_REQUIRED")
    capsule_digest = _digest(capsule.get("capsule_digest"), "workspace_capsule_digest")

    _need(isinstance(profile.get("inference"), Mapping), "PROFILE_INFERENCE_OBJECT_REQUIRED")
    inference = copy.deepcopy(dict(profile["inference"]))
    admitted_system = (" " + system)[1:]
    admitted_user = (" " + user)[1:]
    packet = compile_packet(
        dict(capsule),
        target_engine_class=str(target_engine_class),
        jspace_mode=str(jspace_mode),
        inference=inference,
        system=admitted_system,
        user=admitted_user,
    )
    _need(isinstance(packet, Mapping), "INFERENCE_PACKET_OBJECT_REQUIRED")
    inference_packet_digest = _digest(packet.get("packet_digest"), "inference_packet_digest")

    snapshot = profile.get("_runtime_profile_snapshot")
    _need(isinstance(snapshot, Mapping), "PROFILE_SNAPSHOT_MISSING")
    profile_id = _text(snapshot.get("profile_id"), "profile_snapshot.profile_id")
    profile_hash = _digest(snapshot.get("profile_hash"), "profile_snapshot.profile_hash")
    _need(route.get("profile_id") in {None, profile_id}, "CAPABILITY_PROFILE_ID_DRIFT")
    _need(route.get("profile_hash") in {None, profile_hash}, "CAPABILITY_PROFILE_HASH_DRIFT")

    receipt = {
        "schema": ADMISSION_SCHEMA,
        "generation": generation,
        "causal_turn_id": causal_turn_id,
        "activation_digest": activation_digest,
        "turn_binding_digest": turn_binding_digest,
        "boot_binding_digest": _digest(binding.get("boot_binding_digest"), "boot_binding_digest"),
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": packet_hash,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "workspace_capsule_digest": capsule_digest,
        "workspace_digest": _digest(binding.get("workspace_digest"), "workspace_digest"),
        "jspace_profile_digest": _digest(binding.get("jspace_profile_digest"), "jspace_profile_digest"),
        "jacobian_lens_digest": _digest(binding.get("jacobian_lens_digest"), "jacobian_lens_digest"),
        "workspace_calibration_digest": _digest(binding.get("workspace_calibration_digest"), "workspace_calibration_digest"),
        "policy_authority_digest": _digest(binding.get("policy_authority_digest"), "policy_authority_digest"),
        "capability_binding_digest": capability_binding_digest,
        "capability_receipt_digest": capability_receipt_digest,
        "adapter_version": adapter_version,
        "target_engine_class": target_engine_class,
        "jspace_mode": jspace_mode,
        "inference_packet_digest": inference_packet_digest,
        "authority": "CANDIDATE_INFERENCE_ONLY",
        "real_effect_executed": False,
    }
    return {
        "ok": True,
        "schema": ADMISSION_SCHEMA,
        "generation": generation,
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": packet_hash,
        "inference_packet_digest": inference_packet_digest,
        "cognitive_fabric_receipt_digest": sha256_obj(receipt),
        "inference": inference,
        "system": admitted_system,
        "user": admitted_user,
        "admission_receipt": receipt,
    }


__all__ = ["ADMISSION_SCHEMA", "AdmissionError", "prepare_admission", "canonical_json", "sha256_obj"]
