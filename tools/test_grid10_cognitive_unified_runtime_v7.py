#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_cognitive_unified_runtime_v7 import (
    CognitiveAttemptConflict,
    build_unified_cognitive_runtime_v7,
)


class UnifiedRuntimeV7Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "unified.sqlite"

    def tearDown(self):
        self.td.cleanup()

    def _build(self, *, stale=0.0):
        return build_unified_cognitive_runtime_v7(
            self.db,
            recovery_stale_after_seconds=stale,
        )

    def _attempt_row(self, tick_id):
        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        try:
            return con.execute(
                "SELECT * FROM grid10_v7_cycle_attempts WHERE tick_id=?",
                (tick_id,),
            ).fetchone()
        finally:
            con.close()

    def test_normal_tick_closes_v7_attempt_against_v6_receipt(self):
        _, _, agency, runtime, _ = self._build()
        before = agency.snapshot()
        cycle = runtime.tick_once(
            tick_id="v7-normal",
            now_ts=100.0,
            trusted_axes=_trusted_normal_axes(),
        )
        after = agency.snapshot()
        self.assertEqual(after.state_epoch, before.state_epoch + 1)
        row = self._attempt_row("v7-normal")
        self.assertEqual(row["status"], "CLOSED_SUCCESS")
        self.assertEqual(row["closure_kind"], "V6_RECEIPT_DURABLE")
        self.assertEqual(row["inner_receipt_digest"], cycle.receipt_digest)
        self.assertIsNone(row["recovery_receipt_json"])

    def test_duplicate_tick_id_is_rejected_before_second_v4_commit(self):
        _, _, agency, runtime, _ = self._build()
        runtime.tick_once(
            tick_id="v7-duplicate",
            now_ts=100.0,
            trusted_axes=_trusted_normal_axes(),
        )
        epoch_after_first = agency.snapshot().state_epoch
        with self.assertRaises(CognitiveAttemptConflict):
            runtime.tick_once(
                tick_id="v7-duplicate",
                now_ts=200.0,
                trusted_axes=_trusted_normal_axes(),
            )
        self.assertEqual(agency.snapshot().state_epoch, epoch_after_first)
        con = sqlite3.connect(str(self.db))
        try:
            count = con.execute(
                "SELECT COUNT(*) FROM grid10_cognitive_cycles WHERE tick_id='v7-duplicate'"
            ).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(count, 1)

    def test_reentry_recovers_v4_commit_without_v6_closure_as_unknown(self):
        _, _, agency, runtime, _ = self._build(stale=3600.0)
        runtime._prepare_attempt(tick_id="v7-crash-window")
        runtime.runtime_v4.tick_once(
            tick_id="v7-crash-window",
            now_ts=150.0,
            trusted_axes=_trusted_normal_axes(),
        )
        committed_epoch = agency.snapshot().state_epoch

        con = sqlite3.connect(str(self.db))
        try:
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM grid10_v6_control_bound_receipts WHERE tick_id='v7-crash-window'"
                ).fetchone()[0],
                0,
            )
        finally:
            con.close()

        closures = runtime.reconcile_pending_attempts(force=True)
        self.assertEqual(len(closures), 1)
        self.assertEqual(closures[0].status, "RECOVERED_POST_V4_COMMIT_UNKNOWN")
        row = self._attempt_row("v7-crash-window")
        receipt = json.loads(row["recovery_receipt_json"])
        self.assertEqual(receipt["cognitive_outcome"], "UNKNOWN")
        self.assertFalse(receipt["same_tick_retry_authorized"])
        self.assertEqual(receipt["agency_epoch_after_v4"], committed_epoch)
        self.assertIsNotNone(receipt["v4_control_snapshot"])
        self.assertFalse(receipt["completion_minted"])
        self.assertFalse(receipt["external_effect_executed"])

    def test_reentry_closes_prepared_attempt_when_v6_receipt_already_exists(self):
        _, _, _, runtime, _ = self._build(stale=3600.0)
        runtime._prepare_attempt(tick_id="v7-v6-durable")
        inner = runtime.runtime_v6.tick_once(
            tick_id="v7-v6-durable",
            now_ts=175.0,
            trusted_axes=_trusted_normal_axes(),
        )
        closures = runtime.reconcile_pending_attempts(force=True)
        self.assertEqual(len(closures), 1)
        self.assertEqual(closures[0].status, "RECOVERED_FROM_EXISTING_V6_RECEIPT")
        row = self._attempt_row("v7-v6-durable")
        self.assertEqual(row["inner_receipt_digest"], inner.receipt_digest)
        self.assertIsNone(row["recovery_receipt_json"])

    def test_pre_v4_crash_is_typed_without_claiming_no_agency_mutation(self):
        _, _, agency, runtime, _ = self._build(stale=3600.0)
        before = agency.snapshot().state_epoch
        runtime._prepare_attempt(tick_id="v7-pre-v4")
        closures = runtime.reconcile_pending_attempts(force=True)
        self.assertEqual(len(closures), 1)
        self.assertEqual(closures[0].status, "RECOVERED_PRE_V4_CYCLE_COMMIT_UNKNOWN")
        row = self._attempt_row("v7-pre-v4")
        receipt = json.loads(row["recovery_receipt_json"])
        self.assertEqual(receipt["agency_epoch_at_prepare"], before)
        self.assertEqual(receipt["agency_epoch_current"], before)
        self.assertFalse(receipt["possible_precycle_agency_mutation"])
        self.assertEqual(receipt["cognitive_outcome"], "NOT_ESTABLISHED")
        self.assertFalse(receipt["same_tick_retry_authorized"])

    def test_fresh_prepared_attempt_is_not_reconciled_by_background_scan(self):
        _, _, _, runtime, _ = self._build(stale=3600.0)
        runtime._prepare_attempt(tick_id="v7-fresh")
        closures = runtime.reconcile_pending_attempts(force=False)
        self.assertEqual(closures, ())
        row = self._attempt_row("v7-fresh")
        self.assertEqual(row["status"], "PREPARED")


if __name__ == "__main__":
    unittest.main()
