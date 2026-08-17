from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


def _ok(stdout=""):
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def _v3_run(manager, calls):
    def fake_run(argv, **kwargs):
        calls.append((list(argv), kwargs.get("timeout")))
        tail = argv[5:]
        if tail == ["source-file", str(manager.MANAGED_TMUX)]:
            return _ok()
        if tail == ["show-options", "-sqv", "@clayverse_managed_policy"]:
            return _ok(manager.MANAGED_TMUX_POLICY_ID + "\n")
        if tail in (
            ["show-options", "-gqv", "prefix"],
            ["show-options", "-gqv", "prefix2"],
        ):
            return _ok("None\n")
        if tail == ["show-options", "-gqv", "status"]:
            return _ok("off\n")
        if tail == ["show-options", "-gqv", "mouse"]:
            return _ok("off\n")
        if tail == ["show-options", "-gqv", "default-shell"]:
            return _ok(str(manager.DIRECT_SHELL_GUARD) + "\n")
        if tail == ["list-keys"]:
            return _ok()
        if "new-session" in tail:
            return _ok()
        if "has-session" in tail:
            return _ok()
        raise AssertionError(argv)

    return fake_run


def test_existing_session_reapplies_policy_before_v3_attestation(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    calls = []
    monkeypatch.setattr(terminal_sessions.subprocess, "run", _v3_run(manager, calls))

    manager.ensure("gabriel")

    tails = [argv[5:] for argv, _ in calls]
    assert tails[0] == ["source-file", str(manager.MANAGED_TMUX)]
    assert tails[1] == ["show-options", "-sqv", "@clayverse_managed_policy"]
    assert all(timeout == manager.TMUX_CONTROL_TIMEOUT_SECONDS for _, timeout in calls)


def test_has_session_timeout_fails_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")

    def timeout(argv, **kwargs):
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)
    with pytest.raises(TerminalRuntimeError, match="session liveness probe unavailable"):
        manager._has_session(binding)


def test_policy_reapply_timeout_fails_closed_before_attestation(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)

    def timeout(argv, **kwargs):
        assert argv[5:] == ["source-file", str(manager.MANAGED_TMUX)]
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)
    with pytest.raises(TerminalRuntimeError, match="policy enforcement unavailable"):
        manager.ensure("gabriel")


def test_new_session_timeout_cannot_continue_to_policy_admission(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    policy_calls = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: policy_calls.append(binding))

    def timeout(argv, **kwargs):
        assert "new-session" in argv
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)
    with pytest.raises(TerminalRuntimeError, match="session creation unavailable"):
        manager.ensure("andreas")
    assert policy_calls == []


def test_new_session_uses_direct_argv_then_reapply_then_v3_attestation(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    calls = []
    monkeypatch.setattr(terminal_sessions.subprocess, "run", _v3_run(manager, calls))

    manager.ensure("andreas")

    tails = [argv[5:] for argv, _ in calls]
    assert tails[0][:4] == ["new-session", "-d", "-s", "clayverse-andreas"]
    assert "env" in tails[0]
    assert "claude" in tails[0]
    assert tails[1] == ["source-file", str(manager.MANAGED_TMUX)]
    assert tails[2] == ["show-options", "-sqv", "@clayverse_managed_policy"]
    assert all(timeout == manager.TMUX_CONTROL_TIMEOUT_SECONDS for _, timeout in calls)
