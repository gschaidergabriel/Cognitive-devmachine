from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

from zero_entityos_restart_resize_db_boundary_v1 import (
    BoundaryError,
    RestartResizeDBBoundary,
)


class RestartResizeDBBoundaryTests(unittest.TestCase):
    def test_s0_survives_restart_and_n_change_while_s1_s2_are_rebuilt_or_lost(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "entityos.db"
            a = RestartResizeDBBoundary(db, grid_n=1)
            a.seed_s0_fixture("project/fact", {"value": 7})
            before = a.s0_fingerprint()
            p1 = a.rebuild_s1_from_s0(["project/fact"])
            self.assertEqual("PROJECTED_FROM_S0", p1["project/fact"]["status"])
            a.write_s2("scratch", {"temporary": True})
            self.assertTrue(a.s1)
            self.assertTrue(a.s2)
            g1 = a.runtime_generation
            a.close()

            b = RestartResizeDBBoundary(db, grid_n=20)
            self.assertGreater(b.runtime_generation, g1)
            self.assertEqual(before, b.s0_fingerprint())
            self.assertEqual({}, b.s1)
            self.assertEqual({}, b.s2)
            p2 = b.rebuild_s1_from_s0(["project/fact"])
            self.assertEqual({"value": 7}, p2["project/fact"]["value"])
            self.assertFalse(p2["project/fact"]["truth_authority"])
            self.assertEqual(20, b.grid_n)
            b.close()

    def test_resize_1_10_20_never_changes_s0_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "entityos.db"
            r = RestartResizeDBBoundary(db, grid_n=1)
            r.seed_s0_fixture("memory/a", {"x": 1})
            expected = r.s0_fingerprint()
            r.close()
            for n in (10, 20, 1):
                r = RestartResizeDBBoundary(db, grid_n=n)
                self.assertEqual(expected, r.s0_fingerprint())
                r.close()

    def test_stale_generation_proposal_rejected_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "entityos.db"
            a = RestartResizeDBBoundary(db, grid_n=10)
            a.seed_s0_fixture("project/fact", {"value": 7})
            stale = a.propose_db_write(
                work_id="work-stale", object_key="project/fact", value={"value": 8}
            )
            a.close()

            b = RestartResizeDBBoundary(db, grid_n=20)
            with self.assertRaisesRegex(BoundaryError, "SOURCE_GENERATION_STALE"):
                b.admit_db_write(stale, expected_generation=b.runtime_generation)
            self.assertEqual({"value": 7}, b.read_s0("project/fact")["value"])
            b.close()

    def test_current_generation_proposal_can_be_deterministically_admitted(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "entityos.db"
            r = RestartResizeDBBoundary(db, grid_n=10)
            r.seed_s0_fixture("project/fact", {"value": 7})
            proposal = r.propose_db_write(
                work_id="work-current", object_key="project/fact", value={"value": 9}
            )
            self.assertEqual({"value": 7}, r.read_s0("project/fact")["value"])
            admitted = r.admit_db_write(
                proposal, expected_generation=r.runtime_generation
            )
            self.assertEqual({"value": 9}, admitted["value"])
            self.assertEqual(2, admitted["epoch"])
            self.assertTrue(admitted["provenance"].startswith("ADMITTED_PROPOSAL:"))
            r.close()

    def test_direct_model_grid_claude_jspace_s0_write_is_forbidden(self):
        with tempfile.TemporaryDirectory() as td:
            r = RestartResizeDBBoundary(Path(td) / "entityos.db", grid_n=10)
            with self.assertRaisesRegex(BoundaryError, "TO_S0_FORBIDDEN"):
                r.model_direct_s0_write("project/fact", {"fake": True})
            self.assertEqual(0, r.count("s0_state"))
            r.close()

    def test_s1_cache_cannot_become_recovery_authority(self):
        with tempfile.TemporaryDirectory() as td:
            r = RestartResizeDBBoundary(Path(td) / "entityos.db", grid_n=10)
            with self.assertRaisesRegex(BoundaryError, "NOT_S0_RECOVERY_AUTHORITY"):
                r.recover_s0_from_s1_cache({"project/fact": {"value": 999}})
            self.assertEqual(0, r.count("s0_state"))
            r.close()

    def test_effect_is_proposal_only_and_direct_effect_fails(self):
        with tempfile.TemporaryDirectory() as td:
            r = RestartResizeDBBoundary(Path(td) / "entityos.db", grid_n=10)
            r.propose_effect(work_id="work-1", request={"kind": "fixture-noop"})
            self.assertEqual(1, r.count("effect_proposals"))
            self.assertEqual(0, r.count("effect_journal"))
            with self.assertRaisesRegex(BoundaryError, "EFFECTGATE_REQUIRED"):
                r.direct_effect({"kind": "fixture-noop"})
            self.assertEqual(0, r.count("effect_journal"))
            r.close()

    def test_unknown_s0_rebuild_stays_unknown_not_false(self):
        with tempfile.TemporaryDirectory() as td:
            r = RestartResizeDBBoundary(Path(td) / "entityos.db", grid_n=10)
            p = r.rebuild_s1_from_s0(["missing"])
            self.assertEqual("UNKNOWN", p["missing"]["status"])
            self.assertIsNone(p["missing"]["source_s0_digest"])
            self.assertFalse(p["missing"]["truth_authority"])
            r.close()


if __name__ == "__main__":
    unittest.main()
