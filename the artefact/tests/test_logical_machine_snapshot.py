import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.logical_snapshot import LogicalSnapshotIntegrityError, LogicalSnapshotManager
from clayverse.store import UnifiedDB


def _runtime_identity():
    return {
        "source_revision": "1" * 40,
        "image_digest": "sha256:" + "2" * 64,
        "entityos_sha256": "3" * 64,
        "managed_settings_sha256": "4" * 64,
        "managed_mcp_sha256": "5" * 64,
        "runtime_claude_md_sha256": "6" * 64,
        "claude_identity": "claude-code:test-pinned",
        "tmux_identity": "tmux:test-pinned",
    }


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    sid = db.ensure_session("gabriel", "terminal-gabriel")
    db.append_turn(sid, "gabriel", "user", "persist me")
    return db


def _snapshot_dir(manager, manifest):
    return manager.root / manifest["snapshot_id"]


def test_snapshot_is_self_contained_and_binds_checkpoint_generation_and_runtime(tmp_path):
    db = _db(tmp_path)
    try:
        manager = LogicalSnapshotManager(tmp_path)
        manifest = manager.create(db, runtime_identity=_runtime_identity(), reason="boot-ready")
        snapshot_dir = _snapshot_dir(manager, manifest)
        assert manifest["schema"] == "ClayVerseKnownGoodLogicalMachineSnapshot/v1"
        assert manifest["state"]["entity_generation"] == db.entity_generation()
        assert manifest["state"]["checkpoint_anchor"]["note"] == "logical-snapshot:boot-ready"
        assert manifest["runtime_identity"] == _runtime_identity()
        assert (snapshot_dir / "unified.db").is_file()
        assert not (snapshot_dir / "unified.db-wal").exists()
        assert not (snapshot_dir / "unified.db-shm").exists()
        assert manager.validate(snapshot_dir) == manifest
    finally:
        db.close()


def test_snapshot_manifest_never_serializes_effect_payload(tmp_path):
    db = _db(tmp_path)
    try:
        manager = LogicalSnapshotManager(tmp_path)
        secret = "DO-NOT-SERIALIZE-THIS-EFFECT-PAYLOAD"
        db.db.execute(
            "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) VALUES('effect:test',NULL,'gabriel','state.noop',?,?,?,'DENIED',?,1.0,NULL)",
            (secret, json.dumps([secret]), db.entity_generation(), json.dumps({"reason": secret})),
        )
        manifest = manager.create(db, runtime_identity=_runtime_identity(), reason="effect-redaction")
        text = (_snapshot_dir(manager, manifest) / "manifest.json").read_text()
        assert secret not in text
        assert manifest["state"]["effect_journal"]["count"] == 1
        assert manifest["state"]["effect_journal"]["status_counts"] == {"DENIED": 1}
    finally:
        db.close()


def test_snapshot_database_tamper_fails_closed(tmp_path):
    db = _db(tmp_path)
    try:
        manager = LogicalSnapshotManager(tmp_path)
        manifest = manager.create(db, runtime_identity=_runtime_identity(), reason="tamper")
        db_path = _snapshot_dir(manager, manifest) / "unified.db"
        original = db_path.read_bytes()
        db_path.write_bytes(original[: len(original) // 2])
        with pytest.raises(LogicalSnapshotIntegrityError, match="digest/size"):
            manager.validate(_snapshot_dir(manager, manifest))
    finally:
        db.close()


def test_manifest_generation_drift_fails_closed(tmp_path):
    db = _db(tmp_path)
    try:
        manager = LogicalSnapshotManager(tmp_path)
        manifest = manager.create(db, runtime_identity=_runtime_identity(), reason="manifest-drift")
        manifest_path = _snapshot_dir(manager, manifest) / "manifest.json"
        edited = json.loads(manifest_path.read_text())
        edited["state"]["entity_generation"] += 1
        manifest_path.write_text(json.dumps(edited, sort_keys=True, separators=(",", ":")) + "\n")
        with pytest.raises(LogicalSnapshotIntegrityError, match="manifest/state drift"):
            manager.validate(_snapshot_dir(manager, manifest))
    finally:
        db.close()


def test_corrupt_newest_snapshot_falls_back_to_previous_valid_snapshot(tmp_path):
    db = _db(tmp_path)
    try:
        manager = LogicalSnapshotManager(tmp_path)
        first = manager.create(db, runtime_identity=_runtime_identity(), reason="first")
        db.append_turn("session:gabriel", "gabriel", "user", "newer state")
        second = manager.create(db, runtime_identity=_runtime_identity(), reason="second")
        (_snapshot_dir(manager, second) / "unified.db").write_bytes(b"corrupt")
        selected = manager.latest_valid()
        assert selected is not None
        assert selected["snapshot_id"] == first["snapshot_id"]
    finally:
        db.close()


def test_snapshot_rejects_incomplete_or_malformed_runtime_identity(tmp_path):
    db = _db(tmp_path)
    try:
        manager = LogicalSnapshotManager(tmp_path)
        missing = _runtime_identity()
        missing.pop("entityos_sha256")
        with pytest.raises(LogicalSnapshotIntegrityError, match="fields incomplete"):
            manager.create(db, runtime_identity=missing, reason="bad-runtime")
        malformed = _runtime_identity()
        malformed["image_digest"] = "latest"
        with pytest.raises(LogicalSnapshotIntegrityError, match="image_digest"):
            manager.create(db, runtime_identity=malformed, reason="bad-runtime")
    finally:
        db.close()


def test_snapshot_member_symlink_is_rejected(tmp_path):
    db = _db(tmp_path)
    try:
        manager = LogicalSnapshotManager(tmp_path)
        manifest = manager.create(db, runtime_identity=_runtime_identity(), reason="symlink")
        snapshot_dir = _snapshot_dir(manager, manifest)
        manifest_path = snapshot_dir / "manifest.json"
        real = snapshot_dir / "manifest.real"
        manifest_path.rename(real)
        manifest_path.symlink_to(real.name)
        with pytest.raises(LogicalSnapshotIntegrityError, match="snapshot member invalid"):
            manager.validate(snapshot_dir)
    finally:
        db.close()
