#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_fabric import Fabric
from grid10_cognitive_heartbeat_v1 import CognitiveHeartbeatStore, _trusted_normal_axes
from grid10_cognitive_unified_runtime_v2 import (
    assert_shared_unifieddb_authority,
    build_shared_runtime,
    fingerprint_sqlite,
    run_bounded,
)
from grid10_persistent_agency_v1 import DeferredIntentState, GoalState, WakeKind


class UnifiedRuntimeV2Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_one_physical_db_contains_fabric_heartbeat_and_agency_tables(self):
        db = self.root / "unified.sqlite"
        fabric, store, agency, _, fp = build_shared_runtime(db)
        self.assertEqual(Path(fabric.path).resolve(), Path(store.path).resolve())
        self.assertEqual(Path(fabric.path).resolve(), Path(agency.path).resolve())
        self.assertEqual(fp, fingerprint_sqlite(db))
        con = sqlite3.connect(str(db))
        try:
            names = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
        finally:
            con.close()
        self.assertTrue({
            "nodes", "regulators", "ticks", "meta",
            "agency_meta", "goals", "deferred_intents", "agency_events",
        }.issubset(names))

    def test_split_database_authority_fails_closed(self):
        fabric = Fabric(self.root / "fabric.sqlite")
        store = CognitiveHeartbeatStore(self.root / "heartbeat.sqlite")
        with self.assertRaisesRegex(RuntimeError, "UNIFIEDDB_AUTHORITY_SPLIT"):
            assert_shared_unifieddb_authority(fabric, store)

    def test_restart_reopens_same_authority_and_keeps_tick_and_goal_history(self):
        db = self.root / "unified.sqlite"
        _, store1, agency1, runtime1, fp1 = build_shared_runtime(db)
        agency1.create_goal(
            goal_id="goal-restart",
            origin="test",
            semantic_goal="survive process re-entry",
            success_criteria=("goal survives",),
            uncertainty=0.2,
            event_id="evt-goal-create",
            now_ts=100.0,
        )
        first = runtime1.tick_once(tick_id="restart-before", trusted_axes=_trusted_normal_axes())
        self.assertEqual(first.assurance_mode.value, "NORMAL")
        self.assertTrue(store1.load_previous_projected())

        # New objects simulate process/session re-entry. No in-memory runtime state is reused.
        _, store2, agency2, runtime2, fp2 = build_shared_runtime(db)
        second = runtime2.tick_once(tick_id="restart-after", trusted_axes=_trusted_normal_axes())
        self.assertEqual(second.assurance_mode.value, "NORMAL")
        self.assertEqual(fp1, fp2)
        self.assertTrue(store2.load_previous_projected())
        goal = agency2.get_goal("goal-restart")
        self.assertEqual(goal.semantic_goal, "survive process re-entry")
        self.assertEqual(goal.generation, 0)

        con = sqlite3.connect(str(db))
        try:
            tick_ids = [r[0] for r in con.execute(
                "SELECT tick_id FROM ticks ORDER BY created_ts"
            )]
            last = con.execute("SELECT v FROM meta WHERE k='last_tick_id'").fetchone()[0]
            event_count = con.execute(
                "SELECT COUNT(*) FROM agency_events WHERE goal_id='goal-restart'"
            ).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(tick_ids, ["restart-before", "restart-after"])
        self.assertEqual(last, "restart-after")
        self.assertEqual(event_count, 1)

    def test_hold_wake_resume_survives_unified_runtime_restart(self):
        db = self.root / "unified.sqlite"
        _, _, agency1, runtime1, fp1 = build_shared_runtime(db)
        goal = agency1.create_goal(
            goal_id="goal-hold-wake",
            origin="AUTHENTICATED_USER",
            semantic_goal="resume after a deferred evidence condition",
            success_criteria=("wake from exact condition", "continue cognition"),
            uncertainty=0.3,
            event_id="evt-hold-create",
            now_ts=200.0,
        )
        goal = agency1.transition_goal(
            goal.goal_id,
            expected_generation=goal.generation,
            new_state=GoalState.ACTIVE,
            event_id="evt-hold-activate",
            reason="goal admitted",
            now_ts=201.0,
        )
        agency1.set_continuation_checkpoint(
            {"goal_id": goal.goal_id, "phase": "before-hold", "open_deficit": "new-evidence"},
            event_id="evt-hold-checkpoint",
            now_ts=202.0,
        )
        intent = agency1.defer_goal(
            goal.goal_id,
            expected_generation=goal.generation,
            intent_id="intent-hold-wake",
            wake_kind=WakeKind.EVENT,
            wake_value="evidence:new-material-result",
            event_id="evt-hold-defer",
            reason="no useful action until exact new evidence arrives",
            now_ts=203.0,
        )
        self.assertEqual(intent.state, DeferredIntentState.PENDING)
        self.assertEqual(agency1.get_goal(goal.goal_id).state, GoalState.DORMANT)
        before = runtime1.tick_once(tick_id="hold-before-restart", trusted_axes=_trusted_normal_axes())
        self.assertEqual(before.assurance_mode.value, "NORMAL")

        # Re-open the full runtime from the same physical DB, then prove unrelated events do
        # not wake the goal and the exact condition does. This is process/session re-entry,
        # not reuse of in-memory AgencyState.
        _, _, agency2, runtime2, fp2 = build_shared_runtime(db)
        self.assertEqual(fp1, fp2)
        self.assertEqual(agency2.snapshot().goals[0].state, GoalState.DORMANT)
        self.assertIn('"phase":"before-hold"', agency2.snapshot().continuation_checkpoint)
        self.assertEqual(
            agency2.wake_due(now_ts=204.0, observed_events=("evidence:irrelevant",)),
            (),
        )
        self.assertEqual(agency2.get_goal(goal.goal_id).state, GoalState.DORMANT)
        self.assertEqual(
            agency2.wake_due(
                now_ts=205.0,
                observed_events=("evidence:new-material-result",),
                event_id_prefix="restart-wake",
            ),
            (goal.goal_id,),
        )
        resumed = agency2.get_goal(goal.goal_id)
        self.assertEqual(resumed.state, GoalState.ACTIVE)
        self.assertEqual(agency2.get_intent("intent-hold-wake").state, DeferredIntentState.FIRED)

        after = runtime2.tick_once(tick_id="hold-after-resume", trusted_axes=_trusted_normal_axes())
        self.assertEqual(after.assurance_mode.value, "NORMAL")
        con = sqlite3.connect(str(db))
        try:
            events = [r[0] for r in con.execute(
                "SELECT event_type FROM agency_events WHERE goal_id=? ORDER BY event_seq",
                (goal.goal_id,),
            )]
            tick_ids = [r[0] for r in con.execute(
                "SELECT tick_id FROM ticks WHERE tick_id LIKE 'hold-%' ORDER BY created_ts"
            )]
        finally:
            con.close()
        self.assertEqual(
            events,
            ["GOAL_CREATED", "GOAL_TRANSITION", "GOAL_DEFERRED", "DEFERRED_INTENT_FIRED"],
        )
        self.assertEqual(tick_ids, ["hold-before-restart", "hold-after-resume"])

    def test_bounded_entry_emits_two_replayable_frames_on_shared_db(self):
        db = self.root / "unified.sqlite"
        frames = self.root / "frames.jsonl"
        rows = run_bounded(
            unified_db=db,
            frames_jsonl=frames,
            ticks=2,
            interval=0.0,
            trusted_normal_test_fixture=True,
        )
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["assurance_mode"] == "NORMAL" for r in rows))
        parsed = [json.loads(line) for line in frames.read_text().splitlines() if line.strip()]
        self.assertEqual(len(parsed), 2)
        self.assertTrue(all(r["schema"] == "COGNITIVE_LOOP_FRAME/v1" for r in parsed))
        self.assertEqual(fingerprint_sqlite(db).realpath, str(db.resolve()))


if __name__ == "__main__":
    unittest.main()
