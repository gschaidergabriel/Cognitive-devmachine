from __future__ import annotations

import subprocess

import pytest

from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


def test_has_session_uses_bounded_control_timeout(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen["timeout"] = kwargs.get("timeout")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert manager._has_session(binding) is True
    assert seen["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
    assert "has-session" in seen["argv"]


def test_has_session_timeout_fails_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")

    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout)

    with pytest.raises(TerminalRuntimeError, match="session liveness probe unavailable"):
        manager._has_session(binding)


def test_policy_reapply_timeout_fails_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")

    def timeout(argv, **kwargs):
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout)

    with pytest.raises(TerminalRuntimeError, match="policy enforcement unavailable"):
        manager._enforce_tmux_policy(binding)


def test_policy_attestation_uses_same_control_timeout(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")
    seen = []

    def fake_run(argv, **kwargs):
        seen.append(kwargs.get("timeout"))
        tail = argv[5:]
        if tail == ["show-options", "-sqv", "@clayverse_managed_policy"]:
            return subprocess.CompletedProcess(argv, 0, manager.MANAGED_TMUX_POLICY_ID + "\n", "")
        if tail in (["show-options", "-gqv", "prefix"], ["show-options", "-gqv", "prefix2"]):
            return subprocess.CompletedProcess(argv, 0, "None\n", "")
        if tail in (["show-options", "-gqv", "status"], ["show-options", "-gqv", "mouse"]):
            return subprocess.CompletedProcess(argv, 0, "off\n", "")
        if tail == ["show-options", "-gqv", "default-shell"]:
            return subprocess.CompletedProcess(argv, 0, str(manager.DIRECT_SHELL_GUARD) + "\n", "")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager._assert_tmux_server_policy(binding)

    assert seen == [manager.TMUX_CONTROL_TIMEOUT_SECONDS] * 7


def test_new_session_timeout_does_not_continue_to_policy_attach(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    policy_calls = []
    attestation_calls = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: policy_calls.append(binding))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: attestation_calls.append(binding))

    def timeout(argv, **kwargs):
        assert "new-session" in argv
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout)

    with pytest.raises(TerminalRuntimeError, match="session creation unavailable"):
        manager.ensure("gabriel")

    assert policy_calls == []
    assert attestation_calls == []
