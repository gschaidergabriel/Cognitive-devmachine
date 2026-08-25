from pathlib import Path
import sqlite3
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_historical_backfill as backfill
from free_swarm_backfill_exhaustiveness_878 import (
    MAX_EXHAUSTIVE_PASSES,
    install,
)


class BackfillExhaustiveness878Tests(unittest.TestCase):
    def setUp(self):
        install(backfill)
        self.con = sqlite3.connect(":memory:")
        self.con.execute(
            """
            CREATE TABLE historical_chunks(
              chunk_id TEXT PRIMARY KEY,
              extraction_passes INTEGER NOT NULL DEFAULT 0,
              consecutive_zero_novel INTEGER NOT NULL DEFAULT 0,
              last_novel_count INTEGER NOT NULL DEFAULT 0,
              last_extracted_at TEXT,
              state TEXT NOT NULL DEFAULT 'PENDING_EXTRACTION'
            )
            """
        )
        self.con.execute("INSERT INTO historical_chunks(chunk_id) VALUES('chunk-a')")

    def tearDown(self):
        self.con.close()

    def row(self):
        return self.con.execute(
            "SELECT extraction_passes,consecutive_zero_novel,last_novel_count,state "
            "FROM historical_chunks WHERE chunk_id='chunk-a'"
        ).fetchone()

    def progress(self, extraction_pass, exhaustive, novel_count):
        backfill._record_batch_progress(
            self.con,
            {
                "historical_chunk_id": "chunk-a",
                "extraction_pass": extraction_pass,
                "exhaustive": exhaustive,
            },
            novel_count,
        )

    def test_nonexhaustive_full_batch_never_saturates(self):
        self.progress(1, False, 8)
        self.progress(2, False, 8)
        self.progress(3, False, 0)
        passes, zeros, novel, state = self.row()
        self.assertEqual(passes, 3)
        self.assertEqual(zeros, 0)
        self.assertEqual(novel, 0)
        self.assertEqual(state, "PENDING_EXTRACTION")

    def test_missing_exhaustive_signal_fails_closed(self):
        backfill._record_batch_progress(
            self.con,
            {"historical_chunk_id": "chunk-a", "extraction_pass": 1},
            0,
        )
        self.assertEqual(self.row()[1], 0)
        self.assertEqual(self.row()[3], "PENDING_EXTRACTION")

    def test_requires_two_explicit_exhaustive_zero_confirmations(self):
        self.progress(1, True, 4)
        self.progress(2, True, 0)
        self.assertEqual(self.row()[1], 1)
        self.assertEqual(self.row()[3], "PENDING_EXTRACTION")
        self.progress(3, True, 0)
        self.assertEqual(self.row()[1], 2)
        self.assertEqual(self.row()[3], "SATURATED")

    def test_nonexhaustive_pass_resets_confirmation_streak(self):
        self.progress(1, True, 0)
        self.progress(2, False, 0)
        self.progress(3, True, 0)
        self.assertEqual(self.row()[1], 1)
        self.assertEqual(self.row()[3], "PENDING_EXTRACTION")

    def test_old_three_pass_ceiling_is_not_semantic_completion(self):
        self.assertGreaterEqual(backfill.MAX_PASSES, MAX_EXHAUSTIVE_PASSES)
        self.assertGreater(backfill.MAX_PASSES, 3)

    def test_scheduler_does_not_hardcode_exhaustive_true(self):
        source = (TOOLS / "free_swarm_backfill_scheduler.py").read_text(encoding="utf-8")
        self.assertNotIn('"exhaustive":true', source)
        self.assertIn('"exhaustive":<EXHAUSTIVE_BOOLEAN>', source)
        self.assertIn("two consecutive zero-novel passes", source)


if __name__ == "__main__":
    unittest.main()
