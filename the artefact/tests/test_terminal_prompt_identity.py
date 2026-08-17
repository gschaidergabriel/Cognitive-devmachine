from __future__ import annotations

import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import TerminalHookError, _prompt_id, stop, stop_failure, user_prompt


def configure(monkeypatch, root):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")
    db = UnifiedDB(root / "unified.db")
    IdentityRouter(db, {})
    db.close()


def submit(session_id: str, prompt_id: str, prompt: str):
    return user_prompt({
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


def test_managed_prompt_identity_fails_closed_when_missing():
    with pytest.raises(TerminalHookError, match="prompt id"):
        _prompt_id({}, required=True)


def test_prompt_id_replay_inversion_and_stale_terminal_fence(tmp_path, monkeypatch):
    """One prompt identity must survive both replay directions and stale terminal hooks."""
    configure(monkeypatch, tmp_path)
    session = "claude-session-stable"
    first_text = "identical text may be a genuine later prompt"

    submit(session, "prompt-x", first_text)
    first = active_identity(tmp_path)
    assert first is not None and first[1:] == (session, "prompt-x")

    # Same prompt_id with altered text is still the same hook delivery: reject it.
    with pytest.raises(TerminalHookError, match="duplicate UserPromptSubmit"):
        submit(session, "prompt-x", "ALTERED replay text must not replace the active turn")
    assert active_identity(tmp_path) == first

    # Identical text with a fresh prompt_id is a real next prompt after interruption.
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

    # A delayed terminal event from prompt-x must never mutate prompt-y.
    with pytest.raises(TerminalHookError, match="different Claude prompt"):
        stop({
            "hook_event_name": "Stop",
            "session_id": session,
            "prompt_id": "prompt-x",
            "last_assistant_message": "stale completion",
        })
    assert active_identity(tmp_path) == second

    assert stop_failure({
        "hook_event_name": "StopFailure",
        "session_id": session,
        "prompt_id": "prompt-x",
        "error": "stale failure",
    }) == {"suppressOutput": True}
    assert active_identity(tmp_path) == second

    assert stop({
        "hook_event_name": "Stop",
        "session_id": session,
        "prompt_id": "prompt-y",
        "last_assistant_message": "current completion",
    }) == {"suppressOutput": True}
    assert active_identity(tmp_path) is None
