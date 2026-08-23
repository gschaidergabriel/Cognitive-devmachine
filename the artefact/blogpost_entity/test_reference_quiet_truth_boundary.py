from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def _collect(runtime: ProfilePipelineRuntime, entity_db: Path, source_db: Path, profile: dict) -> dict:
    return runtime.effect(
        "pipeline_collect",
        {
            "entity_db": str(entity_db),
            "source_db": str(source_db),
            "profile": profile,
            "previous": {"cursors": {}},
        },
    )


def _compile(runtime: ProfilePipelineRuntime, profile: dict, collected: dict) -> dict:
    return runtime.effect("pipeline_compile", {"profile": profile, "data": collected})


def _base_profile(source: dict) -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "quiet-boundary",
        "inference": {"kind": "mock", "secret_names": []},
        "personality": {
            "system_prompt": "",
            "public_style": "",
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
        "sources": [source],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {"require_hash_echo": True, "require_evidence_per_section": True},
    }


def test_present_json_snapshot_cannot_coexist_with_quiet_verified(tmp_path: Path) -> None:
    """A successfully read non-null snapshot is evidence, not a verified quiet window."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    assert runtime.effect("pipeline_init", {"entity_db": str(entity_db)})["ok"] is True
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text('{"status":"changed","n":1}', encoding="utf-8")

    profile = _base_profile(
        {
            "kind": "snapshot",
            "adapter": "json_snapshot",
            "path": "snapshot.json",
            "required_for_quiet": True,
            "evidence_prefix": "snapshot:",
        }
    )
    collected = _collect(runtime, entity_db, entity_db, profile)
    assert collected["ok"] is True
    assert collected["sources"]["snapshot"]["ok"] is True
    assert collected["sources"]["snapshot"]["value"] is not None

    compiled = _compile(runtime, profile, collected)
    assert compiled["ok"] is True
    assert "snapshot:" in compiled["allowed_evidence_refs"]
    assert "quiet:verified" not in compiled["allowed_evidence_refs"], (
        "present snapshot evidence was simultaneously represented as a verified quiet window"
    )


def test_untrackable_sqlite_row_cannot_be_silently_reclassified_as_quiet(tmp_path: Path) -> None:
    """Rows missing their configured durable identity are malformed evidence, not silence."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    source_db = tmp_path / "source.db"
    assert runtime.effect("pipeline_init", {"entity_db": str(entity_db)})["ok"] is True
    with sqlite3.connect(source_db) as db:
        db.execute("CREATE TABLE events(payload TEXT NOT NULL)")
        db.execute("INSERT INTO events(payload) VALUES('real-event-without-id')")

    profile = _base_profile(
        {
            "kind": "events",
            "adapter": "sqlite_query",
            "db": "source",
            "query": "SELECT payload FROM events",
            "id_field": "source_id",
            "required_for_quiet": True,
            "evidence_prefix": "event:",
        }
    )
    collected = _collect(runtime, entity_db, source_db, profile)
    assert collected["ok"] is True

    compiled = _compile(runtime, profile, collected)
    assert compiled["ok"] is True
    assert "quiet:verified" not in compiled["allowed_evidence_refs"], (
        "a real row with no durable source identity was silently discarded and promoted to quiet"
    )
