from pathlib import Path
from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


ROOT = Path(__file__).resolve().parents[1]
MANAGED_TMUX = ROOT / "policy" / "managed-tmux.conf"


def _assert_managed_tmux_argv(argv, *, user_id: str):
    assert argv[:5] == ["tmux", "-L", f"clayverse-{user_id}", "-f", "/etc/clayverse/managed-tmux.conf"]


def _attested_policy_run(argv, **kwargs):
    tail = tuple(argv[5:])
    values = {
        ("show-options", "-sqv", "@clayverse_managed_policy"): TerminalSessionManager.MANAGED_TMUX_POLICY_ID,
        ("show-options", "-gqv", "prefix"): "None",
        ("show-options", "-gqv", "prefix2"): "None",
        ("show-options", "-gqv", "status"): "off",
        ("show-options", "-gqv", "mouse"): "off",
        ("show-options", "-gqv", "default-shell"): str(TerminalSessionManager.DIRECT_SHELL_GUARD),
        ("list-keys",): "",
    }
    value = values.get(tail, "")
    return SimpleNamespace(returncode=0, stdout=value + ("\n" if value else ""), stderr="")


def test_managed_tmux_policy_removes_browser_command_surface():
    lines = [line.strip() for line in MANAGED_TMUX.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    assert "set-option -g prefix None" in lines
    assert "set-option -g prefix2 None" in lines
    assert "set-option -g status off" in lines
    assert "set-option -g mouse off" in lines
    assert "set-option -g default-shell /opt/clayverse/runtime/deny-shell" in lines
    for table in ("prefix", "root", "copy-mode", "copy-mode-vi"):
        assert f"unbind-key -a -T {table}" in lines
    assert "unbind-key -a" not in lines
    assert lines[-1] == "set-option -s @clayverse_managed_policy " + TerminalSessionManager.MANAGED_TMUX_POLICY_ID
    assert TerminalSessionManager.MANAGED_TMUX_POLICY_ID.endswith("-v3")
    assert not any(line.startswith("bind ") or line.startswith("bind-key ") for line in lines)


def test_tmux_session_probe_is_pinned_to_managed_policy(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    calls = []
    monkeypatch.setattr(terminal_sessions.subprocess, "run", lambda argv, **kwargs: calls.append(argv) or SimpleNamespace(returncode=0))
    assert manager._has_session(binding) is True
    _assert_managed_tmux_argv(calls[-1], user_id="gabriel")
    assert calls[-1][5:] == ["has-session", "-t", "clayverse-gabriel"]


def test_tmux_server_policy_attestation_checks_effective_server(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    calls = []
    monkeypatch.setattr(terminal_sessions.subprocess, "run", lambda argv, **kwargs: calls.append(argv) or _attested_policy_run(argv, **kwargs))
    manager._assert_tmux_server_policy(binding)
    assert [call[5:] for call in calls] == [
        ["show-options", "-sqv", "@clayverse_managed_policy"],
        ["show-options", "-gqv", "prefix"],
        ["show-options", "-gqv", "prefix2"],
        ["show-options", "-gqv", "status"],
        ["show-options", "-gqv", "mouse"],
        ["show-options", "-gqv", "default-shell"],
        ["list-keys"],
    ]


def test_existing_tmux_session_without_policy_marker_fails_closed(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    def fake_run(argv, **kwargs):
        if argv[5:] == ["show-options", "-sqv", "@clayverse_managed_policy"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return _attested_policy_run(argv, **kwargs)
    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="managed-policy marker"):
        manager.ensure("andreas")


def test_existing_tmux_session_with_wrong_effective_prefix_fails_closed(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    def fake_run(argv, **kwargs):
        if argv[5:] == ["show-options", "-gqv", "prefix"]:
            return SimpleNamespace(returncode=0, stdout="C-b\n", stderr="")
        return _attested_policy_run(argv, **kwargs)
    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="prefix"):
        manager.ensure("gabriel")


def test_existing_tmux_session_with_any_surviving_key_binding_fails_closed(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    def fake_run(argv, **kwargs):
        if argv[5:] == ["list-keys"]:
            return SimpleNamespace(returncode=0, stdout="bind-key -T root C-x run-shell /bin/sh\n", stderr="")
        return _attested_policy_run(argv, **kwargs)
    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="keymap"):
        manager.ensure("andreas")


def test_tmux_session_creation_is_pinned_to_managed_policy(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_attest_existing_session", lambda binding: True)
    calls = []
    monkeypatch.setattr(terminal_sessions.subprocess, "run", lambda argv, **kwargs: calls.append(argv) or SimpleNamespace(returncode=0, stderr="", stdout=""))
    manager.ensure("andreas")
    creation = next(call for call in calls if "new-session" in call)
    _assert_managed_tmux_argv(creation, user_id="andreas")
    assert creation[5:9] == ["new-session", "-d", "-s", "clayverse-andreas"]


def test_new_tmux_session_must_attest_policy_before_admission(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    calls = []
    def fake_run(argv, **kwargs):
        calls.append(argv)
        if argv[5:] == ["show-options", "-sqv", "@clayverse_managed_policy"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="managed-policy marker"):
        manager.ensure("gabriel")
    assert any(call[5:9] == ["new-session", "-d", "-s", "clayverse-gabriel"] for call in calls)


def test_browser_attach_cannot_fall_back_to_default_tmux_policy(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    monkeypatch.setattr(manager, "ensure", lambda user_id: binding)
    monkeypatch.setattr(terminal_sessions.pty, "fork", lambda: (0, 17))
    captured = {}
    def fake_execvpe(file, argv, env):
        captured.update(file=file, argv=argv, env=env)
        raise RuntimeError("stop-before-exec")
    monkeypatch.setattr(terminal_sessions.os, "execvpe", fake_execvpe)
    with pytest.raises(RuntimeError, match="stop-before-exec"):
        manager.attach_pty("gabriel")
    assert captured["file"] == "tmux"
    _assert_managed_tmux_argv(captured["argv"], user_id="gabriel")
    assert captured["argv"][5:] == ["attach-session", "-t", "clayverse-gabriel"]


def test_managed_tmux_policy_is_root_owned_and_read_only_in_image():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY --chown=root:root policy/managed-tmux.conf /etc/clayverse/managed-tmux.conf" in dockerfile
    assert "chmod 0444 /etc/claude-code/managed-mcp.json /etc/claude-code/managed-settings.json /etc/clayverse/managed-tmux.conf" in dockerfile
