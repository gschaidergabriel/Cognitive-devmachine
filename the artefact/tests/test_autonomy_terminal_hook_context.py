from __future__ import annotations

import hashlib
import json

from clayverse.autonomy import AutonomyController
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import _autonomy_context, stop, user_prompt


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _goal(db, controller, user_id: str, objective: str):
    session_id = f"session:{user_id}"
    source_turn_id = db.append_turn(session_id, user_id, "user", objective)
    return controller.create_goal_from_turn(
        user_id,
        session_id,
        source_turn_id,
        completion_mode="user_ack",
    )


def test_autonomy_context_is_owner_scoped_and_marks_only_controller_runnable_goal(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        gabriel = _goal(db, controller, "gabriel", "gabriel-autonomy-goal")
        _goal(db, controller, "andreas", "andreas-private-autonomy-goal")

        view = _autonomy_context(db, "gabriel")
        encoded = json.dumps(view, sort_keys=True)
        assert view["authority"] == "UnifiedDB"
        assert view["scope"] == "current_user_only"
        assert view["unfinished_goal_count"] == 1
        assert view["next_runnable_goal_id"] == gabriel["goal_id"]
        assert view["head_unfinished_goal"]["runnable"] is True
        assert view["head_unfinished_goal"]["objective"]["text"] == "gabriel-autonomy-goal"
        assert "andreas-private-autonomy-goal" not in encoded
    finally:
        db.close()


def test_autonomy_context_does_not_guess_long_goal_text_or_expose_effect_intent(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        objective = "x" * 2_500
        goal = _goal(db, controller, "gabriel", objective)
        controller.propose_step(
            goal["goal_id"],
            "effect",
            "execute only through the admitted effect path",
            effect={"capability": "state.noop", "target": "secret-effect-target", "argv": None},
        )

        view = _autonomy_context(db, "gabriel")
        head = view["head_unfinished_goal"]
        assert head["objective"]["inline"] is False
        assert head["objective"]["text"] is None
        assert head["objective"]["sha256"] == hashlib.sha256(objective.encode()).hexdigest()
        assert head["current_step"]["effect_capability"] == "state.noop"
        assert head["current_step"]["effect_intent_redacted_from_hook"] is True
        assert "secret-effect-target" not in json.dumps(view, sort_keys=True)
    finally:
        db.close()


def test_restart_ambiguous_effect_is_visible_but_never_marked_runnable(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        goal = _goal(db, controller, "gabriel", "continue safely after restart")
        step = controller.propose_step(
            goal["goal_id"],
            "effect",
            "one effect was interrupted by restart",
            effect={"capability": "state.noop", "target": "must-not-replay", "argv": None},
        )
        controller.admit_step(goal["goal_id"], step["step_id"])
        live = db.advance_entity_generation()
        result = controller.recover_generation(expected_generation=live)
        assert result["ambiguous_effect_blocked"] == 1

        view = _autonomy_context(db, "gabriel")
        head = view["head_unfinished_goal"]
        assert view["next_runnable_goal_id"] is None
        assert head["status"] == "BLOCKED"
        assert head["runnable"] is False
        assert head["blocked_reason"] == "unknown_effect_after_generation_change"
        assert "must-not-replay" not in json.dumps(view, sort_keys=True)
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
    finally:
        db.close()


def test_user_prompt_injects_canonical_autonomy_view_without_new_effect_authority(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")

    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        goal = _goal(db, controller, "gabriel", "resume this canonical bounded goal")
    finally:
        db.close()

    submitted = user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-autonomy-context",
        "prompt": "current interactive prompt",
    })
    rendered = submitted["hookSpecificOutput"]["additionalContext"]
    payload = json.loads(rendered.split("\n", 1)[1])
    autonomy = payload["autonomy"]
    assert autonomy["authority"] == "UnifiedDB"
    assert autonomy["model_authority"] == "PROPOSAL_ONLY"
    assert autonomy["completion_authority"] == "AutonomyController"
    assert autonomy["next_runnable_goal_id"] == goal["goal_id"]
    assert autonomy["head_unfinished_goal"]["runnable"] is True
    assert autonomy["head_unfinished_goal"]["objective"]["text"] == "resume this canonical bounded goal"
    assert "mcp__clayverse__request_effect" in autonomy["law"]

    stopped = stop({
        "hook_event_name": "Stop",
        "session_id": "claude-autonomy-context",
        "last_assistant_message": "bounded context observed",
    })
    assert stopped["suppressOutput"] is True
