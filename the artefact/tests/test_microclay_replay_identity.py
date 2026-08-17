import json
import sqlite3
import uuid

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


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


def _retrieve(organ, *, session_id, turn_id, episode_id, causal_id, budget_chars=1200, limit=24):
    return organ.retrieve(
        query="alpha",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=organ.db.entity_generation(),
        budget_chars=budget_chars,
        limit=limit,
    )


def test_exact_replay_preserves_receipt_but_budget_or_limit_drift_fails_closed(tmp_path):
    db = _db(tmp_path)
    try:
        db.add_memory(
            "fact", "memory", ("alpha " * 60).strip(), None, "gabriel", {"test": "replay-identity"}
        )
        session_id, turn_id, episode_id = _episode(db)
        causal_id = str(uuid.uuid4())
        organ = MicroClayRetrieval(db)

        first = _retrieve(
            organ,
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            budget_chars=1200,
            limit=24,
        )
        assert first["receipt"]["chars_selected"] > 256

        replay = _retrieve(
            organ,
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            budget_chars=1200,
            limit=24,
        )
        assert replay["receipt"]["replayed"] is True
        assert replay["receipt"]["retrieval_id"] == first["receipt"]["retrieval_id"]

        for changed_budget in (256, 2000):
            with pytest.raises(StaleGeneration, match="retrieval_identity"):
                _retrieve(
                    organ,
                    session_id=session_id,
                    turn_id=turn_id,
                    episode_id=episode_id,
                    causal_id=causal_id,
                    budget_chars=changed_budget,
                    limit=24,
                )

        for changed_limit in (1, 25):
            with pytest.raises(StaleGeneration, match="retrieval_identity"):
                _retrieve(
                    organ,
                    session_id=session_id,
                    turn_id=turn_id,
                    episode_id=episode_id,
                    causal_id=causal_id,
                    budget_chars=1200,
                    limit=changed_limit,
                )
    finally:
        db.close()


def test_legacy_unknown_limit_fails_closed_and_schema_migration_is_restart_idempotent(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    IdentityRouter(db, {})
    try:
        db.add_memory("fact", "memory", "alpha memory", None, "gabriel", {"test": "legacy-limit"})
        session_id, turn_id, episode_id = _episode(db)
        causal_id = str(uuid.uuid4())
        organ = MicroClayRetrieval(db)
        _retrieve(
            organ,
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            budget_chars=1200,
            limit=24,
        )
        row = db.db.execute(
            "SELECT budget_chars,limit_items FROM retrieval_episodes WHERE causal_id=?",
            (causal_id,),
        ).fetchone()
        assert int(row["budget_chars"]) == 1200
        assert int(row["limit_items"]) == 24

        db.db.execute("UPDATE retrieval_episodes SET limit_items=NULL WHERE causal_id=?", (causal_id,))
        with pytest.raises(StaleGeneration, match="retrieval_identity"):
            _retrieve(
                organ,
                session_id=session_id,
                turn_id=turn_id,
                episode_id=episode_id,
                causal_id=causal_id,
                budget_chars=1200,
                limit=24,
            )
    finally:
        db.close()

    reopened = UnifiedDB(path)
    try:
        columns = {str(row["name"]) for row in reopened.db.execute("PRAGMA table_info(retrieval_episodes)")}
        assert "limit_items" in columns
        assert reopened.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "7"
        assert reopened.db.execute("SELECT limit_items FROM retrieval_episodes WHERE causal_id=?", (causal_id,)).fetchone()[0] is None
    finally:
        reopened.close()


def test_pre_v7_retrieval_table_without_limit_column_migrates_exactly_once(tmp_path):
    path = tmp_path / "legacy-v6.db"
    raw = sqlite3.connect(path)
    try:
        raw.executescript(
            """
            CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT INTO meta(key,value) VALUES('schema_version','6');
            CREATE TABLE retrieval_episodes(
                retrieval_id TEXT PRIMARY KEY,
                turn_id TEXT NOT NULL UNIQUE,
                episode_id TEXT NOT NULL UNIQUE,
                causal_id TEXT NOT NULL UNIQUE,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                policy_version INTEGER NOT NULL,
                mode TEXT NOT NULL CHECK(mode IN ('SHADOW','ACTIVE')),
                query_hash TEXT NOT NULL,
                query_token_hashes TEXT NOT NULL,
                selected_memory_ids TEXT NOT NULL,
                shadow_memory_ids TEXT NOT NULL,
                entry_keys TEXT NOT NULL,
                budget_chars INTEGER NOT NULL,
                chars_selected INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('PRESENT','UNKNOWN')),
                ts REAL NOT NULL
            );
            """
        )
    finally:
        raw.close()

    for _ in range(2):
        migrated = UnifiedDB(path)
        try:
            columns = [str(row["name"]) for row in migrated.db.execute("PRAGMA table_info(retrieval_episodes)")]
            assert columns.count("limit_items") == 1
            assert migrated.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "7"
        finally:
            migrated.close()
