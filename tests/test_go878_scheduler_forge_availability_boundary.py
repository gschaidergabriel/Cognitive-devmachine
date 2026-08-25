from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import free_swarm_backfill_scheduler as scheduler


def _reset(db: Path) -> None:
    scheduler.FORGE_DB = db
    scheduler._cache_at = 0.0
    scheduler._cache = []
    scheduler._leases.clear()


def _valid_db(path: Path, *, pending: int = 0, extraction_passes: int = 0) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE candidates(candidate_hash TEXT PRIMARY KEY);
        CREATE TABLE candidate_sources(candidate_hash TEXT, source_event_id TEXT);
        CREATE TABLE historical_outputs(source_event_id TEXT PRIMARY KEY);
        CREATE TABLE historical_chunks(
          chunk_id TEXT PRIMARY KEY,
          source_event_id TEXT NOT NULL,
          state TEXT NOT NULL,
          extraction_passes INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    con.executemany(
        "INSERT INTO historical_chunks(chunk_id,source_event_id,state,extraction_passes) VALUES(?,?,?,?)",
        [(f"c{i}", f"e{i}", "PENDING_EXTRACTION", extraction_passes) for i in range(pending)],
    )
    con.commit()
    con.close()


def test_missing_forge_db_fails_closed_instead_of_becoming_empty_queue(tmp_path: Path) -> None:
    _reset(tmp_path / "missing.sqlite3")
    with pytest.raises(scheduler.ForgeBackfillUnavailable, match="FORGE_DB_MISSING_FAIL_CLOSED"):
        scheduler._packets()


def test_incomplete_forge_schema_fails_closed(tmp_path: Path) -> None:
    db = tmp_path / "forge.sqlite3"
    sqlite3.connect(db).execute("CREATE TABLE candidates(candidate_hash TEXT PRIMARY KEY)").connection.close()
    _reset(db)
    with pytest.raises(scheduler.ForgeBackfillUnavailable, match="FORGE_SCHEMA_INCOMPLETE_FAIL_CLOSED"):
        scheduler._packets()


def test_verified_empty_queue_allows_empty_result(tmp_path: Path) -> None:
    db = tmp_path / "forge.sqlite3"
    _valid_db(db, pending=0)
    _reset(db)
    assert scheduler._packets() == []


def test_pending_state_cannot_be_collapsed_to_empty_loader_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "forge.sqlite3"
    _valid_db(db, pending=1)
    _reset(db)
    monkeypatch.setattr(scheduler, "load_backfill_packets", lambda *a, **k: [])
    with pytest.raises(scheduler.ForgeBackfillUnavailable, match="FORGE_PACKET_LOAD_EMPTY_WITH_PENDING_FAIL_CLOSED"):
        scheduler._packets()


def test_pending_at_or_beyond_pass_ceiling_fails_closed_as_unschedulable(tmp_path: Path) -> None:
    db = tmp_path / "forge.sqlite3"
    _valid_db(db, pending=1, extraction_passes=int(scheduler.historical_backfill_core.MAX_PASSES))
    _reset(db)
    with pytest.raises(scheduler.ForgeBackfillUnavailable, match="FORGE_PENDING_UNSCHEDULABLE_FAIL_CLOSED"):
        scheduler._packets()


def test_unavailable_state_blocks_before_ordinary_prompt_is_constructed(tmp_path: Path) -> None:
    _reset(tmp_path / "missing.sqlite3")
    calls: list[int] = []

    class Base:
        @staticmethod
        def worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
            calls.append(serial)
            return "RAW"

    base = Base()
    scheduler.install(base)
    with pytest.raises(scheduler.ForgeBackfillUnavailable):
        base.worker_prompt("p", "r", "t", "s", 7)
    assert calls == []


def test_verified_empty_state_returns_ordinary_prompt(tmp_path: Path) -> None:
    db = tmp_path / "forge.sqlite3"
    _valid_db(db, pending=0)
    _reset(db)

    class Base:
        @staticmethod
        def worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
            return "RAW"

    base = Base()
    scheduler.install(base)
    assert base.worker_prompt("p", "r", "t", "s", 1) == "RAW"
