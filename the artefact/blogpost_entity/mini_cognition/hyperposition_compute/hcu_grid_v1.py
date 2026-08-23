#!/usr/bin/env python3
"""Deterministic source contract for the Mini Entity Hyperposition Computational Unit.

The HCU grid is a candidate-compute organ. It does not own identity, durable state,
truth, or effects. Capacity is derived from measured worker RSS; model footprint is
never guessed for admission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class HCUError(ValueError):
    """Fail-closed HCU contract error."""


@dataclass(frozen=True)
class CapacityPlan:
    total_ram_bytes: int
    reserve_bytes: int
    measured_worker_rss_bytes: int
    resident_slots: int
    active_cpu_slots: int
    queued_slots: int


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    independence_group: str
    candidate: str
    confidence: float


def _positive_int(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise HCUError(f"{field}:POSITIVE_INT_REQUIRED")
    return value


def plan_capacity(
    *,
    total_ram_bytes: int,
    measured_worker_rss_bytes: int,
    cpu_cores: int,
    reserve_ratio: float = 0.25,
    requested_modules: int | None = None,
) -> CapacityPlan:
    """Return a conservative resident/active plan from measured runtime RSS.

    resident_slots is RAM-bound; active_cpu_slots is conservatively CPU-core-bound.
    Extra resident modules are queued/parked rather than presented as simultaneous
    throughput. This is a planner, not runtime/model acceptance evidence.
    """
    total_ram_bytes = _positive_int(total_ram_bytes, "total_ram_bytes")
    measured_worker_rss_bytes = _positive_int(
        measured_worker_rss_bytes, "measured_worker_rss_bytes"
    )
    cpu_cores = _positive_int(cpu_cores, "cpu_cores")
    if not isinstance(reserve_ratio, (int, float)) or isinstance(reserve_ratio, bool):
        raise HCUError("reserve_ratio:NUMBER_REQUIRED")
    reserve_ratio = float(reserve_ratio)
    if not 0.10 <= reserve_ratio <= 0.60:
        raise HCUError("reserve_ratio:OUT_OF_RANGE_0_10_TO_0_60")
    if requested_modules is not None:
        requested_modules = _positive_int(requested_modules, "requested_modules")

    reserve_bytes = int(total_ram_bytes * reserve_ratio)
    usable = total_ram_bytes - reserve_bytes
    resident_slots = usable // measured_worker_rss_bytes
    if requested_modules is not None:
        resident_slots = min(resident_slots, requested_modules)
    if resident_slots < 1:
        raise HCUError("INSUFFICIENT_RAM_FOR_ONE_MEASURED_WORKER")

    active_cpu_slots = min(cpu_cores, resident_slots)
    queued_slots = max(0, resident_slots - active_cpu_slots)
    return CapacityPlan(
        total_ram_bytes=total_ram_bytes,
        reserve_bytes=reserve_bytes,
        measured_worker_rss_bytes=measured_worker_rss_bytes,
        resident_slots=resident_slots,
        active_cpu_slots=active_cpu_slots,
        queued_slots=queued_slots,
    )


def aggregate_diversity_capped(proposals: Iterable[Proposal]) -> tuple[str, dict[str, float]]:
    """Aggregate candidates without letting correlated clones multiply confidence.

    Each declared independence group contributes at most one unit of total voting
    weight. Within a group, confidence is averaged per candidate and the group's
    strongest candidate receives that group's unit vote. Ties fail closed.

    The independence-group label is provenance metadata, not a proof of statistical
    independence; runtime admission must bind it to model/context/route ancestry.
    """
    grouped: dict[str, list[Proposal]] = {}
    seen_ids: set[str] = set()
    for proposal in proposals:
        if not proposal.proposal_id or not proposal.independence_group or not proposal.candidate:
            raise HCUError("PROPOSAL_NONEMPTY_FIELDS_REQUIRED")
        if proposal.proposal_id in seen_ids:
            raise HCUError("DUPLICATE_PROPOSAL_ID")
        seen_ids.add(proposal.proposal_id)
        if isinstance(proposal.confidence, bool) or not isinstance(proposal.confidence, (int, float)):
            raise HCUError("CONFIDENCE_NUMBER_REQUIRED")
        confidence = float(proposal.confidence)
        if not 0.0 <= confidence <= 1.0:
            raise HCUError("CONFIDENCE_OUT_OF_RANGE")
        grouped.setdefault(proposal.independence_group, []).append(
            Proposal(
                proposal_id=proposal.proposal_id,
                independence_group=proposal.independence_group,
                candidate=proposal.candidate,
                confidence=confidence,
            )
        )

    if not grouped:
        raise HCUError("AT_LEAST_ONE_PROPOSAL_REQUIRED")

    scores: dict[str, float] = {}
    for group_items in grouped.values():
        per_candidate: dict[str, list[float]] = {}
        for item in group_items:
            per_candidate.setdefault(item.candidate, []).append(item.confidence)
        means = {
            candidate: sum(values) / len(values)
            for candidate, values in per_candidate.items()
        }
        best_score = max(means.values())
        group_winners = sorted(
            candidate for candidate, score in means.items() if score == best_score
        )
        if len(group_winners) != 1:
            raise HCUError("INDEPENDENCE_GROUP_TIE_UNKNOWN")
        winner = group_winners[0]
        scores[winner] = scores.get(winner, 0.0) + 1.0

    best = max(scores.values())
    winners = sorted(candidate for candidate, score in scores.items() if score == best)
    if len(winners) != 1:
        raise HCUError("GRID_TIE_UNKNOWN")
    return winners[0], scores
