from __future__ import annotations

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

    new_session_calls = [call for call in calls if "new-session" in call]
    assert len(new_session_calls) == 1
    command = new_session_calls[0]
    env_index = command.index("env")
    argv = command[env_index:]
    assert argv[:2] == ["env", "-i"]
    assert "PATH=/usr/local/bin:/usr/bin:/bin" in argv
    assert "HOME=" + str(tmp_path / "state" / "users" / "gabriel" / "home") in argv
    assert "CLAYVERSE_USER_ID=gabriel" in argv
    assert "CLAYVERSE_SESSION_ID=session:gabriel" in argv
    assert "CLAUDE_CODE_SKIP_PROMPT_HISTORY=1" in argv
    assert "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1" in argv
    assert "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1" in argv

    # Provider/auth/build-orchestration secrets belong to the ClayVerse supervisor
    # or its external orchestration boundary, never to the interactive Claude process.
    forbidden_secret_env = (
        "ANTHROPIC_API_KEY=",
        "ANTHROPIC_AUTH_TOKEN=",
        "CLAUDE_API_KEY=",
        "GLM_API_TOKEN=",
        "CLERK_ISSUER=",
        "CLERK_JWKS_URL=",
        "CLERK_AUDIENCE=",
        "CLERK_AUTHORIZED_PARTIES=",
        "CLERK_PUBLISHABLE_KEY=",
        "CLERK_FRONTEND_API_URL=",
        "GITHUB_READ_TOKEN=",
    )
    assert not any(item.startswith(forbidden_secret_env) for item in argv)
    assert argv[-1] == "/opt/clayverse/runtime/CLAUDE.md"


def test_tmux_server_and_control_clients_do_not_inherit_supervisor_environment(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setenv("GLM_API_TOKEN", "should-never-reach-tmux")
    monkeypatch.setenv("GITHUB_READ_TOKEN", "should-never-reach-tmux")
    monkeypatch.setenv("CLERK_ISSUER", "should-never-reach-tmux")
    monkeypatch.setenv("UNRELATED_SUPERVISOR_SECRET", "should-never-reach-tmux")
    monkeypatch.setenv("TERM", "supervisor-term-must-not-flow-through")
    calls = []

    expected_options = {
        "@clayverse_managed_policy": manager.MANAGED_TMUX_POLICY_ID,
        "prefix": "None",
        "prefix2": "None",
        "status": "off",
        "mouse": "off",
        "default-shell": str(manager.DIRECT_SHELL_GUARD),
    }

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        if "has-session" in argv:
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="")
        if "show-options" in argv:
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=expected_options[argv[-1]] + "\n",
                stderr="",
            )
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    binding = manager.ensure("gabriel")

    expected_env = {
        "HOME": str(binding.home),
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "TERM": "xterm-256color",
        "LANG": "C.UTF-8",
    }
    assert calls
    assert any("new-session" in argv for argv, _ in calls)
    assert any("source-file" in argv for argv, _ in calls)
    assert any("show-options" in argv for argv, _ in calls)
    for argv, kwargs in calls:
        assert argv[0] == "tmux"
        assert kwargs["env"] == expected_env
        assert "GLM_API_TOKEN" not in kwargs["env"]
        assert "GITHUB_READ_TOKEN" not in kwargs["env"]
        assert "CLERK_ISSUER" not in kwargs["env"]
        assert "UNRELATED_SUPERVISOR_SECRET" not in kwargs["env"]
