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


def _profile(prompt: str = "profile-v1") -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "snapshot-fence",
        "inference": {"kind": "mock", "model": "fixture", "secret_names": []},
        "personality": {
            "system_prompt": prompt,
            "public_style": "compact",
            "output_contract": {
                "title_field": "title",
                "intro_field": "intro",
                "sections_field": "sections",
                "section_text_field": "text",
                "section_evidence_field": "evidence",
                "section_claims_field": "claims",
                "continuity_field": "thread",
                "autobiographical_hypotheses_field": "hypotheses",
                "longitudinal_self_report_field": "report",
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


def _study_config(label: str) -> dict:
    return {
        "schema": "snapshot-fence-study/v1",
        "profile_id": "snapshot-fence",
        "enabled": False,
        "label": label,
        "epistemic_law": "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT",
    }


def _commit_input(entity_db: str, loaded_profile: dict, previous_generation: int = 0) -> dict:
    payload = {
        "title": "safe",
        "intro": "safe",
        "sections": [],
        "thread": "continue",
        "hypotheses": "none",
        "report": {},
    }
    return {
        "entity_db": entity_db,
        "profile": loaded_profile,
        "previous": {"generation": previous_generation},
        "data": {
            "collected": {"consume": [], "next_cursors": {}},
            "compiled": {
                "canonical_state_hash": "canonical",
                "packet_hash": "packet",
                "source_count": 0,
                "canonical": {"sources_health": {}},
                "packet": {"quiet_sensors_ok": False},
                "personality_state": {},
            },
            "generated": {
                "payload": payload,
                "provider_kind": "mock",
                "inference_kind": "mock",
                "model": "fixture",
            },
            "gated": {"payload": payload},
        },
    }


def _assert_no_generation_writes(entity_db: Path) -> None:
    db = sqlite3.connect(entity_db)
    assert db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_packets").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_studies").fetchone()[0] == 0
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    db.close()


def test_mid_run_profile_replacement_invalidates_loaded_snapshot(tmp_path: Path) -> None:
    """A generation CAS alone cannot authorize a commit under superseded profile semantics."""
    entity_db = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)
    runtime.import_profile(str(entity_db), _profile("profile-v1"))
    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"] is True

    # Same entity generation, but the executable semantics are changed before the old run commits.
    runtime.import_profile(str(entity_db), _profile("profile-v2"))
    result = runtime._pipeline_commit(_commit_input(str(entity_db), loaded["profile"]))

    assert result["ok"] is False, "superseded profile snapshot must fail closed before any write"
    _assert_no_generation_writes(entity_db)


def test_mid_run_study_config_replacement_invalidates_loaded_snapshot(tmp_path: Path) -> None:
    """Study/render config belongs to the same run snapshot and must be generation-fenced too."""
    entity_db = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path)
    runtime.import_profile(str(entity_db), _profile())
    runtime.import_study_surface(str(entity_db), _study_config("study-v1"))
    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"] is True

    runtime.import_study_surface(str(entity_db), _study_config("study-v2"))
    result = runtime._pipeline_commit(_commit_input(str(entity_db), loaded["profile"]))

    assert result["ok"] is False, "superseded study-config snapshot must fail closed before any write"
    _assert_no_generation_writes(entity_db)
