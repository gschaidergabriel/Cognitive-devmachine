import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_historical_backfill as backfill
from free_swarm_backfill_exhaustiveness_878 import MAX_EXHAUSTIVE_PASSES, install


class CurrentHeadSaturationTests(unittest.TestCase):
    def setUp(self):
        install(backfill)
        self.con = sqlite3.connect(":memory:")
        self.con.execute(
            """CREATE TABLE historical_chunks(
              chunk_id TEXT PRIMARY KEY,
              source_event_id TEXT NOT NULL,
              extraction_passes INTEGER NOT NULL DEFAULT 0,
              consecutive_zero_novel INTEGER NOT NULL DEFAULT 0,
              last_novel_count INTEGER NOT NULL DEFAULT 0,
              last_extracted_at TEXT,
              state TEXT NOT NULL DEFAULT 'PENDING_EXTRACTION')"""
        )
        self.con.execute("INSERT INTO historical_chunks(chunk_id,source_event_id) VALUES('c','s')")

    def tearDown(self):
        self.con.close()

    def row(self):
        return self.con.execute(
            "SELECT extraction_passes,consecutive_zero_novel,last_novel_count,state FROM historical_chunks WHERE chunk_id='c'"
        ).fetchone()

    def progress(self, n, exhaustive, novel=0, source="s"):
        backfill._record_batch_progress(
            self.con,
            {"historical_chunk_id":"c","historical_source_event_id":source,
             "extraction_pass":n,"exhaustive":exhaustive,"deltas":[]},
            novel,
        )

    def test_one_exhaustive_zero_is_not_saturated(self):
        self.progress(1, True)
        self.assertEqual(self.row(), (1, 1, 0, "PENDING_EXTRACTION"))

    def test_two_exhaustive_zeroes_saturate(self):
        self.progress(1, True)
        self.progress(2, True)
        self.assertEqual(self.row(), (2, 2, 0, "SATURATED"))

    def test_nonexhaustive_resets_zero_streak(self):
        self.progress(1, True)
        self.progress(2, False)
        self.progress(3, True)
        self.assertEqual(self.row(), (3, 1, 0, "PENDING_EXTRACTION"))

    def test_batch_identity_guard_survives_install(self):
        self.progress(1, True, source="foreign")
        self.assertEqual(self.row(), (0, 0, 0, "PENDING_EXTRACTION"))
        self.progress(2, True)
        self.assertEqual(self.row(), (0, 0, 0, "PENDING_EXTRACTION"))

    def test_pass_ceiling_is_bounded_but_not_old_three(self):
        self.assertGreaterEqual(backfill.MAX_PASSES, MAX_EXHAUSTIVE_PASSES)
        self.assertGreater(backfill.MAX_PASSES, 3)

    def test_runtime_capsule_installs_same_policy_in_fresh_process(self):
        code = (
            "import sys; "
            f"sys.path.insert(0, {str(TOOLS)!r}); "
            "import run_free_swarm_historical_backfill_capsule_878 as capsule; "
            "assert capsule.historical_backfill_core.MAX_PASSES >= 64; "
            "assert capsule.ingest_artifact_history is capsule.historical_backfill_core.ingest_artifact_history; "
            "assert capsule.backfill_metrics is capsule.historical_backfill_core.backfill_metrics"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
