#!/usr/bin/env python3
"""Fail-closed transient selector for one already-bound MiniUnifiedDB cognition turn.

The selector is routing material only. It cannot supply or override Zero/GRF/workspace/
model/J-Space authority. A real Cognitive Fabric admission handler must resolve the
canonical turn in MiniUnifiedDB and verify the resolved binding against this selector.
"""
from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_COGNITIVE_INVOCATION/v1"
_SELECTOR_KEYS = {
    "schema",
    "expected_generation",
    "causal_turn_id",
    "task_text",
    "turn_binding_digest",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class InvocationSelectorFault(ValueError):
    pass


def _need(condition: bool, error: str) -> None:
    if not condition:
        raise InvocationSelectorFault(error)


def _text(value: Any, field: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{field}:NONEMPTY_TEXT_REQUIRED")
    return value


def _digest(value: Any, field: str) -> str:
    _need(type(value) is str and _SHA256_RE.fullmatch(value) is not None,
          f"{field}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{field}:PLACEHOLDER_FORBIDDEN")
    return value


def validate_selector(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the exact non-authorizing invocation selector surface."""
    _need(isinstance(value, Mapping), "SELECTOR_OBJECT_REQUIRED")
    keys = set(value)
    _need(keys == _SELECTOR_KEYS, "SELECTOR_FIELD_SET_MISMATCH")
    _need(value.get("schema") == SCHEMA, "SELECTOR_SCHEMA_MISMATCH")
    generation = value.get("expected_generation")
    _need(type(generation) is int and generation >= 0, "EXPECTED_GENERATION_INVALID")
    return {
        "schema": SCHEMA,
        "expected_generation": generation,
        "causal_turn_id": _text(value.get("causal_turn_id"), "causal_turn_id"),
        "task_text": _text(value.get("task_text"), "task_text"),
        "turn_binding_digest": _digest(value.get("turn_binding_digest"), "turn_binding_digest"),
    }


def verify_resolved_binding(selector: Mapping[str, Any], resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Cross-bind selector to already-resolved MiniUnifiedDB material.

    This function grants no authority. It only proves that the transient selector chose
    the exact generation/turn/task/binding that MiniUnifiedDB returned.
    """
    selected = validate_selector(selector)
    _need(isinstance(resolved, Mapping) and resolved.get("ok") is True,
          "RESOLVED_BINDING_REQUIRED")
    _need(resolved.get("entity_generation") == selected["expected_generation"],
          "RESOLVED_GENERATION_MISMATCH")
    _need(resolved.get("causal_turn_id") == selected["causal_turn_id"],
          "RESOLVED_CAUSAL_TURN_MISMATCH")
    _need(resolved.get("turn_binding_digest") == selected["turn_binding_digest"],
          "RESOLVED_TURN_BINDING_DIGEST_MISMATCH")
    expected_task_sha256 = hashlib.sha256(selected["task_text"].encode("utf-8")).hexdigest()
    _need(resolved.get("task_sha256") == expected_task_sha256,
          "RESOLVED_TASK_BINDING_MISMATCH")
    authority = resolved.get("authority")
    _need(
        isinstance(authority, Mapping)
        and authority.get("durable_state") == "MiniUnifiedDB"
        and authority.get("candidate_only") is True
        and authority.get("direct_truth_authority") is False
        and authority.get("direct_effect_authority") is False,
        "RESOLVED_AUTHORITY_CONTRACT_MISMATCH",
    )
    return {
        "ok": True,
        "schema": SCHEMA,
        "expected_generation": selected["expected_generation"],
        "causal_turn_id": selected["causal_turn_id"],
        "turn_binding_digest": selected["turn_binding_digest"],
        "task_sha256": expected_task_sha256,
        "authority": "ROUTING_ONLY",
    }


class OneShotInvocationSelector:
    """Ephemeral one-use holder suitable for the retained runtime constructor seam."""

    def __init__(self, selector: Mapping[str, Any]):
        self._selector = validate_selector(selector)
        self._consumed = False

    def take(self) -> dict[str, Any]:
        _need(not self._consumed, "INVOCATION_SELECTOR_ALREADY_CONSUMED")
        self._consumed = True
        return dict(self._selector)


__all__ = [
    "SCHEMA",
    "InvocationSelectorFault",
    "validate_selector",
    "verify_resolved_binding",
    "OneShotInvocationSelector",
]
