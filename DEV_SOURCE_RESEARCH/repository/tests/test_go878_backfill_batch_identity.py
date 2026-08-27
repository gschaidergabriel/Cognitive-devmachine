from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys

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


def _worker(text: str, serial: int) -> dict:
    return {
        "http_status": 200,
        "text": text,
        "text_sha256": bf.sha_text(text),
        "provider": "local-test",
        "model": "fixture",
        "role": "FALSIFIER",
        "worker_id": f"worker-{serial}",
        "worker_serial": serial,
        "ts": f"2026-08-25T00:01:{serial:02d}+00:00",
        "repo_head_at_prompt": "a" * 40,
    }


def _proposal(delta_id: str) -> dict:
    return {
        "delta_id": delta_id,
        "hypothesis": "A replay batch must not mutate a foreign causal chunk.",
        "mechanism": "Bind chunk, source event and monotonic pass before admission.",
        "target_files": ["tools/free_swarm_historical_backfill.py"],
        "patch_unified_diff": "",
        "test_commands": ["python3 -m pytest -q tests/test_go878_backfill_batch_identity.py"],
        "negative_test_commands": [],
        "benchmark_command": "",
        "metric": "foreign chunk progress mutations",
        "expected_direction": "zero",
        "baseline_needed": True,
        "falsifier": "Submit a foreign, replayed, future or oversized extraction envelope.",
        "risk": "Weak binding can silently suppress historical evidence by false saturation.",
        "ready_for_forge": False,
    }


def _seed_chunk(con: sqlite3.Connection, tmp_path: Path):
    run = tmp_path / "history"
    run.mkdir(parents=True)
    path = run / "workers.jsonl"
    path.write_text(
        json.dumps(_worker("old hypothesis with test benchmark and falsifier", 1)) + "\n",
        encoding="utf-8",
    )
    bf.ingest_artifact_history(con, tmp_path)
    chunk = con.execute(
        "SELECT chunk_id,source_event_id,extraction_passes,state FROM historical_chunks LIMIT 1"
    ).fetchone()
    assert chunk is not None
    return run, path, chunk


def _append_batch(path: Path, envelope: dict, serial: int) -> None:
    text = "ARCHITECTURE_DELTA_BATCH_JSON=" + json.dumps(envelope)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_worker(text, serial)) + "\n")


def test_foreign_source_event_cannot_mutate_chunk_or_mint_candidate(tmp_path: Path) -> None:
    con = _con()
    _, path, chunk = _seed_chunk(con, tmp_path)
    proposal = _proposal("foreign")
    proposal.update(
        historical_source_event_id="foreign-event",
        historical_chunk_id=chunk["chunk_id"],
        extraction_pass=1,
    )
    envelope = {
        "historical_source_event_id": "foreign-event",
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
        "exhaustive": True,
        "deltas": [proposal],
    }
    _append_batch(path, envelope, 2)
    stats = bf.ingest_artifact_history(con, tmp_path)
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?",
        (chunk["chunk_id"],),
    ).fetchone()
    assert stats["candidate_variants_added"] == 0
    assert con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 0
    assert current["extraction_passes"] == 0
    assert current["state"] == "PENDING_EXTRACTION"


def test_future_pass_cannot_skip_canonical_progress(tmp_path: Path) -> None:
    con = _con()
    _, _, chunk = _seed_chunk(con, tmp_path)
    bf._record_batch_progress(
        con,
        {
            "historical_source_event_id": chunk["source_event_id"],
            "historical_chunk_id": chunk["chunk_id"],
            "extraction_pass": 2,
            "exhaustive": True,
            "deltas": [],
        },
        0,
    )
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?",
        (chunk["chunk_id"],),
    ).fetchone()
    assert current["extraction_passes"] == 0
    assert current["state"] == "PENDING_EXTRACTION"


def test_replayed_pass_is_idempotently_rejected(tmp_path: Path) -> None:
    con = _con()
    _, _, chunk = _seed_chunk(con, tmp_path)
    first = {
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
        "exhaustive": False,
        "deltas": [],
    }
    bf._record_batch_progress(con, first, 0)
    bf._record_batch_progress(con, first, 0)
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?",
        (chunk["chunk_id"],),
    ).fetchone()
    assert current["extraction_passes"] == 1
    assert current["state"] == "PENDING_EXTRACTION"


def test_non_exhaustive_zero_novel_does_not_claim_saturation(tmp_path: Path) -> None:
    con = _con()
    _, _, chunk = _seed_chunk(con, tmp_path)
    first = {
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
        "exhaustive": False,
        "deltas": [],
    }
    bf._record_batch_progress(con, first, 0)
    second = dict(first, extraction_pass=2)
    bf._record_batch_progress(con, second, 0)
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?",
        (chunk["chunk_id"],),
    ).fetchone()
    assert current["extraction_passes"] == 2
    assert current["state"] == "PENDING_EXTRACTION"


def test_exact_exhaustive_zero_novel_second_pass_can_saturate(tmp_path: Path) -> None:
    con = _con()
    _, _, chunk = _seed_chunk(con, tmp_path)
    first = {
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
        "exhaustive": False,
        "deltas": [],
    }
    bf._record_batch_progress(con, first, 0)
    second = dict(first, extraction_pass=2, exhaustive=True)
    bf._record_batch_progress(con, second, 0)
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?",
        (chunk["chunk_id"],),
    ).fetchone()
    assert current["extraction_passes"] == 2
    assert current["state"] == "SATURATED"


def test_oversized_batch_cannot_advance_progress(tmp_path: Path) -> None:
    con = _con()
    _, _, chunk = _seed_chunk(con, tmp_path)
    bf._record_batch_progress(
        con,
        {
            "historical_source_event_id": chunk["source_event_id"],
            "historical_chunk_id": chunk["chunk_id"],
            "extraction_pass": 1,
            "exhaustive": True,
            "deltas": [{} for _ in range(bf.MAX_BATCH_DELTAS + 1)],
        },
        0,
    )
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?",
        (chunk["chunk_id"],),
    ).fetchone()
    assert current["extraction_passes"] == 0
    assert current["state"] == "PENDING_EXTRACTION"
