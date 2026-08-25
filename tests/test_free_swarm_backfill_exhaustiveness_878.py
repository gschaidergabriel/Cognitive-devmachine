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


class BackfillExhaustiveness878Tests(unittest.TestCase):
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

    def envelope(self, extraction_pass, exhaustive, *, source_event_id="source-a", deltas=None):
        return {
            "historical_chunk_id": "chunk-a",
            "historical_source_event_id": source_event_id,
            "extraction_pass": extraction_pass,
            "exhaustive": exhaustive,
            "deltas": [] if deltas is None else deltas,
        }

    def progress(self, extraction_pass, exhaustive, novel_count, **kwargs):
        backfill._record_batch_progress(
            self.con,
            self.envelope(extraction_pass, exhaustive, **kwargs),
            novel_count,
        )

    def test_nonexhaustive_zero_never_counts_toward_saturation(self):
        self.progress(1, False, 0)
        self.progress(2, False, 0)
        self.progress(3, False, 0)
        self.assertEqual(self.row(), (3, 0, 0, "PENDING_EXTRACTION"))

    def test_requires_two_consecutive_explicit_exhaustive_zero_confirmations(self):
        self.progress(1, True, 4)
        self.progress(2, True, 0)
        self.assertEqual(self.row()[1:], (1, 0, "PENDING_EXTRACTION"))
        self.progress(3, True, 0)
        self.assertEqual(self.row()[1:], (2, 0, "SATURATED"))

    def test_nonexhaustive_pass_resets_confirmation_streak(self):
        self.progress(1, True, 0)
        self.progress(2, False, 0)
        self.progress(3, True, 0)
        self.assertEqual(self.row()[1], 1)
        self.assertEqual(self.row()[3], "PENDING_EXTRACTION")

    def test_wrong_source_event_cannot_advance_chunk(self):
        before = self.row()
        self.progress(1, True, 0, source_event_id="source-foreign")
        self.assertEqual(self.row(), before)

    def test_future_or_skipped_pass_cannot_advance_chunk(self):
        before = self.row()
        self.progress(2, True, 0)
        self.assertEqual(self.row(), before)

    def test_oversized_batch_cannot_advance_chunk(self):
        before = self.row()
        self.progress(1, True, 0, deltas=[{} for _ in range(backfill.MAX_BATCH_DELTAS + 1)])
        self.assertEqual(self.row(), before)

    def test_ceiling_is_visible_stall_not_semantic_saturation(self):
        self.assertGreaterEqual(backfill.MAX_PASSES, MAX_EXHAUSTIVE_PASSES)
        self.assertGreater(backfill.MAX_PASSES, 3)
        self.con.execute(
            "UPDATE historical_chunks SET extraction_passes=? WHERE chunk_id='chunk-a'",
            (backfill.MAX_PASSES - 1,),
        )
        self.progress(backfill.MAX_PASSES, False, 0)
        self.assertEqual(self.row()[3], "MAX_PASSES_REACHED")

    def test_scheduler_has_dynamic_exhaustive_signal_and_confirmation_law(self):
        source = (TOOLS / "free_swarm_backfill_scheduler.py").read_text(encoding="utf-8")
        self.assertNotIn('"exhaustive":true', source)
        self.assertIn('"exhaustive":<true|false>', source)
        self.assertIn("two consecutive zero-novel passes", source)


if __name__ == "__main__":
    unittest.main()
