from __future__ import annotations

import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable

GIB = 1024 ** 3
MIB = 1024 ** 2
SCHEMA_VERSION = "1.0"
TOTAL_BUDGET_DEFAULT = 10 * GIB
MAIN_BUDGET_DEFAULT = 9 * GIB
WAL_LIMIT_DEFAULT = 256 * MIB

RETENTION = {
    "DEBUG": 10,
    "INFO": 20,
    "PERFORMANCE": 30,
    "NORMAL": 40,
    "API": 45,
    "TOOL": 50,
    "MODEL": 55,
    "STATE": 70,
    "GWT_CAUSAL": 75,
    "BUILD": 80,
    "RECOVERY": 90,
    "P1": 95,
    "P0": 100,
}
CATEGORY_DEFAULT = {
    "PERFORMANCE": "PERFORMANCE",
    "API": "API",
    "TOOL": "TOOL",
    "MODEL": "MODEL",
    "STATE_DELTA": "STATE",
    "GWT": "GWT_CAUSAL",
    "BUILD": "BUILD",
    "RECOVERY": "RECOVERY",
    "SECURITY": "P1",
    "ERROR": "P1",
}
SECRET_PARTS = ("authorization", "token", "password", "passwd", "secret", "api_key", "apikey", "private_key", "cookie", "bearer")


class CapacityError(RuntimeError):
    pass


