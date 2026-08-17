from __future__ import annotations

import json

from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import stop, user_prompt


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


def test_fresh_claude_session_rehydrates_canonical_unifieddb_context(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path, "gabriel")
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    db.close()

    user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-before-restart",
        "prompt": "FACT: restart continuity marker is heliotrope-731",
    })
    stop({
        "hook_event_name": "Stop",
        "session_id": "claude-before-restart",
        "last_assistant_message": "stored centrally",
    })

    submitted = user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-after-restart",
        "prompt": "What continuity marker do we already know?",
    })
    context = submitted["hookSpecificOutput"]["additionalContext"]
    assert "UnifiedDB" in context
    assert "heliotrope-731" in context
    assert "session:gabriel" in context


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


def test_new_prompt_recovers_interrupted_same_claude_session_atomically(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path, "gabriel")
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    db.close()

    user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "same-claude-session",
        "prompt": "first prompt before Ctrl-C",
    })
    submitted = user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "same-claude-session",
        "prompt": "second prompt after Ctrl-C",
    })
    assert "session:gabriel" in submitted["hookSpecificOutput"]["additionalContext"]

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        turns = [dict(row) for row in db.recent_turns("session:gabriel", 20)]
        assert [row["role"] for row in turns[-3:]] == ["user", "system", "user"]
        assert turns[-2]["content"] == "TURN_ABORTED:previous_turn_interrupted_before_next_prompt"
        states = db.db.execute(
            "SELECT state FROM workspace_episodes WHERE session_id='session:gabriel' ORDER BY ts"
        ).fetchall()
        assert [row["state"] for row in states] == ["ABORTED", "OPEN"]
        active = db.db.execute(
            "SELECT a.turn_id,t.content,t.provenance FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id WHERE a.session_id='session:gabriel'"
        ).fetchone()
        assert active is not None
        assert active["content"] == "second prompt after Ctrl-C"
        assert json.loads(active["provenance"])["claude_session_id"] == "same-claude-session"
        assert db.db.execute("SELECT COUNT(*) FROM causal_episodes WHERE reentered=1").fetchone()[0] == 1
    finally:
        db.close()

    stop({
        "hook_event_name": "Stop",
        "session_id": "same-claude-session",
        "last_assistant_message": "recovered",
    })
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        states = db.db.execute(
            "SELECT state FROM workspace_episodes WHERE session_id='session:gabriel' ORDER BY ts"
        ).fetchall()
        assert [row["state"] for row in states] == ["ABORTED", "COMPLETED"]
        assert db.db.execute("SELECT COUNT(*) FROM active_turns WHERE session_id='session:gabriel'").fetchone()[0] == 0
    finally:
        db.close()


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
