#!/usr/bin/env python3
"""Resolve inference capability evidence against canonical MiniUnifiedDB cognition ancestry.

This module is read-only. It authenticates a capability-evidence digest to the exact
live-generation cognition objects already admitted in MiniUnifiedDB before a local
J-Space route may be materialized. It creates no state, truth, inference, or effect
authority.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Mapping
from typing import Any

import miniunifieddb_cognition_resolution_v1 as cognition_resolution

SCHEMA = "MINI_INFERENCE_CAPABILITY_EVIDENCE/v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_PREPARE_OBJECT_FIELDS = (
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


class CapabilityEvidenceError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CapabilityEvidenceError(message)


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(len(set(value)) > 1, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


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
        raise CapabilityEvidenceError("NONCANONICAL_JSON") from exc


def _sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def resolve_capability_evidence(
    db: sqlite3.Connection,
    *,
    capability: Mapping[str, Any],
    prepare: Mapping[str, Any],
    expected_generation: int,
    semantic_resolver: Any | None = None,
) -> dict[str, Any]:
    """Authenticate one capability receipt to exact live MiniUnifiedDB evidence.

    `BUNDLED_MANIFEST` is admitted only when the capability receipt is exactly the
    admission receipt of the boot-bound BUNDLED_MANIFEST cognition object in the live
    generation, and every boot object digest resolves unambiguously to the same turn.

    `RUNTIME_PROBE` remains fail-closed until a typed runtime-probe object/receipt exists
    in MiniUnifiedDB; accepting an opaque 64-hex value would recreate the authority gap
    this resolver exists to close.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(isinstance(capability, Mapping), "CAPABILITY_OBJECT_REQUIRED")
    _need(isinstance(prepare, Mapping) and prepare.get("ok") is True, "PREPARE_BINDING_REQUIRED")
    _need(type(expected_generation) is int and expected_generation >= 0, "EXPECTED_GENERATION_INVALID")
    _need(prepare.get("entity_generation") == expected_generation, "STALE_GENERATION")

    evidence_kind = _text(capability.get("capability_evidence_kind"), "capability_evidence_kind")
    capability_receipt_digest = _digest(
        capability.get("capability_receipt_digest"), "capability_receipt_digest"
    )
    capability_binding_digest = _digest(
        capability.get("binding_digest"), "capability_binding_digest"
    )
    causal_turn_id = _text(prepare.get("causal_turn_id"), "prepare.causal_turn_id")
    task_text = prepare.get("task_text")
    _need(type(task_text) is str, "PREPARE_TASK_TEXT_REQUIRED")
    turn_binding_digest = _digest(prepare.get("turn_binding_digest"), "prepare.turn_binding_digest")
    boot_binding_digest = _digest(prepare.get("boot_binding_digest"), "prepare.boot_binding_digest")

    if evidence_kind == "STATIC_CONSERVATIVE":
        raise CapabilityEvidenceError("STATIC_EVIDENCE_CANNOT_AUTHORIZE_LOCAL_ROUTE")
    if evidence_kind == "RUNTIME_PROBE":
        raise CapabilityEvidenceError("RUNTIME_PROBE_TYPED_EVIDENCE_NOT_ADMITTED")
    _need(evidence_kind == "BUNDLED_MANIFEST", "CAPABILITY_EVIDENCE_KIND_UNSUPPORTED")

    resolver = semantic_resolver or cognition_resolution
    try:
        bundle = resolver.resolve_prepare_bundle(
            db,
            entity_generation=expected_generation,
            causal_turn_id=causal_turn_id,
            task_text=task_text,
            expected_turn_binding_digest=turn_binding_digest,
        )
    except Exception as exc:
        if isinstance(exc, CapabilityEvidenceError):
            raise
        raise CapabilityEvidenceError(
            "CAPABILITY_EVIDENCE_SEMANTIC_RESOLUTION_FAILED:"
            + type(exc).__name__
            + ":"
            + str(exc)
        ) from exc

    _need(isinstance(bundle, Mapping) and bundle.get("ok") is True, "SEMANTIC_BUNDLE_REQUIRED")
    _need(bundle.get("entity_generation") == expected_generation, "SEMANTIC_BUNDLE_STALE_GENERATION")
    _need(bundle.get("causal_turn_id") == causal_turn_id, "SEMANTIC_BUNDLE_TURN_DRIFT")
    _need(bundle.get("turn_binding_digest") == turn_binding_digest, "SEMANTIC_BUNDLE_TURN_BINDING_DRIFT")
    _need(bundle.get("boot_binding_digest") == boot_binding_digest, "SEMANTIC_BUNDLE_BOOT_BINDING_DRIFT")
    authority = bundle.get("authority")
    _need(
        isinstance(authority, Mapping)
        and authority.get("durable_state") == "MiniUnifiedDB"
        and authority.get("routing_only") is True
        and authority.get("direct_truth_authority") is False
        and authority.get("direct_effect_authority") is False,
        "SEMANTIC_BUNDLE_AUTHORITY_ESCALATION",
    )

    objects = bundle.get("objects")
    _need(isinstance(objects, Mapping), "SEMANTIC_OBJECTS_REQUIRED")
    object_receipts: dict[str, str] = {}
    cognition: dict[str, str] = {}
    for field in _PREPARE_OBJECT_FIELDS:
        expected_digest = _digest(prepare.get(field), f"prepare.{field}")
        obj = objects.get(field)
        _need(isinstance(obj, Mapping), f"SEMANTIC_OBJECT_MISSING:{field}")
        _need(obj.get("admitted_generation") == expected_generation, f"SEMANTIC_OBJECT_STALE:{field}")
        observed_digest = _digest(obj.get("object_digest"), f"semantic.{field}.object_digest")
        _need(observed_digest == expected_digest, f"SEMANTIC_OBJECT_DIGEST_DRIFT:{field}")
        object_receipts[field] = _digest(
            obj.get("admission_receipt_digest"), f"semantic.{field}.admission_receipt_digest"
        )
        cognition[field] = expected_digest

    manifest_receipt = object_receipts["bundled_manifest_digest"]
    _need(
        capability_receipt_digest == manifest_receipt,
        "CAPABILITY_RECEIPT_NOT_CURRENT_BUNDLED_MANIFEST_ADMISSION",
    )

    material = {
        "schema": SCHEMA,
        "entity_generation": expected_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": turn_binding_digest,
        "boot_binding_digest": boot_binding_digest,
        "capability_binding_digest": capability_binding_digest,
        "capability_evidence_kind": evidence_kind,
        "capability_receipt_digest": capability_receipt_digest,
        "cognition": cognition,
        "object_admission_receipts": object_receipts,
        "authority": "READ_ONLY_MINIUNIFIEDDB_CAPABILITY_EVIDENCE",
    }
    evidence_binding_digest = _sha256_obj(material)
    return {
        "ok": True,
        **material,
        "evidence_binding_digest": evidence_binding_digest,
        "direct_truth_authority": False,
        "direct_effect_authority": False,
    }


__all__ = [
    "SCHEMA",
    "CapabilityEvidenceError",
    "resolve_capability_evidence",
]
