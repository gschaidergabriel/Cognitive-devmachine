from __future__ import annotations

import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import user_prompt


def _configure(monkeypatch, root):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")
    db = UnifiedDB(root / "unified.db")
    IdentityRouter(db, {})
    db.close()


def test_user_prompt_commits_claude_session_with_active_turn(tmp_path, monkeypatch):
    _configure(monkeypatch, tmp_path)
    user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-atomic-1",
        "prompt": "atomic session binding probe",
    })

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        row = db.db.execute(
            "SELECT a.causal_id,t.provenance FROM active_turns a "
            "JOIN turns t ON t.turn_id=a.turn_id WHERE a.session_id='session:gabriel'"
        ).fetchone()
        assert row is not None
        provenance = json.loads(row["provenance"])
        assert provenance["claude_session_id"] == "claude-atomic-1"
        assert provenance["causal_id"] == row["causal_id"]
    finally:
        db.close()


def test_invalid_claude_session_never_creates_active_turn(tmp_path, monkeypatch):
    _configure(monkeypatch, tmp_path)
    with pytest.raises(Exception, match="invalid Claude session id|missing Claude session id"):
        user_prompt({
            "hook_event_name": "UserPromptSubmit",
            "session_id": "x" * 513,
            "prompt": "must fail before turn commit",
        })

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
        assert db.db.execute(
            "SELECT COUNT(*) FROM turns WHERE role='user' AND content='must fail before turn commit'"
        ).fetchone()[0] == 0
    finally:
        db.close()
