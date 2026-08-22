from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import PipelineFault, ProfilePipelineRuntime


def _minimal_v2_profile() -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "truth_boundary",
        "inference": {
            "kind": "mock",
            "model": "fixture",
            "secret_names": [],
        },
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
        "state_metrics": [],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": False,
            "max_claim_overshoot": 0.0,
            "leak_patterns": [],
        },
    }


def test_profile_import_rejects_embedded_credential_values_before_persistence(tmp_path: Path) -> None:
    """MiniUnifiedDB may persist secret names/references, never credential values."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    assert hasattr(runtime, "import_profile"), "DB-profile convergence must expose an explicit import path"

    entity_db = tmp_path / "entity.db"
    profile = _minimal_v2_profile()
    profile["inference"]["api_token"] = "credential-value-must-never-be-stored"

    with pytest.raises(PipelineFault):
        runtime.import_profile(str(entity_db), profile)

    if entity_db.exists():
        db = sqlite3.connect(entity_db)
        try:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "profiles" in tables:
                rows = db.execute("SELECT profile_json FROM profiles").fetchall()
                assert all("credential-value-must-never-be-stored" not in str(row[0]) for row in rows)
        finally:
            db.close()


def test_configured_evidence_sql_cannot_mutate_observation_database(tmp_path: Path) -> None:
    """Profile-controlled evidence SQL is an observation surface, never an effect path."""
    source_db = tmp_path / "source.db"
    db = sqlite3.connect(source_db)
    db.execute("CREATE TABLE events(id INTEGER PRIMARY KEY, note TEXT NOT NULL)")
    db.execute("INSERT INTO events(id,note) VALUES(1,'must survive')")
    db.commit()
    db.close()

    runtime = ProfilePipelineRuntime(root=tmp_path)
    with pytest.raises(Exception):
        runtime._query(
            str(source_db),
            "DELETE FROM events WHERE id=1 RETURNING id,note",
        )

    db = sqlite3.connect(source_db)
    try:
        assert db.execute("SELECT id,note FROM events ORDER BY id").fetchall() == [(1, "must survive")]
    finally:
        db.close()
