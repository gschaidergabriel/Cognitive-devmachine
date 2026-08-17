from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
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


def test_existing_session_reapplies_then_attests(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    order = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: order.append("enforce"))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: order.append("attest"))
    monkeypatch.setattr(manager, "_attest_existing_session", lambda binding: True)

    manager.ensure("gabriel")

    assert order == ["enforce", "attest"]


def test_policy_reapply_timeout_fails_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")

    def timeout(argv, **kwargs):
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout)

    with pytest.raises(TerminalRuntimeError, match="policy enforcement unavailable"):
        manager._enforce_tmux_policy(binding)


def test_policy_reapply_tolerates_only_already_removed_key_tables(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")

    def fake_run(argv, **kwargs):
        assert argv[5:] == ["source-file", "/etc/clayverse/managed-tmux.conf"]
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr=(
                "table prefix doesn't exist\n"
                "table copy-mode doesn't exist\n"
                "table copy-mode-vi doesn't exist\n"
            ),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager._enforce_tmux_policy(binding)


def test_policy_reapply_rejects_mixed_or_unknown_diagnostics(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")

    def fake_run(argv, **kwargs):
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="table prefix doesn't exist\nunknown option: unsafe-policy\n",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="failed to enforce tmux policy"):
        manager._enforce_tmux_policy(binding)


def test_policy_reapply_rejects_nonzero_without_diagnostic(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda argv, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr=""),
    )
    with pytest.raises(TerminalRuntimeError, match="failed to enforce tmux policy"):
        manager._enforce_tmux_policy(binding)


def test_new_session_direct_argv_then_reapplies_then_attests(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    order = []
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        order.append("new")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: order.append("enforce"))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: order.append("attest"))
    monkeypatch.setattr(manager, "_attest_existing_session", lambda binding: True)

    manager.ensure("andreas")

    argv, kwargs = calls[0]
    assert order == ["new", "enforce", "attest"]
    assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
    env_index = argv.index("env")
    assert argv[env_index + 1] == "-i"
    assert "claude" in argv[env_index + 2:]
    assert all(not item.startswith("env -i ") for item in argv)


def test_new_session_timeout_does_not_continue_to_policy_or_attestation(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    policy_calls = []
    attest_calls = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: policy_calls.append(binding))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: attest_calls.append(binding))

    def timeout(argv, **kwargs):
        assert "new-session" in argv
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", timeout)

    with pytest.raises(TerminalRuntimeError, match="session creation unavailable"):
        manager.ensure("gabriel")

    assert policy_calls == []
    assert attest_calls == []
