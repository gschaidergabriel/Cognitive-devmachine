from __future__ import annotations

import time
import uuid

import pytest

from clayverse.retrieval import WorldAssembler
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gabriel_session = db.ensure_session("gabriel", "clayverse-gabriel")
    andreas_session = db.ensure_session("andreas", "clayverse-andreas")
    return db, gabriel_session, andreas_session


def _episode(db, *, session_id, turn_id):
    episode_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    return episode_id


def _activate(db, *, session_id, user_id, turn_id, episode_id, causal_id):
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            session_id,
            user_id,
            turn_id,
            episode_id,
            causal_id,
            db.entity_generation(),
            "[]",
            None,
            None,
            0,
            time.time(),
        ),
    )


def test_active_identity_rejects_cross_session_episode_corruption(tmp_path):
    db, gabriel_session, andreas_session = _db(tmp_path)
    try:
        turn_id = db.append_turn(
            gabriel_session,
            "gabriel",
            "user",
            "identity corruption regression",
        )
        episode_id = _episode(db, session_id=andreas_session, turn_id=turn_id)
        _activate(
            db,
            session_id=gabriel_session,
            user_id="gabriel",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id="causal:episode-corrupt",
        )

        with pytest.raises(RuntimeError, match="active causal identity mismatch"):
            WorldAssembler(db)._active_identity(gabriel_session)
    finally:
        db.close()


def test_active_identity_rejects_cross_session_turn_corruption(tmp_path):
    db, gabriel_session, andreas_session = _db(tmp_path)
    try:
        turn_id = db.append_turn(
            andreas_session,
            "andreas",
            "user",
            "cross-session turn corruption",
        )
        episode_id = _episode(db, session_id=gabriel_session, turn_id=turn_id)
        _activate(
            db,
            session_id=gabriel_session,
            user_id="gabriel",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id="causal:turn-corrupt",
        )

        with pytest.raises(RuntimeError, match="active causal identity mismatch"):
            WorldAssembler(db)._active_identity(gabriel_session)
    finally:
        db.close()


def test_active_identity_rejects_active_user_corruption(tmp_path):
    db, gabriel_session, _ = _db(tmp_path)
    try:
        turn_id = db.append_turn(
            gabriel_session,
            "gabriel",
            "user",
            "active user corruption",
        )
        episode_id = _episode(db, session_id=gabriel_session, turn_id=turn_id)
        _activate(
            db,
            session_id=gabriel_session,
            user_id="andreas",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id="causal:user-corrupt",
        )

        with pytest.raises(RuntimeError, match="active causal identity mismatch"):
            WorldAssembler(db)._active_identity(gabriel_session)
    finally:
        db.close()


def test_active_identity_accepts_coherent_causal_identity(tmp_path):
    db, gabriel_session, _ = _db(tmp_path)
    try:
        turn_id = db.append_turn(
            gabriel_session,
            "gabriel",
            "user",
            "coherent identity control",
        )
        episode_id = _episode(db, session_id=gabriel_session, turn_id=turn_id)
        _activate(
            db,
            session_id=gabriel_session,
            user_id="gabriel",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id="causal:coherent",
        )

        identity = WorldAssembler(db)._active_identity(gabriel_session)
        assert identity == {
            "query": "coherent identity control",
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": "causal:coherent",
            "generation": db.entity_generation(),
        }
    finally:
        db.close()
