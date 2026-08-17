from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


def test_has_session_is_bounded_and_timeout_fails_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    seen = {}

    def healthy(argv, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", healthy)
    assert manager._has_session(binding) is True
    assert seen["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS

    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)
    with pytest.raises(TerminalRuntimeError, match="session liveness probe unavailable"):
        manager._has_session(binding)


def test_policy_reapply_is_bounded_and_timeout_fails_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")

    def timeout(argv, **kwargs):
        assert argv[5:] == ["source-file", "/etc/clayverse/managed-tmux.conf"]
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)
    with pytest.raises(TerminalRuntimeError, match="policy enforcement unavailable"):
        manager._enforce_tmux_policy(binding)


def test_existing_session_reapplies_then_attests_before_return(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    events = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: events.append("enforce"))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: events.append("attest"))

    binding = manager.ensure("gabriel")

    assert binding.user_id == "gabriel"
    assert events == ["enforce", "attest"]


def test_new_session_timeout_does_not_continue_to_policy_or_attestation(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    events = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: events.append("enforce"))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: events.append("attest"))

    def timeout(argv, **kwargs):
        assert "new-session" in argv
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)
    with pytest.raises(TerminalRuntimeError, match="session creation unavailable"):
        manager.ensure("andreas")

    assert events == []


def test_new_session_keeps_direct_argv_then_enforces_and_attests(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    events = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: events.append("enforce"))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: events.append("attest"))
    seen = {}

    def healthy(argv, **kwargs):
        seen["argv"] = argv
        seen["timeout"] = kwargs.get("timeout")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", healthy)
    manager.ensure("gabriel")

    argv = seen["argv"]
    env_index = argv.index("env")
    assert argv[env_index + 1] == "-i"
    assert "claude" in argv[env_index + 2:]
    assert all(not item.startswith("env -i ") for item in argv)
    assert seen["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
    assert events == ["enforce", "attest"]
