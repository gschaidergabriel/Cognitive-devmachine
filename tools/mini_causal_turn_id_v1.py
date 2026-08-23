#!/usr/bin/env python3
"""Deterministic causal-turn identity for the Mini Entity pre-inference boundary.

This module creates no state, truth, model, workspace or effect authority.  It derives a
stable causal_turn_id only from the complete already-bound pre-inference material and then
delegates persistence/resolution to the existing MiniUnifiedDB cognition store.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from typing import Any

import miniunifieddb_cognition_store_v1 as cognition_store

SCHEMA = "MINI_ENTITY_CAUSAL_TURN_ID/v1"
ID_PREFIX = "ct1:"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CausalTurnError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CausalTurnError(message)


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _refs(value: Any, name: str, *, nonempty: bool) -> list[str]:
    _need(type(value) is list, f"{name}:LIST_REQUIRED")
    refs = [_text(item, name) for item in value]
    _need(len(refs) == len(set(refs)), f"{name}:DUPLICATE")
    if nonempty:
        _need(bool(refs), f"{name}:NONEMPTY_REQUIRED")
    return refs


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CausalTurnError("NONCANONICAL_IDENTITY_MATERIAL") from exc


def identity_material(
    *,
    entity_generation: int,
    boot_binding_digest: str,
    task_text: str,
    workspace_digest: str,
    selected_workspace_slots: list[str],
    contradiction_state: str,
    provenance_refs: list[str],
    required_zero_mode: str,
) -> dict[str, Any]:
    """Return the exact material whose digest defines one logical pre-inference turn.

    Equal material at the same generation is the same logical turn/retry.  Any change in
    task, boot identity, workspace selection, contradiction/provenance or Zero mode creates
    a different turn identity rather than laundering changed material through an old id.
    """
    _need(type(entity_generation) is int and not isinstance(entity_generation, bool) and entity_generation >= 0,
          "GENERATION_INVALID")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    return {
        "schema": SCHEMA,
        "entity_generation": entity_generation,
        "boot_binding_digest": _digest(boot_binding_digest, "boot_binding_digest"),
        "task_sha256": hashlib.sha256(task_text.encode("utf-8")).hexdigest(),
        "workspace_digest": _digest(workspace_digest, "workspace_digest"),
        "selected_workspace_slots": _refs(selected_workspace_slots, "selected_workspace_slots", nonempty=False),
        "contradiction_state": _text(contradiction_state, "contradiction_state"),
        "provenance_refs": _refs(provenance_refs, "provenance_refs", nonempty=True),
        "required_zero_mode": _text(required_zero_mode, "required_zero_mode"),
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
    }


def derive_causal_turn_id(**kwargs: Any) -> str:
    material = identity_material(**kwargs)
    return ID_PREFIX + hashlib.sha256(canonical_json(material)).hexdigest()


def validate_causal_turn_id(causal_turn_id: str, **kwargs: Any) -> dict[str, Any]:
    expected = derive_causal_turn_id(**kwargs)
    _need(type(causal_turn_id) is str and causal_turn_id == expected, "CAUSAL_TURN_ID_BINDING_MISMATCH")
    return {
        "ok": True,
        "schema": SCHEMA,
        "causal_turn_id": expected,
        "authority": "IDENTITY_ONLY",
        "runtime_credit": "ZERO",
    }


def bind_derived_turn(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    boot_binding_digest: str,
    task_text: str,
    workspace_digest: str,
    selected_workspace_slots: list[str],
    contradiction_state: str,
    provenance_refs: list[str],
    required_zero_mode: str,
) -> dict[str, Any]:
    """Bind a deterministic id through the existing same-MiniUnifiedDB store only."""
    args = {
        "entity_generation": entity_generation,
        "boot_binding_digest": boot_binding_digest,
        "task_text": task_text,
        "workspace_digest": workspace_digest,
        "selected_workspace_slots": selected_workspace_slots,
        "contradiction_state": contradiction_state,
        "provenance_refs": provenance_refs,
        "required_zero_mode": required_zero_mode,
    }
    causal_turn_id = derive_causal_turn_id(**args)
    result = cognition_store.bind_turn(db, causal_turn_id=causal_turn_id, **args)
    return {**result, "causal_turn_id": causal_turn_id, "causal_turn_schema": SCHEMA}


def resolve_derived_prepare_binding(
    db: sqlite3.Connection,
    *,
    entity_generation: int,
    boot_binding_digest: str,
    task_text: str,
    workspace_digest: str,
    selected_workspace_slots: list[str],
    contradiction_state: str,
    provenance_refs: list[str],
    required_zero_mode: str,
) -> dict[str, Any]:
    """Resolve an already-bound derived turn and cross-check all supplied material."""
    args = {
        "entity_generation": entity_generation,
        "boot_binding_digest": boot_binding_digest,
        "task_text": task_text,
        "workspace_digest": workspace_digest,
        "selected_workspace_slots": selected_workspace_slots,
        "contradiction_state": contradiction_state,
        "provenance_refs": provenance_refs,
        "required_zero_mode": required_zero_mode,
    }
    causal_turn_id = derive_causal_turn_id(**args)
    resolved = cognition_store.resolve_prepare_binding(
        db,
        entity_generation=entity_generation,
        causal_turn_id=causal_turn_id,
        task_text=task_text,
    )
    expected = identity_material(**args)
    checks = {
        "boot_binding_digest": expected["boot_binding_digest"],
        "workspace_digest": expected["workspace_digest"],
        "selected_workspace_slots": expected["selected_workspace_slots"],
        "contradiction_state": expected["contradiction_state"],
        "turn_provenance_refs": expected["provenance_refs"],
        "required_zero_mode": expected["required_zero_mode"],
    }
    for key, value in checks.items():
        _need(resolved.get(key) == value, f"RESOLVED_TURN_BINDING_MISMATCH:{key}")
    return {**resolved, "causal_turn_schema": SCHEMA}


__all__ = [
    "SCHEMA",
    "CausalTurnError",
    "identity_material",
    "derive_causal_turn_id",
    "validate_causal_turn_id",
    "bind_derived_turn",
    "resolve_derived_prepare_binding",
]
