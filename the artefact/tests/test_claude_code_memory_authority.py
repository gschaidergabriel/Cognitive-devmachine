import json
import stat

from clayverse.adapters import ClaudeCodeInference


def test_targeted_claude_inference_retains_auth_home_but_forces_no_durable_memory(monkeypatch, tmp_path):
    home = tmp_path / "claude-auth-home"
    home.mkdir()

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "allowed-auth-token")
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_AUTO_MEMORY", "0")
    monkeypatch.setenv("CLAUDE_CODE_SKIP_PROMPT_HISTORY", "0")
    monkeypatch.setenv("CLERK_SECRET_KEY", "must-not-cross")

    env = ClaudeCodeInference._subprocess_env()

    # Auth state remains addressable through the intentionally retained HOME/token.
    assert env["HOME"] == str(home)
    assert env["ANTHROPIC_AUTH_TOKEN"] == "allowed-auth-token"

    # The cognition subprocess cannot inherit caller attempts to re-enable durable
    # Claude-side memory/history: the adapter overwrites both controls fail-closed.
    assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
    assert env["CLAUDE_CODE_SKIP_PROMPT_HISTORY"] == "1"

    # Unrelated product/auth secrets remain outside the cognition boundary.
    assert "CLERK_SECRET_KEY" not in env


def test_targeted_claude_inference_excludes_user_project_local_setting_sources(monkeypatch, tmp_path):
    log = tmp_path / "args.json"
    fake = tmp_path / "claude"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json,sys\n"
        f"open({str(log)!r},'w').write(json.dumps(sys.argv[1:]))\n"
        "print(json.dumps({'structured_output':{'text':'ok','effect':None}}))\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

    home = tmp_path / "auth-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    result = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "probe")
    args = json.loads(log.read_text())

    assert result == {"text": "ok", "selection": "respond", "effect": None}
    assert args[args.index("--setting-sources") + 1] == ""
    assert "--no-session-persistence" in args
    assert args[args.index("--tools") + 1] == ""
