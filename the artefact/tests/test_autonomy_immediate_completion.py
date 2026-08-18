from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _VerifiedEntityOS:
    sha256 = "a" * 64

    def run(self, argv):
        assert argv == ["bounded-ok"]
        return {
            "ok": True,
            "exit": 0,
            "stdout_sha256": "b" * 64,
            "stderr_sha256": "c" * 64,
            "stdout": "ok",
            "stderr": "",
        }


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _source(db, text):
    return db.append_turn("session:gabriel", "gabriel", "user", text)


def test_verified_entityos_effect_completes_before_any_replanning(db):
    controller = AutonomyController(db)
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        _source(db, "Execute one verified bounded EntityOS action."),
        completion_mode="verified_effect",
        required_capability="entityos.exec",
        required_target="autonomy-immediate-completion",
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Run the exact accepted internal effect",
        effect={
            "capability": "entityos.exec",
            "target": "autonomy-immediate-completion",
            "argv": ["bounded-ok"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])

    lifecycle = TurnLifecycle(
        db,
        "gabriel",
        "session:gabriel",
        entityos_bridge=_VerifiedEntityOS(),
    )
    admitted = lifecycle.begin_autonomous(
        "Execute the exact admitted effect now.", goal["goal_id"], step["step_id"]
    )
    bridge = ClayVerseEffectBridge(lifecycle)
    result = bridge.request_autonomy_effect(goal["goal_id"], step["step_id"])

    assert result["verified"] is True
    assert result["autonomy"]["verified"] is True
    assert result["autonomy_completion"] == {
        "goal_id": goal["goal_id"],
        "status": "COMPLETED",
        "evidence": result["effect_id"],
    }
    snapshot = controller.snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["status"] == "COMPLETED"
    assert snapshot["current_step"]["step_id"] == step["step_id"]
    assert snapshot["current_step"]["kind"] == "effect"
    assert snapshot["evidence_effect_ids"] == [result["effect_id"]]
    effect = db.db.execute(
        "SELECT episode_id,status FROM effects WHERE effect_id=?", (result["effect_id"],)
    ).fetchone()
    assert effect["episode_id"] == admitted["episode_id"]
    assert effect["status"] == "VERIFIED"


def test_state_noop_never_auto_completes_verified_effect_contract(db):
    controller = AutonomyController(db)
    # The controller itself rejects state.noop as an automatic completion capability.
    with pytest.raises(ValueError, match="independently verifiable effect capability"):
        controller.create_goal_from_turn(
            "gabriel",
            "session:gabriel",
            _source(db, "A no-op must not prove completion."),
            completion_mode="verified_effect",
            required_capability="state.noop",
        )


def test_user_ack_goal_stays_open_after_verified_noop(db):
    controller = AutonomyController(db)
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        _source(db, "Keep this goal open until I explicitly acknowledge it."),
        completion_mode="user_ack",
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Exercise the exact causal effect spine only",
        effect={"capability": "state.noop", "target": "no-completion-credit", "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    lifecycle.begin_autonomous("Run bounded no-op", goal["goal_id"], step["step_id"])
    result = ClayVerseEffectBridge(lifecycle).request_autonomy_effect(
        goal["goal_id"], step["step_id"]
    )

    assert result["verified"] is True
    assert result["autonomy_completion"] is None
    assert controller.snapshot(user_id="gabriel")["goals"][0]["status"] == "ACTIVE"
