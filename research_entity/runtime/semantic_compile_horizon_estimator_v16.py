from __future__ import annotations

"""Pulse-informed conservative lifetime estimator for U16 compile amortization.

This module does not decide truth, retrieval relevance, or effect authority. It estimates a
lower-bound read horizon before invalidation from completed epoch telemetry, then feeds the
existing U16 compile-economics gate. Sparse history, malformed telemetry, and detected churn
shocks fail conservative to ONLINE.

The estimator is intentionally simple and lesionable. A later learned predictor must beat it
on held-out total-work/regret while preserving the same fail-closed boundary.
"""

from dataclasses import dataclass, replace
import math
from typing import Iterable

from research_entity.runtime.semantic_compile_amortization_gate_v16 import (
    CompileDecision,
    CompileEconomics,
    decide_compile,
)


@dataclass(frozen=True)
class EpochReadLifetime:
    source_epoch: int
    reads_before_invalidation: int
    completed: bool = True
    recovery_or_fault_boundary: bool = False


@dataclass(frozen=True)
class HorizonEstimate:
    status: str
    completed_samples: int
    expected_reads_lower_bound: float
    empirical_q20: float | None
    recent_floor: float | None
    churn_shock: bool
    reason: str
    authority: str = "PERFORMANCE_FORECAST_ONLY_NO_TRUTH_AUTHORITY"


def _validate_sample(x: EpochReadLifetime) -> None:
    if isinstance(x.source_epoch, bool) or not isinstance(x.source_epoch, int) or x.source_epoch < 0:
        raise ValueError("source_epoch must be a non-negative int")
    if (
        isinstance(x.reads_before_invalidation, bool)
        or not isinstance(x.reads_before_invalidation, int)
        or x.reads_before_invalidation < 0
    ):
        raise ValueError("reads_before_invalidation must be a non-negative int")


def _linear_quantile(xs: list[float], q: float) -> float:
    if not xs:
        raise ValueError("quantile requires data")
    ys = sorted(xs)
    if len(ys) == 1:
        return ys[0]
    pos = (len(ys) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ys[lo]
    frac = pos - lo
    return ys[lo] * (1.0 - frac) + ys[hi] * frac


def estimate_read_horizon(
    samples: Iterable[EpochReadLifetime],
    *,
    min_completed_epochs: int = 5,
    window: int = 32,
    recent_window: int = 3,
    lower_quantile: float = 0.20,
    churn_drop_ratio: float = 0.50,
) -> HorizonEstimate:
    if min_completed_epochs < 2:
        raise ValueError("min_completed_epochs must be >=2")
    if window < min_completed_epochs:
        raise ValueError("window must cover minimum history")
    if recent_window < 1 or recent_window > window:
        raise ValueError("invalid recent_window")
    if not (0.0 <= lower_quantile <= 0.5):
        raise ValueError("lower_quantile must be in [0,0.5]")
    if not (0.0 < churn_drop_ratio < 1.0):
        raise ValueError("churn_drop_ratio must be in (0,1)")

    ordered = list(samples)
    for sample in ordered:
        _validate_sample(sample)
    completed = [x for x in ordered if x.completed]
    completed.sort(key=lambda x: x.source_epoch)
    completed = completed[-window:]
    n = len(completed)
    if n < min_completed_epochs:
        return HorizonEstimate(
            status="INSUFFICIENT_HISTORY",
            completed_samples=n,
            expected_reads_lower_bound=0.0,
            empirical_q20=None,
            recent_floor=None,
            churn_shock=False,
            reason="NOT_ENOUGH_COMPLETED_EPOCHS_FAIL_ONLINE",
        )

    horizons = [float(x.reads_before_invalidation) for x in completed]
    q = _linear_quantile(horizons, lower_quantile)
    recent = horizons[-min(recent_window, len(horizons)):]
    recent_floor = min(recent)

    # Compare recent central tendency with the older completed history. A sudden drop in
    # lifetime is a churn shock; use the recent floor rather than a stale long-history bound.
    older = horizons[:-len(recent)]
    shock = False
    if older:
        older_median = _linear_quantile(older, 0.50)
        recent_median = _linear_quantile(recent, 0.50)
        if older_median > 0.0 and recent_median < older_median * churn_drop_ratio:
            shock = True

    # Fault/recovery boundaries are real invalidations and stay in the sample. They are not
    # discarded as outliers because doing so would bias the optimizer toward over-compiling.
    bound = min(q, recent_floor) if shock else q
    bound = max(0.0, float(bound))
    return HorizonEstimate(
        status="CHURN_SHOCK_BOUND" if shock else "HISTORY_BOUND",
        completed_samples=n,
        expected_reads_lower_bound=bound,
        empirical_q20=q,
        recent_floor=recent_floor,
        churn_shock=shock,
        reason=(
            "RECENT_LIFETIME_COLLAPSE_USE_RECENT_FLOOR"
            if shock
            else "EMPIRICAL_LOWER_QUANTILE"
        ),
    )


def decide_compile_from_pulse_history(
    economics_without_horizon: CompileEconomics,
    samples: Iterable[EpochReadLifetime],
    **estimate_kwargs,
) -> tuple[HorizonEstimate, CompileDecision]:
    estimate = estimate_read_horizon(samples, **estimate_kwargs)
    routed = replace(
        economics_without_horizon,
        expected_reads_before_invalidation=estimate.expected_reads_lower_bound,
    )
    decision = decide_compile(routed)
    if estimate.status == "INSUFFICIENT_HISTORY" and decision.mode != "ONLINE":
        raise AssertionError("insufficient Pulse history must fail conservative to ONLINE")
    return estimate, decision
