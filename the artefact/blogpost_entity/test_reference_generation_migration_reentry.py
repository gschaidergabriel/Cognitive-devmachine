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


def _native_generation(path: Path) -> int:
    db = sqlite3.connect(path)
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
        assert row is not None
        return int(row[0])
    finally:
        db.close()


@pytest.mark.skipif(
    not _runtime_has_db_profile_convergence(),
    reason="activates only when current DB-profile reference convergence exists",
)
def test_one_time_legacy_generation_migration_cannot_reassert_on_second_init(
    tmp_path: Path,
) -> None:
    """A legacy donation may happen once; a later init may never promote the mirror again.

    This is deliberately a restart/re-entry discriminator. A weaker test that mutates the
    legacy mirror and then calls only `pipeline_state_read` can miss an implementation that
    accidentally repeats legacy migration every time `pipeline_init` runs.
    """
    entity_db = tmp_path / "entity.db"
    _legacy_reference_db(entity_db, generation=7)

    runtime = ProfilePipelineRuntime(root=tmp_path)
    first = runtime._pipeline_init({"entity_db": str(entity_db)})
    assert first["ok"] is True
    assert _native_generation(entity_db) == 7, (
        "legacy-only continuity was not imported into canonical entity_state exactly once"
    )

    # Counter-reality: after canonical authority exists, stale compatibility storage claims
    # a much newer generation. If the implementation keeps the legacy column only as inert
    # historical storage, poison it. If the repair removed that column entirely, there is
    # no mirror left capable of reasserting generation authority.
    db = sqlite3.connect(entity_db)
    columns = {
        str(row[1])
        for row in db.execute("PRAGMA table_info(eos_pipeline_state)").fetchall()
    }
    if "generation" in columns:
        db.execute(
            "UPDATE eos_pipeline_state SET generation=99 WHERE singleton=1"
        )
        db.commit()
    db.close()

    second = runtime._pipeline_init({"entity_db": str(entity_db)})

    # Whether the implementation tolerates the divergent inert mirror or explicitly fails
    # closed, it must never let the second init advance canonical generation from 7 to 99.
    assert _native_generation(entity_db) == 7, (
        "legacy generation reasserted authority during a later pipeline_init"
    )

    if second.get("ok") is True:
        state = runtime._pipeline_state_read({"entity_db": str(entity_db)})
        assert state["ok"] is True
        assert int(state["generation"]) == 7
    else:
        error_text = str(second.get("error", "")).upper()
        assert "GENERATION" in error_text or "MIGRATION" in error_text, (
            "re-init failed for an unrelated/opaque reason instead of an explicit "
            "generation-authority divergence"
        )
