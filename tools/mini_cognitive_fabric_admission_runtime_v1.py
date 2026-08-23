#!/usr/bin/env python3
"""Fail-closed pre-inference Mini Entity Cognitive Fabric admission implementation.

This is an importable implementation organ for the retained ProfilePipelineRuntime.
It composes only already-bound MiniUnifiedDB turn/cognition material, the explicit
capability binding, ZERO_WORKSPACE_CAPSULE/v1 and ZERO_INFERENCE_PACKET/v2. It creates
candidate/provenance evidence only and has no state/truth/effect authority.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
RECEIPT_SCHEMA = "MINI_ENTITY_COGNITIVE_FABRIC_ADMISSION_RECEIPT/v1"
INVOCATION_KEYS = {"expected_generation", "causal_turn_id", "task_text", "turn_binding_digest"}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class AdmissionError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise AdmissionError(message)


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AdmissionError("NONCANONICAL_JSON") from exc


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AdmissionError(f"IMPORT_FAILED:{name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _modules(root: Path) -> dict[str, Any]:
    tools = root / "tools"
    zero = root / "research_entity" / "global" / "j-space" / "implementations"
    return {
        "store": _load(tools / "miniunifieddb_cognition_store_v1.py", "miniunifieddb_cognition_store_v1"),
        "active": _load(tools / "miniunifieddb_active_turn_v1.py", "miniunifieddb_active_turn_v1"),
        "capability": _load(tools / "mini_inference_capability_binding_v1.py", "mini_inference_capability_binding_v1"),
        "capsule": _load(zero / "zero_workspace_capsule_v1.py", "zero_workspace_capsule_v1"),
        "packet": _load(zero / "zero_inference_packet_v2.py", "zero_inference_packet_v2"),
    }


def _validate_invocation(value: Any, generation: int) -> dict[str, Any]:
    _need(type(value) is dict and set(value) == INVOCATION_KEYS, "COGNITION_INVOCATION_FIELDS_MISMATCH")
    expected = value.get("expected_generation")
    _need(type(expected) is int and not isinstance(expected, bool) and expected >= 0, "INVOCATION_GENERATION_INVALID")
    _need(expected == generation, "INVOCATION_STALE_GENERATION")
    return {
        "expected_generation": expected,
        "causal_turn_id": _text(value.get("causal_turn_id"), "invocation.causal_turn_id"),
        "task_text": value.get("task_text") if type(value.get("task_text")) is str else (_ for _ in ()).throw(AdmissionError("INVOCATION_TASK_TEXT_REQUIRED")),
        "turn_binding_digest": _digest(value.get("turn_binding_digest"), "invocation.turn_binding_digest"),
    }


def _validate_prompt(compiled: Mapping[str, Any], prompt: Any) -> tuple[str, str]:
    _need(isinstance(prompt, Mapping) and prompt.get("ok") is True, "PROMPT_INVALID")
    system = prompt.get("system")
    user = prompt.get("user")
    _need(type(system) is str and type(user) is str, "PROMPT_CONTEXT_REQUIRED")
    try:
        payload = json.loads(user)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AdmissionError("PROMPT_USER_JSON_INVALID") from exc
    _need(type(payload) is dict, "PROMPT_USER_OBJECT_REQUIRED")
    _need(payload.get("CANONICAL_STATE_HASH") == compiled.get("canonical_state_hash"), "PROMPT_CANONICAL_STATE_HASH_MISMATCH")
    _need(payload.get("PACKET_HASH") == compiled.get("packet_hash"), "PROMPT_PACKET_HASH_MISMATCH")
    return system, user


def admit(
    db,
    *,
    profile: Mapping[str, Any],
    previous: Mapping[str, Any],
    data: Mapping[str, Any],
    modules: Mapping[str, Any] | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build the exact pre-inference candidate admission envelope, or raise AdmissionError."""
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")
    _need(isinstance(previous, Mapping), "PREVIOUS_OBJECT_REQUIRED")
    _need(isinstance(data, Mapping), "ADMISSION_DATA_OBJECT_REQUIRED")
    generation = previous.get("generation")
    _need(type(generation) is int and not isinstance(generation, bool) and generation >= 0, "MISSING_GENERATION")

    compiled = data.get("compiled")
    _need(isinstance(compiled, Mapping) and compiled.get("ok") is True, "COMPILED_INVALID")
    canonical_state_hash = _digest(compiled.get("canonical_state_hash"), "canonical_state_hash")
    source_packet_hash = _digest(compiled.get("packet_hash"), "packet_hash")
    system, user = _validate_prompt(compiled, data.get("prompt"))
    invocation = _validate_invocation(data.get("invocation"), generation)

    if modules is None:
        root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[1]
        modules = _modules(root)
    active = modules["active"]
    store = modules["store"]
    capability = modules["capability"]
    capsule_module = modules["capsule"]
    packet_module = modules["packet"]

    resolved = active.resolve_active_prepare(
        db,
        entity_generation=generation,
        store_module=store,
    )
    _need(type(resolved) is dict and resolved.get("ok") is True, "ACTIVE_PREPARE_RESOLUTION_FAILED")
    _need(resolved.get("causal_turn_id") == invocation["causal_turn_id"], "INVOCATION_CAUSAL_TURN_MISMATCH")
    _need(resolved.get("task_text") == invocation["task_text"], "INVOCATION_TASK_TEXT_MISMATCH")
    _need(resolved.get("turn_binding_digest") == invocation["turn_binding_digest"], "INVOCATION_TURN_BINDING_MISMATCH")
    _need(resolved.get("entity_generation") == generation, "ACTIVE_PREPARE_GENERATION_MISMATCH")

    route = capability.resolve_from_profile(profile)
    _need(type(route) is dict and route.get("ok") is True, "CAPABILITY_RESOLUTION_FAILED")

    capsule = capsule_module.compile_workspace_capsule(
        entity_generation=generation,
        causal_turn_id=resolved["causal_turn_id"],
        task_text=resolved["task_text"],
        zero_identity_digest=resolved["zero_identity_digest"],
        grf_digest=resolved["grf_digest"],
        hyperposition_digest=resolved["hyperposition_digest"],
        local_model_digest=resolved["local_model_digest"],
        jacobian_lens_digest=resolved["jacobian_lens_digest"],
        workspace_digest=resolved["workspace_digest"],
        selected_workspace_slots=list(resolved["selected_workspace_slots"]),
        contradiction_state=resolved["contradiction_state"],
        provenance_refs=list(resolved["provenance_refs"]),
        required_zero_mode=resolved["required_zero_mode"],
    )
    _need(capsule.get("mode") == "WORKSPACE_BOUND", "ABSTAINED_CAPSULE_NOT_EXECUTABLE")

    inference = dict(profile.get("inference") or {})
    _need(bool(inference), "INFERENCE_CONFIG_REQUIRED")
    packet = packet_module.compile_packet(
        capsule,
        target_engine_class=route["target_engine_class"],
        jspace_mode=route["jspace_mode"],
        inference=inference,
        system=system,
        user=user,
    )
    packet_module.validate(packet, capsule, inference=inference, system=system, user=user, require_context=True)
    inference_packet_digest = _digest(packet.get("packet_digest"), "inference_packet_digest")

    snapshot = profile.get("_runtime_profile_snapshot")
    _need(isinstance(snapshot, Mapping), "PROFILE_SNAPSHOT_MISSING")
    profile_id = _text(snapshot.get("profile_id"), "profile_snapshot.profile_id")
    profile_hash = _digest(snapshot.get("profile_hash"), "profile_snapshot.profile_hash")

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "generation": generation,
        "causal_turn_id": resolved["causal_turn_id"],
        "canonical_state_hash": canonical_state_hash,
        "source_packet_hash": source_packet_hash,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "activation_digest": _digest(resolved.get("activation_digest"), "activation_digest"),
        "turn_binding_digest": _digest(resolved.get("turn_binding_digest"), "turn_binding_digest"),
        "boot_binding_digest": _digest(resolved.get("boot_binding_digest"), "boot_binding_digest"),
        "workspace_capsule_digest": _digest(capsule.get("capsule_digest"), "workspace_capsule_digest"),
        "workspace_digest": _digest(resolved.get("workspace_digest"), "workspace_digest"),
        "jspace_profile_digest": _digest(resolved.get("jspace_profile_digest"), "jspace_profile_digest"),
        "jacobian_lens_digest": _digest(resolved.get("jacobian_lens_digest"), "jacobian_lens_digest"),
        "workspace_calibration_digest": _digest(resolved.get("workspace_calibration_digest"), "workspace_calibration_digest"),
        "local_model_digest": _digest(resolved.get("local_model_digest"), "local_model_digest"),
        "capability_binding_digest": _digest(route.get("binding_digest"), "capability_binding_digest"),
        "capability_receipt_digest": _digest(route.get("capability_receipt_digest"), "capability_receipt_digest"),
        "target_engine_class": route["target_engine_class"],
        "ucf_engine_class": route["ucf_engine_class"],
        "jspace_mode": route["jspace_mode"],
        "inference_packet_digest": inference_packet_digest,
        "authority": "CANDIDATE_INFERENCE_ONLY",
        "admission_effect_executed": False,
    }
    receipt_digest = sha256_obj(receipt)
    _digest(receipt_digest, "cognitive_fabric_receipt_digest")

    return {
        "ok": True,
        "schema": SCHEMA,
        "generation": generation,
        "causal_turn_id": resolved["causal_turn_id"],
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": source_packet_hash,
        "inference_packet_digest": inference_packet_digest,
        "cognitive_fabric_receipt_digest": receipt_digest,
        "workspace_capsule_digest": capsule["capsule_digest"],
        "capability_binding_digest": route["binding_digest"],
        "activation_digest": resolved["activation_digest"],
        "inference": inference,
        "system": system,
        "user": user,
        "admission_receipt": receipt,
        "authority": "CANDIDATE_INFERENCE_ONLY",
    }


__all__ = ["SCHEMA", "RECEIPT_SCHEMA", "AdmissionError", "admit", "sha256_obj"]
