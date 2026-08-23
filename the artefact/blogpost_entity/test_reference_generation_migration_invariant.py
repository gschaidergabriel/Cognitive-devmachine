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


def _runtime_has_db_profile_convergence() -> bool:
    return hasattr(ProfilePipelineRuntime, "_pipeline_profile_read")


def _legacy_reference_db(path: Path, generation: int) -> None:
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


@pytest.mark.skipif(
    not _runtime_has_db_profile_convergence(),
    reason="activates only when current DB-profile reference convergence exists",
)
def test_legacy_generation_is_imported_once_then_deauthorized(tmp_path: Path) -> None:
    """Legacy reference generation may seed native authority once, never reassert later."""
    entity_db = tmp_path / "entity.db"
    _legacy_reference_db(entity_db, generation=7)

    runtime = ProfilePipelineRuntime(root=tmp_path)
    init = runtime._pipeline_init({"entity_db": str(entity_db)})
    assert init["ok"] is True

    db = sqlite3.connect(entity_db)
    native = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    assert native is not None
    assert int(native[0]) == 7, "legacy-only DB must preserve continuity exactly once"

    # Counter-reality: stale legacy storage later claims a much newer generation.
    # It is now only historical/reference storage and must not retake live authority.
    db.execute("UPDATE eos_pipeline_state SET generation=99 WHERE singleton=1")
    db.commit()
    db.close()

    state = runtime._pipeline_state_read({"entity_db": str(entity_db)})
    assert state["ok"] is True
    assert int(state["generation"]) == 7, (
        "legacy eos_pipeline_state generation reasserted authority after migration"
    )

    db = sqlite3.connect(entity_db)
    final_native = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    assert final_native is not None
    assert int(final_native[0]) == 7
    db.close()


@pytest.mark.skipif(
    not _runtime_has_db_profile_convergence(),
    reason="activates only when current DB-profile reference convergence exists",
)
def test_existing_native_generation_outranks_legacy_generation(tmp_path: Path) -> None:
    """When native authority already exists, legacy generation can never overwrite it."""
    entity_db = tmp_path / "entity.db"
    _legacy_reference_db(entity_db, generation=99)

    db = sqlite3.connect(entity_db)
    db.execute(
        """CREATE TABLE entity_state(
             id INTEGER PRIMARY KEY CHECK(id=1),
             generation INTEGER NOT NULL,
             active_profile TEXT,
             created_at TEXT NOT NULL,
             updated_at TEXT NOT NULL)"""
    )
    db.execute(
        "INSERT INTO entity_state VALUES(1,5,NULL,'2026-08-23T00:00:00Z','2026-08-23T00:00:00Z')"
    )
    db.commit()
    db.close()

    runtime = ProfilePipelineRuntime(root=tmp_path)
    init = runtime._pipeline_init({"entity_db": str(entity_db)})
    assert init["ok"] is True

    state = runtime._pipeline_state_read({"entity_db": str(entity_db)})
    assert state["ok"] is True
    assert int(state["generation"]) == 5, (
        "pre-existing native generation was overwritten by stale legacy reference state"
    )
