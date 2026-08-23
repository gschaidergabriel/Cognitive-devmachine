import hashlib
import json
import stat

import pytest

from clayverse.entityos_bridge import EntityOSBridge, EntityOSIntegrityError
import clayverse.service as service


def _clear_entityos_env(monkeypatch):
    for name in (
        "CLAYVERSE_ENABLE_ENTITYOS_EXEC",
        "CLAYVERSE_ENTITYOS_PATH",
        "CLAYVERSE_ENTITYOS_SHA256",
    ):
        monkeypatch.delenv(name, raising=False)


def _install_image_owned_candidate(monkeypatch, tmp_path, payload=b"#!/bin/sh\nexit 0\n"):
    root = tmp_path / "image" / "opt" / "entityos"
    root.mkdir(parents=True)
    binary = root / "EntityOS"
    binary.write_bytes(payload)
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    digest = hashlib.sha256(payload).hexdigest()
    lock = root / "entityos.lock.json"
    lock.write_text(
        json.dumps(
            {
                "schema": "ClayVerseEntityOSArtifactLock/v1",
                "sha256": digest,
                "size_bytes": len(payload),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(service, "_ENTITYOS_PATH", str(binary))
    monkeypatch.setattr(service, "_ENTITYOS_LOCK_PATH", str(lock))
    return binary, lock, digest


def test_entityos_config_fails_closed_when_embedded_lock_is_missing(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    monkeypatch.setattr(service, "_ENTITYOS_PATH", str(tmp_path / "EntityOS"))
    monkeypatch.setattr(service, "_ENTITYOS_LOCK_PATH", str(tmp_path / "missing.lock.json"))
    with pytest.raises(RuntimeError, match="embedded EntityOS lock open failed"):
        service._entityos_config()


def test_staged_entityos_is_verified_but_execution_disabled_by_default(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    binary, lock, digest = _install_image_owned_candidate(monkeypatch, tmp_path)

    bridge, status = service._entityos_config()
    assert bridge is None
    assert status["staged"] is True
    assert status["verified"] is True
    assert status["execution_enabled"] is False
    assert status["authority"] == "image_embedded_lock"
    assert status["path"] == str(binary)
    assert status["lock_path"] == str(lock)
    assert status["sha256"] == digest


def test_entityos_exec_enable_binds_only_image_owned_candidate(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    binary, _, digest = _install_image_owned_candidate(monkeypatch, tmp_path)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")

    bridge, status = service._entityos_config()
    assert isinstance(bridge, EntityOSBridge)
    assert bridge.path == str(binary)
    assert bridge.sha256 == digest
    assert status["execution_enabled"] is True


def test_runtime_path_and_digest_environment_cannot_redirect_entityos(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    trusted, _, trusted_digest = _install_image_owned_candidate(monkeypatch, tmp_path)

    attacker = tmp_path / "workspace" / "EntityOS"
    attacker.parent.mkdir()
    attacker_payload = b"#!/bin/sh\nexit 77\n"
    attacker.write_bytes(attacker_payload)
    attacker.chmod(attacker.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(attacker))
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", hashlib.sha256(attacker_payload).hexdigest())
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")

    bridge, status = service._entityos_config()
    assert isinstance(bridge, EntityOSBridge)
    assert bridge.path == str(trusted)
    assert bridge.sha256 == trusted_digest
    assert status["path"] == str(trusted)
    assert status["sha256"] == trusted_digest
    assert str(attacker) not in status.values()


def test_entityos_config_rejects_embedded_size_drift(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    _, lock, _ = _install_image_owned_candidate(monkeypatch, tmp_path)
    doc = json.loads(lock.read_text(encoding="utf-8"))
    doc["size_bytes"] += 1
    lock.write_text(json.dumps(doc), encoding="utf-8")

    with pytest.raises(RuntimeError, match="embedded size does not match image lock"):
        service._entityos_config()


def test_entityos_config_rejects_malformed_embedded_lock(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    _, lock, _ = _install_image_owned_candidate(monkeypatch, tmp_path)
    lock.write_text('{"schema":"wrong","sha256":"0"}', encoding="utf-8")

    with pytest.raises(RuntimeError, match="lock schema is invalid"):
        service._entityos_config()


def test_entityos_config_rejects_symlinked_embedded_lock(monkeypatch, tmp_path):
    _clear_entityos_env(monkeypatch)
    _, lock, _ = _install_image_owned_candidate(monkeypatch, tmp_path)
    real_lock = lock.with_name("real.lock.json")
    lock.rename(real_lock)
    lock.symlink_to(real_lock)

    with pytest.raises(RuntimeError, match="lock open failed"):
        service._entityos_config()


def test_entityos_bridge_verify_rejects_symlink(tmp_path):
    real = tmp_path / "real"
    real.write_bytes(b"x")
    real.chmod(real.stat().st_mode | stat.S_IXUSR)
    link = tmp_path / "EntityOS"
    link.symlink_to(real)
    bridge = EntityOSBridge(str(link), hashlib.sha256(b"x").hexdigest())
    with pytest.raises(EntityOSIntegrityError):
        bridge.verify()
