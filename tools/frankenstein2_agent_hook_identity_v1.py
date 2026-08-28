#!/usr/bin/env python3
"""Deterministic Claude Agent hook identity join for Frankenstein 2.0.

This module is a pure identity adapter in front of WorkExecutionBinding. It does not
spawn children, write UnifiedDB, authorize effects, or verify completion.

Truth boundary:
    HANDOFF marker != child start
    Agent tool_use_id != agent_id != task_id
    Agent PostToolUse != work completion

It preserves exact call identity so the existing WorkExecution ledger can bind an
observed package/generation to one native Agent invocation without session/time-window
heuristics.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping

SCHEMA = "FRANKENSTEIN2_AGENT_HOOK_IDENTITY/v1"
_AGENT_TOOL_NAMES = frozenset({"Agent"})
_POST_EVENTS = frozenset({"PostToolUse", "PostToolUseFailure"})
_HANDOFF_LINE = re.compile(r"^HANDOFF ([A-Za-z0-9][A-Za-z0-9._:-]{0,255})$")


class AgentHookIdentityError(ValueError):
    """Observed hook data cannot be joined to one exact delegated work package."""


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AgentHookIdentityError(f"MISSING_OR_INVALID_{key.upper()}")
    return value.strip()


def _digest(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _require_agent_tool(payload: Mapping[str, Any]) -> str:
    tool_name = _required_text(payload, "tool_name")
    if tool_name not in _AGENT_TOOL_NAMES:
        raise AgentHookIdentityError(f"UNEXPECTED_TOOL:{tool_name}")
    return tool_name


def parse_handoff_marker(prompt: str) -> str:
    """Return the one exact HANDOFF package marker from the actual Agent prompt.

    The current donor contract says the delegated capsule starts with the marker. Fail
    closed if it is absent, duplicated, malformed, or displaced behind wrapper text.
    """
    if not isinstance(prompt, str) or not prompt:
        raise AgentHookIdentityError("MISSING_OR_INVALID_AGENT_PROMPT")
    lines = prompt.splitlines()
    exact = [(idx, m.group(1)) for idx, line in enumerate(lines) if (m := _HANDOFF_LINE.fullmatch(line))]
    if len(exact) != 1:
        raise AgentHookIdentityError(f"HANDOFF_MARKER_CARDINALITY:{len(exact)}")
    idx, package_id = exact[0]
    if idx != 0:
        raise AgentHookIdentityError("HANDOFF_MARKER_NOT_FIRST_LINE")
    return package_id


@dataclass(frozen=True)
class PackageResolution:
    workpackage_id: str
    work_generation: str
    admissible_unresolved: bool
    provenance: str

    def validate(self) -> "PackageResolution":
        if not self.workpackage_id.strip():
            raise AgentHookIdentityError("MISSING_RESOLVED_WORKPACKAGE_ID")
        if not self.work_generation.strip():
            raise AgentHookIdentityError("MISSING_RESOLVED_WORK_GENERATION")
        if not self.provenance.strip():
            raise AgentHookIdentityError("MISSING_PACKAGE_RESOLUTION_PROVENANCE")
        if not self.admissible_unresolved:
            raise AgentHookIdentityError("WORKPACKAGE_NOT_ADMISSIBLE_UNRESOLVED")
        return self


@dataclass(frozen=True)
class AgentPreObservation:
    session_id: str
    tool_use_id: str
    tool_name: str
    workpackage_id: str
    prompt_digest: str


@dataclass(frozen=True)
class AgentPostObservation:
    session_id: str
    tool_use_id: str
    tool_name: str
    hook_event_name: str
    native_agent_id: str | None
    native_agent_id_state: str
    response_digest: str


@dataclass(frozen=True)
class WorkExecutionJoin:
    schema: str
    workpackage_id: str
    work_generation: str
    package_resolution_provenance: str
    session_id: str
    spawn_tool_use_id: str
    native_agent_id: str | None
    native_agent_id_state: str
    pre_prompt_digest: str
    post_response_digest: str


def parse_agent_pretool(payload: Mapping[str, Any]) -> AgentPreObservation:
    event = _required_text(payload, "hook_event_name")
    if event != "PreToolUse":
        raise AgentHookIdentityError(f"UNEXPECTED_HOOK_EVENT:{event}")
    tool_name = _require_agent_tool(payload)
    session_id = _required_text(payload, "session_id")
    tool_use_id = _required_text(payload, "tool_use_id")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, Mapping):
        raise AgentHookIdentityError("MISSING_OR_INVALID_TOOL_INPUT")
    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        raise AgentHookIdentityError("MISSING_OR_INVALID_AGENT_PROMPT")
    package_id = parse_handoff_marker(prompt)
    return AgentPreObservation(
        session_id=session_id,
        tool_use_id=tool_use_id,
        tool_name=tool_name,
        workpackage_id=package_id,
        prompt_digest=_digest(prompt),
    )


def parse_agent_posttool(payload: Mapping[str, Any]) -> AgentPostObservation:
    event = _required_text(payload, "hook_event_name")
    if event not in _POST_EVENTS:
        raise AgentHookIdentityError(f"UNEXPECTED_HOOK_EVENT:{event}")
    tool_name = _require_agent_tool(payload)
    session_id = _required_text(payload, "session_id")
    tool_use_id = _required_text(payload, "tool_use_id")
    response = payload.get("tool_response")
    if response is None:
        response = {}
    if not isinstance(response, Mapping):
        raise AgentHookIdentityError("INVALID_TOOL_RESPONSE")
    raw_agent_id = response.get("agentId")
    if raw_agent_id is None:
        agent_id = None
        state = "UNKNOWN"
    elif isinstance(raw_agent_id, str) and raw_agent_id.strip():
        agent_id = raw_agent_id.strip()
        state = "OBSERVED"
    else:
        raise AgentHookIdentityError("INVALID_AGENT_ID")
    return AgentPostObservation(
        session_id=session_id,
        tool_use_id=tool_use_id,
        tool_name=tool_name,
        hook_event_name=event,
        native_agent_id=agent_id,
        native_agent_id_state=state,
        response_digest=_digest(dict(response)),
    )


def join_agent_call(
    pre: AgentPreObservation,
    post: AgentPostObservation,
    package: PackageResolution,
    *,
    expected_work_generation: str,
) -> WorkExecutionJoin:
    """Join exact Pre/Post call identity to one resolved package generation.

    `PackageResolution` must come from the canonical package authority. This adapter
    validates its observed relation but does not itself decide package state.
    """
    package.validate()
    if pre.tool_use_id != post.tool_use_id:
        raise AgentHookIdentityError("TOOL_USE_ID_MISMATCH")
    if pre.session_id != post.session_id:
        raise AgentHookIdentityError("SESSION_ID_MISMATCH")
    if pre.tool_name != post.tool_name:
        raise AgentHookIdentityError("TOOL_NAME_MISMATCH")
    if pre.workpackage_id != package.workpackage_id:
        raise AgentHookIdentityError("HANDOFF_PACKAGE_MISMATCH")
    if not isinstance(expected_work_generation, str) or not expected_work_generation.strip():
        raise AgentHookIdentityError("MISSING_EXPECTED_WORK_GENERATION")
    if package.work_generation != expected_work_generation.strip():
        raise AgentHookIdentityError("STALE_WORK_GENERATION")
    return WorkExecutionJoin(
        schema=SCHEMA,
        workpackage_id=package.workpackage_id,
        work_generation=package.work_generation,
        package_resolution_provenance=package.provenance,
        session_id=pre.session_id,
        spawn_tool_use_id=pre.tool_use_id,
        native_agent_id=post.native_agent_id,
        native_agent_id_state=post.native_agent_id_state,
        pre_prompt_digest=pre.prompt_digest,
        post_response_digest=post.response_digest,
    )
