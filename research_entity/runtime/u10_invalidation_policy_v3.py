"""Measured operating-window selector for U10 structural invalidation.

The policy prevents a local microbenchmark win (e.g. prepared-mask lookup) from becoming an
architecture default while its maintenance/build/memory shadows are worse. It compares full
per-mutation latency cost and rejects PREPARED_MASK when its memory budget is unavailable.

Research candidate only; measured profile inputs must come from the current graph/runtime.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvalidationModeProfile:
    bfs_lookup_ms: float
    bfs_update_ms: float
    prepared_lookup_ms: float
    prepared_update_ms: float
    prepared_build_ms: float
    prepared_extra_bytes: int
    expected_reads_per_mutation: float = 1.0
    expected_mutations_per_prepared_build: float = 1000.0
    memory_budget_bytes: int | None = None


@dataclass(frozen=True)
class InvalidationModeDecision:
    mode: str
    bfs_expected_ms_per_mutation: float
    prepared_expected_ms_per_mutation: float
    latency_break_even_reads_per_mutation: float | None
    memory_admissible: bool
    reason: str


def choose_invalidation_mode(profile: InvalidationModeProfile) -> InvalidationModeDecision:
    if profile.expected_reads_per_mutation < 0:
        raise ValueError("expected_reads_per_mutation must be >= 0")
    if profile.expected_mutations_per_prepared_build <= 0:
        raise ValueError("expected_mutations_per_prepared_build must be > 0")
    if profile.prepared_extra_bytes < 0:
        raise ValueError("prepared_extra_bytes must be >= 0")

    reads = profile.expected_reads_per_mutation
    bfs = profile.bfs_update_ms + reads * profile.bfs_lookup_ms
    prepared = (
        profile.prepared_update_ms
        + reads * profile.prepared_lookup_ms
        + profile.prepared_build_ms / profile.expected_mutations_per_prepared_build
    )
    memory_ok = (
        profile.memory_budget_bytes is None
        or profile.prepared_extra_bytes <= profile.memory_budget_bytes
    )

    lookup_saving = profile.bfs_lookup_ms - profile.prepared_lookup_ms
    fixed_prepared_premium = (
        profile.prepared_update_ms
        - profile.bfs_update_ms
        + profile.prepared_build_ms / profile.expected_mutations_per_prepared_build
    )
    if lookup_saving > 0:
        break_even = max(0.0, fixed_prepared_premium / lookup_saving)
    else:
        break_even = None

    if memory_ok and prepared < bfs:
        mode = "PREPARED_MASK"
        reason = "measured total latency lower and memory budget admits prepared state"
    elif not memory_ok:
        mode = "ON_DEMAND_BFS"
        reason = "prepared state exceeds declared memory budget"
    else:
        mode = "ON_DEMAND_BFS"
        reason = "on-demand BFS has lower or equal measured total cost in this operating window"

    return InvalidationModeDecision(
        mode=mode,
        bfs_expected_ms_per_mutation=bfs,
        prepared_expected_ms_per_mutation=prepared,
        latency_break_even_reads_per_mutation=break_even,
        memory_admissible=memory_ok,
        reason=reason,
    )
