from __future__ import annotations

import io
import json
import sys

import clayverse.terminal_hooks as hooks


def _invoke(monkeypatch, mode: str, payload: dict) -> int:
    monkeypatch.setattr(sys, "argv", ["terminal_hooks.py", mode])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    return hooks._main()


def _raise(_payload):
    raise RuntimeError("synthetic persistence blocker")


def test_first_stop_failure_remains_blocking(monkeypatch):
    monkeypatch.setattr(hooks, "stop", _raise)
    assert _invoke(monkeypatch, "stop", {
        "hook_event_name": "Stop",
        "session_id": "same",
        "stop_hook_active": False,
        "last_assistant_message": "done",
    }) == 2


def test_reentered_stop_failure_does_not_block_again(monkeypatch):
    monkeypatch.setattr(hooks, "stop", _raise)
    assert _invoke(monkeypatch, "stop", {
        "hook_event_name": "Stop",
        "session_id": "same",
        "stop_hook_active": True,
        "last_assistant_message": "done",
    }) == 0


def test_user_prompt_failure_stays_fail_closed(monkeypatch):
    monkeypatch.setattr(hooks, "user_prompt", _raise)
    assert _invoke(monkeypatch, "user_prompt", {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "same",
        "stop_hook_active": True,
        "prompt": "hello",
    }) == 2
