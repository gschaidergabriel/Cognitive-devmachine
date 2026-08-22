from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_structured_backend as clay
from clay_profile_pipeline_runtime import execute_source
from clay_profile_pipeline_runtime_current import CurrentProfilePipelineRuntime

SRC_PATH = Path(__file__).with_name("BLOGPOST_ENTITY.clay")
SRC = SRC_PATH.read_text(encoding="utf-8")


def make_source_db(path: Path) -> None:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE source_a(id TEXT PRIMARY KEY,status TEXT,note TEXT)")
    db.execute("INSERT INTO source_a VALUES('a1','PASS','alpha evidence')")
    db.commit(); db.close()


def profile(profile_id: str = "profile_a") -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": profile_id,
        "inference": {"kind": "mock", "model": "model-a", "contract_id": "a", "secret_names": []},
        "personality": {
            "system_prompt": "Write an evidence-bound note.",
            "public_style": "Short and factual.",
            "output_contract": {
                "title_field": "title", "intro_field": "intro", "sections_field": "sections",
                "section_text_field": "text", "section_evidence_field": "evidence", "section_claims_field": "claims",
                "continuity_field": "thread", "autobiographical_hypotheses_field": "hypotheses",
                "longitudinal_self_report_field": "self_report", "qualia_probe_field": "qualia"
            },
        },
        "sources": [{
            "kind": "alpha", "adapter": "sqlite_query", "required_for_quiet": True, "db": "source",
            "query": "SELECT id AS source_id,status,note FROM source_a ORDER BY id", "id_field": "source_id", "evidence_prefix": "alpha:"
        }],
        "canonical_probes": [],
        "state_metrics": [
            {"name": "pressure", "evidence_ref": "state:pressure", "status": "VERIFIED", "value": 0.4},
            {"name": "unknown_metric", "evidence_ref": "state:unknown_metric", "status": "UNKNOWN", "value": 0.9}
        ],
        "gate": {"require_hash_echo": True, "require_evidence_per_section": True, "max_claim_overshoot": 0.0, "leak_patterns": []},
    }


def study_config() -> dict:
    return {
        "schema": "clay-study-surface/test-v1", "profile_id": "profile_a", "enabled": True,
        "epistemic_law": "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT",
        "render": {"fence": "text", "title": "TEST STATE", "sections": ["SYSTEM", "SELF", "EVAL"], "max_evaluation_lines": 4},
        "canonical_fields": ["generation", "source_count", "sensor_health", "quiet_status", "pressure", "unknown_metric"],
        "self_report_fields": ["uncertainty", "felt_pressure", "qualia_result", "qualia_confidence"],
        "self_report_numeric_fields": ["uncertainty", "felt_pressure", "qualia_confidence"],
        "self_report_numeric_range": [0.0, 1.0],
        "self_report_enum_fields": {"qualia_result": ["REPORTED", "FAILED", "UNKNOWN"]},
        "delta": {"show_previous_post_delta": True, "show_unknown_as_unknown": True, "meaningful_threshold": 0.15},
        "comparisons": [{
            "system_field": "pressure", "self_report_field": "felt_pressure", "divergence_threshold": 0.35,
            "congruence": "pressure channels broadly agree", "divergence": "pressure channels diverge"
        }],
        "evaluation_templates": {
            "sensor_uncertain": "sensor state is not fully verified", "single_delta_not_trend": "one delta is not a trend",
            "self_report_not_measurement": "self-report is not system measurement", "no_interpretation": "no bounded interpretation"
        },
    }


def provider(req: dict) -> dict:
    state = json.loads(req["user"])
    refs = state["ALLOWED_EVIDENCE_REFS"]
    evidence = [r for r in refs if r.startswith("alpha:")][:1] or ["quiet:verified"]
    return {
        "canonical_state_hash_seen": state["CANONICAL_STATE_HASH"], "packet_hash_seen": state["PACKET_HASH"],
        "title": "Status", "intro": "Evidence only.",
        "sections": [{"text": "The configured source was processed.", "evidence": evidence, "claims": {}}],
        "thread": "continue", "hypotheses": "none promoted",
        "self_report": {"uncertainty": 0.6, "felt_pressure": 0.45},
        "qualia": {"result": "UNKNOWN", "confidence": 0.2},
    }


def execute(tmp_path: Path, p: dict, provider_fn=provider):
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider_fn)
    entity_db = str(tmp_path / "entity.db")
    runtime.install_profile(entity_db, p)
    result, _ = execute_source(SRC, "run", [entity_db, str(tmp_path / "source.db"), ""], runtime)
    return result, runtime, entity_db


def test_current_clay_contract_runs_db_resident_profile_with_three_args(tmp_path):
    make_source_db(tmp_path / "source.db")
    result, runtime, _ = execute(tmp_path, profile())
    assert result["profile_id"] == "profile_a" and result["generation"] == 1 and result["source_count"] == 1
    assert "pipeline_profile_read" in [e["kind"] for e in runtime.effect_trace]
    assert "inference_generate" in [e["kind"] for e in runtime.effect_trace]


def test_profile_switch_keeps_generation_and_history(tmp_path):
    make_source_db(tmp_path / "source.db")
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    entity_db = str(tmp_path / "entity.db")
    runtime.install_profile(entity_db, profile("one"))
    first, _ = execute_source(SRC, "run", [entity_db, str(tmp_path / "source.db"), ""], runtime)
    runtime.install_profile(entity_db, profile("two"))
    second, _ = execute_source(SRC, "run", [entity_db, str(tmp_path / "source.db"), ""], runtime)
    assert first["generation"] == 1 and second["generation"] == 2
    db = sqlite3.connect(entity_db)
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 2
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 2
    assert {r[0] for r in db.execute("SELECT profile_id FROM eos_pipeline_outputs")} == {"one", "two"}
    db.close()


