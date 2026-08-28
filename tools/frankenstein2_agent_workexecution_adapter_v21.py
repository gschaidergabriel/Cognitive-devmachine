#!/usr/bin/env python3
"""Claude Agent spawn -> WorkExecutionBinding v2.1 source adapter.

Source-only deterministic identity bridge. It records the exact HANDOFF marker carried
inside an observed Agent PreToolUse prompt and joins the same call-scoped tool_use_id to
the Agent PostToolUse agentId. It does not spawn children, grant task/effect authority,
or claim installed-runtime equivalence between documented agentId and lifecycle agent_id.

Truth boundaries:
  HANDOFF marker = work identity carrier, not completion evidence
  session_id != tool_use_id != agent_id != task_id
  absent/ambiguous agentId = UNKNOWN, never guessed
  task_id remains UNKNOWN here until a separate observed Task lifecycle join exists
  one tool_use_id cannot bind two workpackages
  one workpackage generation cannot silently bind multiple Agent calls

This revision intentionally has no fanout contract. If fanout is later admitted it must
be explicit, typed and separately tested rather than weakening the single-spawn default.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Mapping

from frankenstein2_agent_hook_identity_v1 import (
    AgentHookIdentityError,
    parse_handoff_marker,
)
from frankenstein2_work_execution_binding_v1 import (
    WorkExecutionBinding,
    _append_event,
    _connect,
)
from frankenstein2_work_execution_binding_v2 import init_hardened_schema

SCHEMA = "FRANKENSTEIN2_AGENT_WORKEXECUTION_ADAPTER/v2.1"
PRE_EVENT = "PreToolUse"
POST_EVENT = "PostToolUse"
AGENT_TOOL = "Agent"


class AgentWorkExecutionIdentityError(ValueError):
    """Observed hook payload cannot be bound to one exact delegated work item."""


@dataclass(frozen=True)
class AgentSpawnObservation:
    spawn_tool_use_id: str
    workpackage_id: str
    work_generation: str
    parent_session_id: str
    status: str
    agent_id: str | None
    binding_id: str | None


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AgentWorkExecutionIdentityError(f"MISSING_OR_INVALID_{key.upper()}")
    return value.strip()


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _exact_handoff_package(prompt: str) -> str:
    """Use the single canonical Agent HANDOFF parser for admission semantics."""
    try:
        return parse_handoff_marker(prompt)
    except AgentHookIdentityError as exc:
        raise AgentWorkExecutionIdentityError(str(exc)) from exc


def _validate_agent_hook(payload: Mapping[str, Any], expected_event: str) -> tuple[str, str]:
    event = _required_text(payload, "hook_event_name")
    if event != expected_event:
        raise AgentWorkExecutionIdentityError(f"UNEXPECTED_HOOK_EVENT:{event}")
    tool_name = _required_text(payload, "tool_name")
    if tool_name != AGENT_TOOL:
        raise AgentWorkExecutionIdentityError(f"UNEXPECTED_TOOL:{tool_name}")
    return _required_text(payload, "tool_use_id"), _required_text(payload, "session_id")


def init_agent_spawn_schema(db_path: Path) -> None:
    # Opening the base WorkExecution database first is intentional: this adapter extends
    # the same SQLite authority instead of creating a parallel execution ledger.
    con = _connect(Path(db_path))
    try:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS fr2_agent_spawn_observations(
              spawn_tool_use_id TEXT PRIMARY KEY,
              workpackage_id TEXT NOT NULL,
              work_generation TEXT NOT NULL,
              parent_session_id TEXT NOT NULL,
              prompt_digest TEXT NOT NULL,
              status TEXT NOT NULL,
              agent_id TEXT,
              agent_identity_state TEXT NOT NULL,
              binding_id TEXT UNIQUE,
              native_task_id TEXT,
              pre_payload_digest TEXT NOT NULL,
              post_payload_digest TEXT,
              observed_pre_at REAL NOT NULL,
              observed_post_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_fr2_agent_spawn_package
              ON fr2_agent_spawn_observations(workpackage_id, work_generation, observed_pre_at);
            """
        )
        con.execute("BEGIN IMMEDIATE")
        duplicate = con.execute(
            """SELECT workpackage_id,work_generation,COUNT(*) AS n
               FROM fr2_agent_spawn_observations
               GROUP BY workpackage_id,work_generation
               HAVING COUNT(*) > 1
               ORDER BY workpackage_id,work_generation
               LIMIT 1"""
        ).fetchone()
        if duplicate is not None:
            raise AgentWorkExecutionIdentityError(
                "LEGACY_PACKAGE_GENERATION_FANOUT_REQUIRES_RECONCILIATION:"
                f"{duplicate['workpackage_id']}:{duplicate['work_generation']}:{duplicate['n']}"
            )
        con.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_fr2_agent_spawn_package_generation "
            "ON fr2_agent_spawn_observations(workpackage_id, work_generation)"
        )
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()


