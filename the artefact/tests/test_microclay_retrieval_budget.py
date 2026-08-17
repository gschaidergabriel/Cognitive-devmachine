import json
import sqlite3
import time
import uuid

import pytest

from clayverse.microclay_retrieval import MicroClayRetrieval, RetrievalCandidate
from clayverse.store import StaleGeneration, UnifiedDB


def _open_episode(db: UnifiedDB):
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "terminal:gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "alpha")
    episode_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (
            episode_id,
            session_id,
            time.time(),
            turn_id,
            0.5,
            "[]",
            None,
            "OPEN",
        ),
    )
    return session_id, turn_id, episode_id


def test_first_candidate_cannot_overrun_retrieval_budget(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        session_id, turn_id, episode_id = _open_episode(db)

        small_id = db.add_memory(
            "fact",
            "memory",
            "alpha beta gamma delta epsilon zeta eta theta iota kappa",
            None,
            "gabriel",
            {"test": "budget-fence-small"},
        )
        oversized_id = db.add_memory(
            "fact",
            "memory",
            ("alpha " * 60).strip(),
            None,
            "gabriel",
            {"test": "budget-fence-oversized"},
        )

        result = MicroClayRetrieval(db).retrieve(
            query="alpha",
            user_id="gabriel",
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=str(uuid.uuid4()),
            generation=db.entity_generation(),
            limit=24,
            budget_chars=256,
        )

        selected_ids = [item["memory_id"] for item in result["items"]]
        assert oversized_id not in selected_ids
        assert small_id in selected_ids
        assert result["receipt"]["chars_selected"] <= 256
        assert result["receipt"]["budget_chars"] == 256
        assert result["receipt"]["limit_requested"] == 24
        assert sum(len(item["value"]) for item in result["items"]) <= 256
    finally:
        db.close()


def test_shadow_counterfactual_uses_same_budget_as_serving(tmp_path, monkeypatch):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        session_id, turn_id, episode_id = _open_episode(db)
        small_a = db.add_memory(
            "fact",
            "memory",
            "a" * 100,
            None,
            "gabriel",
            {"test": "shadow-budget-small-a"},
        )
        small_b = db.add_memory(
            "fact",
            "memory",
            "b" * 100,
            None,
            "gabriel",
            {"test": "shadow-budget-small-b"},
        )
        oversized = db.add_memory(
            "fact",
            "memory",
            "x" * 300,
            None,
            "gabriel",
            {"test": "shadow-budget-oversized"},
        )

        now = time.time()
        candidates = {
            small_a: RetrievalCandidate(
                small_a, "fact", "memory", "a" * 100, now,
                {"test": "shadow-budget-small-a"}, 3.0, 2.0, ("kind:fact",),
            ),
            small_b: RetrievalCandidate(
                small_b, "fact", "memory", "b" * 100, now - 1,
                {"test": "shadow-budget-small-b"}, 2.0, 1.0, ("kind:fact",),
            ),
            oversized: RetrievalCandidate(
                oversized, "fact", "memory", "x" * 300, now - 2,
                {"test": "shadow-budget-oversized"}, 1.0, 4.0, ("kind:fact",),
            ),
        }

        retrieval = MicroClayRetrieval(db)

        def fixed_score(row, query_tokens, score_now, capitals):
            del query_tokens, score_now, capitals
            return candidates[str(row["memory_id"])]

        monkeypatch.setattr(retrieval, "_score_candidate", fixed_score)
        causal_id = str(uuid.uuid4())
        result = retrieval.retrieve(
            query="alpha",
            user_id="gabriel",
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=db.entity_generation(),
            limit=2,
            budget_chars=256,
        )

        selected_ids = [item["memory_id"] for item in result["items"]]
        assert selected_ids == [small_a, small_b]
        assert result["receipt"]["chars_selected"] == 200
        assert result["receipt"]["shadow_differs"] is False

        episode = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids,limit_requested,budget_chars "
            "FROM retrieval_episodes WHERE causal_id=?",
            (causal_id,),
        ).fetchone()
        assert json.loads(episode["selected_memory_ids"]) == selected_ids
        assert json.loads(episode["shadow_memory_ids"]) == selected_ids
        assert int(episode["limit_requested"]) == 2
        assert int(episode["budget_chars"]) == 256
    finally:
        db.close()


def test_replay_requires_exact_budget_and_limit_identity(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        session_id, turn_id, episode_id = _open_episode(db)
        large_id = db.add_memory(
            "fact",
            "memory",
            ("alpha " * 60).strip(),
            None,
            "gabriel",
            {"test": "replay-budget-large"},
        )
        retrieval = MicroClayRetrieval(db)
        causal_id = str(uuid.uuid4())
        request = dict(
            query="alpha",
            user_id="gabriel",
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=db.entity_generation(),
            limit=2,
            budget_chars=512,
        )

        first = retrieval.retrieve(**request)
        assert [item["memory_id"] for item in first["items"]] == [large_id]
        assert first["receipt"]["chars_selected"] > 256
        assert first["receipt"]["budget_chars"] == 512
        assert first["receipt"]["limit_requested"] == 2

        exact_retry = retrieval.retrieve(**request)
        assert exact_retry["receipt"]["replayed"] is True
        assert [item["memory_id"] for item in exact_retry["items"]] == [large_id]

        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            retrieval.retrieve(**{**request, "budget_chars": 256})
        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            retrieval.retrieve(**{**request, "limit": 1})
    finally:
        db.close()


def test_schema6_retrieval_table_migrates_limit_identity_column(tmp_path):
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
        raw.commit()
    finally:
        raw.close()

    db = UnifiedDB(path)
    try:
        columns = {
            str(row[1]) for row in db.db.execute("PRAGMA table_info(retrieval_episodes)").fetchall()
        }
        assert "limit_requested" in columns
        schema_version = db.db.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()[0]
        assert schema_version == "7"
    finally:
        db.close()
