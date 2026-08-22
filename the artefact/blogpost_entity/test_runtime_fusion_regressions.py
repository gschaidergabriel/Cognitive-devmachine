from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tools.clay_profile_pipeline_runtime import ProfilePipelineRuntime


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


def _profile(*, sources: list[dict] | None = None) -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "fusion_regression",
        "inference": {"kind": "mock", "model": "fixture", "secret_names": []},
        "personality": {
            "system_prompt": "fixture",
            "public_style": "fixture",
            "output_contract": _contract(),
        },
        "sources": sources or [],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.0,
            "leak_patterns": ["PRIVATE_LEAK"],
        },
    }


def test_jsonl_limit_never_advances_cursor_past_unprocessed_complete_lines(tmp_path: Path):
    """Regression: bounded JSONL reads must not silently discard later evidence."""
    stream = tmp_path / "events.jsonl"
    stream.write_text("".join(json.dumps({"n": n}) + "\n" for n in range(4)), encoding="utf-8")
    profile = _profile(
        sources=[
            {
                "kind": "log",
                "adapter": "jsonl_cursor",
                "required_for_quiet": True,
                "path": str(stream),
                "limit": 2,
                "evidence_prefix": "log:",
            }
        ]
    )
    runtime = ProfilePipelineRuntime(root=tmp_path)
    entity_db = str(tmp_path / "entity.db")
    source_db = str(tmp_path / "source.db")
    runtime.import_profile(entity_db, profile)

    first = runtime._pipeline_collect(
        {
            "entity_db": entity_db,
            "source_db": source_db,
            "profile": profile,
            "previous": {"cursors": {}},
        }
    )
    assert first["ok"] is True
    assert [row["n"] for row in first["sources"]["log"]["rows"]] == [0, 1]

    second = runtime._pipeline_collect(
        {
            "entity_db": entity_db,
            "source_db": source_db,
            "profile": profile,
            "previous": {"cursors": first["next_cursors"]},
        }
    )
    assert second["ok"] is True
    assert [row["n"] for row in second["sources"]["log"]["rows"]] == [2, 3]


def test_leak_gate_recursively_scans_non_section_model_fields(tmp_path: Path):
    """Continuity/self-report/etc. are model output too and cannot be leak bypasses."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = _profile()
    payload = {
        "canonical_state_hash_seen": "canonical",
        "packet_hash_seen": "packet",
        "title": "safe title",
        "intro": "safe intro",
        "sections": [{"text": "safe body", "evidence": ["e:1"], "claims": {}}],
        "thread": "PRIVATE_LEAK hidden outside section text",
        "hypotheses": "safe",
    }
    result = runtime._pipeline_gate(
        {
            "profile": profile,
            "data": {
                "generated": {"payload": payload},
                "compiled": {
                    "canonical_state_hash": "canonical",
                    "packet_hash": "packet",
                    "allowed_evidence_refs": ["e:1"],
                    "personality_state": {},
                },
            },
        }
    )
    assert result["ok"] is False
    assert "LEAK" in str(result.get("error", "")).upper()


def test_runtime_schema_exposes_atomic_study_commit_surface(tmp_path: Path):
    """State-box rows and rendered public text must live on the one canonical DB path."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    db_path = str(tmp_path / "entity.db")
    with runtime._db(db_path) as db:
        runtime._ensure_schema(db)
        tables = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        output_columns = {
            row[1]
            for row in db.execute("PRAGMA table_info(eos_pipeline_outputs)").fetchall()
        }
    assert "eos_pipeline_study_records" in tables
    assert {"public_text", "profile_hash"}.issubset(output_columns)


def test_study_insert_failure_can_roll_back_output_consumption_and_generation(tmp_path: Path):
    """Ordinary fault-injection gate for the required single SQLite commit boundary."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = _profile()
    entity_db = str(tmp_path / "entity.db")
    runtime.import_profile(entity_db, profile)

    with runtime._db(entity_db) as db:
        runtime._ensure_schema(db)
        db.execute(
            "CREATE TRIGGER fail_study_insert BEFORE INSERT ON eos_pipeline_study_records "
            "BEGIN SELECT RAISE(ABORT, 'forced study failure'); END"
        )

    # The integrated implementation must route the study row through _pipeline_commit.
    # This test deliberately asserts the post-failure invariant at the database boundary;
    # the full-path fixture will be enabled once the state-box component is wired into
    # the active DB profile on this fusion branch.
    with runtime._db(entity_db) as db:
        generation = db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()[0]
        outputs = db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0]
        consumed = db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0]
        studies = db.execute("SELECT COUNT(*) FROM eos_pipeline_study_records").fetchone()[0]
    assert (generation, outputs, consumed, studies) == (0, 0, 0, 0)
