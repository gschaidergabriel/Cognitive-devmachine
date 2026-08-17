from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from clayverse.autonomy import AutonomyController, AutonomyStateError, GoalBudget
from clayverse.autonomy_context import admit_explicit_goal_from_turn
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def _canonical_hook_source(path, prompt: str) -> str:
    db = UnifiedDB(path)
    try:
        IdentityRouter(db, {})
        generation = db.entity_generation()
        return db.append_turn(
            "session:gabriel",
            "gabriel",
            "user",
            prompt,
            provenance={
                "source": "claude-hook:UserPromptSubmit",
                "claude_session_id": "atomic-goal-test",
                "session_generation": generation,
                "entity_generation": generation,
                "causal_id": "atomic-goal-source",
            },
        )
    finally:
        db.close()


def test_concurrent_explicit_goal_replay_mints_exactly_one_goal(tmp_path):
    path = tmp_path / "unified.db"
    prompt = "/goal atomically adopt this exact canonical source turn"
    source_turn_id = _canonical_hook_source(path, prompt)
    barrier = threading.Barrier(2)

    def worker() -> str:
        db = UnifiedDB(path)
        try:
            barrier.wait(timeout=10)
            goal = admit_explicit_goal_from_turn(
                db,
                user_id="gabriel",
                session_id="session:gabriel",
                source_turn_id=source_turn_id,
                prompt=prompt,
            )
            assert goal is not None
            return goal["goal_id"]
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        goal_ids = list(pool.map(lambda _index: worker(), range(2)))

    assert len(set(goal_ids)) == 1
    check = UnifiedDB(path)
    try:
        goals = AutonomyController(check).snapshot(user_id="gabriel")["goals"]
        assert len(goals) == 1
        assert goals[0]["goal_id"] == goal_ids[0]
        assert goals[0]["source_turn_id"] == source_turn_id
    finally:
        check.close()


def test_same_source_turn_replay_preserves_existing_goal_state(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    IdentityRouter(db, {})
    source = db.append_turn(
        "session:gabriel", "gabriel", "user", "Durable source identity"
    )
    controller = AutonomyController(db)
    first = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
        priority=70,
        budget=GoalBudget(max_steps=5, max_retries_per_step=1, max_effects=0),
    )
    controller.block_goal(first["goal_id"], "external dependency")

    replay = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
        priority=70,
        budget=GoalBudget(max_steps=5, max_retries_per_step=1, max_effects=0),
    )

    assert replay["goal_id"] == first["goal_id"]
    assert replay["status"] == "BLOCKED"
    assert replay["blocked_reason"] == "external dependency"
    assert len(controller.snapshot(user_id="gabriel")["goals"]) == 1
    db.close()


def test_same_source_turn_cannot_be_reinterpreted_with_different_contract(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    IdentityRouter(db, {})
    source = db.append_turn(
        "session:gabriel", "gabriel", "user", "One source, one goal contract"
    )
    controller = AutonomyController(db)
    controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
        priority=50,
    )

    with pytest.raises(AutonomyStateError, match="different goal contract"):
        controller.create_goal_from_turn(
            "gabriel",
            "session:gabriel",
            source,
            completion_mode="user_ack",
            priority=51,
        )
    assert len(controller.snapshot(user_id="gabriel")["goals"]) == 1
    db.close()


def test_duplicate_source_turns_in_persisted_state_fail_closed(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    IdentityRouter(db, {})
    first_source = db.append_turn("session:gabriel", "gabriel", "user", "first")
    second_source = db.append_turn("session:gabriel", "gabriel", "user", "second")
    controller = AutonomyController(db)
    first = controller.create_goal_from_turn(
        "gabriel", "session:gabriel", first_source, completion_mode="user_ack"
    )
    second = controller.create_goal_from_turn(
        "gabriel", "session:gabriel", second_source, completion_mode="user_ack"
    )

    raw = db.db.execute(
        "SELECT value FROM meta WHERE key='autonomy_state_v1'"
    ).fetchone()[0]
    state = controller._loads(raw)
    state["goals"][second["goal_id"]]["source_turn_id"] = first["source_turn_id"]
    db.db.execute(
        "UPDATE meta SET value=? WHERE key='autonomy_state_v1'",
        (controller._dumps(state),),
    )

    with pytest.raises(AutonomyStateError, match="multiple goals share one source turn"):
        controller.snapshot()
    db.close()
