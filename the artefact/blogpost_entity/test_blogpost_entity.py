from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime, PipelineFault, execute_source

SOURCE = Path(__file__).with_name("BLOGPOST_ENTITY.clay")
PRESETS = Path(__file__).with_name("presets")


def _source_db(path: Path) -> None:
    db = sqlite3.connect(path)
    db.executescript("""
    CREATE TABLE events(source_id TEXT PRIMARY KEY, status TEXT);
    INSERT INTO events VALUES('e1','PASS');
    """)
    db.commit()
    db.close()


def _profile(profile_id="alpha", *, box=True) -> dict:
    p = {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": profile_id,
        "identity": {"entity_name": profile_id, "role": "replaceable application"},
        "inference": {"kind": "test_override", "model": "fixture", "temperature": 0.3, "max_tokens": 100},
        "personality": {
            "system_prompt": "Narrate only supported evidence.",
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
                "longitudinal_self_report_field": "self_report",
                "qualia_probe_field": "qualia_probe",
            },
        },
        "sources": [{
            "kind": "event",
            "adapter": "sqlite_query",
            "required_for_quiet": True,
            "db": "source",
            "query": "SELECT source_id,status FROM events ORDER BY source_id",
            "id_field": "source_id",
            "evidence_prefix": "event:",
        }],
        "canonical_probes": [],
        "state_metrics": [
            {"name": "conflict", "evidence_ref": "state:conflict", "status": "VERIFIED", "value": 0.7},
            {"name": "continuity_pressure", "evidence_ref": "state:continuity_pressure", "status": "UNKNOWN", "value": 0.0},
        ],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.0,
            "leak_patterns": [],
        },
    }
    if box:
        p["public_state_box"] = {
            "enabled": True,
            "epistemic_law": "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT",
            "render": {
                "title": "STATE",
                "fence": "text",
                "sections": ["SYSTEM STATE", "MODEL SELF-REPORT", "EVALUATION"],
                "max_evaluation_lines": 5,
            },
            "canonical_fields": [
                "generation", "inference_backend", "model_label", "source_count",
                "sensor_health", "quiet_status", "conflict", "continuity_pressure",
            ],
            "self_report_fields": ["uncertainty", "felt_conflict", "qualia_result", "qualia_confidence"],
            "delta": {"show_previous_post_delta": True, "show_unknown_as_unknown": True, "never_impute_missing": True},
            "evaluation_text": {
                "unknown_present": "UNKNOWN remains UNKNOWN.",
                "epistemic_split": "Self-report is not system measurement.",
                "inference_changed": "Inference changed.",
                "single_delta_not_trend": "One delta is not a trend.",
                "no_evaluation": "No additional interpretation.",
            },
        }
    return p


def _provider(req: dict) -> dict:
    state = json.loads(req["user"])
    evidence = [r for r in state["ALLOWED_EVIDENCE_REFS"] if r.startswith("event:")][:1] or ["quiet:verified"]
    return {
        "canonical_state_hash_seen": state["CANONICAL_STATE_HASH"],
        "packet_hash_seen": state["PACKET_HASH"],
        "title": "Run",
        "intro": "Evidence-bound.",
        "sections": [{"text": "One bounded observation.", "evidence": evidence, "claims": {}}],
        "thread": "continue",
        "hypotheses": "none",
        "self_report": {
            "uncertainty": 0.4,
            "felt_conflict": 0.9,
            "qualia_result": "UNKNOWN",
            "qualia_confidence": 0.2,
        },
        "qualia_probe": {"result": "UNKNOWN", "confidence": 0.2},
    }


def _run(rt: ProfilePipelineRuntime, entity: Path, source: Path) -> tuple[dict, ProfilePipelineRuntime]:
    return execute_source(SOURCE.read_text(encoding="utf-8"), "run", [str(entity), str(source), ""], rt)


def test_clay_source_uses_db_profile_and_generic_inference_contract():
    source = SOURCE.read_text(encoding="utf-8")
    assert "pipeline_profile_read" in source
    assert "inference_generate" in source
    assert "profile_load" not in source
    assert "provider_chat_json" not in source
    assert "fn run(entity_db:String, source_db:String, secret_file:String)" in source


