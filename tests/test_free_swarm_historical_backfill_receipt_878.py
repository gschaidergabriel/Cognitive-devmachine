from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_historical_backfill as bf
import free_swarm_historical_backfill_receipt as receipt


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


def _insert_candidate(
    con: sqlite3.Connection,
    candidate_hash: str,
    *,
    state: str,
    ready: int,
    concept_id: str,
    variant_id: str,
) -> None:
    con.execute(
        """
        INSERT INTO candidates(
          candidate_hash,delta_id,provider,model,role,worker_sha,proposal_json,
          ready,state,ingested_at,repo_head,concept_id,variant_id,source_count,
          first_seen_at,last_seen_at,extraction_mode,priority
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            candidate_hash,
            candidate_hash,
            "fixture",
            "fixture",
            "FALSIFIER",
            "f" * 64,
            "{}",
            ready,
            state,
            "2026-08-25T00:00:00+00:00",
            "a" * 40,
            concept_id,
            variant_id,
            1,
            "2026-08-25T00:00:00+00:00",
            "2026-08-25T00:00:00+00:00",
            "fixture",
            1.0,
        ),
    )


def test_cutoff_identity_does_not_change_when_scanner_offset_advances(tmp_path: Path) -> None:
    con = _con()
    run = tmp_path / "old-run"
    run.mkdir()
    path = run / "workers.jsonl"
    path.write_text('{"http_status":200,"text":"x"}\n', encoding="utf-8")

    cutoff = receipt.artifact_cutoff(tmp_path)
    before_id = cutoff["cutoff_identity_sha256"]
    st = path.stat()
    con.execute(
        "INSERT INTO backfill_files(source_path,inode,byte_offset,file_size,updated_at) VALUES(?,?,?,?,?)",
        (str(path), int(st.st_ino), int(st.st_size), int(st.st_size), "now"),
    )
    con.commit()

    progress = receipt.cutoff_progress(con, tmp_path, cutoff)
    assert cutoff["cutoff_identity_sha256"] == before_id
    assert progress["caught_up_files"] == 1
    assert progress["uncaught_up_files"] == 0
    assert progress["replaced_or_truncated_files"] == 0


def test_cutoff_progress_allows_append_after_bound_cutoff(tmp_path: Path) -> None:
    con = _con()
    run = tmp_path / "active-run"
    run.mkdir()
    path = run / "workers.jsonl"
    path.write_text("one\n", encoding="utf-8")
    cutoff = receipt.artifact_cutoff(tmp_path)
    cutoff_size = path.stat().st_size
    inode = path.stat().st_ino

    with path.open("a", encoding="utf-8") as fh:
        fh.write("two\n")
    con.execute(
        "INSERT INTO backfill_files(source_path,inode,byte_offset,file_size,updated_at) VALUES(?,?,?,?,?)",
        (str(path), int(inode), int(path.stat().st_size), int(path.stat().st_size), "now"),
    )
    con.commit()

    progress = receipt.cutoff_progress(con, tmp_path, cutoff)
    assert cutoff["files"][0]["size_cutoff"] == cutoff_size
    assert progress["caught_up_files"] == 1
    assert progress["files"][0]["current_size"] > cutoff_size


def test_db_snapshot_exposes_required_878_receipt_metrics() -> None:
    con = _con()
    _insert_candidate(con, "ready", state="NEW", ready=1, concept_id="c1", variant_id="v1")
    _insert_candidate(
        con,
        "implement",
        state="NEEDS_IMPLEMENTATION",
        ready=0,
        concept_id="c2",
        variant_id="v2",
    )
    _insert_candidate(
        con,
        "duplicate",
        state="DUPLICATE_SUPERSEDED",
        ready=0,
        concept_id="c3",
        variant_id="v3",
    )
    con.execute(
        """
        INSERT INTO historical_outputs(
          source_event_id,worker_sha,source_path,line_no,provider,model,role,repo_head,
          text_sha256,text_chars,actionability,explicit_proposals,first_seen_at,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "event",
            "e" * 64,
            "/artifacts/run/workers.jsonl",
            1,
            "fixture",
            "fixture",
            "FALSIFIER",
            "a" * 40,
            "e" * 64,
            10,
            1.0,
            1,
            "now",
            "now",
        ),
    )
    con.execute(
        """
        INSERT INTO historical_chunks(
          chunk_id,source_event_id,chunk_index,char_start,char_end,chunk_text,
          actionability,state,extraction_passes,consecutive_zero_novel,last_novel_count
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        ("chunk", "event", 0, 0, 10, "fixture", 1.0, "SATURATED", 2, 1, 0),
    )
    con.execute(
        "INSERT INTO candidate_sources(candidate_hash,source_event_id,chunk_id,extractor_worker_sha,extraction_mode,seen_at) VALUES(?,?,?,?,?,?)",
        ("ready", "event", "", "e" * 64, "EXPLICIT_WORKER_DELTA", "now"),
    )
    con.execute(
        "INSERT INTO candidate_sources(candidate_hash,source_event_id,chunk_id,extractor_worker_sha,extraction_mode,seen_at) VALUES(?,?,?,?,?,?)",
        ("implement", "event", "chunk", "f" * 64, "HISTORICAL_BATCH", "now"),
    )
    con.commit()

    snap = receipt.db_snapshot(con)
    assert snap["schema_ready"] is True
    assert snap["historical_outputs"] == 1
    assert snap["explicit_deltas_recovered"] == 1
    assert snap["batch_deltas_recovered"] == 1
    assert snap["distinct_concepts"] == 3
    assert snap["distinct_execution_variants"] == 3
    assert snap["duplicates_superseded"] == 1
    assert snap["ready_backlog"] == 1
    assert snap["implementation_backlog"] == 1
    assert snap["remaining_pending_extraction"] == 0
    assert snap["max_passes_reached"] == 0
    assert snap["saturated_chunks"] == 1
    assert snap["non_saturated_chunks"] == 0


def test_classify_passes_only_fully_caught_up_and_saturated_state() -> None:
    status, blockers = receipt.classify(
        source={"dirty": False},
        cutoff={"file_count": 2},
        progress={
            "replaced_or_truncated_files": 0,
            "uncaught_up_files": 0,
        },
        db_after={
            "schema_ready": True,
            "historical_outputs": 10,
            "remaining_pending_extraction": 0,
            "max_passes_reached": 0,
            "non_saturated_chunks": 0,
        },
        rounds=[{"lines_seen": 50000}, {"lines_seen": 0}],
    )
    assert status == "PASS"
    assert blockers == []


def test_classify_blocks_pending_and_unresolved_max_passes() -> None:
    status, blockers = receipt.classify(
        source={"dirty": False},
        cutoff={"file_count": 1},
        progress={
            "replaced_or_truncated_files": 0,
            "uncaught_up_files": 0,
        },
        db_after={
            "schema_ready": True,
            "historical_outputs": 1,
            "remaining_pending_extraction": 2,
            "max_passes_reached": 1,
            "non_saturated_chunks": 3,
        },
        rounds=[{"lines_seen": 0}],
    )
    assert status == "BLOCKED"
    assert "PENDING_EXTRACTION_REMAINS" in blockers
    assert "MAX_PASSES_REACHED_UNRESOLVED" in blockers
    assert "NON_SATURATED_CHUNKS_REMAIN" in blockers
