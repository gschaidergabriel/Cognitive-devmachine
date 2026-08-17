from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


def test_existing_server_reapply_precedes_v3_attestation(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    order = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: order.append("enforce"))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: order.append("attest"))

    manager.ensure("gabriel")

    assert manager.MANAGED_TMUX_POLICY_ID == "clayverse-browser-transport-v3"
    assert order == ["enforce", "attest"]


def test_has_session_uses_bounded_control_timeout(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = list(argv)
        seen["timeout"] = kwargs.get("timeout")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)

    assert manager._has_session(binding) is True
    assert seen["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
    assert seen["argv"][5:] == ["has-session", "-t", "clayverse-gabriel"]


def test_has_session_timeout_fails_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")

    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)

    with pytest.raises(TerminalRuntimeError, match="session liveness probe unavailable"):
        manager._has_session(binding)


def test_policy_reapply_is_bounded_and_fail_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    seen = {}

    def timeout(argv, **kwargs):
        seen["argv"] = list(argv)
        seen["timeout"] = kwargs.get("timeout")
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)

    with pytest.raises(TerminalRuntimeError, match="policy enforcement unavailable"):
        manager._enforce_tmux_policy(binding)

    assert seen["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
    assert seen["argv"][5:] == ["source-file", "/etc/clayverse/managed-tmux.conf"]


def test_new_session_is_bounded_then_reapplied_before_attestation(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    calls = []
    order = []

    def fake_run(argv, **kwargs):
        calls.append((list(argv), kwargs.get("timeout")))
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: order.append("enforce"))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: order.append("attest"))

    manager.ensure("andreas")

    assert len(calls) == 1
    argv, timeout = calls[0]
    assert timeout == manager.TMUX_CONTROL_TIMEOUT_SECONDS
    assert argv[5:9] == ["new-session", "-d", "-s", "clayverse-andreas"]
    env_index = argv.index("env")
    assert argv[env_index + 1] == "-i"
    assert "claude" in argv[env_index + 2:]
    assert order == ["enforce", "attest"]


def test_new_session_timeout_stops_before_policy_or_attestation(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    order = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: order.append("enforce"))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: order.append("attest"))

    def timeout(argv, **kwargs):
        assert "new-session" in argv
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)

    with pytest.raises(TerminalRuntimeError, match="session creation unavailable"):
        manager.ensure("gabriel")

    assert order == []
