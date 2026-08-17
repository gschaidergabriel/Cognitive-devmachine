import uuid

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.terminal_gateway import _runtime_ready


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _episode(db):
    session_id = "session:gabriel"
    turn_id = db.append_turn(session_id, "gabriel", "user", "alpha")
    episode_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, 1.0, turn_id, 0.5, "[]", None, "OPEN"),
    )
    return session_id, turn_id, episode_id


def test_rejected_replay_identity_cannot_trigger_online_learning(tmp_path):
    db = _db(tmp_path)
    try:
        db.add_memory("fact", "memory", "alpha memory", None, "gabriel", {"test": "identity-before-learning"})
        session_id, turn_id, episode_id = _episode(db)
        causal_id = str(uuid.uuid4())
        organ = MicroClayRetrieval(db)
        calls = []

        def fake_learning(**kwargs):
            calls.append(kwargs)
            return {"eligible": 0, "applied": 0}

        organ.learn_from_verified_outcomes = fake_learning
        request = {
            "query": "alpha",
            "user_id": "gabriel",
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": db.entity_generation(),
            "budget_chars": 1200,
            "limit": 24,
        }
        organ.retrieve(**request)
        assert len(calls) == 1

        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            organ.retrieve(**{**request, "budget_chars": 256})
        assert len(calls) == 1
    finally:
        db.close()


def test_schema7_migration_remains_runtime_ready(tmp_path):
    db = _db(tmp_path)
    try:
        assert db.db.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()[0] == "7"
        assert _runtime_ready(db) is True
    finally:
        db.close()
