from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.autonomy_dispatch import (
    DISPATCH_PREFIX,
    AutonomyDispatchError,
    consume_dispatch_prompt,
    reserve_dispatch,
)
from clayverse.autonomy_planner import AutonomyPlanner
from clayverse.identity import IdentityRouter
from clayverse.store import LeaseConflict, StaleGeneration, UnifiedDB


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _goal(db):
    controller = AutonomyController(db)
    source = db.append_turn(
        "session:gabriel", "gabriel", "user", "Continue this goal when detached and idle."
    )
    return controller.create_goal_from_turn(
        "gabriel", "session:gabriel", source, completion_mode="user_ack"
    )


def test_one_shot_dispatch_consumes_exact_nonce_once(db):
    goal = _goal(db)
    prepared = AutonomyPlanner(db).prepare_next("gabriel")
    dispatch = reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal["goal_id"],
        step_id=prepared["step_id"],
        instruction=prepared["prompt"],
    )

    claimed = consume_dispatch_prompt(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        prompt=dispatch.terminal_prompt,
    )
    assert claimed is not None
    assert claimed.goal_id == goal["goal_id"]
    assert claimed.step_id == prepared["step_id"]
    assert claimed.instruction == prepared["prompt"]
    assert claimed.generation == db.entity_generation()

    with pytest.raises(AutonomyDispatchError, match="lease missing"):
        consume_dispatch_prompt(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            prompt=dispatch.terminal_prompt,
        )


def test_human_text_does_not_consume_dispatch_but_reserved_wrong_nonce_fails_closed(db):
    goal = _goal(db)
    prepared = AutonomyPlanner(db).prepare_next("gabriel")
    dispatch = reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal["goal_id"],
        step_id=prepared["step_id"],
        instruction=prepared["prompt"],
    )

    assert consume_dispatch_prompt(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        prompt="ordinary human text",
    ) is None
    with pytest.raises(AutonomyDispatchError, match="nonce mismatch"):
        consume_dispatch_prompt(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            prompt=f"{DISPATCH_PREFIX}{'0' * 32}",
        )

    claimed = consume_dispatch_prompt(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        prompt=dispatch.terminal_prompt,
    )
    assert claimed is not None


def test_malformed_reserved_dispatch_prompt_fails_closed(db):
    with pytest.raises(AutonomyDispatchError, match="prompt malformed"):
        consume_dispatch_prompt(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            prompt=f"{DISPATCH_PREFIX}not-a-valid-nonce",
        )


def test_expired_reserved_dispatch_prompt_fails_closed(db):
    goal = _goal(db)
    prepared = AutonomyPlanner(db).prepare_next("gabriel")
    dispatch = reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal["goal_id"],
        step_id=prepared["step_id"],
        instruction=prepared["prompt"],
    )
    with db.tx() as tx:
        tx.execute(
            "UPDATE leases SET expires_at=0 WHERE resource=?",
            ("autonomy-dispatch:session:gabriel",),
        )

    with pytest.raises(AutonomyDispatchError, match="lease expired"):
        consume_dispatch_prompt(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            prompt=dispatch.terminal_prompt,
        )


def test_second_live_dispatch_reservation_conflicts_even_for_same_step(db):
    goal = _goal(db)
    prepared = AutonomyPlanner(db).prepare_next("gabriel")
    reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal["goal_id"],
        step_id=prepared["step_id"],
        instruction=prepared["prompt"],
    )
    with pytest.raises(LeaseConflict):
        reserve_dispatch(
            db,
            user_id="gabriel",
            goal_id=goal["goal_id"],
            step_id=prepared["step_id"],
            instruction=prepared["prompt"],
        )


def test_dispatch_fails_if_goal_step_changes_before_consume(db):
    goal = _goal(db)
    planner = AutonomyPlanner(db)
    prepared = planner.prepare_next("gabriel")
    dispatch = reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal["goal_id"],
        step_id=prepared["step_id"],
        instruction=prepared["prompt"],
    )
    planner.controller.record_step_failure(
        goal["goal_id"], prepared["step_id"], "changed-after-reservation"
    )

    with pytest.raises(AutonomyDispatchError, match="no longer matches"):
        consume_dispatch_prompt(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            prompt=dispatch.terminal_prompt,
        )


def test_generation_change_fences_dispatch_claim(db):
    goal = _goal(db)
    prepared = AutonomyPlanner(db).prepare_next("gabriel")
    dispatch = reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal["goal_id"],
        step_id=prepared["step_id"],
        instruction=prepared["prompt"],
    )
    db.advance_entity_generation()

    with pytest.raises(StaleGeneration):
        consume_dispatch_prompt(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            prompt=dispatch.terminal_prompt,
        )


def test_unadmitted_step_cannot_receive_dispatch_lease(db):
    goal = _goal(db)
    controller = AutonomyController(db)
    step = controller.propose_step(
        goal["goal_id"],
        "reason",
        "AUTONOMY_PLANNER_DECISION: still only proposed",
    )
    with pytest.raises(AutonomyDispatchError, match="not one live admitted"):
        reserve_dispatch(
            db,
            user_id="gabriel",
            goal_id=goal["goal_id"],
            step_id=step["step_id"],
            instruction="not yet dispatchable",
        )
