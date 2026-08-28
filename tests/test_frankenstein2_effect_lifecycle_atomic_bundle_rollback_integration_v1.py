from __future__ import annotations

import sqlite3
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


class EffectLifecycleAtomicBundleRollbackIntegrationTests(unittest.TestCase):
    """Exercise the canonical Completion-v2 path across an injected writer failure."""

    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "effects.sqlite"
        self.store = EffectLifecycleStore(self.db)

    def tearDown(self) -> None:
        self.td.cleanup()

    def _prepare_submitted(self, invocation_id: str = "call-atomic") -> None:
        request = self.store.build_request(
            invocation_id=invocation_id,
            session_id="session-atomic",
            agent_id="frankenstein-2",
            task_id="task-atomic",
            turn_id="turn-atomic",
            causal_id="cause-atomic",
            generation=7,
            tool_name="bounded-tool",
            normalized_arguments={"x": 1},
            effect_scope="TEST_ONLY",
        )
        self.store.create_request(request, now_ts=1.0)
        self.store.bind_completion_source(
            invocation_id,
            source_digest="src-atomic",
            now_ts=2.0,
        )
        self.store.decide(
            invocation_id,
            AdmissionDecision.ALLOW,
            reason="atomic rollback integration fixture",
            now_ts=3.0,
        )
        self.store.record_enforcement(
            invocation_id,
            boundary_id="effect-gate-atomic",
            dispatch_permitted=True,
            now_ts=4.0,
        )
        self.store.mark_submitted(invocation_id, now_ts=5.0)

    def _record_bundle(self) -> None:
        self.store.record_execution_bundle(
            "call-atomic",
            executable_id="tool-v1",
            command_digest="cmd-atomic",
            environment_id="sandbox-atomic",
            exit_code=0,
            result_digest="result-atomic",
            source_digest="src-atomic",
            duplicate_state="UNIQUE",
            status="SUCCEEDED",
            now_ts=6.0,
        )

    def _install_second_insert_fault(self) -> None:
        """Abort the v2 metadata insert after the base receipt insert in the same transaction."""
        con = sqlite3.connect(str(self.db))
        try:
            con.execute(
                """CREATE TRIGGER fail_execution_v2_insert
                   BEFORE INSERT ON execution_v2_metadata
                   BEGIN
                     SELECT RAISE(ABORT, 'fault_after_base_execution_receipt');
                   END"""
            )
            con.commit()
        finally:
            con.close()

    def _remove_second_insert_fault(self) -> None:
        con = sqlite3.connect(str(self.db))
        try:
            con.execute("DROP TRIGGER fail_execution_v2_insert")
            con.commit()
        finally:
            con.close()

    def test_fault_after_base_insert_rolls_back_then_retry_closes_same_completion_chain(self) -> None:
        self._prepare_submitted()
        self._install_second_insert_fault()

        with self.assertRaisesRegex(EffectLifecycleError, "EXECUTION_BUNDLE_PERSISTENCE_CONFLICT"):
            self._record_bundle()

        failed = self.store.snapshot("call-atomic")
        self.assertEqual(failed["request"]["pending_state"], "SUBMITTED")
        self.assertIsNone(failed["execution"])
        self.assertIsNone(failed["execution_v2"])
        self.assertIsNone(failed["completion"])

        self._remove_second_insert_fault()
        self._record_bundle()
        self.store.verify_world_effect(
            "call-atomic",
            WorldOutcome.SUCCEEDED,
            evidence_digest="world-atomic",
            now_ts=8.0,
        )
        self.store.reenter_result(
            "call-atomic",
            result_digest="result-atomic",
            now_ts=9.0,
        )
        receipt = self.store.issue_completion_evidence("call-atomic", now_ts=10.0)

        closed = self.store.snapshot("call-atomic")
        self.assertTrue(receipt)
        self.assertIsNotNone(closed["execution"])
        self.assertIsNotNone(closed["execution_v2"])
        self.assertEqual(closed["execution_v2"]["source_digest"], "src-atomic")
        self.assertEqual(closed["completion"]["evidence_class"], V2_COMPLETION_EVIDENCE_CLASS)
        self.assertEqual(closed["completion"]["receipt_digest"], receipt)


if __name__ == "__main__":
    unittest.main()
