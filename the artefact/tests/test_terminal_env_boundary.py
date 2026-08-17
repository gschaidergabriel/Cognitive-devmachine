from __future__ import annotations

import shlex
import subprocess

from clayverse.terminal_sessions import TerminalSessionManager


class _Completed:
    returncode = 0
    stderr = ""


def test_claude_terminal_starts_from_empty_allowlisted_environment(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return _Completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.ensure("gabriel")

    command = calls[-1][-1]
    argv = shlex.split(command)
    assert argv[:2] == ["env", "-i"]
    assert "PATH=/usr/local/bin:/usr/bin:/bin" in argv
    assert "HOME=" + str(tmp_path / "state" / "users" / "gabriel" / "home") in argv
    assert "CLAYVERSE_USER_ID=gabriel" in argv
    assert "CLAYVERSE_SESSION_ID=session:gabriel" in argv
    assert "CLAUDE_CODE_SKIP_PROMPT_HISTORY=1" in argv
    assert "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1" in argv
    assert "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1" in argv
    assert not any(item.startswith("ANTHROPIC_API_KEY=") for item in argv)
    assert not any(item.startswith("ANTHROPIC_AUTH_TOKEN=") for item in argv)
    assert argv[-1] == "/opt/clayverse/runtime/CLAUDE.md"
