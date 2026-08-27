from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import stop, user_prompt


def configure(monkeypatch, root, user):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", user)
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", f"session:{user}")


def test_browser_hook_cross_session_context_requires_shared_literal_resource(tmp_path, monkeypatch):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    db.close()

    configure(monkeypatch, tmp_path, "gabriel")
    user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-g",
        "prompt": "file:shared.py FACT: gabriel is editing shared.py",
    })
    stop({
        "hook_event_name": "Stop",
        "session_id": "claude-g",
        "last_assistant_message": "recorded",
    })

    configure(monkeypatch, tmp_path, "andreas")
    unrelated = user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-a-1",
        "prompt": "work on unrelated.py",
    })
    assert "gabriel is editing shared.py" not in unrelated["hookSpecificOutput"]["additionalContext"]
    stop({
        "hook_event_name": "Stop",
        "session_id": "claude-a-1",
        "last_assistant_message": "no collision",
    })

    related = user_prompt({
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-a-2",
        "prompt": "please inspect file:shared.py",
    })
    context = related["hookSpecificOutput"]["additionalContext"]
    assert "file:shared.py" in context
    assert "gabriel is editing shared.py" in context
