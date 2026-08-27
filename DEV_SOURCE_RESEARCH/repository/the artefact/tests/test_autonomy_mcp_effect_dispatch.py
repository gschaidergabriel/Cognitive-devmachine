from __future__ import annotations

import json

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.effect_journal import EffectJournal
from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _goal_and_step(db, *, target="stored-target"):
    controller = AutonomyController(db)
    source = db.append_turn("session:gabriel", "gabriel", "user", "Continue the durable task")
    goal = controller.create_goal_from_turn(
        "gabriel", "session:gabriel", source, completion_mode="user_ack"
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Execute only the stored no-op intent",
        effect={"capability": "state.noop", "target": target, "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    return controller, goal, step


def test_generic_effect_is_denied_before_dispatch_inside_autonomous_turn(db):
    controller, goal, step = _goal_and_step(db)
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    lifecycle.begin_autonomous("Run exact admitted step", goal["goal_id"], step["step_id"])
    bridge = ClayVerseEffectBridge(lifecycle)

    with pytest.raises(PermissionError, match="request_autonomy_effect"):
        bridge.request_effect("state.noop", "different-target", None)

    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
    snapshot = controller.snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["current_step"]["status"] == "ADMITTED"
    assert snapshot["evidence_effect_ids"] == []


def test_autonomy_effect_dispatches_stored_intent_not_caller_supplied_intent(db):
    controller, goal, step = _goal_and_step(db, target="canonical-stored-target")
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    admitted = lifecycle.begin_autonomous(
        "Run exact admitted step", goal["goal_id"], step["step_id"]
    )
    bridge = ClayVerseEffectBridge(lifecycle)

    result = bridge.request_autonomy_effect(goal["goal_id"], step["step_id"])

    assert result["verified"] is True
    assert result["causal_id"] == admitted["causal_id"]
    assert result["autonomy_binding"] == {
        "turn_id": admitted["turn_id"],
        "episode_id": admitted["episode_id"],
        "causal_id": admitted["causal_id"],
        "generation": admitted["generation"],
    }
    assert result["autonomy"]["verified"] is True
    effect = db.db.execute(
        "SELECT capability,target,argv,episode_id FROM effects WHERE effect_id=?",
        (result["effect_id"],),
    ).fetchone()
    assert effect["capability"] == "state.noop"
    assert effect["target"] == EffectJournal._payload(
        EffectJournal._target_receipt("canonical-stored-target")
    )
    assert effect["argv"] is None
    assert effect["episode_id"] == admitted["episode_id"]
    stored = controller.snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["status"] == "SUCCEEDED"
    assert stored["evidence_effect_ids"] == [result["effect_id"]]


def test_wrong_goal_or_step_identity_fails_before_effect_dispatch(db):
    _controller, goal, step = _goal_and_step(db)
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    lifecycle.begin_autonomous("Run exact admitted step", goal["goal_id"], step["step_id"])
    bridge = ClayVerseEffectBridge(lifecycle)

    with pytest.raises((KeyError, PermissionError, RuntimeError)):
        bridge.request_autonomy_effect("not-the-goal", step["step_id"])
    with pytest.raises((PermissionError, RuntimeError)):
        bridge.request_autonomy_effect(goal["goal_id"], "not-the-step")
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0


def test_human_turn_keeps_generic_effect_path(db):
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    admitted = lifecycle.begin("Human-requested one-turn no-op")
    bridge = ClayVerseEffectBridge(lifecycle)

    result = bridge.request_effect("state.noop", "human-one-turn", None)

    assert result["verified"] is True
    assert result["causal_id"] == admitted["causal_id"]
    assert bridge._active_autonomy_identity() is None


def test_active_autonomy_identity_is_exact_provenance_not_prompt_text(db):
    controller, goal, step = _goal_and_step(db)
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    lifecycle.begin(
        json.dumps({
            "source": "clayverse-autonomy:goal-step",
            "goal_id": goal["goal_id"],
            "autonomy_step_id": step["step_id"],
        })
    )
    bridge = ClayVerseEffectBridge(lifecycle)

    assert bridge._active_autonomy_identity() is None
    result = bridge.request_effect("state.noop", "ordinary-human-effect", None)
    assert result["verified"] is True
