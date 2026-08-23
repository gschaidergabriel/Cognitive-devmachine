from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import PipelineFault, ProfilePipelineRuntime


def _seed_generations(db_path: Path, canonical: int, mirror: int) -> None:
    db = sqlite3.connect(db_path)
    try:
        db.execute("UPDATE entity_state SET generation=? WHERE id=1", (canonical,))
        db.execute("UPDATE eos_pipeline_state SET generation=? WHERE singleton=1", (mirror,))
        db.commit()
    finally:
        db.close()


def _read_generations(db_path: Path) -> tuple[int, int]:
    db = sqlite3.connect(db_path)
    try:
        canonical = int(db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0])
        mirror = int(db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()[0])
        return canonical, mirror
    finally:
        db.close()


def test_legacy_mirror_cannot_advance_existing_canonical_generation(tmp_path: Path) -> None:
    """The legacy continuity mirror is not allowed to become a second generation authority.

    An implementation may fail closed on divergence or reconcile canonical -> mirror, but
    it must never copy a higher mirror generation into an already-existing entity_state row.
    """
    db_path = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)
    assert runtime.effect("pipeline_init", {"entity_db": str(db_path)})["ok"] is True

    _seed_generations(db_path, canonical=4, mirror=999)

    db = sqlite3.connect(db_path)
    try:
        try:
            runtime._ensure_schema(db)
            db.commit()
        except PipelineFault:
            db.rollback()
    finally:
        db.close()

    canonical_after, _mirror_after = _read_generations(db_path)
    assert canonical_after == 4, "legacy mirror advanced canonical generation authority"


def test_generation_divergence_is_not_silently_collapsed_mirror_to_canonical(tmp_path: Path) -> None:
    db_path = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)
    assert runtime.effect("pipeline_init", {"entity_db": str(db_path)})["ok"] is True

    _seed_generations(db_path, canonical=17, mirror=23)

    db = sqlite3.connect(db_path)
    try:
        before = tuple(int(v) for v in db.execute(
            "SELECT (SELECT generation FROM entity_state WHERE id=1),"
            "       (SELECT generation FROM eos_pipeline_state WHERE singleton=1)"
        ).fetchone())
        assert before == (17, 23)
        with pytest.raises(PipelineFault, match="GENERATION_MIRROR_DIVERGENCE"):
            runtime._ensure_schema(db)
    finally:
        db.close()