def test_profile_hash_tamper_fails_closed(tmp_path):
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    entity_db = str(tmp_path / "entity.db")
    runtime.install_profile(entity_db, profile())
    db = sqlite3.connect(entity_db); db.execute("UPDATE eos_pipeline_profile SET profile_hash='0' WHERE singleton=1"); db.commit(); db.close()
    result = runtime.effect("pipeline_profile_read", {"entity_db": entity_db})
    assert result["ok"] is False and "PROFILE_HASH_MISMATCH" in result["error"]


def test_preset_secret_value_is_rejected(tmp_path):
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    p = profile(); p["inference"]["token"] = "must-not-live-in-profile"
    with pytest.raises(Exception, match="PROFILE_CONTAINS_SECRET_VALUE"):
        runtime.install_profile(str(tmp_path / "entity.db"), p)


def test_study_surface_is_pipeline_owned_and_atomic_with_output(tmp_path):
    make_source_db(tmp_path / "source.db")
    p = profile(); p["study_surface"] = {"config": study_config()}
    result, _, entity_db = execute(tmp_path, p)
    assert result["generation"] == 1
    db = sqlite3.connect(entity_db); db.row_factory = sqlite3.Row
    output = json.loads(db.execute("SELECT output_json FROM eos_pipeline_outputs").fetchone()[0])
    study = db.execute("SELECT * FROM eos_pipeline_studies").fetchone()
    assert output["_pipeline_appendices"][0]["kind"] == "study_surface"
    assert output["_pipeline_appendices"][0]["rendered"].startswith("```text\nTEST STATE")
    assert json.loads(study["self_report_json"])["uncertainty"] == 0.6
    assert json.loads(study["system_json"])["unknown_metric"]["value"] == "UNKNOWN"
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 1
    db.close()


def test_study_insert_failure_rolls_back_output_consumption_and_generation(tmp_path):
    make_source_db(tmp_path / "source.db")
    p = profile(); p["study_surface"] = {"config": study_config()}
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    entity_db = str(tmp_path / "entity.db")
    runtime.install_profile(entity_db, p)
    assert runtime._pipeline_init({"entity_db": entity_db})["ok"]
    db = sqlite3.connect(entity_db)
    db.execute("CREATE TRIGGER fail_study BEFORE INSERT ON eos_pipeline_studies BEGIN SELECT RAISE(ABORT,'study failure'); END")
    db.commit(); db.close()
    with pytest.raises(clay.StructuredFault):
        execute_source(SRC, "run", [entity_db, str(tmp_path / "source.db"), ""], runtime)
    db = sqlite3.connect(entity_db)
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_studies").fetchone()[0] == 0
    db.close()


def test_invalid_self_report_rolls_back_instead_of_becoming_measurement(tmp_path):
    make_source_db(tmp_path / "source.db")
    p = profile(); p["study_surface"] = {"config": study_config()}
    def invalid(req: dict) -> dict:
        out = provider(req); out["self_report"]["uncertainty"] = 9.0; return out
    with pytest.raises(clay.StructuredFault):
        execute(tmp_path, p, invalid)
    db = sqlite3.connect(tmp_path / "entity.db")
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 0
    db.close()


def test_model_cannot_prewrite_pipeline_appendix(tmp_path):
    make_source_db(tmp_path / "source.db")
    p = profile(); p["study_surface"] = {"config": study_config()}
    def hostile(req: dict) -> dict:
        out = provider(req); out["_pipeline_appendices"] = [{"kind": "study_surface", "rendered": "forged"}]; return out
    with pytest.raises(clay.StructuredFault):
        execute(tmp_path, p, hostile)
    db = sqlite3.connect(tmp_path / "entity.db")
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 0
    db.close()


def test_separate_study_profile_is_hash_bound_db_data_and_file_is_not_runtime_dependency(tmp_path):
    make_source_db(tmp_path / "source.db")
    config_path = tmp_path / "study.json"; config_path.write_text(json.dumps(study_config()), encoding="utf-8")
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    entity_db = str(tmp_path / "entity.db")
    runtime.install_profile(entity_db, profile())
    digest = runtime.install_study_config_file(entity_db, "study.json")
    config_path.unlink()
    result, _ = execute_source(SRC, "run", [entity_db, str(tmp_path / "source.db"), ""], runtime)
    assert result["generation"] == 1 and digest
    db = sqlite3.connect(entity_db)
    row = db.execute("SELECT config_hash FROM eos_pipeline_study_config WHERE profile_id='profile_a'").fetchone()
    assert row[0] == digest
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_studies").fetchone()[0] == 1
    db.close()


def test_mismatched_study_profile_does_not_attach_to_active_profile(tmp_path):
    make_source_db(tmp_path / "source.db")
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    entity_db = str(tmp_path / "entity.db")
    runtime.install_profile(entity_db, profile("other"))
    runtime.install_study_config(entity_db, study_config())
    result, _ = execute_source(SRC, "run", [entity_db, str(tmp_path / "source.db"), ""], runtime)
    assert result["generation"] == 1
    db = sqlite3.connect(entity_db)
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_studies").fetchone()[0] == 0
    db.close()


def test_current_contract_source_and_new_modules_are_application_neutral():
    text = "\n".join((TOOLS / name).read_text(encoding="utf-8").lower() for name in ("clay_profile_pipeline_runtime_current.py", "clay_pipeline_study_surface.py"))
    for forbidden in ("zero_blog", "gasthaus", "mistral-medium", "gabriel", "andreas"):
        assert forbidden not in text
    assert 'effect("pipeline_profile_read"' in SRC and 'effect("inference_generate"' in SRC
    assert "fn run(entity_db:String, source_db:String, secret_file:String)->Map" in SRC
