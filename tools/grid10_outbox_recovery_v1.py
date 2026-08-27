#!/usr/bin/env python3
"""Crash-recovery helper for GRID10 coordinator outbox.

Problem closed by this helper:
`Fabric.coordinator_drain_and_commit()` currently performs the S1/admitted_results
commit and `outbox.consumed=1` in two separate SQLite transactions. If a coordinator
is killed after the first transaction commits but before the second, the packet is
already admitted exactly once but remains pending forever; the replacement coordinator
then sees DUPLICATE_RESULT_REJECTED on every retry.

This helper provides deterministic recovery without granting ordinary nodes S1 write
authority. It only marks an outbox packet consumed when the same packet digest already
exists in `admitted_results` with the same scope. No S1 scope content, epoch, truth or
effect state is changed.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from grid10_fabric import connect

SCHEMA = "GRID10_OUTBOX_RECOVERY/v1"


def reconcile_admitted_outbox(path: Path, *, scope: str | None = None) -> dict[str, Any]:
    con = connect(path)
    repaired: list[str] = []
    conflicts: list[str] = []
    try:
        con.execute("BEGIN IMMEDIATE")
        sql = (
            "SELECT o.packet_digest,o.scope,o.consumed,a.scope AS admitted_scope "
            "FROM outbox o JOIN admitted_results a ON a.result_digest=o.packet_digest "
            "WHERE o.consumed=0"
        )
        params: tuple[Any, ...] = ()
        if scope is not None:
            sql += " AND o.scope=?"
            params = (scope,)
        rows = con.execute(sql, params).fetchall()
        for row in rows:
            digest = str(row["packet_digest"])
            if str(row["scope"]) != str(row["admitted_scope"]):
                conflicts.append(digest)
                continue
            con.execute("UPDATE outbox SET consumed=1 WHERE packet_digest=? AND consumed=0", (digest,))
            repaired.append(digest)
        if conflicts:
            con.execute("ROLLBACK")
            return {
                "schema": SCHEMA,
                "pass": False,
                "repaired": [],
                "conflicts": conflicts,
                "canonical_truth": False,
                "effect_authority": False,
                "s1_epoch_changed": False,
            }
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()
    return {
        "schema": SCHEMA,
        "pass": True,
        "repaired": repaired,
        "conflicts": [],
        "canonical_truth": False,
        "effect_authority": False,
        "s1_epoch_changed": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("db", type=Path)
    ap.add_argument("--scope")
    args = ap.parse_args()
    result = reconcile_admitted_outbox(args.db, scope=args.scope)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
