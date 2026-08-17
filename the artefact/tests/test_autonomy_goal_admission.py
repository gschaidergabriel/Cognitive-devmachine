from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController, AutonomyStateError
from clayverse.autonomy_context import admit_explicit_goal_from_turn
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "terminal-gabriel")
    db.ensure_session("andreas", "terminal-andreas")
    return db


def _hook_turn(db: UnifiedDB, prompt: str, *, user_id: str = "gabriel") -> str:
    generation = db.entity_generation()
    return db.append_turn(
        f"session:{user_id}",
        user_id,
        "user",
        prompt,
        provenance={
            "source": "claude-hook:UserPromptSubmit",
            "session_generation": generation,
            "entity_generation": generation,
            "causal_id": f"test:{user_id}:{generation}",
        },
    )


def test_ordinary_prompt_does_not_mint_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    prompt = "please improve the artifact"
    turn_id = _hook_turn(db, prompt)
    assert admit_explicit_goal_from_turn(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=turn_id,
        prompt=prompt,
    ) is None
    assert controller.snapshot(user_id="gabriel")["goals"] == []


def test_explicit_goal_is_exact_turn_bound_and_sequential_replay_deduplicated(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    prompt = "/goal ship the verified artifact"
    turn_id = _hook_turn(db, prompt)
    first = admit_explicit_goal_from_turn(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=turn_id,
        prompt=prompt,
    )
    second = admit_explicit_goal_from_turn(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=turn_id,
        prompt=prompt,
    )
    assert first is not None and second is not None
    assert first["goal_id"] == second["goal_id"]
    assert first["source_turn_id"] == turn_id
    assert first["objective"] == prompt
    assert first["completion_contract"] == {"mode": "user_ack", "required_capability": None}
    assert len(controller.snapshot(user_id="gabriel")["goals"]) == 1


def test_empty_explicit_goal_is_rejected(tmp_path):
    db = _db(tmp_path)
    prompt = "/goal   "
    turn_id = _hook_turn(db, prompt)
    with pytest.raises(AutonomyStateError, match="objective is empty"):
        admit_explicit_goal_from_turn(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            source_turn_id=turn_id,
            prompt=prompt,
        )


def test_forged_non_hook_turn_cannot_mint_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    prompt = "/goal forged objective"
    turn_id = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        prompt,
        provenance={
            "source": "synthetic-test",
            "session_generation": db.entity_generation(),
            "entity_generation": db.entity_generation(),
        },
    )
    with pytest.raises(PermissionError, match="live admitted UserPromptSubmit"):
        admit_explicit_goal_from_turn(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            source_turn_id=turn_id,
            prompt=prompt,
        )
    assert controller.snapshot(user_id="gabriel")["goals"] == []


def test_stale_hook_turn_cannot_mint_goal_after_generation_advance(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    prompt = "/goal stale objective"
    turn_id = _hook_turn(db, prompt)
    db.advance_entity_generation()
    with pytest.raises(PermissionError, match="live admitted UserPromptSubmit"):
        admit_explicit_goal_from_turn(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            source_turn_id=turn_id,
            prompt=prompt,
        )
    assert controller.snapshot(user_id="gabriel")["goals"] == []


def test_prompt_bytes_must_match_canonical_source_turn(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    turn_id = _hook_turn(db, "/goal canonical objective")
    with pytest.raises(PermissionError, match="exact canonical owner user turn"):
        admit_explicit_goal_from_turn(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            source_turn_id=turn_id,
            prompt="/goal substituted objective",
        )
    assert controller.snapshot(user_id="gabriel")["goals"] == []
