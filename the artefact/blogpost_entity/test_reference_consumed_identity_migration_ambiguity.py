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


def _namespaced_reference_active() -> bool:
    if not RUNTIME_PATH.is_file():
        return False
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    return "def _pipeline_profile_read" in source and "source_namespace" in source


def _load_runtime_module():
    sys.path.insert(0, str(TOOLS))
    try:
        return importlib.import_module("clay_profile_pipeline_runtime")
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)


def _legacy_consumed_db(path: Path) -> None:
    db = sqlite3.connect(path)
    try:
        db.execute(
            """CREATE TABLE eos_pipeline_consumed(
                 source_kind TEXT NOT NULL,
                 source_id TEXT NOT NULL,
                 output_id TEXT NOT NULL,
                 consumed_at REAL NOT NULL,
                 PRIMARY KEY(source_kind,source_id))"""
        )
        db.execute(
            "INSERT INTO eos_pipeline_consumed VALUES(?,?,?,?)",
            ("event", "1", "legacy-output", 123.0),
        )
        db.commit()
    finally:
        db.close()


def _legacy_shape(path: Path) -> tuple[list[str], list[tuple]]:
    db = sqlite3.connect(path)
    try:
        columns = [
            str(row[1])
            for row in db.execute("PRAGMA table_info(eos_pipeline_consumed)").fetchall()
        ]
        rows = db.execute(
            """SELECT source_kind,source_id,output_id,consumed_at
               FROM eos_pipeline_consumed ORDER BY source_kind,source_id"""
        ).fetchall()
        return columns, rows
    finally:
        db.close()


@pytest.mark.skipif(
    not _namespaced_reference_active(),
    reason="activates only when reference convergence owns namespaced consumed identity",
)
def test_nonempty_legacy_consumed_identity_never_gets_a_guessed_namespace(tmp_path: Path) -> None:
    """Ambiguous old `(kind,id)` history must not be silently promoted to a namespace.

    Once Exactly-Once identity becomes `(source_namespace, kind, id)`, a nonempty legacy
    table has lost the information needed to prove which logical source produced each row.
    Fabricating a namespace such as `kind:<kind>` can either re-consume an old event after
    a profile/source migration or suppress a distinct source that reuses the local id.

    With no provenance-bound mapping supplied, initialization therefore has to fail closed
    and leave the legacy evidence byte-semantically intact. A separately admitted one-shot
    migration may later succeed only when it has enough provenance to prove the mapping.
    """
    runtime_module = _load_runtime_module()
    entity_db = tmp_path / "entity.db"
    _legacy_consumed_db(entity_db)
    before_columns, before_rows = _legacy_shape(entity_db)

    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)
    first = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})

    assert first.get("ok") is False, (
        "pipeline_init silently assigned a namespace to intrinsically ambiguous legacy "
        "consumption history"
    )
    error = str(first.get("error", "")).upper()
    assert "CONSUMED" in error and "MIGRATION" in error, (
        "ambiguous consumed identity needs a distinct migration-required fail-closed state"
    )

    after_columns, after_rows = _legacy_shape(entity_db)
    assert after_columns == before_columns
    assert after_rows == before_rows

    # Failure must be atomic and stable: retry cannot manufacture canonical/native state
    # that changes the migration decision or mutates the ambiguous evidence.
    second = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    assert second.get("ok") is False
    second_error = str(second.get("error", "")).upper()
    assert "CONSUMED" in second_error and "MIGRATION" in second_error
    retry_columns, retry_rows = _legacy_shape(entity_db)
    assert retry_columns == before_columns
    assert retry_rows == before_rows
