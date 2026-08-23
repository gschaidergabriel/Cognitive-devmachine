#!/usr/bin/env python3
"""Fail-closed execution identity for Mini Entity runtime evidence.

This object is build/launcher evidence only. It must not be sourced from a mutable
MiniUnifiedDB application profile, model output, J-Space/GWT state, or effect result.
It binds exact build-source identity and runtime/artifact bytes to the same boot source
lock already admitted by MiniUnifiedDB cognition prepare material.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_ENTITY_EXECUTION_IDENTITY/v1"
BOUND_SCHEMA = "MINI_ENTITY_BOUND_EXECUTION_IDENTITY/v1"
AUTHORITY = "EXECUTION_EVIDENCE_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY"
_GIT_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_FIELDS = {
    "schema",
    "source_commit",
    "source_tree",
    "source_dirty",
    "runtime_module_digest",
    "artifact_sha256",
    "mini_entity_version",
    "entityos_version",
    "source_lock_digest",
    "provenance_refs",
    "authority",
    "identity_digest",
}


class ExecutionIdentityError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutionIdentityError(message)


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ExecutionIdentityError("NONCANONICAL_JSON") from exc


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _git_oid(value: Any, name: str) -> str:
    _need(type(value) is str and _GIT_OID.fullmatch(value) is not None, f"{name}:GIT_OID_REQUIRED")
    _need(len(set(value)) > 1, f"{name}:PLACEHOLDER_REJECTED")
    return value


def compile_identity(
    *,
    source_commit: str,
    source_tree: str,
    source_dirty: bool,
    runtime_module_digest: str,
    artifact_sha256: str,
    mini_entity_version: str,
    entityos_version: str,
    source_lock_digest: str,
    provenance_refs: list[str],
) -> dict[str, Any]:
    doc = {
        "schema": SCHEMA,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "source_dirty": source_dirty,
        "runtime_module_digest": runtime_module_digest,
        "artifact_sha256": artifact_sha256,
        "mini_entity_version": mini_entity_version,
        "entityos_version": entityos_version,
        "source_lock_digest": source_lock_digest,
        "provenance_refs": provenance_refs,
        "authority": AUTHORITY,
    }
    doc["identity_digest"] = sha256_obj(doc)
    validate_identity(doc)
    return doc


def validate_identity(doc: Mapping[str, Any]) -> dict[str, Any]:
    _need(isinstance(doc, Mapping), "EXECUTION_IDENTITY_OBJECT_REQUIRED")
    value = dict(doc)
    _need(set(value) == _FIELDS, "EXECUTION_IDENTITY_FIELDS_MISMATCH")
    _need(value.get("schema") == SCHEMA, "EXECUTION_IDENTITY_SCHEMA_MISMATCH")
    source_commit = _git_oid(value.get("source_commit"), "source_commit")
    source_tree = _git_oid(value.get("source_tree"), "source_tree")
    _need(type(value.get("source_dirty")) is bool, "SOURCE_DIRTY_BOOL_REQUIRED")
    _need(value["source_dirty"] is False, "SOURCE_DIRTY_OR_UNKNOWN")
    runtime_module_digest = _digest(value.get("runtime_module_digest"), "runtime_module_digest")
    artifact_sha256 = _digest(value.get("artifact_sha256"), "artifact_sha256")
    mini_entity_version = _text(value.get("mini_entity_version"), "mini_entity_version")
    entityos_version = _text(value.get("entityos_version"), "entityos_version")
    source_lock_digest = _digest(value.get("source_lock_digest"), "source_lock_digest")
    refs = value.get("provenance_refs")
    _need(type(refs) is list and bool(refs), "PROVENANCE_REFS_REQUIRED")
    normalized_refs = [_text(item, "provenance_ref") for item in refs]
    _need(len(normalized_refs) == len(set(normalized_refs)), "PROVENANCE_REFS_DUPLICATE")
    _need(value.get("authority") == AUTHORITY, "EXECUTION_IDENTITY_AUTHORITY_MISMATCH")
    observed = _digest(value.get("identity_digest"), "identity_digest")
    unsigned = dict(value)
    unsigned.pop("identity_digest")
    _need(observed == sha256_obj(unsigned), "EXECUTION_IDENTITY_DIGEST_MISMATCH")
    return {
        "ok": True,
        "schema": SCHEMA,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "runtime_module_digest": runtime_module_digest,
        "artifact_sha256": artifact_sha256,
        "mini_entity_version": mini_entity_version,
        "entityos_version": entityos_version,
        "source_lock_digest": source_lock_digest,
        "identity_digest": observed,
        "authority": AUTHORITY,
    }


def bind_to_prepare(
    identity: Mapping[str, Any],
    prepare: Mapping[str, Any],
    *,
    expected_generation: int,
) -> dict[str, Any]:
    """Cross-bind immutable execution evidence to one canonical cognition prepare ancestry."""
    validated = validate_identity(identity)
    _need(isinstance(prepare, Mapping) and prepare.get("ok") is True, "PREPARE_BINDING_REQUIRED")
    _need(type(expected_generation) is int and expected_generation >= 0, "EXPECTED_GENERATION_INVALID")
    _need(prepare.get("entity_generation") == expected_generation, "STALE_GENERATION")
    causal_turn_id = _text(prepare.get("causal_turn_id"), "prepare.causal_turn_id")
    turn_binding_digest = _digest(prepare.get("turn_binding_digest"), "prepare.turn_binding_digest")
    boot_source_lock_digest = _digest(
        prepare.get("boot_source_lock_digest"), "prepare.boot_source_lock_digest"
    )
    _need(
        boot_source_lock_digest == validated["source_lock_digest"],
        "EXECUTION_IDENTITY_SOURCE_LOCK_MISMATCH",
    )
    material = {
        "schema": BOUND_SCHEMA,
        "entity_generation": expected_generation,
        "causal_turn_id": causal_turn_id,
        "turn_binding_digest": turn_binding_digest,
        "boot_source_lock_digest": boot_source_lock_digest,
        "execution_identity_digest": validated["identity_digest"],
        "source_commit": validated["source_commit"],
        "source_tree": validated["source_tree"],
        "runtime_module_digest": validated["runtime_module_digest"],
        "artifact_sha256": validated["artifact_sha256"],
        "mini_entity_version": validated["mini_entity_version"],
        "entityos_version": validated["entityos_version"],
    }
    return {
        "ok": True,
        **material,
        "bound_digest": sha256_obj(material),
        "authority": AUTHORITY,
    }


__all__ = [
    "SCHEMA",
    "BOUND_SCHEMA",
    "AUTHORITY",
    "ExecutionIdentityError",
    "compile_identity",
    "validate_identity",
    "bind_to_prepare",
    "sha256_obj",
]
