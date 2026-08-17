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
        assert result["receipt"]["served"] is False
    finally:
        db.close()


def test_explicit_signature_not_raw_query_controls_shadow_selection():
    """Regression-only: known lexical-decoy class stays fenced after signature-gate repair."""

    row = {
        "memory_id": "method:1",
        "kind": "framework",
        "subject": "generic method",
        "provenance": "{}",
        "ts": 1.0,
    }

    class _Rows:
        def execute(self, *_args, **_kwargs):
            return [row]

    class _DB:
        db = _Rows()

        @staticmethod
        def assert_session_owner(_session_id, _user_id):
            return True

        @staticmethod
        def assert_live_generation(_session_id, _generation):
            return True

    organ = MicroClayMethodRetrieval(_DB())
    organ._method_record = lambda _row, user_id: {  # type: ignore[method-assign]
        "problem_signature": ["causal provenance repair"],
    }

    selected = organ.retrieve(
        query="banana wallpaper lexical decoy",
        problem_signature=["causal provenance repair"],
        user_id="gabriel",
        session_id="session:gabriel",
        turn_id="turn:1",
        episode_id="episode:1",
        causal_id="causal:1",
        generation=1,
    )
    assert [item["memory_id"] for item in selected["items"]] == ["method:1"]
    assert selected["receipt"]["signature_source"] == "EXPLICIT_SHADOW_INPUT"
    assert selected["receipt"]["served"] is False

    rejected = organ.retrieve(
        query="causal provenance repair",
        problem_signature=["visual layout composition"],
        user_id="gabriel",
        session_id="session:gabriel",
        turn_id="turn:1",
        episode_id="episode:1",
        causal_id="causal:1",
        generation=1,
    )
    assert rejected["items"] == []
    assert rejected["receipt"]["status"] == "METHOD_UNKNOWN"
