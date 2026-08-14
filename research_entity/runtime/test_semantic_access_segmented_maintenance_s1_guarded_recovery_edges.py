from __future__ import annotations

import unittest

from semantic_access_pulse_v12 import PulsePlan
from semantic_access_segmented_maintenance_s1_guarded import (
    SPMIntegrityError,
    SegmentedPulseMaintenanceS1Guarded,
)
from test_semantic_access_pulse_v12 import VERSIONS, seed_ids, paths_for


class SPMGuardedRecoveryEdgeTests(unittest.TestCase):
    def setUp(self):
        for key in VERSIONS:
            VERSIONS[key] = 0

    def make(self):
        x = SegmentedPulseMaintenanceS1Guarded()
        x.bootstrap(event_id="boot", source_epoch=1, graph_epoch=1, seeds=seed_ids(), recompute_seed=paths_for)
        return x

    @staticmethod
    def segment_for(x, generation_id: str, seed_id: str) -> str:
        return str(x.con.execute(
            "SELECT segment_id FROM access_generation_seed WHERE generation_id=? AND seed_id=?",
            (generation_id, seed_id),
        ).fetchone()[0])

    def test_corrupted_previous_generation_map_is_quarantined_after_repair(self):
        x = self.make()
        before = x.head_basis()
        assert before is not None
        previous_generation = before[2]
        replacement = self.segment_for(x, previous_generation, "seed:0:1")
        x.con.execute(
            "UPDATE access_generation_seed SET segment_id=? WHERE generation_id=? AND seed_id='seed:0:0'",
            (replacement, previous_generation),
        )
        x.con.commit()
        self.assertEqual(x.integrity_state()["status"], "DIRTY")
        receipt = x.apply_pulse(
            PulsePlan("repair-map-edge", "VALUE_UPDATE", ("cluster:4",), tuple(f"seed:4:{i}" for i in range(4)), True, 2, 1),
            recompute_seed=paths_for,
            recompute_all_seeds=seed_ids,
            incremental_fraction_limit=.25,
        )
        self.assertEqual(receipt.mode, "FULL_FALLBACK")
        self.assertEqual(receipt.previous_generation_id, previous_generation)
        status = x.con.execute(
            "SELECT status FROM access_generation WHERE generation_id=?", (previous_generation,)
        ).fetchone()[0]
        self.assertEqual(status, "QUARANTINED")
        self.assertEqual(x.integrity_state()["status"], "CLEAN")
        self.assertTrue(x.guarded_audit()["pass"])
        x.close()

    def test_incoherent_access_head_is_detected_on_read_and_fails_closed(self):
        x = self.make()
        x.con.execute("UPDATE access_head SET generation_hash='forged' WHERE head_key='CURRENT'")
        x.con.commit()
        self.assertEqual(x.integrity_state()["status"], "CLEAN")
        with self.assertRaisesRegex(SPMIntegrityError, "access_head is present but incoherent"):
            x.query("seed:0:0")
        state = x.integrity_state()
        self.assertEqual(state["status"], "DIRTY")
        self.assertEqual(state["dirty_reason"], "ACCESS_HEAD_INCOHERENT")
        x.close()

    def test_dependency_key_move_away_from_current_is_caught_on_old_membership(self):
        x = self.make()
        head = x.head_basis()
        assert head is not None
        segment = self.segment_for(x, head[2], "seed:2:0")
        x.con.execute(
            "INSERT INTO access_segment(segment_id,seed_id,segment_hash,path_count,created_ns) VALUES(?,?,?,?,?)",
            ("seg-unused-test", "unused", "unused-hash", 1, 0),
        )
        x.con.execute(
            "UPDATE access_segment_dependency SET segment_id='seg-unused-test' "
            "WHERE segment_id=? AND dependency_logical_id='cluster:2'",
            (segment,),
        )
        x.con.commit()
        state = x.integrity_state()
        self.assertEqual(state["status"], "DIRTY")
        self.assertEqual(state["dirty_reason"], "DEPENDENCY_UPDATE_AFTER_PUBLISH")
        self.assertEqual(state["dirty_segment_id"], segment)
        with self.assertRaises(SPMIntegrityError):
            x.query("seed:2:0")
        x.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
