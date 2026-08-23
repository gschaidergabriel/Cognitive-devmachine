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


def _db_profile_reference_active() -> bool:
    return hasattr(ProfilePipelineRuntime, "_pipeline_profile_read")


def _make_legacy_only_db(path: Path, generation: int) -> None:
    db = sqlite3.connect(path)
    try:
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
    finally:
        db.close()


def _canonical_generation_if_materialized(path: Path) -> int | None:
    db = sqlite3.connect(path)
    try:
        table = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entity_state'"
        ).fetchone()
        if table is None:
            return None
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
        return None if row is None else int(row[0])
    finally:
        db.close()


def _legacy_generation(path: Path) -> int:
    db = sqlite3.connect(path)
    try:
        row = db.execute(
            "SELECT generation FROM eos_pipeline_state WHERE singleton=1"
        ).fetchone()
        assert row is not None
        return int(row[0])
    finally:
        db.close()


@pytest.mark.skipif(
    not _db_profile_reference_active(),
    reason="activates only when DB-profile reference convergence is present",
)
def test_fail_closed_legacy_migration_is_atomic_and_repeatable(tmp_path: Path) -> None:
    """A migration-required failure must not partially materialize canonical generation.

    Current main permits either a correct one-shot preservation migration or an explicit
    fail-closed migration-required outcome. This regression covers only the latter branch:
    failure must be side-effect-safe, preserve legacy evidence, and remain fail-closed on
    immediate retry rather than becoming admissible because init wrote generation zero first.
    """
    entity_db = tmp_path / "legacy_only.db"
    _make_legacy_only_db(entity_db, generation=7)
    runtime = ProfilePipelineRuntime(root=tmp_path)

    first = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    if first.get("ok"):
        # The separately admitted alternative is a true one-shot migration. Main's broader
        # migration-boundary test owns post-migration mirror-tamper semantics; here we only
        # ensure success did not silently reset continuity.
        assert _canonical_generation_if_materialized(entity_db) == 7
        return

    assert "LEGACY_GENERATION_MIGRATION_REQUIRED" in str(first.get("error", ""))
    assert _canonical_generation_if_materialized(entity_db) is None, (
        "fail-closed migration left a live canonical entity_state row behind"
    )
    assert _legacy_generation(entity_db) == 7

    second = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    assert second.get("ok") is False, (
        "retry became admissible after a fail-closed migration attempt; partial state leaked"
    )
    assert "LEGACY_GENERATION_MIGRATION_REQUIRED" in str(second.get("error", ""))
    assert _canonical_generation_if_materialized(entity_db) is None
    assert _legacy_generation(entity_db) == 7
