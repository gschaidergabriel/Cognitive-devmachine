from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def _contract() -> dict:
    return {
        "title_field": "title",
        "intro_field": "intro",
        "sections_field": "sections",
        "section_text_field": "text",
        "section_evidence_field": "evidence",
        "section_claims_field": "claims",
        "continuity_field": "thread",
        "autobiographical_hypotheses_field": "hypotheses",
    }


def _profile(metric: float = 0.4) -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "authority-test",
        "inference": {"kind": "mock", "secret_names": []},
        "personality": {"output_contract": _contract(), "system_prompt": "", "public_style": ""},
        "sources": [],
        "canonical_probes": [],
        "state_metrics": [
            {"name": "confidence", "status": "VERIFIED", "value": metric, "evidence_ref": "state:confidence"}
        ],
        "gate": {"require_hash_echo": True, "require_evidence_per_section": True},
    }


def _empty_collected() -> dict:
    return {
        "sources": {},
        "sensors": {},
        "probes": {},
        "consume": [],
        "next_cursors": {},
        "source_count": 0,
        "quiet_sensors_ok": False,
    }


def _commit_payload(entity_db: str, profile: dict) -> dict:
    return {
        "entity_db": entity_db,
        "profile": profile,
        "previous": {"generation": 0},
        "data": {
            "collected": _empty_collected(),
            "compiled": {
                "packet_hash": "p",
                "canonical_state_hash": "c",
                "source_count": 0,
                "canonical": {"personality_state": {}},
            },
            "generated": {"provider_kind": "mock", "model": "m"},
            "gated": {"payload": {"thread": "t", "hypotheses": "h"}},
        },
    }


def test_legacy_generation_projection_cannot_advance_existing_native_generation(tmp_path: Path) -> None:
    entity_db = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)
    assert runtime.effect("pipeline_init", {"entity_db": str(entity_db)})["ok"] is True

    with sqlite3.connect(entity_db) as db:
        db.execute("UPDATE entity_state SET generation=4 WHERE id=1")
        db.execute("ALTER TABLE eos_pipeline_state ADD COLUMN generation INTEGER NOT NULL DEFAULT 0")
        db.execute("UPDATE eos_pipeline_state SET generation=999 WHERE singleton=1")

    result = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    assert result["ok"] is True
    with sqlite3.connect(entity_db) as db:
        assert db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0] == 4
        assert "generation" not in {row[1] for row in db.execute("PRAGMA table_info(eos_pipeline_state)")}


def test_legacy_only_nonzero_generation_requires_explicit_migration(tmp_path: Path) -> None:
    entity_db = tmp_path / "legacy.db"
    with sqlite3.connect(entity_db) as db:
        db.execute(
            """CREATE TABLE eos_pipeline_state(
                 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                 generation INTEGER NOT NULL DEFAULT 0,
                 continuity_json TEXT NOT NULL DEFAULT '{}',
                 canonical_json TEXT NOT NULL DEFAULT '{}',
                 canonical_hash TEXT NOT NULL DEFAULT '',
                 cursors_json TEXT NOT NULL DEFAULT '{}',
                 updated_at REAL NOT NULL DEFAULT 0)"""
        )
        db.execute("INSERT INTO eos_pipeline_state(singleton,generation) VALUES(1,7)")

    runtime = ProfilePipelineRuntime(root=tmp_path)
    result = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    assert result["ok"] is False
    assert "LEGACY_GENERATION_MIGRATION_REQUIRED" in result["error"]
    with sqlite3.connect(entity_db) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "entity_state" not in tables
        assert db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()[0] == 7


def test_partial_native_table_without_singleton_row_cannot_discard_legacy_generation(tmp_path: Path) -> None:
    """Table presence alone is not evidence that canonical generation authority exists."""
    entity_db = tmp_path / "partial-native.db"
    with sqlite3.connect(entity_db) as db:
        db.execute(
            """CREATE TABLE entity_state(
                 id INTEGER PRIMARY KEY CHECK(id=1),
                 generation INTEGER NOT NULL,
                 active_profile TEXT,
                 created_at TEXT NOT NULL,
                 updated_at TEXT NOT NULL)"""
        )
        db.execute(
            """CREATE TABLE eos_pipeline_state(
                 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                 generation INTEGER NOT NULL DEFAULT 0,
                 continuity_json TEXT NOT NULL DEFAULT '{}',
                 canonical_json TEXT NOT NULL DEFAULT '{}',
                 canonical_hash TEXT NOT NULL DEFAULT '',
                 cursors_json TEXT NOT NULL DEFAULT '{}',
                 updated_at REAL NOT NULL DEFAULT 0)"""
        )
        db.execute("INSERT INTO eos_pipeline_state(singleton,generation) VALUES(1,7)")

    runtime = ProfilePipelineRuntime(root=tmp_path)
    result = runtime.effect("pipeline_init", {"entity_db": str(entity_db)})
    assert result["ok"] is False
    assert "LEGACY_GENERATION_MIGRATION_REQUIRED" in result["error"]
    with sqlite3.connect(entity_db) as db:
        assert db.execute("SELECT 1 FROM entity_state WHERE id=1").fetchone() is None
        assert "generation" in {row[1] for row in db.execute("PRAGMA table_info(eos_pipeline_state)")}
        assert db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()[0] == 7


def test_profile_json_only_tamper_aborts_commit_with_zero_durable_delta(tmp_path: Path) -> None:
    entity_db = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)
    runtime.import_profile(str(entity_db), _profile())
    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"] is True

    with sqlite3.connect(entity_db) as db:
        original = db.execute(
            "SELECT profile_json FROM profiles WHERE profile_id='authority-test'"
        ).fetchone()[0]
        changed = json.loads(original)
        changed["personality"]["system_prompt"] = "tampered bytes"
        db.execute(
            "UPDATE profiles SET profile_json=? WHERE profile_id='authority-test'",
            (json.dumps(changed, sort_keys=True, separators=(",", ":")),),
        )

    result = runtime.effect(
        "pipeline_commit",
        _commit_payload(str(entity_db), loaded["profile"]),
    )
    assert result["ok"] is False
    assert "PROFILE_SNAPSHOT_STALE" in result["error"]
    with sqlite3.connect(entity_db) as db:
        assert db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM eos_pipeline_packets").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 0


def test_claim_authorizing_metrics_are_inside_canonical_hash_boundary(tmp_path: Path) -> None:
    runtime = ProfilePipelineRuntime(root=tmp_path)
    low = runtime.effect("pipeline_compile", {"profile": _profile(0.2), "data": _empty_collected()})
    high = runtime.effect("pipeline_compile", {"profile": _profile(0.8), "data": _empty_collected()})
    assert low["ok"] is True and high["ok"] is True
    assert low["canonical"]["personality_state"] == low["personality_state"]
    assert high["canonical"]["personality_state"] == high["personality_state"]
    assert low["canonical_state_hash"] != high["canonical_state_hash"]
