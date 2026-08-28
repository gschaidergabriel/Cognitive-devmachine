#!/usr/bin/env python3
"""Strict semantic resolver for versioned MiniUnifiedDB cognition objects.

This module is a read-only composition layer over the canonical cognition store. It
exists for runtime admission code that needs the payload semantics behind boot-bound
object digests. It creates no table, durable state, truth authority, or effect path.

A v1 boot binding carries object kind + digest but not object_version. Therefore a
same-kind/same-digest object admitted under more than one version in the live
entity generation is semantically ambiguous and must fail closed before inference.
"""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

import miniunifieddb_cognition_store_v1 as store

SCHEMA = "MINIUNIFIEDDB_COGNITION_SEMANTIC_RESOLUTION/v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CognitionResolutionError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitionResolutionError(message)


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(len(set(value)) > 1, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _refs(raw: Any, name: str) -> list[str]:
    _need(type(raw) is str, f"{name}:JSON_TEXT_REQUIRED")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CognitionResolutionError(f"{name}:JSON_INVALID") from exc
    _need(type(value) is list, f"{name}:LIST_REQUIRED")
    refs: list[str] = []
    for item in value:
        _need(type(item) is str and bool(item.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
        refs.append(item.strip())
    _need(bool(refs), f"{name}:REQUIRED")
    _need(len(refs) == len(set(refs)), f"{name}:DUPLICATE")
    return refs


def _resolve_object(
    db: sqlite3.Connection,
    *,
    object_kind: str,
    object_digest: str,
    entity_generation: int,
) -> dict[str, Any]:
    _need(object_kind in store.OBJECT_KINDS, "OBJECT_KIND_UNSUPPORTED")
    object_digest = _digest(object_digest, "object_digest")
    rows = db.execute(
        """SELECT o.object_version,o.digest_basis,o.payload_json,o.payload_digest,
                  o.provenance_refs_json,a.admission_receipt_digest
             FROM mini_cognition_objects o
             JOIN mini_cognition_object_admissions a
               ON a.object_kind=o.object_kind
              AND a.object_version=o.object_version
              AND a.object_digest=o.object_digest
            WHERE o.object_kind=? AND o.object_digest=? AND a.admitted_generation=?
            ORDER BY o.object_version""",
        (object_kind, object_digest, entity_generation),
    ).fetchall()
    _need(bool(rows), f"COGNITION_OBJECT_NOT_ADMITTED:{object_kind}")
    _need(len(rows) == 1, f"COGNITION_OBJECT_VERSION_AMBIGUOUS:{object_kind}")

    object_version, digest_basis, payload_json, payload_digest, refs_json, receipt = rows[0]
    _need(type(object_version) is str and bool(object_version.strip()), "OBJECT_VERSION_INVALID")
    _need(digest_basis in store.DIGEST_BASES, "DIGEST_BASIS_UNSUPPORTED")
    _need(type(payload_json) is str, "OBJECT_PAYLOAD_JSON_INVALID")
    payload_digest = _digest(payload_digest, "payload_digest")
    _need(store.sha256_text(payload_json) == payload_digest, "OBJECT_PAYLOAD_DIGEST_MISMATCH")
    try:
        payload = json.loads(payload_json)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CognitionResolutionError("OBJECT_PAYLOAD_JSON_INVALID") from exc
    _need(type(payload) is dict, "OBJECT_PAYLOAD_OBJECT_REQUIRED")
    _need(store.canonical_json(payload) == payload_json, "OBJECT_PAYLOAD_NOT_CANONICAL")
    if digest_basis == "CANONICAL_JSON":
        _need(object_digest == payload_digest, "OBJECT_DIGEST_PAYLOAD_MISMATCH")
    provenance_refs = _refs(refs_json, "provenance_refs")
    admission_receipt_digest = _digest(receipt, "admission_receipt_digest")

    return {
        "object_kind": object_kind,
        "object_version": object_version.strip(),
        "object_digest": object_digest,
        "digest_basis": digest_basis,
        "payload": payload,
        "payload_digest": payload_digest,
        "provenance_refs": provenance_refs,
        "admission_receipt_digest": admission_receipt_digest,
        "admitted_generation": entity_generation,
    }


def resolve_prepare_bundle(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    causal_turn_id: str,
    task_text: str,
    expected_turn_binding_digest: str | None = None,
) -> dict[str, Any]:
    """Resolve one already-bound turn plus unambiguous live-generation object payloads."""
    try:
        prepare = store.resolve_prepare_binding(
            db,
            entity_generation=entity_generation,
            causal_turn_id=causal_turn_id,
            task_text=task_text,
        )
    except store.CognitionStoreError as exc:
        raise CognitionResolutionError(str(exc)) from exc

    if expected_turn_binding_digest is not None:
        expected = _digest(expected_turn_binding_digest, "expected_turn_binding_digest")
        _need(prepare["turn_binding_digest"] == expected, "TURN_BINDING_DIGEST_MISMATCH")

    objects: dict[str, dict[str, Any]] = {}
    for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
        objects[field_name] = _resolve_object(
            db,
            object_kind=object_kind,
            object_digest=prepare[field_name],
            entity_generation=entity_generation,
        )

    return {
        "ok": True,
        "schema": SCHEMA,
        "entity_generation": entity_generation,
        "causal_turn_id": prepare["causal_turn_id"],
        "turn_binding_digest": prepare["turn_binding_digest"],
        "boot_binding_digest": prepare["boot_binding_digest"],
        "task_sha256": prepare["task_sha256"],
        "workspace_digest": prepare["workspace_digest"],
        "selected_workspace_slots": prepare["selected_workspace_slots"],
        "contradiction_state": prepare["contradiction_state"],
        "turn_provenance_refs": prepare["turn_provenance_refs"],
        "required_zero_mode": prepare["required_zero_mode"],
        "boot_provenance_refs": prepare["boot_provenance_refs"],
        "objects": objects,
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "routing_only": True,
            "candidate_configuration_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
    }
