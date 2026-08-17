from __future__ import annotations

from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


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


def _expected_attestation_tails():
    return [
        ["show-options", "-sqv", "@clayverse_managed_policy"],
        ["show-options", "-gqv", "prefix"],
        ["show-options", "-gqv", "prefix2"],
        ["show-options", "-gqv", "status"],
        ["show-options", "-gqv", "mouse"],
        ["show-options", "-gqv", "default-shell"],
        ["list-keys"],
    ]


def test_existing_server_reapplies_policy_before_attestation(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return _attested_policy_run(argv, **kwargs)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    binding = manager.ensure("gabriel")

    assert binding.user_id == "gabriel"
    tails = [call[5:] for call in calls]
    assert tails[0] == ["source-file", "/etc/clayverse/managed-tmux.conf"]
    assert tails[1:] == _expected_attestation_tails()


def test_failed_policy_reapply_blocks_effective_attestation(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=1, stdout="", stderr="policy rejected")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="failed to enforce tmux policy"):
        manager.ensure("andreas")

    assert [call[5:] for call in calls] == [
        ["source-file", "/etc/clayverse/managed-tmux.conf"]
    ]


def test_new_session_keeps_direct_argv_then_reapplies_and_attests(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return _attested_policy_run(argv, **kwargs)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager.ensure("gabriel")

    creation = calls[0]
    assert creation[5:9] == ["new-session", "-d", "-s", "clayverse-gabriel"]
    env_index = creation.index("env")
    assert creation[env_index + 1] == "-i"
    assert "claude" in creation[env_index + 2:]
    assert all(not item.startswith("env -i ") for item in creation)
    assert "mcp__clayverse__session_state" in creation
    assert "mcp__clayverse__request_effect" in creation

    tails = [call[5:] for call in calls[1:]]
    assert tails[0] == ["source-file", "/etc/clayverse/managed-tmux.conf"]
    assert tails[1:] == _expected_attestation_tails()
