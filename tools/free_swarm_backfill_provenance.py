#!/usr/bin/env python3
"""Deterministic provenance reconciliation for historical Free-Swarm backfill.

`candidates.source_count` is a scheduling hint, not evidence authority. It must track
unique historical source executions and must not increase merely because the same
worker output is replayed, re-read, or appears through multiple chunks/extraction
passes. The canonical provenance remains `candidate_sources`.
"""
from __future__ import annotations

import sqlite3


def reconcile_candidate_source_counts(con: sqlite3.Connection) -> int:
    """Set source_count to COUNT(DISTINCT source_event_id) for linked candidates.

    Returns the number of candidate rows whose stored count changed. Candidates with
    no `candidate_sources` rows are intentionally left untouched so legacy Forge rows
    are not silently reinterpreted as having zero provenance.
    """
    expected = {
        str(candidate_hash): int(source_events)
        for candidate_hash, source_events in con.execute(
            "SELECT candidate_hash,COUNT(DISTINCT source_event_id) "
            "FROM candidate_sources GROUP BY candidate_hash"
        )
    }
    changed = 0
    for candidate_hash, source_events in expected.items():
        row = con.execute(
            "SELECT COALESCE(source_count,0) FROM candidates WHERE candidate_hash=?",
            (candidate_hash,),
        ).fetchone()
        if row is None:
            continue
        if int(row[0] or 0) == source_events:
            continue
        con.execute(
            "UPDATE candidates SET source_count=? WHERE candidate_hash=?",
            (source_events, candidate_hash),
        )
        changed += 1
    if changed:
        con.commit()
    return changed
