#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from grid10_cognitive_agency_loop_v1 import PersistentAgencyHeartbeatLoop
from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_cognitive_unified_runtime_v2 import build_shared_runtime
from grid10_persistent_agency_v1 import GoalState, WakeKind


class PersistentAgencyHeartbeatLoopTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.db = self.root / "unified.sqlite"
        _, self.heartbeat_store, self.agency, self.heartbeat, _ = build_shared_runtime(self.db)
        self.loop = PersistentAgencyHeartbeatLoop(self.agency, self.heartbeat, tick_interval_seconds=10.0)

    def tearDown(self):
        self.td.cleanup()

    def seed_active(self, now: float = 100.0):
        g = self.agency.create_goal(
            goal_id="g1", origin="AUTHENTICATED_USER", semantic_goal="continue bounded work",
            state=GoalState.CANDIDATE, success_criteria=("verified receipt",),
            uncertainty=0.2, priority=10, event_id="e:create", now_ts=now,
        )
        return self.agency.transition_goal(
            "g1", expected_generation=g.generation, new_state=GoalState.ACTIVE,
            event_id="e:activate", reason="admitted", now_ts=now + 0.1,
        )

    def test_not_due_means_no_heartbeat_tick(self):
        self.seed_active()
        self.agency.schedule_next_tick(not_before=200.0, mode="NORMAL", event_id="e:schedule", now_ts=101.0)
        receipt = self.loop.tick_if_due(
            tick_id="t-not-due", now_ts=150.0, trusted_axes=_trusted_normal_axes()
        )
        self.assertEqual(receipt.disposition, "NOT_DUE")
        self.assertIsNone(receipt.heartbeat)
        self.assertEqual(receipt.active_goal_ids, ("g1",))
        self.assertEqual(self.heartbeat_store.load_previous_projected(), {})

    def test_due_tick_runs_heartbeat_and_persists_checkpoint_and_next_tick(self):
        self.seed_active()
        self.agency.schedule_next_tick(not_before=110.0, mode="NORMAL", event_id="e:schedule", now_ts=101.0)
        receipt = self.loop.tick_if_due(
            tick_id="t-due", now_ts=110.0, trusted_axes=_trusted_normal_axes()
        )
        self.assertEqual(receipt.disposition, "TICKED")
        self.assertEqual(receipt.active_goal_ids, ("g1",))
        self.assertIsNotNone(receipt.heartbeat)
        self.assertEqual(receipt.heartbeat.assurance_mode.value, "NORMAL")
        snap = self.agency.snapshot()
        self.assertEqual(snap.next_tick_not_before, 120.0)
        self.assertIn('"tick_id":"t-due"', snap.continuation_checkpoint)
        self.assertIn('"active_goal_ids":["g1"]', snap.continuation_checkpoint)

    def test_due_wake_forces_immediate_tick_even_when_idle_schedule_is_later(self):
        active = self.seed_active()
        self.agency.defer_goal(
            "g1", expected_generation=active.generation, intent_id="i1",
            wake_kind=WakeKind.TIME_AT, wake_value="150", event_id="e:defer",
            reason="bounded hold", now_ts=120.0,
        )
        self.agency.schedule_next_tick(not_before=999.0, mode="HOLD", event_id="e:idle", now_ts=121.0)

        receipt = self.loop.tick_if_due(
            tick_id="t-wake", now_ts=150.0, trusted_axes=_trusted_normal_axes()
        )
        self.assertEqual(receipt.disposition, "TICKED")
        self.assertEqual(receipt.awakened_goal_ids, ("g1",))
        self.assertEqual(receipt.active_goal_ids, ("g1",))
        self.assertEqual(self.agency.get_goal("g1").state, GoalState.ACTIVE)
        self.assertEqual(self.agency.snapshot().next_tick_not_before, 160.0)

    def test_restart_reuses_same_agency_schedule_and_goal_state(self):
        self.seed_active()
        self.agency.schedule_next_tick(not_before=175.0, mode="NORMAL", event_id="e:schedule", now_ts=101.0)

        _, heartbeat_store2, agency2, heartbeat2, _ = build_shared_runtime(self.db)
        loop2 = PersistentAgencyHeartbeatLoop(agency2, heartbeat2, tick_interval_seconds=10.0)
        before = loop2.tick_if_due(
            tick_id="t-before", now_ts=174.0, trusted_axes=_trusted_normal_axes()
        )
        self.assertEqual(before.disposition, "NOT_DUE")
        due = loop2.tick_if_due(
            tick_id="t-after", now_ts=175.0, trusted_axes=_trusted_normal_axes()
        )
        self.assertEqual(due.disposition, "TICKED")
        self.assertEqual(agency2.get_goal("g1").state, GoalState.ACTIVE)
        self.assertTrue(heartbeat_store2.load_previous_projected())


if __name__ == "__main__":
    unittest.main()
