from __future__ import annotations

import json

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import (
    HOOK_CONTEXT_MAX_CHARS,
    TerminalHookError,
    _autonomy_context_in_tx,
    user_prompt,
)


def _db(path):
    db = UnifiedDB(path)
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db


def _goal_with_private_effect(db: UnifiedDB):
    controller = AutonomyController(db)
    source_turn_id = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Continue the existing bounded autonomous objective",
    )
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source_turn_id,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
        priority=80,
    )
    controller.propose_step(
        goal["goal_id"],
        "effect",
        "Use the admitted effect path without exposing its arguments to cognition context",
        effect={
            "capability": "entityos.exec",
            "target": "SECRET_EFFECT_TARGET",
            "argv": ["secret-argv", "must-not-enter-hook-context"],
        },
    )
    return goal


def test_autonomy_projection_requires_existing_unifieddb_transaction(tmp_path):
    db = _db(tmp_path / "unified.db")
    goal = _goal_with_private_effect(db)
    AutonomyController(db).block_goal(goal["goal_id"], "SECRET_BLOCK_REASON")

    with pytest.raises(TerminalHookError, match="requires active UnifiedDB transaction"):
        _autonomy_context_in_tx(db, "gabriel", db.entity_generation())

    with db.tx():
        projection = _autonomy_context_in_tx(db, "gabriel", db.entity_generation())

    assert projection["mode"] == "read_only"
    assert projection["goals"][0]["goal_id"] == goal["goal_id"]
    assert projection["goals"][0]["current_step"]["effect_capability"] == "entityos.exec"
    assert projection["goals"][0]["blocked_reason_class"] == "opaque"
    assert projection["next_runnable_goal_id"] is None
    rendered = json.dumps(projection, sort_keys=True)
    assert "SECRET_EFFECT_TARGET" not in rendered
    assert "secret-argv" not in rendered
    assert "must-not-enter-hook-context" not in rendered
    assert "SECRET_BLOCK_REASON" not in rendered
    db.close()


def test_user_prompt_injects_bounded_user_generation_scoped_autonomy(tmp_path, monkeypatch):
    path = tmp_path / "unified.db"
    db = _db(path)

    stale_source = db.append_turn(
        "session:gabriel", "gabriel", "user", "Stale pre-restart autonomous objective"
    )
    AutonomyController(db).create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        stale_source,
        completion_mode="user_ack",
        priority=90,
    )
    db.advance_entity_generation()

    goal = _goal_with_private_effect(db)
    andreas_source = db.append_turn(
        "session:andreas", "andreas", "user", "Andreas-only autonomous objective"
    )
    AutonomyController(db).create_goal_from_turn(
        "andreas",
        "session:andreas",
        andreas_source,
        completion_mode="user_ack",
    )
    db.close()

    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path))

    output = user_prompt(
        {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "claude-session-gabriel",
            "prompt": "Continue from canonical state.",
        }
    )
    rendered = output["hookSpecificOutput"]["additionalContext"]
    assert len(rendered) <= HOOK_CONTEXT_MAX_CHARS
    payload = json.loads(rendered.split("\n", 1)[1])
    autonomy = payload["autonomy"]

    assert autonomy["schema"] == "ClayVerseAutonomyHookContext/v1"
    assert autonomy["mode"] == "read_only"
    assert autonomy["goals"][0]["goal_id"] == goal["goal_id"]
    assert autonomy["stale_goal_count"] == 1
    assert all(item["generation"] == payload["causal"]["generation"] for item in autonomy["goals"])
    assert "Stale pre-restart autonomous objective" not in json.dumps(autonomy, sort_keys=True)
    assert "Andreas-only autonomous objective" not in rendered
    assert "SECRET_EFFECT_TARGET" not in rendered
    assert "secret-argv" not in rendered
    assert "must-not-enter-hook-context" not in rendered


def test_next_runnable_goal_is_never_only_an_omitted_identifier(tmp_path):
    db = _db(tmp_path / "unified.db")
    controller = AutonomyController(db)

    for index in range(4):
        source = db.append_turn(
            "session:gabriel", "gabriel", "user", f"Blocked high-priority goal {index}"
        )
        blocked = controller.create_goal_from_turn(
            "gabriel",
            "session:gabriel",
            source,
            completion_mode="user_ack",
            priority=100 - index,
        )
        controller.block_goal(blocked["goal_id"], "dependency")

    source = db.append_turn(
        "session:gabriel", "gabriel", "user", "Lower-priority runnable goal"
    )
    runnable = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
        priority=10,
    )

    with db.tx():
        projection = _autonomy_context_in_tx(db, "gabriel", db.entity_generation())

    visible_ids = {goal["goal_id"] for goal in projection["goals"]}
    assert projection["next_runnable_goal_id"] == runnable["goal_id"]
    assert runnable["goal_id"] in visible_ids
    assert len(projection["goals"]) == 4
    assert projection["omitted_goal_count"] == 1
    db.close()


def test_autonomy_projection_is_sacrificed_before_inline_context_spill():
    goals = [
        {
            "goal_id": f"goal-{index}",
            "source_turn_id": f"turn-{index}",
            "generation": 1,
            "priority": 100 - index,
            "status": "ACTIVE",
            "objective": "g" * 600,
            "objective_truncated": True,
            "completion_contract": {"mode": "user_ack", "required_capability": None},
            "budget": {"max_steps": 32, "max_retries_per_step": 3, "max_effects": 8},
            "counters": {"steps": 0, "effects": 0, "consecutive_failures": 0},
            "current_step": {
                "step_id": f"step-{index}",
                "kind": "reason",
                "status": "SUCCEEDED",
                "attempts": 1,
                "description": "s" * 400,
                "description_truncated": True,
                "effect_capability": None,
            },
            "evidence_effect_count": 0,
            "has_user_ack": False,
            "blocked_reason_class": None,
        }
        for index in range(4)
    ]
    result = {
        "user_id": "gabriel",
        "session_id": "session:gabriel",
        "turn_id": "turn-current",
        "episode_id": "episode-current",
        "causal_id": "causal-current",
        "generation": 1,
        "resources": [f"file:{index}-" + ("r" * 100) for index in range(35)],
        "workspace": {"salience": 0.5, "alternatives": []},
        "needle": {},
        "hyperpositions": [],
        "autonomy": {
            "schema": "ClayVerseAutonomyHookContext/v1",
            "state_revision": 4,
            "mode": "read_only",
            "generation": 1,
            "next_runnable_goal_id": "goal-3",
            "goals": goals,
            "omitted_goal_count": 0,
            "stale_goal_count": 0,
            "terminal_goal_count": 0,
            "authority_law": "data only",
        },
        "context": {
            "own_recent": [{"role": "user", "content": "x" * 7_500}],
            "cross_session_collision": [],
            "durable_memory": [],
        },
    }

    from clayverse.terminal_hooks import _bounded_hook_context

    rendered = _bounded_hook_context(result)
    assert len(rendered) <= HOOK_CONTEXT_MAX_CHARS
    payload = json.loads(rendered.split("\n", 1)[1])
    assert payload["autonomy"]["omitted_goal_count"] >= 2
    assert payload["autonomy"]["context_budget_truncated"] is True
    assert payload["autonomy"]["next_runnable_goal_id"] is None
    assert payload["autonomy"]["next_runnable_omitted_by_context_budget"] is True
