from pathlib import Path
import sqlite3
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_historical_backfill as backfill


class BackfillCoreExhaustiveness878Tests(unittest.TestCase):
    def setUp(self):
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

    @staticmethod
    def envelope(extraction_pass, exhaustive, *, source_event_id="source-a", deltas=None):
        return {
            "historical_source_event_id": source_event_id,
            "historical_chunk_id": "chunk-a",
            "extraction_pass": extraction_pass,
            "exhaustive": exhaustive,
            "deltas": [] if deltas is None else deltas,
        }

    def progress(self, extraction_pass, exhaustive, novel_count):
        backfill._record_batch_progress(
            self.con,
            self.envelope(extraction_pass, exhaustive),
            novel_count,
        )

    def test_nonexhaustive_zero_does_not_count_toward_saturation(self):
        self.progress(1, False, 8)
        self.progress(2, False, 0)
        self.progress(3, False, 0)
        self.assertEqual(self.row(), (3, 0, 0, "PENDING_EXTRACTION"))

    def test_missing_exhaustive_signal_fails_closed(self):
        envelope = self.envelope(1, False)
        envelope.pop("exhaustive")
        backfill._record_batch_progress(self.con, envelope, 0)
        self.assertEqual(self.row(), (1, 0, 0, "PENDING_EXTRACTION"))

    def test_requires_two_consecutive_explicit_exhaustive_zero_confirmations(self):
        self.progress(1, True, 4)
        self.progress(2, True, 0)
        self.assertEqual(self.row(), (2, 1, 0, "PENDING_EXTRACTION"))
        self.progress(3, True, 0)
        self.assertEqual(self.row(), (3, 2, 0, "SATURATED"))

    def test_nonexhaustive_or_novel_pass_resets_confirmation_streak(self):
        self.progress(1, True, 0)
        self.progress(2, False, 0)
        self.assertEqual(self.row()[1], 0)
        self.progress(3, True, 0)
        self.progress(4, True, 2)
        self.assertEqual(self.row()[1], 0)
        self.assertEqual(self.row()[3], "PENDING_EXTRACTION")

    def test_foreign_stale_and_future_bindings_cannot_advance_progress(self):
        backfill._record_batch_progress(
            self.con,
            self.envelope(1, True, source_event_id="source-foreign"),
            0,
        )
        self.assertEqual(self.row(), (0, 0, 0, "PENDING_EXTRACTION"))
        self.progress(1, True, 0)
        before = self.row()
        backfill._record_batch_progress(self.con, self.envelope(1, True), 0)
        self.assertEqual(self.row(), before)
        backfill._record_batch_progress(self.con, self.envelope(3, True), 0)
        self.assertEqual(self.row(), before)

    def test_missing_or_oversized_delta_list_cannot_advance_progress(self):
        missing = self.envelope(1, True)
        missing.pop("deltas")
        backfill._record_batch_progress(self.con, missing, 0)
        self.assertEqual(self.row(), (0, 0, 0, "PENDING_EXTRACTION"))
        oversized = self.envelope(
            1,
            True,
            deltas=[{} for _ in range(int(backfill.MAX_BATCH_DELTAS) + 1)],
        )
        backfill._record_batch_progress(self.con, oversized, 0)
        self.assertEqual(self.row(), (0, 0, 0, "PENDING_EXTRACTION"))

    def test_pass_ceiling_is_bounded_but_not_semantic_saturation(self):
        self.assertGreaterEqual(backfill.MAX_PASSES, 64)
        self.con.execute(
            "UPDATE historical_chunks SET extraction_passes=? WHERE chunk_id='chunk-a'",
            (backfill.MAX_PASSES - 1,),
        )
        backfill._record_batch_progress(
            self.con,
            self.envelope(backfill.MAX_PASSES, False),
            0,
        )
        self.assertEqual(self.row()[3], "MAX_PASSES_REACHED")

    def test_scheduler_never_hardcodes_exhaustive_true(self):
        source = (TOOLS / "free_swarm_backfill_scheduler.py").read_text(encoding="utf-8")
        self.assertNotIn('"exhaustive":true', source)
        self.assertIn("exhaustive MUST be false", source)
        self.assertIn("Set exhaustive=true only after", source)


if __name__ == "__main__":
    unittest.main()
