from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.frankenstein2_agent_workexecution_adapter_v21 import (
    AgentWorkExecutionAdapter,
    AgentWorkExecutionIdentityError,
)


class AgentWorkExecutionHandoffParserConsistencyTests(unittest.TestCase):
    """Keep the live WorkExecution adapter aligned with the strict hook-identity contract."""

    def test_displaced_handoff_marker_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            adapter = AgentWorkExecutionAdapter(Path(td) / "work.sqlite")
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Agent",
                "tool_use_id": "spawn-1",
                "session_id": "session-1",
                "tool_input": {
                    "prompt": "WRAPPER TEXT\nHANDOFF wp-1\nDo the bounded delegated work."
                },
            }

            # frankenstein2_agent_hook_identity_v1.parse_handoff_marker() rejects this
            # shape because HANDOFF is not the first line. The live adapter must not
            # admit a broader identity language for the same causal boundary.
            with self.assertRaisesRegex(
                AgentWorkExecutionIdentityError,
                "HANDOFF_MARKER_NOT_FIRST_LINE",
            ):
                adapter.record_agent_pretool(
                    payload,
                    expected_workpackage_id="wp-1",
                    expected_work_generation="g1",
                )


if __name__ == "__main__":
    unittest.main()
