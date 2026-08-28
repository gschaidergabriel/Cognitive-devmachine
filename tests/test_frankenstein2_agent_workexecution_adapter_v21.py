#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "frankenstein2_agent_workexecution_adapter_v21.py"
SPEC = importlib.util.spec_from_file_location(
    "frankenstein2_agent_workexecution_adapter_v21", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

AgentWorkExecutionAdapter = mod.AgentWorkExecutionAdapter
AgentWorkExecutionIdentityError = mod.AgentWorkExecutionIdentityError


def _pre(
    tool_use_id: str,
    package: str,
    *,
    session: str = "session-1",
    prompt: str | None = None,
):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Agent",
        "tool_use_id": tool_use_id,
        "session_id": session,
        "tool_input": {
            "prompt": prompt if prompt is not None else f"HANDOFF {package}\nDo bounded work."
        },
    }


def _post(
    tool_use_id: str,
    agent_id: str | None,
    *,
    session: str = "session-1",
):
    response = {} if agent_id is None else {"agentId": agent_id}
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Agent",
        "tool_use_id": tool_use_id,
        "session_id": session,
        "tool_response": response,
    }


def _count(db: Path, table: str) -> int:
    con = sqlite3.connect(str(db))
    try:
        return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        con.close()


def test_zero_handoff_marker_fails_closed(tmp_path: Path) -> None:
    db = tmp_path / "u.sqlite"
    adapter = AgentWorkExecutionAdapter(db)
    with pytest.raises(
        AgentWorkExecutionIdentityError, match="HANDOFF_MARKER_CARDINALITY:0"
    ):
        adapter.record_agent_pretool(
            _pre("spawn-a", "wp-a", prompt="No marker here"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g1",
        )
    assert _count(db, "fr2_agent_spawn_observations") == 0


def test_multiple_handoff_markers_fail_closed(tmp_path: Path) -> None:
    db = tmp_path / "u.sqlite"
    adapter = AgentWorkExecutionAdapter(db)
    with pytest.raises(
        AgentWorkExecutionIdentityError, match="HANDOFF_MARKER_CARDINALITY:2"
    ):
        adapter.record_agent_pretool(
            _pre("spawn-a", "wp-a", prompt="HANDOFF wp-a\nHANDOFF wp-b\n"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g1",
        )
    assert _count(db, "fr2_agent_spawn_observations") == 0


def test_handoff_package_mismatch_fails_closed(tmp_path: Path) -> None:
    db = tmp_path / "u.sqlite"
    adapter = AgentWorkExecutionAdapter(db)
    with pytest.raises(
        AgentWorkExecutionIdentityError, match="HANDOFF_PACKAGE_MISMATCH"
    ):
        adapter.record_agent_pretool(
            _pre("spawn-a", "wp-other"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g1",
        )
    assert _count(db, "fr2_agent_spawn_observations") == 0


def test_tool_use_id_cannot_bind_two_packages(tmp_path: Path) -> None:
    db = tmp_path / "u.sqlite"
    adapter = AgentWorkExecutionAdapter(db)
    adapter.record_agent_pretool(
        _pre("spawn-x", "wp-a"),
        expected_workpackage_id="wp-a",
        expected_work_generation="g1",
    )
    with pytest.raises(
        AgentWorkExecutionIdentityError, match="SPAWN_TOOL_USE_ID_ALREADY_BOUND"
    ):
        adapter.record_agent_pretool(
            _pre("spawn-x", "wp-b"),
            expected_workpackage_id="wp-b",
            expected_work_generation="g1",
        )
    assert _count(db, "fr2_agent_spawn_observations") == 1


def test_absent_agent_id_remains_unknown_and_mints_no_binding(tmp_path: Path) -> None:
    db = tmp_path / "u.sqlite"
    adapter = AgentWorkExecutionAdapter(db)
    adapter.record_agent_pretool(
        _pre("spawn-a", "wp-a"),
        expected_workpackage_id="wp-a",
        expected_work_generation="g7",
    )
    result = adapter.record_agent_posttool(
        _post("spawn-a", None),
        binding_id="binding-a",
        child_runtime_kind="CLAUDE_AGENT",
        identity_provenance="test-observed-posttool",
    )
    assert result is None
    snap = adapter.spawn_snapshot("spawn-a")
    assert snap["status"] == "AGENT_ID_UNKNOWN"
    assert snap["agent_identity_state"] == "UNKNOWN"
    assert snap["agent_id"] is None
    assert snap["binding_id"] is None
    assert _count(db, "fr2_work_execution_bindings") == 0


def test_same_session_interleave_reverse_post_preserves_identity(tmp_path: Path) -> None:
    db = tmp_path / "u.sqlite"
    adapter = AgentWorkExecutionAdapter(db)
    adapter.record_agent_pretool(
        _pre("spawn-a", "wp-a"),
        expected_workpackage_id="wp-a",
        expected_work_generation="g1",
    )
    adapter.record_agent_pretool(
        _pre("spawn-b", "wp-b"),
        expected_workpackage_id="wp-b",
        expected_work_generation="g2",
    )
    b = adapter.record_agent_posttool(
        _post("spawn-b", "agent-b"),
        binding_id="binding-b",
        child_runtime_kind="CLAUDE_AGENT",
        identity_provenance="test-post-b",
    )
    a = adapter.record_agent_posttool(
        _post("spawn-a", "agent-a"),
        binding_id="binding-a",
        child_runtime_kind="CLAUDE_AGENT",
        identity_provenance="test-post-a",
    )
    assert b is not None and a is not None
    assert (b.workpackage_id, b.work_generation, b.native_agent_id) == (
        "wp-b",
        "g2",
        "agent-b",
    )
    assert (a.workpackage_id, a.work_generation, a.native_agent_id) == (
        "wp-a",
        "g1",
        "agent-a",
    )
    assert adapter.spawn_snapshot("spawn-a")["binding_id"] == "binding-a"
    assert adapter.spawn_snapshot("spawn-b")["binding_id"] == "binding-b"

    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    try:
        rows = {
            row["binding_id"]: dict(row)
            for row in con.execute(
                "SELECT binding_id,workpackage_id,work_generation,parent_execution_id,"
                "native_agent_id,native_task_id FROM fr2_work_execution_bindings"
            )
        }
    finally:
        con.close()
    assert rows["binding-a"]["parent_execution_id"] == "spawn-a"
    assert rows["binding-b"]["parent_execution_id"] == "spawn-b"
    assert rows["binding-a"]["native_agent_id"] == "agent-a"
    assert rows["binding-b"]["native_agent_id"] == "agent-b"


def test_post_session_mismatch_cannot_mint_binding(tmp_path: Path) -> None:
    db = tmp_path / "u.sqlite"
    adapter = AgentWorkExecutionAdapter(db)
    adapter.record_agent_pretool(
        _pre("spawn-a", "wp-a", session="session-a"),
        expected_workpackage_id="wp-a",
        expected_work_generation="g1",
    )
    with pytest.raises(AgentWorkExecutionIdentityError, match="SESSION_ID_MISMATCH"):
        adapter.record_agent_posttool(
            _post("spawn-a", "agent-a", session="session-b"),
            binding_id="binding-a",
            child_runtime_kind="CLAUDE_AGENT",
            identity_provenance="test-post",
        )
    assert adapter.spawn_snapshot("spawn-a")["status"] == "PRE_OBSERVED"
    assert _count(db, "fr2_work_execution_bindings") == 0


def test_task_identity_remains_distinct_from_agent_identity(tmp_path: Path) -> None:
    db = tmp_path / "u.sqlite"
    adapter = AgentWorkExecutionAdapter(db)
    adapter.record_agent_pretool(
        _pre("spawn-a", "wp-a"),
        expected_workpackage_id="wp-a",
        expected_work_generation="g1",
    )
    bound = adapter.record_agent_posttool(
        _post("spawn-a", "agent-17"),
        binding_id="binding-a",
        child_runtime_kind="CLAUDE_AGENT",
        identity_provenance="test-post",
        native_task_id="task-17",
    )
    assert bound is not None
    assert bound.native_agent_id == "agent-17"
    assert bound.native_task_id == "task-17"
    assert bound.native_agent_id != bound.native_task_id
