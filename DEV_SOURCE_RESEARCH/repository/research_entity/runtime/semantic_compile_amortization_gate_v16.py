from __future__ import annotations

"""Clay U16 read-plane compile amortization gate.

This controller never decides truth. It chooses whether a semantically equivalent derived
access field should be materialized or whether the already-valid online path should remain
in use. The decision is fail-conservative: if quality is worse, savings are non-positive,
or workload lifetime is unknown/too short, stay ONLINE.
"""

from dataclasses import dataclass
import math

@dataclass(frozen=True)
class CompileEconomics:
    build_cost_us: float
    online_query_us: float
    compiled_query_us: float
    online_quality: float
    compiled_quality: float
    expected_reads_before_invalidation: float
    safety_factor: float = 1.20

@dataclass(frozen=True)
class CompileDecision:
    mode: str
    break_even_reads: float | None
    guarded_break_even_reads: float | None
    expected_net_savings_us: float
    quality_delta: float
    reason: str
    authority: str = "PERFORMANCE_ROUTING_ONLY_NO_TRUTH_AUTHORITY"

def decide_compile(e: CompileEconomics) -> CompileDecision:
    vals=(e.build_cost_us,e.online_query_us,e.compiled_query_us,e.online_quality,
          e.compiled_quality,e.expected_reads_before_invalidation,e.safety_factor)
    if any(not math.isfinite(float(v)) for v in vals):
        raise ValueError('all compile economics values must be finite')
    if e.build_cost_us < 0 or e.online_query_us < 0 or e.compiled_query_us < 0:
        raise ValueError('costs must be non-negative')
    if e.expected_reads_before_invalidation < 0 or e.safety_factor < 1.0:
        raise ValueError('invalid workload lifetime or safety factor')
    quality_delta=e.compiled_quality-e.online_quality
    saving=e.online_query_us-e.compiled_query_us
    if quality_delta < 0:
        return CompileDecision('ONLINE',None,None,-e.build_cost_us,quality_delta,'COMPILED_QUALITY_WORSE')
    if saving <= 0:
        return CompileDecision('ONLINE',None,None,-e.build_cost_us,quality_delta,'NO_POSITIVE_QUERY_SAVING')
    raw=e.build_cost_us/saving if saving else None
    guarded=raw*e.safety_factor if raw is not None else None
    expected_net=e.expected_reads_before_invalidation*saving-e.build_cost_us*e.safety_factor
    if e.expected_reads_before_invalidation >= guarded:
        return CompileDecision('COMPILE',raw,guarded,expected_net,quality_delta,'EXPECTED_LIFETIME_AMORTIZES_BUILD')
    return CompileDecision('ONLINE',raw,guarded,expected_net,quality_delta,'EXPECTED_LIFETIME_BELOW_GUARDED_BREAK_EVEN')
