from __future__ import annotations

import http.server
import json
import sqlite3
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime, VERSION, execute_source

SRC_PATH = Path(__file__).with_name("BLOGPOST_ENTITY.clay")
SRC = SRC_PATH.read_text(encoding="utf-8")
STATE_BOX_PATH = Path(__file__).with_name("presets") / "zero_blog_state_box.json"


def make_source(path: Path) -> None:
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE events(id TEXT PRIMARY KEY, status TEXT, note TEXT);
        INSERT INTO events VALUES('e1','OPEN','first evidence');
        CREATE TABLE probe(state TEXT);
        INSERT INTO probe VALUES('OPEN');
        """
    )
    db.commit()
    db.close()


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
        "longitudinal_self_report_field": "self_report",
    }


def profile(pid: str = "observer", *, with_box: bool = True, prompt: str = "Be concise.") -> dict:
    p = {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": pid,
        "identity": {"entity_name": "Replaceable"},
        "inference": {
            "kind": "openai_style_chat_json",
            "endpoint": "https://example.invalid/v1/chat",
            "model": "fixture",
            "secret_names": ["SOME_API_KEY"],
            "response_pointer": "/choices/0/message/content",
        },
        "personality": {
            "system_prompt": prompt,
            "public_style": "short",
            "output_contract": contract(),
        },
        "sources": [
            {
                "kind": "event",
                "adapter": "sqlite_query",
                "required_for_quiet": True,
                "db": "source",
                "query": "SELECT id AS source_id,status,note FROM events ORDER BY id",
                "id_field": "source_id",
                "evidence_prefix": "event:",
            }
        ],
        "canonical_probes": [
            {
                "name": "probe",
                "adapter": "sqlite_query",
                "db": "source",
                "query": "SELECT state,COUNT(*) AS n FROM probe GROUP BY state",
                "evidence_ref": "probe:state",
            }
        ],
        "state_metrics": [
            {"name": "conflict", "evidence_ref": "state:conflict", "status": "VERIFIED", "value": 0.8},
            {"name": "continuity", "evidence_ref": "state:continuity", "status": "UNKNOWN", "value": 0.0},
        ],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.05,
            "leak_patterns": ["PRIVATE_MARKER"],
        },
    }
    if with_box:
        p["public_state_box"] = {
            "schema": "clay-public-state-box/v1",
            "enabled": True,
            "render": {"fence": "text", "title": "STATE", "max_evaluation_lines": 5},
            "labels": {
                "system_state": "SYSTEM",
                "model_self_report": "SELF",
                "evaluation": "EVAL",
                "no_evaluation": "No deterministic evaluation.",
            },
            "canonical_fields": [
                "generation", "timestamp", "inference_backend", "model_label",
                "source_count", "sensor_health", "quiet_status", "conflict", "continuity",
            ],
            "self_report_fields": ["felt_conflict", "uncertainty", "qualia_result", "qualia_confidence"],
            "enum_fields": {"qualia_result": ["REPORTED", "FAILED", "UNKNOWN"]},
            "delta": {"show_previous_post_delta": True, "never_impute_missing": True, "report_threshold": 0.05},
            "comparisons": [{"system": "conflict", "self_report": "felt_conflict", "threshold": 0.15}],
            "strong_self_report_threshold": 0.7,
            "evaluation_templates": {
                "unknown": "Unknown system fields: {fields}.",
                "congruent": "{system} and {self_report} are aligned.",
                "divergent": "{system} and {self_report} diverge.",
                "delta": "{field} changed by {delta:+.2f}; one delta is not a trend.",
                "self_report_calibration": "Strong language remains self-report, not system measurement.",
                "confound": "Longitudinal confound changed: {changes}.",
            },
        }
    return p


def fixture_payload(prompt: dict, *, felt: float = 0.77) -> dict:
    state = json.loads(prompt["user"])
    evidence = ["event:e1"] if "event:e1" in state["ALLOWED_EVIDENCE_REFS"] else ["quiet:verified"]
    return {
        "canonical_state_hash_seen": state["CANONICAL_STATE_HASH"],
        "packet_hash_seen": state["PACKET_HASH"],
        "title": "Measured note",
        "intro": "Only bounded claims.",
        "sections": [{"text": "The event remains visible.", "evidence": evidence, "claims": {}}],
        "thread": "continue",
        "hypotheses": "nothing promoted",
        "self_report": {
            "felt_conflict": felt,
            "uncertainty": 0.3,
            "qualia_result": "FAILED",
            "qualia_confidence": 0.2,
        },
    }


def inference_override(req: dict) -> dict:
    return fixture_payload({"user": req["user"]})


def run_direct(rt: ProfilePipelineRuntime, entity_db: Path, source_db: Path, *, mutate=None) -> dict:
    loaded = rt.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"], loaded
    p = loaded["profile"]
    base = {"entity_db": str(entity_db), "source_db": str(source_db), "profile": p, "previous": {}, "data": {}}
    assert rt.effect("pipeline_init", base)["ok"]
    previous = rt.effect("pipeline_state_read", base)
    collected = rt.effect("pipeline_collect", {**base, "previous": previous})
    compiled = rt.effect("pipeline_compile", {**base, "previous": previous, "data": collected})
    prompt = rt.effect("pipeline_build_prompt", {**base, "previous": previous, "data": compiled})
    payload = fixture_payload(prompt)
    if mutate:
        mutate(payload)
    generated = {
        "ok": True,
        "payload": payload,
        "inference_kind": p["inference"]["kind"],
        "model": p["inference"]["model"],
    }
    gated = rt.effect(
        "pipeline_gate",
        {**base, "previous": previous, "data": {"generated": generated, "compiled": compiled, "prompt": prompt}},
    )
    if not gated["ok"]:
        return {"stage": "gate", "result": gated, "previous": previous, "collected": collected, "compiled": compiled}
    committed = rt.effect(
        "pipeline_commit",
        {**base, "previous": previous, "data": {"generated": generated, "compiled": compiled, "collected": collected, "gated": gated}},
    )
    return {"stage": "commit", "result": committed, "previous": previous, "collected": collected, "compiled": compiled}


def counts(db_path: Path) -> dict:
    db = sqlite3.connect(db_path)
    out = {
        name: db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        for name in ("eos_pipeline_outputs", "eos_pipeline_consumed", "eos_pipeline_studies")
    }
    out["generation"] = db.execute("SELECT generation FROM eos_pipeline_state WHERE singleton=1").fetchone()[0]
    db.close()
    return out


def test_current_clay_source_and_runtime_contract_execute_together(tmp_path: Path) -> None:
    make_source(tmp_path / "source.db")
    rt = ProfilePipelineRuntime(root=tmp_path, inference_override=inference_override)
    assert rt.apply_profile(str(tmp_path / "entity.db"), profile())["ok"]
    result, _ = execute_source(
        SRC,
        "run",
        [str(tmp_path / "entity.db"), str(tmp_path / "source.db"), ""],
        rt,
    )
    assert result["ok"] is True
    assert result["generation"] == 1
    assert result["profile_id"] == "observer"
    assert counts(tmp_path / "entity.db") == {
        "eos_pipeline_outputs": 1,
        "eos_pipeline_consumed": 1,
        "eos_pipeline_studies": 1,
        "generation": 1,
    }


def test_contract_names_match_current_clay_source() -> None:
    assert "pipeline_profile_read" in SRC and "inference_generate" in SRC
    assert "profile_load" not in SRC and "provider_chat_json" not in SRC
    assert "fn run(entity_db:String, source_db:String, secret_file:String)" in SRC
    assert VERSION.endswith("/0.2")


def test_profile_is_db_resident_v2_and_history_survives_profile_switch(tmp_path: Path) -> None:
    make_source(tmp_path / "source.db")
    rt = ProfilePipelineRuntime(root=tmp_path)
    assert rt.apply_profile(str(tmp_path / "entity.db"), profile("alpha"))["ok"]
    assert run_direct(rt, tmp_path / "entity.db", tmp_path / "source.db")["result"]["ok"]
    p2 = profile("beta", prompt="Different role, same persistent entity DB.")
    assert rt.apply_profile(str(tmp_path / "entity.db"), p2)["ok"]
    assert run_direct(rt, tmp_path / "entity.db", tmp_path / "source.db")["result"]["ok"]
    c = counts(tmp_path / "entity.db")
    assert c["generation"] == 2 and c["eos_pipeline_outputs"] == 2 and c["eos_pipeline_studies"] == 2
    db = sqlite3.connect(tmp_path / "entity.db")
    assert {row[0] for row in db.execute("SELECT profile_id FROM eos_pipeline_outputs")} == {"alpha", "beta"}
    db.close()


def test_state_box_is_pipeline_appended_and_machine_payload_atomic(tmp_path: Path) -> None:
    make_source(tmp_path / "source.db")
    rt = ProfilePipelineRuntime(root=tmp_path)
    rt.apply_profile(str(tmp_path / "entity.db"), profile())
    out = run_direct(rt, tmp_path / "entity.db", tmp_path / "source.db")
    assert out["result"]["ok"]
    db = sqlite3.connect(tmp_path / "entity.db")
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT public_text FROM eos_pipeline_outputs").fetchone()
    study = db.execute("SELECT study_json,rendered_text FROM eos_pipeline_studies").fetchone()
    assert "Measured note" in row["public_text"] and "```text\nSTATE — generation 1" in row["public_text"]
    assert row["public_text"].endswith(study["rendered_text"])
    payload = json.loads(study["study_json"])
    assert payload["system_state"]["conflict"] == {"status": "VERIFIED", "value": 0.8}
    assert payload["system_state"]["continuity"] == "UNKNOWN"
    assert payload["model_self_report"]["felt_conflict"] == pytest.approx(0.77)
    assert payload["system_state"]["conflict"] != payload["model_self_report"]["felt_conflict"]
    db.close()


def test_self_report_out_of_range_fails_before_consumption(tmp_path: Path) -> None:
    make_source(tmp_path / "source.db")
    rt = ProfilePipelineRuntime(root=tmp_path)
    rt.apply_profile(str(tmp_path / "entity.db"), profile())
    def bad(payload: dict) -> None:
        payload["self_report"]["felt_conflict"] = 1.7
    out = run_direct(rt, tmp_path / "entity.db", tmp_path / "source.db", mutate=bad)
    assert out["stage"] == "gate" and out["result"]["ok"] is False
    assert counts(tmp_path / "entity.db") == {
        "eos_pipeline_outputs": 0,
        "eos_pipeline_consumed": 0,
        "eos_pipeline_studies": 0,
        "generation": 0,
    }


def test_secret_or_leak_in_continuity_is_rejected(tmp_path: Path) -> None:
    make_source(tmp_path / "source.db")
    rt = ProfilePipelineRuntime(root=tmp_path)
    rt.apply_profile(str(tmp_path / "entity.db"), profile())
    def leak(payload: dict) -> None:
        payload["thread"] = "PRIVATE_MARKER hidden in continuity"
    out = run_direct(rt, tmp_path / "entity.db", tmp_path / "source.db", mutate=leak)
    assert out["stage"] == "gate" and "LEAK_PATTERN" in out["result"]["error"]
    assert counts(tmp_path / "entity.db")["generation"] == 0


def test_no_state_box_when_application_profile_disables_it(tmp_path: Path) -> None:
    make_source(tmp_path / "source.db")
    rt = ProfilePipelineRuntime(root=tmp_path)
    rt.apply_profile(str(tmp_path / "entity.db"), profile(with_box=False))
    out = run_direct(rt, tmp_path / "entity.db", tmp_path / "source.db")
    assert out["result"]["ok"]
    c = counts(tmp_path / "entity.db")
    assert c["eos_pipeline_studies"] == 0 and c["generation"] == 1


def test_unknown_is_never_imputed_into_delta(tmp_path: Path) -> None:
    make_source(tmp_path / "source.db")
    rt = ProfilePipelineRuntime(root=tmp_path)
    rt.apply_profile(str(tmp_path / "entity.db"), profile())
    assert run_direct(rt, tmp_path / "entity.db", tmp_path / "source.db")["result"]["ok"]
    assert run_direct(rt, tmp_path / "entity.db", tmp_path / "source.db")["result"]["ok"]
    db = sqlite3.connect(tmp_path / "entity.db")
    study = json.loads(db.execute("SELECT study_json FROM eos_pipeline_studies ORDER BY generation DESC LIMIT 1").fetchone()[0])
    db.close()
    assert study["deltas"]["continuity"] == "UNKNOWN"
    assert study["system_state"]["quiet_status"] == "VERIFIED_QUIET"


def test_jsonl_limit_does_not_skip_unprocessed_or_partial_tail(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    make_source(source)
    p = profile(with_box=False)
    log = tmp_path / "events.jsonl"
    log.write_bytes(b'{"n":1}\n{"n":2}\n{"n":3}\n{"n":4}')
    p["sources"] = [{
        "kind": "stream", "adapter": "jsonl_cursor", "required_for_quiet": True,
        "path": str(log), "limit": 2, "evidence_prefix": "stream:",
    }]
    rt = ProfilePipelineRuntime(root=tmp_path)
    rt.apply_profile(str(tmp_path / "entity.db"), p)
    pr = rt.effect("pipeline_profile_read", {"entity_db": str(tmp_path / "entity.db")})["profile"]
    base = {
        "entity_db": str(tmp_path / "entity.db"), "source_db": str(source), "profile": pr,
        "previous": {"generation": 0, "continuity": {}, "cursors": {}}, "data": {},
    }
    first = rt.effect("pipeline_collect", base)
    assert [x["n"] for x in first["sources"]["stream"]["rows"]] == [1, 2]
    cursor = first["next_cursors"]["stream"]
    assert cursor == len(b'{"n":1}\n{"n":2}\n')
    second = rt.effect(
        "pipeline_collect",
        {**base, "previous": {"generation": 0, "continuity": {}, "cursors": {"stream": cursor}}},
    )
    assert [x["n"] for x in second["sources"]["stream"]["rows"]] == [3]
    assert second["next_cursors"]["stream"] == len(b'{"n":1}\n{"n":2}\n{"n":3}\n')


def test_malformed_jsonl_is_sensor_error_without_cursor_advance(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    make_source(source)
    p = profile(with_box=False)
    log = tmp_path / "bad.jsonl"
    log.write_text('{"n":1}\nnot-json\n{"n":3}\n', encoding="utf-8")
    p["sources"] = [{
        "kind": "stream", "adapter": "jsonl_cursor", "required_for_quiet": True,
        "path": str(log), "limit": 10, "evidence_prefix": "stream:",
    }]
    rt = ProfilePipelineRuntime(root=tmp_path)
    rt.apply_profile(str(tmp_path / "entity.db"), p)
    pr = rt.effect("pipeline_profile_read", {"entity_db": str(tmp_path / "entity.db")})["profile"]
    out = rt.effect(
        "pipeline_collect",
        {
            "entity_db": str(tmp_path / "entity.db"), "source_db": str(source), "profile": pr,
            "previous": {"generation": 0, "continuity": {}, "cursors": {}}, "data": {},
        },
    )
    assert out["sources"]["stream"]["ok"] is False
    assert out["quiet_sensors_ok"] is False
    assert out["next_cursors"].get("stream", 0) == 0


def test_local_exec_is_direct_argv_tokenless_and_cleans_prompt(tmp_path: Path) -> None:
    model = tmp_path / "fixture.gguf"
    model.write_text("fixture", encoding="utf-8")
    runner = tmp_path / "runner.py"
    runner.write_text('import json,sys; print(json.dumps({"ok_from_local": True, "argv": sys.argv[1:]}))', encoding="utf-8")
    rt = ProfilePipelineRuntime(root=tmp_path)
    out = rt.effect(
        "inference_generate",
        {
            "inference": {
                "kind": "local_exec", "local_model_path": str(model),
                "local_argv_json": [sys.executable, str(runner), "{{MODEL_PATH}}", "{{PROMPT_FILE}}", "{{MAX_TOKENS}}", "{{TEMPERATURE}}"],
                "max_tokens": 33, "temperature": 0.2,
            },
            "system": "S", "user": "U", "secret_file": "",
        },
    )
    assert out["ok"] and out["payload"]["ok_from_local"] is True
    assert out["payload"]["argv"][0] == str(model)
    assert not list(tmp_path.glob("clay_prompt_*.txt"))


def test_loopback_api_is_tokenless_but_nonloopback_plaintext_is_rejected(tmp_path: Path) -> None:
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:
            pass
        def do_POST(self) -> None:
            n = int(self.headers.get("content-length", "0"))
            self.rfile.read(n)
            body = json.dumps({"choices": [{"message": {"content": json.dumps({"loopback": True})}}]}).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        rt = ProfilePipelineRuntime(root=tmp_path, allow_network=True)
        out = rt.effect(
            "inference_generate",
            {
                "inference": {
                    "kind": "openai_style_chat_json",
                    "endpoint": f"http://127.0.0.1:{server.server_port}/v1/chat",
                    "model": "local", "secret_names": [],
                    "response_pointer": "/choices/0/message/content",
                },
                "system": "S", "user": "U", "secret_file": "",
            },
        )
        assert out["ok"] and out["payload"] == {"loopback": True}
        bad = rt.effect(
            "inference_generate",
            {
                "inference": {"kind": "openai_style_chat_json", "endpoint": "http://example.com/v1/chat", "model": "x", "secret_names": []},
                "system": "S", "user": "U", "secret_file": "",
            },
        )
        assert bad["ok"] is False and bad["error_kind"] == "PLAINTEXT_NON_LOOPBACK_FORBIDDEN"
    finally:
        server.shutdown()
        server.server_close()


def test_current_zero_state_box_sidecar_shape_is_generic_runtime_data(tmp_path: Path) -> None:
    make_source(tmp_path / "source.db")
    p = profile("zero_blog")
    p["state_metrics"] = [
        {"name": "cognitive_conflict", "evidence_ref": "state:cognitive_conflict", "status": "VERIFIED", "value": 0.8},
        {"name": "continuity_pressure", "evidence_ref": "state:continuity_pressure", "status": "UNKNOWN", "value": 0.0},
    ]
    p["public_state_box"] = json.loads(STATE_BOX_PATH.read_text(encoding="utf-8"))
    rt = ProfilePipelineRuntime(root=tmp_path)
    assert rt.apply_profile(str(tmp_path / "entity.db"), p)["ok"]
    out = run_direct(rt, tmp_path / "entity.db", tmp_path / "source.db")
    assert out["result"]["ok"]
    text = out["result"]["public_text"]
    assert "ZERO STATE — generation 1" in text
    assert "\nSYSTEM STATE\n" in text
    assert "\nMODEL SELF-REPORT\n" in text
    assert "\nAUSWERTUNG\n" in text


def test_old_provider_kind_output_schema_is_forward_compatible(tmp_path: Path) -> None:
    make_source(tmp_path / "source.db")
    entity = tmp_path / "entity.db"
    db = sqlite3.connect(entity)
    db.executescript(
        """
        CREATE TABLE eos_pipeline_outputs(
          output_id TEXT PRIMARY KEY, ts REAL NOT NULL, generation INTEGER NOT NULL,
          profile_id TEXT NOT NULL, output_json TEXT NOT NULL, provider_kind TEXT NOT NULL,
          model TEXT, packet_hash TEXT NOT NULL, canonical_hash TEXT NOT NULL);
        """
    )
    db.commit()
    db.close()
    rt = ProfilePipelineRuntime(root=tmp_path)
    assert rt.apply_profile(str(entity), profile())["ok"]
    out = run_direct(rt, entity, tmp_path / "source.db")
    assert out["result"]["ok"]
    db = sqlite3.connect(entity)
    row = db.execute("SELECT provider_kind,inference_kind,public_text FROM eos_pipeline_outputs").fetchone()
    db.close()
    assert row[0] == "openai_style_chat_json" and row[1] == "openai_style_chat_json" and "STATE" in row[2]


def test_study_insert_failure_rolls_back_output_consumption_and_generation(tmp_path: Path) -> None:
    """Regression-only codification of the go atomicity fault-injection experiment."""
    make_source(tmp_path / "source.db")
    entity = tmp_path / "entity.db"
    rt = ProfilePipelineRuntime(root=tmp_path)
    assert rt.apply_profile(str(entity), profile())["ok"]
    db = sqlite3.connect(entity)
    db.execute(
        "CREATE TRIGGER deliberate_study_abort BEFORE INSERT ON eos_pipeline_studies "
        "BEGIN SELECT RAISE(ABORT,'DELIBERATE_STUDY_ABORT'); END;"
    )
    db.commit()
    db.close()
    out = run_direct(rt, entity, tmp_path / "source.db")
    assert out["stage"] == "commit" and out["result"]["ok"] is False
    assert "DELIBERATE_STUDY_ABORT" in out["result"]["error"]
    assert counts(entity) == {
        "eos_pipeline_outputs": 0,
        "eos_pipeline_consumed": 0,
        "eos_pipeline_studies": 0,
        "generation": 0,
    }


def test_runtime_binary_semantics_are_application_neutral() -> None:
    text = (TOOLS / "clay_profile_pipeline_runtime.py").read_text(encoding="utf-8").lower()
    for forbidden in ("zero_blog", "gasthaus", "bare metal", "t_omega", "gabriel", "andreas"):
        assert forbidden not in text


def test_profile_secret_values_are_rejected_but_secret_names_are_allowed(tmp_path: Path) -> None:
    rt = ProfilePipelineRuntime(root=tmp_path)
    assert rt.apply_profile(str(tmp_path / "entity.db"), profile())["ok"]
    bad = profile()
    bad["inference"]["api_token"] = "supersecret"
    out = rt.apply_profile(str(tmp_path / "entity2.db"), bad)
    assert out["ok"] is False and "SECRET_VALUE_IN_PROFILE" in out["error"]
