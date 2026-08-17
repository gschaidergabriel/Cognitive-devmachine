import hashlib
import os
import stat

import pytest

from clayverse.entityos_bridge import EntityOSBridge, EntityOSIntegrityError
from clayverse.service import _entityos_config


def _clear_entityos_env(monkeypatch):
    for name in (
        "CLAYVERSE_REQUIRE_ENTITYOS",
        "CLAYVERSE_ENABLE_ENTITYOS_EXEC",
        "CLAYVERSE_ENTITYOS_PATH",
        "CLAYVERSE_ENTITYOS_SHA256",
    ):
        monkeypatch.delenv(name, raising=False)


def test_entityos_config_allows_absent_optional_baseline(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(tmp_path / "EntityOS"))

    bridge, status = _entityos_config()

    assert bridge is None
    assert status == {
        "staged": False,
        "verified": False,
        "execution_enabled": False,
    }


def test_entityos_config_rejects_unpinned_bytes_even_when_execution_disabled(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    binary = tmp_path / "EntityOS"
    binary.write_bytes(b"untrusted")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(binary))

    with pytest.raises(RuntimeError, match="unpinned EntityOS bytes"):
        _entityos_config()


def test_entityos_config_rejects_execution_without_digest_binding(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(tmp_path / "EntityOS"))

    with pytest.raises(RuntimeError, match="requires an embedded SHA-256 pin"):
        _entityos_config()


def test_staged_entityos_is_verified_but_not_bound_when_execution_disabled(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    binary = tmp_path / "EntityOS"
    payload = b"#!/bin/sh\nexit 0\n"
    binary.write_bytes(payload)
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    digest = hashlib.sha256(payload).hexdigest()

    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(binary))
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", digest)

    bridge, status = _entityos_config()
    assert bridge is None
    assert status["staged"] is True
    assert status["verified"] is True
    assert status["execution_enabled"] is False
    assert status["sha256"] == digest
    assert status["size"] == len(payload)


def test_entityos_config_rejects_sha_without_path_and_relative_binding(monkeypatch):
    _clear_entityos_env(monkeypatch)
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match="path is required"):
        _entityos_config()

    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", "EntityOS")
    with pytest.raises(RuntimeError, match="must be absolute"):
        _entityos_config()


def test_entityos_bridge_boot_binds_exact_executable_only_when_execution_enabled(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    binary = tmp_path / "EntityOS"
    payload = b"#!/bin/sh\nexit 0\n"
    binary.write_bytes(payload)
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    digest = hashlib.sha256(payload).hexdigest()

    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(binary))
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", digest)

    bridge, status = _entityos_config()
    assert isinstance(bridge, EntityOSBridge)
    assert status["execution_enabled"] is True
    assert status["verified"] is True
    assert status["sha256"] == digest
    assert status["size"] == len(payload)


def test_entityos_bridge_boot_rejects_digest_drift(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    binary = tmp_path / "EntityOS"
    binary.write_bytes(b"not the pinned bytes")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(binary))
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "0" * 64)

    with pytest.raises(RuntimeError, match="verification failed"):
        _entityos_config()


def test_entityos_bridge_verify_rejects_symlink(tmp_path):
    real = tmp_path / "real"
    real.write_bytes(b"x")
    real.chmod(real.stat().st_mode | stat.S_IXUSR)
    link = tmp_path / "EntityOS"
    link.symlink_to(real)
    bridge = EntityOSBridge(str(link), hashlib.sha256(b"x").hexdigest())
    with pytest.raises(EntityOSIntegrityError):
        bridge.verify()
