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


def _attested_policy_run(argv, **kwargs):
    tail = argv[5:]
    if tail == ["show-options", "-sqv", "@clayverse_managed_policy"]:
        return SimpleNamespace(
            returncode=0,
            stdout=TerminalSessionManager.MANAGED_TMUX_POLICY_ID + "\n",
            stderr="",
        )
    if tail in (
        ["show-options", "-gqv", "prefix"],
        ["show-options", "-gqv", "prefix2"],
    ):
        return SimpleNamespace(returncode=0, stdout="None\n", stderr="")
    if tail in (
        ["show-options", "-gqv", "status"],
        ["show-options", "-gqv", "mouse"],
    ):
        return SimpleNamespace(returncode=0, stdout="off\n", stderr="")
    if tail == ["show-options", "-gqv", "default-shell"]:
        return SimpleNamespace(
            returncode=0,
            stdout=str(TerminalSessionManager.DIRECT_SHELL_GUARD) + "\n",
            stderr="",
        )
    if tail == ["list-keys"]:
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    return SimpleNamespace(returncode=0, stdout="", stderr="")


def test_managed_tmux_policy_removes_browser_command_surface():
    lines = [
        line.strip()
        for line in MANAGED_TMUX.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert "set-option -g prefix None" in lines
    assert "set-option -g prefix2 None" in lines
    assert "set-option -g status off" in lines
    assert "set-option -g mouse off" in lines
    assert "set-option -g default-shell /opt/clayverse/runtime/deny-shell" in lines
    assert "unbind-key -a -T prefix" in lines
    assert "unbind-key -a -T root" in lines
    assert "unbind-key -a -T copy-mode" in lines
    assert "unbind-key -a -T copy-mode-vi" in lines
    assert "unbind-key -a" not in lines
    assert lines[-1] == (
        "set-option -s @clayverse_managed_policy "
        + TerminalSessionManager.MANAGED_TMUX_POLICY_ID
    )
    assert TerminalSessionManager.MANAGED_TMUX_POLICY_ID.endswith("-v3")
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


def test_tmux_server_policy_attestation_checks_effective_server(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return _attested_policy_run(argv, **kwargs)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
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
    assert all(call[:5] == [
        "tmux", "-L", "clayverse-gabriel", "-f", "/etc/clayverse/managed-tmux.conf"
    ] for call in calls)


def test_existing_tmux_session_without_policy_marker_fails_closed(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)

    def fake_run(argv, **kwargs):
        tail = argv[5:]
        if tail == ["show-options", "-sqv", "@clayverse_managed_policy"]:
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
        tail = argv[5:]
        if tail == ["show-options", "-gqv", "prefix"]:
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
            return SimpleNamespace(
                returncode=0,
                stdout="bind-key -T root C-x run-shell /bin/sh\n",
                stderr="",
            )
        return _attested_policy_run(argv, **kwargs)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="keymap"):
        manager.ensure("andreas")


def test_tmux_session_creation_is_pinned_to_managed_policy(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager.ensure("andreas")
    creation = [call for call in calls if "new-session" in call]
    assert len(creation) == 1
    _assert_managed_tmux_argv(creation[0], user_id="andreas")
    assert creation[0][5:9] == ["new-session", "-d", "-s", "clayverse-andreas"]


def test_new_tmux_session_must_attest_policy_before_admission(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        tail = argv[5:]
        if tail == ["show-options", "-sqv", "@clayverse_managed_policy"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="managed-policy marker"):
        manager.ensure("gabriel")

    assert any(call[5:9] == ["new-session", "-d", "-s", "clayverse-gabriel"] for call in calls)
    assert any(call[5:] == ["source-file", "/etc/clayverse/managed-tmux.conf"] for call in calls)


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
