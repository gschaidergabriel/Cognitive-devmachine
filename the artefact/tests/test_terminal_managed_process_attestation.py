from __future__ import annotations

import shlex
from types import SimpleNamespace

import pytest

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import TerminalRuntimeError, TerminalSessionManager


def _completed(*, returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_managed_session_attests_single_live_claude_pane_and_exact_launch(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    expected_start = shlex.join(manager._launch_argv(binding))
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        if "has-session" in argv:
            return _completed(returncode=0)
        if "list-panes" in argv:
            return _completed(stdout=f"0\tclaude\t{expected_start}\n")
        raise AssertionError(argv)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)

    assert manager.is_managed_session(binding) is True
    assert any("has-session" in argv for argv in calls)
    pane_call = next(argv for argv in calls if "list-panes" in argv)
    assert pane_call[pane_call.index("-L") + 1] == "clayverse-gabriel"
    assert "-s" in pane_call
    assert pane_call[pane_call.index("-t") + 1] == "clayverse-gabriel"


@pytest.mark.parametrize(
    "pane_output",
    [
        "1\tclaude\tenv -i claude\n",
        "0\tbash\tenv -i claude\n",
        "0\tclaude\tenv -i claude\n0\tclaude\tenv -i claude\n",
        "malformed\n",
    ],
)
def test_managed_session_rejects_dead_wrong_multi_or_malformed_panes(tmp_path, monkeypatch, pane_output):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("andreas")

    def fake_run(argv, **kwargs):
        if "has-session" in argv:
            return _completed(returncode=0)
        if "list-panes" in argv:
            return _completed(stdout=pane_output)
        raise AssertionError(argv)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    assert manager.is_managed_session(binding) is False


def test_managed_session_rejects_same_process_name_with_wrong_launch_contract(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = manager.binding("gabriel")
    wrong_start = shlex.join(manager._launch_argv(binding)[:-2] + ["--permission-mode", "bypassPermissions"])

    def fake_run(argv, **kwargs):
        if "has-session" in argv:
            return _completed(returncode=0)
        if "list-panes" in argv:
            return _completed(stdout=f"0\tclaude\t{wrong_start}\n")
        raise AssertionError(argv)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    assert manager.is_managed_session(binding) is False


def test_ensure_fails_closed_on_existing_unmanaged_session(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)

    def fake_run(argv, **kwargs):
        if "has-session" in argv:
            return _completed(returncode=0)
        if "list-panes" in argv:
            return _completed(stdout="0\tbash\t/bin/bash\n")
        raise AssertionError(argv)

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)

    with pytest.raises(TerminalRuntimeError, match="not the managed Claude session"):
        manager.ensure("andreas")
