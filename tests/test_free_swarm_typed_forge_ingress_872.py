from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import free_swarm_typed_forge_ingress_872 as typed  # noqa: E402
import run_free_evidence_forge as forge  # noqa: E402
from free_swarm_delta_ingress import SCHEMA as INGRESS_SCHEMA  # noqa: E402
from free_swarm_typed_delta_bridge import CANDIDATE_SCHEMA  # noqa: E402

typed.install(forge)


def proposal():
    return {
        "delta_id": "typed-one",
        "hypothesis": "typed sidecar is consumed",
        "mechanism": "forge sidecar ingress",
        "target_files": ["tools/x.py"],
        "patch_unified_diff": "--- a/tools/x.py\n+++ b/tools/x.py\n@@ -1 +1 @@\n-a\n+b\n",
        "test_commands": ["python -m pytest -q tests/test_x.py"],
        "negative_test_commands": [],
        "benchmark_command": "",
        "metric": "accepted_candidate_count",
        "expected_direction": "higher",
        "baseline_needed": True,
        "falsifier": "typed sidecar produces no candidate",
        "risk": "sidecar tampering",
        "ready_for_forge": True,
    }


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def memory_db():
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE candidates(
          candidate_hash TEXT PRIMARY KEY, delta_id TEXT, provider TEXT, model TEXT, role TEXT,
          worker_sha TEXT, proposal_json TEXT NOT NULL, ready INTEGER NOT NULL DEFAULT 0,
          state TEXT NOT NULL DEFAULT 'NEW', ingested_at TEXT NOT NULL, evaluated_at TEXT,
          last_reason TEXT, repo_head TEXT
        );
        CREATE TABLE counters(key TEXT PRIMARY KEY,value REAL NOT NULL DEFAULT 0);
        """
    )
    return con


def write_typed(active: Path, *, text: str, obj: dict, sidecar_hash: str | None = None,
                worker_provider: str = "nvidia", sidecar_provider: str = "nvidia"):
    worker_sha = hashlib.sha256(text.encode()).hexdigest()
    proposal_sha = hashlib.sha256(canonical(obj).encode()).hexdigest()
    worker = {
        "http_status": 200,
        "text": text,
        "text_sha256": worker_sha,
        "provider": worker_provider,
        "model": "model",
        "role": "hcu_grid10",
        "repo_head_at_prompt": "a" * 40,
        "delta_ingress": {
            "schema": INGRESS_SCHEMA,
            "status": "VALID_READY",
            "valid": True,
            "ready_for_forge": True,
            "reasons": [],
            "proposal_sha256": proposal_sha,
        },
    }
    sidecar = {
        "schema": CANDIDATE_SCHEMA,
        "ingress_schema": INGRESS_SCHEMA,
        "provider": sidecar_provider,
        "model": "model",
        "role": "hcu_grid10",
        "repo_head_at_prompt": "a" * 40,
        "worker_text_sha256": worker_sha,
        "proposal_sha256": sidecar_hash or proposal_sha,
        "ready_for_forge": True,
        "proposal": obj,
    }
    (active / "workers.jsonl").write_text(json.dumps(worker) + "\n")
    (active / "architecture_deltas.jsonl").write_text(json.dumps(sidecar) + "\n")


def counter(con, key):
    row = con.execute("SELECT value FROM counters WHERE key=?", (key,)).fetchone()
    return float(row[0]) if row else 0.0


def test_typed_sidecar_is_consumed_without_forge_prose_reparse(tmp_path, monkeypatch):
    active = tmp_path / "active-test"
    active.mkdir()
    write_typed(active, text="model text intentionally has no architecture marker", obj=proposal())
    monkeypatch.setattr(forge, "ARTIFACT_ROOT", tmp_path)
    con = memory_db()
    assert forge.ingest_worker_candidates(con) == 1
    assert con.execute("SELECT ready,provider,repo_head FROM candidates").fetchone() == (1, "nvidia", "a" * 40)
    assert counter(con, "typed_candidates_ingested") == 1


def test_typed_hash_tamper_never_falls_back_to_valid_raw_prose(tmp_path, monkeypatch):
    active = tmp_path / "active-test"
    active.mkdir()
    obj = proposal()
    text = "ARCHITECTURE_DELTA_JSON=" + json.dumps(obj)
    write_typed(active, text=text, obj=obj, sidecar_hash="0" * 64)
    monkeypatch.setattr(forge, "ARTIFACT_ROOT", tmp_path)
    con = memory_db()
    assert forge.ingest_worker_candidates(con) == 0
    assert con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 0
    assert counter(con, "typed_candidates_rejected") == 1


def test_typed_identity_mismatch_fails_closed(tmp_path, monkeypatch):
    active = tmp_path / "active-test"
    active.mkdir()
    write_typed(active, text="typed worker", obj=proposal(), sidecar_provider="groq")
    monkeypatch.setattr(forge, "ARTIFACT_ROOT", tmp_path)
    con = memory_db()
    assert forge.ingest_worker_candidates(con) == 0
    assert counter(con, "typed_candidates_rejected") == 1


def test_pretyped_historical_row_retains_legacy_compatibility(tmp_path, monkeypatch):
    active = tmp_path / "active-test"
    active.mkdir()
    obj = proposal()
    text = "ARCHITECTURE_DELTA_JSON=" + json.dumps(obj)
    (active / "workers.jsonl").write_text(json.dumps({
        "http_status": 200,
        "text": text,
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "provider": "nvidia",
        "model": "historical",
        "role": "legacy",
        "repo_head_at_prompt": "b" * 40,
    }) + "\n")
    monkeypatch.setattr(forge, "ARTIFACT_ROOT", tmp_path)
    con = memory_db()
    assert forge.ingest_worker_candidates(con) == 1
    assert counter(con, "legacy_candidates_ingested") == 1


def test_fast_launcher_preserves_backpressure_and_installs_typed_bridge():
    text = (ROOT / "tools/run_6000_free_swarm_fast.py").read_text()
    assert "conversion_backpressure.apply()" in text
    assert "model_health.bind_request_observer(fabric)" in text
    assert "typed_delta_bridge.install(fabric.fabric)" in text


def test_safe_forge_installs_typed_ingress_on_real_base_module():
    text = (ROOT / "tools/run_free_evidence_forge_safe_871.py").read_text()
    assert "import run_free_evidence_forge as base" in text
    assert "typed_ingress.install(base)" in text
    assert "base.safe_command = admission.safe_command" in text
    assert "base.run_cmd = _run_cmd_disposable_only" in text
