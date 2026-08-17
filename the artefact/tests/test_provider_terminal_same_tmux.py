from types import SimpleNamespace

from clayverse.terminal_sessions import TerminalSessionManager


def test_api_provider_is_canonical_secretless_tmux_session_process(tmp_path, monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "must-not-enter-pane")
    monkeypatch.setenv("CLAYVERSE_LLM_API_TOKEN", "also-must-not-enter-pane")

    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setattr(manager, "_set_provider_marker", lambda binding, provider: None)
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_pane_pid", lambda binding, target: 4242)
    monkeypatch.setattr(manager, "_assert_single_provider_pane", lambda binding, pid: None)

    new_session = None

    def fake_run(argv, **kwargs):
        nonlocal new_session
        if "new-session" in argv:
            new_session = list(argv)
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

    assert target == binding.tmux_name
    assert pid == 4242
    assert registered == {
        "user_id": "gabriel",
        "session_id": "session:gabriel",
        "pid": 4242,
    }
    assert new_session is not None
    rendered = "\n".join(new_session)
    assert "new-session" in new_session
    assert "new-window" not in new_session
    assert binding.tmux_name in new_session
    assert "env" in new_session and "-i" in new_session
    assert "CLAYVERSE_PROVIDER_BROKER_SOCKET=/tmp/clayverse/provider.sock" in new_session
    assert "python3" in new_session
    assert "clayverse.provider_terminal" in new_session
    assert "must-not-enter-pane" not in rendered
    assert "also-must-not-enter-pane" not in rendered
    assert "MISTRAL_API_KEY" not in rendered
    assert "CLAYVERSE_LLM_API_TOKEN" not in rendered
