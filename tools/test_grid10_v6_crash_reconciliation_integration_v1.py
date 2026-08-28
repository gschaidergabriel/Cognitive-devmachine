#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_cognitive_unified_runtime_v6 import (
    CognitiveCycleExecutionError,
    build_unified_cognitive_runtime_v6,
)
from grid10_v6_crash_reconciliation_v1 import (
    STATUS_ABORTED_BEFORE_V4_COMMIT,
    STATUS_CLOSED,
    STATUS_RECOVERY_REQUIRED,
    classify_cycle_intent,
    prepare_cycle_intent,
)


class ExplodingInference:
    def __call__(self, messages, *, config):
        raise RuntimeError("integration-bounded-explosion")


class V6CrashReconciliationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "u.sqlite"

    def tearDown(self):
        self.td.cleanup()

    def test_normal_v6_receipt_and_intent_close_together(self):
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v6(self.db)
        cycle = runtime.tick_once(
            tick_id="integrated-closed",
            now_ts=100.0,
            trusted_axes=_trusted_normal_axes(),
        )
        result = classify_cycle_intent(self.db, tick_id=cycle.tick_id)
        self.assertEqual(result.status, STATUS_CLOSED)
        con = sqlite3.connect(str(self.db))
        try:
            intent = con.execute(
                "SELECT status,closure_receipt_digest FROM grid10_v6_cycle_intents WHERE tick_id=?",
                (cycle.tick_id,),
            ).fetchone()
            receipt = con.execute(
                "SELECT receipt_digest FROM grid10_v6_control_bound_receipts WHERE tick_id=?",
                (cycle.tick_id,),
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(intent[0], STATUS_CLOSED)
        self.assertEqual(intent[1], receipt[0])
        self.assertEqual(receipt[0], cycle.receipt_digest)

    def test_exception_closure_still_closes_intent_before_bounded_reraise(self):
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v6(
            self.db,
            inference_fn=ExplodingInference(),
        )
        with self.assertRaises(CognitiveCycleExecutionError):
            runtime.tick_once(
                tick_id="integrated-failed-closed",
                now_ts=200.0,
                trusted_axes=_trusted_normal_axes(),
                cognitive_context={"goal": "g"},
            )
        result = classify_cycle_intent(self.db, tick_id="integrated-failed-closed")
        self.assertEqual(result.status, STATUS_CLOSED)
        self.assertFalse(result.same_tick_retry_authorized)

    def test_crash_before_v6_receipt_leaves_recovery_required_intent(self):
        _, _, _, runtime, _ = build_unified_cognitive_runtime_v6(self.db)
        with patch(
            "grid10_cognitive_unified_runtime_v6._connect",
            side_effect=RuntimeError("SIMULATED_PROCESS_DEATH_BEFORE_V6_RECEIPT"),
        ):
            with self.assertRaisesRegex(RuntimeError, "SIMULATED_PROCESS_DEATH"):
                runtime.tick_once(
                    tick_id="integrated-crash-window",
                    now_ts=300.0,
                    trusted_axes=_trusted_normal_axes(),
                )

        result = classify_cycle_intent(self.db, tick_id="integrated-crash-window")
        self.assertEqual(result.status, STATUS_RECOVERY_REQUIRED)
        self.assertTrue(result.v4_cycle_present)
        self.assertFalse(result.v6_closure_present)
        self.assertEqual(result.provider_calls_status, "UNKNOWN_AFTER_PROCESS_INTERRUPTION")
        self.assertFalse(result.same_tick_retry_authorized)

    def test_legacy_expected_epoch_schema_remains_read_write_compatible(self):
        # The first source-only reconciler revision used this column name. A persistent
        # developer/test DB created at that revision must not become unreadable merely because
        # the semantics were later renamed to agency_epoch_at_prepare.
        con = sqlite3.connect(str(self.db))
        try:
            con.execute(
                """
                CREATE TABLE grid10_v6_cycle_intents(
                  tick_id TEXT PRIMARY KEY,
                  schema TEXT NOT NULL,
                  expected_agency_epoch INTEGER NOT NULL,
                  control_epoch INTEGER NOT NULL,
                  control_snapshot_digest TEXT NOT NULL,
                  status TEXT NOT NULL,
                  prepared_ts REAL NOT NULL,
                  terminal_ts REAL,
                  classification_json TEXT,
                  classification_digest TEXT,
                  closure_receipt_digest TEXT
                )
                """
            )
            con.commit()
        finally:
            con.close()

        prepare_cycle_intent(
            self.db,
            tick_id="legacy-schema",
            agency_epoch_at_prepare=17,
            control_epoch=3,
            control_snapshot_digest="legacy-control",
            prepared_ts=400.0,
        )
        result = classify_cycle_intent(self.db, tick_id="legacy-schema")
        self.assertEqual(result.status, STATUS_ABORTED_BEFORE_V4_COMMIT)
        self.assertEqual(result.evidence["agency_epoch_at_prepare"], 17)
        self.assertEqual(result.evidence["control_epoch"], 3)
        self.assertEqual(result.evidence["control_snapshot_digest"], "legacy-control")


if __name__ == "__main__":
    unittest.main()
