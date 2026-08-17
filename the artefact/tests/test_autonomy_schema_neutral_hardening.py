from __future__ import annotations

import json

import pytest

from clayverse.autonomy import (
    AutonomyBudgetExceeded,
    AutonomyController,
    CompletionNotVerified,
    GoalBudget,
)
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db


def test_zero_effect_budget_still_allows_reasoning_but_denies_effects(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source = db.append_turn("session:gabriel", "gabriel", "user", "Reason without effects")
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
        budget=GoalBudget(max_steps=3, max_retries_per_step=1, max_effects=0),
    )

    reason = controller.propose_step(goal["goal_id"], "reason", "Inspect canonical state")
    controller.admit_step(goal["goal_id"], reason["step_id"])
    controller.record_reason_success(goal["goal_id"], reason["step_id"])

    with pytest.raises(AutonomyBudgetExceeded, match="effect budget exhausted"):
        controller.propose_step(
            goal["goal_id"],
            "effect",
            "No effects are admitted for this goal",
            effect={"capability": "state.noop", "target": "denied-by-budget", "argv": None},
        )

    snapshot = controller.snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["counters"]["steps"] == 1
    assert snapshot["counters"]["effects"] == 0
    assert snapshot["status"] == "ACTIVE"


def test_goal_source_turn_cannot_acknowledge_itself(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source = db.append_turn("session:gabriel", "gabriel", "user", "Prepare a report")
    goal = controller.create_goal_from_turn(
        "gabriel", "session:gabriel", source, completion_mode="user_ack"
    )

    with pytest.raises(PermissionError, match="explicit later owner turn"):
        controller.acknowledge_by_user(goal["goal_id"], source)

    later = db.append_turn("session:gabriel", "gabriel", "user", "I confirm it is complete")
    controller.acknowledge_by_user(goal["goal_id"], later)
    assert controller.verify_completion(goal["goal_id"])["evidence"] == later


def test_completion_revalidates_persisted_user_ack_provenance(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source = db.append_turn("session:gabriel", "gabriel", "user", "Prepare a report")
    goal = controller.create_goal_from_turn(
        "gabriel", "session:gabriel", source, completion_mode="user_ack"
    )

    raw = db.db.execute(
        "SELECT value FROM meta WHERE key='autonomy_state_v1'"
    ).fetchone()[0]
    state = json.loads(raw)
    state["goals"][goal["goal_id"]]["user_ack_turn_id"] = source
    db.db.execute(
        "UPDATE meta SET value=? WHERE key='autonomy_state_v1'",
        (json.dumps(state, sort_keys=True, separators=(",", ":")),),
    )

    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])
