import json
import stat

from clayverse.adapters import ClaudeCodeInference


def test_claude_memory_authority_is_fail_closed_even_if_parent_enables_memory(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".claude").mkdir()
    (home / ".claude" / "CLAUDE.md").write_text("POISON_USER_MEMORY", encoding="utf-8")
    memory = home / ".claude" / "projects" / "repo" / "memory"
    memory.mkdir(parents=True)
    (memory / "MEMORY.md").write_text("POISON_AUTO_MEMORY", encoding="utf-8")

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "oauth-kept")
    monkeypatch.setenv("CLERK_SECRET_KEY", "must-not-cross")
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_AUTO_MEMORY", "0")
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_CLAUDE_MDS", "0")

    env = ClaudeCodeInference._subprocess_env()

    assert env["HOME"] == str(home)
    assert env["ANTHROPIC_AUTH_TOKEN"] == "oauth-kept"
    assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
    assert env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] == "1"
    assert env["CLAUDE_CODE_SKIP_PROMPT_HISTORY"] == "1"
    assert "CLERK_SECRET_KEY" not in env


def test_claude_memory_authority_guards_reach_the_subprocess(tmp_path, monkeypatch):
    log = tmp_path / "env.json"
    fake = tmp_path / "claude"
    home = tmp_path / "home"
    home.mkdir()
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os\n"
        f"open({str(log)!r}, 'w').write(json.dumps(dict(os.environ)))\n"
        "print(json.dumps({'structured_output': {'text': 'ok', 'effect': None}}))\n",
        encoding="utf-8",
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "oauth-kept")
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_AUTO_MEMORY", "0")
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_CLAUDE_MDS", "0")

    out = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "hello")
    child = json.loads(log.read_text(encoding="utf-8"))

    assert out["text"] == "ok"
    assert child["HOME"] == str(home)
    assert child["ANTHROPIC_AUTH_TOKEN"] == "oauth-kept"
    assert child["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
    assert child["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] == "1"
