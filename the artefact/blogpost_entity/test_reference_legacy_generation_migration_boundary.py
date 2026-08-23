from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def _db_profile_convergence_active() -> bool:
    return hasattr(ProfilePipelineRuntime, "_pipeline_profile_read")


def _legacy_only_db(path: Path, generation: int) -> None:
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE eos_pipeline_state(
          singleton INTEGER PRIMARY KEY CHECK(singleton=1),
          generation INTEGER NOT NULL DEFAULT 0,
          continuity_json TEXT NOT NULL DEFAULT '{}',
          canonical_json TEXT NOT NULL DEFAULT '{}',
          canonical_hash TEXT NOT NULL DEFAULT '',
          cursors_json TEXT NOT NULL DEFAULT '{}',
          updated_at REAL NOT NULL DEFAULT 0);
        INSERT INTO eos_pipeline_state(singleton,generation) VALUES(1,0);
        """
    )
    db.execute(
        "UPDATE eos_pipeline_state SET generation=? WHERE singleton=1",
        (generation,),
    )
    db.commit()
    db.close()


def _canonical_rows(path: Path) -> int | None:
    db = sqlite3.connect(path)
    try:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entity_state'"
        ).fetchone()
        if exists is None:
            return None
        return int(db.execute("SELECT COUNT(*) FROM entity_state").fetchone()[0])
    finally:
        db.close()


@pytest.mark.skipif(
    not _db_profile_convergence_active(),
    reason="activates when DB-profile/current-effect reference convergence lands",
)
def test_legacy_only_generation_requires_explicit_migration_adjudication(tmp_path: Path) -> None:
    """Never turn unresolved legacy continuity into a fresh canonical generation zero.

    Current generation-authority law forbids the legacy reference mirror from becoming
    live canonical authority. The complementary boundary is that an old DB carrying a
    nonzero legacy generation but no native entity_state is *not* a fresh DB either.
    Bootstrap must fail closed and leave canonical state uncreated until an explicit,
    separately admitted migration/adjudication path resolves that historical state.
    """
    entity_db = tmp_path / "entity.db"
    _legacy_only_db(entity_db, generation=7)

    runtime = ProfilePipelineRuntime(root=tmp_path)
    result = runtime._pipeline_init({"entity_db": str(entity_db)})

    assert result["ok"] is False
    assert "LEGACY_GENERATION_MIGRATION_REQUIRED" in str(result.get("error", ""))

    db = sqlite3.connect(entity_db)
    try:
        legacy = db.execute(
            "SELECT generation FROM eos_pipeline_state WHERE singleton=1"
        ).fetchone()
        assert legacy is not None and int(legacy[0]) == 7
    finally:
        db.close()

    assert _canonical_rows(entity_db) in (None, 0), (
        "unresolved legacy state created a canonical entity_state row before migration adjudication"
    )


@pytest.mark.skipif(
    not _db_profile_convergence_active(),
    reason="activates when DB-profile/current-effect reference convergence lands",
)
def test_truly_fresh_db_may_initialize_native_generation_zero(tmp_path: Path) -> None:
    """Fail-closed legacy handling must not make a genuinely fresh DB unusable."""
    entity_db = tmp_path / "fresh.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)

    result = runtime._pipeline_init({"entity_db": str(entity_db)})
    assert result["ok"] is True

    db = sqlite3.connect(entity_db)
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
        assert row is not None and int(row[0]) == 0
    finally:
        db.close()
