from __future__ import annotations

import time
import uuid

import pytest

from clayverse.retrieval import WorldAssembler
from clayverse.store import UnifiedDB


def test_active_identity_rejects_cross_session_episode_corruption(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        db.ensure_user("andreas", "Andreas")
        gabriel_session = db.ensure_session("gabriel", "clayverse-gabriel")
        andreas_session = db.ensure_session("andreas", "clayverse-andreas")
        turn_id = db.append_turn(
            gabriel_session,
            "gabriel",
            "user",
            "identity corruption regression",
        )
        episode_id = str(uuid.uuid4())
        db.db.execute(
            "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (episode_id, andreas_session, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
        )
        db.db.execute(
            "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                gabriel_session,
                "gabriel",
                turn_id,
                episode_id,
                "causal:corrupt",
                db.entity_generation(),
                "[]",
                None,
                None,
                0,
                time.time(),
            ),
        )

        with pytest.raises(RuntimeError, match="active causal identity mismatch"):
            WorldAssembler(db)._active_identity(gabriel_session)
    finally:
        db.close()
