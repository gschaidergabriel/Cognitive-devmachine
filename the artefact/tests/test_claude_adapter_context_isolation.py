import json
import stat
from pathlib import Path

import pytest

from clayverse.adapters import ClaudeCodeInference


def _fake_claude(path: Path, log: Path) -> None:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os,stat,sys\n"
        "from pathlib import Path\n"
        "cfg=Path(os.environ['CLAUDE_CONFIG_DIR'])\n"
        "cred=cfg/'.credentials.json'\n"
        f"Path({str(log)!r}).write_text(json.dumps({{"
        "'args':sys.argv[1:],"
        "'env':dict(os.environ),"
        "'cred_exists':cred.exists(),"
        "'cred_mode':oct(stat.S_IMODE(cred.stat().st_mode)) if cred.exists() else None,"
        "'ambient_claude_md':(cfg/'CLAUDE.md').exists()"
        "}}))\n"
        "print(json.dumps({'structured_output':{'text':'ok','effect':None}}))\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_context_authority_fence_uses_ephemeral_home_and_credential_only_copy(tmp_path, monkeypatch):
    source_home = tmp_path / "source-home"
    source_config = source_home / ".claude"
    source_config.mkdir(parents=True)
    credential = source_config / ".credentials.json"
    credential.write_text('{"oauth":"dummy"}')
    credential.chmod(0o600)
    (source_config / "CLAUDE.md").write_text("AMBIENT USER MEMORY")

    log = tmp_path / "child.json"
    fake = tmp_path / "claude"
    _fake_claude(fake, log)

    monkeypatch.setenv("HOME", str(source_home))
    monkeypatch.setenv("CLERK_SECRET_KEY", "must-not-cross-cognition-boundary")
    monkeypatch.setenv("RANDOM_DATABASE_PASSWORD", "must-not-cross-either")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)

    out = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "hello")
    assert out == {"text": "ok", "selection": "respond", "effect": None}

    payload = json.loads(log.read_text())
    args = payload["args"]
    env = payload["env"]
    child_home = Path(env["HOME"])

    assert args[args.index("--setting-sources") + 1] == ""
    assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
    assert env["CLAUDE_CODE_DISABLE_AGENT_VIEW"] == "1"
    assert env["CLAUDE_CODE_SKIP_PROMPT_HISTORY"] == "1"
    assert child_home != source_home
    assert env["CLAUDE_CONFIG_DIR"] == str(child_home / ".claude")
    assert payload["cred_exists"] is True
    assert payload["cred_mode"] == "0o600"
    assert payload["ambient_claude_md"] is False
    assert "CLERK_SECRET_KEY" not in env
    assert "RANDOM_DATABASE_PASSWORD" not in env
    assert not child_home.exists()
    assert credential.read_text() == '{"oauth":"dummy"}'


def test_symlinked_ambient_credentials_fail_closed_before_claude_start(tmp_path, monkeypatch):
    source_home = tmp_path / "source-home"
    source_config = source_home / ".claude"
    source_config.mkdir(parents=True)
    real_secret = tmp_path / "real-secret"
    real_secret.write_text("dummy")
    (source_config / ".credentials.json").symlink_to(real_secret)

    marker = tmp_path / "CLAUDE_STARTED"
    fake = tmp_path / "claude"
    fake.write_text(f"#!/bin/sh\ntouch {marker}\nexit 0\n")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("HOME", str(source_home))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)

    with pytest.raises(RuntimeError, match="credential source"):
        ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "hello")
    assert not marker.exists()


def test_explicit_oauth_token_avoids_ambient_credential_copy(tmp_path, monkeypatch):
    source_home = tmp_path / "source-home"
    source_config = source_home / ".claude"
    source_config.mkdir(parents=True)
    (source_config / ".credentials.json").write_text("ambient-dummy")

    log = tmp_path / "oauth-child.json"
    fake = tmp_path / "claude"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os\n"
        "from pathlib import Path\n"
        "cfg=Path(os.environ['CLAUDE_CONFIG_DIR'])\n"
        f"Path({str(log)!r}).write_text(json.dumps({{"
        "'oauth_present':bool(os.environ.get('CLAUDE_CODE_OAUTH_TOKEN'))," 
        "'cred_exists':(cfg/'.credentials.json').exists()"
        "}}))\n"
        "print(json.dumps({'structured_output':{'text':'ok','effect':None}}))\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("HOME", str(source_home))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "dummy-oauth-token")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)

    out = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "hello")
    assert out["text"] == "ok"
    assert json.loads(log.read_text()) == {"oauth_present": True, "cred_exists": False}
