from __future__ import annotations

import ast
import importlib
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
RUNTIME_PATH = TOOLS / "clay_profile_pipeline_runtime.py"


def _has_db_profile_reference(source: str) -> bool:
    tree = ast.parse(source)
    return any(
        isinstance(node, ast.FunctionDef) and node.name == "_pipeline_profile_read"
        for node in ast.walk(tree)
    )


def _legacy_db(path: Path, generation: int) -> None:
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


def _canonical_generation(path: Path) -> int:
    db = sqlite3.connect(path)
    try:
        row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
        assert row is not None, "successful migration/init must materialize canonical entity_state"
        return int(row[0])
    finally:
        db.close()


def _legacy_generation_column(path: Path) -> bool:
    db = sqlite3.connect(path)
    try:
        columns = {str(row[1]) for row in db.execute("PRAGMA table_info(eos_pipeline_state)")}
        return "generation" in columns
    finally:
        db.close()


def test_future_reference_legacy_generation_migration_is_one_shot_or_fail_closed(tmp_path) -> None:
    """Legacy generation may be preserved once, but never become recurrent authority.

    A future DB-profile reference has two safe choices when it opens a legacy DB that has
    only eos_pipeline_state.generation and no canonical entity_state yet:

    1. fail closed with an explicit migration-required error; or
    2. preserve that legacy generation exactly once while establishing entity_state as the
       sole live authority.

    What is forbidden is silently resetting continuity to zero or continuing to let later
    mirror tampering advance canonical generation.
    """

    source = RUNTIME_PATH.read_text(encoding="utf-8")
    if not _has_db_profile_reference(source):
        return

    sys.path.insert(0, str(TOOLS))
    try:
        runtime_module = importlib.import_module("clay_profile_pipeline_runtime")
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)

    entity_db = tmp_path / "legacy_entity.db"
    _legacy_db(entity_db, generation=7)
    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)

    first = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    if not first.get("ok"):
        error = str(first.get("error", ""))
        assert "LEGACY_GENERATION_MIGRATION_REQUIRED" in error, (
            "legacy-only generation may fail closed, but the failure must explicitly preserve "
            "the migration obligation rather than silently resetting or discarding continuity"
        )
        return

    assert _canonical_generation(entity_db) == 7, (
        "a successful automatic legacy migration must preserve the pre-existing generation "
        "exactly; silently resetting canonical generation is not an admissible convergence"
    )

    if _legacy_generation_column(entity_db):
        db = sqlite3.connect(entity_db)
        try:
            db.execute(
                "UPDATE eos_pipeline_state SET generation=999 WHERE singleton=1"
            )
            db.commit()
        finally:
            db.close()

        second = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
        assert second.get("ok") is True, (
            "once canonical authority exists, a stale compatibility column must not force "
            "re-migration or make normal init unavailable"
        )
        assert _canonical_generation(entity_db) == 7, (
            "post-migration legacy mirror tampering must never advance canonical generation"
        )
