from pathlib import Path

import pytest

from clayverse.identity import IdentityRouter
from clayverse.logical_snapshot import LogicalSnapshotIntegrityError, LogicalSnapshotManager
from clayverse.recovery import recover_incomplete_episodes
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


def _snapshot(tmp_path: Path, *, pending_effect: bool = False):
    source_root = tmp_path / "source"
    db = UnifiedDB(source_root / "unified.db")
    IdentityRouter(db, {})
    sid = db.ensure_session("gabriel", "terminal-gabriel")
    db.append_turn(sid, "gabriel", "user", "persist across appliance recreation")
    if pending_effect:
        db.db.execute(
            "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) VALUES('pending-before-recreate',NULL,'gabriel','entityos.exec','redacted-test-target',NULL,?,'PENDING',NULL,1.0,NULL)",
            (db.entity_generation(),),
        )
    manager = LogicalSnapshotManager(source_root)
    manifest = manager.create(db, runtime_identity=_runtime_identity(), reason="tier1-recreate")
    snapshot_dir = manager.root / manifest["snapshot_id"]
    db.close()
    return snapshot_dir, manifest


def test_restore_fresh_stages_exact_db_without_opening_second_authority(tmp_path):
    snapshot_dir, manifest = _snapshot(tmp_path)
    target_root = tmp_path / "restored"
    receipt = LogicalSnapshotManager(target_root).restore_fresh(
        snapshot_dir, runtime_identity=_runtime_identity()
    )
    assert receipt["restored"] is True
    assert receipt["snapshot_id"] == manifest["snapshot_id"]
    assert receipt["database_sha256"] == manifest["database"]["sha256"]
    assert (target_root / "unified.db").is_file()
    assert not (target_root / "unified.db-wal").exists()
    assert not (target_root / "unified.db-shm").exists()

    restored = UnifiedDB(target_root / "unified.db")
    try:
        row = restored.db.execute(
            "SELECT content FROM turns WHERE role='user' ORDER BY ordinal LIMIT 1"
        ).fetchone()
        assert row["content"] == "persist across appliance recreation"
    finally:
        restored.close()


def test_restore_rejects_runtime_identity_mismatch_without_writing_state(tmp_path):
    snapshot_dir, _ = _snapshot(tmp_path)
    target_root = tmp_path / "wrong-runtime"
    changed = _runtime_identity()
    changed["image_digest"] = "sha256:" + "9" * 64
    with pytest.raises(LogicalSnapshotIntegrityError, match="runtime identity"):
        LogicalSnapshotManager(target_root).restore_fresh(snapshot_dir, runtime_identity=changed)
    assert not target_root.exists()


def test_restore_refuses_existing_or_symlinked_live_target(tmp_path):
    snapshot_dir, _ = _snapshot(tmp_path)
    target_root = tmp_path / "occupied"
    target_root.mkdir()
    (target_root / "unified.db").write_bytes(b"existing-live-state")
    with pytest.raises(LogicalSnapshotIntegrityError, match="fresh UnifiedDB target"):
        LogicalSnapshotManager(target_root).restore_fresh(
            snapshot_dir, runtime_identity=_runtime_identity()
        )
    assert (target_root / "unified.db").read_bytes() == b"existing-live-state"

    real_root = tmp_path / "real-root"
    real_root.mkdir()
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(real_root, target_is_directory=True)
    with pytest.raises(LogicalSnapshotIntegrityError, match="real directory"):
        LogicalSnapshotManager(linked_root).restore_fresh(
            snapshot_dir, runtime_identity=_runtime_identity()
        )


def test_restored_pending_effect_becomes_unknown_after_restart_without_replay(tmp_path):
    snapshot_dir, manifest = _snapshot(tmp_path, pending_effect=True)
    target_root = tmp_path / "recovered"
    LogicalSnapshotManager(target_root).restore_fresh(
        snapshot_dir, runtime_identity=_runtime_identity()
    )

    restored = UnifiedDB(target_root / "unified.db")
    try:
        before = restored.entity_generation()
        assert before == manifest["state"]["entity_generation"]
        recovery = recover_incomplete_episodes(restored)
        row = restored.db.execute(
            "SELECT status,outcome FROM effects WHERE effect_id='pending-before-recreate'"
        ).fetchone()
        assert row["status"] == "UNKNOWN_AFTER_RESTART"
        assert "restart_before_verified_outcome" in row["outcome"]
        causal = restored.db.execute(
            "SELECT credit,reentered FROM causal_episodes WHERE effect_id='pending-before-recreate'"
        ).fetchone()
        assert float(causal["credit"]) == 0.0
        assert int(causal["reentered"]) == 1
        assert recovery["generation"] == before + 1
        assert restored.entity_generation() == before + 1
    finally:
        restored.close()
