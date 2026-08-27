#!/usr/bin/env python3
"""Fail-closed inference capability/J-Space binding for Mini Entity.

This module resolves packet/UCF routing only from an explicit capability binding carried
inside the canonical MiniUnifiedDB profile snapshot. Provider/model names are descriptive
metadata and never grant latent access, truth, state, or effect authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_INFERENCE_CAPABILITY_BINDING/v1"
BOUND_ROUTE_SCHEMA = "MINI_INFERENCE_BOUND_ROUTE/v1"
PREPARE_DIGEST_FIELDS = (
    "zero_identity_digest", "grf_digest", "hyperposition_digest",
    "bundled_manifest_digest", "local_model_digest", "tokenizer_digest",
    "jspace_profile_digest", "jacobian_lens_digest", "workspace_calibration_digest",
    "boot_source_lock_digest", "policy_authority_digest",
)
EVIDENCE_KINDS = {"STATIC_CONSERVATIVE", "BUNDLED_MANIFEST", "RUNTIME_PROBE"}
ENGINE_CLASSES = {"CLAUDE_CODE", "BUNDLED_LOCAL_08B", "ADAPTIVE_BACKEND"}
JSPACE_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY", "COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}
ENGINE_TO_UCF = {
    "CLAUDE_CODE": "claude_code",
    "BUNDLED_LOCAL_08B": "local_08b",
    "ADAPTIVE_BACKEND": "adaptive_backend",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_KEYS = {
    "schema", "binding_id", "engine_class", "jspace_mode", "local_activation_access",
    "external_hidden_state_claimed", "provider_observability_claim_supported",
    "adapter_version", "capability_evidence_kind", "capability_receipt_digest",
    "provenance_refs", "binding_digest",
}


class CapabilityBindingError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CapabilityBindingError(message)


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _bool(value: Any, name: str) -> bool:
    _need(type(value) is bool, f"{name}:BOOL_REQUIRED")
    return value


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CapabilityBindingError("NONCANONICAL_JSON") from exc


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def compile_binding(*, binding_id: str, engine_class: str, jspace_mode: str,
                    local_activation_access: bool, external_hidden_state_claimed: bool,
                    provider_observability_claim_supported: bool, adapter_version: str,
                    capability_evidence_kind: str, capability_receipt_digest: str,
                    provenance_refs: list[str]) -> dict[str, Any]:
    doc = {
        "schema": SCHEMA,
        "binding_id": binding_id,
        "engine_class": engine_class,
        "jspace_mode": jspace_mode,
        "local_activation_access": local_activation_access,
        "external_hidden_state_claimed": external_hidden_state_claimed,
        "provider_observability_claim_supported": provider_observability_claim_supported,
        "adapter_version": adapter_version,
        "capability_evidence_kind": capability_evidence_kind,
        "capability_receipt_digest": capability_receipt_digest,
        "provenance_refs": provenance_refs,
    }
    doc["binding_digest"] = sha256_obj(doc)
    validate_binding(doc)
    return doc


def validate_binding(doc: Mapping[str, Any]) -> dict[str, Any]:
    _need(isinstance(doc, Mapping), "CAPABILITY_BINDING_OBJECT_REQUIRED")
    value = dict(doc)
    _need(set(value) == _KEYS, "CAPABILITY_BINDING_FIELDS_MISMATCH")
    _need(value.get("schema") == SCHEMA, "CAPABILITY_BINDING_SCHEMA_MISMATCH")
    _text(value.get("binding_id"), "binding_id")
    engine = _text(value.get("engine_class"), "engine_class")
    mode = _text(value.get("jspace_mode"), "jspace_mode")
    _need(engine in ENGINE_CLASSES, "ENGINE_CLASS_UNSUPPORTED")
    _need(mode in JSPACE_MODES, "JSPACE_MODE_UNSUPPORTED")
    local_access = _bool(value.get("local_activation_access"), "local_activation_access")
    hidden_claim = _bool(value.get("external_hidden_state_claimed"), "external_hidden_state_claimed")
    observability = _bool(value.get("provider_observability_claim_supported"), "provider_observability_claim_supported")
    _need(observability, "PROVIDER_OBSERVABILITY_CLAIM_UNSUPPORTED")
    _text(value.get("adapter_version"), "adapter_version")
    evidence_kind = _text(value.get("capability_evidence_kind"), "capability_evidence_kind")
    _need(evidence_kind in EVIDENCE_KINDS, "CAPABILITY_EVIDENCE_KIND_UNSUPPORTED")
    _digest(value.get("capability_receipt_digest"), "capability_receipt_digest")
    refs = value.get("provenance_refs")
    _need(type(refs) is list and bool(refs), "PROVENANCE_REFS_REQUIRED")
    normalized_refs = [_text(item, "provenance_ref") for item in refs]
    _need(len(normalized_refs) == len(set(normalized_refs)), "PROVENANCE_REFS_DUPLICATE")

    if hidden_claim:
        raise CapabilityBindingError("EXTERNAL_HIDDEN_STATE_CLAIM_FORBIDDEN")

    if mode in {"COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}:
        _need(not local_access, "EXTERNAL_MODE_CANNOT_CLAIM_LOCAL_ACTIVATION_ACCESS")
    else:
        _need(local_access, "LOCAL_JSPACE_REQUIRES_ACTIVATION_ACCESS")
        _need(evidence_kind in {"BUNDLED_MANIFEST", "RUNTIME_PROBE"}, "LOCAL_JSPACE_REQUIRES_MEASURED_OR_MANIFEST_EVIDENCE")

    if engine == "CLAUDE_CODE":
        _need(mode == "COMPILED_EXTERNAL", "CLAUDE_MUST_BE_COMPILED_EXTERNAL")
        _need(not local_access, "CLAUDE_LOCAL_ACTIVATION_CLAIM_FORBIDDEN")
    elif engine == "BUNDLED_LOCAL_08B":
        _need(mode in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"}, "LOCAL_08B_JSPACE_MODE_INVALID")
        _need(evidence_kind in {"BUNDLED_MANIFEST", "RUNTIME_PROBE"}, "LOCAL_08B_CAPABILITY_EVIDENCE_REQUIRED")
    elif evidence_kind == "STATIC_CONSERVATIVE":
        _need(mode in {"COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}, "STATIC_CAPABILITY_CANNOT_AUTHORIZE_LOCAL_LATENT")

    observed = _digest(value.get("binding_digest"), "binding_digest")
    unsigned = dict(value)
    unsigned.pop("binding_digest")
    _need(observed == sha256_obj(unsigned), "CAPABILITY_BINDING_DIGEST_MISMATCH")
    return {
        "ok": True,
        "schema": SCHEMA,
        "binding_digest": observed,
        "target_engine_class": engine,
        "ucf_engine_class": ENGINE_TO_UCF[engine],
        "jspace_mode": mode,
        "local_activation_access": local_access,
        "external_hidden_state_claimed": hidden_claim,
        "provider_observability_claim_supported": observability,
        "adapter_version": value["adapter_version"],
        "capability_receipt_digest": value["capability_receipt_digest"],
        "capability_evidence_kind": evidence_kind,
        "authority": "ROUTING_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
    }


def resolve_from_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve only an explicit binding from a verified runtime profile snapshot.

    The caller must have obtained this profile through the canonical MiniUnifiedDB profile
    read path. Model/provider/kind strings are intentionally ignored for capability routing.
    """
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")
    snapshot = profile.get("_runtime_profile_snapshot")
    _need(isinstance(snapshot, Mapping), "PROFILE_SNAPSHOT_MISSING")
    _text(snapshot.get("profile_id"), "profile_snapshot.profile_id")
    _digest(snapshot.get("profile_hash"), "profile_snapshot.profile_hash")
    inference = profile.get("inference")
    _need(isinstance(inference, Mapping), "PROFILE_INFERENCE_OBJECT_REQUIRED")
    binding = inference.get("capability_binding")
    _need(isinstance(binding, Mapping), "INFERENCE_CAPABILITY_BINDING_REQUIRED")
    result = validate_binding(binding)
    result.update({
        "profile_id": str(snapshot["profile_id"]),
        "profile_hash": str(snapshot["profile_hash"]),
    })
    return result


