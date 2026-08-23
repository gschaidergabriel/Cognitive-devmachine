import json
import stat

from clayverse.adapters import ClaudeCodeInference


def test_claude_code_targeted_inference_uses_safe_mode_without_losing_home(tmp_path, monkeypatch):
    log = tmp_path / "probe.json"
    fake = tmp_path / "claude"
    home = tmp_path / "auth-home"
    home.mkdir()
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os,sys\n"
        f"open({str(log)!r}, 'w').write(json.dumps({{'args':sys.argv[1:], 'env':dict(os.environ)}}))\n"
        "print(json.dumps({'structured_output':{'text':'ok','effect':None}}))\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "allowed-auth")
    monkeypatch.setenv("UNRELATED_SECRET", "must-not-cross")

    out = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "probe")
    payload = json.loads(log.read_text())
    args = payload["args"]
    env = payload["env"]

    assert out == {"text": "ok", "selection": "respond", "effect": None}
    assert "--safe-mode" in args
    assert "--no-session-persistence" in args
    assert "--strict-mcp-config" in args
    assert args[args.index("--tools") + 1] == ""
    assert "--bare" not in args
    assert env["HOME"] == str(home)
    assert env["CLAUDE_CODE_SKIP_PROMPT_HISTORY"] == "1"
    assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
    assert "UNRELATED_SECRET" not in env
