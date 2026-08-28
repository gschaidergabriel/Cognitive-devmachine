from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from free_swarm_backfill_provenance import reconcile_candidate_source_counts


class FreeSwarmBackfillProvenance878Tests(unittest.TestCase):
    def connection(self) -> sqlite3.Connection:
        con = sqlite3.connect(":memory:")
        con.executescript(
            """
            CREATE TABLE candidates(
              candidate_hash TEXT PRIMARY KEY,
              source_count INTEGER
            );
            CREATE TABLE candidate_sources(
              candidate_hash TEXT NOT NULL,
              source_event_id TEXT NOT NULL,
              chunk_id TEXT NOT NULL DEFAULT '',
              extractor_worker_sha TEXT NOT NULL DEFAULT '',
              extraction_mode TEXT NOT NULL,
              seen_at TEXT NOT NULL,
              PRIMARY KEY(candidate_hash,source_event_id,chunk_id,extractor_worker_sha,extraction_mode)
            );
            """
        )
        return con

    def test_same_source_execution_across_chunks_counts_once(self):
        con = self.connection()
        con.execute("INSERT INTO candidates(candidate_hash,source_count) VALUES('c1',9)")
        con.executemany(
            "INSERT INTO candidate_sources(candidate_hash,source_event_id,chunk_id,extractor_worker_sha,extraction_mode,seen_at) VALUES(?,?,?,?,?,?)",
            [
                ("c1", "event-a", "chunk-1", "worker-a", "HISTORICAL_BATCH", "t1"),
                ("c1", "event-a", "chunk-2", "worker-a", "HISTORICAL_BATCH", "t2"),
                ("c1", "event-a", "chunk-2", "worker-b", "HISTORICAL_BATCH", "t3"),
                ("c1", "event-b", "", "worker-b", "EXPLICIT_WORKER_DELTA", "t4"),
            ],
        )
        self.assertEqual(reconcile_candidate_source_counts(con), 1)
        self.assertEqual(con.execute("SELECT source_count FROM candidates WHERE candidate_hash='c1'").fetchone()[0], 2)
        con.close()

    def test_reconciliation_is_idempotent(self):
        con = self.connection()
        con.execute("INSERT INTO candidates(candidate_hash,source_count) VALUES('c1',7)")
        con.execute(
            "INSERT INTO candidate_sources(candidate_hash,source_event_id,extraction_mode,seen_at) VALUES('c1','event-a','EXPLICIT_WORKER_DELTA','t1')"
        )
        self.assertEqual(reconcile_candidate_source_counts(con), 1)
        self.assertEqual(reconcile_candidate_source_counts(con), 0)
        self.assertEqual(con.execute("SELECT source_count FROM candidates WHERE candidate_hash='c1'").fetchone()[0], 1)
        con.close()

    def test_legacy_candidate_without_source_links_is_not_reinterpreted(self):
        con = self.connection()
        con.execute("INSERT INTO candidates(candidate_hash,source_count) VALUES('legacy',3)")
        self.assertEqual(reconcile_candidate_source_counts(con), 0)
        self.assertEqual(con.execute("SELECT source_count FROM candidates WHERE candidate_hash='legacy'").fetchone()[0], 3)
        con.close()


if __name__ == "__main__":
    unittest.main()
