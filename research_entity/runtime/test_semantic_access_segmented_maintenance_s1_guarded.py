from __future__ import annotations

import os
import tempfile
import unittest

from semantic_access_pulse_v12 import PulsePlan
from semantic_access_segmented_maintenance_s1 import SegmentedPulseMaintenanceS1
from semantic_access_segmented_maintenance_s1_guarded import (
    SPMIntegrityError,
    SegmentedPulseMaintenanceS1Guarded,
)
from test_semantic_access_pulse_v12 import VERSIONS, seed_ids, paths_for


class SegmentedPulseMaintenanceS1GuardedTests(unittest.TestCase):
    def setUp(self):
        for key in VERSIONS:
            VERSIONS[key] = 0

    def make(self):
        x = SegmentedPulseMaintenanceS1Guarded()
        x.bootstrap(
            event_id="boot",
            source_epoch=1,
            graph_epoch=1,
            seeds=seed_ids(),
            recompute_seed=paths_for,
        )
        self.assertEqual(x.integrity_state()["status"], "CLEAN")
        self.assertTrue(x.guarded_audit()["pass"])
        return x

    @staticmethod
    def current_segment(x, seed_id: str) -> str:
        head = x.head_basis()
        assert head is not None
        row = x.con.execute(
            "SELECT segment_id FROM access_generation_seed WHERE generation_id=? AND seed_id=?",
            (head[2], seed_id),
        ).fetchone()
        assert row is not None
        return str(row[0])

    @staticmethod
    def repair_plan(event_id: str = "repair") -> PulsePlan:
        impacted = tuple(f"seed:4:{i}" for i in range(4))
        return PulsePlan(event_id, "VALUE_UPDATE", ("cluster:4",), impacted, True, 2, 1)

    def repair(self, x, event_id: str = "repair"):
        return x.apply_pulse(
            self.repair_plan(event_id),
            recompute_seed=paths_for,
            recompute_all_seeds=seed_ids,
            incremental_fraction_limit=0.25,
        )

    def test_clean_local_change_preserves_incremental_spm_s1_path(self):
        x = self.make()
        impacted = tuple(f"seed:3:{i}" for i in range(4))
        for seed in impacted:
            VERSIONS[seed] = 3
        receipt = x.apply_pulse(
            PulsePlan("local", "STATUS_UPDATE", ("cluster:3",), impacted, True, 2, 1),
            recompute_seed=paths_for,
            recompute_all_seeds=seed_ids,
            incremental_fraction_limit=0.25,
        )
        self.assertEqual(receipt.mode, "SEGMENTED_INCREMENTAL_PULSE")
        self.assertEqual(receipt.reused_segment_count, 16)
        self.assertEqual(x.integrity_state()["status"], "CLEAN")
        self.assertTrue(x.guarded_audit()["pass"])
        self.assertIn(":v3", x.query("seed:3:0")[0])
        x.close()

    def test_reverse_dependency_delete_is_dirty_same_transaction_and_rollback_restores_clean(self):
        x = self.make()
        seed = "seed:1:0"
        segment = self.current_segment(x, seed)
        x.con.execute("BEGIN IMMEDIATE")
        x.con.execute(
            "DELETE FROM access_segment_dependency WHERE segment_id=? AND dependency_logical_id=?",
            (segment, "cluster:1"),
        )
        self.assertEqual(x.integrity_state()["status"], "DIRTY")
        self.assertEqual(x.integrity_state()["dirty_reason"], "DEPENDENCY_DELETE_AFTER_PUBLISH")
        x.con.rollback()
        self.assertEqual(x.integrity_state()["status"], "CLEAN")
        self.assertEqual(
            x.con.execute(
                "SELECT count(*) FROM access_segment_dependency WHERE segment_id=? AND dependency_logical_id=?",
                (segment, "cluster:1"),
            ).fetchone()[0],
            1,
        )
        self.assertIn(":v0", x.query(seed)[0])
        x.close()

    def test_committed_reverse_dependency_delete_blocks_read_and_forces_full_repair(self):
        x = self.make()
        seed = "seed:1:0"
        segment = self.current_segment(x, seed)
        x.con.execute(
            "DELETE FROM access_segment_dependency WHERE segment_id=? AND dependency_logical_id=?",
            (segment, "cluster:1"),
        )
        x.con.commit()
        state = x.integrity_state()
        self.assertEqual(state["status"], "DIRTY")
        self.assertEqual(state["dirty_segment_id"], segment)
        with self.assertRaisesRegex(SPMIntegrityError, "projection DIRTY"):
            x.query(seed)

        receipt = self.repair(x)
        self.assertEqual(receipt.mode, "FULL_FALLBACK")
        self.assertEqual(x.integrity_state()["status"], "CLEAN")
        self.assertTrue(x.guarded_audit()["pass"])
        self.assertEqual(self.current_segment(x, seed), segment)
        self.assertEqual(
            x.con.execute(
                "SELECT count(*) FROM access_segment_dependency WHERE segment_id=? AND dependency_logical_id=?",
                (segment, "cluster:1"),
            ).fetchone()[0],
            1,
        )
        repair = x.con.execute(
            "SELECT repair_mode,repaired_generation_id FROM spm_s1_integrity_repair_receipt WHERE event_id='repair'"
        ).fetchone()
        self.assertEqual(repair[0], "FULL_FALLBACK")
        self.assertEqual(repair[1], receipt.generation_id)
        x.close()

    def test_path_update_blocks_tampered_hot_read_and_full_repair_restores_hash(self):
        x = self.make()
        seed = "seed:2:0"
        segment = self.current_segment(x, seed)
        x.con.execute(
            "UPDATE access_segment_path SET path_weight=999.0 WHERE segment_id=? AND path_rank=2",
            (segment,),
        )
        x.con.commit()
        self.assertEqual(x.integrity_state()["dirty_reason"], "PATH_UPDATE_AFTER_PUBLISH")
        with self.assertRaises(SPMIntegrityError):
            x.query(seed)
        receipt = self.repair(x, "repair-path")
        self.assertEqual(receipt.mode, "FULL_FALLBACK")
        self.assertEqual(x.integrity_state()["status"], "CLEAN")
        self.assertTrue(x.audit_current_generation()["pass"])
        self.assertIn(":v0", x.query(seed)[0])
        x.close()

    def test_post_publish_path_insert_and_current_map_mutation_trip_dirty(self):
        x = self.make()
        seed = "seed:0:0"
        segment = self.current_segment(x, seed)
        x.con.execute(
            "INSERT INTO access_segment_path VALUES(?,?,?,?,?,?,?,?)",
            (segment, "malicious", "malicious", 99, 9, 999.0, 0.0, "{}"),
        )
        x.con.commit()
        self.assertEqual(x.integrity_state()["dirty_reason"], "PATH_INSERT_AFTER_PUBLISH")
        with self.assertRaises(SPMIntegrityError):
            x.query(seed)
        self.repair(x, "repair-insert")
        self.assertEqual(x.integrity_state()["status"], "CLEAN")

        head = x.head_basis()
        assert head is not None
        replacement = self.current_segment(x, "seed:0:1")
        x.con.execute(
            "UPDATE access_generation_seed SET segment_id=? WHERE generation_id=? AND seed_id=?",
            (replacement, head[2], seed),
        )
        x.con.commit()
        self.assertEqual(x.integrity_state()["dirty_reason"], "CURRENT_GENERATION_MAP_UPDATE")
        with self.assertRaises(SPMIntegrityError):
            x.query(seed)
        repaired = self.repair(x, "repair-map")
        self.assertEqual(repaired.mode, "FULL_FALLBACK")
        self.assertTrue(x.guarded_audit()["pass"])
        x.close()

    def test_mark_dirty_preserves_outer_transaction_ownership(self):
        x = self.make()
        x.con.execute("CREATE TABLE caller_tx(v TEXT)")
        x.con.execute("INSERT INTO caller_tx VALUES('must-rollback')")
        self.assertTrue(x.con.in_transaction)
        x._set_dirty(None, "TEST_OUTER_TX")
        self.assertTrue(x.con.in_transaction)
        self.assertEqual(x.integrity_state()["status"], "DIRTY")
        x.con.rollback()
        self.assertEqual(x.integrity_state()["status"], "CLEAN")
        self.assertEqual(x.con.execute("SELECT count(*) FROM caller_tx").fetchone()[0], 0)
        x.close()

    def test_opening_guard_over_corrupt_existing_spm_s1_fails_closed(self):
        fd, path = tempfile.mkstemp(prefix="spm-s1-integrity-", suffix=".sqlite3")
        os.close(fd)
        try:
            base = SegmentedPulseMaintenanceS1(path)
            base.bootstrap(
                event_id="boot",
                source_epoch=1,
                graph_epoch=1,
                seeds=seed_ids(),
                recompute_seed=paths_for,
            )
            segment = self.current_segment(base, "seed:1:0")
            base.con.execute(
                "DELETE FROM access_segment_dependency WHERE segment_id=? AND dependency_logical_id=?",
                (segment, "cluster:1"),
            )
            base.con.commit()
            base.close()

            guarded = SegmentedPulseMaintenanceS1Guarded(path)
            self.assertEqual(guarded.integrity_state()["status"], "DIRTY")
            self.assertEqual(guarded.integrity_state()["dirty_reason"], "BOOT_DEEP_AUDIT_FAILED")
            with self.assertRaises(SPMIntegrityError):
                guarded.query("seed:1:0")
            receipt = self.repair(guarded, "repair-boot")
            self.assertEqual(receipt.mode, "FULL_FALLBACK")
            self.assertEqual(guarded.integrity_state()["status"], "CLEAN")
            self.assertTrue(guarded.guarded_audit()["pass"])
            guarded.close()
        finally:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