class AgentWorkExecutionAdapter:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        # Install the hardened v2 completion invariant on the same v1-compatible
        # WorkExecution substrate before extending it with Agent spawn observations.
        init_hardened_schema(self.db_path)
        init_agent_spawn_schema(self.db_path)

    def record_agent_pretool(
        self,
        payload: Mapping[str, Any],
        *,
        expected_workpackage_id: str,
        expected_work_generation: str,
    ) -> AgentSpawnObservation:
        """Record exact package -> Agent call identity from observed PreToolUse.

        The expected package/generation comes from already-admitted durable work state.
        This adapter verifies only that the actual observed Agent prompt carries exactly
        one HANDOFF marker and that its package id matches that admitted identity.
        """
        spawn_tool_use_id, session_id = _validate_agent_hook(payload, PRE_EVENT)
        expected_workpackage_id = str(expected_workpackage_id or "").strip()
        expected_work_generation = str(expected_work_generation or "").strip()
        if not expected_workpackage_id:
            raise AgentWorkExecutionIdentityError("EXPECTED_WORKPACKAGE_ID_REQUIRED")
        if not expected_work_generation:
            raise AgentWorkExecutionIdentityError("EXPECTED_WORK_GENERATION_REQUIRED")

        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, Mapping):
            raise AgentWorkExecutionIdentityError("MISSING_OR_INVALID_TOOL_INPUT")
        prompt = tool_input.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            raise AgentWorkExecutionIdentityError("MISSING_OR_INVALID_AGENT_PROMPT")
        marker_package_id = _exact_handoff_package(prompt)
        if marker_package_id != expected_workpackage_id:
            raise AgentWorkExecutionIdentityError(
                f"HANDOFF_PACKAGE_MISMATCH:{expected_workpackage_id}:{marker_package_id}"
            )

        prompt_digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        pre_payload_digest = _digest(dict(payload))
        con = _connect(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            existing = con.execute(
                "SELECT workpackage_id,work_generation FROM fr2_agent_spawn_observations "
                "WHERE spawn_tool_use_id=?",
                (spawn_tool_use_id,),
            ).fetchone()
            if existing is not None:
                raise AgentWorkExecutionIdentityError(
                    "SPAWN_TOOL_USE_ID_ALREADY_BOUND:"
                    f"{spawn_tool_use_id}:{existing['workpackage_id']}:{existing['work_generation']}"
                )
            existing_package = con.execute(
                """SELECT spawn_tool_use_id FROM fr2_agent_spawn_observations
                   WHERE workpackage_id=? AND work_generation=?""",
                (expected_workpackage_id, expected_work_generation),
            ).fetchone()
            if existing_package is not None:
                raise AgentWorkExecutionIdentityError(
                    "PACKAGE_GENERATION_ALREADY_HAS_SPAWN:"
                    f"{expected_workpackage_id}:{expected_work_generation}:"
                    f"{existing_package['spawn_tool_use_id']}"
                )
            con.execute(
                """INSERT INTO fr2_agent_spawn_observations(
                     spawn_tool_use_id,workpackage_id,work_generation,parent_session_id,
                     prompt_digest,status,agent_id,agent_identity_state,binding_id,native_task_id,
                     pre_payload_digest,post_payload_digest,observed_pre_at,observed_post_at
                   ) VALUES(?,?,?,?,?,'PRE_OBSERVED',NULL,'UNKNOWN',NULL,NULL,?,NULL,?,NULL)""",
                (
                    spawn_tool_use_id,
                    expected_workpackage_id,
                    expected_work_generation,
                    session_id,
                    prompt_digest,
                    pre_payload_digest,
                    time.time(),
                ),
            )
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()
        return AgentSpawnObservation(
            spawn_tool_use_id,
            expected_workpackage_id,
            expected_work_generation,
            session_id,
            "PRE_OBSERVED",
            None,
            None,
        )

    def record_agent_posttool(
        self,
        payload: Mapping[str, Any],
        *,
        binding_id: str,
        child_runtime_kind: str,
        identity_provenance: str,
        native_task_id: str | None = None,
    ) -> WorkExecutionBinding | None:
        """Atomically join exact Agent call identity to observed agentId.

        If PostToolUse lacks an unambiguous agentId, the spawn remains explicitly UNKNOWN
        and no WorkExecutionBinding row is minted. That UNKNOWN state is sticky: a later
        duplicate/replayed PostToolUse cannot silently convert it into observed identity.
        Task identity is not admitted by this Agent-only edge; it requires separately
        observed TaskCreated/TaskCompleted evidence.
        """
        spawn_tool_use_id, session_id = _validate_agent_hook(payload, POST_EVENT)
        binding_id = str(binding_id or "").strip()
        child_runtime_kind = str(child_runtime_kind or "").strip()
        identity_provenance = str(identity_provenance or "").strip()
        if not binding_id:
            raise AgentWorkExecutionIdentityError("BINDING_ID_REQUIRED")
        if not child_runtime_kind:
            raise AgentWorkExecutionIdentityError("CHILD_RUNTIME_KIND_REQUIRED")
        if not identity_provenance:
            raise AgentWorkExecutionIdentityError("IDENTITY_PROVENANCE_REQUIRED")
        if native_task_id is not None:
            raise AgentWorkExecutionIdentityError(
                "NATIVE_TASK_ID_REQUIRES_SEPARATE_OBSERVED_TASK_BINDING"
            )

        tool_response = payload.get("tool_response")
        if not isinstance(tool_response, Mapping):
            raise AgentWorkExecutionIdentityError("MISSING_OR_INVALID_TOOL_RESPONSE")
        raw_agent_id = tool_response.get("agentId")
        agent_id = raw_agent_id.strip() if isinstance(raw_agent_id, str) and raw_agent_id.strip() else None
        post_payload_digest = _digest(dict(payload))

        con = _connect(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            spawn = con.execute(
                "SELECT * FROM fr2_agent_spawn_observations WHERE spawn_tool_use_id=?",
                (spawn_tool_use_id,),
            ).fetchone()
            if spawn is None:
                raise AgentWorkExecutionIdentityError("POST_WITHOUT_BOUND_PRE")
            if spawn["parent_session_id"] != session_id:
                raise AgentWorkExecutionIdentityError(
                    f"SESSION_ID_MISMATCH:{spawn['parent_session_id']}:{session_id}"
                )
            if spawn["status"] == "BOUND":
                raise AgentWorkExecutionIdentityError("SPAWN_ALREADY_BOUND")
            if spawn["status"] == "AGENT_ID_UNKNOWN":
                raise AgentWorkExecutionIdentityError(
                    "AGENT_ID_UNKNOWN_REQUIRES_RECONCILIATION"
                )
            if agent_id is None:
                con.execute(
                    """UPDATE fr2_agent_spawn_observations
                       SET status='AGENT_ID_UNKNOWN',agent_identity_state='UNKNOWN',
                           post_payload_digest=?,observed_post_at=?
                       WHERE spawn_tool_use_id=?""",
                    (post_payload_digest, time.time(), spawn_tool_use_id),
                )
                con.execute("COMMIT")
                return None

            # One transaction writes the child binding and marks the spawn observation bound.
            # No intermediate state may claim a child binding while the spawn record remains
            # unbound (or vice versa).
            con.execute(
                """INSERT INTO fr2_work_execution_bindings(
                     binding_id,workpackage_id,work_generation,parent_execution_id,
                     child_runtime_kind,child_execution_id,native_agent_id,native_task_id,
                     identity_provenance,identity_observed_at,status,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,'BOUND',?)""",
                (
                    binding_id,
                    spawn["workpackage_id"],
                    spawn["work_generation"],
                    spawn_tool_use_id,
                    child_runtime_kind,
                    agent_id,
                    agent_id,
                    None,
                    identity_provenance,
                    time.time(),
                    time.time(),
                ),
            )
            _append_event(
                con,
                binding_id,
                "CHILD_IDENTITY_BOUND",
                {
                    "workpackage_id": spawn["workpackage_id"],
                    "work_generation": spawn["work_generation"],
                    "child_runtime_kind": child_runtime_kind,
                    "child_execution_id": agent_id,
                    "native_agent_id": agent_id,
                    "native_task_id": None,
                    "identity_provenance": identity_provenance,
                    "spawn_tool_use_id": spawn_tool_use_id,
                    "parent_session_id": session_id,
                },
            )
            con.execute(
                """UPDATE fr2_agent_spawn_observations
                   SET status='BOUND',agent_id=?,agent_identity_state='OBSERVED',
                       binding_id=?,native_task_id=NULL,post_payload_digest=?,observed_post_at=?
                   WHERE spawn_tool_use_id=?""",
                (
                    agent_id,
                    binding_id,
                    post_payload_digest,
                    time.time(),
                    spawn_tool_use_id,
                ),
            )
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

        return WorkExecutionBinding(
            binding_id=binding_id,
            workpackage_id=spawn["workpackage_id"],
            work_generation=spawn["work_generation"],
            child_runtime_kind=child_runtime_kind,
            child_execution_id=agent_id,
            native_agent_id=agent_id,
            native_task_id=None,
            identity_provenance=identity_provenance,
            status="BOUND",
        )

    def spawn_snapshot(self, spawn_tool_use_id: str) -> dict[str, Any]:
        con = _connect(self.db_path)
        try:
            row = con.execute(
                "SELECT * FROM fr2_agent_spawn_observations WHERE spawn_tool_use_id=?",
                (str(spawn_tool_use_id),),
            ).fetchone()
            if row is None:
                raise AgentWorkExecutionIdentityError("UNKNOWN_SPAWN_TOOL_USE_ID")
            return {"schema": SCHEMA, **dict(row)}
        finally:
            con.close()
