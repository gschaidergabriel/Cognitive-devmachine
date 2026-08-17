from pathlib import Path
from types import SimpleNamespace
import subprocess

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


ROOT = Path(__file__).resolve().parents[1]


def test_existing_server_reapply_precedes_attestation(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    order = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: order.append("enforce"))
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: order.append("attest"))

    manager.ensure("gabriel")

    assert order == ["enforce", "attest"]


def test_has_session_timeout_fails_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")

    def timeout(argv, **kwargs):
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)
    with pytest.raises(TerminalRuntimeError, match="session liveness probe unavailable"):
        manager._has_session(binding)


def test_policy_reapply_timeout_fails_closed(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")

    def timeout(argv, **kwargs):
        assert argv[5:] == ["source-file", "/etc/clayverse/managed-tmux.conf"]
        assert kwargs["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)
    with pytest.raises(TerminalRuntimeError, match="policy enforcement unavailable"):
        manager._enforce_tmux_policy(binding)


def test_new_session_is_direct_argv_and_bounded(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = list(argv)
        seen["timeout"] = kwargs.get("timeout")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager.ensure("gabriel")

    argv = seen["argv"]
    assert seen["timeout"] == manager.TMUX_CONTROL_TIMEOUT_SECONDS
    assert "new-session" in argv
    env_index = argv.index("env")
    assert argv[env_index + 1] == "-i"
    assert "claude" in argv[env_index + 2:]
    assert all(not item.startswith("env -i ") for item in argv)


def test_new_session_timeout_stops_before_policy(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    policy_calls = []
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: policy_calls.append(binding))

    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(terminal_sessions.subprocess, "run", timeout)
    with pytest.raises(TerminalRuntimeError, match="session creation unavailable"):
        manager.ensure("andreas")

    assert policy_calls == []


def test_runtime_rejects_writable_managed_tmux_policy(monkeypatch, tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    runtime_prompt = tmp_path / "CLAUDE.md"
    settings = tmp_path / "managed-settings.json"
    mcp = tmp_path / "managed-mcp.json"
    policy = tmp_path / "managed-tmux.conf"
    guard = tmp_path / "deny-shell"
    for path in (runtime_prompt, settings, mcp, policy, guard):
        path.write_text("x")
    policy.chmod(0o444)
    guard.chmod(0o555)

    manager.runtime_prompt = runtime_prompt
    manager.MANAGED_SETTINGS = settings
    manager.MANAGED_MCP = mcp
    manager.MANAGED_TMUX = policy
    manager.DIRECT_SHELL_GUARD = guard
    monkeypatch.setattr(terminal_sessions.shutil, "which", lambda program: f"/usr/bin/{program}")

    manager._require_programs()
    policy.chmod(0o644)
    with pytest.raises(TerminalRuntimeError, match="unavailable or writable"):
        manager._require_programs()


def test_policy_preserves_v2_tables_and_adds_shell_fallback_fences():
    lines = [
        line.strip()
        for line in (ROOT / "policy" / "managed-tmux.conf").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for line in (
        "set-option -g prefix None",
        "set-option -g prefix2 None",
        "set-option -g status off",
        "set-option -g mouse off",
        "set-option -g default-shell /opt/clayverse/runtime/deny-shell",
        "unbind-key -a -T prefix",
        "unbind-key -a -T root",
        "unbind-key -a -T copy-mode",
        "unbind-key -a -T copy-mode-vi",
    ):
        assert line in lines
    assert lines[-1] == (
        "set-option -s @clayverse_managed_policy "
        "clayverse-browser-transport-v2"
    )
