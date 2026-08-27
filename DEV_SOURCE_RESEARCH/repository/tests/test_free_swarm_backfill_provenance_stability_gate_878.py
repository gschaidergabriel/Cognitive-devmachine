from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from free_swarm_backfill_provenance import (
    reconcile_candidate_source_counts,
    replay_stable_source_event_identity_available,
)


def _con(*, stable_line_checkpoint: bool) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE candidates(
          candidate_hash TEXT PRIMARY KEY,
          source_count INTEGER NOT NULL DEFAULT 1
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
    if stable_line_checkpoint:
        con.execute(
            "CREATE TABLE backfill_files(source_path TEXT PRIMARY KEY, inode INTEGER, byte_offset INTEGER NOT NULL DEFAULT 0, file_size INTEGER NOT NULL DEFAULT 0, line_no INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL)"
        )
    else:
        con.execute(
            "CREATE TABLE backfill_files(source_path TEXT PRIMARY KEY, inode INTEGER, byte_offset INTEGER NOT NULL DEFAULT 0, file_size INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL)"
        )
    return con


def _seed(con: sqlite3.Connection) -> None:
    con.execute("INSERT INTO candidates(candidate_hash,source_count) VALUES('c1',9)")
    con.executemany(
        "INSERT INTO candidate_sources(candidate_hash,source_event_id,chunk_id,extractor_worker_sha,extraction_mode,seen_at) VALUES(?,?,?,?,?,?)",
        [
            ("c1", "event-a", "chunk-1", "w1", "HISTORICAL_BATCH", "t1"),
            ("c1", "event-a", "chunk-2", "w2", "HISTORICAL_BATCH", "t2"),
            ("c1", "event-b", "", "w2", "EXPLICIT_WORKER_DELTA", "t3"),
        ],
    )
    con.commit()


def test_offset_only_schema_clamps_unprovable_multi_source_weight() -> None:
    con = _con(stable_line_checkpoint=False)
    _seed(con)
    assert replay_stable_source_event_identity_available(con) is False
    assert reconcile_candidate_source_counts(con) == 1
    assert con.execute("SELECT source_count FROM candidates WHERE candidate_hash='c1'").fetchone()[0] == 1
    assert reconcile_candidate_source_counts(con) == 0


def test_absolute_line_schema_allows_distinct_event_reconciliation() -> None:
    con = _con(stable_line_checkpoint=True)
    _seed(con)
    assert replay_stable_source_event_identity_available(con) is True
    assert reconcile_candidate_source_counts(con) == 1
    assert con.execute("SELECT source_count FROM candidates WHERE candidate_hash='c1'").fetchone()[0] == 2
    assert reconcile_candidate_source_counts(con) == 0
