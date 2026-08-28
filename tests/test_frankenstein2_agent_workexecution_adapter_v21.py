#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from frankenstein2_agent_workexecution_adapter_v21 import (  # noqa: E402
    AgentWorkExecutionAdapter,
    AgentWorkExecutionIdentityError,
)


def _pre(
    tool_use_id: str,
    package: str,
    *,
    session: str = "session-1",
    prompt: str | None = None,
) -> dict:
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
) -> dict:
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


class AgentWorkExecutionAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "unified.sqlite"
        self.adapter = AgentWorkExecutionAdapter(self.db)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_adapter_created_db_installs_v2_single_completion_invariant(self) -> None:
        con = sqlite3.connect(str(self.db))
        try:
            indexes = {
                row[1]: int(row[2])
                for row in con.execute("PRAGMA index_list('fr2_completion_evidence')").fetchall()
            }
        finally:
            con.close()
        self.assertEqual(indexes.get("idx_fr2_single_completion_per_binding"), 1)

    def test_zero_handoff_marker_fails_closed_without_write(self) -> None:
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError, "HANDOFF_MARKER_CARDINALITY:0"
        ):
            self.adapter.record_agent_pretool(
                _pre("spawn-a", "wp-a", prompt="No marker here"),
                expected_workpackage_id="wp-a",
                expected_work_generation="g1",
            )
        self.assertEqual(_count(self.db, "fr2_agent_spawn_observations"), 0)

    def test_multiple_handoff_markers_fail_closed_without_write(self) -> None:
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError, "HANDOFF_MARKER_CARDINALITY:2"
        ):
            self.adapter.record_agent_pretool(
                _pre("spawn-a", "wp-a", prompt="HANDOFF wp-a\nHANDOFF wp-b\n"),
                expected_workpackage_id="wp-a",
                expected_work_generation="g1",
            )
        self.assertEqual(_count(self.db, "fr2_agent_spawn_observations"), 0)

    def test_displaced_handoff_marker_uses_same_fail_closed_contract_as_identity_parser(self) -> None:
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError, "HANDOFF_MARKER_NOT_FIRST_LINE"
        ):
            self.adapter.record_agent_pretool(
                _pre("spawn-a", "wp-a", prompt="wrapper text\nHANDOFF wp-a\n"),
                expected_workpackage_id="wp-a",
                expected_work_generation="g1",
            )
        self.assertEqual(_count(self.db, "fr2_agent_spawn_observations"), 0)

    def test_handoff_package_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError, "HANDOFF_PACKAGE_MISMATCH"
        ):
            self.adapter.record_agent_pretool(
                _pre("spawn-a", "wp-other"),
                expected_workpackage_id="wp-a",
                expected_work_generation="g1",
            )
        self.assertEqual(_count(self.db, "fr2_agent_spawn_observations"), 0)

    def test_tool_use_id_cannot_bind_two_packages(self) -> None:
        self.adapter.record_agent_pretool(
            _pre("spawn-x", "wp-a"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g1",
        )
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError, "SPAWN_TOOL_USE_ID_ALREADY_BOUND"
        ):
            self.adapter.record_agent_pretool(
                _pre("spawn-x", "wp-b"),
                expected_workpackage_id="wp-b",
                expected_work_generation="g1",
            )
        self.assertEqual(_count(self.db, "fr2_agent_spawn_observations"), 1)

    def test_same_package_generation_cannot_silently_fan_out(self) -> None:
        self.adapter.record_agent_pretool(
            _pre("spawn-a", "wp-a"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g1",
        )
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError, "PACKAGE_GENERATION_ALREADY_HAS_SPAWN"
        ):
            self.adapter.record_agent_pretool(
                _pre("spawn-b", "wp-a"),
                expected_workpackage_id="wp-a",
                expected_work_generation="g1",
            )
        self.assertEqual(_count(self.db, "fr2_agent_spawn_observations"), 1)

    def test_new_work_generation_may_have_distinct_spawn(self) -> None:
        self.adapter.record_agent_pretool(
            _pre("spawn-g1", "wp-a"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g1",
        )
        self.adapter.record_agent_pretool(
            _pre("spawn-g2", "wp-a"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g2",
        )
        self.assertEqual(_count(self.db, "fr2_agent_spawn_observations"), 2)

    def test_absent_agent_id_remains_unknown_and_mints_no_binding(self) -> None:
        self.adapter.record_agent_pretool(
            _pre("spawn-a", "wp-a"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g7",
        )
        result = self.adapter.record_agent_posttool(
            _post("spawn-a", None),
            binding_id="binding-a",
            child_runtime_kind="CLAUDE_AGENT",
            identity_provenance="test-observed-posttool",
        )
        self.assertIsNone(result)
        snap = self.adapter.spawn_snapshot("spawn-a")
        self.assertEqual(snap["status"], "AGENT_ID_UNKNOWN")
        self.assertEqual(snap["agent_identity_state"], "UNKNOWN")
        self.assertIsNone(snap["agent_id"])
        self.assertIsNone(snap["binding_id"])
        self.assertEqual(_count(self.db, "fr2_work_execution_bindings"), 0)

    def test_unknown_agent_id_is_sticky_and_late_post_cannot_mint_binding(self) -> None:
        self.adapter.record_agent_pretool(
            _pre("spawn-a", "wp-a"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g7",
        )
        self.assertIsNone(
            self.adapter.record_agent_posttool(
                _post("spawn-a", None),
                binding_id="binding-a",
                child_runtime_kind="CLAUDE_AGENT",
                identity_provenance="test-first-post-unknown",
            )
        )
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError,
            "AGENT_ID_UNKNOWN_REQUIRES_RECONCILIATION",
        ):
            self.adapter.record_agent_posttool(
                _post("spawn-a", "agent-late"),
                binding_id="binding-a",
                child_runtime_kind="CLAUDE_AGENT",
                identity_provenance="test-late-post-replay",
            )
        snap = self.adapter.spawn_snapshot("spawn-a")
        self.assertEqual(snap["status"], "AGENT_ID_UNKNOWN")
        self.assertEqual(snap["agent_identity_state"], "UNKNOWN")
        self.assertIsNone(snap["agent_id"])
        self.assertIsNone(snap["binding_id"])
        self.assertEqual(_count(self.db, "fr2_work_execution_bindings"), 0)

    def test_same_session_interleave_reverse_post_preserves_identity(self) -> None:
        self.adapter.record_agent_pretool(
            _pre("spawn-a", "wp-a"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g1",
        )
        self.adapter.record_agent_pretool(
            _pre("spawn-b", "wp-b"),
            expected_workpackage_id="wp-b",
            expected_work_generation="g2",
        )
        bound_b = self.adapter.record_agent_posttool(
            _post("spawn-b", "agent-b"),
            binding_id="binding-b",
            child_runtime_kind="CLAUDE_AGENT",
            identity_provenance="test-post-b",
        )
        bound_a = self.adapter.record_agent_posttool(
            _post("spawn-a", "agent-a"),
            binding_id="binding-a",
            child_runtime_kind="CLAUDE_AGENT",
            identity_provenance="test-post-a",
        )
        self.assertIsNotNone(bound_a)
        self.assertIsNotNone(bound_b)
        assert bound_a is not None and bound_b is not None
        self.assertEqual(
            (bound_a.workpackage_id, bound_a.work_generation, bound_a.native_agent_id),
            ("wp-a", "g1", "agent-a"),
        )
        self.assertEqual(
            (bound_b.workpackage_id, bound_b.work_generation, bound_b.native_agent_id),
            ("wp-b", "g2", "agent-b"),
        )
        self.assertEqual(self.adapter.spawn_snapshot("spawn-a")["binding_id"], "binding-a")
        self.assertEqual(self.adapter.spawn_snapshot("spawn-b")["binding_id"], "binding-b")

    def test_post_session_mismatch_cannot_mint_binding(self) -> None:
        self.adapter.record_agent_pretool(
            _pre("spawn-a", "wp-a", session="session-a"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g1",
        )
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError, "SESSION_ID_MISMATCH"
        ):
            self.adapter.record_agent_posttool(
                _post("spawn-a", "agent-a", session="session-b"),
                binding_id="binding-a",
                child_runtime_kind="CLAUDE_AGENT",
                identity_provenance="test-post",
            )
        self.assertEqual(self.adapter.spawn_snapshot("spawn-a")["status"], "PRE_OBSERVED")
        self.assertEqual(_count(self.db, "fr2_work_execution_bindings"), 0)

    def test_agent_adapter_cannot_invent_task_identity(self) -> None:
        self.adapter.record_agent_pretool(
            _pre("spawn-a", "wp-a"),
            expected_workpackage_id="wp-a",
            expected_work_generation="g1",
        )
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError,
            "NATIVE_TASK_ID_REQUIRES_SEPARATE_OBSERVED_TASK_BINDING",
        ):
            self.adapter.record_agent_posttool(
                _post("spawn-a", "agent-17"),
                binding_id="binding-a",
                child_runtime_kind="CLAUDE_AGENT",
                identity_provenance="test-post",
                native_task_id="task-17",
            )
        self.assertEqual(self.adapter.spawn_snapshot("spawn-a")["status"], "PRE_OBSERVED")
        self.assertEqual(_count(self.db, "fr2_work_execution_bindings"), 0)


if __name__ == "__main__":
    unittest.main()
