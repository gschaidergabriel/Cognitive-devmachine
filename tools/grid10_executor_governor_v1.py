#!/usr/bin/env python3
"""Completion- and context-governed executor/Claude boundary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Any

from grid10_cognitive_envelope_control_v1 import (
    CompletionMetric,
    CompletionObservation,
    ContextItem,
    ExecutorWorkDirective,
    TaskContextCapsule,
    build_delta_directive,
    compile_context_capsule,
    evaluate_completion,
)


@dataclass(frozen=True)
class GovernedWorkContract:
    work_id: str
    goal_id: str
    spec_revision: int
    completion_metrics: tuple[CompletionMetric, ...]
    allowed_write_scope: tuple[str, ...]
    allowed_tool_scope: tuple[str, ...]
    effect_scope: tuple[str, ...]
    context_token_budget: int
    continuation_checkpoint_ref: str | None
    do_not_repeat_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutorMetricReport:
    value: Any
    evidence_refs: tuple[str, ...]
    evidence_status: str


@dataclass(frozen=True)
class ExecutorResultReport:
    work_id: str
    spec_revision: int
    claimed_status: str
    metrics: Mapping[str, ExecutorMetricReport]
    changed_refs: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()


@dataclass(frozen=True)
class GovernedExecutorDecision:
    status: str
    claimed_status: str
    verified_complete: bool
    deficits: tuple[str, ...]
    context_capsule: TaskContextCapsule | None
    continuation_directive: ExecutorWorkDirective | None
    reason: str


def evaluate_executor_result(
    contract: GovernedWorkContract,
    result: ExecutorResultReport,
    *,
    context_candidates: Sequence[ContextItem] = (),
) -> GovernedExecutorDecision:
    """Treat executor DONE as a proposal and independently evaluate the contract."""
    if result.work_id != contract.work_id:
        return GovernedExecutorDecision(
            "REJECTED", result.claimed_status, False, (), None, None, "WORK_ID_MISMATCH"
        )
    if result.spec_revision != contract.spec_revision:
        return GovernedExecutorDecision(
            "STALE_RESULT", result.claimed_status, False, (), None, None,
            "SPEC_REVISION_MISMATCH_REVALIDATE_BEFORE_MORE_WORK",
        )

    observations = tuple(
        CompletionObservation(
            name=name,
            value=report.value,
            evidence_refs=report.evidence_refs,
            evidence_status=report.evidence_status,
        )
        for name, report in sorted(result.metrics.items())
    )
    verdict = evaluate_completion(contract.work_id, contract.completion_metrics, observations)
    if verdict.verified_complete:
        return GovernedExecutorDecision(
            "VERIFIED_COMPLETE",
            result.claimed_status,
            True,
            (),
            None,
            None,
            "ALL_MANDATORY_COMPLETION_METRICS_VERIFIED",
        )

    capsule = compile_context_capsule(
        goal_id=contract.goal_id,
        work_id=contract.work_id,
        token_budget=contract.context_token_budget,
        candidates=context_candidates,
    )
    directive = build_delta_directive(
        work_id=contract.work_id,
        goal_id=contract.goal_id,
        spec_revision=contract.spec_revision,
        verdict=verdict,
        context_capsule_ref=f"context:{contract.work_id}:{contract.spec_revision}",
        allowed_write_scope=contract.allowed_write_scope,
        allowed_tool_scope=contract.allowed_tool_scope,
        effect_scope=contract.effect_scope,
        max_context_tokens=contract.context_token_budget,
        continuation_checkpoint_ref=contract.continuation_checkpoint_ref,
        do_not_repeat_refs=contract.do_not_repeat_refs + tuple(result.changed_refs),
    )
    deficits = tuple(d.metric for d in verdict.deficits)
    return GovernedExecutorDecision(
        "CONTINUE_DELTA_ONLY",
        result.claimed_status,
        False,
        deficits,
        capsule,
        directive,
        "EXECUTOR_CLAIM_IS_NONAUTHORITATIVE; COMPLETION_DEFICITS_REMAIN",
    )
