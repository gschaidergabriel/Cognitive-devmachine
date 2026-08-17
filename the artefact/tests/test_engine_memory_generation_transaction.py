from __future__ import annotations

import pytest

from clayverse.engine import ClayVerseEngine
from clayverse.store import UnifiedDB


def _engine(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    engine = ClayVerseEngine(db, {"subject-gabriel": "gabriel"})
    return db, engine, "session:gabriel"


def test_turn_derived_memory_runs_inside_begin_generation_transaction(tmp_path, monkeypatch):
    db, engine, sid = _engine(tmp_path)
    observed = []
    original_extract = engine.memory.extract_explicit
    original_compact = engine.memory.compact

    def extract(turn_id, user_id, content):
        observed.append(("extract", db.db.in_transaction))
        return original_extract(turn_id, user_id, content)

    def compact(session_id):
        observed.append(("compact", db.db.in_transaction))
        return original_compact(session_id)

    monkeypatch.setattr(engine.memory, "extract_explicit", extract)
    monkeypatch.setattr(engine.memory, "compact", compact)

    try:
        turn_id, workspace, generation, causal_id = engine._begin_engine_turn(
            "gabriel", sid, "FACT: generation-fenced", []
        )

        assert observed == [("extract", True), ("compact", True)]
        assert generation == db.entity_generation() == db.session_generation(sid)
        memory = db.db.execute(
            "SELECT kind,value,source_turn_id FROM durable_memory WHERE source_turn_id=?",
            (turn_id,),
        ).fetchone()
        assert dict(memory) == {
            "kind": "fact",
            "value": "generation-fenced",
            "source_turn_id": turn_id,
        }
        active = db.db.execute(
            "SELECT turn_id,episode_id,causal_id,generation FROM active_turns WHERE session_id=?",
            (sid,),
        ).fetchone()
        assert active["turn_id"] == turn_id
        assert active["episode_id"] == workspace["episode_id"]
        assert active["causal_id"] == causal_id
        assert int(active["generation"]) == generation
    finally:
        db.close()


def test_memory_failure_rolls_back_entire_admitted_turn_spine(tmp_path, monkeypatch):
    db, engine, sid = _engine(tmp_path)

    def fail_after_memory_write(turn_id, user_id, content):
        assert db.db.in_transaction is True
        db.add_memory(
            "fact",
            user_id,
            "must-roll-back",
            turn_id,
            user_id,
            {"extractor": "test"},
        )
        raise RuntimeError("memory-failure")

    monkeypatch.setattr(engine.memory, "extract_explicit", fail_after_memory_write)

    try:
        with pytest.raises(RuntimeError, match="memory-failure"):
            engine._begin_engine_turn("gabriel", sid, "FACT: must-roll-back", [])

        assert db.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM workspace_episodes").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
        assert db.entity_generation() == db.session_generation(sid) == 1
    finally:
        db.close()
