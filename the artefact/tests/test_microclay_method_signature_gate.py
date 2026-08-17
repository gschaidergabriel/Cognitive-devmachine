from __future__ import annotations

import inspect
import time
import uuid

from clayverse.microclay_methods import MicroClayMethodRetrieval
from clayverse.store import UnifiedDB


def _identity(db: UnifiedDB):
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    generation = db.entity_generation()
    turn_id = db.append_turn(session_id, "gabriel", "user", "sensor timeout dependency")
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 1.0, "[]", None, "OPEN"),
    )
    return session_id, generation, turn_id, episode_id, causal_id


def test_stage_b_api_has_explicit_structural_signature_input():
    """Raw prompt text must never be the authority that invents a structural signature."""
    parameters = inspect.signature(MicroClayMethodRetrieval.retrieve).parameters
    assert "problem_signature" in parameters
    assert parameters["problem_signature"].default is None


def test_stage_b_without_admitted_signature_fails_closed(tmp_path):
    """No signature means no method serving, while factual UNKNOWN remains untouched upstream."""
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        result = MicroClayMethodRetrieval(db).retrieve(
            query="sensor timeout dependency",
            problem_signature=None,
            user_id="gabriel",
            session_id=sid,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        assert result["items"] == []
        assert result["receipt"]["status"] == "SIGNATURE_REQUIRED"
        assert result["receipt"]["signature_source"] == "NONE"
        assert result["receipt"]["truth_authority"] is False
        assert result["receipt"]["effect_authority"] is False
    finally:
        db.close()
