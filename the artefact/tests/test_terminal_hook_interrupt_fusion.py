import io

import pytest

import clayverse.terminal_hooks as terminal_hooks
from clayverse.store import UnifiedDB


def configure(monkeypatch, tmp_path):
    root = tmp_path / "state"
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")
    return root


def test_failed_successor_context_preserves_prior_active_turn(monkeypatch, tmp_path):
    root = configure(monkeypatch, tmp_path)
    terminal_hooks.user_prompt({"hook_event_name": "UserPromptSubmit", "session_id": "claude-shared", "prompt": "first"})
    db = UnifiedDB(root / "unified.db")
    prior_turn = db.db.execute("SELECT turn_id FROM active_turns WHERE session_id='session:gabriel'").fetchone()[0]
    db.close()

    def reject_context(result):
        raise terminal_hooks.TerminalHookError("bounded context rejected")

    monkeypatch.setattr(terminal_hooks, "_bounded_hook_context", reject_context)
    with pytest.raises(terminal_hooks.TerminalHookError, match="bounded context rejected"):
        terminal_hooks.user_prompt({"hook_event_name": "UserPromptSubmit", "session_id": "claude-shared", "prompt": "second"})

    db = UnifiedDB(root / "unified.db")
    try:
        active = db.db.execute("SELECT turn_id FROM active_turns WHERE session_id='session:gabriel'").fetchone()[0]
        assert active == prior_turn
        assert [row["role"] for row in db.all_turns("session:gabriel")] == ["user"]
        assert db.db.execute("SELECT state FROM workspace_episodes WHERE observation_turn_id=?", (prior_turn,)).fetchone()[0] == "OPEN"
    finally:
        db.close()


def test_same_session_interrupt_commits_abort_then_successor(monkeypatch, tmp_path):
    root = configure(monkeypatch, tmp_path)
    terminal_hooks.user_prompt({"hook_event_name": "UserPromptSubmit", "session_id": "claude-shared", "prompt": "first"})
    terminal_hooks.user_prompt({"hook_event_name": "UserPromptSubmit", "session_id": "claude-shared", "prompt": "second"})

    db = UnifiedDB(root / "unified.db")
    try:
        turns = db.all_turns("session:gabriel")
        assert [row["role"] for row in turns] == ["user", "system", "user"]
        assert turns[1]["content"].startswith("TURN_ABORTED:previous_turn_interrupted_before_next_prompt")
        states = [row["state"] for row in db.db.execute("SELECT state FROM workspace_episodes ORDER BY ts,episode_id")]
        assert states == ["ABORTED", "OPEN"]
        assert db.db.execute("SELECT COUNT(*) FROM active_turns WHERE session_id='session:gabriel'").fetchone()[0] == 1
        assert db.db.execute("SELECT COUNT(*) FROM causal_episodes WHERE reentered=1").fetchone()[0] == 1
    finally:
        db.close()


def test_reentered_stop_failure_terminates_hook_loop(monkeypatch):
    def fail_stop(payload):
        raise RuntimeError("persistent store failure")

    monkeypatch.setattr(terminal_hooks, "stop", fail_stop)
    monkeypatch.setattr(terminal_hooks.sys, "argv", ["terminal_hooks", "stop"])
    monkeypatch.setattr(terminal_hooks.sys, "stdin", io.StringIO('{"hook_event_name":"Stop","stop_hook_active":false}'))
    assert terminal_hooks._main() == 2
    monkeypatch.setattr(terminal_hooks.sys, "stdin", io.StringIO('{"hook_event_name":"Stop","stop_hook_active":true}'))
    assert terminal_hooks._main() == 0
