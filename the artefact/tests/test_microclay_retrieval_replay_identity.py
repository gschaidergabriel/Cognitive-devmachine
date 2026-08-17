import hashlib
import sqlite3
import time
import uuid

import pytest

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


def _open_episode(db: UnifiedDB):
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "terminal:gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "alpha")
    episode_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    return session_id, turn_id, episode_id


def test_exact_retry_replays_but_budget_or_limit_change_fails_closed(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        session_id, turn_id, episode_id = _open_episode(db)
        memory_id = db.add_memory(
            "fact",
            "memory",
            "alpha memory",
            None,
            "gabriel",
            {"test": "replay-identity"},
        )
        retrieval = MicroClayRetrieval(db)
        request = {
            "query": "alpha",
            "user_id": "gabriel",
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": str(uuid.uuid4()),
            "generation": db.entity_generation(),
            "limit": 2,
            "budget_chars": 512,
        }

        first = retrieval.retrieve(**request)
        assert [item["memory_id"] for item in first["items"]] == [memory_id]
        assert first["receipt"]["limit_requested"] == 2
        assert first["receipt"]["budget_chars"] == 512

        replay = retrieval.retrieve(**request)
        assert replay["receipt"]["replayed"] is True
        assert replay["receipt"]["limit_requested"] == 2
        assert replay["receipt"]["budget_chars"] == 512
        assert [item["memory_id"] for item in replay["items"]] == [memory_id]
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_episodes WHERE causal_id=?",
            (request["causal_id"],),
        ).fetchone()[0] == 1

        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            retrieval.retrieve(**{**request, "budget_chars": 256})
        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            retrieval.retrieve(**{**request, "limit": 1})
        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            retrieval.retrieve(**{**request, "turn_id": str(uuid.uuid4())})
        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            retrieval.retrieve(**{**request, "episode_id": str(uuid.uuid4())})
    finally:
        db.close()


def test_invalid_retry_rejects_before_outcome_learning(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        session_id, turn_id, episode_id = _open_episode(db)
        db.add_memory("fact", "memory", "alpha memory", None, "gabriel", {"test": "learning-fence"})
        retrieval = MicroClayRetrieval(db)
        request = {
            "query": "alpha",
            "user_id": "gabriel",
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": str(uuid.uuid4()),
            "generation": db.entity_generation(),
            "limit": 2,
            "budget_chars": 512,
        }
        retrieval.retrieve(**request)

        calls = []
        retrieval.learn_from_verified_outcomes = lambda *, session_id, generation: (
            calls.append((session_id, generation)) or {"eligible": 0, "applied": 0}
        )
        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            retrieval.retrieve(**{**request, "budget_chars": 256})
        assert calls == []

        replay = retrieval.retrieve(**request)
        assert replay["receipt"]["replayed"] is True
        assert calls == [(session_id, request["generation"])]
    finally:
        db.close()


def test_schema6_receipt_migrates_without_inventing_missing_limit_identity(tmp_path):
    path = tmp_path / "schema6.db"
    raw = sqlite3.connect(path)
    try:
        raw.execute(
            "CREATE TABLE retrieval_episodes("
            "retrieval_id TEXT PRIMARY KEY,turn_id TEXT NOT NULL UNIQUE,"
            "episode_id TEXT NOT NULL UNIQUE,causal_id TEXT NOT NULL UNIQUE,"
            "session_id TEXT NOT NULL,user_id TEXT NOT NULL,generation INTEGER NOT NULL,"
            "policy_version INTEGER NOT NULL,mode TEXT NOT NULL,query_hash TEXT NOT NULL,"
            "query_token_hashes TEXT NOT NULL,selected_memory_ids TEXT NOT NULL,"
            "shadow_memory_ids TEXT NOT NULL,entry_keys TEXT NOT NULL,"
            "budget_chars INTEGER NOT NULL,chars_selected INTEGER NOT NULL,"
            "status TEXT NOT NULL,ts REAL NOT NULL)"
        )
        raw.execute(
            "INSERT INTO retrieval_episodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "legacy-retrieval",
                "legacy-turn",
                "legacy-episode",
                "legacy-causal",
                "session:gabriel",
                "gabriel",
                1,
                1,
                "SHADOW",
                hashlib.sha256(b"alpha").hexdigest(),
                "[]",
                "[]",
                "[]",
                "[]",
                512,
                0,
                "UNKNOWN",
                1.0,
            ),
        )
        raw.commit()
    finally:
        raw.close()

    db = UnifiedDB(path)
    try:
        db.ensure_user("gabriel", "Gabriel")
        session_id = db.ensure_session("gabriel", "terminal:gabriel")
        columns = {
            str(row[1]): int(row[3])
            for row in db.db.execute("PRAGMA table_info(retrieval_episodes)").fetchall()
        }
        assert columns["limit_requested"] == 0
        assert db.db.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()[0] == "7"
        assert db.db.execute(
            "SELECT limit_requested FROM retrieval_episodes WHERE retrieval_id='legacy-retrieval'"
        ).fetchone()[0] is None

        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            MicroClayRetrieval(db).retrieve(
                query="alpha",
                user_id="gabriel",
                session_id=session_id,
                turn_id="legacy-turn",
                episode_id="legacy-episode",
                causal_id="legacy-causal",
                generation=db.entity_generation(),
                limit=2,
                budget_chars=512,
            )
    finally:
        db.close()

    reopened = UnifiedDB(path)
    try:
        columns = [str(row[1]) for row in reopened.db.execute("PRAGMA table_info(retrieval_episodes)").fetchall()]
        assert columns.count("limit_requested") == 1
        assert reopened.db.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()[0] == "7"
        assert reopened.db.execute(
            "SELECT limit_requested FROM retrieval_episodes WHERE retrieval_id='legacy-retrieval'"
        ).fetchone()[0] is None
    finally:
        reopened.close()


def test_fresh_schema_uses_same_nullable_limit_shape_as_migrated_schema(tmp_path):
    db = UnifiedDB(tmp_path / "fresh.db")
    try:
        columns = {
            str(row[1]): int(row[3])
            for row in db.db.execute("PRAGMA table_info(retrieval_episodes)").fetchall()
        }
        assert columns["limit_requested"] == 0
    finally:
        db.close()
