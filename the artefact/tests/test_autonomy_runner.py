import pytest

from clayverse.autonomy import AutonomyController
from clayverse.autonomy_scheduler import (
    AutonomySchedulerRunner,
    UserHomeClaudeInferenceRouter,
)
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


class FakeInference:
    def __init__(self, decision):
        self.decision = decision
        self.calls = 0
        self.worlds = []

    def reason(self, world, observation):
        self.calls += 1
        self.worlds.append(world)
        return dict(self.decision)


class FakeRouter:
    def __init__(self, inference):
        self.inference = inference
        self.calls = 0

    def adapter(self, user_id):
        self.calls += 1
        assert user_id in {"gabriel", "andreas"}
        return self.inference


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "autonomy-scheduler.db")
    IdentityRouter(db, {"g": "gabriel", "a": "andreas"})
    return db


def _goal(db, objective="Advance the durable goal"):
    turn = db.append_turn("session:gabriel", "gabriel", "user", objective)
    return AutonomyController(db).create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        turn,
        completion_mode="user_ack",
    )


def test_owner_home_router_uses_only_canonical_user_home(tmp_path):
    router = UserHomeClaudeInferenceRouter(tmp_path)
    adapter = router.adapter("gabriel")
    assert adapter._subprocess_env()["HOME"] == str(tmp_path / "users" / "gabriel" / "home")
    assert router.adapter("gabriel") is adapter
    with pytest.raises(PermissionError, match="unknown autonomous goal owner"):
        router.adapter("mallory")


def test_idle_wake_performs_zero_model_calls(tmp_path):
    db = _db(tmp_path)
    inference = FakeInference({"text": "must not run", "selection": "respond", "effect": None})
    router = FakeRouter(inference)
    result = AutonomySchedulerRunner(db, router).run_wake()
    assert result == {"status": "idle", "steps": 0, "effects": 0}
    assert router.calls == 0
    assert inference.calls == 0
    db.close()


def test_wait_step_is_bounded_to_one_wake_and_persisted(tmp_path):
    db = _db(tmp_path)
    goal = _goal(db)
    inference = FakeInference(
        {"text": "STEP:WAIT\nWait for the next bounded wake.", "selection": "respond", "effect": None}
    )
    result = AutonomySchedulerRunner(db, FakeRouter(inference)).run_wake()
    assert result["status"] == "waiting"
    assert result["steps"] == 1
    assert result["effects"] == 0
    snapshot = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["goal_id"] == goal["goal_id"]
    assert snapshot["counters"]["steps"] == 1
    assert snapshot["current_step"]["kind"] == "wait"
    assert snapshot["current_step"]["status"] == "SUCCEEDED"
    assert inference.worlds[0]["agency"]["profile"]["substrate_anchor"] == "SERVER_UNIFIEDDB"
    db.close()


def test_completion_candidate_cannot_self_certify_without_contract_evidence(tmp_path):
    db = _db(tmp_path)
    goal = _goal(db, "Prepare a reviewable report")
    inference = FakeInference(
        {"text": "STEP:COMPLETE_CANDIDATE\nThe proposal appears ready for independent completion verification.", "selection": "respond", "effect": None}
    )
    result = AutonomySchedulerRunner(db, FakeRouter(inference)).run_wake()
    assert result["status"] == "waiting_for_evidence"
    assert result["goal_id"] == goal["goal_id"]
    snapshot = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["status"] == "VERIFYING"
    assert snapshot["user_ack_turn_id"] is None
    db.close()


def test_mismatched_text_marker_and_effect_fails_closed_before_admission(tmp_path):
    db = _db(tmp_path)
    goal = _goal(db)
    inference = FakeInference(
        {
            "text": "STEP:REASON\nPretend this effect is only reasoning.",
            "selection": "request_effect",
            "effect": {"capability": "state.noop", "target": "marker-test", "argv": None},
        }
    )
    result = AutonomySchedulerRunner(db, FakeRouter(inference)).run_wake()
    assert result["status"] == "blocked"
    snapshot = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["goal_id"] == goal["goal_id"]
    assert snapshot["current_step"] is None
    assert snapshot["counters"]["steps"] == 0
    db.close()
