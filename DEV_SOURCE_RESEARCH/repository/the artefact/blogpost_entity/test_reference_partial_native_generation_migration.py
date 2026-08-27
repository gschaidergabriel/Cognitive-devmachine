from __future__ import annotations

import importlib
import sqlite3
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
RUNTIME_PATH = TOOLS / "clay_profile_pipeline_runtime.py"


def _db_profile_reference_active() -> bool:
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    return "def _pipeline_profile_read" in source


def _make_partial_native_legacy_db(path: Path, legacy_generation: int) -> None:
    db = sqlite3.connect(path)
    try:
        db.executescript(
            """
            CREATE TABLE entity_state(
              id INTEGER PRIMARY KEY CHECK(id=1),
              generation INTEGER NOT NULL,
              active_profile TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL);
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
            (legacy_generation,),
        )
        db.commit()
    finally:
        db.close()


def _canonical_generation(path: Path) -> int | None:
    db = sqlite3.connect(path)
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
        return None if row is None else int(row[0])
    finally:
        db.close()


def _legacy_generation_if_present(path: Path) -> int | None:
    db = sqlite3.connect(path)
    try:
        columns = {str(row[1]) for row in db.execute("PRAGMA table_info(eos_pipeline_state)")}
        if "generation" not in columns:
            return None
        row = db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()
        return None if row is None else int(row[0])
    finally:
        db.close()


@pytest.mark.skipif(
    not _db_profile_reference_active(),
    reason="activates only when DB-profile reference convergence is present",
)
def test_empty_native_table_does_not_silently_reset_legacy_generation(tmp_path: Path) -> None:
    """A table shell is not canonical authority; the singleton row is.

    Crash/partial-migration state can leave an empty native entity_state table beside a
    legacy eos_pipeline_state generation. Init must treat that as unresolved migration,
    not as established native authority. It may either fail closed without losing the
    legacy evidence or perform the already-admitted exact one-shot preservation. It may
    never insert generation zero and discard the only surviving nonzero generation.
    """

    sys.path.insert(0, str(TOOLS))
    try:
        runtime_module = importlib.import_module("clay_profile_pipeline_runtime")
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)

    entity_db = tmp_path / "partial_native.db"
    _make_partial_native_legacy_db(entity_db, legacy_generation=7)
    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)

    first = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    if not first.get("ok"):
        assert "LEGACY_GENERATION_MIGRATION_REQUIRED" in str(first.get("error", ""))
        assert _canonical_generation(entity_db) is None
        assert _legacy_generation_if_present(entity_db) == 7
        return

    assert _canonical_generation(entity_db) == 7, (
        "successful partial-native migration silently reset legacy generation instead of "
        "preserving it exactly once"
    )

    legacy_after = _legacy_generation_if_present(entity_db)
    if legacy_after is not None:
        db = sqlite3.connect(entity_db)
        try:
            db.execute("UPDATE eos_pipeline_state SET generation=999 WHERE singleton=1")
            db.commit()
        finally:
            db.close()
        second = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
        assert second.get("ok") is True
        assert _canonical_generation(entity_db) == 7, (
            "post-migration compatibility generation regained authority over canonical state"
        )
