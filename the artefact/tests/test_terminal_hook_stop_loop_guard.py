from __future__ import annotations

import io
import json
import sys

import clayverse.terminal_hooks as terminal_hooks


def _run_stop(monkeypatch, *, stop_hook_active: bool) -> int:
    monkeypatch.delenv("CLAYVERSE_USER_ID", raising=False)
    monkeypatch.delenv("CLAYVERSE_SESSION_ID", raising=False)
    payload = {
        "hook_event_name": "Stop",
        "session_id": "claude-session-1",
        "last_assistant_message": "final response",
        "stop_hook_active": stop_hook_active,
    }
    monkeypatch.setattr(sys, "argv", ["terminal_hooks", "stop"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    return terminal_hooks._main()


def test_first_stop_persistence_failure_blocks_once(monkeypatch, capsys):
    assert _run_stop(monkeypatch, stop_hook_active=False) == 2
    assert "terminal user identity is missing or invalid" in capsys.readouterr().err


def test_reentered_stop_persistence_failure_does_not_livelock(monkeypatch, capsys):
    assert _run_stop(monkeypatch, stop_hook_active=True) == 0
    assert "terminal user identity is missing or invalid" in capsys.readouterr().err


def test_user_prompt_failure_remains_blocking_even_if_payload_mentions_stop_retry(monkeypatch):
    monkeypatch.delenv("CLAYVERSE_USER_ID", raising=False)
    payload = {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "claude-session-1",
        "prompt": "hello",
        "stop_hook_active": True,
    }
    monkeypatch.setattr(sys, "argv", ["terminal_hooks", "user_prompt"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert terminal_hooks._main() == 2
