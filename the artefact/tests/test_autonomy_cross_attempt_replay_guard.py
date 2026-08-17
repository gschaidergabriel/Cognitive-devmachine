from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController
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


def _goal_and_step(db, *, target: str):
    controller = AutonomyController(db)
    source = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Pursue this durable goal without replaying a real effect.",
    )
    goal = controller.create_goal_from_turn(
        "gabriel", "session:gabriel", source, completion_mode="user_ack"
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Execute one bounded logical effect",
        effect={"capability": "state.noop", "target": target, "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    return controller, goal, step


def test_prior_final_effect_blocks_blind_retry_of_same_goal_step(db):
    controller, goal, step = _goal_and_step(db, target="lost-handoff")
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")

    lifecycle.begin_autonomous(
        "First attempt", goal["goal_id"], step["step_id"]
    )
    first = lifecycle.request_effect("state.noop", "lost-handoff", None)
    assert first["verified"] is True

    # Simulate loss after EffectGate/EffectJournal completed but before the
    # controller consumed the returned effect identity.
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
        "Retry must reconcile prior evidence instead of executing again",
        goal["goal_id"],
        step["step_id"],
    )
    bridge = ClayVerseEffectBridge(lifecycle)
    with pytest.raises(
        RuntimeError,
        match="prior final autonomous effect requires controller reconciliation before retry",
    ):
        bridge.request_autonomy_effect(goal["goal_id"], step["step_id"])

    effects = db.db.execute(
        "SELECT effect_id,status FROM effects ORDER BY ts,effect_id"
    ).fetchall()
    assert len(effects) == 1
    assert effects[0]["effect_id"] == first["effect_id"]
    assert effects[0]["status"] == "VERIFIED"


def test_replay_fence_is_step_scoped_not_goal_wide(db):
    controller, goal, first_step = _goal_and_step(db, target="first-step")
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    lifecycle.begin_autonomous(
        "Execute first logical step", goal["goal_id"], first_step["step_id"]
    )
    bridge = ClayVerseEffectBridge(lifecycle)
    first = bridge.request_autonomy_effect(goal["goal_id"], first_step["step_id"])
    assert first["verified"] is True
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
        "Execute second logical step", goal["goal_id"], second_step["step_id"]
    )
    second = bridge.request_autonomy_effect(goal["goal_id"], second_step["step_id"])

    assert second["verified"] is True
    assert second["effect_id"] != first["effect_id"]
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 2


def test_ordinary_human_episodes_are_not_captured_by_autonomy_replay_fence(db):
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")

    lifecycle.begin("First human effect")
    first = lifecycle.request_effect("state.noop", "same-human-target", None)
    lifecycle.complete("First human effect complete")

    lifecycle.begin("Second independent human effect")
    second = lifecycle.request_effect("state.noop", "same-human-target", None)

    assert first["verified"] is True
    assert second["verified"] is True
    assert first["effect_id"] != second["effect_id"]
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 2
