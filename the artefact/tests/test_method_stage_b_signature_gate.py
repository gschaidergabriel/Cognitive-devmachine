from __future__ import annotations

import time
import uuid

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
