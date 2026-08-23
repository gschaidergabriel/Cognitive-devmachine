from __future__ import annotations

import importlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
RUNTIME_PATH = TOOLS / "clay_profile_pipeline_runtime.py"


def _reference_is_active() -> bool:
    return RUNTIME_PATH.is_file() and "def _pipeline_collect" in RUNTIME_PATH.read_text(encoding="utf-8")


def _runtime_module():
    sys.path.insert(0, str(TOOLS))
    try:
        return importlib.import_module("clay_profile_pipeline_runtime")
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)


def _source_db(path: Path) -> None:
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE source_a(id INTEGER PRIMARY KEY,payload TEXT NOT NULL)")
        db.execute("CREATE TABLE source_b(id INTEGER PRIMARY KEY,payload TEXT NOT NULL)")
        db.execute("INSERT INTO source_a(id,payload) VALUES(1,'packet-sentinel-logical-A')")
        db.execute("INSERT INTO source_b(id,payload) VALUES(2,'packet-sentinel-logical-B')")
        db.commit()
    finally:
        db.close()


def _profile() -> dict:
    return {
        "profile_id": "same-kind-two-logical-sources",
        "sources": [
            {
                "kind": "event",
                "source_namespace": "logical-A",
                "adapter": "sqlite_query",
                "required_for_quiet": True,
                "db": "source",
                "query": "SELECT id AS source_id,payload FROM source_a ORDER BY id",
                "id_field": "source_id",
                "evidence_prefix": "event-a:",
            },
            {
                "kind": "event",
                "source_namespace": "logical-B",
                "adapter": "sqlite_query",
                "required_for_quiet": True,
                "db": "source",
                "query": "SELECT id AS source_id,payload FROM source_b ORDER BY id",
                "id_field": "source_id",
                "evidence_prefix": "event-b:",
            },
        ],
        "canonical_probes": [],
        "state_metrics": [],
    }


@pytest.mark.skipif(not _reference_is_active(), reason="activates with DB-profile reference convergence")
def test_same_kind_distinct_logical_sources_cannot_be_consumed_without_packetization(tmp_path: Path) -> None:
    """Exactly-once consumption must not outrun packet/source representation.

    The retained reference design explicitly permits distinct logical sources to share one
    source kind. Both admitted source identities may therefore enter the consume set, but
    neither source may disappear from the packet merely because the implementation uses
    `kind` as a dictionary key. A later successful commit iterates the full consume set, so
    silent packet overwrite would irreversibly mark unseen evidence as consumed.

    This test intentionally does not prescribe the internal packet shape. It requires only
    that every admitted same-kind source payload remains represented before commit.
    """
    runtime_module = _runtime_module()
    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    source_db = tmp_path / "source.db"
    _source_db(source_db)
    assert runtime.effect("pipeline_init", {"entity_db": str(entity_db)}).get("ok") is True

    profile = _profile()
    collected = runtime._pipeline_collect(
        {
            "entity_db": str(entity_db),
            "source_db": str(source_db),
            "profile": profile,
            "previous": {"cursors": {}},
        }
    )
    assert collected.get("ok") is True
    assert collected["source_count"] == 2
    assert {
        (item["namespace"], item["kind"], item["id"])
        for item in collected["consume"]
    } == {
        ("logical-A", "event", "1"),
        ("logical-B", "event", "2"),
    }

    compiled = runtime._pipeline_compile({"profile": profile, "data": collected})
    assert compiled.get("ok") is True
    packet_blob = json.dumps(compiled["packet"], sort_keys=True)

    assert "packet-sentinel-logical-A" in packet_blob, (
        "logical-A entered the durable consume set but disappeared from the compiled packet"
    )
    assert "packet-sentinel-logical-B" in packet_blob
