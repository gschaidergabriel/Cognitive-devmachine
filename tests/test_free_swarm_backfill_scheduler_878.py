from __future__ import annotations

import sqlite3
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_backfill_scheduler as scheduler


def _reset(monkeypatch, tmp_path: Path) -> Path:
    db = tmp_path / "forge.sqlite3"
    monkeypatch.setattr(scheduler, "FORGE_DB", db)
    monkeypatch.setattr(scheduler, "_cache_at", 0.0)
    monkeypatch.setattr(scheduler, "_cache", [])
    monkeypatch.setattr(scheduler, "_control_at", 0.0)
    monkeypatch.setattr(scheduler, "_control", {"state": "UNOBSERVED"})
    scheduler._leases.clear()
    return db


def _forge(db: Path, *, ready: int = 0, implementation: int = 0, pending: int = 0) -> None:
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE candidates(candidate_hash TEXT, concept_id TEXT, ready INTEGER NOT NULL, state TEXT NOT NULL)")
    con.executemany("INSERT INTO candidates(ready,state) VALUES(?,?)", [(1, "NEW")] * ready)
    con.executemany("INSERT INTO candidates(ready,state) VALUES(?,?)", [(0, "NEEDS_IMPLEMENTATION")] * implementation)
    con.execute(
        "CREATE TABLE historical_outputs(source_event_id TEXT PRIMARY KEY, provider TEXT, model TEXT, role TEXT, repo_head TEXT, text_sha256 TEXT)"
    )
    con.execute(
        "CREATE TABLE historical_chunks(chunk_id TEXT, source_event_id TEXT, chunk_index INTEGER, char_start INTEGER, char_end INTEGER, chunk_text TEXT, actionability REAL, state TEXT, extraction_passes INTEGER DEFAULT 0)"
    )
    con.executemany(
        "INSERT INTO historical_chunks(chunk_id,source_event_id,chunk_index,char_start,char_end,chunk_text,actionability,state,extraction_passes) VALUES(?,?,?,?,?,?,?,?,?)",
        [(f"c{i}", f"e{i}", 0, 0, 1, "x", 1.0, "PENDING_EXTRACTION", 0) for i in range(pending)],
    )
    con.execute("CREATE TABLE candidate_sources(source_event_id TEXT, candidate_hash TEXT)")
    con.commit()
    con.close()


def _installed_prompt() -> object:
    base = SimpleNamespace(worker_prompt=lambda protocol, role, task, state_context, serial: "ORIGINAL_TASK")
    scheduler.install(base)
    return base.worker_prompt


def test_missing_forge_db_holds_ordinary_research_fail_closed(monkeypatch, tmp_path: Path):
    _reset(monkeypatch, tmp_path)
    prompt = _installed_prompt()("p", "r", "task", "state", 0)
    assert "FREE-SWARM FORGE STATE HOLD" in prompt
    assert "NO_DELTA=FORGE_ALLOCATION_STATE_UNKNOWN" in prompt
    assert "ordinary raw research is NOT authorized" in prompt


def test_valid_empty_forge_allows_ordinary_research(monkeypatch, tmp_path: Path):
    db = _reset(monkeypatch, tmp_path)
    _forge(db)
    prompt = _installed_prompt()("p", "r", "task", "state", 0)
    assert prompt == "ORIGINAL_TASK"


def test_non_extraction_conversion_pressure_holds_raw_research_without_killing_fabric(monkeypatch, tmp_path: Path):
    db = _reset(monkeypatch, tmp_path)
    _forge(db, ready=40, implementation=24)
    prompt = _installed_prompt()("p", "r", "task", "state", 0)
    assert "FREE-SWARM CONVERSION BACKPRESSURE HOLD" in prompt
    assert "NO_DELTA=FORGE_CONVERSION_BACKPRESSURE" in prompt
    assert "Keep the shared 6000 process available" in prompt


def test_pending_extraction_repurposes_fabric_slot_instead_of_raw_research(monkeypatch, tmp_path: Path):
    db = _reset(monkeypatch, tmp_path)
    _forge(db, pending=1)
    packet = {
        "historical_source_event_id": "e0",
        "historical_chunk_id": "c0",
        "extraction_pass": 1,
        "chunk_text": "historical source",
    }
    monkeypatch.setattr(scheduler, "load_backfill_packets", lambda _db, limit: [packet])
    prompt = _installed_prompt()("p", "r", "task", "state", 0)
    assert "HISTORICAL FREE-SWARM BACKFILL OVERRIDE" in prompt
    assert '"historical_chunk_id":"c0"' in prompt
    assert "ARCHITECTURE_DELTA_BATCH_JSON=" in prompt
