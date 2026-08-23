#!/usr/bin/env python3
"""Canonical pre-inference Cognitive Fabric materializer for Mini Entity.

V2 supersedes the stale direct-route candidate from draft PR #1284.  Routing authority
comes only from the landed MINI_INFERENCE_CAPABILITY_BINDING/v1 in the verified
MiniUnifiedDB profile snapshot.  The runtime invocation is an assertion against the one
already-active MiniUnifiedDB cognition turn; it cannot select or mint another turn.
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

SCHEMA = "MINI_ENTITY_COGNITIVE_FABRIC_ADMISSION/v2"
VERSION = "mini-cognitive-fabric-prepare/2.0"
ROOT = Path(__file__).resolve().parents[1]
JSPACE_IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
CAPSULE_IMPL = JSPACE_IMPL / "zero_workspace_capsule_v1.py"
PACKET_IMPL = JSPACE_IMPL / "zero_inference_packet_v2.py"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_INVOCATION_KEYS = {"expected_generation", "causal_turn_id", "task_text", "turn_binding_digest"}


class PrepareError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise PrepareError(message)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
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
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_modules() -> tuple[Any, Any]:
    capsule = _load_module(CAPSULE_IMPL, "zero_workspace_capsule_v1")
    packet = _load_module(PACKET_IMPL, "zero_inference_packet_v2")
    return capsule, packet


def _validate_invocation(invocation: Mapping[str, Any], prepare: Mapping[str, Any], generation: int) -> dict[str, Any]:
    _need(isinstance(invocation, Mapping), "INVOCATION_OBJECT_REQUIRED")
    value = dict(invocation)
    _need(set(value) == _INVOCATION_KEYS, "INVOCATION_FIELDS_MISMATCH")
    expected_generation = value.get("expected_generation")
    _need(type(expected_generation) is int and not isinstance(expected_generation, bool), "INVOCATION_GENERATION_INVALID")
    _need(expected_generation == generation, "INVOCATION_GENERATION_MISMATCH")
    causal_turn_id = _text(value.get("causal_turn_id"), "invocation.causal_turn_id")
    task_text = value.get("task_text")
    _need(type(task_text) is str, "INVOCATION_TASK_TEXT_REQUIRED")
    turn_binding_digest = _digest(value.get("turn_binding_digest"), "invocation.turn_binding_digest")
    _need(causal_turn_id == prepare.get("causal_turn_id"), "INVOCATION_ACTIVE_TURN_MISMATCH")
    _need(task_text == prepare.get("task_text"), "INVOCATION_ACTIVE_TASK_MISMATCH")
    _need(turn_binding_digest == prepare.get("turn_binding_digest"), "INVOCATION_TURN_BINDING_MISMATCH")
    return {
        "expected_generation": expected_generation,
        "causal_turn_id": causal_turn_id,
        "task_sha256": _sha256_text(task_text),
        "turn_binding_digest": turn_binding_digest,
    }


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
    _need(user_doc.get("CANONICAL_STATE_HASH") == canonical_state_hash, "PROMPT_CANONICAL_STATE_HASH_MISMATCH")
    _need(user_doc.get("PACKET_HASH") == packet_hash, "PROMPT_PACKET_HASH_MISMATCH")
    return system, user, canonical_state_hash, packet_hash


def _profile_binding(profile: Mapping[str, Any]) -> tuple[str, str, dict[str, Any]]:
    snapshot = profile.get("_runtime_profile_snapshot")
    _need(isinstance(snapshot, Mapping), "PROFILE_SNAPSHOT_REQUIRED")
    profile_id = _text(snapshot.get("profile_id"), "profile_id")
    profile_hash = _digest(snapshot.get("profile_hash"), "profile_hash")
    _need(_text(profile.get("profile_id"), "profile.profile_id") == profile_id, "PROFILE_SNAPSHOT_ID_MISMATCH")
    raw_inference = profile.get("inference")
    _need(isinstance(raw_inference, Mapping), "INFERENCE_CONFIG_OBJECT_REQUIRED")
    inference = json.loads(_canonical_json(dict(raw_inference)))
    return profile_id, profile_hash, inference


def materialize_admission(
    db: sqlite3.Connection,
    *,
    previous_generation: int,
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
    profile: Mapping[str, Any],
    invocation: Mapping[str, Any],
    active_turn_module: Any | None = None,
    capability_module: Any | None = None,
    capsule_module: Any | None = None,
    packet_module: Any | None = None,
) -> dict[str, Any]:
    """Build one exact candidate-only pre-inference envelope from canonical bound material."""
    _need(type(previous_generation) is int and not isinstance(previous_generation, bool) and previous_generation >= 0, "GENERATION_INVALID")
    _need(isinstance(compiled, Mapping), "COMPILED_OBJECT_REQUIRED")
    _need(isinstance(prompt, Mapping), "PROMPT_OBJECT_REQUIRED")
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")

    system, user, canonical_state_hash, source_packet_hash = _prompt_binding(compiled, prompt)
    profile_id, profile_hash, inference = _profile_binding(profile)

    if active_turn_module is None:
        import miniunifieddb_active_turn_v1 as active_turn_module  # type: ignore[no-redef]
    prepare = active_turn_module.resolve_active_prepare(db, entity_generation=previous_generation)
    _need(type(prepare) is dict and prepare.get("ok") is True, "ACTIVE_PREPARE_RESOLVE_FAILED")
    _need(prepare.get("entity_generation") == previous_generation, "ACTIVE_PREPARE_GENERATION_MISMATCH")
    invocation_assertion = _validate_invocation(invocation, prepare, previous_generation)

    causal_turn_id = _text(prepare.get("causal_turn_id"), "causal_turn_id")
    task_text = prepare.get("task_text")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    _need(prepare.get("task_sha256") == _sha256_text(task_text), "ACTIVE_PREPARE_TASK_HASH_MISMATCH")
    activation_digest = _digest(prepare.get("activation_digest"), "activation_digest")
    turn_binding_digest = _digest(prepare.get("turn_binding_digest"), "turn_binding_digest")
    boot_binding_digest = _digest(prepare.get("boot_binding_digest"), "boot_binding_digest")

    if capability_module is None:
        import mini_inference_capability_binding_v1 as capability_module  # type: ignore[no-redef]
    route = capability_module.resolve_from_profile(profile)
    _need(type(route) is dict and route.get("ok") is True, "CAPABILITY_BINDING_RESOLVE_FAILED")
    _need(route.get("profile_id") == profile_id and route.get("profile_hash") == profile_hash, "CAPABILITY_PROFILE_BINDING_MISMATCH")
    capability_binding_digest = _digest(route.get("binding_digest"), "capability_binding_digest")
    target_engine_class = _text(route.get("target_engine_class"), "target_engine_class")
    ucf_engine_class = _text(route.get("ucf_engine_class"), "ucf_engine_class")
    jspace_mode = _text(route.get("jspace_mode"), "jspace_mode")

    provenance_refs = _refs(
        prepare.get("boot_provenance_refs"),
        prepare.get("turn_provenance_refs"),
        prepare.get("activation_provenance_refs"),
    )
    capability_ref = f"mini-entity:inference-capability:{capability_binding_digest}"
    if capability_ref not in provenance_refs:
        provenance_refs.append(capability_ref)

    if capsule_module is None or packet_module is None:
        canonical_capsule, canonical_packet = _canonical_modules()
        capsule_module = capsule_module or canonical_capsule
        packet_module = packet_module or canonical_packet

    capsule = capsule_module.compile_workspace_capsule(
        entity_generation=previous_generation,
        causal_turn_id=causal_turn_id,
        task_text=task_text,
        zero_identity_digest=_digest(prepare.get("zero_identity_digest"), "zero_identity_digest"),
        grf_digest=_digest(prepare.get("grf_digest"), "grf_digest"),
        hyperposition_digest=_digest(prepare.get("hyperposition_digest"), "hyperposition_digest"),
        local_model_digest=_digest(prepare.get("local_model_digest"), "local_model_digest"),
        jacobian_lens_digest=_digest(prepare.get("jacobian_lens_digest"), "jacobian_lens_digest"),
        workspace_digest=_digest(prepare.get("workspace_digest"), "workspace_digest"),
        selected_workspace_slots=list(prepare.get("selected_workspace_slots") or []),
        contradiction_state=_text(prepare.get("contradiction_state"), "contradiction_state"),
        provenance_refs=provenance_refs,
        required_zero_mode=_text(prepare.get("required_zero_mode"), "required_zero_mode"),
    )
    _need(type(capsule) is dict, "WORKSPACE_CAPSULE_OBJECT_REQUIRED")
    capsule_digest = _digest(capsule.get("capsule_digest"), "workspace_capsule_digest")

    packet = packet_module.compile_packet(
        capsule,
        target_engine_class=target_engine_class,
        jspace_mode=jspace_mode,
        inference=inference,
        system=system,
        user=user,
    )
    _need(type(packet) is dict, "INFERENCE_PACKET_OBJECT_REQUIRED")
    inference_packet_digest = _digest(packet.get("packet_digest"), "inference_packet_digest")
    admitted_context_digest = _digest(packet.get("admitted_context_digest"), "admitted_context_digest")

    receipt = {
        "schema": SCHEMA,
        "version": VERSION,
        "generation": previous_generation,
        "causal_turn_id": causal_turn_id,
        "canonical_state_hash": canonical_state_hash,
        "source_packet_hash": source_packet_hash,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "activation_digest": activation_digest,
        "turn_binding_digest": turn_binding_digest,
        "boot_binding_digest": boot_binding_digest,
        "invocation_assertion_digest": _sha256_obj(invocation_assertion),
        "workspace_capsule_digest": capsule_digest,
        "workspace_digest": _digest(prepare.get("workspace_digest"), "workspace_digest"),
        "inference_packet_digest": inference_packet_digest,
        "admitted_context_digest": admitted_context_digest,
        "capability_binding_digest": capability_binding_digest,
        "target_engine_class": target_engine_class,
        "ucf_engine_class": ucf_engine_class,
        "jspace_mode": jspace_mode,
        "zero_identity_digest": _digest(prepare.get("zero_identity_digest"), "zero_identity_digest"),
        "grf_digest": _digest(prepare.get("grf_digest"), "grf_digest"),
        "hyperposition_digest": _digest(prepare.get("hyperposition_digest"), "hyperposition_digest"),
        "local_model_digest": _digest(prepare.get("local_model_digest"), "local_model_digest"),
        "jspace_profile_digest": _digest(prepare.get("jspace_profile_digest"), "jspace_profile_digest"),
        "jacobian_lens_digest": _digest(prepare.get("jacobian_lens_digest"), "jacobian_lens_digest"),
        "workspace_calibration_digest": _digest(prepare.get("workspace_calibration_digest"), "workspace_calibration_digest"),
        "policy_authority_digest": _digest(prepare.get("policy_authority_digest"), "policy_authority_digest"),
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
    return {
        "ok": True,
        "schema": SCHEMA,
        "generation": previous_generation,
        "causal_turn_id": causal_turn_id,
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": source_packet_hash,
        "inference_packet_digest": inference_packet_digest,
        "cognitive_fabric_receipt_digest": receipt_digest,
        "inference": inference,
        "system": system,
        "user": user,
        "audit": {
            "workspace_capsule": capsule,
            "inference_packet": packet,
            "admission_receipt": receipt,
            "capability_binding": route,
        },
    }


def prepare_admission(*args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return materialize_admission(*args, **kwargs)
    except Exception as exc:
        return {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)}


__all__ = ["SCHEMA", "VERSION", "PrepareError", "materialize_admission", "prepare_admission"]
