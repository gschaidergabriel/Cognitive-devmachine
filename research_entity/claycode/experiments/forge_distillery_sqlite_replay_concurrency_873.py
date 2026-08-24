#!/usr/bin/env python3
"""Deterministic SQLite concurrency discriminator for Forge->Distillery replay admission.

This is a database-semantics research reproducer, not EntityOS/HCU runtime evidence.
It compares the current SELECT-before-write admission shape with a write-intent
transaction acquired before replay lookup. It performs no network/provider/model I/O.
"""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import threading


def _init(db: Path) -> None:
    con = sqlite3.connect(db)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute(
            "CREATE TABLE ingest("
            "evaluation_sha256 TEXT PRIMARY KEY, "
            "execution_replay_identity_sha256 TEXT, "
            "measured_evidence_sha256 TEXT, "
            "packet_id TEXT UNIQUE)"
        )
        con.execute(
            "CREATE UNIQUE INDEX replay_uq ON ingest(execution_replay_identity_sha256) "
            "WHERE execution_replay_identity_sha256 IS NOT NULL"
        )
        con.commit()
    finally:
        con.close()


def current_shape() -> dict:
    root = Path(tempfile.mkdtemp(prefix="clay-replay-race-current-"))
    db = root / "race.sqlite3"
    _init(db)
    after_lookup = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def worker(n: int) -> None:
        con = sqlite3.connect(db, timeout=5)
        try:
            con.execute("PRAGMA journal_mode=WAL")
            existing = con.execute(
                "SELECT measured_evidence_sha256 FROM ingest "
                "WHERE evaluation_sha256=? OR execution_replay_identity_sha256=? LIMIT 1",
                (f"eval-{n}", "same-replay"),
            ).fetchone()
            if existing:
                outcome = "DUPLICATE"
            else:
                after_lookup.wait()
                try:
                    con.execute(
                        "INSERT INTO ingest VALUES(?,?,?,?)",
                        (f"eval-{n}", "same-replay", "same-measured", f"packet-{n}"),
                    )
                    con.commit()
                    outcome = "INSERTED"
                except sqlite3.IntegrityError as exc:
                    con.rollback()
                    outcome = f"INTEGRITY_ERROR:{exc}"
        finally:
            con.close()
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=worker, args=(n,)) for n in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    con = sqlite3.connect(db)
    try:
        rows = int(con.execute("SELECT COUNT(*) FROM ingest").fetchone()[0])
    finally:
        con.close()
    return {"outcomes": sorted(outcomes), "durable_rows": rows}


def serialized_shape() -> dict:
    root = Path(tempfile.mkdtemp(prefix="clay-replay-race-serialized-"))
    db = root / "race.sqlite3"
    _init(db)
    start = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def worker(n: int) -> None:
        con = sqlite3.connect(db, timeout=5)
        try:
            start.wait()
            con.execute("BEGIN IMMEDIATE")
            existing = con.execute(
                "SELECT measured_evidence_sha256 FROM ingest "
                "WHERE evaluation_sha256=? OR execution_replay_identity_sha256=? LIMIT 1",
                (f"eval-{n}", "same-replay"),
            ).fetchone()
            if existing:
                outcome = "DUPLICATE"
            else:
                con.execute(
                    "INSERT INTO ingest VALUES(?,?,?,?)",
                    (f"eval-{n}", "same-replay", "same-measured", f"packet-{n}"),
                )
                outcome = "INSERTED"
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=worker, args=(n,)) for n in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    con = sqlite3.connect(db)
    try:
        rows = int(con.execute("SELECT COUNT(*) FROM ingest").fetchone()[0])
    finally:
        con.close()
    return {"outcomes": sorted(outcomes), "durable_rows": rows}


def main() -> int:
    current = current_shape()
    serialized = serialized_shape()
    current_integrity_errors = sum(x.startswith("INTEGRITY_ERROR:") for x in current["outcomes"])
    result = {
        "schema": "CLAY_FORGE_DISTILLERY_SQLITE_REPLAY_CONCURRENCY_DISCRIMINATOR/v1",
        "scope": "GENERIC_SQLITE_WAL_TRANSACTION_SEMANTICS_NOT_ENTITYOS_RUNTIME",
        "current_select_then_insert": current,
        "write_intent_before_lookup": serialized,
        "current_gap_observed": current["durable_rows"] == 1
        and current_integrity_errors == 1
        and current["outcomes"].count("INSERTED") == 1,
        "serialized_control_pass": serialized == {
            "outcomes": ["DUPLICATE", "INSERTED"],
            "durable_rows": 1,
        },
        "runtime_credit": 0,
        "jspace_model_credit": 0,
        "training_credit": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["current_gap_observed"] and result["serialized_control_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
