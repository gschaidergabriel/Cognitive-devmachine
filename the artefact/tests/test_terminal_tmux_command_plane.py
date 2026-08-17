from __future__ import annotations

from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


def _ok():
    return SimpleNamespace(returncode=0, stderr="", stdout="")


def test_new_tmux_server_uses_empty_config_and_locks_command_plane(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        if "has-session" in argv:
            return SimpleNamespace(returncode=1, stderr="", stdout="")
        return _ok()

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)

    manager.ensure("gabriel")

    new_session = next(argv for argv in calls if "new-session" in argv)
    assert new_session[:5] == ["tmux", "-f", "/dev/null", "-L", "clayverse-gabriel"]

    security_commands = [
        argv[3:]
        for argv in calls
        if argv[:3] == ["tmux", "-L", "clayverse-gabriel"]
        and "has-session" not in argv
    ]
    assert ["set-option", "-g", "prefix", "None"] in security_commands
    assert ["set-option", "-g", "prefix2", "None"] in security_commands
    assert ["unbind-key", "-a"] in security_commands
    assert ["set-option", "-g", "mouse", "off"] in security_commands


def test_existing_tmux_server_is_relocked_before_return(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        return _ok()

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)

    manager.ensure("andreas")

    assert not any("new-session" in argv for argv in calls)
    assert ["tmux", "-L", "clayverse-andreas", "unbind-key", "-a"] in calls
    assert ["tmux", "-L", "clayverse-andreas", "set-option", "-g", "prefix", "None"] in calls
    assert ["tmux", "-L", "clayverse-andreas", "set-option", "-g", "prefix2", "None"] in calls


def test_lockdown_failure_kills_server_and_fails_closed(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        if "has-session" in argv:
            return SimpleNamespace(returncode=1, stderr="", stdout="")
        if "unbind-key" in argv:
            return SimpleNamespace(returncode=1, stderr="unbind denied", stdout="")
        return _ok()

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)

    with pytest.raises(TerminalRuntimeError, match="failed to lock tmux control plane"):
        manager.ensure("gabriel")

    assert ["tmux", "-L", "clayverse-gabriel", "kill-server"] in calls
