from __future__ import annotations

"""Pulse-history estimator for SPM-S1 maintenance economics.

Produces conservative, lesionable estimates for:
- reads before semantic-field invalidation;
- updates during that lifetime;
- probability that an update is impact-complete/local enough for segmented maintenance.

Sparse or malformed history fails conservative. The estimator has performance-forecast
authority only; it never decides semantic truth, relevance or effects.
"""

from dataclasses import dataclass, replace
import math
from typing import Iterable

from research_entity.runtime.semantic_compile_horizon_estimator_v16 import (
    EpochReadLifetime,
    HorizonEstimate,
    estimate_read_horizon,
)
from research_entity.runtime.semantic_maintenance_economics_s1 import (
    MaintenanceDecision,
    MaintenanceEconomics,
    decide_maintenance,
)


@dataclass(frozen=True)
class MaintenanceLifetime:
    source_epoch: int
    reads_before_invalidation: int
    updates_before_invalidation: int
    local_impact_updates: int
    completed: bool = True
    recovery_or_fault_boundary: bool = False


@dataclass(frozen=True)
class MaintenanceHorizonEstimate:
    status: str
    completed_samples: int
    expected_reads_lower_bound: float
    expected_updates_lower_bound: float
    local_impact_probability_lower_bound: float | None
    read_horizon_status: str
    churn_shock: bool
    reason: str
    authority: str = "PERFORMANCE_FORECAST_ONLY_NO_TRUTH_AUTHORITY"


def _validate(x: MaintenanceLifetime) -> None:
    if isinstance(x.source_epoch, bool) or not isinstance(x.source_epoch, int) or x.source_epoch < 0:
        raise ValueError("source_epoch must be a non-negative int")
    for name in ("reads_before_invalidation", "updates_before_invalidation", "local_impact_updates"):
        v = getattr(x, name)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ValueError(f"{name} must be a non-negative int")
    if x.local_impact_updates > x.updates_before_invalidation:
        raise ValueError("local_impact_updates cannot exceed updates_before_invalidation")


def _linear_quantile(xs: list[float], q: float) -> float:
    if not xs:
        raise ValueError("quantile requires data")
    ys = sorted(xs)
    if len(ys) == 1:
        return ys[0]
    pos = (len(ys) - 1) * q
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return ys[lo]
    frac = pos - lo
    return ys[lo] * (1.0 - frac) + ys[hi] * frac


def _wilson_lower(successes: int, trials: int, z: float = 1.6448536269514722) -> float | None:
    """One-sided ~95% Wilson lower bound; None when there is no locality evidence."""
    if trials <= 0:
        return None
    p = successes / trials
    z2 = z * z
    den = 1.0 + z2 / trials
    center = p + z2 / (2.0 * trials)
    radius = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * trials)) / trials)
    return max(0.0, (center - radius) / den)


def estimate_maintenance_horizon(
    samples: Iterable[MaintenanceLifetime],
    *,
    min_completed_epochs: int = 5,
    window: int = 32,
    recent_window: int = 3,
    lower_quantile: float = 0.20,
) -> MaintenanceHorizonEstimate:
    if min_completed_epochs < 2:
        raise ValueError("min_completed_epochs must be >=2")
    if window < min_completed_epochs:
        raise ValueError("window must cover minimum history")
    if recent_window < 1 or recent_window > window:
        raise ValueError("invalid recent_window")
    if not 0.0 <= lower_quantile <= 0.5:
        raise ValueError("lower_quantile must be in [0,0.5]")

    ordered = list(samples)
    for s in ordered:
        _validate(s)
    completed = sorted((s for s in ordered if s.completed), key=lambda s: s.source_epoch)[-window:]
    if len(completed) < min_completed_epochs:
        return MaintenanceHorizonEstimate(
            status="INSUFFICIENT_HISTORY",
            completed_samples=len(completed),
            expected_reads_lower_bound=0.0,
            expected_updates_lower_bound=0.0,
            local_impact_probability_lower_bound=None,
            read_horizon_status="INSUFFICIENT_HISTORY",
            churn_shock=False,
            reason="NOT_ENOUGH_COMPLETED_LIFETIMES_FAIL_CONSERVATIVE",
        )

    read_est: HorizonEstimate = estimate_read_horizon(
        [
            EpochReadLifetime(
                source_epoch=s.source_epoch,
                reads_before_invalidation=s.reads_before_invalidation,
                completed=True,
                recovery_or_fault_boundary=s.recovery_or_fault_boundary,
            )
            for s in completed
        ],
        min_completed_epochs=min_completed_epochs,
        window=window,
        recent_window=recent_window,
        lower_quantile=lower_quantile,
    )

    updates = [float(s.updates_before_invalidation) for s in completed]
    update_bound = _linear_quantile(updates, lower_quantile)

    successes = sum(s.local_impact_updates for s in completed)
    trials = sum(s.updates_before_invalidation for s in completed)
    locality = _wilson_lower(successes, trials)

    # A recent locality collapse should not be hidden by old good history. Bound the global
    # Wilson estimate by the lowest recent observed ratio among lifetimes that had updates.
    recent = completed[-min(recent_window, len(completed)):]
    recent_ratios = [
        s.local_impact_updates / s.updates_before_invalidation
        for s in recent
        if s.updates_before_invalidation > 0
    ]
    if locality is not None and recent_ratios:
        locality = min(locality, min(recent_ratios))

    status = "HISTORY_BOUND"
    reason = "LOWER_QUANTILE_UPDATES_PLUS_WILSON_LOCALITY"
    if read_est.churn_shock:
        status = "CHURN_SHOCK_BOUND"
        reason = "READ_CHURN_SHOCK_PLUS_CONSERVATIVE_UPDATE_LOCALITY"
    if trials == 0:
        status = "NO_UPDATE_LOCALITY_EVIDENCE"
        reason = "NO_COMPLETED_UPDATE_TRIALS_SPM_DISABLED"

    return MaintenanceHorizonEstimate(
        status=status,
        completed_samples=len(completed),
        expected_reads_lower_bound=read_est.expected_reads_lower_bound,
        expected_updates_lower_bound=max(0.0, update_bound),
        local_impact_probability_lower_bound=locality,
        read_horizon_status=read_est.status,
        churn_shock=read_est.churn_shock,
        reason=reason,
    )


def decide_maintenance_from_pulse_history(
    economics_without_horizon: MaintenanceEconomics,
    samples: Iterable[MaintenanceLifetime],
    **estimate_kwargs,
) -> tuple[MaintenanceHorizonEstimate, MaintenanceDecision]:
    estimate = estimate_maintenance_horizon(samples, **estimate_kwargs)
    routed = replace(
        economics_without_horizon,
        expected_reads=estimate.expected_reads_lower_bound,
        expected_updates=estimate.expected_updates_lower_bound,
        local_impact_probability=estimate.local_impact_probability_lower_bound,
    )
    decision = decide_maintenance(routed)
    if estimate.status in {"INSUFFICIENT_HISTORY", "NO_UPDATE_LOCALITY_EVIDENCE"} and decision.mode == "SPM_S1":
        raise AssertionError("SPM-S1 must not be selected without locality evidence")
    return estimate, decision
