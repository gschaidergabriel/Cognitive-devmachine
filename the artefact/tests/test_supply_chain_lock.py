from __future__ import annotations
import importlib.util
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def _installer():
    path = ROOT / "build" / "install_pinned_claude.py"
    spec = importlib.util.spec_from_file_location("install_pinned_claude", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _archive(entries=(('bundle/claude', b'bin'),)):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tf:
        for name, payload in entries:
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            info.mode = 0o755
            tf.addfile(info, io.BytesIO(payload))
    return out.getvalue()


def test_docker_uses_digest_pinned_native_claude_release():
    lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text())
    docker = (ROOT / "Dockerfile").read_text()
    assert lock["claude_code"]["version"] == "2.1.233"
    assert "@anthropic-ai/claude-code" not in docker
    assert "CLAUDE_CODE_SPEC" not in docker
    assert 'npm install --global "${XTERM_SPEC}"' in docker
    assert "install_pinned_claude.py" in docker
    assert lock["base_image"]["index_digest"] in docker


def test_build_context_admits_lock_and_installer_but_not_receipts_or_state():
    ignore = (ROOT / ".dockerignore").read_text().splitlines()
    assert "!SOURCE_LOCK.json" in ignore
    assert "!build/install_pinned_claude.py" in ignore
    assert not any(x in ignore for x in ("!receipts/", "!tests/", ".git"))


def test_installer_accepts_only_locked_architectures_and_sha_shape(monkeypatch):
    mod = _installer()
    monkeypatch.setattr(mod, "LOCK_PATH", ROOT / "SOURCE_LOCK.json")
    monkeypatch.setenv("TARGETARCH", "amd64")
    version, asset, digest = mod.load_config()
    assert version == "2.1.233" and asset == "claude-linux-x64.tar.gz" and len(digest) == 64
    monkeypatch.setenv("TARGETARCH", "arm64")
    _, asset2, digest2 = mod.load_config()
    assert asset2 == "claude-linux-arm64.tar.gz" and len(digest2) == 64
    monkeypatch.setenv("TARGETARCH", "386")
    try:
        mod.load_config()
    except SystemExit:
        pass
    else:
        raise AssertionError("unsupported architecture did not fail closed")


def test_installer_extracts_exactly_one_regular_claude_binary(tmp_path):
    mod = _installer()
    target = tmp_path / "claude"
    mod.install_archive(_archive(), target)
    assert target.read_bytes() == b"bin"
    assert target.stat().st_mode & 0o111


def test_installer_rejects_path_traversal_and_links():
    mod = _installer()
    for member in (tarfile.TarInfo("../claude"), tarfile.TarInfo("/claude")):
        class Fake:
            def getmembers(self):
                return [member]
        try:
            mod.safe_members(Fake())
        except SystemExit:
            pass
        else:
            raise AssertionError("unsafe member accepted")
    link = tarfile.TarInfo("bundle/claude")
    link.type = tarfile.SYMTYPE
    link.linkname = "/bin/sh"
    class LinkFake:
        def getmembers(self):
            return [link]
    try:
        mod.safe_members(LinkFake())
    except SystemExit:
        pass
    else:
        raise AssertionError("symlink member accepted")


def test_installer_rejects_ambiguous_duplicate_claude(tmp_path):
    mod = _installer()
    target = tmp_path / "claude"
    archive = _archive((("a/claude", b"first"), ("b/claude", b"second")))
    try:
        mod.install_archive(archive, target)
    except SystemExit as exc:
        assert "exactly one Claude binary" in str(exc)
    else:
        raise AssertionError("ambiguous archive was accepted")
    assert not target.exists()
