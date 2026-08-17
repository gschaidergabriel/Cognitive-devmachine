import json

import pytest

from clayverse import service as service_module


def _valid_lock():
    return {
        "schema": "ClayVerseEntityOSArtifactLock/v1",
        "sha256": "a" * 64,
        "size_bytes": 1,
    }


def test_entityos_lock_reader_rejects_symlink(monkeypatch, tmp_path):
    real = tmp_path / "real-lock.json"
    real.write_text(json.dumps(_valid_lock()), encoding="utf-8")
    link = tmp_path / "entityos.lock.json"
    link.symlink_to(real)
    monkeypatch.setattr(service_module, "_ENTITYOS_LOCK_PATH", str(link))

    with pytest.raises(RuntimeError, match="embedded EntityOS lock unavailable"):
        service_module._load_entityos_lock()


def test_entityos_lock_reader_rejects_non_regular_file(monkeypatch, tmp_path):
    monkeypatch.setattr(service_module, "_ENTITYOS_LOCK_PATH", str(tmp_path))

    with pytest.raises(RuntimeError, match="must be a regular file"):
        service_module._load_entityos_lock()


def test_entityos_lock_reader_rejects_oversized_file(monkeypatch, tmp_path):
    lock_path = tmp_path / "entityos.lock.json"
    lock_path.write_bytes(b"x" * (service_module._ENTITYOS_LOCK_MAX_BYTES + 1))
    monkeypatch.setattr(service_module, "_ENTITYOS_LOCK_PATH", str(lock_path))

    with pytest.raises(RuntimeError, match="lock file size is invalid"):
        service_module._load_entityos_lock()


def test_entityos_lock_reader_normalizes_valid_uppercase_digest(monkeypatch, tmp_path):
    lock_path = tmp_path / "entityos.lock.json"
    lock = _valid_lock()
    lock["sha256"] = "A" * 64
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    monkeypatch.setattr(service_module, "_ENTITYOS_LOCK_PATH", str(lock_path))

    loaded = service_module._load_entityos_lock()
    assert loaded == {"sha256": "a" * 64, "size_bytes": 1}
