#!/usr/bin/env python3
"""Fail-closed Claude Code hook -> Frankenstein 2.0 effect invocation adapter.

This source adapter closes only the *identity handoff* between hook payloads and the
Frankenstein-2 effect lifecycle substrate. It does not execute tools, block tools, grant
EffectGate authority, or claim host/runtime enforcement.

Design law:
    session_id = contextual identity only
    tool_use_id = immutable call-scoped invocation identity

PreToolUse is converted into an EffectRequest keyed by tool_use_id. PostToolUse and
PostToolUseFailure must carry the same tool_use_id, session_id, and tool_name as the
request they close. Missing or ambiguous identity fails closed; there is deliberately no
fallback to a session-scoped "current effect" pointer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

try:  # package import
    from .frankenstein2_effect_lifecycle_v1 import EffectLifecycleStore, EffectRequest
except ImportError:  # direct tools-PYTHONPATH execution
    from frankenstein2_effect_lifecycle_v1 import EffectLifecycleStore, EffectRequest


SCHEMA = "FRANKENSTEIN2_HOOK_INVOCATION_ADAPTER/v1"
PRE_EVENT = "PreToolUse"
POST_EVENTS = frozenset({"PostToolUse", "PostToolUseFailure"})


class HookInvocationIdentityError(ValueError):
    """Hook payload cannot be bound to one exact effect invocation."""


@dataclass(frozen=True)
class HookInvocationContext:
    invocation_id: str
    session_id: str
    tool_name: str
    hook_event_name: str


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HookInvocationIdentityError(f"MISSING_OR_INVALID_{key.upper()}")
    return value.strip()


def _context(payload: Mapping[str, Any], *, allowed_events: frozenset[str]) -> HookInvocationContext:
    event = _required_text(payload, "hook_event_name")
    if event not in allowed_events:
        raise HookInvocationIdentityError(f"UNEXPECTED_HOOK_EVENT:{event}")
    return HookInvocationContext(
        invocation_id=_required_text(payload, "tool_use_id"),
        session_id=_required_text(payload, "session_id"),
        tool_name=_required_text(payload, "tool_name"),
        hook_event_name=event,
    )


def build_effect_request_from_pretool(
    store: EffectLifecycleStore,
    payload: Mapping[str, Any],
    *,
    agent_id: str,
    task_id: str,
    turn_id: str,
    causal_id: str,
    generation: int,
    effect_scope: str,
    parent_candidate_id: str | None = None,
) -> EffectRequest:
    """Build one source-bound request from a single PreToolUse call.

    The adapter intentionally refuses payloads without tool_use_id. A caller must not
    manufacture an invocation id from session_id, ordering, timestamps, or a mutable
    active-turn slot.
    """
    ctx = _context(payload, allowed_events=frozenset({PRE_EVENT}))
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, Mapping):
        raise HookInvocationIdentityError("MISSING_OR_INVALID_TOOL_INPUT")
    return store.build_request(
        invocation_id=ctx.invocation_id,
        session_id=ctx.session_id,
        agent_id=agent_id,
        task_id=task_id,
        turn_id=turn_id,
        causal_id=causal_id,
        generation=generation,
        tool_name=ctx.tool_name,
        normalized_arguments=dict(tool_input),
        effect_scope=effect_scope,
        parent_candidate_id=parent_candidate_id,
    )


def require_matching_posttool(request: EffectRequest, payload: Mapping[str, Any]) -> HookInvocationContext:
    """Bind a PostToolUse/PostToolUseFailure event to exactly one prior request."""
    ctx = _context(payload, allowed_events=POST_EVENTS)
    if ctx.invocation_id != request.invocation_id:
        raise HookInvocationIdentityError(
            f"INVOCATION_ID_MISMATCH:{request.invocation_id}:{ctx.invocation_id}"
        )
    if ctx.session_id != request.session_id:
        raise HookInvocationIdentityError(
            f"SESSION_ID_MISMATCH:{request.session_id}:{ctx.session_id}"
        )
    if ctx.tool_name != request.tool_name:
        raise HookInvocationIdentityError(
            f"TOOL_NAME_MISMATCH:{request.tool_name}:{ctx.tool_name}"
        )
    return ctx
