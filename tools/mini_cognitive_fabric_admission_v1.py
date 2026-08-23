#!/usr/bin/env python3
"""Compose the canonical Mini Entity pre-inference Cognitive Fabric admission.

Authority is deliberately split and one-way:
MiniUnifiedDB supplies the already-active turn/cognition ancestry; the bounded invocation
selector may only cross-check that turn; the single canonical capability binder supplies
an ancestry-bound route; ZERO capsule + InferencePacket v2 bind the exact downstream
candidate context. This module creates no turn, durable truth, effect, or final UCF receipt.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
INVOCATION_SCHEMA = "MINI_COGNITIVE_INVOCATION/v1"
INVOCATION_FIELDS = {
    "expected_generation",
    "causal_turn_id",
    "task_text",
    "turn_binding_digest",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ROOT = Path(__file__).resolve().parents[1]
_JSPACE_IMPL = _ROOT / "research_entity" / "global" / "j-space" / "implementations"
_CAPSULE_IMPL = _JSPACE_IMPL / "zero_workspace_capsule_v1.py"
_PACKET_IMPL = _JSPACE_IMPL / "zero_inference_packet_v2.py"


class AdmissionError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise AdmissionError(message)


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
        raise AdmissionError("NONCANONICAL_JSON") from exc


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _load_module(path: Path, name: str) -> Any:
    _need(path.is_file(), f"CANONICAL_MODULE_MISSING:{path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    _need(spec is not None and spec.loader is not None, f"IMPORT_SPEC_FAILED:{name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_zero_modules() -> tuple[Any, Any]:
    capsule = _load_module(_CAPSULE_IMPL, "zero_workspace_capsule_v1")
    previous = sys.modules.get("zero_workspace_capsule_v1")
    sys.modules["zero_workspace_capsule_v1"] = capsule
    try:
        packet = _load_module(_PACKET_IMPL, "zero_inference_packet_v2")
    finally:
        if previous is None:
            sys.modules.pop("zero_workspace_capsule_v1", None)
        else:
            sys.modules["zero_workspace_capsule_v1"] = previous
    _need(getattr(capsule, "SCHEMA", None) == "ZERO_WORKSPACE_CAPSULE/v1", "CAPSULE_V1_REQUIRED")
    _need(getattr(packet, "SCHEMA", None) == "ZERO_INFERENCE_PACKET/v2", "PACKET_V2_REQUIRED")
    return capsule, packet


def _default_dependencies() -> tuple[Callable[..., Any], Callable[..., Any], Callable[..., Any], Callable[..., Any]]:
    import mini_inference_capability_binding_v1 as capability
    import miniunifieddb_active_turn_v1 as active_turn

    capsule, packet = _load_zero_modules()
    return (
        active_turn.resolve_active_prepare,
        capability.resolve_bound_route,
        capsule.compile_workspace_capsule,
        packet.compile_packet,
    )


def _invocation(invocation: Mapping[str, Any], generation: int) -> tuple[dict[str, Any], str]:
    _need(isinstance(invocation, Mapping), "COGNITION_INVOCATION_OBJECT_REQUIRED")
    value = dict(invocation)
    _need(set(value) == INVOCATION_FIELDS, "COGNITION_INVOCATION_FIELDS_MISMATCH")
    expected_generation = value.get("expected_generation")
    _need(type(expected_generation) is int and expected_generation >= 0, "COGNITION_INVOCATION_GENERATION_INVALID")
    _need(expected_generation == generation, "COGNITION_INVOCATION_STALE_GENERATION")
    normalized = {
        "expected_generation": expected_generation,
        "causal_turn_id": _text(value.get("causal_turn_id"), "invocation.causal_turn_id"),
        "task_text": value.get("task_text"),
        "turn_binding_digest": _digest(value.get("turn_binding_digest"), "invocation.turn_binding_digest"),
    }
    _need(type(normalized["task_text"]) is str, "COGNITION_INVOCATION_TASK_TEXT_REQUIRED")
    return normalized, sha256_obj({"schema": INVOCATION_SCHEMA, **normalized})


def _prompt_binding(compiled: Mapping[str, Any], prompt: Mapping[str, Any]) -> tuple[str, str, str, str]:
    canonical_state_hash = _digest(compiled.get("canonical_state_hash"), "canonical_state_hash")
    packet_hash = _digest(compiled.get("packet_hash"), "packet_hash")
    system = _text(prompt.get("system"), "prompt.system")
    user = _text(prompt.get("user"), "prompt.user")
    try:
        user_doc = json.loads(user)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise AdmissionError("PROMPT_USER_JSON_INVALID") from exc
    _need(type(user_doc) is dict, "PROMPT_USER_OBJECT_REQUIRED")
    _need(
        user_doc.get("CANONICAL_STATE_HASH") == canonical_state_hash
        and user_doc.get("PACKET_HASH") == packet_hash,
        "PROMPT_COMPILED_IDENTITY_MISMATCH",
    )
    return system, user, canonical_state_hash, packet_hash


def prepare_admission(
    db: Any,
    *,
    profile: Mapping[str, Any],
    previous: Mapping[str, Any],
    invocation: Mapping[str, Any],
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
    expected_activation_digest: str | None = None,
    resolve_active_prepare: Callable[..., dict[str, Any]] | None = None,
    resolve_bound_route: Callable[..., dict[str, Any]] | None = None,
    compile_workspace_capsule: Callable[..., dict[str, Any]] | None = None,
    compile_packet: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one candidate-only admission through the single retained authority path."""
    _need(isinstance(previous, Mapping), "PREVIOUS_OBJECT_REQUIRED")
    generation = previous.get("generation")
    _need(type(generation) is int and generation >= 0, "PREVIOUS_GENERATION_INVALID")
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")
    _need(isinstance(compiled, Mapping), "COMPILED_OBJECT_REQUIRED")
    _need(isinstance(prompt, Mapping), "PROMPT_OBJECT_REQUIRED")
    selector, selector_digest = _invocation(invocation, generation)
    system, user, canonical_state_hash, packet_hash = _prompt_binding(compiled, prompt)
    if expected_activation_digest is not None:
        _digest(expected_activation_digest, "expected_activation_digest")

    if any(
        item is None
        for item in (
            resolve_active_prepare,
            resolve_bound_route,
            compile_workspace_capsule,
            compile_packet,
        )
    ):
        defaults = _default_dependencies()
        resolve_active_prepare = resolve_active_prepare or defaults[0]
        resolve_bound_route = resolve_bound_route or defaults[1]
        compile_workspace_capsule = compile_workspace_capsule or defaults[2]
        compile_packet = compile_packet or defaults[3]

    binding = resolve_active_prepare(
        db,
        entity_generation=generation,
        expected_activation_digest=expected_activation_digest,
    )
    _need(isinstance(binding, Mapping) and binding.get("ok") is True, "ACTIVE_PREPARE_BINDING_UNAVAILABLE")
    _need(binding.get("entity_generation") == generation, "ACTIVE_PREPARE_GENERATION_MISMATCH")
    causal_turn_id = _text(binding.get("causal_turn_id"), "causal_turn_id")
    task_text = binding.get("task_text")
    _need(type(task_text) is str, "ACTIVE_TASK_TEXT_REQUIRED")
    _need(
        binding.get("task_sha256") == hashlib.sha256(task_text.encode("utf-8")).hexdigest(),
        "ACTIVE_TASK_BINDING_MISMATCH",
    )
    turn_binding_digest = _digest(binding.get("turn_binding_digest"), "turn_binding_digest")
    activation_digest = _digest(binding.get("activation_digest"), "activation_digest")
    _need(selector["causal_turn_id"] == causal_turn_id, "COGNITION_INVOCATION_CAUSAL_TURN_MISMATCH")
    _need(selector["task_text"] == task_text, "COGNITION_INVOCATION_TASK_MISMATCH")
    _need(selector["turn_binding_digest"] == turn_binding_digest, "COGNITION_INVOCATION_TURN_BINDING_MISMATCH")
    _need(
        binding.get("authority")
        == {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
        "ACTIVE_PREPARE_AUTHORITY_ESCALATION",
    )

    route = resolve_bound_route(profile, binding, expected_generation=generation)
    _need(isinstance(route, Mapping) and route.get("ok") is True, "BOUND_ROUTE_UNAVAILABLE")
    _need(route.get("entity_generation") == generation, "BOUND_ROUTE_GENERATION_MISMATCH")
    _need(route.get("causal_turn_id") == causal_turn_id, "BOUND_ROUTE_TURN_MISMATCH")
    _need(route.get("turn_binding_digest") == turn_binding_digest, "BOUND_ROUTE_BINDING_MISMATCH")
    _need(route.get("authority") == "ROUTING_ONLY_BOUND_TO_CANONICAL_PREPARE", "BOUND_ROUTE_AUTHORITY_ESCALATION")
    route_digest = _digest(route.get("route_digest"), "bound_route_digest")
    target_engine_class = _text(route.get("target_engine_class"), "target_engine_class")
    jspace_mode = _text(route.get("jspace_mode"), "jspace_mode")

    refs: list[str] = []
    for group in (
        binding.get("activation_provenance_refs"),
        binding.get("turn_provenance_refs"),
        binding.get("boot_provenance_refs"),
    ):
        _need(type(group) is list, "PROVENANCE_REFS_LIST_REQUIRED")
        for item in group:
            ref = _text(item, "provenance_ref")
            if ref not in refs:
                refs.append(ref)
    _need(bool(refs), "PROVENANCE_REFS_REQUIRED")

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
        provenance_refs=refs,
        required_zero_mode=_text(binding.get("required_zero_mode"), "required_zero_mode"),
    )
    _need(isinstance(capsule, Mapping) and capsule.get("mode") == "WORKSPACE_BOUND", "EXECUTABLE_WORKSPACE_CAPSULE_REQUIRED")
    capsule_digest = _digest(capsule.get("capsule_digest"), "workspace_capsule_digest")

    inference = copy.deepcopy(dict(profile.get("inference") or {}))
    _need(bool(inference), "PROFILE_INFERENCE_OBJECT_REQUIRED")
    packet = compile_packet(
        dict(capsule),
        target_engine_class=target_engine_class,
        jspace_mode=jspace_mode,
        inference=inference,
        system=system,
        user=user,
    )
    _need(isinstance(packet, Mapping) and packet.get("schema") == "ZERO_INFERENCE_PACKET/v2", "INFERENCE_PACKET_V2_REQUIRED")
    inference_packet_digest = _digest(packet.get("packet_digest"), "inference_packet_digest")
    admitted_context_digest = _digest(packet.get("admitted_context_digest"), "admitted_context_digest")

    snapshot = profile.get("_runtime_profile_snapshot")
    _need(isinstance(snapshot, Mapping), "PROFILE_SNAPSHOT_MISSING")
    profile_id = _text(snapshot.get("profile_id"), "profile_snapshot.profile_id")
    profile_hash = _digest(snapshot.get("profile_hash"), "profile_snapshot.profile_hash")
    _need(route.get("profile_id") == profile_id, "BOUND_ROUTE_PROFILE_ID_MISMATCH")
    _need(route.get("profile_hash") == profile_hash, "BOUND_ROUTE_PROFILE_HASH_MISMATCH")

    receipt = {
        "schema": ADMISSION_SCHEMA,
        "generation": generation,
        "causal_turn_id": causal_turn_id,
        "cognition_invocation_digest": selector_digest,
        "activation_digest": activation_digest,
        "turn_binding_digest": turn_binding_digest,
        "boot_binding_digest": _digest(binding.get("boot_binding_digest"), "boot_binding_digest"),
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": packet_hash,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "workspace_capsule_digest": capsule_digest,
        "workspace_digest": _digest(binding.get("workspace_digest"), "workspace_digest"),
        "bound_route_digest": route_digest,
        "capability_binding_digest": _digest(route.get("capability_binding_digest"), "capability_binding_digest"),
        "capability_receipt_digest": _digest(route.get("capability_receipt_digest"), "capability_receipt_digest"),
        "target_engine_class": target_engine_class,
        "jspace_mode": jspace_mode,
        "inference_packet_digest": inference_packet_digest,
        "admitted_context_digest": admitted_context_digest,
        "authority": "CANDIDATE_INFERENCE_ONLY",
        "real_effect_executed": False,
    }
    return {
        "ok": True,
        "schema": ADMISSION_SCHEMA,
        "generation": generation,
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": packet_hash,
        "cognition_invocation_digest": selector_digest,
        "inference_packet_digest": inference_packet_digest,
        "cognitive_fabric_receipt_digest": sha256_obj(receipt),
        "inference": inference,
        "system": system,
        "user": user,
        "admission_receipt": receipt,
    }


__all__ = [
    "ADMISSION_SCHEMA",
    "INVOCATION_SCHEMA",
    "INVOCATION_FIELDS",
    "AdmissionError",
    "prepare_admission",
    "canonical_json",
    "sha256_obj",
]
