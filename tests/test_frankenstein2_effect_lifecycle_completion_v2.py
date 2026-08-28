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


if __name__ == "__main__":
    unittest.main()
