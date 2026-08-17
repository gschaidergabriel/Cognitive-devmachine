import ast
from pathlib import Path

import pytest

from clayverse.api_probe_cli import (
    _create_acceptance_snapshot,
    _final_required_effect_policy,
    _restore_before_db_open,
)
from clayverse.identity import IdentityRouter
from clayverse.logical_snapshot import LogicalSnapshotManager
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


def test_final_required_effect_defaults_to_entityos_when_effect_is_required(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_REQUIRE_EFFECT", "1")
    monkeypatch.delenv("CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY", raising=False)
    assert _final_required_effect_policy() == (True, "entityos.exec")


def test_final_required_effect_rejects_generic_noop_acceptance_credit(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_REQUIRE_EFFECT", "1")
    monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_REQUIRED_EFFECT_CAPABILITY", "state.noop")
    with pytest.raises(RuntimeError, match="only be entityos.exec"):
        _final_required_effect_policy()


def test_generic_api_cli_restores_snapshot_before_unifieddb_open():
    source = (
        Path(__file__).resolve().parents[1] / "clayverse" / "api_probe_cli.py"
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
        if isinstance(node.func, ast.Name) and node.func.id == "_restore_before_db_open":
            restore_line = node.lineno
        if isinstance(node.func, ast.Name) and node.func.id == "UnifiedDB":
            db_line = node.lineno
    assert restore_line is not None and db_line is not None
    assert restore_line < db_line


def test_acceptance_snapshot_and_restore_share_exact_runtime_identity(tmp_path, monkeypatch):
    source_root = tmp_path / "source"
    db = UnifiedDB(source_root / "unified.db")
    try:
        IdentityRouter(db, {})
        sid = db.ensure_session("gabriel", "terminal-gabriel")
        db.append_turn(sid, "gabriel", "user", "provider-generic recovery")
        monkeypatch.setenv("CLAYVERSE_ACCEPTANCE_CREATE_SNAPSHOT", "1")
        monkeypatch.setattr("clayverse.api_probe_cli.collect_runtime_identity", _runtime_identity)
        receipt = _create_acceptance_snapshot(db)
        assert receipt["created"] is True
        snapshot_dir = source_root / "snapshots" / receipt["snapshot_id"]
        assert LogicalSnapshotManager(source_root).validate(snapshot_dir)["runtime_identity"] == _runtime_identity()
    finally:
        db.close()

    target_root = tmp_path / "target"
    monkeypatch.setenv("CLAYVERSE_RESTORE_SNAPSHOT_DIR", str(snapshot_dir))
    restore = _restore_before_db_open(str(target_root))
    assert restore["restored"] is True
    assert restore["snapshot_id"] == receipt["snapshot_id"]
    assert (target_root / "unified.db").is_file()
