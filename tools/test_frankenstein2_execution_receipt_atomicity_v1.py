#!/usr/bin/env python3
from pathlib import Path
import sqlite3
import tempfile
import unittest

from frankenstein2_effect_lifecycle_v1 import (
    AdmissionDecision,
    EffectLifecycleError,
    EffectLifecycleStore,
)


SOURCE_DIGEST = "s" * 64


class ExecutionReceiptAtomicityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "lifecycle.sqlite3"
        self.store = EffectLifecycleStore(self.db)
        self.req = self.store.build_request(
            invocation_id="inv-atomic",
            session_id="session-1",
            agent_id="agent-1",
            task_id="task-1",
            turn_id="turn-1",
            causal_id="cause-1",
            generation=7,
            tool_name="fixture-tool",
            normalized_arguments={"x": 1},
            effect_scope="fixture",
        )
        self.store.create_request(self.req, now_ts=1.0)
        self.store.bind_completion_source(
            self.req.invocation_id,
            source_digest=SOURCE_DIGEST,
            now_ts=2.0,
        )
        self.store.decide(
            self.req.invocation_id,
            AdmissionDecision.ALLOW,
            reason="fixture",
            now_ts=3.0,
        )
        self.store.record_enforcement(
            self.req.invocation_id,
            boundary_id="fixture-boundary",
            dispatch_permitted=True,
            now_ts=4.0,
        )
        self.store.mark_submitted(self.req.invocation_id, now_ts=5.0)

    def tearDown(self) -> None:
        self.td.cleanup()

    def _count(self, table: str) -> int:
        con = sqlite3.connect(str(self.db))
        try:
            return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        finally:
            con.close()

    def _record_bundle(self) -> None:
        self.store.record_execution_bundle(
            self.req.invocation_id,
            executable_id="fixture-executable",
            command_digest="c" * 64,
            environment_id="fixture-environment",
            exit_code=0,
            result_digest="r" * 64,
            source_digest=SOURCE_DIGEST,
            duplicate_state="UNIQUE",
            status="SUCCEEDED",
            now_ts=6.0,
        )

    def test_injected_second_insert_failure_rolls_back_entire_bundle(self) -> None:
        con = sqlite3.connect(str(self.db))
        try:
            con.execute(
                """CREATE TRIGGER inject_execution_v2_failure
                   BEFORE INSERT ON execution_v2_metadata
                   BEGIN
                     SELECT RAISE(ABORT, 'INJECTED_V2_METADATA_FAILURE');
                   END"""
            )
            con.commit()
        finally:
            con.close()

        with self.assertRaisesRegex(
            EffectLifecycleError,
            "EXECUTION_BUNDLE_PERSISTENCE_CONFLICT",
        ):
            self._record_bundle()

        self.assertEqual(self._count("execution_receipts"), 0)
        self.assertEqual(self._count("execution_v2_metadata"), 0)
        con = sqlite3.connect(str(self.db))
        try:
            execution_events = con.execute(
                "SELECT COUNT(*) FROM effect_lifecycle_events WHERE event_type IN ('EXECUTION_RECORDED','EXECUTION_V2_METADATA_RECORDED')"
            ).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(execution_events, 0)

    def test_success_commits_one_bound_identity_bundle(self) -> None:
        self._record_bundle()
        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        try:
            row = con.execute(
                """SELECT r.invocation_id,r.request_digest,r.generation,
                          e.request_digest AS execution_request_digest,e.exit_code,e.result_digest,
                          m.source_digest,m.duplicate_state,m.status
                   FROM effect_requests r
                   JOIN execution_receipts e USING(invocation_id)
                   JOIN execution_v2_metadata m USING(invocation_id)
                   WHERE r.invocation_id=?""",
                (self.req.invocation_id,),
            ).fetchone()
        finally:
            con.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["invocation_id"], self.req.invocation_id)
        self.assertEqual(row["request_digest"], self.req.request_digest)
        self.assertEqual(row["execution_request_digest"], self.req.request_digest)
        self.assertEqual(row["generation"], 7)
        self.assertEqual(row["source_digest"], SOURCE_DIGEST)
        self.assertEqual(row["duplicate_state"], "UNIQUE")
        self.assertEqual(row["status"], "SUCCEEDED")
        self.assertEqual(row["exit_code"], 0)
        self.assertEqual(row["result_digest"], "r" * 64)

    def test_source_transplant_fails_before_any_execution_bundle_is_persisted(self) -> None:
        with self.assertRaisesRegex(EffectLifecycleError, "EXECUTION_SOURCE_DIGEST_MISMATCH"):
            self.store.record_execution_bundle(
                self.req.invocation_id,
                executable_id="fixture-executable",
                command_digest="c" * 64,
                environment_id="fixture-environment",
                exit_code=0,
                result_digest="r" * 64,
                source_digest="x" * 64,
                duplicate_state="UNIQUE",
                status="SUCCEEDED",
                now_ts=6.0,
            )
        self.assertEqual(self._count("execution_receipts"), 0)
        self.assertEqual(self._count("execution_v2_metadata"), 0)


if __name__ == "__main__":
    unittest.main()
