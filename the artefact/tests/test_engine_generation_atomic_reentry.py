from __future__ import annotations

import pytest

from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.workspace import Workspace


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel", "subject-gabriel")
    sid = db.ensure_session("gabriel", "clay-gabriel")
    return db, sid


def test_generation_fenced_append_rejects_stale_provider_response(tmp_path):
    db, sid = _db(tmp_path)
    try:
        user_turn = db.append_turn(sid, "gabriel", "user", "prompt")
        expected_generation = db.session_generation(sid)
        db.advance_entity_generation()

        with pytest.raises(StaleGeneration):
            db.append_turn(
                sid,
                "gabriel",
                "assistant",
                "stale provider response",
                expected_generation=expected_generation,
            )

        rows = db.all_turns(sid)
        assert [row["turn_id"] for row in rows] == [user_turn]
        assert [row["role"] for row in rows] == ["user"]
    finally:
        db.close()


def test_workspace_selection_and_assistant_append_roll_back_together_when_generation_is_stale(tmp_path):
    db, sid = _db(tmp_path)
    try:
        user_turn = db.append_turn(sid, "gabriel", "user", "prompt")
        workspace = Workspace(db)
        episode = workspace.open(sid, user_turn, "prompt", [])
        expected_generation = db.session_generation(sid)
        db.advance_entity_generation()

        with pytest.raises(StaleGeneration):
            with db.tx():
                workspace.select_in_tx(episode["episode_id"], "respond")
                db.append_turn_in_tx(
                    sid,
                    "gabriel",
                    "assistant",
                    "stale provider response",
                    expected_generation=expected_generation,
                )

        row = db.db.execute(
            "SELECT selected,state FROM workspace_episodes WHERE episode_id=?",
            (episode["episode_id"],),
        ).fetchone()
        assert row["selected"] is None
        assert row["state"] == "OPEN"
        assert [turn["role"] for turn in db.all_turns(sid)] == ["user"]
    finally:
        db.close()


def test_append_turn_in_tx_requires_existing_transaction(tmp_path):
    db, sid = _db(tmp_path)
    try:
        with pytest.raises(RuntimeError, match="requires active transaction"):
            db.append_turn_in_tx(sid, "gabriel", "assistant", "no transaction")
    finally:
        db.close()
