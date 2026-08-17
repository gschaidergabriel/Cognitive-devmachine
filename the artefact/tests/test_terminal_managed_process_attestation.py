from __future__ import annotations

import shlex
from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


def _pane(manager: TerminalSessionManager, binding, *, command="claude", launch=None, dead="0"):
    start = launch if launch is not None else manager._launch_argv(binding)
    return SimpleNamespace(returncode=0, stdout=f"{dead}\t{command}\t{shlex.join(start)}\n", stderr="")


def test_exact_managed_claude_launch_contract_is_accepted(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    monkeypatch.setattr(terminal_sessions.subprocess, "run", lambda argv, **kwargs: _pane(manager, binding))
    assert manager._attest_existing_session(binding) is True


def test_policy_valid_but_non_claude_pane_is_not_managed(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    monkeypatch.setattr(manager, "_has_session", lambda b: True)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda b: None)
    monkeypatch.setattr(terminal_sessions.subprocess, "run", lambda argv, **kwargs: _pane(manager, binding, command="bash"))
    assert manager.is_managed_session(binding) is False


def test_same_named_claude_with_changed_launch_contract_is_rejected(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")
    changed = manager._launch_argv(binding) + ["--dangerously-skip-permissions"]
    monkeypatch.setattr(terminal_sessions.subprocess, "run", lambda argv, **kwargs: _pane(manager, binding, launch=changed))
    assert manager._attest_existing_session(binding) is False


def test_existing_session_fails_closed_when_process_attestation_fails(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda b: True)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda b: None)
    monkeypatch.setattr(manager, "_attest_existing_session", lambda b: False)
    with pytest.raises(TerminalRuntimeError, match="not the managed Claude session"):
        manager.ensure("gabriel")


def test_readiness_predicate_is_read_only(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")
    monkeypatch.setattr(manager, "_has_session", lambda b: True)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda b: None)
    monkeypatch.setattr(manager, "_attest_existing_session", lambda b: True)
    assert manager.is_managed_session(binding) is True
