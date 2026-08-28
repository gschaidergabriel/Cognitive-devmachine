#!/usr/bin/env python3
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_persistent_agency_v1 import DeferredIntentState, GoalState, WakeKind
from grid10_persistent_scheduler_v1 import PersistentCognitiveScheduler, SchedulerConfig


class PersistentSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.db = self.root / "unified.sqlite"
        self.frames = self.root / "frames.jsonl"
        self.config = SchedulerConfig(
            active_interval_seconds=5.0,
            hold_poll_seconds=20.0,
            idle_poll_seconds=30.0,
            trusted_normal_test_fixture=True,
        )

    def tearDown(self):
        self.td.cleanup()

    def scheduler(self):
        return PersistentCognitiveScheduler(self.db, self.frames, config=self.config)

    def seed_active(self, scheduler, *, goal_id="g1", now=100.0):
        goal = scheduler.agency.create_goal(
            goal_id=goal_id,
            origin="AUTHENTICATED_USER",
            semantic_goal="continue without a new prompt",
            success_criteria=("next heartbeat occurs",),
            uncertainty=0.2,
            priority=10,
            event_id=f"{goal_id}:create",
            now_ts=now,
        )
        return scheduler.agency.transition_goal(
            goal_id,
            expected_generation=goal.generation,
            new_state=GoalState.ACTIVE,
            event_id=f"{goal_id}:activate",
            reason="admitted",
            now_ts=now + 1,
        )

    def test_completed_cycle_uses_v4_atomic_receipt_and_restart_respects_due_time(self):
        s1 = self.scheduler()
        self.seed_active(s1)
        before_epoch = s1.agency.snapshot().state_epoch
        first = s1.cycle_once(cycle_id="cycle-1", now_ts=110.0)
        self.assertEqual(first.status, "HEARTBEAT_RAN")
        self.assertEqual(first.cognitive_action, "ACT_CANDIDATE")
        self.assertEqual(first.next_tick_not_before, 115.0)
        self.assertEqual(first.agency_state_epoch, before_epoch + 1)
        self.assertTrue(self.frames.exists())

        con = sqlite3.connect(str(self.db))
        try:
            row = con.execute(
                "SELECT checkpoint_json,next_tick_not_before FROM grid10_cognitive_cycles WHERE tick_id=?",
                ("cycle-1:heartbeat",),
            ).fetchone()
        finally:
            con.close()
        self.assertIsNotNone(row)
        checkpoint = json.loads(row[0])
        self.assertEqual(checkpoint["schema"], "GRID10_COGNITIVE_CYCLE_CHECKPOINT/v1")
        self.assertEqual(row[1], 115.0)

        # Re-open all runtime objects from UnifiedDB. The scheduler must not run early merely
        # because this is a new process/session.
        s2 = self.scheduler()
        early = s2.cycle_once(cycle_id="cycle-early", now_ts=114.9)
        self.assertEqual(early.status, "NOT_DUE")
        due = s2.cycle_once(cycle_id="cycle-2", now_ts=115.0)
        self.assertEqual(due.status, "HEARTBEAT_RAN")
        self.assertEqual(due.heartbeat_tick_id, "cycle-2:heartbeat")
        self.assertEqual(s2.agency.get_goal("g1").state, GoalState.ACTIVE)

    def test_no_active_goal_enters_hold_with_one_atomic_state_transition(self):
        s = self.scheduler()
        before_epoch = s.agency.snapshot().state_epoch
        row = s.cycle_once(cycle_id="idle", now_ts=200.0)
        self.assertEqual(row.status, "HOLD_NO_ACTIVE_GOAL")
        self.assertEqual(row.cognitive_action, "HOLD")
        self.assertEqual(row.next_tick_not_before, 230.0)
        self.assertEqual(row.agency_state_epoch, before_epoch + 1)
        snap = s.agency.snapshot()
        self.assertEqual(snap.mode, "HOLD")
        checkpoint = json.loads(snap.continuation_checkpoint)
        self.assertEqual(checkpoint["schema"], "GRID10_IDLE_HOLD_CHECKPOINT/v1")
        self.assertEqual(checkpoint["reason"], "NO_ACTIVE_OR_TRIAL_GOAL")

        con = sqlite3.connect(str(self.db))
        try:
            heartbeat_count = con.execute("SELECT COUNT(*) FROM ticks").fetchone()[0]
            cycle_count = con.execute("SELECT COUNT(*) FROM grid10_cognitive_cycles").fetchone()[0]
            idle_events = con.execute(
                "SELECT COUNT(*) FROM agency_events WHERE event_type='COGNITIVE_IDLE_HOLD_COMMITTED'"
            ).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(heartbeat_count, 0)
        self.assertEqual(cycle_count, 0)
        self.assertEqual(idle_events, 1)

    def test_exact_wake_event_overrides_later_idle_poll_after_restart(self):
        s1 = self.scheduler()
        active = self.seed_active(s1, now=300.0)
        s1.agency.set_continuation_checkpoint(
            {"goal_id": active.goal_id, "phase": "waiting-for-evidence"},
            event_id="wake:checkpoint",
            now_ts=302.0,
        )
        s1.agency.defer_goal(
            active.goal_id,
            expected_generation=active.generation,
            intent_id="wake:intent",
            wake_kind=WakeKind.EVENT,
            wake_value="percept:new-evidence",
            event_id="wake:defer",
            reason="wait instead of busy-loop",
            now_ts=303.0,
        )
        # With no active goal, scheduler backs off to a later idle poll.
        idle = s1.cycle_once(cycle_id="wake-idle", now_ts=304.0)
        self.assertEqual(idle.status, "HOLD_NO_ACTIVE_GOAL")
        self.assertEqual(idle.next_tick_not_before, 334.0)

        s2 = self.scheduler()
        irrelevant = s2.cycle_once(
            cycle_id="wake-irrelevant",
            now_ts=305.0,
            observed_events=("percept:noise",),
        )
        self.assertEqual(irrelevant.status, "NOT_DUE")
        self.assertEqual(s2.agency.get_goal(active.goal_id).state, GoalState.DORMANT)

        # Exact new evidence wakes immediately even though 334.0 was the prior idle schedule.
        resumed = s2.cycle_once(
            cycle_id="wake-exact",
            now_ts=306.0,
            observed_events=("percept:new-evidence",),
        )
        self.assertEqual(resumed.status, "HEARTBEAT_RAN")
        self.assertEqual(resumed.awakened_goal_ids, (active.goal_id,))
        self.assertEqual(s2.agency.get_goal(active.goal_id).state, GoalState.ACTIVE)
        self.assertEqual(s2.agency.get_intent("wake:intent").state, DeferredIntentState.FIRED)
        self.assertEqual(resumed.next_tick_not_before, 311.0)

        con = sqlite3.connect(str(self.db))
        try:
            row = con.execute(
                "SELECT woken_goal_ids_json FROM grid10_cognitive_cycles WHERE tick_id=?",
                ("wake-exact:heartbeat",),
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(json.loads(row[0]), [active.goal_id])

    def test_default_untrusted_semantic_axes_fail_closed_to_hold_cadence(self):
        config = SchedulerConfig(active_interval_seconds=5.0, hold_poll_seconds=20.0)
        s = PersistentCognitiveScheduler(self.db, self.frames, config=config)
        self.seed_active(s)
        row = s.cycle_once(cycle_id="fail-closed", now_ts=120.0)
        self.assertEqual(row.status, "HEARTBEAT_RAN")
        self.assertEqual(row.cognitive_action, "HOLD")
        self.assertEqual(row.next_tick_not_before, 140.0)


if __name__ == "__main__":
    unittest.main()
