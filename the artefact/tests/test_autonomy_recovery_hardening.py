from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyBudgetExceeded, AutonomyController, GoalBudget
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db


def _goal(
    db,
    controller,
    *,
    completion_mode="user_ack",
    required_capability=None,
    required_target=None,
    budget=None,
):
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
        required_target=required_target,
        budget=budget,
    )


class _FakeEntityOS:
    sha256 = "1" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0}


def _verified_completion_effect(db, controller, goal, step, *, target):
    lifecycle = TurnLifecycle(
        db,
        "gabriel",
        "session:gabriel",
        entityos_bridge=_FakeEntityOS(),
    )
    lifecycle.begin_autonomous(
        "Execute one restart-bound completion effect",
        goal["goal_id"],
        step["step_id"],
        resources=[f"goal:{goal['goal_id']}", f"goal-step:{step['step_id']}"],
    )
    result = lifecycle.request_effect("entityos.exec", target, ["verify", target])
    assert result["verified"] is True
    recorded = controller.record_effect_result(
        goal["goal_id"], step["step_id"], result["effect_id"]
    )
    assert recorded["verified"] is True
    assert recorded["completion_evidence"] is True
    return result["effect_id"]


def test_zero_effect_budget_still_allows_non_effect_reasoning(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        budget=GoalBudget(max_steps=3, max_retries_per_step=0, max_effects=0),
    )

    step = controller.propose_step(goal["goal_id"], "reason", "Inspect canonical state only")
    controller.admit_step(goal["goal_id"], step["step_id"])
    controller.record_reason_success(goal["goal_id"], step["step_id"])

    with pytest.raises(AutonomyBudgetExceeded, match="effect budget"):
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


def test_boot_recovery_reenters_goal_after_generation_advance(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    step = controller.propose_step(goal["goal_id"], "reason", "Interrupted by restart")
    controller.admit_step(goal["goal_id"], step["step_id"])

    result = recover_incomplete_episodes(db)

    assert result["generation"] == 2
    recovered = controller.snapshot(user_id="gabriel")["goals"][0]
    assert recovered["generation"] == 2
    assert recovered["status"] == "ACTIVE"
    assert recovered["current_step"]["status"] == "FAILED"
    assert controller.next_runnable(user_id="gabriel")["goal_id"] == goal["goal_id"]


def test_generation_recovery_never_replays_ambiguous_admitted_effect(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        completion_mode="user_ack",
        budget=GoalBudget(max_steps=3, max_retries_per_step=1, max_effects=1),
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Request one intermediate no-op whose outcome will be unknown after restart",
        effect={"capability": "state.noop", "target": "restart-boundary", "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0

    live = db.advance_entity_generation()
    result = controller.recover_generation(expected_generation=live)

    assert result["ambiguous_effect_blocked"] == 1
    recovered = controller.snapshot(user_id="gabriel")["goals"][0]
    assert recovered["status"] == "BLOCKED"
    assert recovered["blocked_reason"] == "unknown_effect_after_generation_change"
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0


def test_verified_old_generation_effect_is_preserved_but_not_rebound(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    target = "receipt-boundary"
    goal = _goal(
        db,
        controller,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
        required_target=target,
        budget=GoalBudget(max_steps=3, max_retries_per_step=1, max_effects=1),
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "One verified side-effect boundary",
        effect={
            "capability": "entityos.exec",
            "target": target,
            "argv": ["verify", target],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _verified_completion_effect(db, controller, goal, step, target=target)

    live = db.advance_entity_generation()
    result = controller.recover_generation(expected_generation=live)

    assert result["effect_evidence_rebind_required"] == 1
    recovered = controller.snapshot(user_id="gabriel")["goals"][0]
    assert recovered["generation"] == live
    assert recovered["status"] == "BLOCKED"
    assert recovered["blocked_reason"] == "effect_evidence_requires_generation_rebind"
    assert recovered["evidence_effect_ids"] == [effect_id]
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1


def test_generation_recovery_preserves_existing_block_and_terminal_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    blocked = _goal(db, controller)
    controller.block_goal(blocked["goal_id"], "needs external information")

    complete_source = db.append_turn("session:gabriel", "gabriel", "user", "Complete another goal")
    complete = controller.create_goal_from_turn(
        "gabriel", "session:gabriel", complete_source, completion_mode="user_ack"
    )
    ack = db.append_turn("session:gabriel", "gabriel", "user", "confirmed complete")
    controller.acknowledge_by_user(complete["goal_id"], ack)
    controller.verify_completion(complete["goal_id"])
    terminal_before = [
        g
        for g in controller.snapshot(user_id="gabriel")["goals"]
        if g["goal_id"] == complete["goal_id"]
    ][0]

    live = db.advance_entity_generation()
    result = controller.recover_generation(expected_generation=live)

    goals = {g["goal_id"]: g for g in controller.snapshot(user_id="gabriel")["goals"]}
    assert result["blocked_preserved"] == 1
    assert result["terminal_preserved"] == 1
    assert goals[blocked["goal_id"]]["generation"] == live
    assert goals[blocked["goal_id"]]["status"] == "BLOCKED"
    assert goals[blocked["goal_id"]]["blocked_reason"] == "needs external information"
    assert goals[complete["goal_id"]] == terminal_before