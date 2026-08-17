from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


ROOT = Path(__file__).resolve().parents[1]


def _assert_managed_socket(argv: list[str], user_id: str) -> None:
    assert argv[:5] == [
        "tmux",
        "-L",
        f"clayverse-{user_id}",
        "-f",
        "/etc/clayverse/managed-tmux.conf",
    ]


def test_canonical_users_have_disjoint_tmux_server_sockets(tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    gabriel = manager.binding("gabriel")
    andreas = manager.binding("andreas")
    assert manager._tmux_socket(gabriel) == "clayverse-gabriel"
    assert manager._tmux_socket(andreas) == "clayverse-andreas"
    assert manager._tmux_socket(gabriel) != manager._tmux_socket(andreas)
    assert gabriel.tmux_name == "clayverse-gabriel"
    assert andreas.tmux_name == "clayverse-andreas"


def test_session_creation_uses_managed_socket_and_direct_argv(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_attest_existing_session", lambda binding: True)
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        if "has-session" in argv:
            return SimpleNamespace(returncode=1, stderr="", stdout="")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager.ensure("gabriel")
    manager.ensure("andreas")

    creation = [argv for argv in calls if "new-session" in argv]
    assert len(creation) == 2
    for argv, user_id in zip(creation, ("gabriel", "andreas"), strict=True):
        _assert_managed_socket(argv, user_id)
        env_index = argv.index("env")
        assert argv[env_index + 1] == "-i"
        assert "claude" in argv[env_index + 2:]
        assert all(not item.startswith("env -i ") for item in argv)
        assert "mcp__clayverse__session_state" in argv
        assert "mcp__clayverse__request_effect" in argv


def test_attach_pty_uses_only_the_bound_users_tmux_server(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")
    monkeypatch.setattr(manager, "ensure", lambda user_id: binding)
    monkeypatch.setattr(terminal_sessions.pty, "fork", lambda: (0, 99))
    exec_calls = []

    def fake_execvpe(program, argv, env):
        exec_calls.append((program, list(argv), dict(env)))

    monkeypatch.setattr(terminal_sessions.os, "execvpe", fake_execvpe)
    manager.attach_pty("andreas")

    assert len(exec_calls) == 1
    program, argv, env = exec_calls[0]
    assert program == "tmux"
    _assert_managed_socket(argv, "andreas")
    assert argv[5:] == ["attach-session", "-t", "clayverse-andreas"]
    assert env["HOME"] == str(binding.home)


def test_managed_tmux_policy_disables_commands_and_shell_fallback():
    policy = (ROOT / "policy" / "managed-tmux.conf").read_text()
    assert "set-option -g prefix None" in policy
    assert "set-option -g prefix2 None" in policy
    assert "set-option -g status off" in policy
    assert "set-option -g mouse off" in policy
    assert "set-option -g default-shell /opt/clayverse/runtime/deny-shell" in policy
    for table in ("prefix", "root", "copy-mode", "copy-mode-vi"):
        assert f"unbind-key -a -T {table}" in policy
    assert "set-option -s @clayverse_managed_policy clayverse-browser-transport-v3" in policy


def test_runtime_rejects_writable_managed_tmux_policy(tmp_path, monkeypatch):
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
    with pytest.raises(TerminalRuntimeError, match="tmux command-surface policy"):
        manager._require_programs()


def test_live_tmux_policy_attests_full_transport_surface(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    expected = {
        ("show-options", "-sqv", "@clayverse_managed_policy"): "clayverse-browser-transport-v3",
        ("show-options", "-gqv", "prefix"): "None",
        ("show-options", "-gqv", "prefix2"): "None",
        ("show-options", "-gqv", "status"): "off",
        ("show-options", "-gqv", "mouse"): "off",
        ("show-options", "-gqv", "default-shell"): "/opt/clayverse/runtime/deny-shell",
        ("list-keys",): "",
    }
    observed = []

    def fake_run(argv, **kwargs):
        command = tuple(argv[5:])
        observed.append(command)
        return SimpleNamespace(returncode=0, stdout=expected[command] + "\n", stderr="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager._assert_tmux_server_policy(binding)
    assert observed == list(expected)


def test_live_tmux_policy_rejects_mutated_default_shell(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")
    expected = {
        ("show-options", "-sqv", "@clayverse_managed_policy"): "clayverse-browser-transport-v3",
        ("show-options", "-gqv", "prefix"): "None",
        ("show-options", "-gqv", "prefix2"): "None",
        ("show-options", "-gqv", "status"): "off",
        ("show-options", "-gqv", "mouse"): "off",
        ("show-options", "-gqv", "default-shell"): "/bin/sh",
        ("list-keys",): "",
    }

    def fake_run(argv, **kwargs):
        command = tuple(argv[5:])
        return SimpleNamespace(returncode=0, stdout=expected[command] + "\n", stderr="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="default-shell"):
        manager._assert_tmux_server_policy(binding)
