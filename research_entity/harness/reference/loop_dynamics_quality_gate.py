from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Literal
import hashlib, json, math

SCHEMA_VERSION = "h1-loop-dynamics-quality-gate-0.3"
AUTHORITY_NONE = "NONE"
DEFAULT_POLICY_ID = "h1-loop-quality-gate-default-v3"

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

    def validate(self) -> None:
        if not self.loop_id:
            raise ValueError("loop_id is required")
        for name, value in (
            ("state_epoch", self.state_epoch),
            ("low_delta_streak", self.low_delta_streak),
            ("measurement_age_cycles", self.measurement_age_cycles),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name, value in (
            ("state_delta_norm", self.state_delta_norm),
            ("residual_pressure", self.residual_pressure),
            ("oscillation_indicator", self.oscillation_indicator),
            ("marginal_utility_next", self.marginal_utility_next),
            ("residual_uncertainty", self.residual_uncertainty),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite")
        if self.state_delta_norm < 0 or self.residual_pressure < 0:
            raise ValueError("state_delta_norm and residual_pressure must be non-negative")
        if not 0.0 <= self.oscillation_indicator <= 1.0:
            raise ValueError("oscillation_indicator must be in [0,1]")
        if not 0.0 <= self.residual_uncertainty <= 1.0:
            raise ValueError("residual_uncertainty must be in [0,1]")

@dataclass(frozen=True)
class RecurrenceDecisionReceipt:
    schema_version: str
    loop_id: str
    state_epoch: int
    decision: Decision
    reason: str
    readout_sha256: str
    policy_sha256: str
    receipt_sha256: str
    authority: str = AUTHORITY_NONE
    effect_eligible: bool = False
    effect_gate_required: bool = True

def _canonical_hash(payload: object, domain: str) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + raw).hexdigest()

def _validate_policy(
    *,
    controller_policy_id: str,
    max_residual_uncertainty: float,
    max_measurement_age_cycles: int,
    low_delta_epsilon: float,
    converged_residual: float,
    stalled_residual: float,
) -> dict[str, object]:
    if not controller_policy_id:
        raise ValueError("controller_policy_id is required")
    if isinstance(max_measurement_age_cycles, bool) or not isinstance(max_measurement_age_cycles, int) or max_measurement_age_cycles < 0:
        raise ValueError("max_measurement_age_cycles must be a non-negative integer")
    values = {
        "max_residual_uncertainty": max_residual_uncertainty,
        "low_delta_epsilon": low_delta_epsilon,
        "converged_residual": converged_residual,
        "stalled_residual": stalled_residual,
    }
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite")
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    if max_residual_uncertainty > 1:
        raise ValueError("max_residual_uncertainty must be in [0,1]")
    if stalled_residual < converged_residual:
        raise ValueError("stalled_residual must be >= converged_residual")
    return {
        "schema_version": SCHEMA_VERSION,
        "controller_policy_id": controller_policy_id,
        "max_residual_uncertainty": max_residual_uncertainty,
        "max_measurement_age_cycles": max_measurement_age_cycles,
        "low_delta_epsilon": low_delta_epsilon,
        "converged_residual": converged_residual,
        "stalled_residual": stalled_residual,
    }

def decide_recurrence(
    r: LoopDynamicsReadout,
    *,
    controller_policy_id: str = DEFAULT_POLICY_ID,
    max_residual_uncertainty: float = 0.08,
    max_measurement_age_cycles: int = 1,
    low_delta_epsilon: float = 0.02,
    converged_residual: float = 0.08,
    stalled_residual: float = 0.25,
) -> RecurrenceDecisionReceipt:
    """Deterministic proposal-only H1 reference candidate.

    Invalid telemetry is rejected before classification. Missing, stale, or
    over-uncertain residual-estimator metadata routes fail-closed. Convergence
    requires both persistent low state change and low residual pressure. The
    receipt binds both the readout and the controller policy/thresholds used.
    """
    r.validate()
    policy = _validate_policy(
        controller_policy_id=controller_policy_id,
        max_residual_uncertainty=max_residual_uncertainty,
        max_measurement_age_cycles=max_measurement_age_cycles,
        low_delta_epsilon=low_delta_epsilon,
        converged_residual=converged_residual,
        stalled_residual=stalled_residual,
    )
    readout_sha256 = _canonical_hash(asdict(r), "H1_LOOP_QUALITY_READOUT_V3")
    policy_sha256 = _canonical_hash(policy, "H1_LOOP_QUALITY_POLICY_V3")

    if not r.residual_estimator_id or not r.residual_estimator_version:
        decision, reason = "ROUTE_READOUT_UNCERTAIN", "missing_residual_estimator_identity"
    elif r.residual_uncertainty > max_residual_uncertainty:
        decision, reason = "ROUTE_READOUT_UNCERTAIN", "residual_uncertainty_above_floor"
    elif r.measurement_age_cycles > max_measurement_age_cycles:
        decision, reason = "ROUTE_READOUT_UNCERTAIN", "residual_readout_stale"
    elif r.low_delta_streak >= 2 and r.state_delta_norm < low_delta_epsilon and r.residual_pressure > stalled_residual:
        decision, reason = "ESCALATE_STALLED", "low_delta_high_residual"
    elif r.low_delta_streak >= 2 and r.state_delta_norm < low_delta_epsilon and r.residual_pressure < converged_residual:
        decision, reason = "HALT_CANDIDATE_CONVERGED", "low_delta_and_low_residual_with_valid_readout"
    elif r.marginal_utility_next < 0 and r.residual_pressure <= stalled_residual:
        decision, reason = "HALT_MARGINAL", "negative_marginal_utility"
    else:
        decision, reason = "CONTINUE", "unresolved_pressure_or_productive_cycle"

    receipt_payload = {
        "schema_version": SCHEMA_VERSION,
        "loop_id": r.loop_id,
        "state_epoch": r.state_epoch,
        "decision": decision,
        "reason": reason,
        "readout_sha256": readout_sha256,
        "policy_sha256": policy_sha256,
        "authority": AUTHORITY_NONE,
        "effect_eligible": False,
        "effect_gate_required": True,
    }
    return RecurrenceDecisionReceipt(
        schema_version=SCHEMA_VERSION,
        loop_id=r.loop_id,
        state_epoch=r.state_epoch,
        decision=decision,
        reason=reason,
        readout_sha256=readout_sha256,
        policy_sha256=policy_sha256,
        receipt_sha256=_canonical_hash(receipt_payload, "H1_LOOP_QUALITY_RECEIPT_V3"),
    )
