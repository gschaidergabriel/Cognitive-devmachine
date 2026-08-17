from types import SimpleNamespace

from clayverse.terminal_sessions import TerminalSessionManager


def test_api_provider_window_uses_same_tmux_and_secretless_env(tmp_path, monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "must-not-enter-pane")
    monkeypatch.setenv("CLAYVERSE_LLM_API_TOKEN", "also-must-not-enter-pane")

    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: True)
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)

    display_calls = 0
    new_window = None

    def fake_run(argv, **kwargs):
        nonlocal display_calls, new_window
        if "display-message" in argv:
            display_calls += 1
            if display_calls == 1:
                return SimpleNamespace(returncode=1, stdout="", stderr="missing")
            return SimpleNamespace(returncode=0, stdout="4242\n", stderr="")
        if "new-window" in argv:
            new_window = list(argv)
            assert kwargs["env"] == manager._tmux_control_env()
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(argv)

    monkeypatch.setattr("clayverse.terminal_sessions.subprocess.run", fake_run)
    registered = {}

    def register_peer(**kwargs):
        registered.update(kwargs)

    binding, target, pid = manager.ensure_api_provider(
        "gabriel",
        "/tmp/clayverse/provider.sock",
        register_peer,
    )

    assert binding.tmux_name in target
    assert target.endswith(":" + manager.API_PROVIDER_WINDOW)
    assert pid == 4242
    assert registered == {
        "user_id": "gabriel",
        "session_id": "session:gabriel",
        "pid": 4242,
    }
    assert new_window is not None
    rendered = "\n".join(new_window)
    assert "new-window" in new_window
    assert binding.tmux_name in new_window
    assert manager.API_PROVIDER_WINDOW in new_window
    assert "env" in new_window and "-i" in new_window
    assert "CLAYVERSE_PROVIDER_BROKER_SOCKET=/tmp/clayverse/provider.sock" in new_window
    assert "must-not-enter-pane" not in rendered
    assert "also-must-not-enter-pane" not in rendered
    assert "MISTRAL_API_KEY" not in rendered
    assert "CLAYVERSE_LLM_API_TOKEN" not in rendered
