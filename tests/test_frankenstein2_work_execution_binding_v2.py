from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "frankenstein2_work_execution_binding_v2.py"
SPEC = importlib.util.spec_from_file_location("frankenstein2_work_execution_binding_v2", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

WorkExecutionLedger = mod.WorkExecutionLedger
LegacyLedger = mod.v1.WorkExecutionLedger


def _row(db_path: Path, sql: str, args: tuple[object, ...] = ()) -> sqlite3.Row:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(sql, args).fetchone()
        assert row is not None
        return row
    finally:
        con.close()


def _count(db_path: Path, table: str, where: str = "1=1", args: tuple[object, ...] = ()) -> int:
    return int(_row(db_path, f"SELECT COUNT(*) AS n FROM {table} WHERE {where}", args)["n"])


class WorkExecutionBindingV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "binding.sqlite3"
        self.ledger = WorkExecutionLedger(self.db)

    def tearDown(self) -> None:
        self.td.cleanup()

    def _bind(self, ledger=None, binding: str = "b1") -> None:
        ledger = ledger or self.ledger
        ledger.bind_child(
            binding_id=binding,
            workpackage_id="wp1",
            work_generation="g1",
            child_runtime_kind="TEST_NATIVE_CHILD",
            child_execution_id="child-1",
            identity_provenance="deterministic-test-fixture",
        )

    def _invoke(self, invocation: str, ledger=None, binding: str = "b1") -> None:
        ledger = ledger or self.ledger
        ledger.record_invocation(
            binding_id=binding,
            invocation_id=invocation,
            invocation_kind="TEST_CALL",
            request={"binding": binding, "invocation": invocation},
        )

    def _result(
        self,
        invocation: str,
        result: str,
        outcome: str = "SUCCESS",
        ledger=None,
        binding: str = "b1",
    ) -> None:
        ledger = ledger or self.ledger
        ledger.record_result(
            result_id=result,
            binding_id=binding,
            invocation_id=invocation,
            outcome=outcome,
            result={"result_id": result, "outcome": outcome},
            result_provenance="deterministic-test-fixture",
        )

    def _complete(
        self,
        invocation: str,
        result: str,
        completion: str = "c1",
        ledger=None,
        binding: str = "b1",
    ) -> str:
        ledger = ledger or self.ledger
        return ledger.verify_completion(
            completion_id=completion,
            binding_id=binding,
            invocation_id=invocation,
            result_id=result,
            expected_work_generation="g1",
            evidence_kind="DETERMINISTIC_TEST_RECEIPT",
            evidence_ref=f"fixture://{completion}",
            evidence_payload={"verified": True, "binding": binding, "result": result},
        )

    def test_completion_fails_closed_while_any_invocation_is_unresolved(self) -> None:
        self._bind()
        self._invoke("inv-1")
        self._invoke("inv-2")
        self._result("inv-1", "r1")
        with self.assertRaisesRegex(ValueError, "UNRESOLVED_INVOCATIONS:1"):
            self._complete("inv-1", "r1")
        self.assertEqual(_count(self.db, "fr2_completion_evidence"), 0)
        self.assertEqual(
            _row(self.db, "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'")["status"],
            "RESULT_OBSERVED",
        )

    def test_completion_succeeds_after_all_invocations_are_resolved(self) -> None:
        self._bind()
        self._invoke("inv-1")
        self._invoke("inv-2")
        self._result("inv-1", "r1")
        self._result("inv-2", "r2")
        digest = self._complete("inv-2", "r2")
        self.assertEqual(len(digest), 64)
        self.assertEqual(
            _row(self.db, "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'")["status"],
            "COMPLETED",
        )
        self.assertEqual(_count(self.db, "fr2_completion_evidence", "binding_id=?", ("b1",)), 1)

    def test_unknown_prior_invocation_blocks_later_success_completion(self) -> None:
        self._bind()
        self._invoke("inv-1")
        self._invoke("inv-2")
        self._result("inv-1", "r1", outcome="UNKNOWN")
        self._result("inv-2", "r2", outcome="SUCCESS")
        self.assertEqual(
            _row(self.db, "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'")["status"],
            "UNKNOWN_OUTCOME",
        )
        with self.assertRaisesRegex(ValueError, "UNKNOWN_OUTCOME_REQUIRES_RECONCILIATION"):
            self._invoke("inv-3")
        self.assertEqual(
            _count(self.db, "fr2_work_invocations", "binding_id=?", ("b1",)),
            2,
        )
        with self.assertRaisesRegex(ValueError, "UNKNOWN_INVOCATION_OUTCOME:1"):
            self._complete("inv-2", "r2")
        self.assertEqual(_count(self.db, "fr2_completion_evidence"), 0)

    def test_failure_prior_invocation_blocks_later_success_completion(self) -> None:
        self._bind()
        self._invoke("inv-1")
        self._invoke("inv-2")
        self._result("inv-1", "r1", outcome="FAILURE")
        self._result("inv-2", "r2", outcome="SUCCESS")
        with self.assertRaisesRegex(ValueError, "NON_SUCCESS_INVOCATION_OUTCOME:FAILURE:1"):
            self._complete("inv-2", "r2")
        self.assertEqual(_count(self.db, "fr2_completion_evidence"), 0)
        self.assertEqual(
            _row(self.db, "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'")["status"],
            "RESULT_OBSERVED",
        )

    def test_rejected_prior_invocation_blocks_later_success_completion(self) -> None:
        self._bind()
        self._invoke("inv-1")
        self._invoke("inv-2")
        self._result("inv-1", "r1", outcome="REJECTED")
        self._result("inv-2", "r2", outcome="SUCCESS")
        with self.assertRaisesRegex(ValueError, "NON_SUCCESS_INVOCATION_OUTCOME:REJECTED:1"):
            self._complete("inv-2", "r2")
        self.assertEqual(_count(self.db, "fr2_completion_evidence"), 0)
        self.assertEqual(
            _row(self.db, "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'")["status"],
            "RESULT_OBSERVED",
        )

    def test_unknown_outcome_blocks_same_binding_reinvocation(self) -> None:
        self._bind()
        self._invoke("inv-1")
        self._result("inv-1", "r1", outcome="UNKNOWN")
        with self.assertRaisesRegex(ValueError, "UNKNOWN_OUTCOME_REQUIRES_RECONCILIATION"):
            self._invoke("inv-2")
        self.assertEqual(
            _count(self.db, "fr2_work_invocations", "binding_id=?", ("b1",)),
            1,
        )
        self.assertEqual(
            _row(self.db, "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'")["status"],
            "UNKNOWN_OUTCOME",
        )

    def test_late_result_cannot_regress_a_legacy_terminal_binding(self) -> None:
        self._bind()
        self._invoke("inv-1")
        self._invoke("inv-2")
        self._result("inv-1", "r1")
        con = sqlite3.connect(str(self.db))
        try:
            con.execute("UPDATE fr2_work_execution_bindings SET status='COMPLETED' WHERE binding_id='b1'")
            con.commit()
        finally:
            con.close()
        with self.assertRaisesRegex(ValueError, "binding is terminal: COMPLETED"):
            self._result("inv-2", "r2")
        self.assertEqual(_count(self.db, "fr2_work_results", "result_id=?", ("r2",)), 0)
        self.assertEqual(
            _row(self.db, "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'")["status"],
            "COMPLETED",
        )

    def test_second_completion_of_same_binding_is_forbidden(self) -> None:
        self._bind()
        self._invoke("inv-1")
        self._result("inv-1", "r1")
        self._complete("inv-1", "r1", completion="c1")
        with self.assertRaisesRegex(ValueError, "binding is terminal: COMPLETED"):
            self._complete("inv-1", "r1", completion="c2")
        self.assertEqual(_count(self.db, "fr2_completion_evidence", "binding_id=?", ("b1",)), 1)

    def test_v2_refuses_legacy_database_with_multiple_completions(self) -> None:
        """Represent pre-hardening v1 state directly so predecessor repairs cannot erase coverage."""
        legacy_db = Path(self.td.name) / "legacy.sqlite3"
        mod.v1.init_schema(legacy_db)
        con = sqlite3.connect(str(legacy_db))
        try:
            con.execute("PRAGMA foreign_keys=ON")
            con.execute(
                """INSERT INTO fr2_work_execution_bindings
                   (binding_id,workpackage_id,work_generation,parent_execution_id,child_runtime_kind,
                    child_execution_id,native_agent_id,native_task_id,identity_provenance,
                    identity_observed_at,status,created_at)
                   VALUES('b1','wp1','g1',NULL,'LEGACY_TEST_CHILD','child-1',NULL,NULL,
                          'legacy-fixture',1.0,'COMPLETED',1.0)"""
            )
            con.executemany(
                """INSERT INTO fr2_work_invocations
                   (invocation_id,binding_id,invocation_kind,native_tool_use_id,request_digest,started_at)
                   VALUES(?, 'b1', 'LEGACY_CALL', NULL, ?, ?)""",
                [
                    ("inv-1", "legacy-request-1", 2.0),
                    ("inv-2", "legacy-request-2", 3.0),
                ],
            )
            con.executemany(
                """INSERT INTO fr2_work_results
                   (result_id,binding_id,invocation_id,outcome,result_digest,result_provenance,observed_at)
                   VALUES(?, 'b1', ?, 'SUCCESS', ?, 'legacy-fixture', ?)""",
                [
                    ("r1", "inv-1", "legacy-result-1", 4.0),
                    ("r2", "inv-2", "legacy-result-2", 5.0),
                ],
            )
            con.executemany(
                """INSERT INTO fr2_completion_evidence
                   (completion_id,binding_id,invocation_id,result_id,evidence_kind,evidence_digest,evidence_ref,verified_at)
                   VALUES(?, 'b1', ?, ?, 'DETERMINISTIC_TEST_RECEIPT', ?, ?, ?)""",
                [
                    ("c1", "inv-1", "r1", "legacy-evidence-1", "fixture://legacy/c1", 6.0),
                    ("c2", "inv-2", "r2", "legacy-evidence-2", "fixture://legacy/c2", 7.0),
                ],
            )
            con.commit()
        finally:
            con.close()

        self.assertEqual(_count(legacy_db, "fr2_completion_evidence", "binding_id=?", ("b1",)), 2)
        with self.assertRaisesRegex(
            ValueError,
            "LEGACY_MULTIPLE_COMPLETIONS_REQUIRE_RECONCILIATION:b1:2",
        ):
            WorkExecutionLedger(legacy_db)


if __name__ == "__main__":
    unittest.main()
