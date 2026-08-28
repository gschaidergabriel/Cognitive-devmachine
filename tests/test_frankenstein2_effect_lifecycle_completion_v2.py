import tempfile
from pathlib import Path
import unittest

from tools.frankenstein2_effect_lifecycle_v1 import (
    AdmissionDecision,
    EffectLifecycleError,
    EffectLifecycleStore,
    V2_COMPLETION_EVIDENCE_CLASS,
    WorldOutcome,
)
from tools.frankenstein2_hook_invocation_adapter_v1 import (
    HookInvocationIdentityError,
    build_effect_request_from_pretool,
    require_matching_posttool,
)


class EffectLifecycleCompletionV2IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "effects.sqlite"
        self.store = EffectLifecycleStore(self.db)

    def tearDown(self):
        self.td.cleanup()

    def _prepare_success_chain(
        self,
        *,
        invocation_id: str = "call-A",
        expected_source: str | None = "src-A",
        execution_source: str | None = "src-A",
        duplicate_state: str | None = "UNIQUE",
        execution_status: str | None = "SUCCEEDED",
        world_evidence: str | None = "world-proof-A",
    ) -> None:
        req = self.store.build_request(
            invocation_id=invocation_id,
            session_id="session-1",
            agent_id="frankenstein-2",
            task_id="task-1",
            turn_id="turn-1",
            causal_id="cause-1",
            generation=7,
            tool_name="bounded-tool",
            normalized_arguments={"x": 1},
            effect_scope="TEST_ONLY",
        )
        self.store.create_request(req, now_ts=1.0)
        if expected_source is not None:
            self.store.bind_completion_source(
                invocation_id,
                source_digest=expected_source,
                now_ts=2.0,
            )
        self.store.decide(
            invocation_id,
            AdmissionDecision.ALLOW,
            reason="test admission",
            now_ts=3.0,
        )
        self.store.record_enforcement(
            invocation_id,
            boundary_id="effect-gate-1",
            dispatch_permitted=True,
            now_ts=4.0,
        )
        self.store.mark_submitted(invocation_id, now_ts=5.0)
        self.store.record_execution(
            invocation_id,
            executable_id="tool-v1",
            command_digest="cmd-A",
            environment_id="sandbox-A",
            exit_code=0,
            result_digest="result-A",
            now_ts=6.0,
        )
        if execution_source is not None and duplicate_state is not None and execution_status is not None:
            self.store.record_execution_v2_metadata(
                invocation_id,
                source_digest=execution_source,
                duplicate_state=duplicate_state,
                status=execution_status,
                now_ts=7.0,
            )
        self.store.verify_world_effect(
            invocation_id,
            WorldOutcome.SUCCEEDED,
            evidence_digest=world_evidence,
            now_ts=8.0,
        )
        self.store.reenter_result(invocation_id, result_digest="result-A", now_ts=9.0)

    def test_v2_bound_success_is_only_completion_minting_path(self):
        self._prepare_success_chain()
        receipt = self.store.issue_completion_evidence("call-A", now_ts=10.0)
        self.assertTrue(receipt)
        snap = self.store.snapshot("call-A")
        self.assertEqual(snap["completion"]["evidence_class"], V2_COMPLETION_EVIDENCE_CLASS)
        self.assertEqual(snap["completion"]["receipt_digest"], receipt)
        self.assertEqual(snap["completion_v2_source"]["expected_source_digest"], "src-A")
        self.assertEqual(snap["execution_v2"]["source_digest"], "src-A")
        self.assertEqual(snap["execution_v2"]["duplicate_state"], "UNIQUE")

    def test_legacy_complete_chain_without_v2_evidence_cannot_mint(self):
        self._prepare_success_chain(expected_source=None, execution_source=None)
        legacy = self.store.completion_status("call-A")
        self.assertTrue(legacy.closable)
        with self.assertRaisesRegex(EffectLifecycleError, "COMPLETION_V2_GATE_OPEN"):
            self.store.issue_completion_evidence("call-A", now_ts=10.0)
        self.assertIsNone(self.store.snapshot("call-A")["completion"])

    def test_source_drift_between_pre_submission_binding_and_execution_is_rejected(self):
        self._prepare_success_chain(expected_source="src-A", execution_source="src-B")
        with self.assertRaisesRegex(EffectLifecycleError, "EXECUTION_SOURCE_DRIFT"):
            self.store.issue_completion_evidence("call-A", now_ts=10.0)
        self.assertIsNone(self.store.snapshot("call-A")["completion"])

    def test_unresolved_duplicate_cannot_mint_completion(self):
        self._prepare_success_chain(duplicate_state="UNRESOLVED_DUPLICATE")
        with self.assertRaisesRegex(EffectLifecycleError, "EXECUTION_DUPLICATE_UNRESOLVED"):
            self.store.issue_completion_evidence("call-A", now_ts=10.0)
        self.assertIsNone(self.store.snapshot("call-A")["completion"])

    def test_missing_world_evidence_is_rejected_by_v2_even_when_v1_status_is_closable(self):
        self._prepare_success_chain(world_evidence=None)
        legacy = self.store.completion_status("call-A")
        self.assertTrue(legacy.closable)
        with self.assertRaisesRegex(EffectLifecycleError, "MISSING_WORLD_EVIDENCE"):
            self.store.issue_completion_evidence("call-A", now_ts=10.0)
        self.assertIsNone(self.store.snapshot("call-A")["completion"])

    def test_source_binding_is_create_once_and_must_precede_submission(self):
        req = self.store.build_request(
            invocation_id="call-B",
            session_id="session-1",
            agent_id="frankenstein-2",
            task_id="task-1",
            turn_id="turn-1",
            causal_id="cause-1",
            generation=1,
            tool_name="bounded-tool",
            normalized_arguments={},
            effect_scope="TEST_ONLY",
        )
        self.store.create_request(req)
        self.store.bind_completion_source("call-B", source_digest="src-A")
        with self.assertRaisesRegex(EffectLifecycleError, "SOURCE_ALREADY_BOUND"):
            self.store.bind_completion_source("call-B", source_digest="src-B")

        req2 = self.store.build_request(
            invocation_id="call-C",
            session_id="session-1",
            agent_id="frankenstein-2",
            task_id="task-1",
            turn_id="turn-1",
            causal_id="cause-1",
            generation=1,
            tool_name="bounded-tool",
            normalized_arguments={},
            effect_scope="TEST_ONLY",
        )
        self.store.create_request(req2)
        self.store.decide("call-C", AdmissionDecision.ALLOW, reason="test")
        self.store.record_enforcement("call-C", boundary_id="gate", dispatch_permitted=True)
        self.store.mark_submitted("call-C")
        with self.assertRaisesRegex(EffectLifecycleError, "SOURCE_BINDING_REQUIRES_PRE_SUBMISSION"):
            self.store.bind_completion_source("call-C", source_digest="late-source")

    def test_same_session_two_call_interleaving_rejects_cross_invocation_result_and_closes_independently(self):
        """Falsify mutable session-scoped effect correlation with reordered same-session calls."""
        req_a = self.store.build_request(
            invocation_id="tool-use-A",
            session_id="shared-session",
            agent_id="agent-1",
            task_id="task-A",
            turn_id="turn-A",
            causal_id="cause-A",
            generation=11,
            tool_name="bounded-tool",
            normalized_arguments={"slot": "A"},
            effect_scope="TEST_ONLY",
        )
        req_b = self.store.build_request(
            invocation_id="tool-use-B",
            session_id="shared-session",
            agent_id="agent-1",
            task_id="task-B",
            turn_id="turn-B",
            causal_id="cause-B",
            generation=11,
            tool_name="bounded-tool",
            normalized_arguments={"slot": "B"},
            effect_scope="TEST_ONLY",
        )
        self.store.create_request(req_a, now_ts=1.0)
        self.store.create_request(req_b, now_ts=1.1)
        self.store.bind_completion_source("tool-use-A", source_digest="src-A", now_ts=2.0)
        self.store.bind_completion_source("tool-use-B", source_digest="src-B", now_ts=2.1)

        # Deliberately interleave/reorder state transitions inside one session.
        self.store.decide("tool-use-B", AdmissionDecision.ALLOW, reason="B admitted", now_ts=3.0)
        self.store.decide("tool-use-A", AdmissionDecision.ALLOW, reason="A admitted", now_ts=3.1)
        self.store.record_enforcement("tool-use-A", boundary_id="gate-A", dispatch_permitted=True, now_ts=4.0)
        self.store.record_enforcement("tool-use-B", boundary_id="gate-B", dispatch_permitted=True, now_ts=4.1)
        self.store.mark_submitted("tool-use-B", now_ts=5.0)
        self.store.mark_submitted("tool-use-A", now_ts=5.1)
        self.store.record_execution(
            "tool-use-B",
            executable_id="tool-v1",
            command_digest="cmd-B",
            environment_id="sandbox",
            exit_code=0,
            result_digest="result-B",
            now_ts=6.0,
        )
        self.store.record_execution(
            "tool-use-A",
            executable_id="tool-v1",
            command_digest="cmd-A",
            environment_id="sandbox",
            exit_code=0,
            result_digest="result-A",
            now_ts=6.1,
        )
        self.store.record_execution_v2_metadata(
            "tool-use-B",
            source_digest="src-B",
            duplicate_state="UNIQUE",
            status="SUCCEEDED",
            now_ts=7.0,
        )
        self.store.record_execution_v2_metadata(
            "tool-use-A",
            source_digest="src-A",
            duplicate_state="UNIQUE",
            status="SUCCEEDED",
            now_ts=7.1,
        )
        self.store.verify_world_effect(
            "tool-use-A", WorldOutcome.SUCCEEDED, evidence_digest="world-A", now_ts=8.0
        )
        self.store.verify_world_effect(
            "tool-use-B", WorldOutcome.SUCCEEDED, evidence_digest="world-B", now_ts=8.1
        )

        # A mutable session singleton would be vulnerable to attaching B's latest result to A.
        with self.assertRaisesRegex(EffectLifecycleError, "RESULT_REENTRY_DIGEST_MISMATCH"):
            self.store.reenter_result("tool-use-A", result_digest="result-B", now_ts=9.0)
        self.assertIsNone(self.store.snapshot("tool-use-A")["reentry"])

        # Exact invocation correlation survives the adversarial reorder and both chains close.
        self.store.reenter_result("tool-use-B", result_digest="result-B", now_ts=9.1)
        self.store.reenter_result("tool-use-A", result_digest="result-A", now_ts=9.2)
        receipt_b = self.store.issue_completion_evidence("tool-use-B", now_ts=10.0)
        receipt_a = self.store.issue_completion_evidence("tool-use-A", now_ts=10.1)
        self.assertTrue(receipt_a)
        self.assertTrue(receipt_b)
        snap_a = self.store.snapshot("tool-use-A")
        snap_b = self.store.snapshot("tool-use-B")
        self.assertEqual(snap_a["reentry"]["result_digest"], "result-A")
        self.assertEqual(snap_b["reentry"]["result_digest"], "result-B")
        self.assertEqual(snap_a["completion"]["evidence_class"], V2_COMPLETION_EVIDENCE_CLASS)
        self.assertEqual(snap_b["completion"]["evidence_class"], V2_COMPLETION_EVIDENCE_CLASS)

    def test_hook_adapter_uses_tool_use_id_and_survives_reverse_posttool_order(self):
        pre_a = {
            "hook_event_name": "PreToolUse",
            "session_id": "shared-session",
            "tool_use_id": "call-A",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/a", "content": "A"},
        }
        pre_b = {
            "hook_event_name": "PreToolUse",
            "session_id": "shared-session",
            "tool_use_id": "call-B",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/b", "content": "B"},
        }
        req_a = build_effect_request_from_pretool(
            self.store,
            pre_a,
            agent_id="agent-1",
            task_id="task-A",
            turn_id="turn-A",
            causal_id="cause-A",
            generation=12,
            effect_scope="TEST_ONLY",
        )
        req_b = build_effect_request_from_pretool(
            self.store,
            pre_b,
            agent_id="agent-1",
            task_id="task-B",
            turn_id="turn-B",
            causal_id="cause-B",
            generation=12,
            effect_scope="TEST_ONLY",
        )
        self.assertEqual(req_a.invocation_id, "call-A")
        self.assertEqual(req_b.invocation_id, "call-B")
        self.assertEqual(req_a.session_id, req_b.session_id)
        self.assertNotEqual(req_a.request_digest, req_b.request_digest)
        self.store.create_request(req_a)
        self.store.create_request(req_b)

        # Post events arrive in reverse order but still bind to their immutable call ids.
        post_b = {
            "hook_event_name": "PostToolUse",
            "session_id": "shared-session",
            "tool_use_id": "call-B",
            "tool_name": "Write",
        }
        post_a = {
            "hook_event_name": "PostToolUseFailure",
            "session_id": "shared-session",
            "tool_use_id": "call-A",
            "tool_name": "Write",
        }
        self.assertEqual(require_matching_posttool(req_b, post_b).invocation_id, "call-B")
        self.assertEqual(require_matching_posttool(req_a, post_a).invocation_id, "call-A")

        # A session-scoped fallback would accept this cross-close; the adapter must not.
        with self.assertRaisesRegex(HookInvocationIdentityError, "INVOCATION_ID_MISMATCH"):
            require_matching_posttool(req_a, post_b)

    def test_hook_adapter_missing_call_identity_fails_closed_without_session_fallback(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": "shared-session",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/a", "content": "A"},
        }
        with self.assertRaisesRegex(HookInvocationIdentityError, "MISSING_OR_INVALID_TOOL_USE_ID"):
            build_effect_request_from_pretool(
                self.store,
                payload,
                agent_id="agent-1",
                task_id="task-A",
                turn_id="turn-A",
                causal_id="cause-A",
                generation=12,
                effect_scope="TEST_ONLY",
            )

    def test_hook_adapter_rejects_wrong_event_session_and_tool(self):
        pre = {
            "hook_event_name": "PreToolUse",
            "session_id": "session-A",
            "tool_use_id": "call-A",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/tmp/a", "old_string": "x", "new_string": "y"},
        }
        req = build_effect_request_from_pretool(
            self.store,
            pre,
            agent_id="agent-1",
            task_id="task-A",
            turn_id="turn-A",
            causal_id="cause-A",
            generation=12,
            effect_scope="TEST_ONLY",
        )
        with self.assertRaisesRegex(HookInvocationIdentityError, "UNEXPECTED_HOOK_EVENT"):
            require_matching_posttool(req, pre)
        with self.assertRaisesRegex(HookInvocationIdentityError, "SESSION_ID_MISMATCH"):
            require_matching_posttool(
                req,
                {
                    "hook_event_name": "PostToolUse",
                    "session_id": "session-B",
                    "tool_use_id": "call-A",
                    "tool_name": "Edit",
                },
            )
        with self.assertRaisesRegex(HookInvocationIdentityError, "TOOL_NAME_MISMATCH"):
            require_matching_posttool(
                req,
                {
                    "hook_event_name": "PostToolUse",
                    "session_id": "session-A",
                    "tool_use_id": "call-A",
                    "tool_name": "Write",
                },
            )


if __name__ == "__main__":
    unittest.main()
