from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def test_nonempty_legacy_consumed_ledger_requires_explicit_namespace_migration(tmp_path: Path) -> None:
    """Do not manufacture source identity while upgrading the exactly-once key.

    Legacy rows contain only (source_kind, source_id). Once current semantics distinguish
    stable logical source namespaces, a non-empty legacy ledger cannot in general be mapped
    losslessly: different logical sources may have reused both fields. With no provenance in
    this fixture that can disambiguate the row, init must fail closed and preserve the ledger
    rather than dropping it, assigning an invented namespace, or silently re-consuming it.
    """
    entity_db = tmp_path / "legacy-consumed.db"
    with sqlite3.connect(entity_db) as db:
        db.execute(
            """CREATE TABLE eos_pipeline_consumed(
                 source_kind TEXT NOT NULL,
                 source_id TEXT NOT NULL,
                 output_id TEXT NOT NULL,
                 consumed_at REAL NOT NULL,
                 PRIMARY KEY(source_kind,source_id))"""
        )
        db.execute(
            "INSERT INTO eos_pipeline_consumed(source_kind,source_id,output_id,consumed_at) "
            "VALUES('event','1','old-output',1.0)"
        )
        db.commit()

    runtime = ProfilePipelineRuntime(root=tmp_path)
    result = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})

    assert result["ok"] is False
    assert "CONSUMED_SOURCE_NAMESPACE_MIGRATION_REQUIRED" in str(result.get("error", ""))

    with sqlite3.connect(entity_db) as db:
        columns = [str(row[1]) for row in db.execute("PRAGMA table_info(eos_pipeline_consumed)")]
        row = db.execute(
            "SELECT source_kind,source_id,output_id,consumed_at FROM eos_pipeline_consumed"
        ).fetchone()
        assert columns == ["source_kind", "source_id", "output_id", "consumed_at"]
        assert row == ("event", "1", "old-output", 1.0)
