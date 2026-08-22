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
        "longitudinal_self_report_field": "self_report",
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


def _study_surface() -> dict:
    return {
        "schema": "clay-study-surface/v1",
        "profile_id": "fusion_regression",
        "enabled": True,
        "epistemic_law": "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT",
        "self_report_payload_field": "self_report",
        "canonical_fields": [
            "generation",
            "timestamp",
            "inference_backend",
            "model_label",
            "source_count",
            "sensor_health",
            "quiet_status",
        ],
        "self_report_fields": ["uncertainty"],
        "render": {
            "fence": "text",
            "title": "TEST STATE",
            "sections": ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"],
            "max_evaluation_lines": 3,
        },
    }


def _commit_payload() -> dict:
    return {
        "canonical_state_hash_seen": "canonical",
        "packet_hash_seen": "packet",
        "title": "safe title",
        "intro": "safe intro",
        "sections": [{"text": "safe body", "evidence": ["e:1"], "claims": {}}],
        "thread": "continue",
        "hypotheses": "unknown",
        "self_report": {"uncertainty": 0.4},
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


def test_required_missing_file_adapters_are_unhealthy_not_quiet(tmp_path: Path):
    """A missing required file is UNKNOWN/ERROR, never a verified empty observation."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    entity_db = str(tmp_path / "entity.db")
    source_db = str(tmp_path / "source.db")
    for adapter in ("json_snapshot", "jsonl_cursor"):
        profile = _profile(
            sources=[
                {
                    "kind": adapter,
                    "adapter": adapter,
                    "required_for_quiet": True,
                    "path": str(tmp_path / (adapter + ".missing")),
                    "limit": 2,
                    "evidence_prefix": adapter + ":",
                }
            ]
        )
        result = runtime._pipeline_collect(
            {
                "entity_db": entity_db,
                "source_db": source_db,
                "profile": profile,
                "previous": {"cursors": {}},
            }
        )
        assert result["sources"][adapter]["ok"] is False
        assert result["quiet_sensors_ok"] is False


def test_malformed_required_jsonl_is_not_silently_consumed_as_quiet(tmp_path: Path):
    """Malformed complete records must fail closed rather than disappear behind the cursor."""
    stream = tmp_path / "malformed.jsonl"
    stream.write_text("this-is-not-json\n", encoding="utf-8")
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
    result = runtime._pipeline_collect(
        {
            "entity_db": str(tmp_path / "entity.db"),
            "source_db": str(tmp_path / "source.db"),
            "profile": profile,
            "previous": {"cursors": {}},
        }
    )
    assert result["sources"]["log"]["ok"] is False
    assert result["quiet_sensors_ok"] is False


def test_sqlite_source_query_is_read_only_even_when_profile_requests_delete(tmp_path: Path):
    """Profile-configured evidence SQL must never become a hidden write/effect path."""
    source_db = tmp_path / "source.db"
    with sqlite3.connect(source_db) as db:
        db.execute("CREATE TABLE events(source_id TEXT PRIMARY KEY, value TEXT)")
        db.execute("INSERT INTO events VALUES('one','keep-me')")
    profile = _profile(
        sources=[
            {
                "kind": "events",
                "adapter": "sqlite_query",
                "db": "source",
                "query": "DELETE FROM events RETURNING source_id, value",
                "id_field": "source_id",
                "required_for_quiet": True,
                "evidence_prefix": "event:",
            }
        ]
    )
    runtime = ProfilePipelineRuntime(root=tmp_path)
    result = runtime._pipeline_collect(
        {
            "entity_db": str(tmp_path / "entity.db"),
            "source_db": str(source_db),
            "profile": profile,
            "previous": {"cursors": {}},
        }
    )
    with sqlite3.connect(source_db) as db:
        remaining = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert remaining == 1
    assert result["sources"]["events"]["ok"] is False
    assert result["quiet_sensors_ok"] is False


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


def test_runtime_schema_has_one_canonical_study_table(tmp_path: Path):
    """The study surface is persisted inside the same MiniUnifiedDB, not a side authority."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    db_path = str(tmp_path / "entity.db")
    with runtime._db(db_path) as db:
        runtime._ensure_schema(db)
        tables = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
    assert "eos_pipeline_studies" in tables
    assert "eos_pipeline_outputs" in tables
    assert "eos_pipeline_consumed" in tables
    assert "eos_pipeline_state" in tables


def test_study_insert_failure_rolls_back_output_consumption_packet_and_generation(tmp_path: Path):
    """Ordinary fault injection for the required single SQLite transaction boundary."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = _profile()
    profile["study_surface"] = _study_surface()
    entity_db = str(tmp_path / "entity.db")
    runtime.import_profile(entity_db, _profile())

    with runtime._db(entity_db) as db:
        runtime._ensure_schema(db)
        db.execute(
            "CREATE TRIGGER fail_study_insert BEFORE INSERT ON eos_pipeline_studies "
            "BEGIN SELECT RAISE(ABORT, 'forced study failure'); END"
        )

    payload = _commit_payload()
    result = runtime._pipeline_commit(
        {
            "entity_db": entity_db,
            "profile": profile,
            "previous": {"generation": 0},
            "data": {
                "collected": {
                    "consume": [{"kind": "fixture", "id": "event-1"}],
                    "next_cursors": {},
                },
                "compiled": {
                    "canonical_state_hash": "canonical",
                    "packet_hash": "packet",
                    "source_count": 1,
                    "canonical": {"sources_health": {"fixture": {"ok": True}}},
                    "packet": {"quiet_sensors_ok": True},
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
    )
    assert result["ok"] is False

    with runtime._db(entity_db) as db:
        generation = db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()[0]
        outputs = db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0]
        packets = db.execute("SELECT COUNT(*) FROM eos_pipeline_packets").fetchone()[0]
        consumed = db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0]
        studies = db.execute("SELECT COUNT(*) FROM eos_pipeline_studies").fetchone()[0]
    assert (generation, outputs, packets, consumed, studies) == (0, 0, 0, 0, 0)


def test_previous_study_is_scoped_to_active_profile_not_latest_foreign_profile(tmp_path: Path):
    """Switching application/persona must not contaminate longitudinal deltas across profiles."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = _profile()
    study_surface = _study_surface()
    study_surface["canonical_fields"].append("cognitive_conflict")
    profile["study_surface"] = study_surface
    entity_db = str(tmp_path / "entity.db")
    runtime.import_profile(entity_db, _profile())

    own_previous = {
        "schema": "clay-study-surface/v1",
        "generation": 1,
        "system_state": {
            "inference_backend": "mock",
            "model_label": "fixture",
            "cognitive_conflict": {"status": "VERIFIED", "value": 0.1},
        },
        "self_report": {},
        "deltas": {},
        "evaluation": [],
        "rendered_text": "own",
    }
    foreign_latest = {
        "schema": "clay-study-surface/v1",
        "generation": 2,
        "system_state": {
            "inference_backend": "other-backend",
            "model_label": "other-model",
            "cognitive_conflict": {"status": "VERIFIED", "value": 0.9},
        },
        "self_report": {},
        "deltas": {},
        "evaluation": [],
        "rendered_text": "foreign",
    }
    with runtime._db(entity_db) as db:
        runtime._ensure_schema(db)
        db.execute("UPDATE eos_pipeline_state SET generation=2 WHERE singleton=1")
        db.execute(
            "INSERT INTO eos_pipeline_studies VALUES(?,?,?,?,?,?,?)",
            ("own-1", 1, "fusion_regression", "clay-study-surface/v1", json.dumps(own_previous), "own", 1.0),
        )
        db.execute(
            "INSERT INTO eos_pipeline_studies VALUES(?,?,?,?,?,?,?)",
            ("foreign-2", 2, "other_profile", "clay-study-surface/v1", json.dumps(foreign_latest), "foreign", 2.0),
        )

    payload = _commit_payload()
    result = runtime._pipeline_commit(
        {
            "entity_db": entity_db,
            "profile": profile,
            "previous": {"generation": 2},
            "data": {
                "collected": {"consume": [], "next_cursors": {}},
                "compiled": {
                    "canonical_state_hash": "canonical-3",
                    "packet_hash": "packet-3",
                    "source_count": 1,
                    "canonical": {"sources_health": {"fixture": {"ok": True}}},
                    "packet": {"quiet_sensors_ok": True},
                    "personality_state": {
                        "cognitive_conflict": {"status": "VERIFIED", "value": 0.2}
                    },
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
    )
    assert result["ok"] is True
    with runtime._db(entity_db) as db:
        row = db.execute(
            "SELECT study_json FROM eos_pipeline_studies WHERE output_id=?",
            (result["output_id"],),
        ).fetchone()
    current = json.loads(row[0])
    assert abs(current["deltas"]["cognitive_conflict"] - 0.1) < 1e-9
    assert not any(item.get("code") in {"BACKEND_CHANGE", "MODEL_CHANGE"} for item in current["evaluation"])
