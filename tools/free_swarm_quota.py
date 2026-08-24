#!/usr/bin/env python3
"""Cross-process FREE_ONLY provider gate for Clay research swarms.

The gate coordinates concurrency and provider-wide cooldowns in one SQLite file
shared by the main Free Swarm and the research distillery. It does not rotate
credentials to evade provider limits and it never upgrades billing.

External LLM-provider leases are subordinate to canonical typed FREE admission.
Search/research transports remain quota-coordinated but are not silently promoted
into the LLM provider authority.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid
from typing import Iterator

from free_provider_admission import require_provider_admitted_free

DB_PATH = Path(os.getenv("CLAY_FREE_PROVIDER_BUDGET_DB", "/artifacts/clay-entityos-swarm/provider_budget.sqlite3"))
LLM_PROVIDERS = frozenset({"groq", "mistral", "nvidia", "openrouter"})
DEFAULTS = {
    "groq": (12, 0.0),
    "mistral": (6, 0.0),
    "nvidia": (12, 0.0),
    "openrouter": (3, 0.5),
    "tavily": (2, 0.5),
    "exa": (2, 0.5),
    "github": (1, 1.0),
    "arxiv": (1, 3.1),
    "reddit": (1, 1.0),
}


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=20, isolation_level=None)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS provider_state(
          provider TEXT PRIMARY KEY,
          max_inflight INTEGER NOT NULL,
          min_interval_s REAL NOT NULL DEFAULT 0,
          cooldown_until REAL NOT NULL DEFAULT 0,
          last_start REAL NOT NULL DEFAULT 0,
          total_requests INTEGER NOT NULL DEFAULT 0,
          total_success INTEGER NOT NULL DEFAULT 0,
          total_429 INTEGER NOT NULL DEFAULT 0,
          total_errors INTEGER NOT NULL DEFAULT 0,
          last_status TEXT,
          last_observed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS leases(
          lease_id TEXT PRIMARY KEY,
          provider TEXT NOT NULL,
          owner TEXT NOT NULL,
          acquired_at REAL NOT NULL,
          expires_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS leases_provider_idx ON leases(provider, expires_at);
        CREATE TABLE IF NOT EXISTS observations(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          observed_at TEXT NOT NULL,
          provider TEXT NOT NULL,
          owner TEXT NOT NULL,
          status TEXT,
          retry_after_s REAL,
          remaining_json TEXT
        );
        """
    )
    return con


def ensure_provider(provider: str) -> None:
    cap, interval = DEFAULTS.get(provider, (1, 0.0))
    with _connect() as con:
        con.execute(
            "INSERT OR IGNORE INTO provider_state(provider,max_inflight,min_interval_s) VALUES(?,?,?)",
            (provider, cap, interval),
        )


def _require_llm_admission(provider: str) -> None:
    if provider in LLM_PROVIDERS:
        require_provider_admitted_free(provider)


def acquire(provider: str, owner: str, timeout_s: float = 60.0, lease_s: float = 300.0) -> str:
    # This runs before a quota lease is minted and before the caller can proceed to
    # provider network I/O. UNKNOWN/PAID/SUBSCRIPTION/stale authority fails closed.
    _require_llm_admission(provider)
    ensure_provider(provider)
    deadline = time.monotonic() + max(0.5, timeout_s)
    while time.monotonic() < deadline:
        now = time.time()
        con = _connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute("DELETE FROM leases WHERE expires_at <= ?", (now,))
            row = con.execute(
                "SELECT max_inflight,min_interval_s,cooldown_until,last_start FROM provider_state WHERE provider=?",
                (provider,),
            ).fetchone()
            cap, interval, cooldown, last_start = row
            active = con.execute("SELECT COUNT(*) FROM leases WHERE provider=?", (provider,)).fetchone()[0]
            if now >= float(cooldown) and active < int(cap) and now - float(last_start) >= float(interval):
                lease_id = uuid.uuid4().hex
                con.execute(
                    "INSERT INTO leases(lease_id,provider,owner,acquired_at,expires_at) VALUES(?,?,?,?,?)",
                    (lease_id, provider, owner, now, now + lease_s),
                )
                con.execute(
                    "UPDATE provider_state SET last_start=?, total_requests=total_requests+1, last_observed_at=? WHERE provider=?",
                    (now, dt.datetime.now(dt.timezone.utc).isoformat(), provider),
                )
                con.execute("COMMIT")
                return lease_id
            con.execute("ROLLBACK")
        finally:
            con.close()
        time.sleep(0.15)
    raise TimeoutError(f"shared provider gate timeout: {provider}")


