from __future__ import annotations

import json
import os
import sqlite3
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_structured_backend as clay
from clay_profile_pipeline_runtime import ProfilePipelineRuntime, execute_source

SRC = Path(__file__).with_name("BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")


def contract() -> dict:
    return {
        "title_field": "title",
        "intro_field": "intro",
        "sections_field": "sections",
        "section_text_field": "text",
        "section_evidence_field": "evidence",
        "section_claims_field": "claims",
        "continuity_field": "thread",
        "autobiographical_hypotheses_field": "hypotheses",
        "longitudinal_self_report_field": "report",
    }


def profile(query: str, *, source_adapter: str = "sqlite_query", source_path: str | None = None) -> dict:
    source = {
        "kind": "event",
        "adapter": source_adapter,
        "required_for_quiet": True,
        "evidence_prefix": "event:",
    }
    if source_adapter == "sqlite_query":
        source.update({"db": "source", "query": query, "id_field": "source_id"})
    else:
        source.update({"path": source_path, "limit": 1})
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "study_profile",
        "inference": {"kind": "mock", "model": "model-r", "secret_names": []},
        "personality": {
            "system_prompt": "Evidence-bound test writer.",
            "public_style": "compact",
            "output_contract": contract(),
        },
        "sources": [source],
        "canonical_probes": [],
        "state_metrics": [
            {
                "name": "signal",
                "evidence_ref": "state:signal",
                "status": "VERIFIED",
                "value": 0.7,
            }
        ],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.0,
            "leak_patterns": [],
        },
    }


def good_provider(req: dict) -> dict:
    state = json.loads(req["user"])
    refs = state["ALLOWED_EVIDENCE_REFS"]
    evidence = [next((ref for ref in refs if ref.startswith("event:")), "state:signal")]
    return {
        "canonical_state_hash_seen": state["CANONICAL_STATE_HASH"],
        "packet_hash_seen": state["PACKET_HASH"],
        "title": "State",
        "intro": "Bounded.",
        "sections": [{"text": "Only admitted evidence.", "evidence": evidence, "claims": {}}],
        "thread": "continue",
        "hypotheses": "unknown remains unknown",
        "report": {"felt": 0.65},
    }


def run(runtime: ProfilePipelineRuntime, entity_db: Path, source_db: Path):
    return execute_source(SRC, "run", [str(entity_db), str(source_db), ""], runtime)[0]


def make_events(path: Path, count: int) -> None:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE events(id INTEGER PRIMARY KEY,status TEXT)")
    db.executemany("INSERT INTO events VALUES(?,?)", [(i, "PASS") for i in range(1, count + 1)])
    db.commit()
    db.close()


def test_terminal_sql_limit_is_delivery_budget_not_permanent_head_window(tmp_path):
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    make_events(source_db, 3)
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=good_provider)
    runtime.import_profile(
        str(entity_db),
        profile("SELECT id AS source_id,status FROM events ORDER BY id LIMIT 1"),
    )

    assert run(runtime, entity_db, source_db)["source_count"] == 1
    assert run(runtime, entity_db, source_db)["source_count"] == 1
    assert run(runtime, entity_db, source_db)["source_count"] == 1

    db = sqlite3.connect(entity_db)
    consumed = [row[0] for row in db.execute("SELECT source_id FROM eos_pipeline_consumed ORDER BY CAST(source_id AS INTEGER)")]
    assert consumed == ["1", "2", "3"]
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 3
    db.close()


def test_repeated_identical_verified_quiet_packets_are_distinct_generations(tmp_path):
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    make_events(source_db, 1)
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=good_provider)
    runtime.import_profile(str(entity_db), profile("SELECT id AS source_id,status FROM events ORDER BY id LIMIT 1"))

    first = run(runtime, entity_db, source_db)
    quiet_one = run(runtime, entity_db, source_db)
    quiet_two = run(runtime, entity_db, source_db)
    assert [first["generation"], quiet_one["generation"], quiet_two["generation"]] == [1, 2, 3]
    assert quiet_one["source_count"] == quiet_two["source_count"] == 0
    assert quiet_one["packet_hash"] == quiet_two["packet_hash"]

    db = sqlite3.connect(entity_db)
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_packets").fetchone()[0] == 3
    assert db.execute(
        "SELECT COUNT(*) FROM eos_pipeline_packets WHERE packet_hash=?",
        (quiet_one["packet_hash"],),
    ).fetchone()[0] == 2
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    db.close()


def study_config() -> dict:
    return {
        "schema": "clay-test-state-box/v1",
        "profile_id": "study_profile",
        "enabled": True,
        "epistemic_law": "SYSTEM_MEASUREMENT != MODEL_SELF_REPORT",
        "self_report_payload_field": "report",
        "canonical_fields": [
            "generation",
            "timestamp",
            "inference_backend",
            "model_label",
            "source_count",
            "sensor_health",
            "quiet_status",
            "signal",
        ],
        "self_report_fields": ["felt"],
        "comparison_pairs": [
            {"system_metric": "signal", "self_report_metric": "felt", "tolerance": 0.1}
        ],
        "render": {
            "append_after_public_post": True,
            "fence": "text",
            "title": "STATE",
            "sections": ["SYSTEM STATE", "MODEL SELF-REPORT", "AUSWERTUNG"],
            "max_evaluation_lines": 4,
        },
    }


