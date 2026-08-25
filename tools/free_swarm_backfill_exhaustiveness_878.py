#!/usr/bin/env python3
"""Fail-closed exhaustiveness semantics for historical Free-Swarm extraction.

A historical chunk must not become SATURATED from a single zero-novel pass or from
an implicit/missing exhaustiveness signal. This patch is installed into the shared
historical-backfill module by both the producer scheduler and backlog-first Forge,
so there remains exactly one Forge state/evidence authority.
"""
from __future__ import annotations

from typing import Any

MIN_EXHAUSTIVE_ZERO_CONFIRMATIONS = 2
MAX_EXHAUSTIVE_PASSES = 64


def install(backfill: Any) -> None:
    """Install conservative completion semantics into *backfill*."""
    backfill.MAX_PASSES = max(
        int(getattr(backfill, "MAX_PASSES", 0) or 0),
        MAX_EXHAUSTIVE_PASSES,
    )

    original_binding = getattr(backfill, "_batch_binding")
    max_batch_deltas = int(getattr(backfill, "MAX_BATCH_DELTAS"))

    def record_batch_progress(con, envelope: dict[str, Any], novel_count: int) -> None:
        binding = original_binding(con, envelope)
        values = envelope.get("deltas")
        if binding is None or not isinstance(values, list) or len(values) > max_batch_deltas:
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
            # A bounded ceiling is a visible stall, never semantic saturation.
            state = "MAX_PASSES_REACHED"

        con.execute(
            "UPDATE historical_chunks SET extraction_passes=?,consecutive_zero_novel=?,"
            "last_novel_count=?,last_extracted_at=?,state=? WHERE chunk_id=?",
            (passes, zero, int(novel_count), backfill.now(), state, chunk_id),
        )

    backfill._record_batch_progress = record_batch_progress
