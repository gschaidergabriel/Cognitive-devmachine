from __future__ import annotations

import json

import pytest

from clayverse.autonomy import AutonomyController, GoalBudget
from clayverse.autonomy_planner import (
    DECISION_SCHEMA,
    PLANNER_STEP_PREFIX,
    AutonomyDecisionError,
    AutonomyPlanner,
)
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _goal(db, *, budget=None):
    controller = AutonomyController(db)
    turn = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Autonomously advance this durable bounded goal.",
    )
    return controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        turn,
        completion_mode="user_ack",
        budget=budget,
    )


def _decision(kind, description="next", effect=None):
    return json.dumps(
        {
            "schema": DECISION_SCHEMA,
            "kind": kind,
            "description": description,
            "effect": effect,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def test_prepare_next_creates_one_admitted_typed_planner_step(db):
    goal = _goal(db)
    planner = AutonomyPlanner(db)

    prepared = planner.prepare_next("gabriel")
    again = planner.prepare_next("gabriel")

    assert prepared["goal_id"] == goal["goal_id"]
    assert prepared["mode"] == "reason"
    assert prepared["kind"] == "reason"
    assert prepared["step_id"] == again["step_id"]
    assert DECISION_SCHEMA in prepared["prompt"]
    stored = planner.controller.snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["status"] == "ADMITTED"
    assert stored["current_step"]["description"].startswith(PLANNER_STEP_PREFIX)
    assert stored["counters"]["steps"] == 1


def test_valid_effect_decision_becomes_exact_admitted_effect_step(db):
    goal = _goal(db)
    planner = AutonomyPlanner(db)
    planning = planner.prepare_next("gabriel")

    result = planner.ingest_reason_response(
        goal["goal_id"],
        planning["step_id"],
        _decision(
            "effect",
            "perform exact bounded noop",
            {"capability": "state.noop", "target": "planner-target", "argv": None},
        ),
        expected_generation=planning["generation"],
    )

    step = result["next_step"]
    assert step["kind"] == "effect"
    assert step["status"] == "ADMITTED"
    assert step["effect"] == {
        "capability": "state.noop",
        "target": "planner-target",
        "argv": None,
    }
    prepared = planner.prepare_next("gabriel")
    assert prepared["step_id"] == step["step_id"]
    assert prepared["mode"] == "effect"
    stored = planner.controller.snapshot(user_id="gabriel")["goals"][0]
    assert stored["counters"]["steps"] == 2
    assert stored["counters"]["effects"] == 1


def test_valid_reason_decision_preserves_typed_planner_contract_for_next_turn(db):
    goal = _goal(db)
    planner = AutonomyPlanner(db)
    first = planner.prepare_next("gabriel")

    result = planner.ingest_reason_response(
        goal["goal_id"], first["step_id"], _decision("reason", "compare two bounded alternatives")
    )

    next_step = result["next_step"]
    assert next_step["kind"] == "reason"
    assert next_step["status"] == "ADMITTED"
    assert next_step["description"] == f"{PLANNER_STEP_PREFIX} compare two bounded alternatives"
    again = planner.prepare_next("gabriel")
    assert again["step_id"] == next_step["step_id"]
    assert again["mode"] == "reason"


def test_complete_candidate_never_self_completes_user_ack_goal(db):
    goal = _goal(db)
    planner = AutonomyPlanner(db)
    planning = planner.prepare_next("gabriel")

    result = planner.ingest_reason_response(
        goal["goal_id"], planning["step_id"], _decision("complete_candidate", "candidate only")
    )

    assert result["completion"] is None
    assert result["next_step"]["kind"] == "complete_candidate"
    assert result["next_step"]["status"] == "PROPOSED"
    stored = planner.controller.snapshot(user_id="gabriel")["goals"][0]
    assert stored["status"] == "VERIFYING"


@pytest.mark.parametrize(
    "payload",
    [
        '{"schema":"ClayVerseAutonomyDecision/v1","kind":"reason","kind":"effect","description":"x","effect":null}',
        '{"schema":"ClayVerseAutonomyDecision/v1","kind":"reason","description":"x","effect":null,"extra":1}',
        '{"schema":"ClayVerseAutonomyDecision/v1","kind":"wait","description":"x","effect":null}',
        '{"schema":"ClayVerseAutonomyDecision/v1","kind":"reason","description":"x","effect":NaN}',
        '```json\n{"schema":"ClayVerseAutonomyDecision/v1","kind":"reason","description":"x","effect":null}\n```',
    ],
)
def test_invalid_planner_output_fails_current_step_without_creating_next_step(db, payload):
    goal = _goal(db)
    planner = AutonomyPlanner(db)
    planning = planner.prepare_next("gabriel")

    with pytest.raises(AutonomyDecisionError):
        planner.ingest_reason_response(goal["goal_id"], planning["step_id"], payload)

    stored = planner.controller.snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["step_id"] == planning["step_id"]
    assert stored["current_step"]["status"] == "FAILED"
    assert stored["blocked_reason"] == "invalid_autonomy_planner_decision"
    assert stored["evidence_effect_ids"] == []


def test_oversized_description_fails_before_planner_step_is_marked_success(db):
    goal = _goal(db)
    planner = AutonomyPlanner(db)
    planning = planner.prepare_next("gabriel")
    payload = _decision("reason", "x" * 9000)

    with pytest.raises(AutonomyDecisionError, match="exceeds step bound"):
        planner.ingest_reason_response(goal["goal_id"], planning["step_id"], payload)

    stored = planner.controller.snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["step_id"] == planning["step_id"]
    assert stored["current_step"]["status"] == "FAILED"


def test_prepare_reuses_failed_step_and_consumes_existing_retry_policy(db):
    goal = _goal(db, budget=GoalBudget(max_steps=3, max_retries_per_step=1, max_effects=0))
    planner = AutonomyPlanner(db)
    first = planner.prepare_next("gabriel")
    with pytest.raises(AutonomyDecisionError):
        planner.ingest_reason_response(goal["goal_id"], first["step_id"], "not-json")

    retry = planner.prepare_next("gabriel")
    assert retry["step_id"] == first["step_id"]
    stored = planner.controller.snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["attempts"] == 2
    assert stored["counters"]["steps"] == 2
