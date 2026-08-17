from types import SimpleNamespace

from clayverse.terminal_sessions import TerminalSessionManager


def test_tmux_control_environment_never_inherits_service_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-secret-must-not-reach-tmux")
    monkeypatch.setenv("CLAYVERSE_LLM_API_TOKEN", "generic-secret-must-not-reach-tmux")
    monkeypatch.setenv("CLERK_SECRET_KEY", "clerk-secret-must-not-reach-tmux")
    monkeypatch.setenv("GITHUB_READ_TOKEN", "source-secret-must-not-reach-tmux")

    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    seen_envs = []

    def fake_run(argv, **kwargs):
        env = kwargs.get("env")
        seen_envs.append(dict(env or {}))
        assert env == {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "TERM": "xterm-256color",
            "LANG": "C.UTF-8",
        }
        for secret_name in (
            "MISTRAL_API_KEY",
            "CLAYVERSE_LLM_API_TOKEN",
            "CLERK_SECRET_KEY",
            "GITHUB_READ_TOKEN",
        ):
            assert secret_name not in env

        if "has-session" in argv:
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if "source-file" in argv or "new-session" in argv or "list-keys" in argv:
            rendered = "\n".join(argv)
            assert "secret-must-not-reach-tmux" not in rendered
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if "show-options" in argv:
            if "@clayverse_managed_policy" in argv:
                value = manager.MANAGED_TMUX_POLICY_ID
            elif "prefix" in argv or "prefix2" in argv:
                value = "None"
            elif "status" in argv:
                value = "off"
            elif "mouse" in argv:
                value = "off"
            elif "default-shell" in argv:
                value = str(manager.DIRECT_SHELL_GUARD)
            else:
                raise AssertionError(argv)
            return SimpleNamespace(returncode=0, stdout=value + "\n", stderr="")
        raise AssertionError(argv)

    monkeypatch.setattr("clayverse.terminal_sessions.subprocess.run", fake_run)

    binding = manager.ensure("gabriel")
    assert binding.user_id == "gabriel"
    assert seen_envs
