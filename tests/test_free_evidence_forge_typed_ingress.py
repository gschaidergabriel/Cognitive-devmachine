from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_free_evidence_forge as forge  # noqa: E402
from free_swarm_delta_ingress import CANDIDATE_SCHEMA, canonical_json  # noqa: E402


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


def db():
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE candidates(
          candidate_hash TEXT PRIMARY KEY, delta_id TEXT, provider TEXT, model TEXT, role TEXT,
          worker_sha TEXT, proposal_json TEXT NOT NULL, ready INTEGER NOT NULL DEFAULT 0,
          state TEXT NOT NULL DEFAULT 'NEW', ingested_at TEXT NOT NULL, evaluated_at TEXT,
          last_reason TEXT
        );
        CREATE TABLE counters(key TEXT PRIMARY KEY,value REAL NOT NULL DEFAULT 0);
        """
    )
    return con


def sidecar(obj, worker_sha="a" * 64):
    raw = canonical_json(obj)
    return {
        "schema": CANDIDATE_SCHEMA,
        "provider": "nvidia",
        "model": "model",
        "role": "hcu_grid10",
        "worker_text_sha256": worker_sha,
        "proposal_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "ready_for_forge": bool(obj["ready_for_forge"]),
        "proposal": obj,
    }


def test_forge_consumes_typed_sidecar_without_model_text_reparse(tmp_path, monkeypatch):
    active = tmp_path / "active-test"
    active.mkdir()
    row = sidecar(proposal())
    (active / "architecture_deltas.jsonl").write_text(json.dumps(row) + "\n")
    (active / "workers.jsonl").write_text(json.dumps({
        "http_status": 200,
        "text": "no architecture marker here",
        "text_sha256": row["worker_text_sha256"],
        "delta_ingress": {
            "valid": True,
            "proposal_sha256": row["proposal_sha256"],
        },
    }) + "\n")
    monkeypatch.setattr(forge.legacy, "ARTIFACT_ROOT", tmp_path)
    con = db()
    assert forge.ingest_worker_candidates(con) == 1
    got = con.execute("SELECT ready,provider FROM candidates").fetchone()
    assert got == (1, "nvidia")


def test_hash_tamper_is_rejected_and_typed_row_never_falls_back_to_prose(tmp_path, monkeypatch):
    active = tmp_path / "active-test"
    active.mkdir()
    obj = proposal()
    row = sidecar(obj)
    row["proposal_sha256"] = "0" * 64
    (active / "architecture_deltas.jsonl").write_text(json.dumps(row) + "\n")
    raw_model_text = "ARCHITECTURE_DELTA_JSON=" + json.dumps(obj)
    (active / "workers.jsonl").write_text(json.dumps({
        "http_status": 200,
        "text": raw_model_text,
        "text_sha256": row["worker_text_sha256"],
        "delta_ingress": {
            "valid": True,
            "proposal_sha256": row["proposal_sha256"],
        },
    }) + "\n")
    monkeypatch.setattr(forge.legacy, "ARTIFACT_ROOT", tmp_path)
    con = db()
    assert forge.ingest_worker_candidates(con) == 0
    assert con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 0
    assert con.execute("SELECT value FROM counters WHERE key='typed_candidates_rejected'").fetchone()[0] >= 1
