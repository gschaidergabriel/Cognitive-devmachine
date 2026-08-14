from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import research_entity.runtime.ingest_frank_bug_feedback as ingest


def test_valid_frank_bug_becomes_one_ready_clay_work_item(tmp_path, monkeypatch):
    clay = tmp_path / "clay"
    frank = tmp_path / "frank"
    runtime = clay / "research_entity/runtime"
    state = clay / "research_entity/state"
    exports = frank / "exports/clay_pull/bugs"
    runtime.mkdir(parents=True)
    state.mkdir(parents=True)
    exports.mkdir(parents=True)

    (runtime / "RAE_UNIFIEDDB_V9_DYNAMIC_WORK_FABRIC.sql").write_text(
        """
        CREATE TABLE IF NOT EXISTS clay_work_items(work_id TEXT PRIMARY KEY,goal_ref TEXT,origin_class TEXT,created_by TEXT,created_at TEXT,terminal_status TEXT,terminal_at TEXT);
        CREATE TABLE IF NOT EXISTS clay_work_spec_revisions(work_id TEXT,spec_rev INTEGER,parent_rev INTEGER,title TEXT,work_clay TEXT,reason_clay TEXT,completion_clay TEXT,evidence_need_clay TEXT,executor_policy_clay TEXT,required_capabilities_clay TEXT,write_scope_clay TEXT,dependency_clay TEXT,invalidation_clay TEXT,base_priority REAL,expected_impact REAL,urgency REAL,information_gain REAL,status TEXT,source_ref TEXT,created_by TEXT,created_at TEXT,PRIMARY KEY(work_id,spec_rev));
        """,
        encoding="utf-8",
    )
    source_schema = Path(__file__).resolve().parents[1] / "research_entity/runtime/RAE_UNIFIEDDB_V10_FRANK_BUG_FEEDBACK.sql"
    (runtime / "RAE_UNIFIEDDB_V10_FRANK_BUG_FEEDBACK.sql").write_text(source_schema.read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setattr(ingest, "ROOT", clay)
    monkeypatch.setattr(ingest, "DB", state / "RAE_UNIFIED.sqlite")
    monkeypatch.setattr(ingest, "SCHEMA9", runtime / "RAE_UNIFIEDDB_V9_DYNAMIC_WORK_FABRIC.sql")
    monkeypatch.setattr(ingest, "SCHEMA10", runtime / "RAE_UNIFIEDDB_V10_FRANK_BUG_FEEDBACK.sql")

    payload = {
        "schema_version": "1.0",
        "kind": "FRANK_RESEARCH_BUG_REPORT",
        "bug_id": "bug:abc",
        "trigger": "bug",
        "reporter": "Dr. Andreas Unterweger",
        "captured_pair": {"previous_andreas_input": "Q", "previous_frank_output": "A"},
        "provenance": {"session_ref": "s", "source_cycle_id": "c", "semantic_epoch": 3, "source_repo_head": "h", "captured_at": "t"},
        "authority": {"origin": "ANDREAS_EXPLICIT_BUG_TRIGGER", "frank_role": "CAPTURE_AND_EXPORT_ONLY", "research_execution": "SEPARATE_CLAY_RESEARCH_ENTITY_ONLY", "frank_may_modify_own_harness": False},
        "redaction_applied": False,
    }
    payload["payload_hash"] = hashlib.sha256(ingest.canonical_bytes(payload)).hexdigest()
    (exports / "bug_abc.json").write_text(json.dumps(payload), encoding="utf-8")

    first = ingest.ingest(frank)
    second = ingest.ingest(frank)
    assert first[0]["state"] == "INGESTED"
    assert second[0]["state"] == "DUPLICATE"

    db = sqlite3.connect(ingest.DB)
    assert db.execute("SELECT COUNT(*) FROM clay_frank_bug_reports").fetchone()[0] == 1
    assert db.execute("SELECT origin_class FROM clay_work_items").fetchone()[0] == "FRANK_EXPLICIT_BUG_FEEDBACK"
    assert db.execute("SELECT status FROM clay_work_spec_revisions").fetchone()[0] == "READY"
    db.close()
