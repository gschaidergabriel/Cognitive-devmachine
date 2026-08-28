#!/usr/bin/env python3
"""Deterministic provenance reconciliation for historical Free-Swarm backfill.

`candidates.source_count` is a scheduling hint, not evidence authority. It must track
unique historical source executions and must not increase merely because the same
worker output is replayed, re-read, or appears through multiple chunks/extraction
passes. The canonical provenance remains `candidate_sources`.

Reconciliation is intentionally fail-closed until historical replay persists an
absolute line checkpoint. Older offset-only scanners can assign a different
`source_event_id` to the same physical JSONL row when replay is partitioned across
multiple resumes; counting those IDs as distinct would manufacture scheduling weight.
"""
from __future__ import annotations

import sqlite3


def replay_stable_source_event_identity_available(con: sqlite3.Connection) -> bool:
    """Return whether the DB schema proves cumulative line checkpoints are present.

    `backfill_files.line_no` is the additive schema marker introduced by the
    replay-stable absolute-line checkpoint. Absence of the table or column means the
    current database cannot prove that `source_event_id` is replay-partition invariant.
    """
    table = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='backfill_files'"
    ).fetchone()
    if table is None:
        return False
    columns = {str(row[1]) for row in con.execute("PRAGMA table_info(backfill_files)")}
    return "line_no" in columns


def _clamp_unstable_source_counts(con: sqlite3.Connection) -> int:
    """Conservatively remove unprovable multi-source scheduling weight.

    Until replay-partition-invariant event identity exists, any count above one may be
    an artefact of segmented replay. Candidates with at least one provenance link are
    clamped to the known-safe lower bound of one. Unlinked legacy candidates are left
    untouched because their provenance cannot be reconstructed here.
    """
    before = con.total_changes
    con.execute(
        "UPDATE candidates SET source_count=1 "
        "WHERE COALESCE(source_count,1)<>1 AND EXISTS ("
        "SELECT 1 FROM candidate_sources cs WHERE cs.candidate_hash=candidates.candidate_hash)"
    )
    changed = con.total_changes - before
    if changed:
        con.commit()
    return int(changed)


def reconcile_candidate_source_counts(con: sqlite3.Connection) -> int:
    """Reconcile source counts under the strongest currently provable identity.

    Returns the number of candidate rows whose stored count changed. Before the
    absolute-line checkpoint is admitted, linked candidates are clamped to one so
    partition-sensitive replay identities cannot bias Forge scheduling. Once the
    checkpoint exists, source_count becomes COUNT(DISTINCT source_event_id). Candidates
    with no `candidate_sources` rows are intentionally left untouched.
    """
    if not replay_stable_source_event_identity_available(con):
        return _clamp_unstable_source_counts(con)

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
