#!/usr/bin/env python3
"""Deterministic evidence producers for hard cognitive-envelope axes.

These monitors do not grant authority and do not replace EffectGate. They only translate
explicit, provenance-bound observations/contracts into typed evidence consumed by the
Cognitive Envelope heartbeat.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from grid10_cognitive_envelope_control_v1 import ProjectionPolicy
from grid10_cognitive_fabric_adapter_v1 import TrustedAxisEvidence


@dataclass(frozen=True)
class AuthorityObservation:
    canonical_state_authority_unique: bool | None
    effect_path_is_effectgate_only: bool | None
    capability_scope_not_self_granted: bool | None
    work_spec_revision_current: bool | None
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class ContainmentObservation:
    candidate_effect_risk: float | None
    allowed_effect_risk_ceiling: float | None
    tool_scope_valid: bool | None
    effect_scope_valid: bool | None
    reversible: bool | None
    rollback_ready: bool | None
    unknown_effect_fraction: float | None
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class GoalContract:
    goal_id: str
    revision: int
    immutable_constraints: FrozenSet[str]
    allowed_effect_scope: FrozenSet[str]
    allowed_resource_scope: FrozenSet[str]
    max_semantic_drift_per_revision: float
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class GoalRevisionObservation:
    goal_id: str
    parent_revision: int
    current_revision: int
    current_constraints: FrozenSet[str]
    requested_effect_scope: FrozenSet[str]
    requested_resource_scope: FrozenSet[str]
    measured_semantic_drift: float | None
    measurement_status: str
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class GoalMutationDecision:
    admitted: bool
    reasons: tuple[str, ...]
    goal_lineage_alignment: TrustedAxisEvidence
    goal_drift_rate: TrustedAxisEvidence


def authority_integrity_evidence(obs: AuthorityObservation) -> TrustedAxisEvidence:
    checks = (
        obs.canonical_state_authority_unique,
        obs.effect_path_is_effectgate_only,
        obs.capability_scope_not_self_granted,
        obs.work_spec_revision_current,
    )
    if any(x is None for x in checks):
        value = None
        status = "UNKNOWN"
        confidence = 0.0
    else:
        value = 1.0 if all(checks) else 0.0
        status = "VERIFIED" if obs.provenance else "UNVERIFIED"
        confidence = 1.0 if obs.provenance else 0.5
    return TrustedAxisEvidence(
        "authority_integrity", value, status, obs.provenance, confidence,
        ProjectionPolicy.PESSIMISTIC_MIN,
    )


def containment_margin_evidence(obs: ContainmentObservation) -> TrustedAxisEvidence:
    required = (
        obs.candidate_effect_risk,
        obs.allowed_effect_risk_ceiling,
        obs.tool_scope_valid,
        obs.effect_scope_valid,
        obs.reversible,
        obs.rollback_ready,
        obs.unknown_effect_fraction,
    )
    if any(x is None for x in required):
        return TrustedAxisEvidence(
            "containment_margin", None, "UNKNOWN", obs.provenance, 0.0,
            ProjectionPolicy.PESSIMISTIC_MIN,
        )
    candidate = max(0.0, min(1.0, float(obs.candidate_effect_risk)))
    ceiling = max(0.0, min(1.0, float(obs.allowed_effect_risk_ceiling)))
    unknown = max(0.0, min(1.0, float(obs.unknown_effect_fraction)))
    if ceiling <= 0:
        risk_margin = 1.0 if candidate <= 0 else 0.0
    else:
        risk_margin = max(0.0, min(1.0, (ceiling - candidate) / ceiling))
    scope_margin = 1.0 if bool(obs.tool_scope_valid) and bool(obs.effect_scope_valid) else 0.0
    reversibility_margin = 1.0 if bool(obs.reversible) and bool(obs.rollback_ready) else 0.35 if bool(obs.reversible) else 0.0
    margin = min(risk_margin, scope_margin, reversibility_margin, 1.0 - unknown)
    return TrustedAxisEvidence(
        "containment_margin", margin, "VERIFIED" if obs.provenance else "UNVERIFIED",
        obs.provenance, 1.0 if obs.provenance else 0.5, ProjectionPolicy.PESSIMISTIC_MIN,
    )


def evaluate_goal_mutation(contract: GoalContract, obs: GoalRevisionObservation) -> GoalMutationDecision:
    reasons: list[str] = []
    if contract.goal_id != obs.goal_id:
        reasons.append("GOAL_ID_MISMATCH")
    if obs.parent_revision != contract.revision:
        reasons.append("STALE_PARENT_REVISION")
    if not contract.immutable_constraints.issubset(obs.current_constraints):
        reasons.append("IMMUTABLE_CONSTRAINT_REMOVED")
    if not obs.requested_effect_scope.issubset(contract.allowed_effect_scope):
        reasons.append("EFFECT_SCOPE_BROADENED")
    if not obs.requested_resource_scope.issubset(contract.allowed_resource_scope):
        reasons.append("RESOURCE_SCOPE_BROADENED")

    drift = obs.measured_semantic_drift
    if drift is None or obs.measurement_status not in {"VERIFIED", "ADMITTED", "PASS"}:
        reasons.append("SEMANTIC_DRIFT_UNKNOWN")
        drift_ev = TrustedAxisEvidence(
            "goal_drift_rate", None, "UNKNOWN",
            contract.provenance + obs.provenance, 0.0, ProjectionPolicy.PESSIMISTIC_MAX,
        )
    else:
        drift = max(0.0, min(1.0, float(drift)))
        if drift > contract.max_semantic_drift_per_revision:
            reasons.append("SEMANTIC_DRIFT_LIMIT_EXCEEDED")
        drift_ev = TrustedAxisEvidence(
            "goal_drift_rate", drift, obs.measurement_status,
            contract.provenance + obs.provenance, 1.0, ProjectionPolicy.PESSIMISTIC_MAX,
        )

    structural_failures = {
        "GOAL_ID_MISMATCH", "STALE_PARENT_REVISION", "IMMUTABLE_CONSTRAINT_REMOVED",
        "EFFECT_SCOPE_BROADENED", "RESOURCE_SCOPE_BROADENED",
    }
    structure_ok = not any(r in structural_failures for r in reasons)
    if drift is None:
        align_value = None
        align_status = "UNKNOWN"
        align_conf = 0.0
    else:
        align_value = min(1.0 if structure_ok else 0.0, max(0.0, 1.0 - float(drift)))
        align_status = "VERIFIED" if contract.provenance and obs.provenance else "UNVERIFIED"
        align_conf = 1.0 if align_status == "VERIFIED" else 0.5

    alignment_ev = TrustedAxisEvidence(
        "goal_lineage_alignment", align_value, align_status,
        contract.provenance + obs.provenance, align_conf, ProjectionPolicy.PESSIMISTIC_MIN,
    )
    return GoalMutationDecision(
        admitted=not reasons,
        reasons=tuple(reasons) if reasons else ("GOAL_MUTATION_WITHIN_CONTRACT",),
        goal_lineage_alignment=alignment_ev,
        goal_drift_rate=drift_ev,
    )
