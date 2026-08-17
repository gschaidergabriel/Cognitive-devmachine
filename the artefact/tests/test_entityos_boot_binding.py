import hashlib
import json
import stat

import pytest

from clayverse import service as service_module
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


def _stage_locked_entityos(monkeypatch, tmp_path, payload=b"#!/bin/sh\nexit 0\n"):
    binary = tmp_path / "EntityOS"
    binary.write_bytes(payload)
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    digest = hashlib.sha256(payload).hexdigest()
    lock_path = tmp_path / "entityos.lock.json"
    lock_path.write_text(
        json.dumps(
            {
                "schema": "ClayVerseEntityOSArtifactLock/v1",
                "sha256": digest,
                "size_bytes": len(payload),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(service_module, "_ENTITYOS_PATH", str(binary))
    monkeypatch.setattr(service_module, "_ENTITYOS_LOCK_PATH", str(lock_path))
    return binary, lock_path, digest, payload


def test_staged_entityos_is_verified_from_embedded_lock_when_execution_disabled(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    _, lock_path, digest, payload = _stage_locked_entityos(monkeypatch, tmp_path)

    bridge, status = _entityos_config()
    assert bridge is None
    assert status["staged"] is True
    assert status["verified"] is True
    assert status["execution_enabled"] is False
    assert status["artifact_authority"] == "embedded-lock"
    assert status["lock_path"] == str(lock_path)
    assert status["sha256"] == digest
    assert status["size"] == len(payload)


def test_entityos_execution_binding_uses_exact_embedded_lock(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    _, _, digest, payload = _stage_locked_entityos(monkeypatch, tmp_path)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")

    bridge, status = _entityos_config()
    assert isinstance(bridge, EntityOSBridge)
    assert bridge.sha256 == digest
    assert status["execution_enabled"] is True
    assert status["sha256"] == digest
    assert status["size"] == len(payload)


def test_runtime_path_cannot_override_embedded_entityos(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    _stage_locked_entityos(monkeypatch, tmp_path)
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(tmp_path / "attacker-EntityOS"))

    with pytest.raises(RuntimeError, match="cannot override the embedded EntityOS path"):
        _entityos_config()


def test_runtime_digest_cannot_override_embedded_entityos_lock(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    _stage_locked_entityos(monkeypatch, tmp_path)
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "0" * 64)

    with pytest.raises(RuntimeError, match="cannot override the embedded EntityOS lock"):
        _entityos_config()


def test_matching_runtime_assertions_are_accepted_but_do_not_select_identity(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    binary, _, digest, _ = _stage_locked_entityos(monkeypatch, tmp_path)
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(binary))
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", digest.upper())

    bridge, status = _entityos_config()
    assert bridge is None
    assert status["artifact_authority"] == "embedded-lock"
    assert status["sha256"] == digest


@pytest.mark.parametrize(
    "lock_doc,error",
    [
        ({}, "schema is invalid"),
        ({"schema": "wrong", "sha256": "0" * 64, "size_bytes": 1}, "schema is invalid"),
        ({"schema": "ClayVerseEntityOSArtifactLock/v1", "sha256": "nope", "size_bytes": 1}, "SHA-256 is invalid"),
        ({"schema": "ClayVerseEntityOSArtifactLock/v1", "sha256": "0" * 64, "size_bytes": 0}, "size is invalid"),
    ],
)
def test_malformed_embedded_lock_fails_closed(monkeypatch, tmp_path, lock_doc, error):
    _clear_entityos_env(monkeypatch)
    binary = tmp_path / "EntityOS"
    binary.write_bytes(b"x")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    lock_path = tmp_path / "entityos.lock.json"
    lock_path.write_text(json.dumps(lock_doc), encoding="utf-8")
    monkeypatch.setattr(service_module, "_ENTITYOS_PATH", str(binary))
    monkeypatch.setattr(service_module, "_ENTITYOS_LOCK_PATH", str(lock_path))

    with pytest.raises(RuntimeError, match=error):
        _entityos_config()


def test_missing_or_invalid_lock_fails_closed(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    binary = tmp_path / "EntityOS"
    binary.write_bytes(b"x")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    lock_path = tmp_path / "entityos.lock.json"
    monkeypatch.setattr(service_module, "_ENTITYOS_PATH", str(binary))
    monkeypatch.setattr(service_module, "_ENTITYOS_LOCK_PATH", str(lock_path))

    with pytest.raises(RuntimeError, match="embedded EntityOS lock unavailable"):
        _entityos_config()

    lock_path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(RuntimeError, match="embedded EntityOS lock unavailable"):
        _entityos_config()


def test_entityos_boot_rejects_digest_drift_from_locked_bytes(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    binary, _, _, _ = _stage_locked_entityos(monkeypatch, tmp_path)
    binary.write_bytes(b"not the locked bytes")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)

    with pytest.raises(RuntimeError, match="verification failed"):
        _entityos_config()


def test_entityos_boot_rejects_size_drift_even_when_digest_is_consistent(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    _, lock_path, digest, payload = _stage_locked_entityos(monkeypatch, tmp_path)
    lock_path.write_text(
        json.dumps(
            {
                "schema": "ClayVerseEntityOSArtifactLock/v1",
                "sha256": digest,
                "size_bytes": len(payload) + 1,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="embedded size does not match lock"):
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
