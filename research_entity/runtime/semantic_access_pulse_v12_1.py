"""U12.1 concurrency-hardened wrapper for segmented semantic-access Pulse.

Adds a database-level single-CURRENT invariant to U12. This closes the stale-parent
TOCTOU window even if another publisher advances access_head after the initial _head()
read but before this writer obtains BEGIN IMMEDIATE. The existing U12 transaction then
rolls back instead of producing two CURRENT generations or overwriting a newer head.
"""
from __future__ import annotations
from pathlib import Path

from semantic_access_pulse_v12 import (  # re-export current U12 API
    AccessPath,
    PulseInvariantError,
    PulsePlan,
    PulseReceipt,
    SegmentedPulseProjection,
    StalePulse,
)


class ConcurrentSafeSegmentedPulseProjection(SegmentedPulseProjection):
    def __init__(self, path: str = ":memory:"):
        super().__init__(path)
        guard = Path(__file__).with_name("RAE_UNIFIEDDB_V12_1_PULSE_CONCURRENCY_GUARD.sql")
        self.con.executescript(guard.read_text(encoding="utf-8"))


__all__ = [
    "AccessPath",
    "PulseInvariantError",
    "PulsePlan",
    "PulseReceipt",
    "StalePulse",
    "ConcurrentSafeSegmentedPulseProjection",
]
