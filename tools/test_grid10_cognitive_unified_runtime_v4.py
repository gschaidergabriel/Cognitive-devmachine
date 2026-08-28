#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_cognitive_unified_runtime_v4 import (
    RuntimeCycleConflict,
    RuntimeCycleNotDue,
    _atomic_commit_cycle,
    build_unified_cognitive_runtime_v4,
)
from grid10_persistent_agency_v1 import GoalState, WakeKind


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

    def test_missing_hard_evidence_persists_hold(self):
        _, _, agency, runtime, _ = build_unified_cognitive_runtime_v4(self.db)
        cycle = runtime.tick_once(tick_id="t-hold", interval=1.0, now_ts=200.0)
        snap = agency.snapshot()
        checkpoint = json.loads(snap.continuation_checkpoint)
        self.assertEqual(cycle.assurance_mode, "HOLD")
        self.assertEqual(cycle.next_action, "HOLD")
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
