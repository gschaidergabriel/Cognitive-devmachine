from __future__ import annotations

import json

from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import stop, stop_failure, user_prompt


def _configure(monkeypatch, root, user="gabriel"):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", user)
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", f"session:{user}")
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    db = UnifiedDB(root / "unified.db")
    IdentityRouter(db, {})
    db.close()


def test_hook_effect_stop_share_one_active_turn_and_terminal_workspace(tmp_path, monkeypatch):
    _configure(monkeypatch, tmp_path)
    user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-session-A",
        "prompt": "run one bounded state effect",
    })

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        active = db.db.execute(
            "SELECT turn_id,episode_id,causal_id FROM active_turns WHERE session_id='session:gabriel'"
        ).fetchone()
        assert active is not None
        provenance = json.loads(db.db.execute(
            "SELECT provenance FROM turns WHERE turn_id=?", (active["turn_id"],)
        ).fetchone()[0])
        assert provenance["claude_session_id"] == "claude-session-A"
        assert provenance["causal_id"] == active["causal_id"]
        assert db.db.execute(
            "SELECT state FROM workspace_episodes WHERE episode_id=?", (active["episode_id"],)
        ).fetchone()[0] == "OPEN"
        causal_id = active["causal_id"]
        episode_id = active["episode_id"]
    finally:
        db.close()

    bridge = ClayVerseEffectBridge.from_env()
    try:
        result = bridge.request_effect("state.noop", "checkpoint", None)
        assert result["verified"] is True
        assert result["causal_id"] == causal_id
        effect_id = result["effect_id"]
    finally:
        bridge.db.close()

    stop({
        "hook_event_name": "Stop",
        "session_id": "claude-session-A",
        "last_assistant_message": "done",
    })

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        assert db.db.execute(
            "SELECT COUNT(*) FROM active_turns WHERE session_id='session:gabriel'"
        ).fetchone()[0] == 0
        assert db.db.execute(
            "SELECT state FROM workspace_episodes WHERE episode_id=?", (episode_id,)
        ).fetchone()[0] == "COMPLETED"
        causal = db.db.execute(
            "SELECT causal_id,effect_id,reentered FROM causal_episodes WHERE episode_id=?", (episode_id,)
        ).fetchone()
        assert tuple(causal) == (causal_id, effect_id, 1)
        assistant = db.db.execute(
            "SELECT causal_refs FROM turns WHERE session_id='session:gabriel' AND role='assistant' ORDER BY ordinal DESC LIMIT 1"
        ).fetchone()
        assert json.loads(assistant[0]) == [effect_id]
    finally:
        db.close()


def test_stop_failure_retires_active_turn_as_failed(tmp_path, monkeypatch):
    _configure(monkeypatch, tmp_path)
    user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-session-fail",
        "prompt": "begin then fail",
    })
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        episode_id = db.db.execute(
            "SELECT episode_id FROM active_turns WHERE session_id='session:gabriel'"
        ).fetchone()[0]
    finally:
        db.close()

    stop_failure({
        "hook_event_name": "StopFailure",
        "session_id": "claude-session-fail",
        "error": "provider interrupted",
    })

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
        assert db.db.execute(
            "SELECT state FROM workspace_episodes WHERE episode_id=?", (episode_id,)
        ).fetchone()[0] == "FAILED"
        assert db.db.execute(
            "SELECT COUNT(*) FROM causal_episodes WHERE episode_id=? AND reentered=1", (episode_id,)
        ).fetchone()[0] == 1
    finally:
        db.close()