def release(lease_id: str) -> None:
    with _connect() as con:
        con.execute("DELETE FROM leases WHERE lease_id=?", (lease_id,))


def observe(provider: str, owner: str, status: int | str | None, headers: dict[str, str] | None = None,
            retry_after_s: float | None = None) -> None:
    ensure_provider(provider)
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    if retry_after_s is None:
        raw = headers.get("retry-after")
        try:
            retry_after_s = float(raw) if raw is not None else None
        except ValueError:
            retry_after_s = None
    status_s = str(status) if status is not None else "UNKNOWN"
    now = time.time()
    success = status_s.isdigit() and 200 <= int(status_s) < 300
    rate = status_s == "429"
    error = not success and not rate
    remaining = {k: v for k, v in headers.items() if k.startswith("x-ratelimit-") or "remaining" in k or "reset" in k}
    with _connect() as con:
        if rate:
            cooldown = now + max(1.0, float(retry_after_s or 10.0))
            con.execute("UPDATE provider_state SET cooldown_until=MAX(cooldown_until,?), total_429=total_429+1,last_status=?,last_observed_at=? WHERE provider=?",
                        (cooldown, status_s, dt.datetime.now(dt.timezone.utc).isoformat(), provider))
        elif success:
            con.execute("UPDATE provider_state SET total_success=total_success+1,last_status=?,last_observed_at=? WHERE provider=?",
                        (status_s, dt.datetime.now(dt.timezone.utc).isoformat(), provider))
        else:
            con.execute("UPDATE provider_state SET total_errors=total_errors+1,last_status=?,last_observed_at=? WHERE provider=?",
                        (status_s, dt.datetime.now(dt.timezone.utc).isoformat(), provider))
        con.execute(
            "INSERT INTO observations(observed_at,provider,owner,status,retry_after_s,remaining_json) VALUES(?,?,?,?,?,?)",
            (dt.datetime.now(dt.timezone.utc).isoformat(), provider, owner, status_s, retry_after_s,
             json.dumps(remaining, sort_keys=True, separators=(",", ":"))),
        )
        con.execute("DELETE FROM observations WHERE id NOT IN (SELECT id FROM observations ORDER BY id DESC LIMIT 5000)")


@contextlib.contextmanager
def slot(provider: str, owner: str, timeout_s: float = 60.0, lease_s: float = 300.0) -> Iterator[str]:
    lease = acquire(provider, owner, timeout_s=timeout_s, lease_s=lease_s)
    try:
        yield lease
    finally:
        release(lease)


def snapshot() -> dict:
    if not DB_PATH.exists():
        return {"schema": "CLAY_SHARED_PROVIDER_BUDGET/v1", "providers": {}}
    con = _connect()
    try:
        now = time.time()
        con.execute("DELETE FROM leases WHERE expires_at <= ?", (now,))
        rows = con.execute("SELECT provider,max_inflight,min_interval_s,cooldown_until,total_requests,total_success,total_429,total_errors,last_status,last_observed_at FROM provider_state ORDER BY provider").fetchall()
        out = {}
        for row in rows:
            provider = row[0]
            active = con.execute("SELECT COUNT(*) FROM leases WHERE provider=?", (provider,)).fetchone()[0]
            out[provider] = {
                "max_inflight": row[1], "active_leases": active, "min_interval_s": row[2],
                "cooldown_seconds": max(0.0, float(row[3]) - now), "total_requests": row[4],
                "total_success": row[5], "total_429": row[6], "total_errors": row[7],
                "last_status": row[8], "last_observed_at": row[9],
            }
        return {"schema": "CLAY_SHARED_PROVIDER_BUDGET/v1", "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "providers": out}
    finally:
        con.close()


if __name__ == "__main__":
    print(json.dumps(snapshot(), indent=2, ensure_ascii=False))
