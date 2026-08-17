import pytest

import clayverse.terminal_hooks as terminal_hooks
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.workspace import Workspace


def _env(monkeypatch, tmp_path):
    root = tmp_path / "state"
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")
    return root


def _fail_context(*args, **kwargs):
    raise terminal_hooks.TerminalHookError("injected context failure")


def test_user_prompt_failure_rolls_back_turn_memory_and_workspace(monkeypatch, tmp_path):
    root = _env(monkeypatch, tmp_path)
    monkeypatch.setattr(terminal_hooks, "_bounded_context", _fail_context)

    with pytest.raises(terminal_hooks.TerminalHookError, match="injected context failure"):
        terminal_hooks.user_prompt({
            "hook_event_name": "UserPromptSubmit",
            "session_id": "claude-session-new",
            "prompt": "FACT: this must not survive a blocked prompt",
        })

    db = UnifiedDB(root / "unified.db")
    try:
        assert db.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM workspace_episodes").fetchone()[0] == 0
    finally:
        db.close()


def test_failed_new_prompt_does_not_retire_prior_open_episode(monkeypatch, tmp_path):
    root = _env(monkeypatch, tmp_path)
    db = UnifiedDB(root / "unified.db")
    IdentityRouter(db, {})
    session_id = db.ensure_session("gabriel", "terminal-gabriel")
    turn_id = db.append_turn(
        session_id,
        "gabriel",
        "user",
        "prior prompt",
        provenance={"claude_session_id": "claude-session-prior", "session_generation": 1},
    )
    prior = Workspace(db).open(session_id, turn_id, "prior prompt", [])
    db.close()

    monkeypatch.setattr(terminal_hooks, "_bounded_context", _fail_context)
    with pytest.raises(terminal_hooks.TerminalHookError, match="injected context failure"):
        terminal_hooks.user_prompt({
            "hook_event_name": "UserPromptSubmit",
            "session_id": "claude-session-new",
            "prompt": "new prompt that Claude will reject",
        })

    db = UnifiedDB(root / "unified.db")
    try:
        state = db.db.execute(
            "SELECT state FROM workspace_episodes WHERE episode_id=?", (prior["episode_id"],)
        ).fetchone()[0]
        assert state == "OPEN"
        assert db.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0] == 1
        assert db.db.execute("SELECT COUNT(*) FROM workspace_episodes").fetchone()[0] == 1
    finally:
        db.close()


def test_append_turn_in_tx_refuses_ambient_autocommit(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    session_id = db.ensure_session("gabriel", "terminal-gabriel")
    try:
        with pytest.raises(RuntimeError, match="requires an active transaction"):
            db.append_turn_in_tx(session_id, "gabriel", "user", "not atomic")
        assert db.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0] == 0
    finally:
        db.close()
