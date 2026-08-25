from pathlib import Path
import sqlite3
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_historical_backfill as backfill
from free_swarm_backfill_exhaustiveness_878 import MAX_EXHAUSTIVE_PASSES, install


class BackfillExhaustiveness878SuccessorTests(unittest.TestCase):
    def setUp(self):
        install(backfill)
        self.con = sqlite3.connect(":memory:")
        self.con.execute(
            """
            CREATE TABLE historical_chunks(
              chunk_id TEXT PRIMARY KEY,
              source_event_id TEXT NOT NULL,
              extraction_passes INTEGER NOT NULL DEFAULT 0,
              consecutive_zero_novel INTEGER NOT NULL DEFAULT 0,
              last_novel_count INTEGER NOT NULL DEFAULT 0,
              last_extracted_at TEXT,
              state TEXT NOT NULL DEFAULT 'PENDING_EXTRACTION'
            )
            """
        )
        self.con.execute(
            "INSERT INTO historical_chunks(chunk_id,source_event_id) VALUES('chunk-a','source-a')"
        )

    def tearDown(self):
        self.con.close()

    def row(self):
        return self.con.execute(
            "SELECT extraction_passes,consecutive_zero_novel,last_novel_count,state "
            "FROM historical_chunks WHERE chunk_id='chunk-a'"
        ).fetchone()

    def progress(self, extraction_pass, exhaustive, novel_count, *, source_event_id="source-a"):
        backfill._record_batch_progress(
            self.con,
            {
                "historical_source_event_id": source_event_id,
                "historical_chunk_id": "chunk-a",
                "extraction_pass": extraction_pass,
                "exhaustive": exhaustive,
                "deltas": [],
            },
            novel_count,
        )

    def test_nonexhaustive_zero_never_counts_toward_saturation(self):
        self.progress(1, False, 0)
        self.progress(2, False, 0)
        self.assertEqual(self.row(), (2, 0, 0, "PENDING_EXTRACTION"))

    def test_requires_two_explicit_exhaustive_zero_confirmations(self):
        self.progress(1, True, 0)
        self.assertEqual(self.row()[1:], (1, 0, "PENDING_EXTRACTION"))
        self.progress(2, True, 0)
        self.assertEqual(self.row()[1:], (2, 0, "SATURATED"))

    def test_nonexhaustive_or_novel_pass_resets_confirmation_streak(self):
        self.progress(1, True, 0)
        self.progress(2, False, 0)
        self.progress(3, True, 0)
        self.assertEqual(self.row()[1], 1)
        self.assertEqual(self.row()[3], "PENDING_EXTRACTION")

    def test_original_batch_identity_guard_is_preserved(self):
        self.progress(1, True, 0, source_event_id="foreign-source")
        self.assertEqual(self.row(), (0, 0, 0, "PENDING_EXTRACTION"))
        self.progress(2, True, 0)
        self.assertEqual(self.row(), (0, 0, 0, "PENDING_EXTRACTION"))

    def test_pass_ceiling_is_bounded_but_not_three(self):
        self.assertGreaterEqual(backfill.MAX_PASSES, MAX_EXHAUSTIVE_PASSES)
        self.assertGreater(backfill.MAX_PASSES, 3)

    def test_scheduler_never_hardcodes_exhaustive_true(self):
        source = (TOOLS / "free_swarm_backfill_scheduler.py").read_text(encoding="utf-8")
        self.assertNotIn('"exhaustive":true', source)
        self.assertIn('"exhaustive":<EXHAUSTIVE_BOOLEAN>', source)
        self.assertIn("two consecutive zero-novel passes", source)


if __name__ == "__main__":
    unittest.main()
