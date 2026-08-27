import json
import stat

from clayverse.adapters import ClaudeCodeInference


def test_claude_code_adapter_forces_pinned_safe_mode(tmp_path, monkeypatch):
    log = tmp_path / "args.json"
    fake = tmp_path / "claude"
    home = tmp_path / "home"
    home.mkdir()
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os,sys\n"
        f"open({str(log)!r},'w').write(json.dumps({{'args':sys.argv[1:],'env':dict(os.environ)}}))\n"
        "print(json.dumps({'structured_output':{'text':'ok','effect':None}}))\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("HOME", str(home))

    result = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "hello")
    payload = json.loads(log.read_text())
    args = payload["args"]
    env = payload["env"]

    assert result == {"text": "ok", "selection": "respond", "effect": None}
    assert args[0] == "--safe-mode"
    assert args[args.index("--tools") + 1] == ""
    assert "--strict-mcp-config" in args
    assert "--no-session-persistence" in args
    assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
    assert env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] == "1"
    assert env["HOME"] == str(home)
