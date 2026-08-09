#!/usr/bin/env python3
"""Deterministic mechanism probe for H-WP-02 idempotency pre-lock race.

This is a small standalone reproduction of the transaction ordering currently visible
in the H1 reference state-ledger implementation: idempotency lookup before
BEGIN IMMEDIATE, then insert without a second lookup after lock acquisition.

Evidence boundary: this probe demonstrates the SQLite race mechanism; it is not itself
a project-host execution of the full H1 StateLedger module.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile


def new_db() -> str:
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
    path = f.name
    f.close()
    c = sqlite3.connect(path)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute(
        "CREATE TABLE events("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "event_id TEXT UNIQUE NOT NULL,"
        "idem TEXT UNIQUE NOT NULL)"
    )
    c.commit()
    c.close()
    return path


def vulnerable_interleaving() -> dict:
    path = new_db()
    a = sqlite3.connect(path, isolation_level=None)
    b = sqlite3.connect(path, isolation_level=None)
    try:
        pre_a = a.execute("SELECT event_id FROM events WHERE idem=?", ("same",)).fetchone()
        pre_b = b.execute("SELECT event_id FROM events WHERE idem=?", ("same",)).fetchone()

        a.execute("BEGIN IMMEDIATE")
        a.execute("INSERT INTO events(event_id,idem) VALUES(?,?)", ("e1", "same"))
        a.execute("COMMIT")

        second = None
        try:
            b.execute("BEGIN IMMEDIATE")
            b.execute("INSERT INTO events(event_id,idem) VALUES(?,?)", ("e1", "same"))
            b.execute("COMMIT")
            second = {"status": "UNEXPECTED_COMMIT"}
        except Exception as exc:  # exact failure class is part of the probe output
            try:
                b.execute("ROLLBACK")
            except Exception:
                pass
            second = {"status": "ERROR", "type": type(exc).__name__, "detail": str(exc)}

        rows = sqlite3.connect(path).execute("SELECT event_id,idem FROM events").fetchall()
        return {
            "both_preflight_missed": pre_a is None and pre_b is None,
            "second": second,
            "rows": rows,
        }
    finally:
        a.close()
        b.close()
        os.unlink(path)


def guarded_interleaving() -> dict:
    path = new_db()
    a = sqlite3.connect(path, isolation_level=None)
    b = sqlite3.connect(path, isolation_level=None)
    try:
        assert a.execute("SELECT 1 FROM events WHERE idem=?", ("same",)).fetchone() is None
        assert b.execute("SELECT 1 FROM events WHERE idem=?", ("same",)).fetchone() is None

        a.execute("BEGIN IMMEDIATE")
        a.execute("INSERT INTO events(event_id,idem) VALUES(?,?)", ("e1", "same"))
        a.execute("COMMIT")

        b.execute("BEGIN IMMEDIATE")
        inside = b.execute("SELECT event_id FROM events WHERE idem=?", ("same",)).fetchone()
        if inside:
            b.execute("ROLLBACK")
            second = {"status": "IDEMPOTENT_REPLAY", "event_id": inside[0]}
        else:
            b.execute("INSERT INTO events(event_id,idem) VALUES(?,?)", ("e1", "same"))
            b.execute("COMMIT")
            second = {"status": "COMMITTED"}

        rows = sqlite3.connect(path).execute("SELECT event_id,idem FROM events").fetchall()
        return {"second": second, "rows": rows}
    finally:
        a.close()
        b.close()
        os.unlink(path)


def main() -> None:
    vulnerable = vulnerable_interleaving()
    guarded = guarded_interleaving()
    passed = (
        vulnerable["both_preflight_missed"]
        and vulnerable["second"].get("type") == "IntegrityError"
        and guarded["second"].get("status") == "IDEMPOTENT_REPLAY"
        and len(vulnerable["rows"]) == 1
        and len(guarded["rows"]) == 1
    )
    print(json.dumps({"probe_pass": passed, "vulnerable": vulnerable, "guarded": guarded}, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