def resolve_bound_route(profile: Mapping[str, Any], prepare: Mapping[str, Any], *, expected_generation: int) -> dict[str, Any]:
    """Bind explicit capability routing to one exact canonical cognition prepare result.

    Cognition identities are not duplicated into profile configuration. They are taken only
    from the already-verified MiniUnifiedDB prepare material and folded into one route digest.
    """
    _need(isinstance(prepare, Mapping) and prepare.get("ok") is True, "PREPARE_BINDING_REQUIRED")
    _need(type(expected_generation) is int and expected_generation >= 0, "EXPECTED_GENERATION_INVALID")
    _need(prepare.get("entity_generation") == expected_generation, "STALE_GENERATION")
    causal_turn_id = _text(prepare.get("causal_turn_id"), "prepare.causal_turn_id")
    turn_binding_digest = _digest(prepare.get("turn_binding_digest"), "prepare.turn_binding_digest")
    boot_binding_digest = _digest(prepare.get("boot_binding_digest"), "prepare.boot_binding_digest")
    workspace_digest = _digest(prepare.get("workspace_digest"), "prepare.workspace_digest")
    cognition = {field: _digest(prepare.get(field), f"prepare.{field}") for field in PREPARE_DIGEST_FIELDS}

    capability = resolve_from_profile(profile)
    material = {
        "schema": BOUND_ROUTE_SCHEMA,
        "entity_generation": expected_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": turn_binding_digest,
        "boot_binding_digest": boot_binding_digest,
        "workspace_digest": workspace_digest,
        "profile_id": capability["profile_id"],
        "profile_hash": capability["profile_hash"],
        "capability_binding_digest": capability["binding_digest"],
        "capability_receipt_digest": capability["capability_receipt_digest"],
        "target_engine_class": capability["target_engine_class"],
        "ucf_engine_class": capability["ucf_engine_class"],
        "jspace_mode": capability["jspace_mode"],
        "cognition": cognition,
    }
    route_digest = sha256_obj(material)
    return {
        "ok": True,
        **material,
        "route_digest": route_digest,
        "local_activation_access": capability["local_activation_access"],
        "external_hidden_state_claimed": capability["external_hidden_state_claimed"],
        "provider_observability_claim_supported": capability["provider_observability_claim_supported"],
        "adapter_version": capability["adapter_version"],
        "capability_evidence_kind": capability["capability_evidence_kind"],
        "authority": "ROUTING_ONLY_BOUND_TO_CANONICAL_PREPARE",
    }


__all__ = ["SCHEMA", "BOUND_ROUTE_SCHEMA", "PREPARE_DIGEST_FIELDS", "CapabilityBindingError", "compile_binding", "validate_binding", "resolve_from_profile", "resolve_bound_route", "sha256_obj"]
