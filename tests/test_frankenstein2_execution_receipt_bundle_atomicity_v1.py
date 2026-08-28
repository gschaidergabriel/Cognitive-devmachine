from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.frankenstein2_effect_lifecycle_v1 import (
    AdmissionDecision,
    EffectLifecycleError,
    EffectLifecycleStore,
)


class ExecutionReceiptBundleAtomicityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "effects.sqlite"
        self.store = EffectLifecycleStore(self.db)

        req = self.store.build_request(
            invocation_id="inv-atomic",
            session_id="session-1",
            agent_id="agent-1",
            task_id="task-1",
            turn_id="turn-1",
            causal_id="cause-1",
            generation=7,
            tool_name="bounded-tool",
            normalized_arguments={"x": 1},
            effect_scope="TEST_ONLY",
        )
        self.request_digest = req.request_digest
        self.store.create_request(req, now_ts=1.0)
        self.store.bind_completion_source(
            "inv-atomic", source_digest="source-A", now_ts=2.0
        )
        self.store.decide(
            "inv-atomic", AdmissionDecision.ALLOW, reason="test", now_ts=3.0
        )
        self.store.record_enforcement(
            "inv-atomic",
            boundary_id="gate-1",
            dispatch_permitted=True,
            now_ts=4.0,
        )
        self.store.mark_submitted("inv-atomic", now_ts=5.0)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        return con

    def _record_bundle(self) -> None:
        self.store.record_execution_bundle(
            "inv-atomic",
            executable_id="tool-v1",
            command_digest="cmd-A",
            environment_id="sandbox-A",
            exit_code=0,
            result_digest="result-A",
            source_digest="source-A",
            duplicate_state="UNIQUE",
            status="SUCCEEDED",
            now_ts=6.0,
        )

    def test_failure_between_logical_inserts_rolls_back_entire_bundle(self) -> None:
        # Inject a deterministic SQLite failure exactly at the second logical insert.
        # If both rows are truly one writer transaction, the first insert and both
        # execution events must disappear with the rollback.
        con = self._connect()
        try:
            con.executescript(
                """
                CREATE TRIGGER fail_execution_v2_insert
                BEFORE INSERT ON execution_v2_metadata
                BEGIN
                  SELECT RAISE(ABORT, 'injected execution_v2_metadata failure');
                END;
                """
            )
            con.commit()
        finally:
            con.close()

        with self.assertRaisesRegex(
            EffectLifecycleError, "EXECUTION_BUNDLE_PERSISTENCE_CONFLICT"
        ):
            self._record_bundle()

        con = self._connect()
        try:
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM execution_receipts WHERE invocation_id=?",
                    ("inv-atomic",),
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM execution_v2_metadata WHERE invocation_id=?",
                    ("inv-atomic",),
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                con.execute(
                    """SELECT COUNT(*) FROM effect_lifecycle_events
                       WHERE invocation_id=?
                         AND event_type IN ('EXECUTION_RECORDED','EXECUTION_V2_METADATA_RECORDED')""",
                    ("inv-atomic",),
                ).fetchone()[0],
                0,
            )
            con.execute("DROP TRIGGER fail_execution_v2_insert")
            con.commit()
        finally:
            con.close()

        # The success path must commit both identity-bearing rows for one invocation.
        self._record_bundle()
        con = self._connect()
        try:
            base = con.execute(
                "SELECT * FROM execution_receipts WHERE invocation_id=?",
                ("inv-atomic",),
            ).fetchone()
            meta = con.execute(
                "SELECT * FROM execution_v2_metadata WHERE invocation_id=?",
                ("inv-atomic",),
            ).fetchone()
            self.assertIsNotNone(base)
            self.assertIsNotNone(meta)
            assert base is not None and meta is not None
            self.assertEqual(base["invocation_id"], meta["invocation_id"])
            self.assertEqual(base["request_digest"], self.request_digest)
            self.assertEqual(meta["source_digest"], "source-A")
            self.assertEqual(meta["duplicate_state"], "UNIQUE")
            self.assertEqual(meta["status"], "SUCCEEDED")
            self.assertEqual(base["executed_ts"], meta["recorded_ts"])
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
