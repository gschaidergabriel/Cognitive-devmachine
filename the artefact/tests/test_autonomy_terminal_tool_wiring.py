from __future__ import annotations

from types import SimpleNamespace

from clayverse.terminal_sessions import TerminalSessionManager


def test_managed_claude_launch_allows_exact_autonomy_effect_tool(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)

    calls = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("clayverse.terminal_sessions.subprocess.run", fake_run)

    manager.ensure("gabriel")

    assert len(calls) == 1
    argv = calls[0]
    assert "claude" in argv
    allowed_index = argv.index("--allowedTools")
    permission_index = argv.index("--permission-mode")
    allowed = argv[allowed_index + 1 : permission_index]
    assert allowed == [
        "mcp__clayverse__session_state",
        "mcp__clayverse__request_effect",
        "mcp__clayverse__request_autonomy_effect",
    ]
    assert allowed.count("mcp__clayverse__request_autonomy_effect") == 1


def test_existing_tmux_reuse_does_not_spawn_second_claude_process(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)

    def forbidden_run(*args, **kwargs):
        raise AssertionError("existing persistent tmux session must not spawn another Claude")

    monkeypatch.setattr("clayverse.terminal_sessions.subprocess.run", forbidden_run)
    binding = manager.ensure("gabriel")
    assert binding.session_id == "session:gabriel"
