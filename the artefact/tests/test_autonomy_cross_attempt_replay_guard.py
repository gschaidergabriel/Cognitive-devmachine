from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _admitted_effect_step(db, controller, *, target: str):
    source = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        f"Execute one bounded effect for {target}.",
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


def test_final_effect_from_prior_attempt_must_be_reconciled_before_retry_execution(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    target = "autonomy-retry-request-identity"
    goal, step = _admitted_effect_step(db, controller, target=target)

    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=None)
    lifecycle.begin_autonomous(
        "Attempt one for the admitted logical effect step",
        goal["goal_id"],
        step["step_id"],
    )
    first = lifecycle.request_effect("state.noop", target, None)
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

    with pytest.raises(TurnLifecycleError, match="reconcil|prior|already.*effect|retry"):
        lifecycle.request_effect("state.noop", target, None)

    count = db.db.execute(
        "SELECT COUNT(*) FROM effects WHERE user_id=? AND capability=?",
        ("gabriel", "state.noop"),
    ).fetchone()[0]
    assert count == 1


def test_same_episode_idempotent_effect_recovery_is_not_blocked(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    target = "autonomy-same-episode-idempotence"
    goal, step = _admitted_effect_step(db, controller, target=target)

    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=None)
    lifecycle.begin_autonomous(
        "One autonomous episode may reconcile its own already-journaled effect",
        goal["goal_id"],
        step["step_id"],
    )
    first = lifecycle.request_effect("state.noop", target, None)
    second = lifecycle.request_effect("state.noop", target, None)

    assert first["effect_id"] == second["effect_id"]
    assert second["verified"] is True
    assert second["outcome"]["recovered"] is True
    count = db.db.execute(
        "SELECT COUNT(*) FROM effects WHERE user_id=? AND capability=?",
        ("gabriel", "state.noop"),
    ).fetchone()[0]
    assert count == 1


def test_identical_effect_intent_for_different_goal_step_is_not_overblocked(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    target = "autonomy-shared-effect-intent"
    goal_a, step_a = _admitted_effect_step(db, controller, target=target)

    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=None)
    lifecycle.begin_autonomous(
        "Execute goal A",
        goal_a["goal_id"],
        step_a["step_id"],
    )
    first = lifecycle.request_effect("state.noop", target, None)
    assert first["verified"] is True
    lifecycle.abort_autonomous(
        "goal_a_finished_for_scope_control",
        goal_a["goal_id"],
        step_a["step_id"],
    )

    goal_b, step_b = _admitted_effect_step(db, controller, target=target)
    lifecycle.begin_autonomous(
        "Execute distinct goal B with the same bounded intent",
        goal_b["goal_id"],
        step_b["step_id"],
    )
    second = lifecycle.request_effect("state.noop", target, None)

    assert second["verified"] is True
    assert second["effect_id"] != first["effect_id"]
    count = db.db.execute(
        "SELECT COUNT(*) FROM effects WHERE user_id=? AND capability=?",
        ("gabriel", "state.noop"),
    ).fetchone()[0]
    assert count == 2
