from __future__ import annotations

import subprocess

from clayverse.terminal_sessions import TerminalSessionManager


class _Completed:
    returncode = 0
    stderr = ""
    stdout = ""


def test_claude_terminal_starts_from_empty_allowlisted_environment(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_attest_existing_session", lambda binding: True)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        return _Completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.ensure("gabriel")

    launch = manager._launch_argv(manager.binding("gabriel"))
    new_session = next(argv for argv in calls if "new-session" in argv)
    assert new_session[-len(launch):] == launch
    assert launch[:2] == ["env", "-i"]
    assert "PATH=/usr/local/bin:/usr/bin:/bin" in launch
    assert "HOME=" + str(tmp_path / "state" / "users" / "gabriel" / "home") in launch
    assert "CLAYVERSE_USER_ID=gabriel" in launch
    assert "CLAYVERSE_SESSION_ID=session:gabriel" in launch
    assert "DISABLE_UPDATES=1" in launch
    assert "CLAUDE_CODE_SKIP_PROMPT_HISTORY=1" in launch
    assert "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1" in launch
    assert "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1" in launch
    assert not any(item.startswith("ANTHROPIC_API_KEY=") for item in launch)
    assert not any(item.startswith("ANTHROPIC_AUTH_TOKEN=") for item in launch)
    assert launch[-1] == "/opt/clayverse/runtime/CLAUDE.md"
