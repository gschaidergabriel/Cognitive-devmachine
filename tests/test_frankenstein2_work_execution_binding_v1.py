from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "frankenstein2_work_execution_binding_v1.py"
SPEC = importlib.util.spec_from_file_location("frankenstein2_work_execution_binding_v1", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

WorkExecutionLedger = mod.WorkExecutionLedger


def _row(db_path: Path, sql: str, args: tuple[object, ...] = ()) -> sqlite3.Row:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(sql, args).fetchone()
        assert row is not None
        return row
    finally:
        con.close()


class WorkExecutionBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "binding.sqlite3"
        self.ledger = WorkExecutionLedger(self.db)

    def tearDown(self) -> None:
        self.td.cleanup()

    def _bind(self, *, binding: str, package: str, generation: str, child: str) -> None:
        self.ledger.bind_child(
            binding_id=binding,
            workpackage_id=package,
            work_generation=generation,
            child_runtime_kind="TEST_NATIVE_CHILD",
            child_execution_id=child,
            identity_provenance="deterministic-test-fixture",
        )

    def _invoke(self, *, binding: str, invocation: str) -> None:
        self.ledger.record_invocation(
            binding_id=binding,
            invocation_id=invocation,
            invocation_kind="TEST_CALL",
            request={"binding": binding, "invocation": invocation},
        )

    def _result(
        self,
        *,
        binding: str,
        invocation: str,
        result: str,
        outcome: str,
    ) -> None:
        self.ledger.record_result(
            result_id=result,
            binding_id=binding,
            invocation_id=invocation,
            outcome=outcome,
            result={"result_id": result, "outcome": outcome},
            result_provenance="deterministic-test-fixture",
        )

    def test_nullable_native_ids_are_not_invented(self) -> None:
        self._bind(binding="b1", package="wp1", generation="g1", child="child-exec-1")
        row = _row(
            self.db,
            "SELECT native_agent_id,native_task_id,status FROM fr2_work_execution_bindings WHERE binding_id=?",
            ("b1",),
        )
        self.assertIsNone(row["native_agent_id"])
        self.assertIsNone(row["native_task_id"])
        self.assertEqual(row["status"], "BOUND")

    def test_task_and_agent_identity_namespaces_remain_distinct(self) -> None:
        self.ledger.bind_child(
            binding_id="b1",
            workpackage_id="wp1",
            work_generation="g1",
            child_runtime_kind="TEST_NATIVE_CHILD",
            child_execution_id="child-exec-1",
            identity_provenance="observed-fixture",
            native_agent_id="agent-17",
            native_task_id="task-17",
        )
        row = _row(
            self.db,
            "SELECT native_agent_id,native_task_id FROM fr2_work_execution_bindings WHERE binding_id=?",
            ("b1",),
        )
        self.assertEqual(row["native_agent_id"], "agent-17")
        self.assertEqual(row["native_task_id"], "task-17")
        self.assertNotEqual(row["native_agent_id"], row["native_task_id"])

    def test_result_cross_talk_between_bindings_fails_closed(self) -> None:
        self._bind(binding="b1", package="wp1", generation="g1", child="child-1")
        self._bind(binding="b2", package="wp2", generation="g1", child="child-2")
        self._invoke(binding="b1", invocation="inv-1")
        self._invoke(binding="b2", invocation="inv-2")

        with self.assertRaisesRegex(ValueError, "result does not bind"):
            self._result(
                binding="b1",
                invocation="inv-2",
                result="result-cross-talk",
                outcome="SUCCESS",
            )
        self.assertEqual(
            _row(
                self.db,
                "SELECT COUNT(*) AS n FROM fr2_work_results WHERE result_id=?",
                ("result-cross-talk",),
            )["n"],
            0,
        )

    def test_unknown_outcome_never_becomes_completion(self) -> None:
        self._bind(binding="b1", package="wp1", generation="g1", child="child-1")
        self._invoke(binding="b1", invocation="inv-1")
        self._result(binding="b1", invocation="inv-1", result="r1", outcome="UNKNOWN")
        self.assertEqual(
            _row(
                self.db,
                "SELECT status FROM fr2_work_execution_bindings WHERE binding_id=?",
                ("b1",),
            )["status"],
            "UNKNOWN_OUTCOME",
        )
        with self.assertRaisesRegex(ValueError, "completion forbidden for outcome=UNKNOWN"):
            self.ledger.verify_completion(
                completion_id="c1",
                binding_id="b1",
                invocation_id="inv-1",
                result_id="r1",
                expected_work_generation="g1",
                evidence_kind="DETERMINISTIC_TEST_RECEIPT",
                evidence_ref="fixture://unknown-must-not-complete",
                evidence_payload={"verified": False},
            )

    def test_stale_generation_cannot_close_success(self) -> None:
        self._bind(binding="b1", package="wp1", generation="g2", child="child-1")
        self._invoke(binding="b1", invocation="inv-1")
        self._result(binding="b1", invocation="inv-1", result="r1", outcome="SUCCESS")
        with self.assertRaisesRegex(ValueError, "STALE_WORK_GENERATION"):
            self.ledger.verify_completion(
                completion_id="c1",
                binding_id="b1",
                invocation_id="inv-1",
                result_id="r1",
                expected_work_generation="g1",
                evidence_kind="DETERMINISTIC_TEST_RECEIPT",
                evidence_ref="fixture://stale",
                evidence_payload={"generation": "g1"},
            )
        self.assertEqual(
            _row(
                self.db,
                "SELECT status FROM fr2_work_execution_bindings WHERE binding_id=?",
                ("b1",),
            )["status"],
            "RESULT_OBSERVED",
        )

    def test_textual_claim_is_not_mechanistic_completion_evidence(self) -> None:
        self._bind(binding="b1", package="wp1", generation="g1", child="child-1")
        self._invoke(binding="b1", invocation="inv-1")
        self._result(binding="b1", invocation="inv-1", result="r1", outcome="SUCCESS")
        with self.assertRaisesRegex(ValueError, "mechanistic evidence"):
            self.ledger.verify_completion(
                completion_id="c1",
                binding_id="b1",
                invocation_id="inv-1",
                result_id="r1",
                expected_work_generation="g1",
                evidence_kind="MODEL_TEXT_CLAIM",
                evidence_ref="fixture://text-only",
                evidence_payload={"text": "done"},
            )

    def test_exact_success_plus_mechanistic_evidence_can_close_binding(self) -> None:
        self._bind(binding="b1", package="wp1", generation="g1", child="child-1")
        self._invoke(binding="b1", invocation="inv-1")
        self._result(binding="b1", invocation="inv-1", result="r1", outcome="SUCCESS")
        digest = self.ledger.verify_completion(
            completion_id="c1",
            binding_id="b1",
            invocation_id="inv-1",
            result_id="r1",
            expected_work_generation="g1",
            evidence_kind="DETERMINISTIC_TEST_RECEIPT",
            evidence_ref="fixture://verified",
            evidence_payload={"test": "pass", "identity": "b1/inv-1/r1/g1"},
        )
        self.assertEqual(len(digest), 64)
        self.assertEqual(
            _row(
                self.db,
                "SELECT status FROM fr2_work_execution_bindings WHERE binding_id=?",
                ("b1",),
            )["status"],
            "COMPLETED",
        )
        completion = _row(
            self.db,
            "SELECT binding_id,invocation_id,result_id,evidence_kind FROM fr2_completion_evidence WHERE completion_id=?",
            ("c1",),
        )
        self.assertEqual(
            dict(completion),
            {
                "binding_id": "b1",
                "invocation_id": "inv-1",
                "result_id": "r1",
                "evidence_kind": "DETERMINISTIC_TEST_RECEIPT",
            },
        )


if __name__ == "__main__":
    unittest.main()
