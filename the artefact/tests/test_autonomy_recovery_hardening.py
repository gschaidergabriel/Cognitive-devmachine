from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyBudgetExceeded, AutonomyController, GoalBudget
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db


def _goal(db, controller, *, completion_mode="user_ack", required_capability=None, budget=None):
    turn_id = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Continue this durable goal safely across a restart.",
    )
    return controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        turn_id,
        completion_mode=completion_mode,
        required_capability=required_capability,
        budget=budget,
    )


def test_zero_effect_budget_still_allows_non_effect_reasoning(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        budget=GoalBudget(max_steps=3, max_retries_per_step=0, max_effects=0),
    )

    step = controller.propose_step(goal["goal_id"], "reason", "Inspect canonical state only")
    admitted = controller.admit_step(goal["goal_id"], step["step_id"])
    assert admitted["status"] == "ADMITTED"
    controller.record_reason_success(goal["goal_id"], step["step_id"])

    with pytest.raises(AutonomyBudgetExceeded):
        controller.propose_step(
            goal["goal_id"],
            "effect",
            "No effects are budgeted",
            effect={"capability": "state.noop", "target": "budget-test", "argv": None},
        )


def test_generation_recovery_requeues_interrupted_non_effect_step(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    step = controller.propose_step(goal["goal_id"], "reason", "Prepare the next bounded step")
    controller.admit_step(goal["goal_id"], step["step_id"])

    live = db.advance_entity_generation()
    result = controller.recover_generation(expected_generation=live)

    assert result["interrupted_no_effect_requeued"] == 1
    recovered = controller.snapshot(user_id="gabriel")["goals"][0]
    assert recovered["generation"] == live
    assert recovered["status"] == "ACTIVE"
    assert recovered["current_step"]["status"] == "FAILED"
    assert recovered["blocked_reason"] == "recovered_interrupted_no_effect_step"
    assert controller.next_runnable(user_id="gabriel")["goal_id"] == goal["goal_id"]


def test_generation_recovery_never_replays_or_self_verifies_ambiguous_effect(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        completion_mode="verified_effect",
        required_capability="state.noop",
        budget=GoalBudget(max_steps=3, max_retries_per_step=1, max_effects=1),
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Request one canonical no-op",
        effect={"capability": "state.noop", "target": "restart-boundary", "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0

    live = db.advance_entity_generation()
    result = controller.recover_generation(expected_generation=live)

    assert result["ambiguous_effect_blocked"] == 1
    recovered = controller.snapshot(user_id="gabriel")["goals"][0]
    assert recovered["generation"] == live
    assert recovered["status"] == "BLOCKED"
    assert recovered["current_step"]["status"] == "FAILED"
    assert recovered["blocked_reason"] == "unknown_effect_after_generation_change"
    assert controller.next_runnable(user_id="gabriel") is None
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0


def test_generation_recovery_preserves_existing_block_without_reactivation(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    controller.block_goal(goal["goal_id"], "needs external information")

    live = db.advance_entity_generation()
    result = controller.recover_generation(expected_generation=live)

    assert result["blocked_preserved"] == 1
    recovered = controller.snapshot(user_id="gabriel")["goals"][0]
    assert recovered["generation"] == live
    assert recovered["status"] == "BLOCKED"
    assert recovered["blocked_reason"] == "needs external information"


def test_terminal_goal_is_not_rewritten_during_generation_recovery(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    ack = db.append_turn("session:gabriel", "gabriel", "user", "confirmed complete")
    controller.acknowledge_by_user(goal["goal_id"], ack)
    controller.verify_completion(goal["goal_id"])
    before = controller.snapshot(user_id="gabriel")["goals"][0]

    db.advance_entity_generation()
    result = controller.recover_generation()
    after = controller.snapshot(user_id="gabriel")["goals"][0]

    assert result["terminal_preserved"] == 1
    assert after == before
