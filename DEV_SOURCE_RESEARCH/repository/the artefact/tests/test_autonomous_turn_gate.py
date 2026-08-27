from __future__ import annotations

import json

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _lifecycle(db):
    return TurnLifecycle(db, "gabriel", "session:gabriel")


def test_autonomous_admission_never_preempts_active_human_turn(db):
    lifecycle = _lifecycle(db)
    human = lifecycle.begin("Human work is active")
    before = dict(lifecycle.active())

    with pytest.raises(TurnLifecycleError, match="deferred without preemption"):
        lifecycle.begin_autonomous("Background step must defer", "goal-1", "step-1")

    after = dict(lifecycle.active())
    assert after["turn_id"] == before["turn_id"] == human["turn_id"]
    assert after["causal_id"] == before["causal_id"] == human["causal_id"]
    assert db.db.execute(
        "SELECT COUNT(*) FROM turns WHERE content LIKE 'TURN_ABORTED:%'"
    ).fetchone()[0] == 0


def test_autonomous_observation_is_system_state_not_user_goal_source(db):
    lifecycle = _lifecycle(db)
    admitted = lifecycle.begin_autonomous(
        "FACT: planner prose must not become owner authority",
        "goal-1",
        "step-1",
        resources=["task:goal-1"],
    )
    turn = db.db.execute(
        "SELECT role,provenance FROM turns WHERE turn_id=?", (admitted["turn_id"],)
    ).fetchone()
    provenance = json.loads(turn["provenance"])
    assert turn["role"] == "system"
    assert provenance["source"] == "clayverse-autonomy:goal-step"
    assert provenance["goal_id"] == "goal-1"
    assert provenance["autonomy_step_id"] == "step-1"
    assert db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE source_turn_id=?", (admitted["turn_id"],)
    ).fetchone()[0] == 0

    controller = AutonomyController(db)
    with pytest.raises(PermissionError, match="canonical owner user turn"):
        controller.create_goal_from_turn(
            "gabriel",
            "session:gabriel",
            admitted["turn_id"],
            completion_mode="user_ack",
        )


def test_autonomous_effect_reuses_canonical_effect_and_causal_path(db):
    lifecycle = _lifecycle(db)
    admitted = lifecycle.begin_autonomous(
        "Run the exact bounded autonomous no-op",
        "goal-1",
        "step-1",
        resources=["task:goal-1"],
    )
    result = lifecycle.request_effect("state.noop", "autonomy:goal-1:step-1", None)
    assert result["verified"] is True
    assert result["causal_id"] == admitted["causal_id"]

    effect = db.db.execute(
        "SELECT episode_id,status FROM effects WHERE effect_id=?", (result["effect_id"],)
    ).fetchone()
    causal = db.db.execute(
        "SELECT causal_id,episode_id,effect_id,reentered FROM causal_episodes WHERE effect_id=?",
        (result["effect_id"],),
    ).fetchone()
    assert effect["episode_id"] == admitted["episode_id"]
    assert effect["status"] == "VERIFIED"
    assert causal["causal_id"] == admitted["causal_id"]
    assert causal["episode_id"] == admitted["episode_id"]
    assert causal["effect_id"] == result["effect_id"]
    assert causal["reentered"] == 1

    completed = lifecycle.complete_autonomous(
        "Observed verified no-op receipt.", "goal-1", "step-1"
    )
    assert completed["completed"] is True
    assert completed["effect_id"] == result["effect_id"]
    output = db.db.execute(
        "SELECT provenance FROM turns WHERE turn_id=?", (completed["assistant_turn_id"],)
    ).fetchone()
    output_provenance = json.loads(output["provenance"])
    assert output_provenance["source"] == "clayverse-autonomy:goal-step:complete"
    assert output_provenance["goal_id"] == "goal-1"
    assert output_provenance["autonomy_step_id"] == "step-1"


def test_human_and_autonomous_completion_cannot_close_each_others_turns(db):
    lifecycle = _lifecycle(db)
    lifecycle.begin_autonomous("background", "goal-1", "step-1")
    with pytest.raises(TurnLifecycleError, match="interactive completion"):
        lifecycle.complete("must not close autonomous work")
    with pytest.raises(TurnLifecycleError, match="identity mismatch"):
        lifecycle.complete_autonomous("wrong binding", "goal-1", "step-other")
    assert lifecycle.active() is not None
    lifecycle.complete_autonomous("correct binding", "goal-1", "step-1")

    lifecycle.begin("human turn")
    with pytest.raises(TurnLifecycleError, match="not an autonomous goal step"):
        lifecycle.complete_autonomous("must not close human work", "goal-1", "step-1")
    assert lifecycle.active() is not None
    lifecycle.complete("human response")


def test_new_human_prompt_may_preempt_autonomous_turn(db):
    lifecycle = _lifecycle(db)
    autonomous = lifecycle.begin_autonomous("background work", "goal-1", "step-1")
    human = lifecycle.begin("Human priority takes over")

    assert human["turn_id"] != autonomous["turn_id"]
    assert lifecycle.active()["turn_id"] == human["turn_id"]
    old_workspace = db.db.execute(
        "SELECT state FROM workspace_episodes WHERE episode_id=?", (autonomous["episode_id"],)
    ).fetchone()
    assert old_workspace["state"] == "ABORTED"
    abort = db.db.execute(
        "SELECT content FROM turns WHERE role='system' AND content LIKE 'TURN_ABORTED:%' ORDER BY ordinal DESC LIMIT 1"
    ).fetchone()
    assert "previous_turn_interrupted_before_next_prompt" in abort["content"]


def test_autonomous_abort_requires_exact_goal_step_binding(db):
    lifecycle = _lifecycle(db)
    lifecycle.begin_autonomous("background", "goal-1", "step-1")
    with pytest.raises(TurnLifecycleError, match="identity mismatch"):
        lifecycle.abort_autonomous("wrong step", "goal-1", "step-2")
    assert lifecycle.active() is not None
    result = lifecycle.abort_autonomous("dependency unavailable", "goal-1", "step-1")
    assert result["aborted"] is True
    assert lifecycle.active() is None
