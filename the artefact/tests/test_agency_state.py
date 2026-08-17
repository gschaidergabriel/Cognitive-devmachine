import json

import pytest

from clayverse.agency import AgencyPolicyError, AgencyState
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def _agency(tmp_path):
    db = UnifiedDB(tmp_path / "agency.db")
    IdentityRouter(db, {"g": "gabriel", "a": "andreas"})
    return db, AgencyState(db)


def test_agency_identity_is_server_state_not_prompt_or_device_roleplay(tmp_path):
    db, agency = _agency(tmp_path)
    snap = agency.snapshot(user_id="gabriel")
    profile = snap["profile"]
    assert snap["authority"] == "UnifiedDB"
    assert profile["identity_mode"] == "PERSISTENT_GOAL_AGENT"
    assert profile["substrate_anchor"] == "SERVER_UNIFIEDDB"
    assert profile["behavior_mode"] == "PROACTIVE_GROUNDED"
    rendered = json.dumps(snap, sort_keys=True).lower()
    assert "usb" not in rendered
    assert "smart contract" not in rendered
    assert "crypto" not in rendered
    assert "model assertions" in rendered
    db.close()


def test_goal_snapshots_are_user_scoped(tmp_path):
    db, agency = _agency(tmp_path)
    g = agency.create_goal("gabriel", "Gabriel goal", "private-g-objective", "g-done")
    a = agency.create_goal("andreas", "Andreas goal", "private-a-objective", "a-done")
    agency.add_milestone(g, "CONCEPT", "G concept", "g-evidence")
    agency.add_milestone(a, "CONCEPT", "A concept", "a-evidence")

    gs = json.dumps(agency.snapshot(user_id="gabriel"), sort_keys=True)
    ass = json.dumps(agency.snapshot(user_id="andreas"), sort_keys=True)
    assert "private-g-objective" in gs
    assert "private-a-objective" not in gs
    assert "private-a-objective" in ass
    assert "private-g-objective" not in ass
    db.close()


def test_phase_progress_requires_review_and_cannot_be_declared_by_model(tmp_path):
    db, agency = _agency(tmp_path)
    goal = agency.create_goal("gabriel", "Build thing", "ship it", "final tests pass")
    concept = agency.add_milestone(goal, "CONCEPT", "Concept", "design evidence")
    prototype = agency.add_milestone(goal, "PROTOTYPE", "Prototype", "test evidence")

    cycle = agency.begin_cycle()
    work = agency.claim_next(cycle)
    assert work.milestone_id == concept
    status = agency.complete_attempt(work.attempt_id, {"text": "ready", "effect": None}, None, None)
    assert status == "SUCCEEDED"
    assert db.db.execute("SELECT status FROM agency_milestones WHERE milestone_id=?", (concept,)).fetchone()[0] == "READY_FOR_REVIEW"

    # Waiting for review is idle, not an empty background cycle and not permission
    # for the model to move itself into a later phase.
    assert agency.begin_cycle() is None
    assert db.db.execute("SELECT status FROM agency_milestones WHERE milestone_id=?", (prototype,)).fetchone()[0] == "PENDING"

    with pytest.raises(AgencyPolicyError, match="owner mismatch"):
        agency.review_milestone(concept, "andreas", "PASS")
    agency.review_milestone(concept, "gabriel", "PASS")

    cycle3 = agency.begin_cycle()
    next_work = agency.claim_next(cycle3)
    assert next_work.milestone_id == prototype
    db.close()


def test_only_review_transition_can_complete_goal(tmp_path):
    db, agency = _agency(tmp_path)
    goal = agency.create_goal("gabriel", "One phase", "produce evidence", "accepted")
    milestone = agency.add_milestone(goal, "CONCEPT", "Concept", "reviewable result")
    cycle = agency.begin_cycle()
    work = agency.claim_next(cycle)
    agency.complete_attempt(work.attempt_id, {"text": "done", "effect": None}, None, None)

    assert db.db.execute("SELECT status FROM agency_goals WHERE goal_id=?", (goal,)).fetchone()[0] == "ACTIVE"
    agency.review_milestone(milestone, "gabriel", "PASS", "accepted")
    assert db.db.execute("SELECT status FROM agency_goals WHERE goal_id=?", (goal,)).fetchone()[0] == "COMPLETE"
    db.close()


def test_caller_cannot_forge_success_when_effect_journal_says_denied(tmp_path):
    db, agency = _agency(tmp_path)
    goal = agency.create_goal("gabriel", "Ground truth", "use persisted evidence", "no forged progress")
    milestone = agency.add_milestone(goal, "CONCEPT", "Attempt", "verified outcome")
    cycle = agency.begin_cycle()
    work = agency.claim_next(cycle)
    generation = db.entity_generation()
    effect_id = db.record_effect(
        None,
        "gabriel",
        "entityos.exec",
        "bounded-target",
        generation,
        "DENIED",
        outcome={"ok": True, "denied": True},
    )

    status = agency.complete_attempt(
        work.attempt_id,
        {"text": "I claim success"},
        effect_id,
        {"ok": True},
    )
    assert status == "FAILED"
    assert db.db.execute("SELECT status FROM agency_milestones WHERE milestone_id=?", (milestone,)).fetchone()[0] == "ACTIVE"
    db.close()


def test_ers_does_not_reward_state_noop(tmp_path):
    db, agency = _agency(tmp_path)
    goal = agency.create_goal("gabriel", "Telemetry", "avoid reward gaming", "review")
    agency.add_milestone(goal, "CONCEPT", "Noop", "no-op does not earn reputation")
    cycle = agency.begin_cycle()
    work = agency.claim_next(cycle)
    effect_id = db.record_effect(
        None,
        "gabriel",
        "state.noop",
        "noop",
        db.entity_generation(),
        "VERIFIED",
        outcome={"ok": True},
    )
    assert agency.complete_attempt(work.attempt_id, {"text": "noop"}, effect_id, {"ok": True}) == "SUCCEEDED"
    metrics = agency.metrics("gabriel")
    assert metrics["verified_effect_steps"] == 0
    assert metrics["failed_effect_steps"] == 0
    assert metrics["ers"] == 0.0
    assert metrics["ers_role"] == "telemetry_only_not_authority"
    db.close()