def test_study_appendix_output_consumption_and_generation_commit_atomically(tmp_path):
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    make_events(source_db, 1)
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=good_provider)
    runtime.import_profile(str(entity_db), profile("SELECT id AS source_id,status FROM events ORDER BY id"))
    runtime.import_study_surface(str(entity_db), study_config())

    result = run(runtime, entity_db, source_db)
    assert result["study_recorded"] is True
    assert result["study_appendix"].count("```text") == 1
    assert result["study_appendix"].count("```") == 2

    db = sqlite3.connect(entity_db)
    output = db.execute("SELECT output_id,generation FROM eos_pipeline_outputs").fetchone()
    study = db.execute("SELECT output_id,generation,study_json,rendered_text FROM eos_pipeline_studies").fetchone()
    assert output[:2] == study[:2] == (result["output_id"], 1)
    record = json.loads(study[2])
    assert record["system_state"]["signal"] == {"status": "VERIFIED", "value": 0.7}
    assert record["self_report"]["felt"] == 0.65
    assert record["rendered_text"] == study[3] == result["study_appendix"]
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 1
    db.close()


def test_bad_self_report_rolls_back_new_event_output_study_and_generation(tmp_path):
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    make_events(source_db, 1)
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=good_provider)
    runtime.import_profile(str(entity_db), profile("SELECT id AS source_id,status FROM events ORDER BY id"))
    runtime.import_study_surface(str(entity_db), study_config())
    run(runtime, entity_db, source_db)

    db = sqlite3.connect(source_db)
    db.execute("INSERT INTO events VALUES(2,'PASS')")
    db.commit()
    db.close()

    def bad_provider(req: dict) -> dict:
        payload = good_provider(req)
        payload["report"] = {"felt": 7.0}
        return payload

    runtime.provider_override = bad_provider
    with pytest.raises(clay.StructuredFault):
        run(runtime, entity_db, source_db)

    db = sqlite3.connect(entity_db)
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_outputs").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_studies").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM eos_pipeline_consumed").fetchone()[0] == 1
    assert db.execute(
        "SELECT COUNT(*) FROM eos_pipeline_consumed WHERE source_id='2'"
    ).fetchone()[0] == 0
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    db.close()


def test_jsonl_limit_advances_only_processed_complete_lines(tmp_path):
    source_db = tmp_path / "source.db"
    entity_db = tmp_path / "entity.db"
    sqlite3.connect(source_db).close()
    log_path = tmp_path / "events.jsonl"
    log_path.write_text('{"n":1}\n{"n":2}\n{"n":3}\n', encoding="utf-8")

    p = profile("", source_adapter="jsonl_cursor", source_path=str(log_path))
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=good_provider)
    runtime.import_profile(str(entity_db), p)
    assert run(runtime, entity_db, source_db)["source_count"] == 1
    assert run(runtime, entity_db, source_db)["source_count"] == 1
    assert run(runtime, entity_db, source_db)["source_count"] == 1

    db = sqlite3.connect(entity_db)
    cursor = json.loads(db.execute("SELECT cursors_json FROM eos_pipeline_state").fetchone()[0])["event"]
    assert cursor == len(log_path.read_bytes())
    assert db.execute("SELECT generation FROM eos_pipeline_state").fetchone()[0] == 3
    db.close()


def test_legacy_packet_hash_primary_key_is_migrated_without_data_loss(tmp_path):
    entity_db = tmp_path / "entity.db"
    db = sqlite3.connect(entity_db)
    db.execute(
        """CREATE TABLE eos_pipeline_packets(
             packet_hash TEXT PRIMARY KEY,output_id TEXT NOT NULL,ts REAL NOT NULL,
             generation INTEGER NOT NULL,profile_id TEXT NOT NULL,source_count INTEGER NOT NULL,
             canonical_hash TEXT NOT NULL)"""
    )
    db.execute("INSERT INTO eos_pipeline_packets VALUES('p1','o1',1.0,1,'old',0,'c1')")
    db.commit()
    db.close()

    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=good_provider)
    runtime.import_profile(str(entity_db), profile("SELECT 1 AS source_id,'PASS' AS status"))

    db = sqlite3.connect(entity_db)
    pk = [row[1] for row in db.execute("PRAGMA table_info(eos_pipeline_packets)") if row[5]]
    assert pk == ["output_id"]
    assert db.execute(
        "SELECT output_id,packet_hash,generation FROM eos_pipeline_packets"
    ).fetchone() == ("o1", "p1", 1)
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    db.close()


def test_local_exec_child_environment_does_not_inherit_provider_secret(tmp_path, monkeypatch):
    model = tmp_path / "model.gguf"
    model.write_bytes(b"fixture")
    runner = tmp_path / "runner.py"
    runner.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os\n"
        "print(json.dumps({'seen_secret': os.environ.get('MISTRAL_API_KEY')}))\n",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("MISTRAL_API_KEY", "must-not-enter-child")

    runtime = ProfilePipelineRuntime(root=tmp_path)
    generated = runtime._local_exec_generate(
        {
            "kind": "local_exec",
            "local_model_path": str(model),
            "local_argv_json": [sys.executable, str(runner)],
            "local_env_allowlist": ["PATH"],
        },
        {"system": "s", "user": "u"},
    )
    assert generated["ok"] is True
    assert generated["payload"]["seen_secret"] is None
    assert os.environ["MISTRAL_API_KEY"] == "must-not-enter-child"
