import os
from pathlib import Path

import pytest

from clay_vps_mcp import server


def configure_tmp(monkeypatch, tmp_path: Path):
    root = tmp_path / "root"
    state = tmp_path / "state"
    root.mkdir()
    state.mkdir()
    monkeypatch.setenv("CLAY_MCP_ALLOWED_ROOTS", str(root))
    monkeypatch.setenv("CLAY_MCP_STATE_DIR", str(state))
    return root, state


def test_resolve_rejects_escape(monkeypatch, tmp_path):
    root, _ = configure_tmp(monkeypatch, tmp_path)
    assert server._resolve(str(root / "x")) == root / "x"
    with pytest.raises(PermissionError):
        server._resolve(str(tmp_path / "outside"))


def test_destructive_executables_are_denied(monkeypatch, tmp_path):
    configure_tmp(monkeypatch, tmp_path)
    for exe in ["rm", "shred", "wipefs", "mkfs.ext4", "fdisk", "dd", "dropdb"]:
        with pytest.raises(PermissionError):
            server._allowed_executable(exe)


def test_destructive_git_patterns_are_denied(monkeypatch, tmp_path):
    configure_tmp(monkeypatch, tmp_path)
    bad = [
        ["git", "reset", "--hard", "HEAD~1"],
        ["git", "clean", "-fdx"],
        ["git", "push", "--force", "origin", "main"],
        ["git", "checkout", "-f", "main"],
    ]
    for argv in bad:
        with pytest.raises(PermissionError):
            server._validate_argv(argv)


def test_existing_write_requires_cas_and_keeps_backup(monkeypatch, tmp_path):
    root, state = configure_tmp(monkeypatch, tmp_path)
    p = root / "a.txt"
    p.write_text("old", encoding="utf-8")
    old_sha = server._sha256(p)
    with pytest.raises(PermissionError):
        server.write_text_file(str(p), "new")
    result = server.write_text_file(str(p), "new", expected_sha256=old_sha)
    assert p.read_text(encoding="utf-8") == "new"
    assert result["prior_sha256"] == old_sha
    backup = Path(result["backup"])
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == "old"
    assert str(backup).startswith(str(state))


def test_create_only_is_non_overwriting(monkeypatch, tmp_path):
    root, _ = configure_tmp(monkeypatch, tmp_path)
    p = root / "new.txt"
    result = server.write_text_file(str(p), "one", create_only=True)
    assert result["prior_sha256"] is None
    with pytest.raises(FileExistsError):
        server.write_text_file(str(p), "two", create_only=True)


def test_python_eval_is_denied():
    with pytest.raises(PermissionError):
        server._validate_argv(["python3", "-c", "print(1)"])


def test_mcp_token_is_required(monkeypatch):
    monkeypatch.delenv("CLAY_MCP_TOKEN", raising=False)
    assert os.getenv("CLAY_MCP_TOKEN") is None
