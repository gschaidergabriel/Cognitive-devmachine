import hashlib
import json
import stat

import clayverse.service as service
from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.store import UnifiedDB


def test_enabled_mcp_ignores_runtime_entityos_path_and_digest_redirect(monkeypatch, tmp_path):
    state_root = tmp_path / "state"
    state_root.mkdir()
    db = UnifiedDB(state_root / "unified.db")
    IdentityRouter(db, {})
    db.close()

    trusted_root = tmp_path / "image" / "opt" / "entityos"
    trusted_root.mkdir(parents=True)
    trusted = trusted_root / "EntityOS"
    trusted_payload = b"#!/bin/sh\nexit 0\n"
    trusted.write_bytes(trusted_payload)
    trusted.chmod(trusted.stat().st_mode | stat.S_IXUSR)
    trusted_digest = hashlib.sha256(trusted_payload).hexdigest()
    lock = trusted_root / "entityos.lock.json"
    lock.write_text(
        json.dumps(
            {
                "schema": "ClayVerseEntityOSArtifactLock/v1",
                "sha256": trusted_digest,
                "size_bytes": len(trusted_payload),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(service, "_ENTITYOS_PATH", str(trusted))
    monkeypatch.setattr(service, "_ENTITYOS_LOCK_PATH", str(lock))

    attacker = tmp_path / "workspace" / "EntityOS"
    attacker.parent.mkdir()
    attacker_payload = b"#!/bin/sh\nexit 77\n"
    attacker.write_bytes(attacker_payload)
    attacker.chmod(attacker.stat().st_mode | stat.S_IXUSR)

    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(state_root))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(attacker))
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", hashlib.sha256(attacker_payload).hexdigest())

    bridge = ClayVerseEffectBridge.from_env()
    try:
        entityos = bridge.lifecycle.effects.entityos_bridge
        assert entityos is not None
        assert entityos.path == str(trusted)
        assert entityos.sha256 == trusted_digest
        assert entityos.path != str(attacker)
    finally:
        bridge.db.close()
