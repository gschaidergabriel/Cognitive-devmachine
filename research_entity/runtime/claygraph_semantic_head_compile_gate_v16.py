from __future__ import annotations

"""Correctness-first compile gate for ClayGraph semantic-access heads.

Strict latest-version semantics are always the correctness fallback. A derived head may be
materialized only after strict/head equality and ambiguity gates pass, and only when the
measured read lifetime amortizes its rebuild cost under U16 economics. This controller never
creates truth/effect authority; it selects a derived access representation.
"""

from dataclasses import dataclass

from semantic_compile_amortization_gate_v16 import CompileEconomics, decide_compile


@dataclass(frozen=True)
class SemanticHeadEvidence:
    rebuild_cost_us: float
    strict_query_us: float
    head_query_us: float
    expected_reads_before_invalidation: float
    strict_current_row_count: int
    head_current_row_count: int
    full_row_mismatch_count: int
    ambiguity_count: int
    safety_factor: float = 1.20


@dataclass(frozen=True)
class SemanticHeadDecision:
    mode: str
    break_even_reads: float | None
    guarded_break_even_reads: float | None
    expected_net_savings_us: float
    reason: str
    authority: str = 'DERIVED_ACCESS_ONLY_NO_TRUTH_AUTHORITY'


def decide_semantic_head(e: SemanticHeadEvidence) -> SemanticHeadDecision:
    if e.strict_current_row_count < 0 or e.head_current_row_count < 0:
        raise ValueError('row counts must be non-negative')
    if e.full_row_mismatch_count < 0 or e.ambiguity_count < 0:
        raise ValueError('mismatch/ambiguity counts must be non-negative')

    if e.ambiguity_count:
        return SemanticHeadDecision(
            'ONLINE_STRICT', None, None, -e.rebuild_cost_us, 'AMBIGUOUS_LATEST_VERSION_HEADS'
        )
    if e.strict_current_row_count != e.head_current_row_count or e.full_row_mismatch_count:
        return SemanticHeadDecision(
            'ONLINE_STRICT', None, None, -e.rebuild_cost_us, 'STRICT_HEAD_EQUIVALENCE_FAILED'
        )

    economics = decide_compile(
        CompileEconomics(
            build_cost_us=e.rebuild_cost_us,
            online_query_us=e.strict_query_us,
            compiled_query_us=e.head_query_us,
            online_quality=1.0,
            compiled_quality=1.0,
            expected_reads_before_invalidation=e.expected_reads_before_invalidation,
            safety_factor=e.safety_factor,
        )
    )
    return SemanticHeadDecision(
        'COMPILE_HEAD' if economics.mode == 'COMPILE' else 'ONLINE_STRICT',
        economics.break_even_reads,
        economics.guarded_break_even_reads,
        economics.expected_net_savings_us,
        economics.reason,
    )
