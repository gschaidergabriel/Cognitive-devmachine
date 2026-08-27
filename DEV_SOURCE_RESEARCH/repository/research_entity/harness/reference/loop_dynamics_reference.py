from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class DynamicRegime(str, Enum):
    CONVERGING_FIXED_POINT = "CONVERGING_FIXED_POINT"
    PRODUCTIVE_LIMIT_CYCLE = "PRODUCTIVE_LIMIT_CYCLE"
    STALLED = "STALLED"
    DIVERGING_OR_OVERTHINKING = "DIVERGING_OR_OVERTHINKING"
    CHAOTIC_OR_UNCLASSIFIED = "CHAOTIC_OR_UNCLASSIFIED"


class RecurrenceDecision(str, Enum):
    CONTINUE = "CONTINUE"
    HALT_CANDIDATE_CONVERGED = "HALT_CANDIDATE_CONVERGED"
    ROUTE = "ROUTE"
    ESCALATE_STALLED = "ESCALATE_STALLED"
    ABORT_DIVERGING = "ABORT_DIVERGING"
    ROLLBACK = "ROLLBACK"


@dataclass(frozen=True)
class ControllerThresholds:
    convergence_delta_max: float = 0.06
    convergence_pressure_max: float = 0.14
    productive_oscillation_min: float = 0.45
    diverging_delta_min: float = 0.85
    marginal_utility_cost: float = 0.04


@dataclass(frozen=True)
class LoopDynamicsReadout:
    loop_id: str
    loop_family: str
    timescale: str
    state_epoch: int
    state_delta_norm: float
    residual_pressure: float
    recurrence_count: int
    recurrence_budget: int
    marginal_utility_next: float
    oscillation_indicator: float = 0.0
    overthinking_indicator: float = 0.0
    rollback_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    uncertainty: float = 0.0
    provenance: str = "H1_REFERENCE"

    def validate(self) -> None:
        if not self.loop_id or not self.loop_family or not self.timescale:
            raise ValueError("loop identity/family/timescale are required")
        if self.state_epoch < 0 or self.recurrence_count < 0 or self.recurrence_budget < 0:
            raise ValueError("epochs/counts/budgets must be non-negative")
        if self.state_delta_norm < 0 or self.residual_pressure < 0:
            raise ValueError("state delta and residual pressure must be non-negative")
        if not 0.0 <= self.oscillation_indicator <= 1.0:
            raise ValueError("oscillation_indicator must be in [0,1]")
        if not 0.0 <= self.overthinking_indicator <= 1.0:
            raise ValueError("overthinking_indicator must be in [0,1]")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0,1]")


@dataclass(frozen=True)
class RecurrenceDecisionReceipt:
    regime: DynamicRegime
    decision: RecurrenceDecision
    reason: str
    authority: str
    input_hash: str
    receipt_hash: str


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def classify_regime(
    readout: LoopDynamicsReadout,
    thresholds: ControllerThresholds = ControllerThresholds(),
) -> DynamicRegime:
    readout.validate()
    budget_left = readout.recurrence_count < readout.recurrence_budget

    if (
        readout.overthinking_indicator >= 0.5
        or (
            readout.state_delta_norm >= thresholds.diverging_delta_min
            and readout.marginal_utility_next <= thresholds.marginal_utility_cost
        )
    ):
        return DynamicRegime.DIVERGING_OR_OVERTHINKING

    if (
        readout.state_delta_norm <= thresholds.convergence_delta_max
        and readout.residual_pressure <= thresholds.convergence_pressure_max
    ):
        return DynamicRegime.CONVERGING_FIXED_POINT

    if (
        readout.state_delta_norm <= thresholds.convergence_delta_max
        and readout.residual_pressure > thresholds.convergence_pressure_max
    ):
        return DynamicRegime.STALLED

    if (
        budget_left
        and readout.oscillation_indicator >= thresholds.productive_oscillation_min
        and readout.marginal_utility_next > thresholds.marginal_utility_cost
    ):
        return DynamicRegime.PRODUCTIVE_LIMIT_CYCLE

    return DynamicRegime.CHAOTIC_OR_UNCLASSIFIED


def decide_recurrence(
    readout: LoopDynamicsReadout,
    thresholds: ControllerThresholds = ControllerThresholds(),
) -> RecurrenceDecisionReceipt:
    regime = classify_regime(readout, thresholds)
    budget_left = readout.recurrence_count < readout.recurrence_budget

    if regime is DynamicRegime.CONVERGING_FIXED_POINT:
        decision = RecurrenceDecision.HALT_CANDIDATE_CONVERGED
        reason = "low_delta_and_low_residual_pressure"
    elif regime is DynamicRegime.STALLED:
        if budget_left and readout.marginal_utility_next > thresholds.marginal_utility_cost:
            decision = RecurrenceDecision.CONTINUE
            reason = "stalled_but_next_recurrence_has_positive_expected_margin"
        else:
            decision = RecurrenceDecision.ESCALATE_STALLED
            reason = "stalled_without_justified_local_recurrence"
    elif regime is DynamicRegime.PRODUCTIVE_LIMIT_CYCLE:
        decision = RecurrenceDecision.CONTINUE
        reason = "bounded_cycle_with_positive_expected_margin"
    elif regime is DynamicRegime.DIVERGING_OR_OVERTHINKING:
        decision = RecurrenceDecision.ROLLBACK if readout.rollback_ref else RecurrenceDecision.ABORT_DIVERGING
        reason = "overthinking_or_divergence_detected"
    else:
        if budget_left and readout.residual_pressure > thresholds.convergence_pressure_max and readout.marginal_utility_next > thresholds.marginal_utility_cost:
            decision = RecurrenceDecision.CONTINUE
            reason = "unclassified_but_bounded_positive_expected_margin"
        else:
            decision = RecurrenceDecision.ROUTE
            reason = "unclassified_requires_external_route_or_reseed"

    input_payload = asdict(readout)
    input_hash = _canonical_hash(input_payload)
    receipt_payload = {
        "regime": regime.value,
        "decision": decision.value,
        "reason": reason,
        "authority": "PROPOSAL_ONLY",
        "input_hash": input_hash,
    }
    return RecurrenceDecisionReceipt(
        regime=regime,
        decision=decision,
        reason=reason,
        authority="PROPOSAL_ONLY",
        input_hash=input_hash,
        receipt_hash=_canonical_hash(receipt_payload),
    )
