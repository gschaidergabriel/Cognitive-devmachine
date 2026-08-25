#!/usr/bin/env python3
"""Fail-closed exhaustiveness semantics for historical Free-Swarm extraction.

Keeps the existing historical backfill module and its canonical causal/source/pass
binding as the sole authority. It only strengthens completion semantics: a chunk
cannot become SATURATED from an implicit or one-off zero-novel pass, and the bounded
pass ceiling is no longer the old three-pass truncation.

No provider/model/network call occurs here.
"""
from __future__ import annotations

from typing import Any

MIN_EXHAUSTIVE_ZERO_CONFIRMATIONS = 2
MAX_EXHAUSTIVE_PASSES = 64
_INSTALL_MARKER = "_CLAY_BACKFILL_EXHAUSTIVENESS_878_INSTALLED"


def install(backfill: Any) -> None:
    """Install conservative completion semantics without weakening causal binding."""
    backfill.MAX_PASSES = max(
        int(getattr(backfill, "MAX_PASSES", 0) or 0),
        MAX_EXHAUSTIVE_PASSES,
    )
    if getattr(backfill, _INSTALL_MARKER, False):
        return

    def record_batch_progress(con, envelope: dict[str, Any], novel_count: int) -> None:
        # Reuse the canonical binding gate. Foreign source identity, stale/future
        # pass identity and other invalid envelopes cannot advance a chunk.
        binding = backfill._batch_binding(con, envelope)
        values = envelope.get("deltas")
        if (
            binding is None
            or not isinstance(values, list)
            or len(values) > int(backfill.MAX_BATCH_DELTAS)
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
            # Finite safety ceiling is a measured stall, never semantic PASS.
            state = "MAX_PASSES_REACHED"

        con.execute(
            "UPDATE historical_chunks SET extraction_passes=?,"
            "consecutive_zero_novel=?,last_novel_count=?,last_extracted_at=?,"
            "state=? WHERE chunk_id=?",
            (passes, zero, int(novel_count), backfill.now(), state, chunk_id),
        )

    backfill._record_batch_progress = record_batch_progress
    setattr(backfill, _INSTALL_MARKER, True)
