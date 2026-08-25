import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from zero_entityos_restart_resize_db_smoke_v1 import (
    BoundaryError,
    CanonicalStateAuthority,
    CognitiveGridRuntime,
    GridConfig,
    run_restart_resize_smoke,
)


class RestartResizeDBSmokeTests(unittest.TestCase):
    def test_full_restart_resize_discriminator(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = run_restart_resize_smoke(Path(td) / "s0.sqlite3")
        self.assertEqual(1, receipt["N_before"])
        self.assertEqual(20, receipt["N_after"])
        self.assertTrue(all(receipt["checks"].values()))
        self.assertNotEqual(
            receipt["evidence"]["s0_before_digest"],
            receipt["evidence"]["s0_after_admission_digest"],
        )
        self.assertTrue(all(v == 0 for v in receipt["evidence"]["s1_after_restart"].values()))
        self.assertEqual(0, receipt["credit_boundary"]["whole_entityos_hcu_runtime"])

    def test_sqlite_readonly_engine_rejects_direct_cognitive_write(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "s0.sqlite3"
            authority = CanonicalStateAuthority(path)
            authority.seed("fact", 7, provenance="test", generation=1, epoch=1)
            grid = CognitiveGridRuntime(path, GridConfig(n=1, generation=1))
            try:
                self.assertTrue(grid.attempt_direct_s0_write("illegal", 9))
                self.assertIsNone(authority.get("illegal"))
            finally:
                grid.close()
                authority.close()

    def test_stale_generation_proposal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "s0.sqlite3"
            authority = CanonicalStateAuthority(path)
            authority.seed("fact", 7, provenance="test", generation=2, epoch=1)
            grid = CognitiveGridRuntime(path, GridConfig(n=1, generation=2))
            try:
                result = grid.execute(grid.enqueue("ZECP15", {"x": 1}))
                proposal = grid.propose_db_write(result, "memory", {"m": 1})
                proposal["generation"] = 1
                with self.assertRaisesRegex(BoundaryError, "STALE_GENERATION"):
                    authority.admit_proposal(proposal, current_generation=2, epoch=2)
                self.assertIsNone(authority.get("memory"))
            finally:
                grid.close()
                authority.close()

    def test_read_epoch_stays_fresh_after_rejected_direct_write(self):
        """Regression: a failed direct-write attempt must not pin the read-only
        S0 connection to a stale pre-attempt snapshot. See
        attempt_direct_s0_write's rollback -- without it, subsequent epoch
        reads on the same connection silently kept returning 0 even after
        another connection committed a newer epoch."""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "s0.sqlite3"
            authority = CanonicalStateAuthority(path)
            authority.seed("goal", {"g": 1}, provenance="test", generation=1, epoch=1)
            grid = CognitiveGridRuntime(path, GridConfig(n=1, generation=1))
            try:
                self.assertTrue(grid.attempt_direct_s0_write("illegal/first", {"x": 1}))
                self.assertEqual(0, grid.read_s0_epoch("shared/key"))
                authority.seed("shared/key", {"winner": "base"}, provenance="test", generation=1, epoch=7)
                self.assertEqual(
                    7,
                    grid.read_s0_epoch("shared/key"),
                    "read-only connection must observe the freshly committed epoch, "
                    "not a stale snapshot pinned by the earlier rejected write attempt",
                )
                result = grid.execute(grid.enqueue("ZECP15", {"x": 1}))
                proposal_a = grid.propose_db_write(result, "shared/key", {"winner": "A"})
                proposal_b = grid.propose_db_write(result, "shared/key", {"winner": "B"})
                self.assertEqual(7, proposal_a["expected_s0_epoch"])
                self.assertEqual(7, proposal_b["expected_s0_epoch"])
            finally:
                grid.close()
                authority.close()

    def test_restart_drops_s1_but_preserves_s0(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "s0.sqlite3"
            authority = CanonicalStateAuthority(path)
            authority.seed("goal", {"g": 1}, provenance="test", generation=1, epoch=1)
            first = CognitiveGridRuntime(path, GridConfig(n=1, generation=1))
            first.execute(first.enqueue("ZECP03", {"goal_ref": "goal"}))
            self.assertEqual(1, first.s1_counts()["result_log"])
            first.close()
            second = CognitiveGridRuntime(path, GridConfig(n=10, generation=1))
            try:
                self.assertEqual({"g": 1}, second.read_s0("goal"))
                self.assertTrue(all(v == 0 for v in second.s1_counts().values()))
            finally:
                second.close()
                authority.close()


if __name__ == "__main__":
    unittest.main()
