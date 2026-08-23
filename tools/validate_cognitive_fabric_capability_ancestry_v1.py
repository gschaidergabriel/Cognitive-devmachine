#!/usr/bin/env python3
"""Fail-closed cross-binding of inference capability evidence into pre-inference UCF admission.

This validator is composition-only. It grants no truth, state, model, J-Space, GWT,
or effect authority. It ensures that a pre-inference Cognitive Fabric admission cannot
launder a different capability receipt into the same engine/J-Space route identity.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_COGNITIVE_FABRIC_CAPABILITY_ANCESTRY/v1"
ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
CAPABILITY_SCHEMA = "MINI_INFERENCE_CAPABILITY_BINDING/v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


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


def validate_capability_ancestry(
    admission: Mapping[str, Any],
    capability: Mapping[str, Any],
) -> dict[str, Any]:
    """Require exact capability evidence identity inside one pre-inference admission."""
    _need(isinstance(admission, Mapping), "ADMISSION_OBJECT_REQUIRED")
    _need(isinstance(capability, Mapping), "CAPABILITY_OBJECT_REQUIRED")
    _need(admission.get("ok") is True, "ADMISSION_NOT_OK")
    _need(admission.get("schema") == ADMISSION_SCHEMA, "ADMISSION_SCHEMA_MISMATCH")
    _need(capability.get("ok") is True, "CAPABILITY_NOT_OK")
    _need(capability.get("schema") == CAPABILITY_SCHEMA, "CAPABILITY_SCHEMA_MISMATCH")

    generation = admission.get("generation")
    _need(type(generation) is int and generation >= 0, "ADMISSION_GENERATION_INVALID")
    profile_id = _text(admission.get("profile_id"), "admission.profile_id")
    profile_hash = _digest(admission.get("profile_hash"), "admission.profile_hash")
    _need(profile_id == _text(capability.get("profile_id"), "capability.profile_id"), "CAPABILITY_PROFILE_ID_MISMATCH")
    _need(profile_hash == _digest(capability.get("profile_hash"), "capability.profile_hash"), "CAPABILITY_PROFILE_HASH_MISMATCH")

    capability_binding_digest = _digest(capability.get("binding_digest"), "capability.binding_digest")
    capability_receipt_digest = _digest(
        capability.get("capability_receipt_digest"), "capability.capability_receipt_digest"
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

    target = _text(capability.get("target_engine_class"), "capability.target_engine_class")
    jspace_mode = _text(capability.get("jspace_mode"), "capability.jspace_mode")
    _need(_text(admission.get("target_engine_class"), "admission.target_engine_class") == target,
          "CAPABILITY_ENGINE_ROUTE_MISMATCH")
    _need(_text(admission.get("jspace_mode"), "admission.jspace_mode") == jspace_mode,
          "CAPABILITY_JSPACE_ROUTE_MISMATCH")

    receipt = admission.get("admission_receipt")
    _need(isinstance(receipt, Mapping), "ADMISSION_RECEIPT_OBJECT_REQUIRED")
    receipt_doc = dict(receipt)
    _need(receipt_doc.get("schema") == ADMISSION_SCHEMA, "ADMISSION_RECEIPT_SCHEMA_MISMATCH")
    _need(receipt_doc.get("generation") == generation, "ADMISSION_RECEIPT_GENERATION_MISMATCH")
    _need(receipt_doc.get("profile_id") == profile_id, "ADMISSION_RECEIPT_PROFILE_ID_MISMATCH")
    _need(receipt_doc.get("profile_hash") == profile_hash, "ADMISSION_RECEIPT_PROFILE_HASH_MISMATCH")
    _need(
        receipt_doc.get("capability_binding_digest") == capability_binding_digest,
        "ADMISSION_RECEIPT_CAPABILITY_BINDING_MISMATCH",
    )
    _need(
        receipt_doc.get("capability_receipt_digest") == capability_receipt_digest,
        "ADMISSION_RECEIPT_CAPABILITY_RECEIPT_MISMATCH",
    )
    _need(receipt_doc.get("target_engine_class") == target, "ADMISSION_RECEIPT_ENGINE_ROUTE_MISMATCH")
    _need(receipt_doc.get("jspace_mode") == jspace_mode, "ADMISSION_RECEIPT_JSPACE_ROUTE_MISMATCH")

    admission_receipt_digest = _digest(
        admission.get("cognitive_fabric_receipt_digest"), "cognitive_fabric_receipt_digest"
    )
    _need(
        admission_receipt_digest == sha256_obj(receipt_doc),
        "ADMISSION_RECEIPT_DIGEST_MISMATCH",
    )
    inference_packet_digest = _digest(
        admission.get("inference_packet_digest"), "inference_packet_digest"
    )
    _need(
        receipt_doc.get("inference_packet_digest") == inference_packet_digest,
        "ADMISSION_PACKET_DIGEST_MISMATCH",
    )

    ancestry = {
        "schema": SCHEMA,
        "generation": generation,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "capability_binding_digest": capability_binding_digest,
        "capability_receipt_digest": capability_receipt_digest,
        "target_engine_class": target,
        "jspace_mode": jspace_mode,
        "inference_packet_digest": inference_packet_digest,
        "cognitive_fabric_admission_receipt_digest": admission_receipt_digest,
        "authority": "PROVENANCE_VALIDATION_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
    }
    return {"ok": True, **ancestry, "ancestry_digest": sha256_obj(ancestry)}


__all__ = [
    "SCHEMA",
    "ADMISSION_SCHEMA",
    "CAPABILITY_SCHEMA",
    "CapabilityAncestryError",
    "canonical_json",
    "sha256_obj",
    "validate_capability_ancestry",
]
