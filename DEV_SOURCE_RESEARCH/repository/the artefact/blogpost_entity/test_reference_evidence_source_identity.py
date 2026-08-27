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


def _reference_is_active() -> bool:
    return RUNTIME_PATH.is_file() and "def _pipeline_profile_read" in RUNTIME_PATH.read_text(encoding="utf-8")


def _runtime_module():
    sys.path.insert(0, str(TOOLS))
    try:
        return importlib.import_module("clay_profile_pipeline_runtime")
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)


def _source_db(path: Path, payload: str) -> None:
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE events(id INTEGER PRIMARY KEY,payload TEXT NOT NULL)")
        db.execute("INSERT INTO events(id,payload) VALUES(1,?)", (payload,))
        db.commit()
    finally:
        db.close()


def _profile(profile_id: str, namespace: str) -> dict:
    return {
        "profile_id": profile_id,
        "sources": [
            {
                "kind": "event",
                "source_namespace": namespace,
                "adapter": "sqlite_query",
                "required_for_quiet": True,
                "db": "source",
                "query": "SELECT id AS source_id,payload FROM events ORDER BY id",
                "id_field": "source_id",
                "evidence_prefix": "event:",
            }
        ],
        "canonical_probes": [],
        "state_metrics": [],
    }


def _allowed_refs(runtime, entity_db: Path, source_db: Path, profile: dict) -> tuple[str, ...]:
    collected = runtime._pipeline_collect(
        {
            "entity_db": str(entity_db),
            "source_db": str(source_db),
            "profile": profile,
            "previous": {"cursors": {}},
        }
    )
    assert collected.get("ok") is True
    compiled = runtime._pipeline_compile({"profile": profile, "data": collected})
    assert compiled.get("ok") is True
    refs = tuple(compiled["allowed_evidence_refs"])
    assert refs
    return refs


@pytest.mark.skipif(not _reference_is_active(), reason="activates with DB-profile reference convergence")
def test_distinct_logical_sources_cannot_alias_the_same_evidence_ref(tmp_path: Path) -> None:
    """Evidence provenance identity must be at least as strong as consumption identity.

    Two logical sources may reuse the same local kind, id and presentation prefix. If their
    allowed evidence refs collapse to the same string, a persisted claim ref can no longer
    identify which admitted source supported it. The concrete ref encoding is deliberately
    unconstrained; only non-aliasing is required.
    """
    runtime_module = _runtime_module()
    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    source_a = tmp_path / "source_a.db"
    source_b = tmp_path / "source_b.db"
    _source_db(source_a, "A")
    _source_db(source_b, "B")
    assert runtime.effect("pipeline_init", {"entity_db": str(entity_db)}).get("ok") is True

    refs_a = _allowed_refs(runtime, entity_db, source_a, _profile("profile-a", "logical-A"))
    refs_b = _allowed_refs(runtime, entity_db, source_b, _profile("profile-b", "logical-B"))

    assert refs_a != refs_b, (
        "distinct logical sources with the same kind/local id collapsed to the same evidence identity"
    )


@pytest.mark.skipif(not _reference_is_active(), reason="activates with DB-profile reference convergence")
def test_same_logical_source_keeps_evidence_identity_across_profile_swaps(tmp_path: Path) -> None:
    """Counterbalance: evidence identity follows the source, not the application profile."""
    runtime_module = _runtime_module()
    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    source = tmp_path / "source.db"
    _source_db(source, "shared")
    assert runtime.effect("pipeline_init", {"entity_db": str(entity_db)}).get("ok") is True

    refs_a = _allowed_refs(runtime, entity_db, source, _profile("profile-a", "logical-shared"))
    refs_b = _allowed_refs(runtime, entity_db, source, _profile("profile-b", "logical-shared"))

    assert refs_a == refs_b, "changing only the application profile changed durable evidence identity"
