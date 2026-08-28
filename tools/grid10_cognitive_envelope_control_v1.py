#!/usr/bin/env python3
"""GRID10 Cognitive Envelope Control integration skeleton.

Research-candidate component only. This module intentionally does NOT write canonical
EntityOS state, does NOT bypass EffectGate, and does NOT claim whole-system alignment.
It provides deterministic, stdlib-only primitives for:

- Hyperposition-aware projection of uncertain cognitive variables;
- typed cognitive-envelope assessment;
- runtime-assurance mode selection;
- version/range validation for live regulator commands;
- completion-metric gating for executor/Claude work;
- delta-only follow-up directive construction;
- read-only CognitiveLoopFrame projection for a future visual twin.

The current GRID10 Fabric already has a CAS-safe regulators table. This module is the
policy/semantics layer intended to sit in front of that low-level primitive during
later integration.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import json
import math
import time
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "GRID10_COGNITIVE_ENVELOPE_CONTROL/v1"
LOOP_FRAME_SCHEMA = "COGNITIVE_LOOP_FRAME/v1"
COMPLETION_SCHEMA = "COGNITIVE_COMPLETION_VERDICT/v1"
DIRECTIVE_SCHEMA = "EXECUTOR_WORK_DIRECTIVE/v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class AssuranceMode(str, Enum):
    NORMAL = "NORMAL"
    CAUTION = "CAUTION"
    CONTAINED = "CONTAINED"
    HOLD = "HOLD"
    RECOVERY = "RECOVERY"


class EnvelopeStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    TARGET = "TARGET"
    SOFT_LOW = "SOFT_LOW"
    SOFT_HIGH = "SOFT_HIGH"
    HARD_LOW = "HARD_LOW"
    HARD_HIGH = "HARD_HIGH"


class ProjectionPolicy(str, Enum):
    EXPECTED = "EXPECTED"
    PESSIMISTIC_MIN = "PESSIMISTIC_MIN"
    PESSIMISTIC_MAX = "PESSIMISTIC_MAX"
    LOW_CONFIDENCE_BOUND = "LOW_CONFIDENCE_BOUND"
    HIGH_CONFIDENCE_BOUND = "HIGH_CONFIDENCE_BOUND"
    ENTROPY = "ENTROPY"
    KEEP_UNKNOWN = "KEEP_UNKNOWN"


@dataclass(frozen=True)
class Alternative:
    value: float | None
    confidence: float
    evidence_status: str
    provenance: tuple[str, ...] = ()
    label: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("alternative confidence must be in [0,1]")


@dataclass(frozen=True)
class HyperVariable:
    variable_id: str
    alternatives: tuple[Alternative, ...]
    projection_policy: ProjectionPolicy = ProjectionPolicy.EXPECTED


@dataclass(frozen=True)
class EnvelopeBand:
    """Typed operating envelope for one projected cognitive axis.

    Any bound may be None when that side is intentionally unconstrained. Target bands
    must live inside hard bounds if both are supplied.
    """

    axis: str
    target_min: float | None = None
    target_max: float | None = None
    soft_min: float | None = None
    soft_max: float | None = None
    hard_min: float | None = None
    hard_max: float | None = None
    max_abs_derivative: float | None = None
    hard_invariant: bool = False
    safety_relevant: bool = False
    unknown_response: AssuranceMode = AssuranceMode.CAUTION

    def __post_init__(self) -> None:
        pairs = [
            ("hard", self.hard_min, self.hard_max),
            ("soft", self.soft_min, self.soft_max),
            ("target", self.target_min, self.target_max),
        ]
        for name, lo, hi in pairs:
            if lo is not None and hi is not None and lo > hi:
                raise ValueError(f"{name} min > max for {self.axis}")
        if self.hard_min is not None and self.target_min is not None and self.target_min < self.hard_min:
            raise ValueError(f"target_min below hard_min for {self.axis}")
        if self.hard_max is not None and self.target_max is not None and self.target_max > self.hard_max:
            raise ValueError(f"target_max above hard_max for {self.axis}")


@dataclass(frozen=True)
class ProjectedValue:
    value: float | None
    uncertainty: float
    projection_policy: ProjectionPolicy
    source_alternatives: int
    evidence_statuses: tuple[str, ...]


@dataclass(frozen=True)
class AxisAssessment:
    axis: str
    projected: ProjectedValue
    status: EnvelopeStatus
    derivative: float | None
    derivative_violation: bool
    target_error: float | None
    hard_margin: float | None
    safety_relevant: bool
    hard_invariant: bool


@dataclass(frozen=True)
class CognitiveEnvelopeSnapshot:
    tick_id: str
    state_epoch: int
    assessments: tuple[AxisAssessment, ...]
    assurance_mode: AssuranceMode
    reasons: tuple[str, ...]

    @property
    def snapshot_digest(self) -> str:
        return digest(asdict(self))


@dataclass(frozen=True)
class RegulatorSpec:
    name: str
    regulator_class: str
    minimum: float
    maximum: float
    max_step: float | None
    default: float
    description: str


@dataclass(frozen=True)
class RegulatorCommand:
    name: str
    requested_value: float
    writer: str
    writer_role: str
    expected_version: int
    reason: str
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegulatorDecision:
    accepted: bool
    reason: str
    clamped_value: float | None = None


@dataclass(frozen=True)
class CompletionMetric:
    name: str
    required: bool
    threshold: float | bool | str
    comparator: str = "EQ"
    evidence_required: bool = True


@dataclass(frozen=True)
class CompletionObservation:
    name: str
    value: float | bool | str | None
    evidence_refs: tuple[str, ...] = ()
    evidence_status: str = "UNKNOWN"


@dataclass(frozen=True)
class CompletionDeficit:
    metric: str
    reason: str
    required: Any
    observed: Any


@dataclass(frozen=True)
class CompletionVerdict:
    schema: str
    work_id: str
    verified_complete: bool
    deficits: tuple[CompletionDeficit, ...]
    satisfied_metrics: tuple[str, ...]
    verdict_digest: str


@dataclass(frozen=True)
class ExecutorWorkDirective:
    schema: str
    work_id: str
    goal_id: str
    spec_revision: int
    exact_delta_to_do: tuple[str, ...]
    context_capsule_ref: str | None
    required_outputs: tuple[str, ...]
    completion_metrics: tuple[str, ...]
    allowed_write_scope: tuple[str, ...]
    allowed_tool_scope: tuple[str, ...]
    effect_scope: tuple[str, ...]
    max_context_tokens: int
    continuation_checkpoint_ref: str | None
    do_not_repeat_refs: tuple[str, ...]


@dataclass(frozen=True)
class ContextItem:
    ref: str
    section: str
    estimated_tokens: int
    priority: float
    provenance_status: str


@dataclass(frozen=True)
class TaskContextCapsule:
    goal_id: str
    work_id: str
    token_budget: int
    items: tuple[ContextItem, ...]
    omitted_refs: tuple[str, ...]

    @property
    def estimated_tokens(self) -> int:
        return sum(x.estimated_tokens for x in self.items)


@dataclass(frozen=True)
class LoopDescriptor:
    loop_id: str
    phase: str
    activation: float
    period_ms: float | None
    phase_progress: float | None
    stability: float | None
    participating_cells: tuple[str, ...] = ()
    causal_edge_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CognitiveLoopFrame:
    schema: str
    frame_id: str
    tick_id: str
    state_epoch: int
    timestamp: float
    assurance_mode: AssuranceMode
    loops: tuple[LoopDescriptor, ...]
    axes: Mapping[str, Mapping[str, Any]]
    regulators: Mapping[str, Mapping[str, Any]]
    hyperposition: Mapping[str, Any]
    work: Mapping[str, Any]
    source_event_refs: tuple[str, ...]
    source_digest: str


def _numeric_alternatives(h: HyperVariable) -> list[Alternative]:
    return [a for a in h.alternatives if a.value is not None and math.isfinite(float(a.value))]


def _normalized_weights(alts: Sequence[Alternative]) -> list[float]:
    if not alts:
        return []
    total = sum(max(0.0, a.confidence) for a in alts)
    if total <= 0:
        return [1.0 / len(alts)] * len(alts)
    return [max(0.0, a.confidence) / total for a in alts]


def project_hypervariable(h: HyperVariable) -> ProjectedValue:
    alts = _numeric_alternatives(h)
    statuses = tuple(sorted({a.evidence_status for a in h.alternatives}))
    if not alts:
        return ProjectedValue(None, 1.0, h.projection_policy, len(h.alternatives), statuses)

    values = [float(a.value) for a in alts]
    weights = _normalized_weights(alts)
    mean = sum(v * w for v, w in zip(values, weights))
    variance = sum(w * (v - mean) ** 2 for v, w in zip(values, weights))
    uncertainty = min(1.0, math.sqrt(variance))

    if h.projection_policy == ProjectionPolicy.PESSIMISTIC_MIN:
        value = min(values)
    elif h.projection_policy == ProjectionPolicy.PESSIMISTIC_MAX:
        value = max(values)
    elif h.projection_policy == ProjectionPolicy.LOW_CONFIDENCE_BOUND:
        value = mean - math.sqrt(variance)
    elif h.projection_policy == ProjectionPolicy.HIGH_CONFIDENCE_BOUND:
        value = mean + math.sqrt(variance)
    elif h.projection_policy == ProjectionPolicy.ENTROPY:
        entropy = -sum(w * math.log(max(w, 1e-12)) for w in weights)
        value = entropy / max(math.log(len(weights)), 1e-12) if len(weights) > 1 else 0.0
    elif h.projection_policy == ProjectionPolicy.KEEP_UNKNOWN:
        if any(a.value is None or a.evidence_status == "UNKNOWN" for a in h.alternatives):
            value = None
        else:
            value = mean
    else:
        value = mean

    return ProjectedValue(value, uncertainty, h.projection_policy, len(h.alternatives), statuses)


def _distance_to_target(value: float, band: EnvelopeBand) -> float:
    if band.target_min is not None and value < band.target_min:
        return value - band.target_min
    if band.target_max is not None and value > band.target_max:
        return value - band.target_max
    return 0.0


def _hard_margin(value: float, band: EnvelopeBand) -> float | None:
    margins = []
    if band.hard_min is not None:
        margins.append(value - band.hard_min)
    if band.hard_max is not None:
        margins.append(band.hard_max - value)
    return min(margins) if margins else None


def assess_axis(
    h: HyperVariable,
    band: EnvelopeBand,
    *,
    previous_projected_value: float | None = None,
    dt_ticks: float = 1.0,
) -> AxisAssessment:
    if h.variable_id != band.axis:
        raise ValueError(f"variable/band mismatch: {h.variable_id!r} != {band.axis!r}")
    projected = project_hypervariable(h)
    value = projected.value
    if value is None:
        return AxisAssessment(
            axis=band.axis,
            projected=projected,
            status=EnvelopeStatus.UNKNOWN,
            derivative=None,
            derivative_violation=False,
            target_error=None,
            hard_margin=None,
            safety_relevant=band.safety_relevant,
            hard_invariant=band.hard_invariant,
        )

    derivative = None
    if previous_projected_value is not None and dt_ticks > 0:
        derivative = (value - previous_projected_value) / dt_ticks

    derivative_violation = bool(
        derivative is not None
        and band.max_abs_derivative is not None
        and abs(derivative) > band.max_abs_derivative
    )

    if band.hard_min is not None and value < band.hard_min:
        status = EnvelopeStatus.HARD_LOW
    elif band.hard_max is not None and value > band.hard_max:
        status = EnvelopeStatus.HARD_HIGH
    elif band.soft_min is not None and value < band.soft_min:
        status = EnvelopeStatus.SOFT_LOW
    elif band.soft_max is not None and value > band.soft_max:
        status = EnvelopeStatus.SOFT_HIGH
    else:
        status = EnvelopeStatus.TARGET

    return AxisAssessment(
        axis=band.axis,
        projected=projected,
        status=status,
        derivative=derivative,
        derivative_violation=derivative_violation,
        target_error=_distance_to_target(value, band),
        hard_margin=_hard_margin(value, band),
        safety_relevant=band.safety_relevant,
        hard_invariant=band.hard_invariant,
    )


def select_assurance_mode(assessments: Iterable[AxisAssessment]) -> tuple[AssuranceMode, tuple[str, ...]]:
    """Conservative deterministic mode selection.

    This is deliberately not a learned policy. Later controller layers may propose
    smoother actuator moves, but hard/safety failures dominate task utility.
    """
    rows = tuple(assessments)
    reasons: list[str] = []

    # Hard invariant ambiguity/violation gets the strongest response.
    for a in rows:
        if a.hard_invariant and a.status in {EnvelopeStatus.HARD_LOW, EnvelopeStatus.HARD_HIGH}:
            reasons.append(f"hard invariant outside envelope: {a.axis}")
            return AssuranceMode.HOLD, tuple(reasons)
        if a.hard_invariant and a.status == EnvelopeStatus.UNKNOWN:
            reasons.append(f"hard invariant unknown: {a.axis}")
            return AssuranceMode.HOLD, tuple(reasons)

    # Safety-relevant hard bound violation narrows operation even if task metrics are good.
    hard_safety = [
        a.axis for a in rows
        if a.safety_relevant and a.status in {EnvelopeStatus.HARD_LOW, EnvelopeStatus.HARD_HIGH}
    ]
    if hard_safety:
        reasons.extend(f"safety hard bound: {x}" for x in hard_safety)
        return AssuranceMode.CONTAINED, tuple(reasons)

    unknown_safety = [a.axis for a in rows if a.safety_relevant and a.status == EnvelopeStatus.UNKNOWN]
    if unknown_safety:
        reasons.extend(f"safety axis unknown: {x}" for x in unknown_safety)
        return AssuranceMode.CONTAINED, tuple(reasons)

    hard_nonsafety = [
        a.axis for a in rows
        if a.status in {EnvelopeStatus.HARD_LOW, EnvelopeStatus.HARD_HIGH}
    ]
    if hard_nonsafety:
        reasons.extend(f"hard cognitive bound: {x}" for x in hard_nonsafety)
        return AssuranceMode.CAUTION, tuple(reasons)

    derivative_violations = [a.axis for a in rows if a.derivative_violation]
    soft = [a.axis for a in rows if a.status in {EnvelopeStatus.SOFT_LOW, EnvelopeStatus.SOFT_HIGH}]
    if derivative_violations or soft:
        reasons.extend(f"drift limit: {x}" for x in derivative_violations)
        reasons.extend(f"soft envelope: {x}" for x in soft)
        return AssuranceMode.CAUTION, tuple(reasons)

    return AssuranceMode.NORMAL, ("all assessed axes inside configured operating envelope",)


def evaluate_envelope(
    *,
    tick_id: str,
    state_epoch: int,
    variables: Mapping[str, HyperVariable],
    bands: Mapping[str, EnvelopeBand],
    previous_projected: Mapping[str, float] | None = None,
    dt_ticks: float = 1.0,
) -> CognitiveEnvelopeSnapshot:
    previous_projected = previous_projected or {}
    assessments: list[AxisAssessment] = []
    for axis in sorted(bands):
        h = variables.get(axis)
        if h is None:
            h = HyperVariable(
                variable_id=axis,
                alternatives=(Alternative(None, 0.0, "UNKNOWN"),),
                projection_policy=ProjectionPolicy.KEEP_UNKNOWN,
            )
        assessments.append(
            assess_axis(
                h,
                bands[axis],
                previous_projected_value=previous_projected.get(axis),
                dt_ticks=dt_ticks,
            )
        )
    mode, reasons = select_assurance_mode(assessments)
    return CognitiveEnvelopeSnapshot(tick_id, state_epoch, tuple(assessments), mode, reasons)


# Candidate metadata only. These bounds are engineering placeholders for integration
# testing; they are NOT empirically calibrated safety guarantees.
DEFAULT_REGULATOR_CATALOG: dict[str, RegulatorSpec] = {
    "cog.temperature": RegulatorSpec("cog.temperature", "L3_ACTUATOR", 0.1, 2.0, 0.15, 0.85, "model sampling temperature"),
    "cog.top_p": RegulatorSpec("cog.top_p", "L3_ACTUATOR", 0.5, 1.0, 0.05, 0.92, "model nucleus-sampling mass"),
    "cog.poll_intensity": RegulatorSpec("cog.poll_intensity", "L3_ACTUATOR", 0.05, 4.0, 0.5, 1.0, "GRID10 polling/work cadence"),
    "cog.max_reflection_rounds": RegulatorSpec("cog.max_reflection_rounds", "L3_ACTUATOR", 1.0, 32.0, 4.0, 8.0, "maximum recursive reasoning rounds without progress checkpoint"),
    "cog.route_diversity_target": RegulatorSpec("cog.route_diversity_target", "L2_SETPOINT", 0.0, 1.0, 0.1, 0.5, "desired route/hypothesis diversity"),
    "cog.workspace_ignition_threshold": RegulatorSpec("cog.workspace_ignition_threshold", "L3_ACTUATOR", 0.0, 1.0, 0.1, 0.5, "GWT selection/ignition candidate threshold"),
    "cog.counterhypothesis_pressure": RegulatorSpec("cog.counterhypothesis_pressure", "L2_SETPOINT", 0.0, 1.0, 0.1, 0.5, "pressure to generate discriminating alternatives"),
    "goal.adoption_threshold": RegulatorSpec("goal.adoption_threshold", "L2_SETPOINT", 0.0, 1.0, 0.1, 0.65, "minimum evidence/utility gate for adopting self-generated goals"),
    "goal.max_drift_per_tick": RegulatorSpec("goal.max_drift_per_tick", "L1_ENVELOPE", 0.0, 1.0, 0.05, 0.08, "maximum admitted goal-semantic drift per tick"),
    "goal.initiative_ceiling": RegulatorSpec("goal.initiative_ceiling", "L1_ENVELOPE", 0.0, 0.12, 0.02, 0.12, "autotelic initiative-pulse ceiling inherited from current agency directive"),
    "goal.concurrent_active_limit": RegulatorSpec("goal.concurrent_active_limit", "L2_SETPOINT", 1.0, 32.0, 2.0, 4.0, "maximum concurrently active goals"),
    "goal.progress_evidence_min": RegulatorSpec("goal.progress_evidence_min", "L2_SETPOINT", 0.0, 1.0, 0.1, 0.65, "minimum evidence quality for material progress promotion"),
    "hyper.max_branches_per_variable": RegulatorSpec("hyper.max_branches_per_variable", "L3_ACTUATOR", 1.0, 64.0, 4.0, 8.0, "resource bound for unresolved alternatives"),
    "hyper.collapse_confidence_min": RegulatorSpec("hyper.collapse_confidence_min", "L2_SETPOINT", 0.0, 1.0, 0.05, 0.8, "minimum confidence candidate for non-safety branch collapse"),
    "hyper.branch_persistence_ticks": RegulatorSpec("hyper.branch_persistence_ticks", "L3_ACTUATOR", 1.0, 1000.0, 50.0, 20.0, "how long unresolved branches persist without new evidence"),
    "memory.context_token_budget": RegulatorSpec("memory.context_token_budget", "L2_SETPOINT", 256.0, 131072.0, 4096.0, 8192.0, "maximum executor context capsule budget"),
    "memory.max_items": RegulatorSpec("memory.max_items", "L3_ACTUATOR", 1.0, 512.0, 32.0, 64.0, "maximum retrieved memory items"),
    "memory.semantic_threshold": RegulatorSpec("memory.semantic_threshold", "L3_ACTUATOR", 0.0, 1.0, 0.05, 0.55, "minimum semantic relevance candidate"),
    "memory.causal_depth": RegulatorSpec("memory.causal_depth", "L3_ACTUATOR", 0.0, 32.0, 2.0, 4.0, "maximum causal-lineage traversal depth"),
    "memory.counterevidence_quota": RegulatorSpec("memory.counterevidence_quota", "L2_SETPOINT", 0.0, 1.0, 0.1, 0.2, "context fraction reserved for relevant counterevidence"),
    "memory.unresolved_branch_quota": RegulatorSpec("memory.unresolved_branch_quota", "L2_SETPOINT", 0.0, 1.0, 0.1, 0.25, "context fraction reserved for unresolved Hyperposition branches"),
    "memory.dedupe_similarity_ceiling": RegulatorSpec("memory.dedupe_similarity_ceiling", "L3_ACTUATOR", 0.0, 1.0, 0.05, 0.92, "deduplicate near-identical memory items"),
    "exec.max_parallel_work": RegulatorSpec("exec.max_parallel_work", "L2_SETPOINT", 1.0, 64.0, 2.0, 4.0, "parallel bounded work revisions"),
    "exec.continuation_bias": RegulatorSpec("exec.continuation_bias", "L2_SETPOINT", 0.0, 1.0, 0.1, 0.8, "prefer continuing valid checkpoint over fresh restart"),
    "exec.max_replan_without_new_evidence": RegulatorSpec("exec.max_replan_without_new_evidence", "L1_ENVELOPE", 0.0, 16.0, 1.0, 2.0, "limit repeated replanning without material evidence delta"),
    "exec.completion_metric_threshold": RegulatorSpec("exec.completion_metric_threshold", "L2_SETPOINT", 0.0, 1.0, 0.05, 1.0, "fraction of mandatory metrics required before completion"),
    "contain.external_action_concurrency": RegulatorSpec("contain.external_action_concurrency", "L1_ENVELOPE", 0.0, 32.0, 1.0, 1.0, "external-effect concurrency ceiling"),
    "contain.effect_risk_ceiling": RegulatorSpec("contain.effect_risk_ceiling", "L1_ENVELOPE", 0.0, 1.0, 0.05, 0.25, "risk ceiling; mapping to effect classes is policy-specific"),
    "contain.required_margin": RegulatorSpec("contain.required_margin", "L1_ENVELOPE", 0.0, 1.0, 0.05, 0.8, "minimum desired containment margin"),
}


def validate_regulator_command(
    command: RegulatorCommand,
    current_value: float,
    current_version: int,
    *,
    assurance_mode: AssuranceMode,
    catalog: Mapping[str, RegulatorSpec] = DEFAULT_REGULATOR_CATALOG,
) -> RegulatorDecision:
    spec = catalog.get(command.name)
    if spec is None:
        return RegulatorDecision(False, "UNKNOWN_REGULATOR")
    if command.expected_version != current_version:
        return RegulatorDecision(False, "REGULATOR_CAS_FAILED")
    if not command.reason.strip():
        return RegulatorDecision(False, "MISSING_REASON")
    if not spec.minimum <= command.requested_value <= spec.maximum:
        return RegulatorDecision(False, "OUTSIDE_POLICY_RANGE")
    if spec.regulator_class == "L1_ENVELOPE" and command.writer_role not in {"ADMIN_POLICY", "ASSURANCE_CONTROLLER"}:
        return RegulatorDecision(False, "L1_WRITE_REQUIRES_POLICY_AUTHORITY")
    if assurance_mode == AssuranceMode.HOLD and command.writer_role not in {"ADMIN_POLICY", "ASSURANCE_CONTROLLER"}:
        return RegulatorDecision(False, "HOLD_MODE_RESTRICTS_WRITES")
    if spec.max_step is not None and abs(command.requested_value - current_value) > spec.max_step:
        return RegulatorDecision(False, "SLEW_RATE_EXCEEDED")
    return RegulatorDecision(True, "ACCEPT", command.requested_value)


def _compare(observed: Any, required: Any, comparator: str) -> bool:
    if comparator == "EQ":
        return observed == required
    if comparator == "GE":
        return observed is not None and float(observed) >= float(required)
    if comparator == "GT":
        return observed is not None and float(observed) > float(required)
    if comparator == "LE":
        return observed is not None and float(observed) <= float(required)
    if comparator == "LT":
        return observed is not None and float(observed) < float(required)
    if comparator == "IN":
        return observed in required
    raise ValueError(f"unknown comparator: {comparator}")


def evaluate_completion(
    work_id: str,
    metrics: Sequence[CompletionMetric],
    observations: Sequence[CompletionObservation],
) -> CompletionVerdict:
    by_name = {x.name: x for x in observations}
    deficits: list[CompletionDeficit] = []
    satisfied: list[str] = []

    for metric in metrics:
        obs = by_name.get(metric.name)
        if obs is None:
            if metric.required:
                deficits.append(CompletionDeficit(metric.name, "MISSING_OBSERVATION", metric.threshold, None))
            continue
        if metric.evidence_required and not obs.evidence_refs:
            deficits.append(CompletionDeficit(metric.name, "MISSING_EVIDENCE", metric.threshold, obs.value))
            continue
        if metric.evidence_required and obs.evidence_status not in {"VERIFIED", "ADMITTED", "PASS"}:
            deficits.append(CompletionDeficit(metric.name, f"EVIDENCE_NOT_VERIFIED:{obs.evidence_status}", metric.threshold, obs.value))
            continue
        if not _compare(obs.value, metric.threshold, metric.comparator):
            deficits.append(CompletionDeficit(metric.name, "THRESHOLD_NOT_MET", metric.threshold, obs.value))
            continue
        satisfied.append(metric.name)

    verified_complete = not any(d for d in deficits if next((m.required for m in metrics if m.name == d.metric), True))
    body = {
        "schema": COMPLETION_SCHEMA,
        "work_id": work_id,
        "verified_complete": verified_complete,
        "deficits": [asdict(d) for d in deficits],
        "satisfied_metrics": sorted(satisfied),
    }
    return CompletionVerdict(
        schema=COMPLETION_SCHEMA,
        work_id=work_id,
        verified_complete=verified_complete,
        deficits=tuple(deficits),
        satisfied_metrics=tuple(sorted(satisfied)),
        verdict_digest=digest(body),
    )


def build_delta_directive(
    *,
    work_id: str,
    goal_id: str,
    spec_revision: int,
    verdict: CompletionVerdict,
    context_capsule_ref: str | None,
    allowed_write_scope: Sequence[str],
    allowed_tool_scope: Sequence[str],
    effect_scope: Sequence[str],
    max_context_tokens: int,
    continuation_checkpoint_ref: str | None,
    do_not_repeat_refs: Sequence[str] = (),
) -> ExecutorWorkDirective:
    if verdict.verified_complete:
        raise ValueError("cannot build a deficit directive for verified-complete work")
    deltas = tuple(
        f"Close completion deficit {d.metric}: {d.reason}; required={d.required!r}; observed={d.observed!r}"
        for d in verdict.deficits
    )
    return ExecutorWorkDirective(
        schema=DIRECTIVE_SCHEMA,
        work_id=work_id,
        goal_id=goal_id,
        spec_revision=spec_revision,
        exact_delta_to_do=deltas,
        context_capsule_ref=context_capsule_ref,
        required_outputs=tuple(d.metric for d in verdict.deficits),
        completion_metrics=tuple(d.metric for d in verdict.deficits),
        allowed_write_scope=tuple(allowed_write_scope),
        allowed_tool_scope=tuple(allowed_tool_scope),
        effect_scope=tuple(effect_scope),
        max_context_tokens=max_context_tokens,
        continuation_checkpoint_ref=continuation_checkpoint_ref,
        do_not_repeat_refs=tuple(do_not_repeat_refs),
    )


def compile_context_capsule(
    *,
    goal_id: str,
    work_id: str,
    token_budget: int,
    candidates: Sequence[ContextItem],
) -> TaskContextCapsule:
    """Deterministic bounded selector for already-ranked context candidates.

    Final retrieval will use UnifiedDB/ClayGraph/Hyperposition. This helper proves the
    downstream token-budget boundary and explicit omission behavior without inventing
    a competing memory store.
    """
    if token_budget <= 0:
        raise ValueError("token_budget must be positive")
    ordered = sorted(candidates, key=lambda x: (-x.priority, x.estimated_tokens, x.ref))
    used = 0
    kept: list[ContextItem] = []
    omitted: list[str] = []
    for item in ordered:
        if item.estimated_tokens < 0:
            raise ValueError("estimated_tokens must be nonnegative")
        if used + item.estimated_tokens <= token_budget:
            kept.append(item)
            used += item.estimated_tokens
        else:
            omitted.append(item.ref)
    return TaskContextCapsule(goal_id, work_id, token_budget, tuple(kept), tuple(omitted))


def build_loop_frame(
    *,
    tick_id: str,
    state_epoch: int,
    assurance_mode: AssuranceMode,
    loops: Sequence[LoopDescriptor],
    envelope: CognitiveEnvelopeSnapshot,
    regulators: Mapping[str, Mapping[str, Any]],
    hyperposition: Mapping[str, Any],
    work: Mapping[str, Any],
    source_event_refs: Sequence[str],
    timestamp: float | None = None,
) -> CognitiveLoopFrame:
    """Build a read-only deterministic projection from the same signal state.

    The frame ID is content-addressed over all deterministic fields. Timestamp is kept
    outside the source digest so replay can reproduce the same semantic frame even when
    rendered later.
    """
    axes: dict[str, dict[str, Any]] = {}
    for a in envelope.assessments:
        axes[a.axis] = {
            "alternatives": a.projected.source_alternatives,
            "projected_value": a.projected.value,
            "uncertainty": a.projected.uncertainty,
            "projection_policy": a.projected.projection_policy.value,
            "status": a.status.value,
            "derivative": a.derivative,
            "controller_error": a.target_error,
            "hard_margin": a.hard_margin,
            "safety_relevant": a.safety_relevant,
        }

    source_body = {
        "tick_id": tick_id,
        "state_epoch": state_epoch,
        "assurance_mode": assurance_mode.value,
        "loops": [asdict(x) for x in loops],
        "axes": axes,
        "regulators": regulators,
        "hyperposition": hyperposition,
        "work": work,
        "source_event_refs": list(source_event_refs),
    }
    source_digest = digest(source_body)
    frame_id = "clf-" + source_digest[:24]
    return CognitiveLoopFrame(
        schema=LOOP_FRAME_SCHEMA,
        frame_id=frame_id,
        tick_id=tick_id,
        state_epoch=state_epoch,
        timestamp=time.time() if timestamp is None else timestamp,
        assurance_mode=assurance_mode,
        loops=tuple(loops),
        axes=axes,
        regulators=dict(regulators),
        hyperposition=dict(hyperposition),
        work=dict(work),
        source_event_refs=tuple(source_event_refs),
        source_digest=source_digest,
    )


def frame_to_json(frame: CognitiveLoopFrame) -> str:
    data = asdict(frame)
    data["assurance_mode"] = frame.assurance_mode.value
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)


# Candidate initial envelope bands. These values are placeholders for integration tests
# and MUST be calibrated against real traces before any runtime-assurance promotion.
DEFAULT_ENVELOPE_BANDS: dict[str, EnvelopeBand] = {
    "authority_integrity": EnvelopeBand(
        "authority_integrity", target_min=1.0, soft_min=1.0, hard_min=1.0,
        hard_invariant=True, safety_relevant=True,
    ),
    "goal_lineage_alignment": EnvelopeBand(
        "goal_lineage_alignment", target_min=0.9, soft_min=0.8, hard_min=0.6,
        max_abs_derivative=0.15, safety_relevant=True,
    ),
    "goal_drift_rate": EnvelopeBand(
        "goal_drift_rate", target_max=0.08, soft_max=0.15, hard_max=0.30,
        max_abs_derivative=0.10, safety_relevant=True,
    ),
    "containment_margin": EnvelopeBand(
        "containment_margin", target_min=0.85, soft_min=0.70, hard_min=0.50,
        max_abs_derivative=0.15, safety_relevant=True,
    ),
    "epistemic_grounding": EnvelopeBand(
        "epistemic_grounding", target_min=0.75, soft_min=0.60, hard_min=0.35,
        max_abs_derivative=0.20, safety_relevant=True,
    ),
    "self_reinforcement_ratio": EnvelopeBand(
        "self_reinforcement_ratio", target_max=0.15, soft_max=0.25, hard_max=0.45,
        max_abs_derivative=0.15, safety_relevant=True,
    ),
    "autonomy_intensity": EnvelopeBand(
        "autonomy_intensity", target_min=0.10, target_max=0.70, soft_max=0.85, hard_max=1.0,
        max_abs_derivative=0.20,
    ),
    "exploration_pressure": EnvelopeBand(
        "exploration_pressure", target_min=0.20, target_max=0.70, soft_max=0.85, hard_max=1.0,
        max_abs_derivative=0.20,
    ),
    "reflection_depth": EnvelopeBand(
        "reflection_depth", target_max=0.60, soft_max=0.80, hard_max=1.0,
        max_abs_derivative=0.25,
    ),
    "stagnation_pressure": EnvelopeBand(
        "stagnation_pressure", target_max=0.40, soft_max=0.65, hard_max=0.90,
        max_abs_derivative=0.20,
    ),
    "retrieval_load": EnvelopeBand(
        "retrieval_load", target_max=0.60, soft_max=0.80, hard_max=1.0,
        max_abs_derivative=0.25,
    ),
    "retrieval_relevance": EnvelopeBand(
        "retrieval_relevance", target_min=0.70, soft_min=0.50, hard_min=0.20,
        max_abs_derivative=0.25,
    ),
    "resource_pressure": EnvelopeBand(
        "resource_pressure", target_max=0.65, soft_max=0.80, hard_max=0.95,
        max_abs_derivative=0.20, safety_relevant=True,
    ),
    "recovery_margin": EnvelopeBand(
        "recovery_margin", target_min=0.80, soft_min=0.60, hard_min=0.30,
        max_abs_derivative=0.25, safety_relevant=True,
    ),
}


if __name__ == "__main__":
    # Tiny deterministic smoke example, not a runtime acceptance test.
    variables = {
        "authority_integrity": HyperVariable(
            "authority_integrity",
            (Alternative(1.0, 1.0, "VERIFIED", ("demo",)),),
            ProjectionPolicy.PESSIMISTIC_MIN,
        ),
        "containment_margin": HyperVariable(
            "containment_margin",
            (
                Alternative(0.9, 0.8, "VERIFIED", ("demo:a",)),
                Alternative(0.65, 0.2, "INFERRED", ("demo:b",)),
            ),
            ProjectionPolicy.PESSIMISTIC_MIN,
        ),
    }
    snapshot = evaluate_envelope(
        tick_id="demo-tick",
        state_epoch=1,
        variables=variables,
        bands={k: DEFAULT_ENVELOPE_BANDS[k] for k in ("authority_integrity", "containment_margin")},
    )
    print(json.dumps({
        "schema": SCHEMA,
        "mode": snapshot.assurance_mode.value,
        "reasons": snapshot.reasons,
        "digest": snapshot.snapshot_digest,
    }, indent=2))
