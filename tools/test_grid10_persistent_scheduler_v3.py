#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes
from grid10_persistent_agency_v1 import GoalState
from grid10_persistent_scheduler_v1 import SchedulerConfig
from grid10_persistent_scheduler_v3 import PersistentCognitiveSchedulerV3


class PersistentSchedulerV3Tests(unittest.TestCase):
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

    def scheduler(self, *, stale=0.0):
        return PersistentCognitiveSchedulerV3(
            self.db,
            self.frames,
            config=self.config,
            recovery_stale_after_seconds=stale,
        )

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
        scheduler.agency.transition_goal(
            goal_id,
            expected_generation=goal.generation,
            new_state=GoalState.ACTIVE,
            event_id=f"{goal_id}:activate",
            reason="admitted",
            now_ts=now + 1,
        )

    def test_active_scheduler_tick_is_attempt_bound_and_provider_off(self):
        s = self.scheduler(stale=0.0)
        self.seed_active(s)
        row = s.cycle_once(cycle_id="sched-v3-normal", now_ts=110.0)
        self.assertEqual(row.status, "HEARTBEAT_RAN")
        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        try:
            attempt = con.execute(
                "SELECT * FROM grid10_v7_cycle_attempts WHERE tick_id=?",
                (row.heartbeat_tick_id,),
            ).fetchone()
            v6 = con.execute(
                "SELECT receipt_json FROM grid10_v6_control_bound_receipts WHERE tick_id=?",
                (row.heartbeat_tick_id,),
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(attempt["status"], "CLOSED_SUCCESS")
        receipt = json.loads(v6["receipt_json"])
        self.assertEqual(
            receipt["controlled_cognitive_cycle_receipt"]["reason"],
            "NO_EXPLICIT_ADMITTED_INFERENCE_FN",
        )
        self.assertEqual(receipt["controlled_cognitive_cycle_receipt"]["provider_calls"], 0)

    def test_scheduler_reentry_recovers_committed_v4_without_v6_closure(self):
        s = self.scheduler(stale=3600.0)
        self.seed_active(s)
        tick_id = "sched-v3-crash:heartbeat"
        s.runtime._prepare_attempt(tick_id=tick_id)
        s.runtime.runtime_v4.tick_once(
            tick_id=tick_id,
            now_ts=110.0,
            trusted_axes=_trusted_normal_axes(),
        )
        s.runtime.reconcile_pending_attempts(force=True)

        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        try:
            row = con.execute(
                "SELECT status,recovery_receipt_json FROM grid10_v7_cycle_attempts WHERE tick_id=?",
                (tick_id,),
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(row["status"], "RECOVERED_POST_V4_COMMIT_UNKNOWN")
        receipt = json.loads(row["recovery_receipt_json"])
        self.assertEqual(receipt["cognitive_outcome"], "UNKNOWN")
        self.assertFalse(receipt["same_tick_retry_authorized"])


if __name__ == "__main__":
    unittest.main()
