from __future__ import annotations

import hashlib
import json
import time
import uuid

import pytest

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


def _identity(db: UnifiedDB, query: str):
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    generation = db.entity_generation()
    turn_id = db.append_turn(session_id, "gabriel", "user", query)
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 1.0, "[]", None, "OPEN"),
    )
    return session_id, generation, turn_id, episode_id, causal_id


def _insert_replay(
    db: UnifiedDB,
    *,
    query: str,
    session_id: str,
    generation: int,
    turn_id: str,
    episode_id: str,
    causal_id: str,
    selected_ids: list[str],
    shadow_ids: list[str],
):
    db.db.execute(
        "INSERT INTO retrieval_episodes("
        "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
        "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
        "shadow_memory_ids,entry_keys,budget_chars,limit_items,chars_selected,status,ts"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            str(uuid.uuid4()), turn_id, episode_id, causal_id, session_id, "gabriel", generation,
            1, "SHADOW", hashlib.sha256(query.encode()).hexdigest(), "[]",
            json.dumps(selected_ids), json.dumps(shadow_ids), "[]", 12000, 24, 20,
            "PRESENT", time.time(),
        ),
    )


def _assert_replay_rejected_before_learning(
    db: UnifiedDB,
    *,
    query: str,
    session_id: str,
    generation: int,
    turn_id: str,
    episode_id: str,
    causal_id: str,
):
    organ = MicroClayRetrieval(db)
    calls = []

    def fake_learning(**kwargs):
        calls.append(kwargs)
        return {"eligible": 0, "applied": 0}

    organ.learn_from_verified_outcomes = fake_learning
    with pytest.raises(StaleGeneration, match="retrieval_route_contract"):
        organ.retrieve(
            query=query,
            user_id="gabriel",
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
    assert calls == []


def test_shadow_method_contamination_fails_before_learning(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        query = "sensor timeout dependency"
        sid, generation, turn_id, episode_id, causal_id = _identity(db, query)
        fact_id = db.add_memory(
            "fact", "sensor", "sensor timeout dependency observed",
            None, "gabriel", {"source": "test"},
        )
        method_id = db.add_memory(
            "framework", "diagnosis", "method record",
            None, "gabriel", {"source": "legacy"},
        )
        _insert_replay(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            selected_ids=[fact_id],
            shadow_ids=[method_id],
        )
        _assert_replay_rejected_before_learning(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
        )
    finally:
        db.close()


def test_shadow_control_contamination_fails_before_learning(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        query = "sensor timeout dependency"
        sid, generation, turn_id, episode_id, causal_id = _identity(db, query)
        fact_id = db.add_memory(
            "fact", "sensor", "sensor timeout dependency observed",
            None, "gabriel", {"source": "test"},
        )
        control_id = db.add_memory(
            "source_archive", "archive", "compressed source control record",
            None, "gabriel", {"source": "legacy-control"},
        )
        _insert_replay(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            selected_ids=[fact_id],
            shadow_ids=[control_id],
        )
        _assert_replay_rejected_before_learning(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
        )
    finally:
        db.close()


def test_missing_replay_memory_reference_fails_closed(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        query = "sensor timeout dependency"
        sid, generation, turn_id, episode_id, causal_id = _identity(db, query)
        _insert_replay(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            selected_ids=["missing-memory-id"],
            shadow_ids=[],
        )
        _assert_replay_rejected_before_learning(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
        )
    finally:
        db.close()


def test_private_other_user_selected_memory_fails_before_learning(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        query = "private memory replay"
        sid, generation, turn_id, episode_id, causal_id = _identity(db, query)
        db.ensure_user("andreas", "Andreas")
        private_id = db.add_memory(
            "fact", "private", "andreas-only evidence",
            None, "andreas", {"source": "test"},
        )
        _insert_replay(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            selected_ids=[private_id],
            shadow_ids=[],
        )
        _assert_replay_rejected_before_learning(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
        )
    finally:
        db.close()


def test_current_turn_shadow_memory_fails_before_learning(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        query = "current turn replay"
        sid, generation, turn_id, episode_id, causal_id = _identity(db, query)
        fact_id = db.add_memory(
            "fact", "history", "older evidence",
            None, "gabriel", {"source": "test"},
        )
        echo_id = db.add_memory(
            "fact", "echo", "same-turn evidence must not self-retrieve",
            turn_id, "gabriel", {"source": "test"},
        )
        _insert_replay(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            selected_ids=[fact_id],
            shadow_ids=[echo_id],
        )
        _assert_replay_rejected_before_learning(
            db,
            query=query,
            session_id=sid,
            generation=generation,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
        )
    finally:
        db.close()
