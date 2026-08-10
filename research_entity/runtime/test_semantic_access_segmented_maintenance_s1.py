from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from semantic_access_pulse_v12 import PulsePlan, StalePulse
from semantic_access_segmented_maintenance_s1 import SegmentedPulseMaintenanceS1
from test_semantic_access_pulse_v16 import SegmentedPulseV16Tests, seed_ids, paths_for
from test_semantic_access_pulse_v12 import VERSIONS


class RaceInjectSPMS1(SegmentedPulseMaintenanceS1):
    """Inject a competitor after stale _head() read and before stale BEGIN IMMEDIATE."""

    def arm_race(self, callback):
        self._race_callback = callback
        self._race_armed = True

    def _head(self):
        head = super()._head()
        if getattr(self, "_race_armed", False):
            self._race_armed = False
            self._race_callback()
        return head


class SegmentedPulseMaintenanceS1Tests(SegmentedPulseV16Tests):
    def make(self):
        x = SegmentedPulseMaintenanceS1()
        x.bootstrap(
            event_id="boot",
            source_epoch=1,
            graph_epoch=1,
            seeds=seed_ids(),
            recompute_seed=paths_for,
        )
        return x

    def test_collision_free_implementation_identity(self):
        x = self.make()
        audit = x.audit_current_generation()
        self.assertEqual(
            audit["implementation"], "UNIFIEDDB_SEGMENTED_PULSE_MAINTENANCE_S1"
        )
        self.assertTrue(audit["single_current_generation"])
        self.assertEqual(audit["stale_parent_cas"], "IN_LOCK")
        x.close()

    def test_database_guard_rejects_second_current_generation(self):
        x = self.make()
        with self.assertRaises(sqlite3.IntegrityError):
            with x.con:
                x.con.execute(
                    "INSERT INTO access_generation VALUES(?,?,?,?,?,'CURRENT',?,?)",
                    ("evil", 2, 1, "evil-hash", 1, 1, 1),
                )
        self.assertEqual(
            x.con.execute(
                "SELECT count(*) FROM access_generation WHERE status='CURRENT'"
            ).fetchone()[0],
            1,
        )
        x.close()

    def test_stale_parent_race_fails_before_publish_and_preserves_winner(self):
        for key in VERSIONS:
            VERSIONS[key] = 0
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "spm-s1.sqlite")
            winner = SegmentedPulseMaintenanceS1(path)
            winner.bootstrap(
                event_id="boot-race",
                source_epoch=1,
                graph_epoch=1,
                seeds=seed_ids(),
                recompute_seed=paths_for,
            )
            stale = RaceInjectSPMS1(path)
            winner_generation = {"id": None}
            impacted = tuple(f"seed:2:{i}" for i in range(4))

            def publish_winner():
                for seed in impacted:
                    VERSIONS[seed] = 1
                receipt = winner.apply_pulse(
                    PulsePlan(
                        "winner", "VALUE_UPDATE", ("cluster:2",), impacted, True, 2, 1
                    ),
                    recompute_seed=paths_for,
                    recompute_all_seeds=seed_ids,
                    incremental_fraction_limit=0.25,
                )
                winner_generation["id"] = receipt.generation_id

            stale.arm_race(publish_winner)
            with self.assertRaises(StalePulse):
                stale.apply_pulse(
                    PulsePlan(
                        "stale", "VALUE_UPDATE", ("cluster:2",), impacted, True, 2, 1
                    ),
                    recompute_seed=paths_for,
                    recompute_all_seeds=seed_ids,
                    incremental_fraction_limit=0.25,
                )

            head = winner.head_basis()
            self.assertIsNotNone(head)
            self.assertEqual(head[2], winner_generation["id"])
            self.assertEqual(
                winner.con.execute(
                    "SELECT count(*) FROM access_generation WHERE status='CURRENT'"
                ).fetchone()[0],
                1,
            )
            self.assertIn(":v1", winner.query("seed:2:0")[0])
            self.assertIsNone(
                winner.con.execute(
                    "SELECT generation_id FROM access_generation "
                    "WHERE status='CURRENT' AND generation_id<>?",
                    (winner_generation["id"],),
                ).fetchone()
            )
            stale.close()
            winner.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
