#!/usr/bin/env python3
"""Fail-closed cognition engine/J-Space route resolver.

This module creates no state, truth, identity, recovery, or effect authority. It only
resolves explicit DB-resident profile routing against already-verified MiniUnifiedDB
cognition prepare material. Provider/model names are never used to infer latent access.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_COGNITIVE_ENGINE_ROUTE/v1"
ROUTE_SCHEMA = "MINI_COGNITIVE_ENGINE_ROUTE_CONFIG/v1"
TARGETS = {"CLAUDE_CODE", "BUNDLED_LOCAL_08B", "ADAPTIVE_BACKEND"}
JSPACE_MODES = {
    "FULL_LOCAL_LATENT",
    "LOCAL_OBSERVE_ONLY",
    "COMPILED_EXTERNAL",
    "PLAIN_COMPATIBILITY",
}
ROUTE_KEYS = {
    "schema",
    "target_engine_class",
    "jspace_mode",
    "bundled_manifest_digest",
    "local_model_digest",
    "tokenizer_digest",
    "jspace_profile_digest",
    "jacobian_lens_digest",
    "workspace_calibration_digest",
}
DIGEST_BINDINGS = {
    "bundled_manifest_digest": "bundled_manifest_digest",
    "local_model_digest": "local_model_digest",
    "tokenizer_digest": "tokenizer_digest",
    "jspace_profile_digest": "jspace_profile_digest",
    "jacobian_lens_digest": "jacobian_lens_digest",
    "workspace_calibration_digest": "workspace_calibration_digest",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CognitiveEngineRouteError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitiveEngineRouteError(message)


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(len(set(value)) > 1, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CognitiveEngineRouteError("NON_CANONICAL_ROUTE") from exc


def _sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def resolve_engine_route(
    profile: Mapping[str, Any],
    prepare: Mapping[str, Any],
    *,
    expected_generation: int,
) -> dict[str, Any]:
    """Resolve one explicit profile route against exact cognition ancestry.

    `prepare` is expected to come from the same-MiniUnifiedDB active-turn/cognition
    resolver. This function does not query a second store and does not invent routing
    capability from provider or model strings.
    """
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")
    _need(isinstance(prepare, Mapping) and prepare.get("ok") is True, "PREPARE_BINDING_REQUIRED")
    _need(type(expected_generation) is int and expected_generation >= 0, "GENERATION_INVALID")
    _need(prepare.get("entity_generation") == expected_generation, "STALE_GENERATION")

    profile_id = _text(profile.get("profile_id"), "profile_id")
    snapshot = profile.get("_runtime_profile_snapshot")
    _need(isinstance(snapshot, Mapping), "PROFILE_SNAPSHOT_REQUIRED")
    _need(_text(snapshot.get("profile_id"), "snapshot_profile_id") == profile_id, "PROFILE_ID_MISMATCH")
    profile_hash = _digest(snapshot.get("profile_hash"), "profile_hash")

    inference = profile.get("inference")
    _need(isinstance(inference, Mapping), "INFERENCE_PROFILE_REQUIRED")
    route = inference.get("cognitive_engine_route")
    _need(isinstance(route, Mapping), "EXPLICIT_COGNITIVE_ENGINE_ROUTE_REQUIRED")
    _need(set(route) == ROUTE_KEYS, "COGNITIVE_ENGINE_ROUTE_FIELDS_MISMATCH")
    _need(route.get("schema") == ROUTE_SCHEMA, "COGNITIVE_ENGINE_ROUTE_SCHEMA_MISMATCH")

    target = _text(route.get("target_engine_class"), "target_engine_class")
    mode = _text(route.get("jspace_mode"), "jspace_mode")
    _need(target in TARGETS, "TARGET_ENGINE_UNSUPPORTED")
    _need(mode in JSPACE_MODES, "JSPACE_MODE_UNSUPPORTED")
    if target == "CLAUDE_CODE":
        _need(mode == "COMPILED_EXTERNAL", "CLAUDE_MUST_BE_COMPILED_EXTERNAL")
    if target == "BUNDLED_LOCAL_08B":
        _need(
            mode in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"},
            "LOCAL_08B_JSPACE_MODE_INVALID",
        )

    bound_digests: dict[str, str] = {}
    for route_key, prepare_key in DIGEST_BINDINGS.items():
        configured = _digest(route.get(route_key), route_key)
        admitted = _digest(prepare.get(prepare_key), prepare_key)
        _need(configured == admitted, f"COGNITION_ROUTE_BINDING_MISMATCH:{route_key}")
        bound_digests[route_key] = admitted

    for name in ("turn_binding_digest", "boot_binding_digest", "workspace_digest"):
        _digest(prepare.get(name), name)
    causal_turn_id = _text(prepare.get("causal_turn_id"), "causal_turn_id")

    inference_copy = json.loads(_canonical(dict(inference)))
    material = {
        "schema": SCHEMA,
        "entity_generation": expected_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": prepare["turn_binding_digest"],
        "boot_binding_digest": prepare["boot_binding_digest"],
        "workspace_digest": prepare["workspace_digest"],
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "target_engine_class": target,
        "jspace_mode": mode,
        "cognition_digests": bound_digests,
        "inference_digest": _sha256_obj(inference_copy),
        "authority": {
            "routing_only": True,
            "durable_state": "MiniUnifiedDB",
            "candidate_inference_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
    }
    route_digest = _sha256_obj(material)
    return {
        "ok": True,
        **material,
        "route_digest": route_digest,
        "inference": inference_copy,
    }


__all__ = [
    "SCHEMA",
    "ROUTE_SCHEMA",
    "TARGETS",
    "JSPACE_MODES",
    "CognitiveEngineRouteError",
    "resolve_engine_route",
]
