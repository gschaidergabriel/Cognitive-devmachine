from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.frankenstein2_effect_lifecycle_v1 import EffectLifecycleStore
from tools.frankenstein2_hook_invocation_adapter_v1 import (
    HookInvocationIdentityError,
    build_effect_request_from_pretool,
    require_matching_posttool,
)


class HookInvocationAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.store = EffectLifecycleStore(Path(self.td.name) / "effects.sqlite")

    def tearDown(self) -> None:
        self.td.cleanup()

    def _pre(self, tool_use_id: str):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_use_id": tool_use_id,
            "session_id": "shared-session",
            "tool_name": "Bash",
            # Keep the semantic request deliberately identical so only the call-scoped
            # runtime identity can distinguish the two overlapping invocations.
            "tool_input": {"command": "printf same"},
        }
        req = build_effect_request_from_pretool(
            self.store,
            payload,
            agent_id="agent-1",
            task_id="task-shared",
            turn_id="turn-shared",
            causal_id=f"cause-{tool_use_id}",
            generation=29,
            effect_scope="TEST_ONLY",
        )
        self.store.create_request(req)
        return req

    @staticmethod
    def _post(tool_use_id: str, event: str = "PostToolUse") -> dict[str, object]:
        return {
            "hook_event_name": event,
            "tool_use_id": tool_use_id,
            "session_id": "shared-session",
            "tool_name": "Bash",
            "tool_response": {"stdout": "same", "exit_code": 0},
        }

    def test_same_session_identical_calls_can_close_in_reverse_order_without_cross_talk(self) -> None:
        req_a = self._pre("tool-call-A")
        req_b = self._pre("tool-call-B")

        # The second call returns first. A session-scoped mutable "current effect"
        # pointer would be vulnerable here; exact call-scoped identity must not be.
        ctx_b = require_matching_posttool(req_b, self._post("tool-call-B"))
        ctx_a = require_matching_posttool(req_a, self._post("tool-call-A"))

        self.assertEqual(ctx_b.invocation_id, "tool-call-B")
        self.assertEqual(ctx_a.invocation_id, "tool-call-A")
        self.assertEqual(self.store.snapshot("tool-call-A")["request"]["invocation_id"], "tool-call-A")
        self.assertEqual(self.store.snapshot("tool-call-B")["request"]["invocation_id"], "tool-call-B")

        # Transplanting B's post event onto A must fail before any caller can treat
        # the result as belonging to A, even though session/tool/input/output match.
        with self.assertRaisesRegex(HookInvocationIdentityError, "INVOCATION_ID_MISMATCH"):
            require_matching_posttool(req_a, self._post("tool-call-B"))

    def test_posttool_failure_uses_the_same_exact_invocation_binding(self) -> None:
        req_a = self._pre("tool-call-A")
        ctx = require_matching_posttool(req_a, self._post("tool-call-A", "PostToolUseFailure"))
        self.assertEqual(ctx.invocation_id, "tool-call-A")

        with self.assertRaisesRegex(HookInvocationIdentityError, "INVOCATION_ID_MISMATCH"):
            require_matching_posttool(req_a, self._post("tool-call-B", "PostToolUseFailure"))

    def test_missing_pretool_call_identity_fails_closed_without_session_fallback(self) -> None:
        with self.assertRaisesRegex(HookInvocationIdentityError, "MISSING_OR_INVALID_TOOL_USE_ID"):
            build_effect_request_from_pretool(
                self.store,
                {
                    "hook_event_name": "PreToolUse",
                    "session_id": "shared-session",
                    "tool_name": "Bash",
                    "tool_input": {"command": "printf same"},
                },
                agent_id="agent-1",
                task_id="task-shared",
                turn_id="turn-shared",
                causal_id="cause-missing-id",
                generation=29,
                effect_scope="TEST_ONLY",
            )


if __name__ == "__main__":
    unittest.main()
