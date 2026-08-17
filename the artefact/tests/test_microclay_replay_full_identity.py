import uuid

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


def test_same_causal_replay_binds_full_request_identity_and_surfaces_bounds(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    try:
        session_id = "session:gabriel"
        turn_id = db.append_turn(session_id, "gabriel", "user", "alpha")
        episode_id = str(uuid.uuid4())
        db.db.execute(
            "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
            (episode_id, session_id, 1.0, turn_id, 0.5, "[]", None, "OPEN"),
        )
        db.add_memory("fact", "memory", "alpha memory", None, "gabriel", {"test": "full-identity"})
        retrieval = MicroClayRetrieval(db)
        request = {
            "query": "alpha",
            "user_id": "gabriel",
            "session_id": session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": str(uuid.uuid4()),
            "generation": db.entity_generation(),
            "limit": 2,
            "budget_chars": 512,
        }

        first = retrieval.retrieve(**request)
        assert first["receipt"]["limit_requested"] == 2
        assert first["receipt"]["budget_chars"] == 512

        replay = retrieval.retrieve(**request)
        assert replay["receipt"]["replayed"] is True
        assert replay["receipt"]["retrieval_id"] == first["receipt"]["retrieval_id"]
        assert replay["receipt"]["limit_requested"] == 2
        assert replay["receipt"]["budget_chars"] == 512

        drifted = [
            {"user_id": "andreas"},
            {"turn_id": str(uuid.uuid4())},
            {"episode_id": str(uuid.uuid4())},
            {"query": "beta"},
            {"limit": 1},
            {"budget_chars": 256},
        ]
        for change in drifted:
            with pytest.raises(StaleGeneration, match="retrieval_identity"):
                retrieval.retrieve(**{**request, **change})
    finally:
        db.close()
