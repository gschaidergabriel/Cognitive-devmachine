from pathlib import Path
from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


ROOT = Path(__file__).resolve().parents[1]
MANAGED_TMUX = ROOT / "policy" / "managed-tmux.conf"


def _assert_managed_tmux_argv(argv, *, user_id: str):
    assert argv[:5] == [
        "tmux",
        "-L",
        f"clayverse-{user_id}",
        "-f",
        "/etc/clayverse/managed-tmux.conf",
    ]


def _assert_policy_reapply(argv, *, user_id: str):
    _assert_managed_tmux_argv(argv, user_id=user_id)
    assert argv[5:] == [
        "source-file",
        "/etc/clayverse/managed-tmux.conf",
    ]


def test_managed_tmux_policy_removes_browser_command_surface():
    lines = [
        line.strip()
        for line in MANAGED_TMUX.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert "set-option -g prefix None" in lines
    assert "set-option -g prefix2 None" in lines
    assert "unbind-key -a" in lines
    assert not any(line.startswith("bind ") or line.startswith("bind-key ") for line in lines)


def test_tmux_session_probe_is_pinned_to_managed_policy(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    assert manager._has_session(binding) is True
    _assert_managed_tmux_argv(calls[-1], user_id="gabriel")
    assert calls[-1][5:] == ["has-session", "-t", "clayverse-gabriel"]


def test_existing_tmux_server_reapplies_managed_policy_before_return(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    binding = manager.ensure("gabriel")

    assert binding.user_id == "gabriel"
    assert len(calls) == 1
    _assert_policy_reapply(calls[0], user_id="gabriel")


def test_existing_tmux_server_policy_reapply_fails_closed(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)

    def fake_run(argv, **kwargs):
        return SimpleNamespace(returncode=1, stderr="policy rejected", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="failed to enforce tmux policy"):
        manager.ensure("andreas")


def test_tmux_session_creation_is_pinned_and_reapplies_managed_policy(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager.ensure("andreas")

    assert len(calls) == 2
    _assert_managed_tmux_argv(calls[0], user_id="andreas")
    assert calls[0][5:9] == ["new-session", "-d", "-s", "clayverse-andreas"]
    _assert_policy_reapply(calls[1], user_id="andreas")


def test_browser_attach_cannot_fall_back_to_default_tmux_policy(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    monkeypatch.setattr(manager, "ensure", lambda user_id: binding)
    monkeypatch.setattr(terminal_sessions.pty, "fork", lambda: (0, 17))
    captured = {}

    def fake_execvpe(file, argv, env):
        captured["file"] = file
        captured["argv"] = argv
        captured["env"] = env
        raise RuntimeError("stop-before-exec")

    monkeypatch.setattr(terminal_sessions.os, "execvpe", fake_execvpe)
    with pytest.raises(RuntimeError, match="stop-before-exec"):
        manager.attach_pty("gabriel")

    assert captured["file"] == "tmux"
    _assert_managed_tmux_argv(captured["argv"], user_id="gabriel")
    assert captured["argv"][5:] == ["attach-session", "-t", "clayverse-gabriel"]


def test_managed_tmux_policy_is_root_owned_and_read_only_in_image():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert (
        "COPY --chown=root:root policy/managed-tmux.conf "
        "/etc/clayverse/managed-tmux.conf"
    ) in dockerfile
    assert (
        "chmod 0444 /etc/claude-code/managed-mcp.json "
        "/etc/claude-code/managed-settings.json /etc/clayverse/managed-tmux.conf"
    ) in dockerfile