def telemetry_dir() -> Path:
    p = Path(os.getenv("FRANK_TELEMETRY_DIR", "/srv/frank-telemetry"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_path() -> Path:
    return Path(os.getenv("FRANK_TELEMETRY_DB", str(telemetry_dir() / "frank_telemetry.sqlite3")))


def total_budget() -> int:
    return int(os.getenv("FRANK_TELEMETRY_TOTAL_BUDGET_BYTES", str(TOTAL_BUDGET_DEFAULT)))


def main_budget() -> int:
    configured = int(os.getenv("FRANK_TELEMETRY_MAIN_BUDGET_BYTES", str(MAIN_BUDGET_DEFAULT)))
    return min(configured, int(total_budget() * 0.90))


def wal_limit() -> int:
    configured = int(os.getenv("FRANK_TELEMETRY_WAL_LIMIT_BYTES", str(WAL_LIMIT_DEFAULT)))
    return min(configured, int(total_budget() * 0.03))


def pressure_limit() -> int:
    return int(total_budget() * float(os.getenv("FRANK_TELEMETRY_PRESSURE_FRACTION", "0.85")))


def cleanup_target() -> int:
    return int(total_budget() * float(os.getenv("FRANK_TELEMETRY_CLEANUP_TARGET_FRACTION", "0.72")))


def storage_usage() -> dict[str, Any]:
    base = db_path()
    files = [base, Path(str(base) + "-wal"), Path(str(base) + "-shm")]
    rows, total = [], 0
    for p in files:
        size = p.stat().st_size if p.exists() else 0
        rows.append({"path": str(p), "size": size})
        total += size
    return {"bytes": total, "budget_bytes": total_budget(), "pressure_bytes": pressure_limit(), "fraction": total / max(1, total_budget()), "files": rows}


def _connect() -> sqlite3.Connection:
    p = db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    conn = sqlite3.connect(p, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    if new:
        conn.execute("PRAGMA page_size=4096")
        conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute(f"PRAGMA journal_size_limit={wal_limit()}")
    conn.execute("PRAGMA wal_autocheckpoint=2048")
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        page_size = int(conn.execute("PRAGMA page_size").fetchone()[0])
        conn.execute(f"PRAGMA max_page_count={max(1024, main_budget() // page_size)}")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events(
              id INTEGER PRIMARY KEY,
              event_id TEXT NOT NULL UNIQUE,
              event_ts REAL NOT NULL,
              ingest_ts REAL NOT NULL,
              module TEXT NOT NULL,
              category TEXT NOT NULL,
              event_type TEXT,
              severity TEXT NOT NULL,
              retention_class TEXT NOT NULL,
              retention_rank INTEGER NOT NULL,
              message TEXT,
              payload_json TEXT NOT NULL DEFAULT '{}',
              correlation_id TEXT,
              episode_id TEXT,
              session_id TEXT,
              conversation_id TEXT,
              request_id TEXT,
              build_id TEXT,
              model_id TEXT,
              model_hash TEXT,
              mmproj_hash TEXT,
              provenance TEXT,
              state_key TEXT,
              entity_id TEXT,
              prev_state_hash TEXT,
              next_state_hash TEXT,
              parent_event_id TEXT,
              tags_json TEXT NOT NULL DEFAULT '[]',
              latency_ms REAL,
              rss_bytes INTEGER,
              gpu_mem_bytes INTEGER,
              schema_version TEXT NOT NULL,
              CHECK(json_valid(payload_json)),
              CHECK(json_valid(tags_json))
            );
            CREATE INDEX IF NOT EXISTS ix_event_time ON events(event_ts);
            CREATE INDEX IF NOT EXISTS ix_module_time ON events(module,event_ts);
            CREATE INDEX IF NOT EXISTS ix_category_time ON events(category,event_ts);
            CREATE INDEX IF NOT EXISTS ix_retention_time ON events(retention_rank,event_ts);
            CREATE INDEX IF NOT EXISTS ix_corr_time ON events(correlation_id,event_ts);
            CREATE INDEX IF NOT EXISTS ix_episode_time ON events(episode_id,event_ts);
            CREATE INDEX IF NOT EXISTS ix_session_time ON events(session_id,event_ts);
            CREATE INDEX IF NOT EXISTS ix_build_time ON events(build_id,event_ts);
            CREATE INDEX IF NOT EXISTS ix_state_time ON events(state_key,entity_id,event_ts);
            CREATE INDEX IF NOT EXISTS ix_parent ON events(parent_event_id);
            CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(message,payload_json,module,category,event_type,tags_json,content='events',content_rowid='id');
            CREATE TRIGGER IF NOT EXISTS events_ai AFTER INSERT ON events BEGIN
              INSERT INTO events_fts(rowid,message,payload_json,module,category,event_type,tags_json)
              VALUES(new.id,new.message,new.payload_json,new.module,new.category,new.event_type,new.tags_json);
            END;
            CREATE TRIGGER IF NOT EXISTS events_ad AFTER DELETE ON events BEGIN
              INSERT INTO events_fts(events_fts,rowid,message,payload_json,module,category,event_type,tags_json)
              VALUES('delete',old.id,old.message,old.payload_json,old.module,old.category,old.event_type,old.tags_json);
            END;
            CREATE TABLE IF NOT EXISTS telemetry_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            """
        )
        conn.execute("INSERT OR REPLACE INTO telemetry_meta(key,value) VALUES('schema_version',?)", (SCHEMA_VERSION,))
        conn.execute("INSERT OR REPLACE INTO telemetry_meta(key,value) VALUES('total_budget_bytes',?)", (str(total_budget()),))
    finally:
        conn.close()


def _secret_key(k: str) -> bool:
    low = k.lower().replace("-", "_")
    return any(part in low for part in SECRET_PARTS)


def redact(v: Any, depth: int = 0) -> Any:
    if depth > 12:
        return "[TRUNCATED_DEPTH]"
    if isinstance(v, dict):
        return {str(k): "[REDACTED]" if _secret_key(str(k)) else redact(val, depth + 1) for k, val in v.items()}
    if isinstance(v, list):
        return [redact(x, depth + 1) for x in v[:2048]]
    if isinstance(v, str):
        n = int(os.getenv("FRANK_TELEMETRY_MAX_STRING_CHARS", "32768"))
        return v if len(v) <= n else v[:n] + "...[TRUNCATED]"
    if v is None or isinstance(v, (bool, int, float)):
        return v
    return str(v)


def _s(v: Any, n: int = 256) -> str | None:
    return None if v is None else str(v)[:n]


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    now = time.time()
    category = str(raw.get("category") or "INFO").upper()[:64]
    retention_class = str(raw.get("retention_class") or CATEGORY_DEFAULT.get(category, "NORMAL")).upper()[:32]
    payload = json.dumps(redact(raw.get("payload") or {}), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = [tags]
    tags_json = json.dumps(redact(tags[:256]), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    message = _s(raw.get("message"), 32768)
    size = len(payload.encode()) + len(tags_json.encode()) + len((message or "").encode())
    if size > int(os.getenv("FRANK_TELEMETRY_EVENT_MAX_BYTES", str(256 * 1024))):
        raise ValueError("event too large")
    return {
        "event_id": _s(raw.get("event_id")) or f"evt-{time.time_ns()}-{secrets.token_hex(8)}",
        "event_ts": float(raw.get("event_ts") or raw.get("timestamp") or now),
        "ingest_ts": now,
        "module": _s(raw.get("module") or "unknown", 128),
        "category": category,
        "event_type": _s(raw.get("event_type"), 128),
        "severity": str(raw.get("severity") or "INFO").upper()[:32],
        "retention_class": retention_class,
        "retention_rank": RETENTION.get(retention_class, RETENTION["NORMAL"]),
        "message": message,
        "payload_json": payload,
        "correlation_id": _s(raw.get("correlation_id")),
        "episode_id": _s(raw.get("episode_id")),
        "session_id": _s(raw.get("session_id")),
        "conversation_id": _s(raw.get("conversation_id")),
        "request_id": _s(raw.get("request_id")),
        "build_id": _s(raw.get("build_id")),
        "model_id": _s(raw.get("model_id")),
        "model_hash": _s(raw.get("model_hash")),
        "mmproj_hash": _s(raw.get("mmproj_hash")),
        "provenance": _s(raw.get("provenance")),
        "state_key": _s(raw.get("state_key")),
        "entity_id": _s(raw.get("entity_id")),
        "prev_state_hash": _s(raw.get("prev_state_hash")),
        "next_state_hash": _s(raw.get("next_state_hash")),
        "parent_event_id": _s(raw.get("parent_event_id")),
        "tags_json": tags_json,
        "latency_ms": float(raw["latency_ms"]) if raw.get("latency_ms") is not None else None,
        "rss_bytes": int(raw["rss_bytes"]) if raw.get("rss_bytes") is not None else None,
        "gpu_mem_bytes": int(raw["gpu_mem_bytes"]) if raw.get("gpu_mem_bytes") is not None else None,
        "schema_version": _s(raw.get("schema_version") or SCHEMA_VERSION, 32),
    }


def maintain(force: bool = False) -> dict[str, Any]:
    init_db()
    before = storage_usage()
    if not force and before["bytes"] < pressure_limit():
        return {"deleted": 0, "before": before, "after": before}
    conn = _connect()
    deleted = 0
    try:
        for max_rank in (20, 30, 40, 50, 55, 70, 80):
            while storage_usage()["bytes"] > cleanup_target():
                ids = [r[0] for r in conn.execute("SELECT id FROM events WHERE retention_rank<=? ORDER BY event_ts LIMIT 5000", (max_rank,)).fetchall()]
                if not ids:
                    break
                conn.execute("BEGIN IMMEDIATE")
                conn.executemany("DELETE FROM events WHERE id=?", [(x,) for x in ids])
                conn.execute("COMMIT")
                deleted += len(ids)
                conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            if storage_usage()["bytes"] <= cleanup_target():
                break
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("PRAGMA incremental_vacuum(8192)")
    finally:
        conn.close()
    after = storage_usage()
    if after["bytes"] >= total_budget():
        raise CapacityError("telemetry hard budget reached; high-priority evidence preserved, ingestion must backpressure")
    return {"deleted": deleted, "before": before, "after": after}


def ingest(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    init_db()
    rows = [normalize(e) for e in events]
    if len(rows) > int(os.getenv("FRANK_TELEMETRY_BATCH_MAX", "1000")):
        raise ValueError("batch too large")
    maintain(False)
    cols = list(rows[0].keys()) if rows else []
    sql = f"INSERT OR IGNORE INTO events({','.join(cols)}) VALUES({','.join('?' for _ in cols)})" if rows else ""
    conn = _connect()
    inserted = 0
    try:
        if rows:
            conn.execute("BEGIN IMMEDIATE")
            for row in rows:
                inserted += conn.execute(sql, [row[c] for c in cols]).rowcount
            conn.execute("COMMIT")
    except sqlite3.OperationalError as exc:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        if "full" in str(exc).lower():
            raise CapacityError("SQLite max_page_count reached") from exc
        raise
    finally:
        conn.close()
    return {"accepted": len(rows), "inserted": inserted, "duplicates": len(rows) - inserted, "storage": storage_usage()}


def _row(r: sqlite3.Row, include_payload: bool) -> dict[str, Any]:
    d = dict(r)
    if include_payload:
        for k in ("payload_json", "tags_json"):
            if k in d:
                try:
                    d[k[:-5] if k.endswith("_json") else k] = json.loads(d[k])
                except Exception:
                    pass
    d.pop("payload_json", None) if not include_payload else None
    d.pop("tags_json", None) if not include_payload else None
    return d


def query(
    *,
    start_ts: float | None = None,
    end_ts: float | None = None,
    module: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    correlation_id: str | None = None,
    episode_id: str | None = None,
    session_id: str | None = None,
    build_id: str | None = None,
    state_key: str | None = None,
    entity_id: str | None = None,
    fts: str | None = None,
    json_path: str | None = None,
    json_equals: Any | None = None,
    min_latency_ms: float | None = None,
    min_retention_rank: int | None = None,
    limit: int = 200,
    include_payload: bool = True,
) -> list[dict[str, Any]]:
    init_db()
    limit = max(1, min(limit, 2000))
    where, args = [], []
    fields = {
        "module": module, "category": category, "severity": severity, "correlation_id": correlation_id,
        "episode_id": episode_id, "session_id": session_id, "build_id": build_id,
        "state_key": state_key, "entity_id": entity_id,
    }
    for k, v in fields.items():
        if v is not None:
            where.append(f"e.{k}=?")
            args.append(v)
    if start_ts is not None:
        where.append("e.event_ts>=?"); args.append(start_ts)
    if end_ts is not None:
        where.append("e.event_ts<=?"); args.append(end_ts)
    if min_latency_ms is not None:
        where.append("e.latency_ms>=?"); args.append(min_latency_ms)
    if min_retention_rank is not None:
        where.append("e.retention_rank>=?"); args.append(min_retention_rank)
    join = ""
    if fts:
        join = " JOIN events_fts f ON f.rowid=e.id "
        where.append("events_fts MATCH ?")
        args.append(fts)
    if json_path is not None:
        if not json_path.startswith("$") or len(json_path) > 256:
            raise ValueError("json_path must be a bounded SQLite JSON path starting with $")
        where.append("json_extract(e.payload_json,?) IS ?")
        args.extend([json_path, json_equals])
    sql = "SELECT e.* FROM events e" + join
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY e.event_ts DESC,e.id DESC LIMIT ?"
    args.append(limit)
    conn = _connect()
    try:
        return [_row(r, include_payload) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def state_timeline(state_key: str, entity_id: str | None = None, episode_id: str | None = None, start_ts: float | None = None, end_ts: float | None = None, limit: int = 1000) -> list[dict[str, Any]]:
    rows = query(start_ts=start_ts, end_ts=end_ts, category="STATE_DELTA", state_key=state_key, entity_id=entity_id, episode_id=episode_id, limit=limit, include_payload=True)
    return sorted(rows, key=lambda r: (r["event_ts"], r["id"]))


def stats() -> dict[str, Any]:
    init_db()
    conn = _connect()
    try:
        total = int(conn.execute("SELECT COUNT(*) FROM events").fetchone()[0])
        by_module = [dict(r) for r in conn.execute("SELECT module,COUNT(*) count FROM events GROUP BY module ORDER BY count DESC LIMIT 100")]
        by_category = [dict(r) for r in conn.execute("SELECT category,COUNT(*) count FROM events GROUP BY category ORDER BY count DESC LIMIT 100")]
        bounds = dict(conn.execute("SELECT MIN(event_ts) min_ts,MAX(event_ts) max_ts FROM events").fetchone())
        return {"events": total, "time_bounds": bounds, "by_module": by_module, "by_category": by_category, "storage": storage_usage()}
    finally:
        conn.close()
