from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from statistics import median
from typing import Any, Mapping, Sequence

from loop_dynamics_reference import LoopDynamicsReadout


POLICY_VERSION = "frank-posthoc-trajectory-readout/0.1"
_HASH_DOMAIN = b"FrankPostHocTrajectoryReadout/v1\x00"


class PostHocDecision(str, Enum):
    CONTINUE = "CONTINUE"
    HALT_CANDIDATE_CONVERGED = "HALT_CANDIDATE_CONVERGED"
    ROUTE = "ROUTE"
    ROLLBACK = "ROLLBACK"
    ABORT_DIVERGING = "ABORT_DIVERGING"


@dataclass(frozen=True)
class PostHocReadoutConfig:
    window: int = 3
    min_observations: int = 3
    convergence_delta_max: float = 0.08
    convergence_pressure_max: float = 0.16
    nonincreasing_slope_tolerance: float = 0.02
    continue_utility_min: float = 0.04
    divergence_delta_min: float = 0.85
    overthinking_min: float = 0.50

    def validate(self) -> None:
        if self.window < 2:
            raise ValueError("window must be >=2")
        if self.min_observations < 2:
            raise ValueError("min_observations must be >=2")
        if self.window > self.min_observations:
            raise ValueError("window cannot exceed min_observations")
        for name in (
            "convergence_delta_max",
            "convergence_pressure_max",
            "nonincreasing_slope_tolerance",
            "continue_utility_min",
            "divergence_delta_min",
            "overthinking_min",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True)
class PostHocTrajectoryStats:
    observations: int
    window_observations: int
    median_delta: float
    median_pressure: float
    median_marginal_utility: float
    delta_slope: float
    pressure_slope: float
    max_overthinking: float
    max_uncertainty: float


@dataclass(frozen=True)
class PostHocDecisionReceipt:
    decision: PostHocDecision
    reason: str
    authority: str
    policy_version: str
    trajectory_hash: str
    stats: PostHocTrajectoryStats
    receipt_hash: str


def _canonical_hash(payload: Mapping[str, Any] | list[Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(_HASH_DOMAIN + raw.encode("utf-8")).hexdigest()


def _slope(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    return (float(values[-1]) - float(values[0])) / float(len(values) - 1)


def _validate_trajectory(readouts: Sequence[LoopDynamicsReadout]) -> None:
    if not readouts:
        raise ValueError("trajectory must contain at least one readout")
    first = readouts[0]
    prior_epoch = -1
    prior_count = -1
    for r in readouts:
        r.validate()
        if (r.loop_id, r.loop_family, r.timescale) != (first.loop_id, first.loop_family, first.timescale):
            raise ValueError("trajectory mixes loop identities/families/timescales")
        if r.state_epoch <= prior_epoch:
            raise ValueError("state_epoch must be strictly increasing")
        if r.recurrence_count < prior_count:
            raise ValueError("recurrence_count must be monotone non-decreasing")
        prior_epoch = r.state_epoch
        prior_count = r.recurrence_count


def trajectory_stats(
    readouts: Sequence[LoopDynamicsReadout],
    config: PostHocReadoutConfig = PostHocReadoutConfig(),
) -> PostHocTrajectoryStats:
    config.validate()
    _validate_trajectory(readouts)
    window = list(readouts[-config.window :])
    deltas = [r.state_delta_norm for r in window]
    pressures = [r.residual_pressure for r in window]
    utilities = [r.marginal_utility_next for r in window]
    return PostHocTrajectoryStats(
        observations=len(readouts),
        window_observations=len(window),
        median_delta=float(median(deltas)),
        median_pressure=float(median(pressures)),
        median_marginal_utility=float(median(utilities)),
        delta_slope=_slope(deltas),
        pressure_slope=_slope(pressures),
        max_overthinking=max(r.overthinking_indicator for r in window),
        max_uncertainty=max(r.uncertainty for r in window),
    )


def decide_posthoc(
    readouts: Sequence[LoopDynamicsReadout],
    config: PostHocReadoutConfig = PostHocReadoutConfig(),
) -> PostHocDecisionReceipt:
    """Deterministic non-trained exit/readout baseline over a frozen recurrence trajectory.

    This is deliberately a readout, not a trajectory-shaping controller. It consumes only
    already-observed LoopDynamicsReadout values and never carries execution authority.
    """
    stats = trajectory_stats(readouts, config)
    latest = readouts[-1]
    budget_left = latest.recurrence_count < latest.recurrence_budget
    window = list(readouts[-config.window :])

    diverging = (
        stats.max_overthinking >= config.overthinking_min
        or (
            max(r.state_delta_norm for r in window) >= config.divergence_delta_min
            and stats.delta_slope > config.nonincreasing_slope_tolerance
        )
    )
    if diverging:
        if latest.rollback_ref:
            decision = PostHocDecision.ROLLBACK
            reason = "recent_trajectory_diverging_with_checkpoint"
        else:
            decision = PostHocDecision.ABORT_DIVERGING
            reason = "recent_trajectory_diverging_without_checkpoint"
    elif not budget_left:
        decision = PostHocDecision.ROUTE
        reason = "recurrence_budget_exhausted"
    elif stats.observations < config.min_observations:
        decision = PostHocDecision.CONTINUE
        reason = "insufficient_frozen_trajectory_for_posthoc_exit"
    else:
        converged = (
            stats.median_delta <= config.convergence_delta_max
            and stats.median_pressure <= config.convergence_pressure_max
            and stats.delta_slope <= config.nonincreasing_slope_tolerance
            and stats.pressure_slope <= config.nonincreasing_slope_tolerance
        )
        if converged:
            decision = PostHocDecision.HALT_CANDIDATE_CONVERGED
            reason = "windowed_low_delta_low_pressure_nonincreasing"
        elif stats.median_marginal_utility > config.continue_utility_min:
            decision = PostHocDecision.CONTINUE
            reason = "recent_trajectory_has_positive_marginal_utility"
        else:
            decision = PostHocDecision.ROUTE
            reason = "no_convergence_and_no_positive_local_margin"

    trajectory_payload = [asdict(r) for r in readouts]
    trajectory_hash = _canonical_hash(trajectory_payload)
    receipt_core = {
        "decision": decision.value,
        "reason": reason,
        "authority": "PROPOSAL_ONLY",
        "policy_version": POLICY_VERSION,
        "trajectory_hash": trajectory_hash,
        "stats": asdict(stats),
    }
    return PostHocDecisionReceipt(
        decision=decision,
        reason=reason,
        authority="PROPOSAL_ONLY",
        policy_version=POLICY_VERSION,
        trajectory_hash=trajectory_hash,
        stats=stats,
        receipt_hash=_canonical_hash(receipt_core),
    )
