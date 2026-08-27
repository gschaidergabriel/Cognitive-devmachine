import json

import pytest

import clayverse.terminal_hooks as terminal_hooks
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _terminal_env(monkeypatch, tmp_path):
    root = tmp_path / "state"
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")
    return root


def _counts(db):
    return {
        table: db.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("turns", "durable_memory", "workspace_episodes", "active_turns")
    }


def test_user_prompt_context_failure_rolls_back_complete_admission(monkeypatch, tmp_path):
    root = _terminal_env(monkeypatch, tmp_path)

    def reject_context(result):
        raise terminal_hooks.TerminalHookError("injected bounded-context rejection")

    monkeypatch.setattr(terminal_hooks, "_bounded_hook_context", reject_context)
    with pytest.raises(terminal_hooks.TerminalHookError, match="injected bounded-context rejection"):
        terminal_hooks.user_prompt({
            "hook_event_name": "UserPromptSubmit",
            "session_id": "claude-session-atomic",
            "prompt": "FACT: must not survive a hook-rejected prompt",
        })

    db = UnifiedDB(root / "unified.db")
    try:
        assert _counts(db) == {
            "turns": 0,
            "durable_memory": 0,
            "workspace_episodes": 0,
            "active_turns": 0,
        }
    finally:
        db.close()


def test_begin_admission_rolls_back_if_world_assembly_fails(monkeypatch, tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    session_id = db.ensure_session("gabriel", "terminal-gabriel")
    lifecycle = TurnLifecycle(db, "gabriel", session_id)

    def fail_world(*args, **kwargs):
        raise RuntimeError("injected world failure")

    monkeypatch.setattr(lifecycle.world, "assemble", fail_world)
    try:
        with pytest.raises(RuntimeError, match="injected world failure"):
            with lifecycle.begin_admission(
                "FACT: this memory must roll back too",
                claude_session_id="claude-session-world-fail",
            ):
                pass
        assert _counts(db) == {
            "turns": 0,
            "durable_memory": 0,
            "workspace_episodes": 0,
            "active_turns": 0,
        }
    finally:
        db.close()


def test_successful_admission_commits_session_binding_and_causal_state(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    session_id = db.ensure_session("andreas", "terminal-andreas")
    lifecycle = TurnLifecycle(db, "andreas", session_id)
    try:
        with lifecycle.begin_admission(
            "hello ClayVerse",
            claude_session_id="claude-session-ok",
        ) as result:
            assert db.db.in_transaction is True
            assert lifecycle.active()["turn_id"] == result["turn_id"]
        assert db.db.in_transaction is False
        row = db.db.execute("SELECT provenance FROM turns WHERE turn_id=?", (result["turn_id"],)).fetchone()
        provenance = json.loads(row["provenance"])
        assert provenance["claude_session_id"] == "claude-session-ok"
        active = lifecycle.active()
        assert active["turn_id"] == result["turn_id"]
        assert active["causal_id"] == result["causal_id"]
    finally:
        db.close()
