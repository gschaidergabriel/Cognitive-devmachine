from __future__ import annotations

import time
import uuid

import pytest

from clayverse.method_stage_b import StageBMethodRetrieval
from clayverse.store import UnifiedDB


def test_stage_b_without_explicit_structural_signature_fails_closed(tmp_path):
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

    result = StageBMethodRetrieval(db).retrieve(
        query="recover state provenance",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature=None,
    )

    assert result["methods"] == []
    assert result["counterevidence"] == []
    assert result["problem_signature"] is None
    assert result["receipt"]["status"] == "SIGNATURE_REQUIRED"
    assert result["receipt"]["triggered"] is False
    assert result["receipt"]["problem_signature_sha256"] is None
    assert result["receipt"]["signature_source"] == "NONE"
    assert result["receipt"]["factual_status_unchanged"] == "UNKNOWN"
    assert result["receipt"]["truth_authority"] is False
    assert result["receipt"]["effect_authority"] is False


def test_stage_b_rejects_cross_session_turn_episode_corruption(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gabriel_session = db.ensure_session("gabriel", "clayverse-gabriel")
    andreas_session = db.ensure_session("andreas", "clayverse-andreas")

    foreign_turn = db.append_turn(andreas_session, "andreas", "user", "foreign turn")
    foreign_episode = "foreign:" + uuid.uuid4().hex
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (foreign_episode, andreas_session, time.time(), foreign_turn, 0.5, "[]", None, "OPEN"),
    )

    causal_id = "causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    # The schema's independent foreign keys allow individually valid IDs from another
    # session to be wired into Gabriel's active row. Stage-B must detect the relational
    # mismatch instead of treating referential validity as canonical identity.
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (gabriel_session, "gabriel", foreign_turn, foreign_episode, causal_id, generation, "[]", None, None, 0, time.time()),
    )

    with pytest.raises(RuntimeError, match="Stage-B retrieval identity mismatch"):
        StageBMethodRetrieval(db).retrieve(
            query="recover state provenance",
            user_id="gabriel",
            session_id=gabriel_session,
            turn_id=foreign_turn,
            episode_id=foreign_episode,
            causal_id=causal_id,
            generation=generation,
            evidence_status="UNKNOWN",
            problem_signature=None,
        )
