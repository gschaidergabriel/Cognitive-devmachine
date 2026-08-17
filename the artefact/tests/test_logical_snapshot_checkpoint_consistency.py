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


def test_snapshot_rejects_state_written_after_checkpoint_before_backup(tmp_path, monkeypatch):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        sid = db.ensure_session("gabriel", "terminal-gabriel")
        db.append_turn(sid, "gabriel", "user", "checkpoint state")
        original_checkpoint = db.checkpoint

        def checkpoint_then_interleave(note):
            checkpoint_id, state_hash = original_checkpoint(note)
            db.append_turn(sid, "gabriel", "user", "interleaved after checkpoint")
            return checkpoint_id, state_hash

        monkeypatch.setattr(db, "checkpoint", checkpoint_then_interleave)

        with pytest.raises(LogicalSnapshotIntegrityError, match="checkpoint.*state.*drift"):
            LogicalSnapshotManager(tmp_path).create(
                db,
                runtime_identity=_runtime_identity(),
                reason="checkpoint-race",
            )
    finally:
        db.close()
