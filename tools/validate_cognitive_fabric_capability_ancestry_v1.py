#!/usr/bin/env python3
"""Fail-closed cross-binding of a bound inference route into pre-inference UCF admission.

This validator is composition-only. It grants no truth, state, model, J-Space, GWT,
or effect authority. It ensures that the exact generation/turn/cognition-bound capability
route survives into the pre-inference Cognitive Fabric admission receipt.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_COGNITIVE_FABRIC_CAPABILITY_ANCESTRY/v1"
ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
BOUND_ROUTE_SCHEMA = "MINI_INFERENCE_BOUND_ROUTE/v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ROUTE_MATERIAL_FIELDS = (
    "schema", "entity_generation", "causal_turn_id", "turn_binding_digest",
    "boot_binding_digest", "workspace_digest", "profile_id", "profile_hash",
    "capability_binding_digest", "capability_receipt_digest", "target_engine_class",
    "ucf_engine_class", "jspace_mode", "cognition",
)


class CapabilityAncestryError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CapabilityAncestryError(message)


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise CapabilityAncestryError("NONCANONICAL_JSON") from exc


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _validate_bound_route(route: Mapping[str, Any]) -> dict[str, Any]:
    _need(isinstance(route, Mapping), "BOUND_ROUTE_OBJECT_REQUIRED")
    _need(route.get("ok") is True, "BOUND_ROUTE_NOT_OK")
    _need(route.get("schema") == BOUND_ROUTE_SCHEMA, "BOUND_ROUTE_SCHEMA_MISMATCH")
    generation = route.get("entity_generation")
    _need(type(generation) is int and generation >= 0, "BOUND_ROUTE_GENERATION_INVALID")
    _text(route.get("causal_turn_id"), "route.causal_turn_id")
    for name in ("turn_binding_digest", "boot_binding_digest", "workspace_digest", "profile_hash",
                 "capability_binding_digest", "capability_receipt_digest"):
        _digest(route.get(name), f"route.{name}")
    for name in ("profile_id", "target_engine_class", "ucf_engine_class", "jspace_mode"):
        _text(route.get(name), f"route.{name}")
    cognition = route.get("cognition")
    _need(isinstance(cognition, Mapping) and bool(cognition), "BOUND_ROUTE_COGNITION_REQUIRED")
    for key, value in cognition.items():
        _text(key, "route.cognition.key")
        _digest(value, f"route.cognition.{key}")
    material = {field: route.get(field) for field in _ROUTE_MATERIAL_FIELDS}
    observed = _digest(route.get("route_digest"), "route.route_digest")
    _need(observed == sha256_obj(material), "BOUND_ROUTE_DIGEST_MISMATCH")
    return {**material, "route_digest": observed}


def validate_capability_ancestry(
    admission: Mapping[str, Any],
    bound_route: Mapping[str, Any],
) -> dict[str, Any]:
    """Require exact bound-route and capability evidence identity inside admission."""
    _need(isinstance(admission, Mapping), "ADMISSION_OBJECT_REQUIRED")
    _need(admission.get("ok") is True, "ADMISSION_NOT_OK")
    _need(admission.get("schema") == ADMISSION_SCHEMA, "ADMISSION_SCHEMA_MISMATCH")
    route = _validate_bound_route(bound_route)

    generation = admission.get("generation")
    _need(type(generation) is int and generation >= 0, "ADMISSION_GENERATION_INVALID")
    _need(generation == route["entity_generation"], "BOUND_ROUTE_GENERATION_MISMATCH")
    profile_id = _text(admission.get("profile_id"), "admission.profile_id")
    profile_hash = _digest(admission.get("profile_hash"), "admission.profile_hash")
    _need(profile_id == route["profile_id"], "BOUND_ROUTE_PROFILE_ID_MISMATCH")
    _need(profile_hash == route["profile_hash"], "BOUND_ROUTE_PROFILE_HASH_MISMATCH")

    route_digest = route["route_digest"]
    capability_binding_digest = route["capability_binding_digest"]
    capability_receipt_digest = route["capability_receipt_digest"]
    _need(
        _digest(admission.get("inference_route_digest"), "admission.inference_route_digest") == route_digest,
        "BOUND_ROUTE_IDENTITY_MISMATCH",
    )
    _need(
        _digest(admission.get("capability_binding_digest"), "admission.capability_binding_digest")
        == capability_binding_digest,
        "CAPABILITY_BINDING_DIGEST_MISMATCH",
    )
    _need(
        _digest(admission.get("capability_receipt_digest"), "admission.capability_receipt_digest")
        == capability_receipt_digest,
        "CAPABILITY_RECEIPT_DIGEST_MISMATCH",
    )
    _need(
        _text(admission.get("target_engine_class"), "admission.target_engine_class")
        == route["target_engine_class"],
        "CAPABILITY_ENGINE_ROUTE_MISMATCH",
    )
    _need(
        _text(admission.get("jspace_mode"), "admission.jspace_mode") == route["jspace_mode"],
        "CAPABILITY_JSPACE_ROUTE_MISMATCH",
    )

    receipt = admission.get("admission_receipt")
    _need(isinstance(receipt, Mapping), "ADMISSION_RECEIPT_OBJECT_REQUIRED")
    receipt_doc = dict(receipt)
    _need(receipt_doc.get("schema") == ADMISSION_SCHEMA, "ADMISSION_RECEIPT_SCHEMA_MISMATCH")
    required_pairs = {
        "generation": generation,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "inference_route_digest": route_digest,
        "capability_binding_digest": capability_binding_digest,
        "capability_receipt_digest": capability_receipt_digest,
        "target_engine_class": route["target_engine_class"],
        "jspace_mode": route["jspace_mode"],
    }
    for key, expected in required_pairs.items():
        _need(receipt_doc.get(key) == expected, f"ADMISSION_RECEIPT_{key.upper()}_MISMATCH")

    admission_receipt_digest = _digest(
        admission.get("cognitive_fabric_receipt_digest"), "cognitive_fabric_receipt_digest"
    )
    _need(admission_receipt_digest == sha256_obj(receipt_doc), "ADMISSION_RECEIPT_DIGEST_MISMATCH")
    inference_packet_digest = _digest(admission.get("inference_packet_digest"), "inference_packet_digest")
    _need(receipt_doc.get("inference_packet_digest") == inference_packet_digest,
          "ADMISSION_PACKET_DIGEST_MISMATCH")

    ancestry = {
        "schema": SCHEMA,
        "generation": generation,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "inference_route_digest": route_digest,
        "capability_binding_digest": capability_binding_digest,
        "capability_receipt_digest": capability_receipt_digest,
        "target_engine_class": route["target_engine_class"],
        "jspace_mode": route["jspace_mode"],
        "inference_packet_digest": inference_packet_digest,
        "cognitive_fabric_admission_receipt_digest": admission_receipt_digest,
        "authority": "PROVENANCE_VALIDATION_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
    }
    return {"ok": True, **ancestry, "ancestry_digest": sha256_obj(ancestry)}


__all__ = [
    "SCHEMA", "ADMISSION_SCHEMA", "BOUND_ROUTE_SCHEMA", "CapabilityAncestryError",
    "canonical_json", "sha256_obj", "validate_capability_ancestry",
]
