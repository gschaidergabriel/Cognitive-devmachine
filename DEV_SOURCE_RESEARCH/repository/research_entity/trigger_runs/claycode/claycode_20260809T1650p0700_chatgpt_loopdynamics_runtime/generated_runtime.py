from dataclasses import dataclass

@dataclass
class Readout:
    loop_id: str
    state_delta: float
    residual_pressure: float
    recurrence_count: int
    recurrence_budget: int
    convergence_rate: float
    period: float | None
    marginal_utility: float
    compute_cost: float
    bounded: bool
    residual_trend: float
    delta_trend: float

def classify(r):
    if r.marginal_utility < -0.02 or r.residual_trend > 0.025 or r.delta_trend > 0.025:
        return ("DIVERGING_OR_OVERTHINKING","ESCALATE","negative_utility_or_growth")
    if r.state_delta < 0.035 and r.residual_pressure > 0.30:
        return ("STALLED","ESCALATE","low_delta_high_pressure")
    if r.state_delta < 0.035 and r.residual_pressure < 0.15 and r.residual_trend <= 0.005:
        return ("CONVERGING_FIXED_POINT","HALT","low_delta_low_pressure")
    if r.period is not None and r.bounded and r.marginal_utility > r.compute_cost:
        if r.recurrence_count < r.recurrence_budget:
            return ("PRODUCTIVE_LIMIT_CYCLE","CONTINUE","bounded_periodic_positive_utility")
        return ("PRODUCTIVE_LIMIT_CYCLE","ROUTE","budget_reached_preserve_cycle_class")
    return ("CHAOTIC_OR_UNCLASSIFIED","ROUTE","insufficient_regime_evidence")

def scalar_baseline(r):
    if r.state_delta < 0.035:
        return ("CONVERGING_FIXED_POINT","HALT")
    if r.period is not None:
        return ("DIVERGING_OR_OVERTHINKING","HALT")
    if r.recurrence_count >= r.recurrence_budget:
        return ("CHAOTIC_OR_UNCLASSIFIED","HALT")
    return ("CHAOTIC_OR_UNCLASSIFIED","CONTINUE")
