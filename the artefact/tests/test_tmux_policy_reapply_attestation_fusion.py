from __future__ import annotations

from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


def _attested_result(manager: TerminalSessionManager, argv):
    tail = argv[5:]
    if tail == ["show-options", "-sqv", "@clayverse_managed_policy"]:
        return SimpleNamespace(returncode=0, stdout=manager.MANAGED_TMUX_POLICY_ID + "\n", stderr="")
    if tail in (["show-options", "-gqv", "prefix"], ["show-options", "-gqv", "prefix2"]):
        return SimpleNamespace(returncode=0, stdout="None\n", stderr="")
    if tail == ["list-keys"]:
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    return SimpleNamespace(returncode=0, stdout="", stderr="")


def test_existing_server_reapplies_policy_then_attests_effective_state(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    tails = []

    def fake_run(argv, **kwargs):
        assert kwargs.get("timeout") == manager.TMUX_CONTROL_TIMEOUT_SECONDS
        tails.append(argv[5:])
        return _attested_result(manager, argv)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager.ensure("gabriel")

    assert tails == [
        ["source-file", "/etc/clayverse/managed-tmux.conf"],
        ["show-options", "-sqv", "@clayverse_managed_policy"],
        ["show-options", "-gqv", "prefix"],
        ["show-options", "-gqv", "prefix2"],
        ["list-keys"],
    ]


def test_policy_reapply_failure_stops_before_attestation(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    tails = []

    def fake_run(argv, **kwargs):
        tails.append(argv[5:])
        return SimpleNamespace(returncode=1, stdout="", stderr="rejected")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    with pytest.raises(TerminalRuntimeError, match="failed to enforce tmux policy"):
        manager.ensure("andreas")

    assert tails == [["source-file", "/etc/clayverse/managed-tmux.conf"]]


def test_new_session_keeps_direct_argv_then_reapplies_and_attests(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return _attested_result(manager, argv)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager.ensure("andreas")

    new_session = calls[0]
    assert new_session[5:9] == ["new-session", "-d", "-s", "clayverse-andreas"]
    assert "env" in new_session
    env_index = new_session.index("env")
    assert new_session[env_index + 1] == "-i"
    assert "claude" in new_session[env_index + 2:]
    assert all(not (isinstance(arg, str) and "env -i " in arg) for arg in new_session)
    assert calls[1][5:] == ["source-file", "/etc/clayverse/managed-tmux.conf"]
    assert [call[5:] for call in calls[2:]] == [
        ["show-options", "-sqv", "@clayverse_managed_policy"],
        ["show-options", "-gqv", "prefix"],
        ["show-options", "-gqv", "prefix2"],
        ["list-keys"],
    ]
