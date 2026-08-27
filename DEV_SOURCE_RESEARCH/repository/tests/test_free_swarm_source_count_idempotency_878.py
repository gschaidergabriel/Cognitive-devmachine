from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_historical_backfill as bf


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE candidates(
          candidate_hash TEXT PRIMARY KEY,
          delta_id TEXT, provider TEXT, model TEXT, role TEXT,
          worker_sha TEXT, proposal_json TEXT NOT NULL,
          ready INTEGER NOT NULL DEFAULT 0,
          state TEXT NOT NULL DEFAULT 'NEW',
          ingested_at TEXT NOT NULL, evaluated_at TEXT,
          last_reason TEXT, repo_head TEXT
        );
        """
    )
    bf.ensure_schema(con)
    return con


def _proposal() -> dict:
    return {
        "delta_id": "source-count-idempotency",
        "hypothesis": "Exact replay of one provenance observation must not create another evidence vote.",
        "mechanism": "Increment source_count only when the candidate_sources primary key admits a new provenance link.",
        "target_files": ["tools/free_swarm_historical_backfill.py"],
        "patch_unified_diff": "",
        "test_commands": ["python3 -m pytest tests/test_free_swarm_source_count_idempotency_878.py -q"],
        "negative_test_commands": [],
        "benchmark_command": "",
        "metric": "source_count after identical replay",
        "expected_direction": "unchanged",
        "baseline_needed": True,
        "falsifier": "Insert the same candidate/source tuple twice and observe source_count > 1.",
        "risk": "Under-counting genuinely distinct provenance links.",
        "ready_for_forge": False,
    }


def _row() -> dict:
    text = "ARCHITECTURE_DELTA_JSON={}"
    return {
        "text": text,
        "text_sha256": bf.sha_text(text),
        "provider": "local-test",
        "model": "deterministic",
        "role": "FALSIFIER",
        "repo_head_at_prompt": "a" * 40,
    }


def test_identical_provenance_replay_does_not_inflate_source_count() -> None:
    con = _con()
    proposal = _proposal()
    row = _row()

    added1, candidate_hash = bf._insert_candidate(
        con,
        obj=proposal,
        row=row,
        source_event_id="event-1",
        chunk_id="",
        extraction_mode="EXPLICIT_WORKER_DELTA",
    )
    added2, candidate_hash2 = bf._insert_candidate(
        con,
        obj=proposal,
        row=row,
        source_event_id="event-1",
        chunk_id="",
        extraction_mode="EXPLICIT_WORKER_DELTA",
    )

    assert added1 is True
    assert added2 is False
    assert candidate_hash2 == candidate_hash
    assert con.execute(
        "SELECT source_count FROM candidates WHERE candidate_hash=?", (candidate_hash,)
    ).fetchone()[0] == 1
    assert con.execute(
        "SELECT COUNT(*) FROM candidate_sources WHERE candidate_hash=?", (candidate_hash,)
    ).fetchone()[0] == 1


def test_distinct_provenance_link_increments_source_count_once() -> None:
    con = _con()
    proposal = _proposal()
    row = _row()

    _, candidate_hash = bf._insert_candidate(
        con,
        obj=proposal,
        row=row,
        source_event_id="event-1",
        chunk_id="",
        extraction_mode="EXPLICIT_WORKER_DELTA",
    )
    bf._insert_candidate(
        con,
        obj=proposal,
        row=row,
        source_event_id="event-2",
        chunk_id="",
        extraction_mode="EXPLICIT_WORKER_DELTA",
    )
    bf._insert_candidate(
        con,
        obj=proposal,
        row=row,
        source_event_id="event-2",
        chunk_id="",
        extraction_mode="EXPLICIT_WORKER_DELTA",
    )

    assert con.execute(
        "SELECT source_count FROM candidates WHERE candidate_hash=?", (candidate_hash,)
    ).fetchone()[0] == 2
    assert con.execute(
        "SELECT COUNT(*) FROM candidate_sources WHERE candidate_hash=?", (candidate_hash,)
    ).fetchone()[0] == 2
