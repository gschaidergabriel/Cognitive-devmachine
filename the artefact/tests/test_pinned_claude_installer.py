from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "build" / "install_pinned_claude.py"
SPEC = importlib.util.spec_from_file_location("install_pinned_claude", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class _Response:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.read_size = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size=-1):
        self.read_size = size
        return self.payload if size < 0 else self.payload[:size]


def test_load_config_binds_exact_release_asset_size(tmp_path, monkeypatch):
    payload = b"claude-archive"
    lock = {
        "claude_code": {
            "version": "2.1.233",
            "linux_amd64": {
                "asset": "claude-linux-x64.tar.gz",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            },
        }
    }
    path = tmp_path / "SOURCE_LOCK.json"
    path.write_text(json.dumps(lock), encoding="utf-8")
    monkeypatch.setattr(installer, "LOCK_PATH", path)
    monkeypatch.setenv("TARGETARCH", "amd64")

    version, asset, digest, size = installer.load_config()
    assert version == "2.1.233"
    assert asset == "claude-linux-x64.tar.gz"
    assert digest == hashlib.sha256(payload).hexdigest()
    assert size == len(payload)


def test_fetch_verified_reads_only_locked_size_plus_one(monkeypatch):
    payload = b"locked-release-bytes"
    response = _Response(payload)
    monkeypatch.setattr(installer.urllib.request, "urlopen", lambda *args, **kwargs: response)

    observed = installer.fetch_verified(
        "https://example.invalid/claude.tar.gz",
        hashlib.sha256(payload).hexdigest(),
        len(payload),
    )
    assert observed == payload
    assert response.read_size == len(payload) + 1


def test_fetch_verified_rejects_oversized_response_before_digest(monkeypatch):
    expected = b"12345678"
    response = _Response(expected + b"X")
    monkeypatch.setattr(installer.urllib.request, "urlopen", lambda *args, **kwargs: response)

    with pytest.raises(SystemExit, match="archive size mismatch"):
        installer.fetch_verified(
            "https://example.invalid/claude.tar.gz",
            hashlib.sha256(expected).hexdigest(),
            len(expected),
        )
    assert response.read_size == len(expected) + 1


def test_fetch_verified_rejects_undersized_response(monkeypatch):
    expected = b"12345678"
    response = _Response(expected[:-1])
    monkeypatch.setattr(installer.urllib.request, "urlopen", lambda *args, **kwargs: response)

    with pytest.raises(SystemExit, match="archive size mismatch"):
        installer.fetch_verified(
            "https://example.invalid/claude.tar.gz",
            hashlib.sha256(expected).hexdigest(),
            len(expected),
        )


def test_load_config_rejects_missing_or_unbounded_size(tmp_path, monkeypatch):
    digest = hashlib.sha256(b"x").hexdigest()
    monkeypatch.setenv("TARGETARCH", "amd64")
    for size in (None, 0, installer.MAX_ARCHIVE_BYTES + 1):
        item = {"asset": "claude-linux-x64.tar.gz", "sha256": digest}
        if size is not None:
            item["size_bytes"] = size
        path = tmp_path / f"lock-{size}.json"
        path.write_text(json.dumps({"claude_code": {"version": "2.1.233", "linux_amd64": item}}), encoding="utf-8")
        monkeypatch.setattr(installer, "LOCK_PATH", path)
        with pytest.raises(SystemExit, match="archive size lock"):
            installer.load_config()
