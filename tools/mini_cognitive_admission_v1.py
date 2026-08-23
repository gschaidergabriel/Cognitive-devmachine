#!/usr/bin/env python3
"""Deterministic pre-inference Mini Entity Cognitive Fabric admission compiler.

This module resolves only already-bound MiniUnifiedDB cognition material.  The caller
selector is a routing assertion, never cognition/state/effect authority.  Engine/J-Space
semantics come from a versioned capability embedded in the generation-admitted
JSPACE_PROFILE object, never from provider/model-name guessing.

Scope: source/mechanism candidate only.  It executes no model and no real effect.
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

import miniunifieddb_active_turn_v1 as active_turn

ROOT = Path(__file__).resolve().parents[1]
CAPSULE_PATH = (
    ROOT
    / "research_entity"
    / "global"
    / "j-space"
    / "implementations"
    / "zero_workspace_capsule_v1.py"
)
PACKET_PATH = (
    ROOT
    / "research_entity"
    / "global"
    / "j-space"
    / "implementations"
    / "zero_inference_packet_v2.py"
)

SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
ROUTE_SCHEMA = "MINI_COGNITIVE_ROUTE_CAPABILITY/v1"
INVOCATION_KEYS = {
    "expected_generation",
    "causal_turn_id",
    "task_text",
    "turn_binding_digest",
}
ROUTE_KEYS = {
    "schema",
    "target_engine_class",
    "jspace_mode",
    "inference_config_digest",
    "allowed_inference_kinds",
    "candidate_only",
    "direct_state_authority",
    "direct_effect_authority",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CognitiveAdmissionError(ValueError):
    pass


def _load(path: Path, name: str):
    parent = str(path.parent)
    inserted = parent not in sys.path
    if inserted:
        sys.path.insert(0, parent)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise CognitiveAdmissionError(f"IMPORT_SPEC_FAILED:{name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if inserted:
            try:
                sys.path.remove(parent)
            except ValueError:
                pass


capsule_v1 = _load(CAPSULE_PATH, "mini_cognitive_zero_capsule_v1")
packet_v2 = _load(PACKET_PATH, "mini_cognitive_zero_packet_v2")


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitiveAdmissionError(message)


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CognitiveAdmissionError("NON_CANONICAL_JSON") from exc


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(len(set(value)) > 1, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _selector(invocation: Any) -> dict[str, Any]:
    _need(type(invocation) is dict, "INVOCATION_OBJECT_REQUIRED")
    _need(set(invocation) == INVOCATION_KEYS, "INVOCATION_FIELDS_MISMATCH")
    generation = invocation.get("expected_generation")
    _need(type(generation) is int and generation >= 0, "INVOCATION_GENERATION_INVALID")
    causal_turn_id = _text(invocation.get("causal_turn_id"), "causal_turn_id")
    task_text = invocation.get("task_text")
    _need(type(task_text) is str, "INVOCATION_TASK_TEXT_REQUIRED")
    turn_binding_digest = _digest(invocation.get("turn_binding_digest"), "turn_binding_digest")
    return {
        "expected_generation": generation,
        "causal_turn_id": causal_turn_id,
        "task_text": task_text,
        "turn_binding_digest": turn_binding_digest,
    }


def _load_route_capability(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    jspace_profile_digest: str,
    inference: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load one exact generation-admitted JSPACE_PROFILE and validate its route capability."""
    jspace_profile_digest = _digest(jspace_profile_digest, "jspace_profile_digest")
    rows = db.execute(
        """SELECT o.object_version,o.digest_basis,o.payload_json,o.payload_digest,
                  a.admission_receipt_digest
             FROM mini_cognition_objects o
             JOIN mini_cognition_object_admissions a
               ON a.object_kind=o.object_kind
              AND a.object_version=o.object_version
              AND a.object_digest=o.object_digest
            WHERE o.object_kind='JSPACE_PROFILE'
              AND o.object_digest=?
              AND a.admitted_generation=?""",
        (jspace_profile_digest, entity_generation),
    ).fetchall()
    _need(bool(rows), "ROUTE_JSPACE_PROFILE_NOT_ADMITTED")
    _need(len(rows) == 1, "ROUTE_JSPACE_PROFILE_AMBIGUOUS")
    row = rows[0]
    try:
        payload = json.loads(str(row[2]))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CognitiveAdmissionError("ROUTE_JSPACE_PROFILE_JSON_INVALID") from exc
    _need(type(payload) is dict, "ROUTE_JSPACE_PROFILE_OBJECT_REQUIRED")
    observed_payload_digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    _need(observed_payload_digest == row[3], "ROUTE_JSPACE_PROFILE_PAYLOAD_DIGEST_MISMATCH")
    if row[1] == "CANONICAL_JSON":
        _need(jspace_profile_digest == observed_payload_digest, "ROUTE_JSPACE_PROFILE_OBJECT_DIGEST_MISMATCH")
    _digest(row[4], "route_admission_receipt_digest")

    route = payload.get("cognitive_route_capability")
    _need(type(route) is dict, "ROUTE_CAPABILITY_REQUIRED")
    _need(set(route) == ROUTE_KEYS, "ROUTE_CAPABILITY_FIELDS_MISMATCH")
    _need(route.get("schema") == ROUTE_SCHEMA, "ROUTE_CAPABILITY_SCHEMA_MISMATCH")
    target = route.get("target_engine_class")
    mode = route.get("jspace_mode")
    _need(target in packet_v2.TARGETS - {"NO_MODEL_REQUIRED"}, "ROUTE_ENGINE_UNSUPPORTED")
    _need(mode in packet_v2.JSPACE_MODES, "ROUTE_JSPACE_MODE_UNSUPPORTED")
    if target == "CLAUDE_CODE":
        _need(mode == "COMPILED_EXTERNAL", "ROUTE_CLAUDE_JSPACE_MODE_INVALID")
    if target == "BUNDLED_LOCAL_08B":
        _need(mode in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"}, "ROUTE_LOCAL_08B_JSPACE_MODE_INVALID")

    kinds = route.get("allowed_inference_kinds")
    _need(type(kinds) is list and bool(kinds), "ROUTE_INFERENCE_KINDS_REQUIRED")
    _need(all(type(item) is str and bool(item.strip()) for item in kinds), "ROUTE_INFERENCE_KIND_INVALID")
    _need(len(kinds) == len(set(kinds)), "ROUTE_INFERENCE_KINDS_DUPLICATE")
    inference_kind = _text(inference.get("kind"), "inference.kind")
    _need(inference_kind in kinds, "ROUTE_INFERENCE_KIND_NOT_ADMITTED")
    _need(route.get("candidate_only") is True, "ROUTE_CANDIDATE_ONLY_REQUIRED")
    _need(route.get("direct_state_authority") is False, "ROUTE_STATE_AUTHORITY_FORBIDDEN")
    _need(route.get("direct_effect_authority") is False, "ROUTE_EFFECT_AUTHORITY_FORBIDDEN")

    inference_digest = packet_v2.sha256_obj(dict(inference))
    _need(
        _digest(route.get("inference_config_digest"), "route.inference_config_digest")
        == inference_digest,
        "ROUTE_INFERENCE_CONFIG_MISMATCH",
    )
    return dict(route), {
        "object_version": str(row[0]),
        "object_digest": jspace_profile_digest,
        "payload_digest": observed_payload_digest,
        "admission_receipt_digest": str(row[4]),
    }


def _profile_identity(profile: Mapping[str, Any]) -> tuple[str, str]:
    snapshot = profile.get("_runtime_profile_snapshot")
    _need(type(snapshot) is dict, "PROFILE_RUNTIME_SNAPSHOT_REQUIRED")
    profile_id = _text(profile.get("profile_id"), "profile_id")
    _need(snapshot.get("profile_id") == profile_id, "PROFILE_SNAPSHOT_ID_MISMATCH")
    profile_hash = _digest(snapshot.get("profile_hash"), "profile_hash")
    normalized = dict(profile)
    normalized.pop("_runtime_profile_snapshot", None)
    _need(sha256_obj(normalized) == profile_hash, "PROFILE_SNAPSHOT_HASH_MISMATCH")
    return profile_id, profile_hash


def admit(
    db: sqlite3.Connection,
    *,
    previous: Mapping[str, Any],
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
    profile: Mapping[str, Any],
    invocation: Any,
) -> dict[str, Any]:
    """Compile one executable pre-inference admission from exact bound MiniUnifiedDB material."""
    selector = _selector(invocation)
    previous_generation = previous.get("generation")
    _need(type(previous_generation) is int and previous_generation >= 0, "PREVIOUS_GENERATION_INVALID")
    _need(
        selector["expected_generation"] == previous_generation,
        "INVOCATION_PREVIOUS_GENERATION_MISMATCH",
    )

    resolved = active_turn.resolve_active_prepare(
        db,
        entity_generation=selector["expected_generation"],
    )
    _need(resolved.get("causal_turn_id") == selector["causal_turn_id"], "SELECTOR_CAUSAL_TURN_MISMATCH")
    _need(resolved.get("task_text") == selector["task_text"], "SELECTOR_TASK_TEXT_MISMATCH")
    _need(
        resolved.get("turn_binding_digest") == selector["turn_binding_digest"],
        "SELECTOR_TURN_BINDING_MISMATCH",
    )
    _need(resolved.get("required_zero_mode") != "ABSTAIN", "ABSTAINED_INVOCATION_NOT_EXECUTABLE")

    inference = profile.get("inference")
    _need(isinstance(inference, Mapping), "PROFILE_INFERENCE_OBJECT_REQUIRED")
    inference = dict(inference)
    system = prompt.get("system")
    user = prompt.get("user")
    _need(type(system) is str, "PROMPT_SYSTEM_REQUIRED")
    _need(type(user) is str, "PROMPT_USER_REQUIRED")
    profile_id, profile_hash = _profile_identity(profile)

    canonical_state_hash = _digest(compiled.get("canonical_state_hash"), "canonical_state_hash")
    source_packet_hash = _digest(compiled.get("packet_hash"), "source_packet_hash")
    route, route_object = _load_route_capability(
        db,
        entity_generation=selector["expected_generation"],
        jspace_profile_digest=resolved["jspace_profile_digest"],
        inference=inference,
    )

    refs = sorted(
        set(
            list(resolved.get("turn_provenance_refs", []))
            + list(resolved.get("boot_provenance_refs", []))
            + list(resolved.get("activation_provenance_refs", []))
        )
    )
    _need(bool(refs), "COGNITION_PROVENANCE_REQUIRED")
    capsule = capsule_v1.compile_workspace_capsule(
        entity_generation=selector["expected_generation"],
        causal_turn_id=selector["causal_turn_id"],
        task_text=selector["task_text"],
        zero_identity_digest=resolved["zero_identity_digest"],
        grf_digest=resolved["grf_digest"],
        hyperposition_digest=resolved["hyperposition_digest"],
        local_model_digest=resolved["local_model_digest"],
        jacobian_lens_digest=resolved["jacobian_lens_digest"],
        workspace_digest=resolved["workspace_digest"],
        selected_workspace_slots=list(resolved["selected_workspace_slots"]),
        contradiction_state=resolved["contradiction_state"],
        provenance_refs=refs,
        required_zero_mode=resolved["required_zero_mode"],
    )
    packet = packet_v2.compile_packet(
        capsule,
        target_engine_class=route["target_engine_class"],
        jspace_mode=route["jspace_mode"],
        inference=inference,
        system=system,
        user=user,
    )

    receipt = {
        "schema": SCHEMA,
        "generation": selector["expected_generation"],
        "causal_turn_id": selector["causal_turn_id"],
        "turn_binding_digest": resolved["turn_binding_digest"],
        "boot_binding_digest": resolved["boot_binding_digest"],
        "active_turn_activation_digest": resolved["activation_digest"],
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "canonical_state_hash": canonical_state_hash,
        "source_packet_hash": source_packet_hash,
        "workspace_capsule_digest": capsule["capsule_digest"],
        "inference_packet_digest": packet["packet_digest"],
        "route_capability_digest": sha256_obj(route),
        "route_object": route_object,
        "authority": {
            "candidate_inference_only": True,
            "direct_truth_authority": False,
            "direct_state_authority": False,
            "direct_effect_authority": False,
        },
        "admission_effect_executed": False,
    }
    admission_digest = sha256_obj(receipt)
    return {
        "ok": True,
        "schema": SCHEMA,
        "generation": selector["expected_generation"],
        "causal_turn_id": selector["causal_turn_id"],
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": source_packet_hash,
        "inference_packet_digest": packet["packet_digest"],
        "cognitive_fabric_receipt_digest": admission_digest,
        "inference": inference,
        "system": system,
        "user": user,
        "workspace_capsule": capsule,
        "inference_packet": packet,
        "admission_receipt": receipt,
        "route_capability": route,
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_state_authority": False,
            "direct_effect_authority": False,
        },
    }


__all__ = [
    "SCHEMA",
    "ROUTE_SCHEMA",
    "CognitiveAdmissionError",
    "canonical_json",
    "sha256_obj",
    "admit",
]
