#!/usr/bin/env python3
"""Read-only causal resolver for Mini Entity inference-capability evidence.

A profile-carried SHA-256 is not evidence by itself. This resolver proves (or
rejects) the referent for local J-Space capability against the current
MiniUnifiedDB generation and exact cognition boot binding. It grants no truth,
state-write, or effect authority.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_CAPABILITY_EVIDENCE_RESOLUTION/v1"
LOCAL_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_BOOT_FIELDS = (
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


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


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
        raise CapabilityEvidenceError("NONCANONICAL_JSON") from exc


def _sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _live_generation(db: sqlite3.Connection) -> int:
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    except sqlite3.Error as exc:
        raise CapabilityEvidenceError("ENTITY_STATE_UNAVAILABLE") from exc
    _need(row is not None, "ENTITY_STATE_UNAVAILABLE")
    generation = row[0]
    _need(type(generation) is int and generation >= 0, "ENTITY_GENERATION_INVALID")
    return generation


def _boot_material(db: sqlite3.Connection, *, prepare: Mapping[str, Any],
                   expected_generation: int) -> dict[str, Any]:
    binding_digest = _digest(prepare.get("boot_binding_digest"), "prepare.boot_binding_digest")
    try:
        row = db.execute(
            """SELECT schema,entity_generation,zero_identity_digest,grf_digest,
                      hyperposition_digest,bundled_manifest_digest,local_model_digest,
                      tokenizer_digest,jspace_profile_digest,jacobian_lens_digest,
                      workspace_calibration_digest,boot_source_lock_digest,
                      policy_authority_digest,provenance_refs_json
                 FROM mini_cognition_boot_bindings
                WHERE binding_digest=? AND entity_generation=?""",
            (binding_digest, expected_generation),
        ).fetchone()
    except sqlite3.Error as exc:
        raise CapabilityEvidenceError("BOOT_BINDING_STORE_UNAVAILABLE") from exc
    _need(row is not None, "BOOT_BINDING_UNAVAILABLE")
    _need(row[0] == "MINIUNIFIEDDB_COGNITION_BOOT_BINDING/v1", "BOOT_BINDING_SCHEMA_MISMATCH")
    _need(type(row[1]) is int and row[1] == expected_generation, "BOOT_BINDING_STALE_GENERATION")
    fields = {name: _digest(row[index], f"boot.{name}") for index, name in enumerate(_BOOT_FIELDS, start=2)}
    for name in _BOOT_FIELDS:
        _need(_digest(prepare.get(name), f"prepare.{name}") == fields[name], f"BOOT_PREPARE_MISMATCH:{name}")
    try:
        refs = json.loads(str(row[13]))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CapabilityEvidenceError("BOOT_PROVENANCE_JSON_INVALID") from exc
    _need(type(refs) is list and all(type(item) is str and item for item in refs), "BOOT_PROVENANCE_INVALID")
    _need(len(refs) == len(set(refs)), "BOOT_PROVENANCE_DUPLICATE")
    material = {
        "schema": "MINIUNIFIEDDB_COGNITION_BOOT_BINDING/v1",
        "entity_generation": expected_generation,
        **fields,
        "provenance_refs": refs,
    }
    _need(_sha256_obj(material) == binding_digest, "BOOT_BINDING_DIGEST_MISMATCH")
    return {**material, "binding_digest": binding_digest}


def _resolve_manifest_admission(db: sqlite3.Connection, *, manifest_digest: str,
                                expected_generation: int,
                                capability_receipt_digest: str) -> dict[str, Any]:
    try:
        rows = db.execute(
            """SELECT o.object_version,o.digest_basis,o.payload_json,o.payload_digest,
                      a.admission_receipt_digest
                 FROM mini_cognition_objects o
                 JOIN mini_cognition_object_admissions a
                   ON a.object_kind=o.object_kind
                  AND a.object_version=o.object_version
                  AND a.object_digest=o.object_digest
                WHERE o.object_kind='BUNDLED_MANIFEST'
                  AND o.object_digest=?
                  AND a.admitted_generation=?
                ORDER BY o.object_version""",
            (manifest_digest, expected_generation),
        ).fetchall()
    except sqlite3.Error as exc:
        raise CapabilityEvidenceError("COGNITION_OBJECT_STORE_UNAVAILABLE") from exc
    _need(bool(rows), "BUNDLED_MANIFEST_NOT_ADMITTED_CURRENT_GENERATION")
    _need(len(rows) == 1, "CAPABILITY_OBJECT_VERSION_AMBIGUOUS")
    row = rows[0]
    version = _text(row[0], "manifest.object_version")
    _need(row[1] == "CANONICAL_JSON", "BUNDLED_MANIFEST_DIGEST_BASIS_UNSUPPORTED")
    payload_json = str(row[2])
    payload_digest = _digest(row[3], "manifest.payload_digest")
    _need(hashlib.sha256(payload_json.encode("utf-8")).hexdigest() == payload_digest,
          "BUNDLED_MANIFEST_PAYLOAD_DIGEST_MISMATCH")
    _need(payload_digest == manifest_digest, "BUNDLED_MANIFEST_OBJECT_DIGEST_MISMATCH")
    admitted_receipt = _digest(row[4], "manifest.admission_receipt_digest")
    _need(admitted_receipt == capability_receipt_digest, "CAPABILITY_RECEIPT_REFERENT_MISMATCH")
    return {
        "object_kind": "BUNDLED_MANIFEST",
        "object_version": version,
        "object_digest": manifest_digest,
        "admission_receipt_digest": admitted_receipt,
    }


def resolve_bound_evidence(db: sqlite3.Connection, *, route: Mapping[str, Any],
                           prepare: Mapping[str, Any],
                           expected_generation: int) -> dict[str, Any]:
    """Resolve capability evidence without mutating MiniUnifiedDB.

    External/compatibility modes do not claim local activation access and therefore
    do not need a local-capability referent. Local modes are admitted only when the
    capability receipt resolves to the exact current-generation bundled manifest.
    RUNTIME_PROBE stays blocked until a typed runtime-probe receipt exists.
    """
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(isinstance(route, Mapping) and route.get("ok") is True, "BOUND_ROUTE_REQUIRED")
    _need(isinstance(prepare, Mapping) and prepare.get("ok") is True, "PREPARE_REQUIRED")
    _need(type(expected_generation) is int and expected_generation >= 0, "EXPECTED_GENERATION_INVALID")
    _need(_live_generation(db) == expected_generation, "STALE_GENERATION")
    _need(route.get("entity_generation") == expected_generation, "ROUTE_GENERATION_MISMATCH")
    _need(prepare.get("entity_generation") == expected_generation, "PREPARE_GENERATION_MISMATCH")

    causal_turn_id = _text(prepare.get("causal_turn_id"), "prepare.causal_turn_id")
    _need(route.get("causal_turn_id") == causal_turn_id, "ROUTE_CAUSAL_TURN_MISMATCH")
    turn_binding = _digest(prepare.get("turn_binding_digest"), "prepare.turn_binding_digest")
    _need(route.get("turn_binding_digest") == turn_binding, "ROUTE_TURN_BINDING_MISMATCH")
    workspace_digest = _digest(prepare.get("workspace_digest"), "prepare.workspace_digest")
    _need(route.get("workspace_digest") == workspace_digest, "ROUTE_WORKSPACE_MISMATCH")

    boot = _boot_material(db, prepare=prepare, expected_generation=expected_generation)
    _need(route.get("boot_binding_digest") == boot["binding_digest"], "ROUTE_BOOT_BINDING_MISMATCH")
    cognition = route.get("cognition")
    _need(isinstance(cognition, Mapping), "ROUTE_COGNITION_BINDING_REQUIRED")
    for name in _BOOT_FIELDS:
        _need(cognition.get(name) == boot[name], f"ROUTE_COGNITION_MISMATCH:{name}")

    mode = _text(route.get("jspace_mode"), "route.jspace_mode")
    engine = _text(route.get("target_engine_class"), "route.target_engine_class")
    evidence_kind = _text(route.get("capability_evidence_kind"), "route.capability_evidence_kind")
    capability_receipt = _digest(route.get("capability_receipt_digest"), "route.capability_receipt_digest")
    local_access = route.get("local_activation_access")
    _need(type(local_access) is bool, "ROUTE_LOCAL_ACTIVATION_ACCESS_BOOL_REQUIRED")

    base = {
        "schema": SCHEMA,
        "entity_generation": expected_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": turn_binding,
        "boot_binding_digest": boot["binding_digest"],
        "workspace_digest": workspace_digest,
        "target_engine_class": engine,
        "jspace_mode": mode,
        "capability_evidence_kind": evidence_kind,
        "capability_receipt_digest": capability_receipt,
        "capability_binding_digest": _digest(route.get("capability_binding_digest"), "route.capability_binding_digest"),
        "route_digest": _digest(route.get("route_digest"), "route.route_digest"),
    }

    if mode not in LOCAL_MODES:
        _need(local_access is False, "EXTERNAL_MODE_LOCAL_ACTIVATION_FORBIDDEN")
        resolution = {
            **base,
            "status": "LOCAL_CAPABILITY_NOT_REQUIRED",
            "local_latent_authorized": False,
            "resolved_object": None,
            "authority": "READ_ONLY_ROUTING_EVIDENCE_NO_TRUTH_STATE_EFFECT_AUTHORITY",
        }
        resolution["resolution_digest"] = _sha256_obj(resolution)
        return {"ok": True, **resolution}

    _need(local_access is True, "LOCAL_MODE_REQUIRES_ACTIVATION_ACCESS")
    _need(engine == "BUNDLED_LOCAL_08B", "LOCAL_MODE_ENGINE_NOT_BUNDLED_08B")
    if evidence_kind == "RUNTIME_PROBE":
        raise CapabilityEvidenceError("TYPED_RUNTIME_PROBE_RECEIPT_UNAVAILABLE")
    _need(evidence_kind == "BUNDLED_MANIFEST", "LOCAL_CAPABILITY_EVIDENCE_KIND_UNSUPPORTED")
    manifest_digest = _digest(prepare.get("bundled_manifest_digest"), "prepare.bundled_manifest_digest")
    resolved = _resolve_manifest_admission(
        db,
        manifest_digest=manifest_digest,
        expected_generation=expected_generation,
        capability_receipt_digest=capability_receipt,
    )
    resolution = {
        **base,
        "status": "RESOLVED_CURRENT_GENERATION",
        "local_latent_authorized": True,
        "resolved_object": resolved,
        "authority": "READ_ONLY_ROUTING_EVIDENCE_NO_TRUTH_STATE_EFFECT_AUTHORITY",
    }
    resolution["resolution_digest"] = _sha256_obj(resolution)
    return {"ok": True, **resolution}


__all__ = [
    "SCHEMA",
    "LOCAL_MODES",
    "CapabilityEvidenceError",
    "resolve_bound_evidence",
]
