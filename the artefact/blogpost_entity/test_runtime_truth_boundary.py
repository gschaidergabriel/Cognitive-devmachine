from __future__ import annotations

import copy
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import PROFILE_SCHEMA, PipelineFault, ProfilePipelineRuntime


def base_profile() -> dict:
    return {
        "schema": PROFILE_SCHEMA,
        "profile_id": "truth_boundary",
        "identity": {"entity_name": "Truth Boundary Fixture"},
        "inference": {"kind": "mock", "model": "fixture", "secret_names": []},
        "personality": {
            "system_prompt": "fixture",
            "public_style": "fixture",
            "output_contract": {
                "title_field": "title",
                "intro_field": "intro",
                "sections_field": "sections",
                "section_text_field": "text",
                "section_evidence_field": "evidence",
                "section_claims_field": "claims",
                "continuity_field": "thread",
                "autobiographical_hypotheses_field": "hypotheses",
            },
        },
        "sources": [],
        "canonical_probes": [],
        "state_metrics": [
            {
                "name": "satisfaction",
                "status": "VERIFIED",
                "value": 0.2,
                "evidence_ref": "state:satisfaction",
            }
        ],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": False,
            "max_claim_overshoot": 0.0,
            "leak_patterns": [],
        },
    }


def collected_fixture() -> dict:
    return {
        "sources": {},
        "sensors": {},
        "probes": {},
        "consume": [],
        "next_cursors": {},
        "source_count": 0,
        "quiet_sensors_ok": False,
    }


def test_canonical_hash_binds_pipeline_owned_state_metrics(tmp_path):
    """Changing a canonical metric must change the hash the model is required to echo."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    low = base_profile()
    high = copy.deepcopy(low)
    high["state_metrics"][0]["value"] = 0.8

    low_compiled = runtime.effect("pipeline_compile", {"profile": low, "data": collected_fixture()})
    high_compiled = runtime.effect("pipeline_compile", {"profile": high, "data": collected_fixture()})

    assert low_compiled["ok"] is True and high_compiled["ok"] is True
    assert low_compiled["personality_state"]["satisfaction"]["value"] == 0.2
    assert high_compiled["personality_state"]["satisfaction"]["value"] == 0.8
    assert low_compiled["canonical_state_hash"] != high_compiled["canonical_state_hash"]
    assert low_compiled["canonical"]["state_metrics"] == low_compiled["personality_state"]


def test_sqlite_evidence_query_cannot_mutate_source_database(tmp_path):
    """Source/probe adapters are observation surfaces, never an effect path."""
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    db = sqlite3.connect(source_db)
    db.execute("CREATE TABLE events(id INTEGER PRIMARY KEY, note TEXT)")
    db.execute("INSERT INTO events VALUES(1,'must survive')")
    db.commit()
    db.close()

    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = base_profile()
    profile["sources"] = [
        {
            "kind": "event",
            "adapter": "sqlite_query",
            "required_for_quiet": True,
            "db": "source",
            "query": "DELETE FROM events RETURNING id AS source_id,note",
            "id_field": "source_id",
            "evidence_prefix": "event:",
        }
    ]
    runtime.install_profile(str(entity_db), profile)
    runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"] is True

    collected = runtime.effect(
        "pipeline_collect",
        {
            "entity_db": str(entity_db),
            "source_db": str(source_db),
            "profile": loaded["profile"],
            "previous": {"generation": 0, "continuity": {}, "cursors": {}},
        },
    )

    assert collected["ok"] is True
    assert collected["sources"]["event"]["ok"] is False
    db = sqlite3.connect(source_db)
    assert db.execute("SELECT id,note FROM events").fetchall() == [(1, "must survive")]
    db.close()


def test_secret_bearing_profile_is_rejected_before_db_persistence(tmp_path):
    """MiniUnifiedDB may store secret references/names, never credential values in profile JSON."""
    entity_db = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = base_profile()
    profile["inference"]["api_token"] = "super-secret-token-value"

    with pytest.raises(PipelineFault):
        runtime.install_profile(str(entity_db), profile)

    if entity_db.exists():
        db = sqlite3.connect(entity_db)
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "eos_pipeline_profiles" in tables:
            assert db.execute("SELECT COUNT(*) FROM eos_pipeline_profiles").fetchone()[0] == 0
        db.close()
