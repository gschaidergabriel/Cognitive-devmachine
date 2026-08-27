from __future__ import annotations

import time

import pytest

from clayverse.autonomy import AutonomyController, GoalBudget
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import _active_autonomy_preemption, _reconcile_preempted_autonomy
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _goal(db, controller, *, budget=None):
    source = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Continue this durable goal even when a human interrupts autonomous work.",
    )
    return controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
        budget=budget,
    )


def test_human_preemption_requeues_admitted_no_effect_step(db):
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    step = controller.propose_step(goal["goal_id"], "reason", "Prepare a bounded plan")
    controller.admit_step(goal["goal_id"], step["step_id"])

    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    autonomous = lifecycle.begin_autonomous("background reasoning", goal["goal_id"], step["step_id"])
    captured = _active_autonomy_preemption(db, "session:gabriel", "gabriel")
    assert captured["turn_id"] == autonomous["turn_id"]
    assert captured["effect_id"] is None

    human = lifecycle.begin("Human priority arrives")
    result = _reconcile_preempted_autonomy(db, "gabriel", captured)

    assert lifecycle.active()["turn_id"] == human["turn_id"]
    assert result["reconciled"] is True
    assert result["mode"] == "no_effect_requeue"
    state = controller.snapshot(user_id="gabriel")["goals"][0]
    assert state["status"] == "ACTIVE"
    assert state["current_step"]["status"] == "FAILED"
    assert state["blocked_reason"] == "human_preempted_autonomy_step"
    assert state["evidence_effect_ids"] == []
    assert controller.next_runnable(user_id="gabriel")["goal_id"] == goal["goal_id"]


def test_human_preemption_reconciles_final_effect_without_replay(db):
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Execute one exact no-op",
        effect={"capability": "state.noop", "target": "preemption-effect", "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])

    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    autonomous = lifecycle.begin_autonomous("perform exact effect", goal["goal_id"], step["step_id"])
    effect = lifecycle.request_effect("state.noop", "preemption-effect", None)
    captured = _active_autonomy_preemption(db, "session:gabriel", "gabriel")
    assert captured["effect_id"] == effect["effect_id"]

    lifecycle.begin("Human prompt preempts after verified effect")
    result = _reconcile_preempted_autonomy(db, "gabriel", captured)

    assert result["mode"] == "final_effect_reentry"
    assert result["effect_id"] == effect["effect_id"]
    assert result["verified"] is True
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    state = controller.snapshot(user_id="gabriel")["goals"][0]
    assert state["current_step"]["status"] == "SUCCEEDED"
    assert state["evidence_effect_ids"] == [effect["effect_id"]]
    assert controller.next_runnable(user_id="gabriel")["goal_id"] == goal["goal_id"]
    causal = db.db.execute(
        "SELECT causal_id,episode_id,reentered FROM causal_episodes WHERE effect_id=?",
        (effect["effect_id"],),
    ).fetchone()
    assert causal["causal_id"] == autonomous["causal_id"]
    assert causal["episode_id"] == autonomous["episode_id"]
    assert causal["reentered"] == 1


def test_pending_effect_blocks_human_preemption_and_is_not_replayed(db):
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Pending boundary",
        effect={"capability": "state.noop", "target": "pending-preempt", "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    autonomous = lifecycle.begin_autonomous("pending effect", goal["goal_id"], step["step_id"])

    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "pending-effect",
            autonomous["episode_id"],
            "gabriel",
            "state.noop",
            "pending",
            None,
            autonomous["generation"],
            "PENDING",
            None,
            time.time(),
            None,
        ),
    )
    captured = _active_autonomy_preemption(db, "session:gabriel", "gabriel")

    with pytest.raises(TurnLifecycleError, match="effect outcome pending"):
        lifecycle.begin("Human prompt cannot race an unknown effect")

    assert lifecycle.active()["turn_id"] == autonomous["turn_id"]
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    with pytest.raises(Exception, match="pending"):
        _reconcile_preempted_autonomy(db, "gabriel", captured)


def test_zero_retry_budget_turns_repeated_human_preemption_into_explicit_block(db):
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        budget=GoalBudget(max_steps=2, max_retries_per_step=0, max_effects=0),
    )
    step = controller.propose_step(goal["goal_id"], "reason", "One admitted attempt")
    controller.admit_step(goal["goal_id"], step["step_id"])
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    lifecycle.begin_autonomous("single attempt", goal["goal_id"], step["step_id"])
    captured = _active_autonomy_preemption(db, "session:gabriel", "gabriel")

    lifecycle.begin("Human takes priority")
    result = _reconcile_preempted_autonomy(db, "gabriel", captured)

    assert result["status"] == "BLOCKED"
    state = controller.snapshot(user_id="gabriel")["goals"][0]
    assert state["current_step"]["status"] == "FAILED"
    assert state["blocked_reason"] == "retry_budget_exhausted"
    assert controller.next_runnable(user_id="gabriel") is None
