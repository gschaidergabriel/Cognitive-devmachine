#!/usr/bin/env python3
"""Fail-closed exhaustiveness semantics for historical Free-Swarm extraction.

Supervisor 8.78 requires the historical corpus to be re-evaluated rather than merely
cursor-scanned. A chunk therefore must not become SATURATED just because one later
extraction pass produced zero novel candidates. Saturation requires two consecutive
zero-novel passes whose batch envelopes explicitly assert exhaustive=true.

This module is a small successor patch installed into the shared historical-backfill
module by both the producer scheduler and the backlog-first Forge. It preserves the
single Forge SQLite authority, the pre-existing exact chunk/source/next-pass causal
binding, and makes no provider/model/network call itself.
"""
from __future__ import annotations

from typing import Any

MIN_EXHAUSTIVE_ZERO_CONFIRMATIONS = 2
MAX_EXHAUSTIVE_PASSES = 64


def install(backfill: Any) -> None:
    """Install conservative extraction completion semantics into *backfill*.

    The original 3-pass ceiling could close a 14k-character chunk after at most a
    handful of bounded outputs. Keep a finite safety ceiling, but make it large
    enough for repeated <=8-delta passes and require an explicit exhaustive signal
    before any zero-novel pass counts toward saturation.

    Crucially, this successor must retain the original `_batch_binding` authority:
    a model-provided chunk id, source-event id or extraction pass is input, not
    authority. Foreign/stale/future envelopes and oversized/non-list batches do not
    advance counters or saturation state.
    """
    backfill.MAX_PASSES = max(
        int(getattr(backfill, "MAX_PASSES", 0) or 0), MAX_EXHAUSTIVE_PASSES
    )

    def record_batch_progress(con, envelope: dict[str, Any], novel_count: int) -> None:
        binding = backfill._batch_binding(con, envelope)
        values = envelope.get("deltas")
        max_batch = int(getattr(backfill, "MAX_BATCH_DELTAS", 0) or 0)
        if (
            binding is None
            or not isinstance(values, list)
            or max_batch <= 0
            or len(values) > max_batch
        ):
            return

        chunk_id, _, passes = binding
        row = con.execute(
            "SELECT consecutive_zero_novel FROM historical_chunks WHERE chunk_id=?",
            (chunk_id,),
        ).fetchone()
        if not row:
            return

        explicitly_exhaustive = envelope.get("exhaustive") is True
        zero = (
            int(row[0] or 0) + 1
            if explicitly_exhaustive and int(novel_count) == 0
            else 0
        )

        state = "PENDING_EXTRACTION"
        if zero >= MIN_EXHAUSTIVE_ZERO_CONFIRMATIONS:
            state = "SATURATED"
        elif passes >= int(backfill.MAX_PASSES):
            # A bounded ceiling is not semantic saturation. Preserve this as a
            # visible measured stall instead of silently converting it to PASS.
            state = "MAX_PASSES_REACHED"

        con.execute(
            "UPDATE historical_chunks SET extraction_passes=?,consecutive_zero_novel=?,"
            "last_novel_count=?,last_extracted_at=?,state=? WHERE chunk_id=?",
            (passes, zero, int(novel_count), backfill.now(), state, chunk_id),
        )

    backfill._record_batch_progress = record_batch_progress
