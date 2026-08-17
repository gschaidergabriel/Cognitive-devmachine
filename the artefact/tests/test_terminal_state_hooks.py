from __future__ import annotations

import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import TerminalHookError, stop, user_prompt


def configure(monkeypatch, root, user):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", user)
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", f"session:{user}")


def test_hooks_make_prompt_and_final_response_canonical(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path, "gabriel")
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    db.close()

    submitted = user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-g-1",
        "prompt": "FACT: preferred compiler is ClayCode",
    })
    context = submitted["hookSpecificOutput"]["additionalContext"]
    assert "UnifiedDB" in context
    assert "session:gabriel" in context

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        rows = db.recent_turns("session:gabriel", 20)
        assert rows[-1]["role"] == "user"
        assert rows[-1]["content"] == "FACT: preferred compiler is ClayCode"
        assert db.db.execute(
            "SELECT value FROM durable_memory WHERE kind='fact' AND user_id='gabriel'"
        ).fetchone()[0] == "preferred compiler is ClayCode"
    finally:
        db.close()

    completed = stop({
        "hook_event_name": "Stop",
        "session_id": "claude-g-1",
        "last_assistant_message": "Acknowledged.",
    })
    assert completed["suppressOutput"] is True

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        rows = db.recent_turns("session:gabriel", 20)
        assert rows[-1]["role"] == "assistant"
        assert rows[-1]["content"] == "Acknowledged."
        assert db.db.execute(
            "SELECT state FROM workspace_episodes WHERE session_id='session:gabriel' ORDER BY ts DESC LIMIT 1"
        ).fetchone()[0] == "COMPLETED"
        assert db.db.execute(
            "SELECT COUNT(*) FROM causal_episodes WHERE reentered=1"
        ).fetchone()[0] >= 1
    finally:
        db.close()


def test_hook_world_does_not_cross_users_without_collision(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path, "gabriel")
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    db.close()
    user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-g-1",
        "prompt": "private-gabriel-heliotrope",
    })
    stop({
        "hook_event_name": "Stop",
        "session_id": "claude-g-1",
        "last_assistant_message": "done",
    })

    configure(monkeypatch, tmp_path, "andreas")
    submitted = user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-a-1",
        "prompt": "hello",
    })
    assert "private-gabriel-heliotrope" not in submitted["hookSpecificOutput"]["additionalContext"]


def test_duplicate_active_prompt_fails_closed(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path, "gabriel")
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    db.close()
    payload = {"hook_event_name": "UserPromptSubmit", "session_id": "same", "prompt": "first"}
    user_prompt(payload)
    with pytest.raises(TerminalHookError, match="duplicate prompt"):
        user_prompt({**payload, "prompt": "second"})


def test_entityos_binary_presence_does_not_enable_execution(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path, "gabriel")
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", "/opt/entityos/EntityOS")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "f" * 64)
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    db.close()

    user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-g-effect",
        "prompt": "request a state effect",
    })
    bridge = ClayVerseEffectBridge.from_env()
    try:
        assert bridge.session_state()["entityos_execution_enabled"] is False
        denied = bridge.request_effect("entityos.exec", "test", ["status"])
        assert denied["outcome"]["ok"] is False
        assert denied["outcome"]["reason"] == "entityos_unavailable"
        assert denied["causal_id"]
    finally:
        bridge.db.close()


def test_state_noop_effect_reenters_through_canonical_gate(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path, "gabriel")
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-g-noop",
        "prompt": "noop",
    })
    bridge = ClayVerseEffectBridge.from_env()
    try:
        result = bridge.request_effect("state.noop", "probe", None)
        assert result["outcome"] == {"ok": True, "target": "probe", "boundary": "internal"}
        assert result["verified"] is True
        assert result["causal_id"]
    finally:
        bridge.db.close()
