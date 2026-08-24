from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from distillery_forge_bridge import accepted_evaluation_is_admissible, ingest_forge_acceptances


def schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE questions(
          id TEXT PRIMARY KEY,parent_id TEXT,root_problem TEXT NOT NULL,question TEXT NOT NULL UNIQUE,
          depth INTEGER NOT NULL DEFAULT 0,priority REAL NOT NULL DEFAULT 1.0,status TEXT NOT NULL DEFAULT 'OPEN',
          attempts INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,last_touched TEXT,source_worker_sha TEXT
        );
        CREATE TABLE knowledge_packets(
          id TEXT PRIMARY KEY,question_id TEXT NOT NULL,root_problem TEXT NOT NULL,packet_text TEXT NOT NULL,
          metadata_json TEXT NOT NULL,intrinsic_score REAL NOT NULL,grf_score REAL NOT NULL,project_fit REAL NOT NULL,
          novelty_score REAL NOT NULL,approx_tokens INTEGER NOT NULL,created_at TEXT NOT NULL
        );
        CREATE TABLE counters(key TEXT PRIMARY KEY,value INTEGER NOT NULL DEFAULT 0);
        """
    )


def bump(con: sqlite3.Connection, key: str, delta: int) -> None:
    con.execute(
        "INSERT INTO counters(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=value+excluded.value",
        (key, delta),
    )


def row(**overrides):
    base = {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "status": "accepted",
        "delta_id": "delta-1",
        "worker_sha": "a" * 64,
        "source_repo_head": "1" * 40,
        "evaluation_repo_head": "2" * 40,
        "target_blob_identities": {"tools/x.py": "3" * 40},
        "metric": "test_pass_rate",
        "relative_improvement_pct": 50.0,
        "reproducible_runs": 2,
        "tests_passed": 4,
        "tests_failed": 0,
        "negative_tests_passed": 1,
        "negative_tests_failed": 0,
        "static_checks_passed": 1,
        "static_checks_failed": 0,
        "benchmark_non_regression": True,
        "requires_rebase_to_evaluation_head": True,
    }
    base.update(overrides)
    return base


def test_acceptance_requires_exact_source_and_positive_reproducible_delta():
    assert accepted_evaluation_is_admissible(row()) == (True, "ADMISSIBLE")
    assert accepted_evaluation_is_admissible(row(source_repo_head=""))[1] == "SOURCE_IDENTITY_UNBOUND"
    assert accepted_evaluation_is_admissible(row(reproducible_runs=1))[1] == "INSUFFICIENT_REPRODUCIBILITY"
    assert accepted_evaluation_is_admissible(row(tests_failed=1))[1] == "TEST_FAILURE_PRESENT"
    assert accepted_evaluation_is_admissible(row(relative_improvement_pct=0))[1] == "NO_POSITIVE_DELTA"


def test_bridge_admits_once_and_keeps_fact_credit_zero(tmp_path: Path):
    con = sqlite3.connect(":memory:")
    schema(con)
    path = tmp_path / "architecture_delta_evaluations.jsonl"
    path.write_text(json.dumps(row()) + "\n", encoding="utf-8")
    events = []
    kwargs = dict(
        now_iso=lambda: "2026-08-24T14:30:00+00:00",
        approx_tokens=lambda text: max(1, len(text) // 4),
        bump=bump,
        emit=lambda event, **data: events.append((event, data)),
    )
    first = ingest_forge_acceptances(con, path, **kwargs)
    second = ingest_forge_acceptances(con, path, **kwargs)
    assert first["admitted_packets"] == 1
    assert first["admitted_tokens"] > 0
    assert second["admitted_packets"] == 0
    assert con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0] == 1
    packet_text, metadata_text = con.execute(
        "SELECT packet_text,metadata_json FROM knowledge_packets"
    ).fetchone()
    packet = json.loads(packet_text)
    meta = json.loads(metadata_text)
    assert packet["epistemic_class"] == "EXECUTABLE_DELTA_COMPONENT_EVIDENCE"
    assert packet["fact_credit"] == 0
    assert meta["canonical_truth"] is False
    assert meta["whole_product_credit"] == 0
    counters = dict(con.execute("SELECT key,value FROM counters"))
    assert counters["forge_evidence_packets"] == 1
    assert counters["accepted_dataset_tokens"] == first["admitted_tokens"]
    assert any(name == "forge_evidence_admitted" for name, _ in events)


def test_bridge_fails_closed_on_legacy_accepted_without_source_identity(tmp_path: Path):
    con = sqlite3.connect(":memory:")
    schema(con)
    path = tmp_path / "architecture_delta_evaluations.jsonl"
    path.write_text(json.dumps(row(source_repo_head=None, target_blob_identities={})) + "\n", encoding="utf-8")
    result = ingest_forge_acceptances(
        con,
        path,
        now_iso=lambda: "2026-08-24T14:30:00+00:00",
        approx_tokens=lambda text: max(1, len(text) // 4),
        bump=bump,
    )
    assert result == {"admitted_packets": 0, "admitted_tokens": 0, "skipped_invalid": 1}
    assert con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0] == 0
