import json
import stat
from pathlib import Path

import pytest

from clayverse.adapters import ClaudeCodeInference


def _write_probe(path: Path, log: Path) -> None:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os,stat\n"
        "from pathlib import Path\n"
        "cfg=Path(os.environ['CLAUDE_CONFIG_DIR'])\n"
        "cred=cfg/'.credentials.json'\n"
        f"Path({str(log)!r}).write_text(json.dumps({{"
        "'home':os.environ['HOME'],"
        "'config':os.environ['CLAUDE_CONFIG_DIR'],"
        "'oauth_present':bool(os.environ.get('CLAUDE_CODE_OAUTH_TOKEN'))," 
        "'cred_exists':cred.exists(),"
        "'cred_mode':oct(stat.S_IMODE(cred.stat().st_mode)) if cred.exists() else None,"
        "'ambient_claude_md':(cfg/'CLAUDE.md').exists()"
        "}}))\n"
        "print(json.dumps({'structured_output':{'text':'ok','effect':None}}))\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_ephemeral_home_copies_only_bounded_credentials_and_is_removed(tmp_path, monkeypatch):
    source_home = tmp_path / "source-home"
    source_config = source_home / ".claude"
    source_config.mkdir(parents=True)
    credential = source_config / ".credentials.json"
    credential.write_text('{"oauth":"dummy"}')
    credential.chmod(0o600)
    (source_config / "CLAUDE.md").write_text("AMBIENT USER MEMORY")

    log = tmp_path / "child.json"
    fake = tmp_path / "claude"
    _write_probe(fake, log)

    monkeypatch.setenv("HOME", str(source_home))
    monkeypatch.setenv("CLERK_SECRET_KEY", "must-not-cross-cognition-boundary")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)

    out = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "hello")
    assert out == {"text": "ok", "selection": "respond", "effect": None}

    payload = json.loads(log.read_text())
    child_home = Path(payload["home"])
    assert child_home != source_home
    assert payload["config"] == str(child_home / ".claude")
    assert payload["cred_exists"] is True
    assert payload["cred_mode"] == "0o600"
    assert payload["ambient_claude_md"] is False
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
    _write_probe(fake, log)

    monkeypatch.setenv("HOME", str(source_home))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "dummy-oauth-token")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)

    out = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "hello")
    assert out["text"] == "ok"
    payload = json.loads(log.read_text())
    assert payload["oauth_present"] is True
    assert payload["cred_exists"] is False
