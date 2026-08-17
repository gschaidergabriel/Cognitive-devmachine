from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _setup(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db, AutonomyController(db), TurnLifecycle(
        db, "gabriel", "session:gabriel", entityos_bridge=None
    )


def _goal_and_effect_step(db, controller, target: str):
    source = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Keep pursuing this goal, but never duplicate a real effect on retry.",
    )
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Execute exactly one bounded effect for this logical step",
        effect={"capability": "state.noop", "target": target, "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    return goal, step


def test_final_effect_from_prior_attempt_blocks_blind_retry_execution(tmp_path):
    db, controller, lifecycle = _setup(tmp_path)
    goal, step = _goal_and_effect_step(
        db, controller, "autonomy-retry-request-identity"
    )

    lifecycle.begin_autonomous(
        "Attempt one for the admitted logical effect step",
        goal["goal_id"],
        step["step_id"],
    )
    first = lifecycle.request_effect(
        "state.noop", "autonomy-retry-request-identity", None
    )
    assert first["verified"] is True
    lifecycle.abort_autonomous(
        "consumer_result_lost_before_controller_reconciliation",
        goal["goal_id"],
        step["step_id"],
    )

    controller.record_step_failure(
        goal["goal_id"],
        step["step_id"],
        "consumer_result_lost_before_controller_reconciliation",
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    lifecycle.begin_autonomous(
        "Retry of the same logical effect step must reconcile prior final evidence",
        goal["goal_id"],
        step["step_id"],
    )

    with pytest.raises(
        RuntimeError,
        match="prior final autonomous effect requires controller reconciliation before retry",
    ):
        lifecycle.request_effect(
            "state.noop", "autonomy-retry-request-identity", None
        )

    count = db.db.execute(
        "SELECT COUNT(*) FROM effects WHERE user_id=? AND capability=?",
        ("gabriel", "state.noop"),
    ).fetchone()[0]
    assert count == 1


def test_replay_fence_is_step_scoped_not_goal_wide(tmp_path):
    db, controller, lifecycle = _setup(tmp_path)
    goal, first_step = _goal_and_effect_step(db, controller, "first-step")

    lifecycle.begin_autonomous(
        "Execute first logical effect step", goal["goal_id"], first_step["step_id"]
    )
    first = lifecycle.request_effect("state.noop", "first-step", None)
    controller.record_effect_result(
        goal["goal_id"], first_step["step_id"], first["effect_id"]
    )
    lifecycle.complete_autonomous(
        "First step recorded", goal["goal_id"], first_step["step_id"]
    )

    second_step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "A distinct logical step may execute its own effect",
        effect={"capability": "state.noop", "target": "second-step", "argv": None},
    )
    controller.admit_step(goal["goal_id"], second_step["step_id"])
    lifecycle.begin_autonomous(
        "Execute second logical effect step", goal["goal_id"], second_step["step_id"]
    )
    second = lifecycle.request_effect("state.noop", "second-step", None)

    assert second["verified"] is True
    count = db.db.execute(
        "SELECT COUNT(*) FROM effects WHERE user_id=? AND capability=?",
        ("gabriel", "state.noop"),
    ).fetchone()[0]
    assert count == 2
