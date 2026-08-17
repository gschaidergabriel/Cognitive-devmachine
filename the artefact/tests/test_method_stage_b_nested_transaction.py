from __future__ import annotations

import time
import uuid

import pytest

from clayverse.method_stage_b import StageBMethodRetrieval
from clayverse.store import UnifiedDB


def _active_turn(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "recover state provenance")
    episode_id = "active:" + uuid.uuid4().hex
    causal_id = "causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )
    return db, session_id, turn_id, episode_id, causal_id, generation


def _request(stage_b, *, session_id, turn_id, episode_id, causal_id, generation):
    return stage_b.retrieve(
        query="recover state provenance",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        resource_refs=["repo:clay"],
        problem_signature=None,
        limit=4,
        budget_chars=2048,
    )


def test_stage_b_receipt_joins_outer_transaction_and_rolls_back(tmp_path):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)
    stage_b = StageBMethodRetrieval(db)
    memory_id = stage_b._receipt_memory_id(causal_id)

    with pytest.raises(RuntimeError, match="rollback sentinel"):
        with db.tx():
            result = _request(
                stage_b,
                session_id=session_id,
                turn_id=turn_id,
                episode_id=episode_id,
                causal_id=causal_id,
                generation=generation,
            )
            assert result["receipt"]["status"] == "SIGNATURE_REQUIRED"
            assert db.db.execute(
                "SELECT COUNT(*) FROM durable_memory WHERE memory_id=?", (memory_id,)
            ).fetchone()[0] == 1
            raise RuntimeError("rollback sentinel")

    assert db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE memory_id=?", (memory_id,)
    ).fetchone()[0] == 0


def test_stage_b_standalone_receipt_still_commits_and_replays(tmp_path):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)
    stage_b = StageBMethodRetrieval(db)
    first = _request(
        stage_b,
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
    )
    replay = _request(
        stage_b,
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
    )

    assert first["receipt"]["replayed"] is False
    assert replay["receipt"]["replayed"] is True
    assert db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind='method_receipt'"
    ).fetchone()[0] == 1
