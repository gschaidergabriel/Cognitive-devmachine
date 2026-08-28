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
from grid10_persistent_agency_v1 import GoalState, WakeKind
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

    def test_real_deferred_wake_gap_is_attested_through_v6(self):
        _, _, agency, runtime, _ = build_unified_cognitive_runtime_v6(self.db)
        goal = agency.create_goal(
            goal_id="g-wake",
            origin="AUTHENTICATED_USER",
            semantic_goal="resume when evidence arrives",
            state=GoalState.CANDIDATE,
            success_criteria=("verified evidence",),
            uncertainty=0.4,
            priority=10,
            event_id="wake-integration:create",
            now_ts=100.0,
        )
        active = agency.transition_goal(
            "g-wake",
            expected_generation=goal.generation,
            new_state=GoalState.ACTIVE,
            event_id="wake-integration:activate",
            reason="admitted",
            now_ts=101.0,
        )
        agency.defer_goal(
            "g-wake",
            expected_generation=active.generation,
            intent_id="i-wake",
            wake_kind=WakeKind.EVENT,
            wake_value="evidence:new",
            event_id="wake-integration:defer",
            reason="await material evidence",
            now_ts=102.0,
        )
        agency.schedule_next_tick(
            not_before=999.0,
            mode="HOLD",
            event_id="wake-integration:far-schedule",
            now_ts=103.0,
        )

        tick_id = "integrated-real-wake"
        runtime.tick_once(
            tick_id=tick_id,
            now_ts=200.0,
            observed_events=("evidence:new",),
            trusted_axes=_trusted_normal_axes(),
        )
        result = classify_cycle_intent(self.db, tick_id=tick_id)
        self.assertEqual(result.status, STATUS_CLOSED)
        self.assertEqual(result.evidence["mismatches"], [])

        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        try:
            intent = con.execute(
                "SELECT agency_epoch_at_prepare FROM grid10_v6_cycle_intents WHERE tick_id=?",
                (tick_id,),
            ).fetchone()
            cycle = con.execute(
                "SELECT agency_epoch_before FROM grid10_cognitive_cycles WHERE tick_id=?",
                (tick_id,),
            ).fetchone()
            gap_events = con.execute(
                "SELECT event_id,event_type,state_epoch FROM agency_events "
                "WHERE state_epoch>? AND state_epoch<=? ORDER BY state_epoch,event_seq",
                (int(intent["agency_epoch_at_prepare"]), int(cycle["agency_epoch_before"])),
            ).fetchall()
        finally:
            con.close()

        self.assertEqual(int(cycle["agency_epoch_before"]), int(intent["agency_epoch_at_prepare"]) + 1)
        self.assertEqual(len(gap_events), 1)
        self.assertEqual(gap_events[0]["event_type"], "DEFERRED_INTENT_FIRED")
        self.assertEqual(gap_events[0]["event_id"], f"{tick_id}:wake:i-wake")
        self.assertEqual(int(gap_events[0]["state_epoch"]), int(cycle["agency_epoch_before"]))
        self.assertEqual(agency.get_goal("g-wake").state, GoalState.ACTIVE)

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
