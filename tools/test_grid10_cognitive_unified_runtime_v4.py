#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_cognitive_unified_runtime_v4 import (
    IDLE_CHECKPOINT_SCHEMA,
    RuntimeCycleConflict,
    RuntimeCycleError,
    RuntimeCycleNotDue,
    _atomic_commit_cycle,
    _atomic_commit_idle_hold,
    build_unified_cognitive_runtime_v4,
)
from grid10_persistent_agency_v1 import GoalState, WakeKind


class CountingControlPlane:
    def __init__(self, delegate):
        self.delegate = delegate
        self.snapshot_calls = 0

    def snapshot(self):
        self.snapshot_calls += 1
        return self.delegate.snapshot()


class UnifiedCognitiveRuntimeV4Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "unified.sqlite"

    def tearDown(self):
        self.td.cleanup()

    def test_normal_tick_commits_agency_checkpoint_and_schedule(self):
        _, _, agency, runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        cycle = runtime.tick_once(
            tick_id="t-normal",
            interval=2.0,
            now_ts=100.0,
            trusted_axes=_trusted_normal_axes(),
        )
        snap = agency.snapshot()
        checkpoint = json.loads(snap.continuation_checkpoint)
        self.assertEqual(cycle.assurance_mode, "NORMAL")
        self.assertEqual(snap.mode, "NORMAL")
        self.assertEqual(snap.next_tick_not_before, 102.0)
        self.assertEqual(checkpoint["tick_id"], "t-normal")
        self.assertEqual(cycle.agency_epoch_after, cycle.agency_epoch_before + 1)
        self.assertFalse(agency.due_for_tick(now_ts=101.99))
        self.assertTrue(agency.due_for_tick(now_ts=102.0))

    def test_live_control_snapshot_latched_once_and_drives_default_pulse_cadence(self):
        _, _, agency, runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        base = runtime.control_plane.snapshot()
        patch = runtime.control_plane.build_patch(
            patch_id="test:pulse-025",
            writer="unit-test",
            writer_kind="EXPERIMENT",
            reason="prove pulse consumer",
            changes={"pulse.active_interval_seconds": 0.25},
            base=base,
        )
        receipt = runtime.control_plane.apply_patch(patch)
        self.assertTrue(receipt.accepted)
        counted = CountingControlPlane(runtime.control_plane)
        runtime.control_plane = counted
        cycle = runtime.tick_once(
            tick_id="t-live-pulse",
            interval=None,
            now_ts=100.0,
            trusted_axes=_trusted_normal_axes(),
        )
        self.assertEqual(counted.snapshot_calls, 1)
        self.assertEqual(cycle.next_tick_not_before, 100.25)
        self.assertEqual(cycle.checkpoint["pulse_interval_seconds_consumed"], 0.25)
        self.assertEqual(cycle.checkpoint["control_snapshot"]["control_epoch"], receipt.control_epoch)
        self.assertEqual(cycle.checkpoint["control_snapshot_source"], "latched_here")
        self.assertEqual(agency.snapshot().next_tick_not_before, 100.25)

    def test_provided_control_snapshot_is_exact_cycle_basis_without_second_latch(self):
        _, _, agency, runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        base = runtime.control_plane.snapshot()
        patch = runtime.control_plane.build_patch(
            patch_id="test:provided-pulse",
            writer="unit-test",
            writer_kind="EXPERIMENT",
            reason="prove one externally latched basis",
            changes={"pulse.active_interval_seconds": 0.35},
            base=base,
        )
        receipt = runtime.control_plane.apply_patch(patch)
        self.assertTrue(receipt.accepted)
        provided = runtime.control_plane.snapshot()
        counted = CountingControlPlane(runtime.control_plane)
        runtime.control_plane = counted
        cycle = runtime.tick_once(
            tick_id="t-provided-control",
            interval=None,
            now_ts=100.0,
            control_snapshot=provided,
            trusted_axes=_trusted_normal_axes(),
        )
        self.assertEqual(counted.snapshot_calls, 0)
        self.assertEqual(cycle.next_tick_not_before, 100.35)
        self.assertEqual(cycle.checkpoint["control_snapshot_source"], "provided")
        self.assertEqual(cycle.checkpoint["control_snapshot"]["control_epoch"], provided.control_epoch)
        self.assertEqual(cycle.checkpoint["control_snapshot"]["snapshot_digest"], provided.snapshot_digest)
        self.assertEqual(agency.snapshot().next_tick_not_before, 100.35)

    def test_missing_hard_evidence_persists_hold_with_hold_interval(self):
        _, _, agency, runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        cycle = runtime.tick_once(
            tick_id="t-hold",
            interval=1.0,
            hold_interval=20.0,
            now_ts=200.0,
        )
        snap = agency.snapshot()
        checkpoint = json.loads(snap.continuation_checkpoint)
        self.assertEqual(cycle.assurance_mode, "HOLD")
        self.assertEqual(cycle.next_action, "HOLD")
        self.assertEqual(cycle.next_tick_not_before, 220.0)
        self.assertEqual(snap.mode, "HOLD")
        self.assertEqual(checkpoint["assurance_mode"], "HOLD")
        self.assertEqual(checkpoint["next_action"], "HOLD")

    def test_schedule_blocks_early_tick_without_material_wake(self):
        _, heartbeat, agency, runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        agency.schedule_next_tick(
            not_before=500.0,
            mode="NORMAL",
            event_id="test:schedule",
            now_ts=400.0,
        )
        with self.assertRaises(RuntimeCycleNotDue):
            runtime.tick_once(
                tick_id="t-too-early",
                interval=1.0,
                now_ts=499.0,
                trusted_axes=_trusted_normal_axes(),
            )
        con = sqlite3.connect(str(heartbeat.path))
        try:
            count = con.execute("SELECT COUNT(*) FROM ticks").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(count, 0)

    def test_due_deferred_event_wakes_goal_and_forces_tick(self):
        _, _, agency, runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        goal = agency.create_goal(
            goal_id="g1",
            origin="AUTHENTICATED_USER",
            semantic_goal="resume when evidence arrives",
            state=GoalState.CANDIDATE,
            success_criteria=("verified evidence",),
            uncertainty=0.4,
            priority=10,
            event_id="test:create",
            now_ts=100.0,
        )
        active = agency.transition_goal(
            "g1",
            expected_generation=goal.generation,
            new_state=GoalState.ACTIVE,
            event_id="test:activate",
            reason="admitted",
            now_ts=101.0,
        )
        agency.defer_goal(
            "g1",
            expected_generation=active.generation,
            intent_id="i1",
            wake_kind=WakeKind.EVENT,
            wake_value="evidence:new",
            event_id="test:defer",
            reason="await material evidence",
            now_ts=102.0,
        )
        agency.schedule_next_tick(
            not_before=999.0,
            mode="HOLD",
            event_id="test:far-schedule",
            now_ts=103.0,
        )
        cycle = runtime.tick_once(
            tick_id="t-wake",
            interval=1.0,
            now_ts=200.0,
            observed_events=("evidence:new",),
            trusted_axes=_trusted_normal_axes(),
        )
        self.assertEqual(cycle.woken_goal_ids, ("g1",))
        self.assertEqual(agency.get_goal("g1").state, GoalState.ACTIVE)
        self.assertEqual(cycle.assurance_mode, "NORMAL")

    def test_fabricated_prewoken_lineage_is_rejected_without_heartbeat_credit(self):
        _, heartbeat, agency, runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        agency.schedule_next_tick(
            not_before=999.0,
            mode="HOLD",
            event_id="pre:schedule",
            now_ts=13.0,
        )
        before = agency.snapshot()
        with self.assertRaisesRegex(RuntimeCycleError, "PREWOKEN_WAKE_LINEAGE_UNSUPPORTED"):
            runtime.tick_once(
                tick_id="t-fabricated-prewake",
                now_ts=20.0,
                prewoken_goal_ids=("fabricated-goal",),
                trusted_axes=_trusted_normal_axes(),
            )
        after = agency.snapshot()
        self.assertEqual(after.state_epoch, before.state_epoch)
        self.assertEqual(after.next_tick_not_before, 999.0)
        con = sqlite3.connect(str(heartbeat.path))
        try:
            tick_count = con.execute("SELECT COUNT(*) FROM ticks").fetchone()[0]
            cycle_count = con.execute("SELECT COUNT(*) FROM grid10_cognitive_cycles").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(tick_count, 0)
        self.assertEqual(cycle_count, 0)

    def test_any_prewoken_argument_is_rejected_even_with_observed_events(self):
        _, _, _agency, runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        with self.assertRaisesRegex(RuntimeCycleError, "PREWOKEN_WAKE_LINEAGE_UNSUPPORTED"):
            runtime.tick_once(
                tick_id="t-ambiguous",
                now_ts=1.0,
                observed_events=("event:x",),
                prewoken_goal_ids=("g1",),
                trusted_axes=_trusted_normal_axes(),
            )

    def test_idle_hold_is_one_atomic_agency_epoch_without_heartbeat_credit(self):
        _, heartbeat, agency, _runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        before = agency.snapshot()
        after_epoch, checkpoint = _atomic_commit_idle_hold(
            agency,
            expected_agency_epoch=before.state_epoch,
            cycle_id="idle-atomic",
            awakened_goal_ids=(),
            next_tick_not_before=30.0,
            now_ts=0.0,
        )
        snap = agency.snapshot()
        self.assertEqual(after_epoch, before.state_epoch + 1)
        self.assertEqual(snap.state_epoch, before.state_epoch + 1)
        self.assertEqual(snap.mode, "HOLD")
        self.assertEqual(checkpoint["schema"], IDLE_CHECKPOINT_SCHEMA)
        self.assertEqual(json.loads(snap.continuation_checkpoint)["reason"], "NO_ACTIVE_OR_TRIAL_GOAL")
        con = sqlite3.connect(str(heartbeat.path))
        try:
            tick_count = con.execute("SELECT COUNT(*) FROM ticks").fetchone()[0]
            cycle_count = con.execute("SELECT COUNT(*) FROM grid10_cognitive_cycles").fetchone()[0]
            idle_events = con.execute(
                "SELECT COUNT(*) FROM agency_events WHERE event_type='COGNITIVE_IDLE_HOLD_COMMITTED'"
            ).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(tick_count, 0)
        self.assertEqual(cycle_count, 0)
        self.assertEqual(idle_events, 1)

    def test_stale_agency_epoch_cycle_commit_fails_closed(self):
        _, _, agency, _runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        before = agency.snapshot()
        agency.schedule_next_tick(
            not_before=5.0,
            mode="NORMAL",
            event_id="test:competing-writer",
            now_ts=1.0,
        )
        with self.assertRaisesRegex(RuntimeCycleConflict, "STALE_AGENCY_EPOCH"):
            _atomic_commit_cycle(
                agency,
                expected_agency_epoch=before.state_epoch,
                tick_id="t-stale",
                source_state_epoch=1,
                assurance_mode="NORMAL",
                next_action="ACT_CANDIDATE",
                woken_goal_ids=(),
                checkpoint={"schema": "test"},
                next_tick_not_before=10.0,
                now_ts=2.0,
            )
        con = sqlite3.connect(str(self.db))
        try:
            count = con.execute(
                "SELECT COUNT(*) FROM grid10_cognitive_cycles WHERE tick_id='t-stale'"
            ).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
