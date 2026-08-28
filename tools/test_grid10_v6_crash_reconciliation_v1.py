#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_v6_crash_reconciliation_v1 import (
    DuplicateCycleIntent,
    RecoveryMutationNotAuthorized,
    STATUS_ABORTED_BEFORE_V4_COMMIT,
    STATUS_CLOSED,
    STATUS_INCONSISTENT,
    STATUS_PREPARED,
    STATUS_RECOVERY_REQUIRED,
    classify_cycle_intent,
    install_reconciliation_schema,
    mark_intent_closed_in_transaction,
    persist_recovery_classification,
    prepare_cycle_intent,
)


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None)
    con.row_factory = sqlite3.Row
    return con


def _install_fixture_runtime_tables(path: Path) -> None:
    con = _connect(path)
    try:
        con.execute(
            """CREATE TABLE grid10_cognitive_cycles(
                 tick_id TEXT PRIMARY KEY,
                 agency_epoch_before INTEGER NOT NULL,
                 agency_epoch_after INTEGER NOT NULL
               )"""
        )
        con.execute(
            """CREATE TABLE grid10_v6_control_bound_receipts(
                 tick_id TEXT PRIMARY KEY,
                 agency_epoch_after INTEGER NOT NULL,
                 control_epoch INTEGER NOT NULL,
                 control_snapshot_digest TEXT NOT NULL,
                 receipt_digest TEXT NOT NULL
               )"""
        )
    finally:
        con.close()


class CrashReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "u.sqlite"
        install_reconciliation_schema(self.db)
        _install_fixture_runtime_tables(self.db)
        prepare_cycle_intent(
            self.db,
            tick_id="t1",
            expected_agency_epoch=7,
            control_epoch=11,
            control_snapshot_digest="ctrl-a",
            prepared_ts=100.0,
        )

    def tearDown(self):
        self.td.cleanup()

    def _insert_v4(self, *, before=7, after=8):
        con = _connect(self.db)
        try:
            con.execute(
                "INSERT INTO grid10_cognitive_cycles VALUES(?,?,?)",
                ("t1", before, after),
            )
        finally:
            con.close()

    def _insert_v6(self, *, after=8, control_epoch=11, digest="ctrl-a", receipt="r1"):
        con = _connect(self.db)
        try:
            con.execute(
                "INSERT INTO grid10_v6_control_bound_receipts VALUES(?,?,?,?,?)",
                ("t1", after, control_epoch, digest, receipt),
            )
        finally:
            con.close()

    def test_prepared_without_v4_is_precommit_abort_not_provider_failure(self):
        result = classify_cycle_intent(self.db, tick_id="t1")
        self.assertEqual(result.status, STATUS_ABORTED_BEFORE_V4_COMMIT)
        self.assertFalse(result.v4_cycle_present)
        self.assertFalse(result.v6_closure_present)
        self.assertEqual(result.provider_calls_status, "ZERO_BY_ORDERING_IF_PROTOCOL_WAS_FOLLOWED")
        self.assertFalse(result.same_tick_retry_authorized)

    def test_v4_without_v6_is_explicit_recovery_required_and_provider_unknown(self):
        self._insert_v4()
        result = classify_cycle_intent(self.db, tick_id="t1")
        self.assertEqual(result.status, STATUS_RECOVERY_REQUIRED)
        self.assertTrue(result.v4_cycle_present)
        self.assertFalse(result.v6_closure_present)
        self.assertEqual(result.provider_calls_status, "UNKNOWN_AFTER_PROCESS_INTERRUPTION")
        self.assertFalse(result.same_tick_retry_authorized)

    def test_matching_v4_and_v6_classify_closed(self):
        self._insert_v4()
        self._insert_v6()
        result = classify_cycle_intent(self.db, tick_id="t1")
        self.assertEqual(result.status, STATUS_CLOSED)
        self.assertEqual(result.evidence["mismatches"], [])

    def test_mismatched_control_or_epoch_is_inconsistent(self):
        self._insert_v4()
        self._insert_v6(after=9, control_epoch=12, digest="ctrl-b")
        result = classify_cycle_intent(self.db, tick_id="t1")
        self.assertEqual(result.status, STATUS_INCONSISTENT)
        self.assertIn("V4_V6_AGENCY_EPOCH_AFTER_MISMATCH", result.evidence["mismatches"])
        self.assertIn("CONTROL_EPOCH_MISMATCH", result.evidence["mismatches"])
        self.assertIn("CONTROL_SNAPSHOT_DIGEST_MISMATCH", result.evidence["mismatches"])

    def test_v6_without_v4_is_inconsistent(self):
        self._insert_v6()
        result = classify_cycle_intent(self.db, tick_id="t1")
        self.assertEqual(result.status, STATUS_INCONSISTENT)

    def test_duplicate_prepare_fails_closed(self):
        with self.assertRaises(DuplicateCycleIntent):
            prepare_cycle_intent(
                self.db,
                tick_id="t1",
                expected_agency_epoch=7,
                control_epoch=11,
                control_snapshot_digest="ctrl-a",
            )

    def test_recovery_persistence_requires_explicit_exclusive_gate(self):
        self._insert_v4()
        with self.assertRaises(RecoveryMutationNotAuthorized):
            persist_recovery_classification(
                self.db,
                tick_id="t1",
                exclusive_recovery_authorized=False,
            )
        result = persist_recovery_classification(
            self.db,
            tick_id="t1",
            exclusive_recovery_authorized=True,
            terminal_ts=200.0,
        )
        self.assertEqual(result.status, STATUS_RECOVERY_REQUIRED)
        con = _connect(self.db)
        try:
            row = con.execute(
                "SELECT status,classification_digest FROM grid10_v6_cycle_intents WHERE tick_id='t1'"
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(row["status"], STATUS_RECOVERY_REQUIRED)
        self.assertEqual(row["classification_digest"], result.digest)

    def test_close_marker_and_v6_receipt_can_commit_atomically(self):
        self._insert_v4()
        con = _connect(self.db)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO grid10_v6_control_bound_receipts VALUES(?,?,?,?,?)",
                ("t1", 8, 11, "ctrl-a", "receipt-atomic"),
            )
            mark_intent_closed_in_transaction(
                con,
                tick_id="t1",
                closure_receipt_digest="receipt-atomic",
                terminal_ts=300.0,
            )
            con.execute("COMMIT")
        finally:
            con.close()
        result = classify_cycle_intent(self.db, tick_id="t1")
        self.assertEqual(result.status, STATUS_CLOSED)

    def test_close_marker_rolls_back_with_v6_receipt(self):
        self._insert_v4()
        con = _connect(self.db)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO grid10_v6_control_bound_receipts VALUES(?,?,?,?,?)",
                ("t1", 8, 11, "ctrl-a", "receipt-rollback"),
            )
            mark_intent_closed_in_transaction(
                con,
                tick_id="t1",
                closure_receipt_digest="receipt-rollback",
                terminal_ts=300.0,
            )
            con.execute("ROLLBACK")
        finally:
            con.close()
        con = _connect(self.db)
        try:
            intent = con.execute(
                "SELECT status FROM grid10_v6_cycle_intents WHERE tick_id='t1'"
            ).fetchone()
            closure = con.execute(
                "SELECT tick_id FROM grid10_v6_control_bound_receipts WHERE tick_id='t1'"
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(intent["status"], STATUS_PREPARED)
        self.assertIsNone(closure)
        result = classify_cycle_intent(self.db, tick_id="t1")
        self.assertEqual(result.status, STATUS_RECOVERY_REQUIRED)


if __name__ == "__main__":
    unittest.main()
