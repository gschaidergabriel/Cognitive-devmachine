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

    def envelope(self, extraction_pass, exhaustive, *, source_event_id="source-a", deltas=None):
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

    def test_nonexhaustive_work_survives_old_three_pass_ceiling(self):
        self.progress(1, False, 8)
        self.progress(2, False, 8)
        self.progress(3, False, 0)
        passes, zeros, novel, state = self.row()
        self.assertEqual(passes, 3)
        self.assertEqual(zeros, 0)
        self.assertEqual(novel, 0)
        self.assertEqual(state, "PENDING_EXTRACTION")
        self.assertGreaterEqual(backfill.MAX_PASSES, MAX_EXHAUSTIVE_PASSES)
        self.assertGreater(backfill.MAX_PASSES, 3)

    def test_missing_exhaustive_signal_fails_closed(self):
        envelope = self.envelope(1, False)
        envelope.pop("exhaustive")
        backfill._record_batch_progress(self.con, envelope, 0)
        self.assertEqual(self.row(), (1, 0, 0, "PENDING_EXTRACTION"))

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

    def test_foreign_source_event_cannot_advance_progress(self):
        backfill._record_batch_progress(
            self.con,
            self.envelope(1, True, source_event_id="source-foreign"),
            0,
        )
        self.assertEqual(self.row(), (0, 0, 0, "PENDING_EXTRACTION"))

    def test_stale_or_future_pass_cannot_advance_progress(self):
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

    def test_both_active_sides_install_same_completion_law(self):
        scheduler = (TOOLS / "free_swarm_backfill_scheduler.py").read_text(encoding="utf-8")
        consumer = (TOOLS / "run_free_evidence_forge_backfill.py").read_text(encoding="utf-8")
        for source in (scheduler, consumer):
            self.assertIn("free_swarm_backfill_exhaustiveness_878", source)
            self.assertIn("install_exhaustiveness(historical_backfill_core)", source)
        self.assertNotIn('"exhaustive":true', scheduler)
        self.assertIn('"exhaustive":<true|false>', scheduler)


if __name__ == "__main__":
    unittest.main()
