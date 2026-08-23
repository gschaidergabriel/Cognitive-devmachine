#!/usr/bin/env python3
"""Fail-closed resolver for the routing-only MINI_COGNITIVE_INVOCATION/v1 selector.

The selector has no cognition, truth, effect, workspace, or identity authority. It may
only select an already-bound current-generation causal turn from canonical MiniUnifiedDB.
All cognition/workspace identities are returned by the existing cognition store resolver.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any, Mapping

import miniunifieddb_cognition_store_v1 as cognition_store

SCHEMA = "MINI_COGNITIVE_INVOCATION/v1"
REQUIRED_FIELDS = {
    "expected_generation",
    "causal_turn_id",
    "task_text",
    "turn_binding_digest",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class InvocationSelectorError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise InvocationSelectorError(message)


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(len(set(value)) > 1, f"{name}:PLACEHOLDER_REJECTED")
    return value


def resolve_selector(db: sqlite3.Connection, selector: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve one selector through the existing MiniUnifiedDB cognition binding store."""
    _need(isinstance(selector, Mapping), "INVOCATION_SELECTOR_OBJECT_REQUIRED")
    keys = set(selector)
    missing = sorted(REQUIRED_FIELDS - keys)
    unknown = sorted(keys - REQUIRED_FIELDS)
    _need(not missing, "INVOCATION_SELECTOR_MISSING_FIELDS:" + ",".join(missing))
    _need(not unknown, "INVOCATION_SELECTOR_UNKNOWN_FIELDS:" + ",".join(unknown))

    generation = selector["expected_generation"]
    _need(type(generation) is int and generation >= 0, "EXPECTED_GENERATION_INVALID")
    causal_turn_id = selector["causal_turn_id"]
    _need(type(causal_turn_id) is str and bool(causal_turn_id.strip()), "CAUSAL_TURN_ID_REQUIRED")
    task_text = selector["task_text"]
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    turn_binding_digest = _digest(selector["turn_binding_digest"], "turn_binding_digest")

    try:
        resolved = cognition_store.resolve_prepare_binding(
            db,
            entity_generation=generation,
            causal_turn_id=causal_turn_id,
            task_text=task_text,
        )
    except cognition_store.CognitionStoreError as exc:
        raise InvocationSelectorError(f"MINIUNIFIEDDB_SELECTOR_REJECTED:{exc}") from exc

    _need(type(resolved) is dict and resolved.get("ok") is True, "MINIUNIFIEDDB_SELECTOR_RESOLUTION_INVALID")
    _need(resolved.get("entity_generation") == generation, "RESOLVED_GENERATION_MISMATCH")
    _need(resolved.get("causal_turn_id") == causal_turn_id.strip(), "RESOLVED_CAUSAL_TURN_MISMATCH")
    _need(resolved.get("turn_binding_digest") == turn_binding_digest, "TURN_BINDING_DIGEST_MISMATCH")

    return {
        **resolved,
        "invocation_selector_schema": SCHEMA,
        "invocation_selector_authority": "NONE_ROUTING_ONLY",
    }
