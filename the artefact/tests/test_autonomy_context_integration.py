from __future__ import annotations

import json

import pytest

import clayverse.terminal_hooks as terminal_hooks
from clayverse.autonomy import AutonomyController, AutonomyStateError
from clayverse.autonomy_context import bounded_autonomy_context
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import HOOK_CONTEXT_MAX_CHARS, _bounded_hook_context
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db


def _goal(db, controller, user_id: str, objective: str):
    session_id = f"session:{user_id}"
    turn_id = db.append_turn(session_id, user_id, "user", objective)
    return controller.create_goal_from_turn(user_id, session_id, turn_id, completion_mode="user_ack")


def test_autonomy_context_is_user_scoped_and_hides_effect_payload(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    gabriel = _goal(db, controller, "gabriel", "Gabriel bounded goal")
    andreas = _goal(db, controller, "andreas", "Andreas private goal")
    step = controller.propose_step(
        gabriel["goal_id"],
        "effect",
        "Execute admitted operation",
        effect={"capability": "entityos.exec", "target": "do-not-prompt-target-secret", "argv": ["do-not-prompt-argv-secret"]},
    )
    context = bounded_autonomy_context(db, "gabriel")
    encoded = str(context)
    assert context["authority"] == "UnifiedDB"
    assert context["model_authority"] == "PROPOSAL_ONLY"
    assert context["user_id"] == "gabriel"
    assert context["attention_goal_count"] == 1
    assert context["goals"][0]["goal_id"] == gabriel["goal_id"]
    assert context["goals"][0]["current_step"]["step_id"] == step["step_id"]
    assert context["goals"][0]["current_step"]["effect_capability"] == "entityos.exec"
    assert andreas["goal_id"] not in encoded
    assert "Andreas private goal" not in encoded
    assert "do-not-prompt-target-secret" not in encoded
    assert "do-not-prompt-argv-secret" not in encoded


def test_autonomy_context_rejects_noncanonical_identity(tmp_path):
    db = _db(tmp_path)
    with pytest.raises(PermissionError):
        bounded_autonomy_context(db, "not-a-canonical-user")


def test_terminal_goals_do_not_consume_attention_context(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller, "gabriel", "Already terminal goal")
    controller.cancel_goal(goal["goal_id"])
    context = bounded_autonomy_context(db, "gabriel")
    assert context["attention_goal_count"] == 0
    assert context["goals"] == []


def test_autonomy_context_reads_inside_existing_transaction(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller, "gabriel", "Atomic hook-visible goal")
    with db.tx():
        context = bounded_autonomy_context(db, "gabriel")
        assert context["goals"][0]["goal_id"] == goal["goal_id"]
        assert db.db.in_transaction is True


def test_autonomy_context_is_deterministically_bounded(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    for index in range(7):
        _goal(db, controller, "gabriel", f"goal-{index}:" + ("x" * 10_000))
    context = bounded_autonomy_context(db, "gabriel", max_chars=1_400, max_goals=3)
    encoded = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert len(encoded) <= 1_400
    assert context["attention_goal_count"] == 7
    assert context["included_goal_count"] <= 3
    assert context["omitted_goal_count"] == 7 - context["included_goal_count"]


def test_hook_context_contains_autonomy_inside_existing_inline_budget(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _goal(db, controller, "gabriel", "Continue canonical autonomous work")
    autonomy = bounded_autonomy_context(db, "gabriel")
    result = {
        "user_id": "gabriel", "session_id": "session:gabriel", "turn_id": "turn-1",
        "episode_id": "episode-1", "causal_id": "causal-1", "generation": 1,
        "resources": [], "workspace": {"salience": 0.2, "alternatives": []}, "needle": {},
        "hyperpositions": [],
        "context": {"durable_memory": [], "cross_session_collision": [], "own_recent": []},
        "autonomy": autonomy,
    }
    rendered = _bounded_hook_context(result)
    assert len(rendered) <= HOOK_CONTEXT_MAX_CHARS
    assert '"autonomy":' in rendered
    assert '"model_authority":"PROPOSAL_ONLY"' in rendered
    assert "Continue canonical autonomous work" in rendered


def test_invalid_autonomy_state_rolls_back_user_prompt_admission(tmp_path, monkeypatch):
    db = _db(tmp_path)
    db.db.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ("autonomy_state_v1", '{"schema":"corrupt"}'),
    )
    db.db.commit()
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=None)
    monkeypatch.setattr(terminal_hooks, "_runtime", lambda: (db, "gabriel", "session:gabriel", lifecycle))
    with pytest.raises(AutonomyStateError):
        terminal_hooks.user_prompt({
            "hook_event_name": "UserPromptSubmit",
            "prompt": "this turn must not survive missing trusted context",
            "session_id": "claude-session-test",
        })
    check = UnifiedDB(tmp_path / "unified.db")
    assert check.db.execute("SELECT 1 FROM turns WHERE content=?", ("this turn must not survive missing trusted context",)).fetchone() is None
    assert check.db.execute("SELECT 1 FROM active_turns WHERE session_id=?", ("session:gabriel",)).fetchone() is None
    check.close()


def test_read_state_mcp_exposes_the_same_user_scoped_projection(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    gabriel = _goal(db, controller, "gabriel", "Gabriel MCP-visible goal")
    andreas = _goal(db, controller, "andreas", "Andreas MCP-private goal")
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=None)
    bridge = ClayVerseEffectBridge(lifecycle)
    state = bridge.session_state()
    encoded = str(state["autonomy"])
    assert state["autonomy"]["goals"][0]["goal_id"] == gabriel["goal_id"]
    assert andreas["goal_id"] not in encoded
    assert "Andreas MCP-private goal" not in encoded
