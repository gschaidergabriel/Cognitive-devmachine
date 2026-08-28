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


def _pre(tool_use_id: str, package: str, generation: str) -> tuple[dict, str, str]:
    return (
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Agent",
            "tool_use_id": tool_use_id,
            "session_id": "session-cardinality",
            "tool_input": {"prompt": f"HANDOFF {package}\nDo bounded work."},
        },
        package,
        generation,
    )


class AgentWorkExecutionCardinalityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "unified.sqlite"
        self.adapter = AgentWorkExecutionAdapter(self.db)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _record(self, tool_use_id: str, package: str, generation: str) -> None:
        payload, package_id, work_generation = _pre(tool_use_id, package, generation)
        self.adapter.record_agent_pretool(
            payload,
            expected_workpackage_id=package_id,
            expected_work_generation=work_generation,
        )

    def test_same_package_generation_cannot_silently_fan_out_to_second_agent_call(self) -> None:
        self._record("spawn-a", "wp-a", "g1")
        with self.assertRaisesRegex(
            AgentWorkExecutionIdentityError,
            "PACKAGE_GENERATION_ALREADY_HAS_SPAWN",
        ):
            self._record("spawn-b", "wp-a", "g1")

        con = sqlite3.connect(str(self.db))
        try:
            rows = con.execute(
                "SELECT spawn_tool_use_id FROM fr2_agent_spawn_observations "
                "WHERE workpackage_id='wp-a' AND work_generation='g1'"
            ).fetchall()
        finally:
            con.close()
        self.assertEqual(rows, [("spawn-a",)])

    def test_new_generation_may_have_its_own_agent_call(self) -> None:
        self._record("spawn-g1", "wp-a", "g1")
        self._record("spawn-g2", "wp-a", "g2")

        con = sqlite3.connect(str(self.db))
        try:
            rows = con.execute(
                "SELECT work_generation,spawn_tool_use_id FROM fr2_agent_spawn_observations "
                "WHERE workpackage_id='wp-a' ORDER BY work_generation"
            ).fetchall()
        finally:
            con.close()
        self.assertEqual(rows, [("g1", "spawn-g1"), ("g2", "spawn-g2")])


if __name__ == "__main__":
    unittest.main()
