from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Literal
import hashlib, json

SCHEMA_VERSION = "h1-loop-dynamics-quality-gate-0.1"
AUTHORITY_NONE = "NONE"

Decision = Literal[
    "CONTINUE",
    "HALT_CANDIDATE_CONVERGED",
    "HALT_MARGINAL",
    "ESCALATE_STALLED",
    "ROUTE_READOUT_UNCERTAIN",
]

@dataclass(frozen=True)
class LoopDynamicsReadout:
    loop_id: str
    state_epoch: int
    state_delta_norm: float
    residual_pressure: float
    low_delta_streak: int
    oscillation_indicator: float
    marginal_utility_next: float
    residual_estimator_id: str
    residual_estimator_version: str
    residual_uncertainty: float
    measurement_age_cycles: int

@dataclass(frozen=True)
class RecurrenceDecisionReceipt:
    schema_version: str
    loop_id: str
    state_epoch: int
    decision: Decision
    reason: str
    readout_sha256: str
    authority: str = AUTHORITY_NONE
    effect_eligible: bool = False
    effect_gate_required: bool = True

def _hash_readout(r: LoopDynamicsReadout) -> str:
    raw = json.dumps(asdict(r), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def decide_recurrence(
    r: LoopDynamicsReadout,
    *,
    max_residual_uncertainty: float = 0.08,
    max_measurement_age_cycles: int = 1,
    low_delta_epsilon: float = 0.02,
    converged_residual: float = 0.08,
    stalled_residual: float = 0.25,
) -> RecurrenceDecisionReceipt:
    """Deterministic proposal-only H1 reference candidate.

    It refuses to call a readout converged when the residual estimator is stale,
    insufficiently identified, or too uncertain. It never grants external-effect
    authority.
    """
    if not r.residual_estimator_id or not r.residual_estimator_version:
        decision, reason = "ROUTE_READOUT_UNCERTAIN", "missing_residual_estimator_identity"
    elif r.residual_uncertainty > max_residual_uncertainty:
        decision, reason = "ROUTE_READOUT_UNCERTAIN", "residual_uncertainty_above_floor"
    elif r.measurement_age_cycles > max_measurement_age_cycles:
        decision, reason = "ROUTE_READOUT_UNCERTAIN", "residual_readout_stale"
    elif r.low_delta_streak >= 2 and r.state_delta_norm < low_delta_epsilon and r.residual_pressure > stalled_residual:
        decision, reason = "ESCALATE_STALLED", "low_delta_high_residual"
    elif r.residual_pressure < converged_residual:
        decision, reason = "HALT_CANDIDATE_CONVERGED", "low_residual_with_valid_readout"
    elif r.marginal_utility_next < 0 and r.residual_pressure <= stalled_residual:
        decision, reason = "HALT_MARGINAL", "negative_marginal_utility"
    else:
        decision, reason = "CONTINUE", "unresolved_pressure_or_productive_cycle"
    return RecurrenceDecisionReceipt(
        schema_version=SCHEMA_VERSION,
        loop_id=r.loop_id,
        state_epoch=r.state_epoch,
        decision=decision,
        reason=reason,
        readout_sha256=_hash_readout(r),
    )
