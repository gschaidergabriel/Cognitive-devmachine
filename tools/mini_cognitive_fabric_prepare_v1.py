#!/usr/bin/env python3
"""Deterministic pre-inference Cognitive Fabric admission materializer.

This module composes already-admitted MiniUnifiedDB cognition identity with the
repository-owned inference-capability binding, ZERO workspace capsule and InferencePacket
v2. It creates candidate inference/provenance material only. It does not mint causal-turn
identity, truth, state, effect authority, model-runtime credit, J-Space/GWT measurement
credit, or product PASS.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sqlite3
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
VERSION = "mini-cognitive-fabric-prepare/1.1"
INVOCATION_SCHEMA = "MINI_COGNITIVE_INVOCATION/v1"
INVOCATION_FIELDS = {
    "expected_generation",
    "causal_turn_id",
    "task_text",
    "turn_binding_digest",
}
ROOT = Path(__file__).resolve().parents[1]
JSPACE_IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
CAPSULE_IMPL = JSPACE_IMPL / "zero_workspace_capsule_v1.py"
PACKET_IMPL = JSPACE_IMPL / "zero_inference_packet_v2.py"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_PREPARE_DIGESTS = (
    "turn_binding_digest",
    "boot_binding_digest",
    "workspace_digest",
    "zero_identity_digest",
    "grf_digest",
    "hyperposition_digest",
    "bundled_manifest_digest",
    "local_model_digest",
    "tokenizer_digest",
    "jspace_profile_digest",
    "jacobian_lens_digest",
    "workspace_calibration_digest",
    "boot_source_lock_digest",
    "policy_authority_digest",
)


class PrepareError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise PrepareError(message)


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
        raise PrepareError("NONCANONICAL_JSON") from exc


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_obj(value: Any) -> str:
    return _sha256_text(_canonical_json(value))


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _refs(*values: Any) -> list[str]:
    out: list[str] = []
    for value in values:
        _need(type(value) is list, "PROVENANCE_REFS_LIST_REQUIRED")
        for item in value:
            ref = _text(item, "provenance_ref")
            if ref not in out:
                out.append(ref)
    _need(bool(out), "PROVENANCE_REFS_REQUIRED")
    return out


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise PrepareError(f"IMPORT_SPEC_FAILED:{name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_modules() -> tuple[Any, Any]:
    capsule = _load_module(CAPSULE_IMPL, "zero_workspace_capsule_v1")
    previous = sys.modules.get("zero_workspace_capsule_v1")
    sys.modules["zero_workspace_capsule_v1"] = capsule
    try:
        packet = _load_module(PACKET_IMPL, "zero_inference_packet_v2")
    finally:
        if previous is None:
            sys.modules.pop("zero_workspace_capsule_v1", None)
        else:
            sys.modules["zero_workspace_capsule_v1"] = previous
    _need(getattr(capsule, "SCHEMA", None) == "ZERO_WORKSPACE_CAPSULE/v1", "CAPSULE_V1_REQUIRED")
    _need(getattr(packet, "SCHEMA", None) == "ZERO_INFERENCE_PACKET/v2", "PACKET_V2_REQUIRED")
    return capsule, packet


def _prompt_binding(compiled: Mapping[str, Any], prompt: Mapping[str, Any]) -> tuple[str, str, str, str]:
    canonical_state_hash = _digest(compiled.get("canonical_state_hash"), "canonical_state_hash")
    packet_hash = _digest(compiled.get("packet_hash"), "packet_hash")
    system = prompt.get("system")
    user = prompt.get("user")
    _need(type(system) is str, "PROMPT_SYSTEM_TEXT_REQUIRED")
    _need(type(user) is str, "PROMPT_USER_TEXT_REQUIRED")
    try:
        user_doc = json.loads(user)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise PrepareError("PROMPT_USER_JSON_INVALID") from exc
    _need(type(user_doc) is dict, "PROMPT_USER_OBJECT_REQUIRED")
    _need(
        user_doc.get("CANONICAL_STATE_HASH") == canonical_state_hash
        and user_doc.get("PACKET_HASH") == packet_hash,
        "PROMPT_COMPILED_IDENTITY_MISMATCH",
    )
    return system, user, canonical_state_hash, packet_hash


def _invocation_binding(invocation: Mapping[str, Any], generation: int) -> tuple[dict[str, Any], str]:
    _need(isinstance(invocation, Mapping), "COGNITION_INVOCATION_OBJECT_REQUIRED")
    value = dict(invocation)
    _need(set(value) == INVOCATION_FIELDS, "COGNITION_INVOCATION_FIELDS_MISMATCH")
    expected_generation = value.get("expected_generation")
    _need(type(expected_generation) is int and expected_generation >= 0, "COGNITION_INVOCATION_GENERATION_INVALID")
    _need(expected_generation == generation, "COGNITION_INVOCATION_STALE_GENERATION")
    normalized = {
        "expected_generation": expected_generation,
        "causal_turn_id": _text(value.get("causal_turn_id"), "cognition_invocation.causal_turn_id"),
        "task_text": value.get("task_text"),
        "turn_binding_digest": _digest(
            value.get("turn_binding_digest"), "cognition_invocation.turn_binding_digest"
        ),
    }
    _need(type(normalized["task_text"]) is str, "COGNITION_INVOCATION_TASK_TEXT_REQUIRED")
    selector_digest = _sha256_obj({"schema": INVOCATION_SCHEMA, **normalized})
    _digest(selector_digest, "cognition_invocation_digest")
    return normalized, selector_digest


def _profile_and_capability(
    profile: Mapping[str, Any],
    capability_module: Any,
) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    snapshot = profile.get("_runtime_profile_snapshot")
    _need(isinstance(snapshot, Mapping), "PROFILE_SNAPSHOT_REQUIRED")
    profile_id = _text(snapshot.get("profile_id"), "profile_id")
    profile_hash = _digest(snapshot.get("profile_hash"), "profile_hash")
    raw_inference = profile.get("inference")
    _need(isinstance(raw_inference, Mapping), "INFERENCE_CONFIG_OBJECT_REQUIRED")
    inference = json.loads(_canonical_json(dict(raw_inference)))

    try:
        route = capability_module.resolve_from_profile(profile)
    except Exception as exc:
        raise PrepareError(f"CAPABILITY_BINDING_REJECTED:{type(exc).__name__}:{exc}") from exc
    _need(type(route) is dict and route.get("ok") is True, "CAPABILITY_BINDING_RESOLVE_FAILED")
    _need(route.get("profile_id") == profile_id, "CAPABILITY_PROFILE_ID_MISMATCH")
    _need(route.get("profile_hash") == profile_hash, "CAPABILITY_PROFILE_HASH_MISMATCH")
    _need(
        route.get("authority") == "ROUTING_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
        "CAPABILITY_AUTHORITY_ESCALATION",
    )
    _text(route.get("target_engine_class"), "capability.target_engine_class")
    _text(route.get("jspace_mode"), "capability.jspace_mode")
    _digest(route.get("binding_digest"), "capability.binding_digest")
    _digest(route.get("capability_receipt_digest"), "capability.capability_receipt_digest")
    return profile_id, profile_hash, inference, route


def materialize_admission(
    db: sqlite3.Connection,
    *,
    previous_generation: int,
    invocation: Mapping[str, Any],
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
    profile: Mapping[str, Any],
    expected_activation_digest: str | None = None,
    active_turn_module: Any | None = None,
    capability_module: Any | None = None,
    capsule_module: Any | None = None,
    packet_module: Any | None = None,
) -> dict[str, Any]:
    """Build one exact pre-inference admission envelope from canonical bound material."""
    _need(type(previous_generation) is int and previous_generation >= 0, "GENERATION_INVALID")
    _need(isinstance(compiled, Mapping), "COMPILED_OBJECT_REQUIRED")
    _need(isinstance(prompt, Mapping), "PROMPT_OBJECT_REQUIRED")
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")

    selector, selector_digest = _invocation_binding(invocation, previous_generation)
    system, user, canonical_state_hash, source_packet_hash = _prompt_binding(compiled, prompt)

    if capability_module is None:
        import mini_inference_capability_binding_v1 as capability_module  # type: ignore[no-redef]
    profile_id, profile_hash, inference, capability = _profile_and_capability(profile, capability_module)

    if active_turn_module is None:
        import miniunifieddb_active_turn_v1 as active_turn_module  # type: ignore[no-redef]
    prepare = active_turn_module.resolve_active_prepare(
        db,
        entity_generation=previous_generation,
        expected_activation_digest=expected_activation_digest,
    )
    _need(type(prepare) is dict and prepare.get("ok") is True, "ACTIVE_PREPARE_RESOLVE_FAILED")
    _need(prepare.get("entity_generation") == previous_generation, "ACTIVE_PREPARE_GENERATION_MISMATCH")

    causal_turn_id = _text(prepare.get("causal_turn_id"), "causal_turn_id")
    task_text = prepare.get("task_text")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    _need(prepare.get("task_sha256") == _sha256_text(task_text), "ACTIVE_PREPARE_TASK_HASH_MISMATCH")
    for name in _REQUIRED_PREPARE_DIGESTS:
        _digest(prepare.get(name), name)
    activation_digest = _digest(prepare.get("activation_digest"), "activation_digest")

    _need(selector["causal_turn_id"] == causal_turn_id, "COGNITION_INVOCATION_CAUSAL_TURN_MISMATCH")
    _need(selector["task_text"] == task_text, "COGNITION_INVOCATION_TASK_MISMATCH")
    _need(
        selector["turn_binding_digest"] == prepare["turn_binding_digest"],
        "COGNITION_INVOCATION_TURN_BINDING_MISMATCH",
    )
    _need(
        prepare.get("authority")
        == {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
        "PREPARE_AUTHORITY_ESCALATION",
    )

    provenance_refs = _refs(
        prepare.get("boot_provenance_refs"),
        prepare.get("turn_provenance_refs"),
        prepare.get("activation_provenance_refs"),
    )
    if capsule_module is None or packet_module is None:
        canonical_capsule, canonical_packet = _canonical_modules()
        capsule_module = capsule_module or canonical_capsule
        packet_module = packet_module or canonical_packet

    capsule = capsule_module.compile_workspace_capsule(
        entity_generation=previous_generation,
        causal_turn_id=causal_turn_id,
        task_text=task_text,
        zero_identity_digest=prepare["zero_identity_digest"],
        grf_digest=prepare["grf_digest"],
        hyperposition_digest=prepare["hyperposition_digest"],
        local_model_digest=prepare["local_model_digest"],
        jacobian_lens_digest=prepare["jacobian_lens_digest"],
        workspace_digest=prepare["workspace_digest"],
        selected_workspace_slots=list(prepare.get("selected_workspace_slots") or []),
        contradiction_state=_text(prepare.get("contradiction_state"), "contradiction_state"),
        provenance_refs=provenance_refs,
        required_zero_mode=_text(prepare.get("required_zero_mode"), "required_zero_mode"),
    )
    _need(type(capsule) is dict, "WORKSPACE_CAPSULE_OBJECT_REQUIRED")
    capsule_digest = _digest(capsule.get("capsule_digest"), "workspace_capsule_digest")

    packet = packet_module.compile_packet(
        capsule,
        target_engine_class=capability["target_engine_class"],
        jspace_mode=capability["jspace_mode"],
        inference=inference,
        system=system,
        user=user,
    )
    _need(type(packet) is dict and packet.get("schema") == "ZERO_INFERENCE_PACKET/v2", "INFERENCE_PACKET_V2_REQUIRED")
    inference_packet_digest = _digest(packet.get("packet_digest"), "inference_packet_digest")
    admitted_context_digest = _digest(packet.get("admitted_context_digest"), "admitted_context_digest")

    receipt = {
        "schema": SCHEMA,
        "version": VERSION,
        "generation": previous_generation,
        "causal_turn_id": causal_turn_id,
        "cognition_invocation_digest": selector_digest,
        "canonical_state_hash": canonical_state_hash,
        "source_packet_hash": source_packet_hash,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "activation_digest": activation_digest,
        "turn_binding_digest": prepare["turn_binding_digest"],
        "boot_binding_digest": prepare["boot_binding_digest"],
        "workspace_capsule_digest": capsule_digest,
        "workspace_digest": prepare["workspace_digest"],
        "zero_identity_digest": prepare["zero_identity_digest"],
        "grf_digest": prepare["grf_digest"],
        "hyperposition_digest": prepare["hyperposition_digest"],
        "bundled_manifest_digest": prepare["bundled_manifest_digest"],
        "local_model_digest": prepare["local_model_digest"],
        "tokenizer_digest": prepare["tokenizer_digest"],
        "jspace_profile_digest": prepare["jspace_profile_digest"],
        "jacobian_lens_digest": prepare["jacobian_lens_digest"],
        "workspace_calibration_digest": prepare["workspace_calibration_digest"],
        "boot_source_lock_digest": prepare["boot_source_lock_digest"],
        "policy_authority_digest": prepare["policy_authority_digest"],
        "capability_binding_digest": capability["binding_digest"],
        "capability_receipt_digest": capability["capability_receipt_digest"],
        "target_engine_class": capability["target_engine_class"],
        "jspace_mode": capability["jspace_mode"],
        "inference_packet_digest": inference_packet_digest,
        "admitted_context_digest": admitted_context_digest,
        "provenance_refs": provenance_refs,
        "authority": {
            "semantic_authority": "CANDIDATE_INFERENCE_ONLY",
            "direct_truth_authority": False,
            "direct_state_authority": False,
            "direct_effect_authority": False,
        },
        "effect_executed": False,
    }
    receipt_digest = _sha256_obj(receipt)
    _digest(receipt_digest, "cognitive_fabric_receipt_digest")

    return {
        "ok": True,
        "schema": SCHEMA,
        "generation": previous_generation,
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": source_packet_hash,
        "cognition_invocation_digest": selector_digest,
        "inference_packet_digest": inference_packet_digest,
        "cognitive_fabric_receipt_digest": receipt_digest,
        "inference": inference,
        "system": system,
        "user": user,
        "causal_turn_id": causal_turn_id,
        "activation_digest": activation_digest,
        "turn_binding_digest": prepare["turn_binding_digest"],
        "capability_binding_digest": capability["binding_digest"],
        "audit": {
            "workspace_capsule": capsule,
            "inference_packet": packet,
            "admission_receipt": receipt,
        },
    }


def prepare_admission(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Runtime-friendly fail-closed wrapper around materialize_admission()."""
    try:
        return materialize_admission(*args, **kwargs)
    except Exception as exc:
        return {
            "ok": False,
            "error_kind": type(exc).__name__,
            "error": str(exc),
        }


__all__ = [
    "SCHEMA",
    "VERSION",
    "INVOCATION_SCHEMA",
    "INVOCATION_FIELDS",
    "PrepareError",
    "materialize_admission",
    "prepare_admission",
]
