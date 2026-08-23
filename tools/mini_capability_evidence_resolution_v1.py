#!/usr/bin/env python3
"""Bind local inference capability claims to the canonical UCF semantic binding.

This module creates no durable state, truth authority, effect authority, model authority,
or second cognition resolver. It consumes the exact semantic binding already produced by
the single pre-inference UCF compositor and decides only whether that evidence can support
a local-latent routing claim.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_CAPABILITY_EVIDENCE_RESOLUTION/v1"
SEMANTIC_SCHEMA = "MINI_ENTITY_COGNITION_SEMANTIC_BINDING/v1"
LOCAL_JSPACE_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"}
_BOOT_OBJECT_KINDS = {
    "zero_identity_digest": "ZERO_IDENTITY",
    "grf_digest": "GRF",
    "hyperposition_digest": "HYPERPOSITION",
    "bundled_manifest_digest": "BUNDLED_MANIFEST",
    "local_model_digest": "LOCAL_MODEL_CHECKPOINT",
    "tokenizer_digest": "TOKENIZER",
    "jspace_profile_digest": "JSPACE_PROFILE",
    "jacobian_lens_digest": "JACOBIAN_LENS_PROFILE",
    "workspace_calibration_digest": "WORKSPACE_CALIBRATION",
    "boot_source_lock_digest": "BOOT_SOURCE_LOCK",
    "policy_authority_digest": "POLICY_AUTHORITY",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CapabilityEvidenceError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CapabilityEvidenceError(message)


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise CapabilityEvidenceError("NONCANONICAL_JSON") from exc


def _sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _verify_semantic_binding(
    semantic_binding: Mapping[str, Any],
    *,
    prepare: Mapping[str, Any],
    expected_generation: int,
) -> tuple[str, Mapping[str, Any]]:
    _need(semantic_binding.get("schema") == SEMANTIC_SCHEMA, "SEMANTIC_BINDING_SCHEMA_MISMATCH")
    _need(
        semantic_binding.get("authority") == "VERSION_BINDING_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
        "SEMANTIC_BINDING_AUTHORITY_ESCALATION",
    )
    observed = _digest(semantic_binding.get("semantic_binding_digest"), "semantic_binding_digest")
    unsigned = dict(semantic_binding)
    unsigned.pop("semantic_binding_digest", None)
    _need(_sha256_obj(unsigned) == observed, "SEMANTIC_BINDING_DIGEST_MISMATCH")
    _need(semantic_binding.get("entity_generation") == expected_generation, "SEMANTIC_GENERATION_DRIFT")
    _need(semantic_binding.get("causal_turn_id") == prepare.get("causal_turn_id"), "SEMANTIC_TURN_DRIFT")
    _need(
        semantic_binding.get("turn_binding_digest") == prepare.get("turn_binding_digest"),
        "SEMANTIC_TURN_BINDING_DRIFT",
    )
    _need(
        semantic_binding.get("boot_binding_digest") == prepare.get("boot_binding_digest"),
        "SEMANTIC_BOOT_BINDING_DRIFT",
    )
    _need(semantic_binding.get("workspace_digest") == prepare.get("workspace_digest"), "SEMANTIC_WORKSPACE_DRIFT")
    objects = semantic_binding.get("objects")
    _need(isinstance(objects, Mapping), "SEMANTIC_OBJECTS_REQUIRED")
    _need(set(objects) == set(_BOOT_OBJECT_KINDS), "SEMANTIC_OBJECT_SET_MISMATCH")
    for field, expected_kind in _BOOT_OBJECT_KINDS.items():
        obj = objects.get(field)
        _need(isinstance(obj, Mapping), f"SEMANTIC_OBJECT_REQUIRED:{field}")
        _need(obj.get("object_kind") == expected_kind, f"SEMANTIC_OBJECT_KIND_DRIFT:{field}")
        _text(obj.get("object_version"), f"semantic.{field}.object_version")
        _need(obj.get("object_digest") == prepare.get(field), f"SEMANTIC_OBJECT_DIGEST_DRIFT:{field}")
        _digest(obj.get("payload_digest"), f"semantic.{field}.payload_digest")
        _digest(obj.get("admission_receipt_digest"), f"semantic.{field}.admission_receipt_digest")
    return observed, objects


def resolve_capability_evidence(
    *,
    prepare: Mapping[str, Any],
    semantic_binding: Mapping[str, Any] | None,
    capability: Mapping[str, Any],
    expected_generation: int,
) -> dict[str, Any]:
    """Resolve route evidence without re-reading MiniUnifiedDB or minting authority."""
    _need(isinstance(prepare, Mapping) and prepare.get("ok") is True, "PREPARE_BINDING_REQUIRED")
    _need(isinstance(capability, Mapping) and capability.get("ok") is True, "CAPABILITY_BINDING_REQUIRED")
    _need(type(expected_generation) is int and expected_generation >= 0, "EXPECTED_GENERATION_INVALID")
    _need(prepare.get("entity_generation") == expected_generation, "STALE_GENERATION")

    causal_turn_id = _text(prepare.get("causal_turn_id"), "prepare.causal_turn_id")
    turn_binding_digest = _digest(prepare.get("turn_binding_digest"), "prepare.turn_binding_digest")
    boot_binding_digest = _digest(prepare.get("boot_binding_digest"), "prepare.boot_binding_digest")
    workspace_digest = _digest(prepare.get("workspace_digest"), "prepare.workspace_digest")
    binding_digest = _digest(capability.get("binding_digest"), "capability_binding_digest")
    evidence_kind = _text(capability.get("capability_evidence_kind"), "capability_evidence_kind")
    receipt_digest = _digest(capability.get("capability_receipt_digest"), "capability_receipt_digest")
    engine_class = _text(capability.get("target_engine_class"), "target_engine_class")
    jspace_mode = _text(capability.get("jspace_mode"), "jspace_mode")
    local_access = capability.get("local_activation_access")
    _need(type(local_access) is bool, "local_activation_access:BOOL_REQUIRED")

    if jspace_mode not in LOCAL_JSPACE_MODES:
        _need(not local_access, "NONLOCAL_MODE_CANNOT_CLAIM_LOCAL_ACTIVATION")
        material = {
            "schema": SCHEMA,
            "entity_generation": expected_generation,
            "causal_turn_id": causal_turn_id,
            "turn_binding_digest": turn_binding_digest,
            "boot_binding_digest": boot_binding_digest,
            "workspace_digest": workspace_digest,
            "capability_binding_digest": binding_digest,
            "capability_evidence_kind": evidence_kind,
            "capability_receipt_digest": receipt_digest,
            "semantic_binding_digest": None,
            "resolution": "NONLOCAL_NO_LATENT_AUTHORITY",
        }
        return {
            "ok": True,
            **material,
            "evidence_binding_digest": _sha256_obj(material),
            "authority": "EVIDENCE_BINDING_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
        }

    _need(local_access, "LOCAL_JSPACE_REQUIRES_ACTIVATION_ACCESS")
    _need(engine_class == "BUNDLED_LOCAL_08B", "LOCAL_LATENT_ENGINE_NOT_CANONICALLY_SUPPORTED")
    if evidence_kind == "RUNTIME_PROBE":
        raise CapabilityEvidenceError("RUNTIME_PROBE_EVIDENCE_NOT_CANONICALLY_RESOLVED")
    _need(evidence_kind == "BUNDLED_MANIFEST", "LOCAL_LATENT_EVIDENCE_KIND_UNSUPPORTED")
    _need(isinstance(semantic_binding, Mapping), "LOCAL_LATENT_SEMANTIC_BINDING_REQUIRED")

    semantic_digest, objects = _verify_semantic_binding(
        semantic_binding,
        prepare=prepare,
        expected_generation=expected_generation,
    )
    manifest = objects["bundled_manifest_digest"]
    manifest_receipt = _digest(
        manifest.get("admission_receipt_digest"),
        "bundled_manifest.admission_receipt_digest",
    )
    _need(
        receipt_digest == manifest_receipt,
        "CAPABILITY_RECEIPT_NOT_CURRENT_BUNDLED_MANIFEST_ADMISSION",
    )

    material = {
        "schema": SCHEMA,
        "entity_generation": expected_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": turn_binding_digest,
        "boot_binding_digest": boot_binding_digest,
        "workspace_digest": workspace_digest,
        "capability_binding_digest": binding_digest,
        "capability_evidence_kind": evidence_kind,
        "capability_receipt_digest": receipt_digest,
        "semantic_binding_digest": semantic_digest,
        "bundled_manifest_digest": prepare.get("bundled_manifest_digest"),
        "bundled_manifest_object_version": _text(manifest.get("object_version"), "bundled_manifest.object_version"),
        "bundled_manifest_payload_digest": _digest(manifest.get("payload_digest"), "bundled_manifest.payload_digest"),
        "resolution": "CURRENT_SEMANTIC_BINDING_BUNDLED_MANIFEST_ADMISSION",
    }
    return {
        "ok": True,
        **material,
        "evidence_binding_digest": _sha256_obj(material),
        "authority": "EVIDENCE_BINDING_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
    }


__all__ = ["SCHEMA", "LOCAL_JSPACE_MODES", "CapabilityEvidenceError", "resolve_capability_evidence"]
