import json
import stat

from clayverse.adapters import ClaudeCodeInference


def test_claude_subprocess_environment_is_explicitly_isolated(tmp_path, monkeypatch):
    env_log = tmp_path / "env.json"
    fake = tmp_path / "claude"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os\n"
        f"open({str(env_log)!r}, 'w').write(json.dumps(dict(os.environ), sort_keys=True))\n"
        "print(json.dumps({'structured_output': {'text': 'ok', 'effect': None}}))\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("CLERK_JWT_KEY", "clerk-jwt-secret")
    monkeypatch.setenv("CLERK_SECRET_KEY", "clerk-backend-secret")
    monkeypatch.setenv("CLAYVERSE_CLERK_MAP_JSON", "identity-map-secret")
    monkeypatch.setenv("RANDOM_APP_SECRET", "unrelated-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-child-auth")
    monkeypatch.setenv("ANTHROPIC_MODEL", "test-model")

    out = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason(
        {"shared": "state"},
        "hello",
    )

    child_env = json.loads(env_log.read_text())
    assert out == {"text": "ok", "selection": "respond", "effect": None}
    assert child_env["ANTHROPIC_API_KEY"] == "anthropic-child-auth"
    assert child_env["ANTHROPIC_MODEL"] == "test-model"
    assert child_env["CLAUDE_CODE_SKIP_PROMPT_HISTORY"] == "1"
    assert child_env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] == "1"
    assert child_env["DISABLE_TELEMETRY"] == "1"
    assert child_env["DISABLE_ERROR_REPORTING"] == "1"
    assert child_env["DISABLE_BUG_COMMAND"] == "1"
    assert "CLERK_JWT_KEY" not in child_env
    assert "CLERK_SECRET_KEY" not in child_env
    assert "CLAYVERSE_CLERK_MAP_JSON" not in child_env
    assert "RANDOM_APP_SECRET" not in child_env