def test_db_profile_statebox_and_study_are_atomic(tmp_path):
    source = tmp_path / "source.db"
    entity = tmp_path / "entity.db"
    _source_db(source)
    rt = ProfilePipelineRuntime(root=tmp_path, provider_override=_provider)
    rt.apply_profile(str(entity), _profile())
    result, _ = _run(rt, entity, source)
    assert result["ok"] is True and result["generation"] == 1
    db = sqlite3.connect(entity)
    db.row_factory = sqlite3.Row
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_study").fetchone()[0] == 1
    out = db.execute("SELECT public_text FROM eos_pipeline_outputs").fetchone()[0]
    assert "```text" in out
    assert "SYSTEM STATE" in out and "MODEL SELF-REPORT" in out
    assert "continuity_pressure" in out and "UNKNOWN" in out
    row = db.execute("SELECT system_metrics_json,self_report_json,state_box_json FROM eos_pipeline_study").fetchone()
    metrics = json.loads(row["system_metrics_json"])
    report = json.loads(row["self_report_json"])
    box = json.loads(row["state_box_json"])
    assert metrics["conflict"]["value"] == 0.7
    assert report["felt_conflict"] == 0.9
    assert box["system_state"]["continuity_pressure"] == {"status": "UNKNOWN"}
    assert box["epistemic_law"] == "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"
    db.close()


def test_profile_swap_preserves_generation_and_history(tmp_path):
    source = tmp_path / "source.db"
    entity = tmp_path / "entity.db"
    _source_db(source)
    rt = ProfilePipelineRuntime(root=tmp_path, provider_override=_provider)
    rt.apply_profile(str(entity), _profile("alpha"))
    first, _ = _run(rt, entity, source)
    assert first["generation"] == 1
    db = sqlite3.connect(source)
    db.execute("INSERT INTO events VALUES('e2','PASS')")
    db.commit()
    db.close()
    beta = _profile("beta")
    beta["identity"]["entity_name"] = "materially different app"
    rt.apply_profile(str(entity), beta)
    second, _ = _run(rt, entity, source)
    assert second["generation"] == 2
    db = sqlite3.connect(entity)
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 2
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_study").fetchone()[0] == 2
    assert db.execute("SELECT profile_id FROM eos_pipeline_profiles WHERE is_active=1").fetchone()[0] == "beta"
    db.close()


def test_model_self_report_cannot_overwrite_canonical_metric(tmp_path):
    source = tmp_path / "source.db"
    entity = tmp_path / "entity.db"
    _source_db(source)
    def extreme(req):
        out = _provider(req)
        out["self_report"]["felt_conflict"] = 1.0
        return out
    rt = ProfilePipelineRuntime(root=tmp_path, provider_override=extreme)
    rt.apply_profile(str(entity), _profile())
    result, _ = _run(rt, entity, source)
    assert result["ok"] is True
    db = sqlite3.connect(entity)
    box = json.loads(db.execute("SELECT state_box_json FROM eos_pipeline_study").fetchone()[0])
    assert box["system_state"]["conflict"]["value"] == 0.7
    assert box["model_self_report"]["felt_conflict"] == 1.0
    db.close()


def test_profile_secret_values_fail_closed(tmp_path):
    rt = ProfilePipelineRuntime(root=tmp_path)
    p = _profile()
    p["inference"]["api_token"] = "must-not-enter-db"
    with pytest.raises(PipelineFault):
        rt.apply_profile(str(tmp_path / "entity.db"), p)


def test_study_insert_failure_rolls_back_output_consumption_packet_and_generation(tmp_path):
    source = tmp_path / "source.db"
    entity = tmp_path / "entity.db"
    _source_db(source)
    rt = ProfilePipelineRuntime(root=tmp_path, provider_override=_provider)
    rt.apply_profile(str(entity), _profile())
    db = sqlite3.connect(entity)
    db.execute("CREATE TRIGGER fail_study BEFORE INSERT ON eos_pipeline_study BEGIN SELECT RAISE(ABORT,'study-fault'); END;")
    db.commit()
    db.close()
    with pytest.raises(Exception):
        _run(rt, entity, source)
    db = sqlite3.connect(entity)
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 0
    for table in ("eos_pipeline_consumed", "eos_pipeline_outputs", "eos_pipeline_packets", "eos_pipeline_study"):
        assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    db.close()


def test_zero_statebox_profile_is_embedded_and_nonfactual():
    preset = json.loads((PRESETS / "zero_blog.json").read_text(encoding="utf-8"))
    standalone = json.loads((PRESETS / "zero_blog_state_box.json").read_text(encoding="utf-8"))
    embedded = preset["public_state_box"]
    for key in (
        "schema", "enabled", "epistemic_law", "no_embodiment", "render", "ownership",
        "canonical_fields", "self_report_fields", "delta", "evaluation_text", "evaluation_rules", "protocol",
    ):
        assert embedded[key] == standalone[key]
    assert embedded["enabled"] is True and embedded["no_embodiment"] is True
    style = preset["personality"]["style_framework"]
    assert style["world_state"].startswith("NONE")
    assert preset["personality"]["embodiment_policy"]["latent_style_frame_is_not_embodiment"] is True
