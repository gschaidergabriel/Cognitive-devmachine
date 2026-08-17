from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalSessionManager


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_users_have_disjoint_tmux_server_sockets(tmp_path):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    gabriel = manager.binding("gabriel")
    andreas = manager.binding("andreas")

    assert manager._tmux_socket(gabriel) == "clayverse-gabriel"
    assert manager._tmux_socket(andreas) == "clayverse-andreas"
    assert manager._tmux_socket(gabriel) != manager._tmux_socket(andreas)
    assert gabriel.tmux_name == "clayverse-gabriel"
    assert andreas.tmux_name == "clayverse-andreas"


def test_session_creation_uses_bound_server_managed_policy_and_direct_argv(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        if "has-session" in argv:
            return SimpleNamespace(returncode=1, stderr="", stdout="")
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)

    manager.ensure("gabriel")
    manager.ensure("andreas")

    gabriel_calls = [argv for argv in calls if "clayverse-gabriel" in argv]
    andreas_calls = [argv for argv in calls if "clayverse-andreas" in argv]
    assert gabriel_calls
    assert andreas_calls
    for argv, expected_socket in (
        *[(argv, "clayverse-gabriel") for argv in gabriel_calls],
        *[(argv, "clayverse-andreas") for argv in andreas_calls],
    ):
        assert argv[argv.index("-f") + 1] == str(manager.TMUX_CONFIG)
        assert argv[argv.index("-L") + 1] == expected_socket

    creation = [argv for argv in calls if "new-session" in argv]
    assert len(creation) == 2
    for argv in creation:
        env_index = argv.index("env")
        assert argv[env_index + 1] == "-i"
        assert "claude" in argv[env_index + 2:]
        assert all(not (item.startswith("env -i ") or item.startswith("'env -i ")) for item in argv)


def test_attach_pty_uses_only_bound_server_and_managed_policy(tmp_path, monkeypatch):
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
    assert argv == [
        "tmux",
        "-f",
        str(manager.TMUX_CONFIG),
        "-L",
        "clayverse-andreas",
        "attach-session",
        "-t",
        "clayverse-andreas",
    ]
    assert env["HOME"] == str(binding.home)


def test_managed_tmux_policy_removes_interactive_control_surface():
    policy = (ROOT / "policy" / "tmux.conf").read_text()
    assert "set-option -g prefix None" in policy
    assert "set-option -g prefix2 None" in policy
    assert "unbind-key -a -T prefix" in policy
    assert "unbind-key -a -T root" in policy
    assert "set-option -g default-shell /opt/clayverse/runtime/deny-shell" in policy
    assert "set-option -g status off" in policy
    assert "set-option -g mouse off" in policy


def test_image_installs_tmux_policy_root_owned_read_only():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "policy/tmux.conf /etc/clayverse/tmux.conf" in dockerfile
    assert "chmod 0444 /etc/claude-code/managed-mcp.json /etc/claude-code/managed-settings.json /etc/clayverse/tmux.conf" in dockerfile
