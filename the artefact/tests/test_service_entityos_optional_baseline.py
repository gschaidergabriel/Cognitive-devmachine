from __future__ import annotations

import pytest

import clayverse.service as service
from clayverse.service import _entityos_config


def _configure_absent(monkeypatch, path):
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(path))
    monkeypatch.delenv("CLAYVERSE_ENTITYOS_SHA256", raising=False)


def test_optional_entityos_baseline_starts_without_artifact(monkeypatch, tmp_path):
    path = tmp_path / "EntityOS"
    _configure_absent(monkeypatch, path)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")

    bridge, status = _entityos_config()

    assert bridge is None
    assert status == {
        "staged": False,
        "verified": False,
        "execution_enabled": False,
    }


def test_optional_entityos_cannot_enable_execution_without_pin(monkeypatch, tmp_path):
    _configure_absent(monkeypatch, tmp_path / "EntityOS")
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")

    with pytest.raises(RuntimeError, match="requires an embedded SHA-256 pin"):
        _entityos_config()


def test_unpinned_entityos_bytes_fail_closed_even_when_execution_disabled(monkeypatch, tmp_path):
    path = tmp_path / "EntityOS"
    path.write_bytes(b"untrusted")
    _configure_absent(monkeypatch, path)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")

    with pytest.raises(RuntimeError, match="unpinned EntityOS bytes"):
        _entityos_config()


def test_unpinned_entityos_symlink_fails_closed(monkeypatch, tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"untrusted")
    path = tmp_path / "EntityOS"
    path.symlink_to(target)
    _configure_absent(monkeypatch, path)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")

    with pytest.raises(RuntimeError, match="unpinned EntityOS bytes"):
        _entityos_config()


class _VerifiedBridge:
    def __init__(self, *, path, sha256):
        self.path = path
        self.sha256 = sha256

    def verify(self):
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size": 7,
            "mode": 0o555,
            "snapshot": "test-verified",
        }


def test_pinned_entityos_stays_verified_but_unexposed_when_execution_disabled(monkeypatch, tmp_path):
    path = tmp_path / "EntityOS"
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(path))
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "a" * 64)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setattr(service, "EntityOSBridge", _VerifiedBridge)

    bridge, status = _entityos_config()

    assert bridge is None
    assert status["staged"] is True
    assert status["verified"] is True
    assert status["execution_enabled"] is False
    assert status["sha256"] == "a" * 64


def test_pinned_entityos_bridge_is_exposed_only_when_execution_enabled(monkeypatch, tmp_path):
    path = tmp_path / "EntityOS"
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(path))
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "b" * 64)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")
    monkeypatch.setattr(service, "EntityOSBridge", _VerifiedBridge)

    bridge, status = _entityos_config()

    assert isinstance(bridge, _VerifiedBridge)
    assert status["staged"] is True
    assert status["verified"] is True
    assert status["execution_enabled"] is True
    assert status["sha256"] == "b" * 64
