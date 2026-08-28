#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_fabric import Fabric
from grid10_cognitive_heartbeat_v1 import CognitiveHeartbeatStore, _trusted_normal_axes
from grid10_cognitive_unified_runtime_v3 import (
    assert_unified_runtime_authority,
    build_unified_agency_runtime,
    runtime_authority_receipt,
)
from grid10_persistent_agency_v1 import GoalState, PersistentAgencyStore


class UnifiedAgencyRuntimeV3Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_one_physical_db_contains_fabric_heartbeat_and_agency(self):
        db = self.root / "unified.sqlite"
        fabric, heartbeat, agency, _, fp = build_unified_agency_runtime(db)
        self.assertEqual(Path(fabric.path).resolve(), db.resolve())
        self.assertEqual(Path(heartbeat.path).resolve(), db.resolve())
        self.assertEqual(Path(agency.path).resolve(), db.resolve())
        self.assertEqual(assert_unified_runtime_authority(fabric, heartbeat, agency), fp)

        con = sqlite3.connect(str(db))
        try:
            names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            con.close()
        for required in ("nodes", "regulators", "ticks", "agency_meta", "goals", "deferred_intents", "agency_events"):
            self.assertIn(required, names)

    def test_split_agency_database_fails_closed(self):
        shared = self.root / "shared.sqlite"
        fabric = Fabric(shared)
        heartbeat = CognitiveHeartbeatStore(shared)
        agency = PersistentAgencyStore(self.root / "agency.sqlite")
        with self.assertRaisesRegex(RuntimeError, "UNIFIEDDB_AGENCY_AUTHORITY_SPLIT"):
            assert_unified_runtime_authority(fabric, heartbeat, agency)

    def test_goal_and_heartbeat_survive_reopen_on_same_authority(self):
        db = self.root / "unified.sqlite"
        _, _, agency1, runtime1, fp1 = build_unified_agency_runtime(db)
        goal = agency1.create_goal(
            goal_id="g1",
            origin="AUTHENTICATED_USER",
            semantic_goal="continue verified GRID10 construction",
            state=GoalState.CANDIDATE,
            success_criteria=("receipt",),
            uncertainty=0.2,
            priority=10,
            event_id="e:create",
            now_ts=100.0,
        )
        agency1.transition_goal(
            "g1",
            expected_generation=goal.generation,
            new_state=GoalState.ACTIVE,
            event_id="e:activate",
            reason="admitted",
            now_ts=101.0,
        )
        first = runtime1.tick_once(tick_id="tick-before-restart", trusted_axes=_trusted_normal_axes())
        self.assertEqual(first.assurance_mode.value, "NORMAL")

        _, heartbeat2, agency2, runtime2, fp2 = build_unified_agency_runtime(db)
        second = runtime2.tick_once(tick_id="tick-after-restart", trusted_axes=_trusted_normal_axes())
        self.assertEqual(second.assurance_mode.value, "NORMAL")
        self.assertEqual(fp1.realpath, fp2.realpath)
        self.assertEqual(fp1.device, fp2.device)
        self.assertEqual(fp1.inode, fp2.inode)
        self.assertEqual(agency2.get_goal("g1").state, GoalState.ACTIVE)
        self.assertTrue(heartbeat2.load_previous_projected())

    def test_receipt_is_bounded_and_grants_no_runtime_promotion(self):
        db = self.root / "unified.sqlite"
        fabric, heartbeat, agency, _, _ = build_unified_agency_runtime(db)
        receipt = runtime_authority_receipt(fabric, heartbeat, agency)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["provider_calls"], 0)
        self.assertEqual(receipt["physical_grid10_credit"], 0)
        self.assertEqual(receipt["whole_hcu_credit"], 0)
        self.assertFalse(receipt["canonical_truth_authority_changed"])
        self.assertFalse(receipt["external_effect_authority_changed"])


if __name__ == "__main__":
    unittest.main()
