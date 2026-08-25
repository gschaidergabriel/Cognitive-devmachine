#!/usr/bin/env python3
from __future__ import annotations
import sqlite3

def reconcile_candidate_source_counts(con: sqlite3.Connection) -> int:
    expected = {
        str(candidate_hash): int(source_events)
        for candidate_hash, source_events in con.execute(
            "SELECT candidate_hash,COUNT(DISTINCT source_event_id) FROM candidate_sources GROUP BY candidate_hash"
        )
    }
    changed = 0
    for candidate_hash, source_events in expected.items():
        row = con.execute(
            "SELECT COALESCE(source_count,0) FROM candidates WHERE candidate_hash=?",
            (candidate_hash,),
        ).fetchone()
        if row is None or int(row[0] or 0) == source_events:
            continue
        con.execute(
            "UPDATE candidates SET source_count=? WHERE candidate_hash=?",
            (source_events, candidate_hash),
        )
        changed += 1
    if changed:
        con.commit()
    return changed
