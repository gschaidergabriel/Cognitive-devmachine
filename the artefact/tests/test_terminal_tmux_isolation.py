from __future__ import annotations

from types import SimpleNamespace

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalSessionManager


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


def test_session_creation_uses_only_the_bound_users_tmux_server(tmp_path, monkeypatch):
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
    assert all(argv[argv.index("-L") + 1] == "clayverse-gabriel" for argv in gabriel_calls)
    assert all(argv[argv.index("-L") + 1] == "clayverse-andreas" for argv in andreas_calls)
    assert all(argv[argv.index("-f") + 1] == "/etc/clayverse/managed-tmux.conf" for argv in gabriel_calls)
    assert all(argv[argv.index("-f") + 1] == "/etc/clayverse/managed-tmux.conf" for argv in andreas_calls)


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
    assert argv[5:] == [
        "attach-session",
        "-t",
        "clayverse-andreas",
    ]
    assert env["HOME"] == str(binding.home)
