from clayverse.agency import AgencyState
from clayverse.autonomy import AutonomyRunner
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


class NeverCalledInference:
    def __init__(self):
        self.calls = 0

    def reason(self, world, observation):
        self.calls += 1
        raise AssertionError("inference must not run without runnable work")


class PlanThenReviewInference:
    def __init__(self):
        self.calls = 0
        self.worlds = []

    def reason(self, world, observation):
        self.calls += 1
        self.worlds.append(world)
        if self.calls == 1:
            return {
                "text": "record one bounded internal planning step",
                "selection": "request_effect",
                "effect": {"capability": "state.noop", "target": "agency.plan-step", "argv": None},
            }
        return {"text": "no further executable move; ready for review", "selection": "respond", "effect": None}


class DeniedExternalInference:
    def __init__(self):
        self.calls = 0

    def reason(self, world, observation):
        self.calls += 1
        return {
            "text": "try bounded EntityOS step",
            "selection": "request_effect",
            "effect": {"capability": "entityos.exec", "target": "prototype-test", "argv": ["status"]},
        }


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "autonomy.db")
    IdentityRouter(db, {"g": "gabriel", "a": "andreas"})
    return db


def test_daemon_cycle_spends_zero_inference_when_no_goal_exists(tmp_path):
    db = _db(tmp_path)
    inference = NeverCalledInference()
    result = AutonomyRunner(db, inference).run_cycle()
    assert result == {"status": "idle", "cycle_id": None, "steps": 0, "effects": 0}
    assert inference.calls == 0
    assert db.db.execute("SELECT COUNT(*) FROM agency_cycles").fetchone()[0] == 0
    db.close()


def test_closed_loop_reingests_verified_outcome_before_next_model_step(tmp_path):
    db = _db(tmp_path)
    agency = AgencyState(db)
    goal = agency.create_goal("gabriel", "Design module", "make a grounded design", "review accepts it")
    milestone = agency.add_milestone(goal, "CONCEPT", "Design", "bounded proposal with evidence")
    inference = PlanThenReviewInference()

    result = AutonomyRunner(db, inference).run_cycle()

    assert result["status"] == "closed"
    assert result["steps"] == 2
    assert result["effects"] == 1
    assert inference.calls == 2
    assert inference.worlds[0]["agency"]["profile"]["substrate_anchor"] == "SERVER_UNIFIEDDB"
    assert inference.worlds[0]["runtime_capabilities"] == ["state.noop"]
    second = inference.worlds[1]["agency"]["active_goals"][0]["milestones"][0]["recent_attempts"]
    assert second
    assert second[-1]["effect_id"] is not None
    assert second[-1]["status"] == "SUCCEEDED"
    assert db.db.execute("SELECT status FROM agency_milestones WHERE milestone_id=?", (milestone,)).fetchone()[0] == "READY_FOR_REVIEW"
    assert db.db.execute("SELECT status FROM agency_goals WHERE goal_id=?", (goal,)).fetchone()[0] == "ACTIVE"
    db.close()


def test_denied_effects_stop_after_failed_retry_limit(tmp_path):
    db = _db(tmp_path)
    agency = AgencyState(db)
    goal = agency.create_goal("gabriel", "Prototype", "run bounded prototype work", "verified result")
    milestone = agency.add_milestone(goal, "CONCEPT", "Try action", "verified EntityOS outcome")
    inference = DeniedExternalInference()

    result = AutonomyRunner(db, inference, entityos_bridge=None).run_cycle()

    assert result["status"] == "closed"
    assert inference.calls == agency.policy()["max_failed_retries_per_milestone"]
    assert result["effects"] == agency.policy()["max_failed_retries_per_milestone"]
    assert db.db.execute("SELECT status FROM agency_milestones WHERE milestone_id=?", (milestone,)).fetchone()[0] == "BLOCKED"
    assert db.db.execute("SELECT COUNT(*) FROM agency_attempts WHERE milestone_id=? AND status='FAILED'", (milestone,)).fetchone()[0] == 3
    db.close()
