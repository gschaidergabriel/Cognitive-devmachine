import json
import sqlite3
from pathlib import Path

from clay_vps_mcp import telemetry, unifieddb_backup


def configure_telemetry(monkeypatch, tmp_path: Path):
    tdir = tmp_path / "telemetry"
    monkeypatch.setenv("FRANK_TELEMETRY_DIR", str(tdir))
    monkeypatch.setenv("FRANK_TELEMETRY_DB", str(tdir / "events.sqlite3"))
    monkeypatch.setenv("FRANK_TELEMETRY_TOTAL_BUDGET_BYTES", str(16 * 1024 * 1024))
    monkeypatch.setenv("FRANK_TELEMETRY_MAIN_BUDGET_BYTES", str(12 * 1024 * 1024))
    monkeypatch.setenv("FRANK_TELEMETRY_WAL_LIMIT_BYTES", str(1024 * 1024))
    return tdir


def test_telemetry_redacts_and_state_timeline_is_surgical(monkeypatch, tmp_path):
    configure_telemetry(monkeypatch, tmp_path)
    telemetry.init_db()
    result = telemetry.ingest([
        {
            "event_id": "e1",
            "event_ts": 10.0,
            "module": "gwt",
            "category": "STATE_DELTA",
            "severity": "INFO",
            "state_key": "workspace.focus",
            "entity_id": "frank",
            "episode_id": "ep-1",
            "prev_state_hash": "a",
            "next_state_hash": "b",
            "message": "focus changed",
            "payload": {"from": "mail", "to": "terminal", "Authorization": "Bearer secret"},
            "tags": ["gwt", "state"],
        },
        {
            "event_id": "e2",
            "event_ts": 11.0,
            "module": "gwt",
            "category": "STATE_DELTA",
            "state_key": "workspace.focus",
            "entity_id": "frank",
            "episode_id": "ep-1",
            "prev_state_hash": "b",
            "next_state_hash": "c",
            "message": "focus changed again",
            "payload": {"to": "browser"},
        },
        {
            "event_id": "other",
            "event_ts": 11.5,
            "module": "retina",
            "category": "PERFORMANCE",
            "message": "frame",
            "payload": {"latency": 4},
        },
    ])
    assert result["inserted"] == 3
    rows = telemetry.state_timeline("workspace.focus", entity_id="frank", episode_id="ep-1")
    assert [r["event_id"] for r in rows] == ["e1", "e2"]
    assert rows[0]["payload"]["Authorization"] == "[REDACTED]"
    fts = telemetry.query(fts="browser", module="gwt")
    assert [r["event_id"] for r in fts] == ["e2"]
    by_json = telemetry.query(json_path="$.to", json_equals="browser")
    assert [r["event_id"] for r in by_json] == ["e2"]


def test_telemetry_database_has_hard_page_limit_below_total_budget(monkeypatch, tmp_path):
    configure_telemetry(monkeypatch, tmp_path)
    telemetry.init_db()
    conn = sqlite3.connect(telemetry.db_path())
    try:
        page_size = conn.execute("PRAGMA page_size").fetchone()[0]
        max_pages = conn.execute("PRAGMA max_page_count").fetchone()[0]
    finally:
        conn.close()
    assert page_size * max_pages <= telemetry.main_budget() + page_size
    assert telemetry.main_budget() + telemetry.wal_limit() < telemetry.total_budget()


def test_unifieddb_online_snapshot_and_recovery_candidate(monkeypatch, tmp_path):
    source = tmp_path / "unified.db"
    conn = sqlite3.connect(source)
    conn.execute("CREATE TABLE state(k TEXT PRIMARY KEY, v TEXT)")
    conn.execute("INSERT INTO state VALUES('focus','terminal')")
    conn.commit()
    conn.close()

    backups = tmp_path / "backups"
    history = tmp_path / "history"
    state = tmp_path / "mcp-state"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    state.mkdir()
    monkeypatch.setenv("FRANK_UNIFIEDDB_BACKUP_ROOT", str(backups))
    monkeypatch.setenv("FRANK_UNIFIEDDB_BACKUP_BUDGET_BYTES", str(64 * 1024 * 1024))
    monkeypatch.setenv("CLAY_HISTORY_REPO", str(history))
    monkeypatch.setenv("CLAY_MCP_STATE_DIR", str(state))
    monkeypatch.setenv("CLAY_MCP_ALLOWED_ROOTS", f"{workspace},{tmp_path}")

    snap = unifieddb_backup.snapshot(source, reason="EXPLICIT", full_check=True)
    assert snap["status"] == "CREATED"
    snapshot_path = Path(snap["snapshot_path"])
    assert snapshot_path.exists()
    assert snap["sqlite"]["ok"] is True
    manifest = json.loads(Path(snap["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["sha256"] == snap["sha256"]

    candidate = tmp_path / "recovered.db"
    receipt = unifieddb_backup.recovery_candidate(snapshot_path, candidate)
    assert receipt["verify"]["ok"] is True
    rc = sqlite3.connect(candidate)
    try:
        assert rc.execute("SELECT v FROM state WHERE k='focus'").fetchone()[0] == "terminal"
    finally:
        rc.close()
