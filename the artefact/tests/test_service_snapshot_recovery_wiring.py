import ast
from pathlib import Path

from clayverse.identity import IdentityRouter
from clayverse.service import _acceptance_snapshot, _snapshot_restore_before_db_open
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


def test_service_calls_snapshot_restore_before_unifieddb_open():
    source = (
        Path(__file__).resolve().parents[1] / "clayverse" / "service.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    main = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    restore_line = None
    db_line = None
    for node in ast.walk(main):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "_snapshot_restore_before_db_open":
            restore_line = node.lineno
        if isinstance(node.func, ast.Name) and node.func.id == "UnifiedDB":
            db_line = node.lineno
    assert restore_line is not None
    assert db_line is not None
    assert restore_line < db_line


def test_acceptance_snapshot_is_explicit_and_uses_measured_runtime_identity(tmp_path, monkeypatch):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        sid = db.ensure_session("gabriel", "terminal-gabriel")
        db.append_turn(sid, "gabriel", "user", "snapshot after final cognition")
        monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_CREATE_SNAPSHOT", "1")
        monkeypatch.setattr("clayverse.service.collect_runtime_identity", _runtime_identity)

        receipt = _acceptance_snapshot(db)

        assert receipt["created"] is True
        assert receipt["snapshot_id"].startswith("snapshot-")
        assert len(receipt["database_sha256"]) == 64
        assert len(receipt["state_hash"]) == 64
        snapshot_dir = tmp_path / "snapshots" / receipt["snapshot_id"]
        assert (snapshot_dir / "unified.db").is_file()
        assert (snapshot_dir / "manifest.json").is_file()
    finally:
        db.close()


def test_restore_entrypoint_uses_measured_runtime_identity_and_exact_snapshot(tmp_path, monkeypatch):
    source_root = tmp_path / "source"
    source_db = UnifiedDB(source_root / "unified.db")
    try:
        IdentityRouter(source_db, {})
        sid = source_db.ensure_session("gabriel", "terminal-gabriel")
        source_db.append_turn(sid, "gabriel", "user", "restore through service pre-open path")
        monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_CREATE_SNAPSHOT", "1")
        monkeypatch.setattr("clayverse.service.collect_runtime_identity", _runtime_identity)
        receipt = _acceptance_snapshot(source_db)
        snapshot_dir = source_root / "snapshots" / receipt["snapshot_id"]
    finally:
        source_db.close()

    target_root = tmp_path / "target"
    monkeypatch.setenv("CLAYVERSE_RESTORE_SNAPSHOT_DIR", str(snapshot_dir))
    restore = _snapshot_restore_before_db_open(str(target_root))
    assert restore["restored"] is True
    assert restore["snapshot_id"] == receipt["snapshot_id"]
    assert (target_root / "unified.db").is_file()
