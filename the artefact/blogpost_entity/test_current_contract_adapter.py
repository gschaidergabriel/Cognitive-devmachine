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

from clay_profile_pipeline_runtime import execute_source
from clay_profile_pipeline_runtime_current import CurrentProfilePipelineRuntime

SRC_PATH = Path(__file__).with_name("BLOGPOST_ENTITY.clay")
SRC = SRC_PATH.read_text(encoding="utf-8")


def make_source_db(path: Path) -> None:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE source_a(id TEXT PRIMARY KEY,status TEXT,note TEXT)")
    db.execute("INSERT INTO source_a VALUES('a1','PASS','alpha evidence')")
    db.commit()
    db.close()


def profile(profile_id: str = "profile_a") -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": profile_id,
        "inference": {"kind": "mock", "model": "model-a", "contract_id": "a", "secret_names": []},
        "personality": {
            "system_prompt": "Write an evidence-bound note.",
            "public_style": "Short and factual.",
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
        "sources": [
            {
                "kind": "alpha",
                "adapter": "sqlite_query",
                "required_for_quiet": True,
                "db": "source",
                "query": "SELECT id AS source_id,status,note FROM source_a ORDER BY id",
                "id_field": "source_id",
                "evidence_prefix": "alpha:",
            }
        ],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {"require_hash_echo": True, "require_evidence_per_section": True, "max_claim_overshoot": 0.0, "leak_patterns": []},
    }


def provider(req: dict) -> dict:
    state = json.loads(req["user"])
    refs = state["ALLOWED_EVIDENCE_REFS"]
    evidence = [r for r in refs if r.startswith("alpha:")][:1] or ["quiet:verified"]
    return {
        "canonical_state_hash_seen": state["CANONICAL_STATE_HASH"],
        "packet_hash_seen": state["PACKET_HASH"],
        "title": "Status",
        "intro": "Evidence only.",
        "sections": [{"text": "The configured source was processed.", "evidence": evidence, "claims": {}}],
        "thread": "continue",
        "hypotheses": "none promoted",
    }


def test_current_clay_contract_runs_db_resident_profile_with_three_args(tmp_path):
    make_source_db(tmp_path / "source.db")
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    runtime.install_profile(str(tmp_path / "entity.db"), profile())
    result, _ = execute_source(
        SRC,
        "run",
        [str(tmp_path / "entity.db"), str(tmp_path / "source.db"), ""],
        runtime,
    )
    assert result["profile_id"] == "profile_a"
    assert result["generation"] == 1
    assert result["source_count"] == 1
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
    assert first["generation"] == 1
    assert second["generation"] == 2
    db = sqlite3.connect(entity_db)
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 2
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 2
    assert {r[0] for r in db.execute("SELECT profile_id FROM eos_pipeline_outputs")} == {"one", "two"}
    db.close()


def test_profile_hash_tamper_fails_closed(tmp_path):
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    entity_db = str(tmp_path / "entity.db")
    runtime.install_profile(entity_db, profile())
    db = sqlite3.connect(entity_db)
    db.execute("UPDATE eos_pipeline_profile SET profile_hash='0' WHERE singleton=1")
    db.commit()
    db.close()
    result = runtime.effect("pipeline_profile_read", {"entity_db": entity_db})
    assert result["ok"] is False
    assert "PROFILE_HASH_MISMATCH" in result["error"]


def test_preset_secret_value_is_rejected(tmp_path):
    runtime = CurrentProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    p = profile()
    p["inference"]["token"] = "must-not-live-in-profile"
    with pytest.raises(Exception, match="PROFILE_CONTAINS_SECRET_VALUE"):
        runtime.install_profile(str(tmp_path / "entity.db"), p)


def test_current_contract_source_and_adapter_are_application_neutral():
    adapter = (TOOLS / "clay_profile_pipeline_runtime_current.py").read_text(encoding="utf-8").lower()
    for forbidden in ("zero_blog", "gasthaus", "mistral-medium", "gabriel", "andreas"):
        assert forbidden not in adapter
    assert 'effect("pipeline_profile_read"' in SRC
    assert 'effect("inference_generate"' in SRC
    assert "fn run(entity_db:String, source_db:String, secret_file:String)->Map" in SRC
