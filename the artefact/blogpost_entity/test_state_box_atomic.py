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
from clay_profile_pipeline_runtime import PROFILE_SCHEMA, ProfilePipelineRuntime, execute_source

SRC = Path(__file__).with_name("BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")


def make_source(path: Path) -> None:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE events(id TEXT PRIMARY KEY, status TEXT)")
    db.execute("INSERT INTO events VALUES('e1','PASS')")
    db.commit()
    db.close()


def study_profile() -> dict:
    return {
        "schema": PROFILE_SCHEMA,
        "profile_id": "study_fixture",
        "identity": {"entity_name": "Replaceable Fixture"},
        "inference": {"kind": "mock", "model": "fixture-model", "contract_id": "study"},
        "personality": {
            "system_prompt": "Write only what evidence supports.",
            "public_style": "Neutral fixture.",
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
            },
        },
        "sources": [
            {
                "kind": "event",
                "adapter": "sqlite_query",
                "required_for_quiet": True,
                "db": "source",
                "query": "SELECT id AS source_id,status FROM events ORDER BY id",
                "id_field": "source_id",
                "evidence_prefix": "event:",
            }
        ],
        "canonical_probes": [],
        "state_metrics": [
            {
                "name": "satisfaction",
                "evidence_ref": "state:satisfaction",
                "status": "VERIFIED",
                "value": 0.8,
            },
            {
                "name": "locality_pressure",
                "evidence_ref": "state:locality_pressure",
                "status": "UNKNOWN",
                "value": 0.0,
            },
        ],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.0,
            "leak_patterns": [],
        },
    }


def state_box_component() -> dict:
    return {
        "schema": "clay-state-box-fixture/v1",
        "profile_id": "study_fixture",
        "enabled": True,
        "render": {
            "fence": "text",
            "title": "STATE",
            "sections": ["SYSTEM", "SELF", "EVALUATION"],
            "max_evaluation_lines": 4,
        },
        "epistemic_law": "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT",
        "canonical_fields": [
            "generation",
            "source_count",
            "satisfaction",
            "locality_pressure",
        ],
        "canonical_metadata_fields": ["generation", "source_count"],
        "self_report_fields": ["felt_conflict"],
        "delta": {
            "show_previous_post_delta": True,
            "never_impute_missing": True,
            "meaningful_numeric_delta": 0.15,
        },
        "interpretation": {
            "comparison_rules": [],
            "confound_fields": ["model_label", "system_prompt_hash"],
            "calibration_self_report_fields": [],
            "templates": {
                "unknown": "{count} unknown system fields",
                "no_comparison": "no comparable fields",
                "confound": "confound changed: {fields}",
            },
        },
    }


def good_provider(req: dict) -> dict:
    state = json.loads(req["user"])
    evidence = [x for x in state["ALLOWED_EVIDENCE_REFS"] if x.startswith("event:")]
    if not evidence:
        evidence = ["quiet:verified"]
    return {
        "canonical_state_hash_seen": state["CANONICAL_STATE_HASH"],
        "packet_hash_seen": state["PACKET_HASH"],
        "title": "Measured update",
        "intro": "Evidence-bound.",
        "sections": [{"text": "Only measured content.", "evidence": evidence[:1], "claims": {}}],
        "thread": "continue",
        "hypotheses": "none promoted",
        "self_report": {"felt_conflict": 0.7},
    }


def test_state_box_component_is_db_resident_and_committed_atomically(tmp_path):
    make_source(tmp_path / "source.db")
    entity_db = tmp_path / "entity.db"
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=good_provider)
    runtime.install_profile(
        str(entity_db),
        study_profile(),
        components={"public_state_box": state_box_component()},
    )

    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"] is True
    assert loaded["profile"]["components"]["public_state_box"]["enabled"] is True
    assert loaded["component_hashes"]["public_state_box"]

    result, _ = execute_source(
        SRC,
        "run",
        [str(entity_db), str(tmp_path / "source.db"), ""],
        runtime,
    )
    assert result["generation"] == 1
    assert result["state_box_text"].startswith("```text\nSTATE")
    assert result["state_box_payload_hash"]

    db = sqlite3.connect(entity_db)
    db.row_factory = sqlite3.Row
    state = db.execute("SELECT generation FROM eos_pipeline_state").fetchone()
    output = db.execute("SELECT output_id,generation FROM eos_pipeline_outputs").fetchone()
    study = db.execute(
        "SELECT output_id,generation,component_kind,study_payload_json,study_payload_hash,rendered_append_text "
        "FROM eos_pipeline_study_records"
    ).fetchone()
    consumed = db.execute("SELECT output_id FROM eos_pipeline_consumed").fetchone()
    db.close()

    assert state["generation"] == output["generation"] == study["generation"] == 1
    assert output["output_id"] == study["output_id"] == consumed["output_id"]
    assert study["component_kind"] == "public_state_box"
    assert study["study_payload_hash"] == result["state_box_payload_hash"]
    assert study["rendered_append_text"] == result["state_box_text"]

    payload = json.loads(study["study_payload_json"])
    assert payload["epistemic_law"] == "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT"
    assert payload["system_state"]["satisfaction"]["status"] == "VERIFIED"
    assert payload["system_state"]["locality_pressure"]["status"] == "UNKNOWN"
    assert payload["system_state"]["locality_pressure"]["value"] is None
    assert payload["model_self_report"]["felt_conflict"] == {"status": "REPORTED", "value": 0.7}
    assert payload["context"]["system_prompt_hash"]


def test_missing_required_self_report_rolls_back_everything(tmp_path):
    make_source(tmp_path / "source.db")
    entity_db = tmp_path / "entity.db"

    def missing_self_report(req: dict) -> dict:
        payload = good_provider(req)
        payload.pop("self_report")
        return payload

    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=missing_self_report)
    runtime.install_profile(
        str(entity_db),
        study_profile(),
        components={"public_state_box": state_box_component()},
    )

    with pytest.raises(clay.StructuredFault):
        execute_source(SRC, "run", [str(entity_db), str(tmp_path / "source.db"), ""], runtime)

    db = sqlite3.connect(entity_db)
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_study_records").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 0
    db.close()


def test_state_box_builder_failure_rolls_back_output_consumption_and_generation(tmp_path):
    make_source(tmp_path / "source.db")
    entity_db = tmp_path / "entity.db"

    def exploding_builder(*args, **kwargs):
        raise ValueError("deliberate state-box failure")

    runtime = ProfilePipelineRuntime(
        root=tmp_path,
        provider_override=good_provider,
        state_box_builder=exploding_builder,
    )
    runtime.install_profile(
        str(entity_db),
        study_profile(),
        components={"public_state_box": state_box_component()},
    )

    with pytest.raises(clay.StructuredFault):
        execute_source(SRC, "run", [str(entity_db), str(tmp_path / "source.db"), ""], runtime)

    db = sqlite3.connect(entity_db)
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_packets").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_study_records").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 0
    db.close()
