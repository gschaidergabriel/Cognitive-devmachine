#!/usr/bin/env python3
"""Crash-injection helper for H-WP-02 state ledger.

Runs in a separate process and intentionally terminates without COMMIT after
crossing selected SQLite transaction boundaries. It is test-only harness code.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path


def crash(db_path: Path, point: str) -> None:
    db = sqlite3.connect(db_path, timeout=8.0, isolation_level=None)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=8000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.execute("BEGIN IMMEDIATE")

    if point in {"AFTER_STATE", "AFTER_EVENT", "AFTER_EPOCH"}:
        db.execute(
            "UPDATE ledger_state SET value_json='999', epistemic_state='CONFLICT' "
            "WHERE domain='world' AND state_key='x'"
        )

    if point in {"AFTER_EVENT", "AFTER_EPOCH"}:
        db.execute(
            """
            INSERT INTO ledger_events(
              event_id,idempotency_key,base_epoch,committed_epoch,event_type,mutations_json,
              provenance_json,previous_event_hash,event_hash,post_root_hash,committed_at,writer_node
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "crash-event", "crash-key", 1, 2, "CRASH_PROBE", "[]", "{}",
                "0" * 64, "1" * 64, "2" * 64, "2026-08-09T10:03:00Z", "crash-probe"
            ),
        )

    if point == "AFTER_EPOCH":
        db.execute(
            """
            INSERT INTO ledger_epochs(epoch,parent_epoch,event_id,root_hash,event_hash,committed_at,writer_node)
            VALUES(?,?,?,?,?,?,?)
            """,
            (2, 1, "crash-event", "2" * 64, "1" * 64, "2026-08-09T10:03:00Z", "crash-probe"),
        )

    # Deliberately bypass Python cleanup/finalizers so SQLite sees abrupt process death.
    os._exit(137)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("db_path", type=Path)
    p.add_argument("point", choices=["AFTER_STATE", "AFTER_EVENT", "AFTER_EPOCH"])
    a = p.parse_args()
    crash(a.db_path, a.point)


if __name__ == "__main__":
    main()
