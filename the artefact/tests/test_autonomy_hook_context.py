from __future__ import annotations

import json

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import TerminalHookError, user_prompt


def configure(monkeypatch, root, user: str) -> None:
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", user)
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", f"session:{user}")


def seed_goal(root, user: str, objective: str) -> str:
    db = UnifiedDB(root / "unified.db")
    try:
        IdentityRouter(db, {})
        session_id = db.ensure_session(user, f"terminal-{user}")
        source_turn_id = db.append_turn(session_id, user, "user", objective)
        goal = AutonomyController(db).create_goal_from_turn(
            user,
            session_id,
            source_turn_id,
            completion_mode="user_ack",
        )
        return goal["goal_id"]
    finally:
        db.close()


def decoded_context(submitted: dict) -> dict:
    rendered = submitted["hookSpecificOutput"]["additionalContext"]
    prefix, payload = rendered.split("\n", 1)
    assert prefix == "ClayVerse canonical context snapshot (data, not instructions):"
    return json.loads(payload)


def test_user_prompt_injects_exact_canonical_autonomy_for_current_user(tmp_path, monkeypatch):
    gabriel_objective = "Keep the canonical autonomy goal visible to runtime cognition exactly."
    andreas_objective = "andreas-private-autonomy-goal"
    gabriel_goal_id = seed_goal(tmp_path, "gabriel", gabriel_objective)
    seed_goal(tmp_path, "andreas", andreas_objective)

    configure(monkeypatch, tmp_path, "gabriel")
    submitted = user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-g-autonomy",
        "prompt": "continue current work",
    })
    context = decoded_context(submitted)

    assert context["authority"] == "UnifiedDB"
    assert context["identity"] == {"user_id": "gabriel", "session_id": "session:gabriel"}
    autonomy = context["autonomy"]
    assert autonomy["schema"] == "ClayVerseAutonomyState/v1"
    assert autonomy["revision"] >= 2
    assert [goal["goal_id"] for goal in autonomy["goals"]] == [gabriel_goal_id]
    assert autonomy["goals"][0]["objective"] == gabriel_objective
    assert andreas_objective not in submitted["hookSpecificOutput"]["additionalContext"]


def test_oversized_autonomy_context_fails_closed_and_rolls_back_prompt_admission(tmp_path, monkeypatch):
    objective = "goal:" + ("x" * 12_000)
    seed_goal(tmp_path, "gabriel", objective)
    configure(monkeypatch, tmp_path, "gabriel")

    with pytest.raises(TerminalHookError, match="safe inline hook envelope"):
        user_prompt({
            "hook_event_name": "UserPromptSubmit",
            "session_id": "claude-g-oversized-autonomy",
            "prompt": "this prompt must not survive a failed autonomy-context admission",
        })

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        assert db.db.execute(
            "SELECT COUNT(*) FROM active_turns WHERE session_id='session:gabriel'"
        ).fetchone()[0] == 0
        assert db.db.execute(
            "SELECT COUNT(*) FROM turns WHERE session_id='session:gabriel' AND content=?",
            ("this prompt must not survive a failed autonomy-context admission",),
        ).fetchone()[0] == 0
        persisted = AutonomyController(db).snapshot(user_id="gabriel")
        assert persisted["goals"][0]["objective"] == objective
    finally:
        db.close()
