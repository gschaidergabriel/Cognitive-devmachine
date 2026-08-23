import json
import stat
from pathlib import Path

from clayverse.adapters import ClaudeCodeInference


def _invoke_boundary_probe(tmp_path, monkeypatch):
    log = tmp_path / "claude-boundary.json"
    fake = tmp_path / "claude"
    sentinel = tmp_path / "SHOULD_NOT_EXIST"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os,sys\n"
        f"open({str(log)!r},'w').write(json.dumps({{'args':sys.argv[1:],'env':dict(os.environ)}}))\n"
        "print(json.dumps({'structured_output':{'text':'ok','effect':None}}))\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("CLERK_SECRET_KEY", "must-not-cross-cognition-boundary")
    monkeypatch.setenv("RANDOM_DATABASE_PASSWORD", "must-not-cross-either")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "allowed-auth")

    observation = f"hello; touch {sentinel}"
    out = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason(
        {"shared": "state"}, observation
    )
    payload = json.loads(log.read_text())
    return out, payload["args"], payload["env"], observation, sentinel


def test_claude_code_adapter_toolless_boundary(tmp_path, monkeypatch):
    _, args, _, observation, sentinel = _invoke_boundary_probe(tmp_path, monkeypatch)

    assert "--bare" not in args
    assert args[args.index("--permission-mode") + 1] == "plan"
    assert args[args.index("--tools") + 1] == ""
    assert "--strict-mcp-config" in args

    prompt = args[args.index("-p") + 1]
    assert observation in prompt
    assert not Path(sentinel).exists()


def test_claude_code_adapter_ephemeral_boundary(tmp_path, monkeypatch):
    _, args, _, _, _ = _invoke_boundary_probe(tmp_path, monkeypatch)

    assert "-p" in args
    assert args[args.index("--max-turns") + 1] == "1"
    assert "--no-session-persistence" in args


def test_claude_code_adapter_structured_output_boundary(tmp_path, monkeypatch):
    out, args, _, _, _ = _invoke_boundary_probe(tmp_path, monkeypatch)

    assert out == {"text": "ok", "selection": "respond", "effect": None}
    assert "--json-schema" in args
    schema = json.loads(args[args.index("--json-schema") + 1])
    capability = schema["properties"]["effect"]["anyOf"][1]["properties"]["capability"]
    assert set(capability["enum"]) == {"entityos.exec", "state.noop"}


def test_claude_code_adapter_environment_isolation_boundary(tmp_path, monkeypatch):
    _, _, env, _, _ = _invoke_boundary_probe(tmp_path, monkeypatch)

    assert env["CLAUDE_CODE_SKIP_PROMPT_HISTORY"] == "1"
    assert env["DISABLE_AUTOUPDATER"] == "1"
    assert env["ANTHROPIC_API_KEY"] == "allowed-auth"
    assert "HOME" in env
    assert "CLERK_SECRET_KEY" not in env
    assert "RANDOM_DATABASE_PASSWORD" not in env
