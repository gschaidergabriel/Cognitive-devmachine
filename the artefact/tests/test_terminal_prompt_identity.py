from __future__ import annotations

import io
import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError
import clayverse.terminal_hooks as hooks


def configure(monkeypatch, root):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")
    db = UnifiedDB(root / "unified.db")
    IdentityRouter(db, {})
    db.close()


def submit(session_id: str, prompt_id: str, prompt: str):
    return hooks.user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": session_id,
        "prompt_id": prompt_id,
        "prompt": prompt,
    })


def active_identity(root):
    db = UnifiedDB(root / "unified.db")
    try:
        row = db.db.execute(
            "SELECT a.turn_id,t.provenance FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id "
            "WHERE a.session_id='session:gabriel'"
        ).fetchone()
        if row is None:
            return None
        provenance = json.loads(row["provenance"])
        return row["turn_id"], provenance["claude_session_id"], provenance["claude_prompt_id"]
    finally:
        db.close()


def invoke_managed_stop(monkeypatch, payload: dict) -> int:
    monkeypatch.setattr(hooks.sys, "argv", ["terminal_hooks", "stop"])
    monkeypatch.setattr(hooks.sys, "stdin", io.StringIO(json.dumps(payload)))
    return hooks._main()


def test_managed_prompt_identity_fails_closed_when_missing():
    with pytest.raises(hooks.TerminalHookError, match="prompt id"):
        hooks._prompt_id({}, required=True)


def test_prompt_identity_replay_is_rejected_inside_canonical_admission(tmp_path):
    path = tmp_path / "unified.db"
    db1 = UnifiedDB(path)
    IdentityRouter(db1, {})
    lifecycle1 = TurnLifecycle(db1, "gabriel", "session:gabriel")
    try:
        with lifecycle1.begin_admission(
            "first",
            claude_session_id="claude-session-stable",
            claude_prompt_id="prompt-x",
        ):
            pass

        db2 = UnifiedDB(path)
        lifecycle2 = TurnLifecycle(db2, "gabriel", "session:gabriel")
        try:
            with pytest.raises(TurnLifecycleError, match="duplicate UserPromptSubmit"):
                with lifecycle2.begin_admission(
                    "ALTERED replay bytes",
                    claude_session_id="claude-session-stable",
                    claude_prompt_id="prompt-x",
                ):
                    pass
        finally:
            db2.close()

        rows = db1.recent_turns("session:gabriel", 20)
        assert [(row["role"], row["content"]) for row in rows] == [("user", "first")]
        row = db1.db.execute(
            "SELECT t.provenance FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id "
            "WHERE a.session_id='session:gabriel'"
        ).fetchone()
        provenance = json.loads(row["provenance"])
        assert provenance["claude_session_id"] == "claude-session-stable"
        assert provenance["claude_prompt_id"] == "prompt-x"
    finally:
        db1.close()


def test_prompt_id_replay_inversion_and_stale_terminal_fence(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path)
    session = "claude-session-stable"
    first_text = "identical text may be a genuine later prompt"

    submit(session, "prompt-x", first_text)
    first = active_identity(tmp_path)
    assert first is not None and first[1:] == (session, "prompt-x")

    with pytest.raises(hooks.TerminalHookError, match="duplicate UserPromptSubmit"):
        submit(session, "prompt-x", "ALTERED replay text must not replace the active turn")
    assert active_identity(tmp_path) == first

    submit(session, "prompt-y", first_text)
    second = active_identity(tmp_path)
    assert second is not None and second[0] != first[0]
    assert second[1:] == (session, "prompt-y")

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        rows = db.recent_turns("session:gabriel", 20)
        assert [(row["role"], row["content"]) for row in rows[-3:]] == [
            ("user", first_text),
            ("system", "TURN_ABORTED:previous_turn_interrupted_before_next_prompt"),
            ("user", first_text),
        ]
    finally:
        db.close()

    with pytest.raises(hooks.TerminalHookError, match="different Claude prompt"):
        hooks.stop({
            "hook_event_name": "Stop",
            "session_id": session,
            "prompt_id": "prompt-x",
            "last_assistant_message": "stale completion",
        })
    assert active_identity(tmp_path) == second

    assert hooks.stop_failure({
        "hook_event_name": "StopFailure",
        "session_id": session,
        "prompt_id": "prompt-x",
        "error": "stale failure",
    }) == {"suppressOutput": True}
    assert active_identity(tmp_path) == second

    assert hooks.stop({
        "hook_event_name": "Stop",
        "session_id": session,
        "prompt_id": "prompt-y",
        "last_assistant_message": "current completion",
    }) == {"suppressOutput": True}
    assert active_identity(tmp_path) is None


def test_stop_hook_loop_protection_aborts_exact_failed_active_prompt(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path)
    session = "claude-loop-session"
    submit(session, "prompt-loop", "turn that reaches a repeated Stop hook")

    def fail_stop(_payload):
        raise RuntimeError("forced atomic Stop failure")

    monkeypatch.setattr(hooks, "stop", fail_stop)
    code = invoke_managed_stop(monkeypatch, {
        "hook_event_name": "Stop",
        "session_id": session,
        "prompt_id": "prompt-loop",
        "stop_hook_active": True,
        "last_assistant_message": "final answer that could not be canonicalized",
    })
    assert code == 0
    assert active_identity(tmp_path) is None

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        state = db.db.execute(
            "SELECT state FROM workspace_episodes WHERE session_id='session:gabriel' ORDER BY ts DESC LIMIT 1"
        ).fetchone()[0]
        assert state == "ABORTED"
        rows = db.recent_turns("session:gabriel", 20)
        assert rows[-1]["role"] == "system"
        assert rows[-1]["content"].startswith(
            "TURN_ABORTED:claude_stop_hook_active_failure:RuntimeError:forced atomic Stop failure"
        )
    finally:
        db.close()


def test_stop_hook_loop_protection_never_aborts_different_active_prompt(tmp_path, monkeypatch):
    configure(monkeypatch, tmp_path)
    session = "claude-loop-session"
    submit(session, "prompt-current", "current turn must survive stale Stop cleanup")
    before = active_identity(tmp_path)

    def fail_stop(_payload):
        raise RuntimeError("forced stale Stop failure")

    monkeypatch.setattr(hooks, "stop", fail_stop)
    code = invoke_managed_stop(monkeypatch, {
        "hook_event_name": "Stop",
        "session_id": session,
        "prompt_id": "prompt-stale",
        "stop_hook_active": True,
        "last_assistant_message": "stale answer",
    })
    assert code == 0
    assert active_identity(tmp_path) == before
