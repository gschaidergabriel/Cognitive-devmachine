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


def _proposal(delta_id: str, *, ready: bool = False) -> dict:
    return {
        "delta_id": delta_id,
        "hypothesis": "A shared retry path can duplicate one causal result.",
        "mechanism": "Bind replay identity before durable admission.",
        "target_files": ["tools/example.py"],
        "patch_unified_diff": "" if not ready else "--- a/tools/example.py\n+++ b/tools/example.py\n@@ -1 +1 @@\n-old\n+new\n",
        "test_commands": ["python3 -m pytest tests/test_example.py -q"],
        "negative_test_commands": [],
        "benchmark_command": "",
        "metric": "duplicate durable rows",
        "expected_direction": "lower",
        "baseline_needed": True,
        "falsifier": "Replay the same event concurrently and count durable rows.",
        "risk": "A wrong identity could collapse genuinely distinct events.",
        "ready_for_forge": ready,
    }


def _worker(text: str, *, serial: int, head: str = "a" * 40) -> dict:
    return {
        "http_status": 200,
        "text": text,
        "text_sha256": bf.sha_text(text),
        "provider": "nvidia",
        "model": "test-model",
        "role": "FALSIFIER",
        "worker_id": f"worker-{serial}",
        "worker_serial": serial,
        "ts": f"2026-08-25T00:00:{serial:02d}+00:00",
        "repo_head_at_prompt": head,
    }


def test_all_history_is_scanned_and_execution_equivalent_deltas_are_deduped(tmp_path: Path) -> None:
    con = _con()
    run = tmp_path / "old" / "nested" / "run"
    run.mkdir(parents=True)
    p1 = _proposal("delta-one", ready=False)
    p2 = _proposal("delta-two", ready=False)
    lines = [
        _worker("analysis\nARCHITECTURE_DELTA_JSON=" + json.dumps(p1), serial=1),
        _worker("different prose\nARCHITECTURE_DELTA_JSON=" + json.dumps(p2), serial=2),
        _worker("A useful old free-form hypothesis with benchmark, test and falsifier but no machine marker.", serial=3),
    ]
    (run / "workers.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")

    stats = bf.ingest_artifact_history(con, tmp_path)
    assert stats["lines_seen"] == 3
    assert stats["successful_outputs"] == 3
    assert con.execute("SELECT COUNT(*) FROM historical_outputs").fetchone()[0] == 3

    # delta_id is volatile: the same execution-relevant proposal from two workers
    # is one candidate variant with two provenance observations.
    assert con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 1
    row = con.execute("SELECT state,ready,source_count FROM candidates").fetchone()
    assert row["state"] == "NEEDS_IMPLEMENTATION"
    assert row["ready"] == 0
    assert row["source_count"] >= 2

    # Every successful historical output is chunked for exhaustive re-extraction,
    # including outputs that never emitted the modern machine-readable marker.
    assert con.execute("SELECT COUNT(*) FROM historical_chunks").fetchone()[0] >= 3
    assert bf.backfill_metrics(con)["pending_extraction"] >= 3

    # Incremental replay is idempotent: no duplicate history after a second scan.
    again = bf.ingest_artifact_history(con, tmp_path)
    assert again["lines_seen"] == 0
    assert con.execute("SELECT COUNT(*) FROM historical_outputs").fetchone()[0] == 3


def test_batch_parser_extracts_all_deltas_and_saturates_after_zero_novel_pass(tmp_path: Path) -> None:
    con = _con()
    run = tmp_path / "active-old"
    run.mkdir(parents=True)

    original = _worker("old unstructured source with several ideas, tests, benchmark and falsifier", serial=1)
    (run / "workers.jsonl").write_text(json.dumps(original) + "\n", encoding="utf-8")
    bf.ingest_artifact_history(con, tmp_path)
    chunk = con.execute("SELECT chunk_id,source_event_id FROM historical_chunks LIMIT 1").fetchone()
    assert chunk is not None

    d1 = _proposal("historical-a", ready=False)
    d2 = dict(_proposal("historical-b", ready=False))
    d2["hypothesis"] = "A second materially different hypothesis exists in the same old output."
    for d in (d1, d2):
        d["historical_source_event_id"] = chunk["source_event_id"]
        d["historical_chunk_id"] = chunk["chunk_id"]
        d["extraction_pass"] = 1
    batch = {
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
        "exhaustive": True,
        "deltas": [d1, d2],
    }
    batch_text = "ARCHITECTURE_DELTA_BATCH_JSON=" + json.dumps(batch)
    proposals, envelopes = bf.explicit_deltas(batch_text)
    assert len(proposals) == 2
    assert len(envelopes) == 1

    # Feed a synthetic extraction worker into the same history. First pass creates
    # two variants and records progress on the original chunk.
    extractor1 = _worker(batch_text, serial=2)
    with (run / "workers.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(extractor1) + "\n")
    first = bf.ingest_artifact_history(con, tmp_path)
    assert first["candidate_variants_added"] == 2
    state = con.execute("SELECT extraction_passes,state,last_novel_count FROM historical_chunks WHERE chunk_id=?", (chunk["chunk_id"],)).fetchone()
    assert state["extraction_passes"] >= 1
    assert state["last_novel_count"] == 2

    # Same material on the next extraction pass is not new evidence. It must add
    # zero variants and saturate the chunk instead of minting duplicate deltas.
    batch2 = dict(batch)
    batch2["extraction_pass"] = 2
    batch2["deltas"] = [dict(d1, extraction_pass=2), dict(d2, extraction_pass=2)]
    text2 = "ARCHITECTURE_DELTA_BATCH_JSON=" + json.dumps(batch2)
    extractor2 = _worker(text2, serial=3)
    with (run / "workers.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(extractor2) + "\n")
    second = bf.ingest_artifact_history(con, tmp_path)
    assert second["candidate_variants_added"] == 0
    state2 = con.execute("SELECT extraction_passes,state,last_novel_count FROM historical_chunks WHERE chunk_id=?", (chunk["chunk_id"],)).fetchone()
    assert state2["extraction_passes"] >= 2
    assert state2["last_novel_count"] == 0
    assert state2["state"] == "SATURATED"


def test_multiple_single_markers_are_all_extracted() -> None:
    a = _proposal("a")
    b = _proposal("b")
    b["hypothesis"] = "Distinct hypothesis"
    text = (
        "ARCHITECTURE_DELTA_JSON=" + json.dumps(a) + "\n" +
        "ARCHITECTURE_DELTA_JSON=" + json.dumps(b)
    )
    proposals, _ = bf.explicit_deltas(text)
    assert len(proposals) == 2
