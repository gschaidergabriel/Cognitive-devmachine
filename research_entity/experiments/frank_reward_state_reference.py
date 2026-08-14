from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from math import sqrt
from typing import Dict, List, Mapping, Tuple
import copy


class RewardDimension(str, Enum):
    TASK = "task"
    EPISTEMIC = "epistemic"
    SOCIAL = "social"
    SAFETY = "safety"
    RESOURCE = "resource"
    HOMEOSTATIC = "homeostatic"
    NOVELTY = "novelty"


class EvidenceClass(str, Enum):
    VERIFIED_OUTCOME = "verified_outcome"
    VERIFIED_USER_FEEDBACK = "verified_user_feedback"
    VERIFIED_EPISTEMIC = "verified_epistemic"
    SELF_PROPOSAL = "self_proposal"
    ACTIVITY_ONLY = "activity_only"
    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class RewardOutcomeEvidence:
    episode_id: str
    outcome_id: str
    dimension: RewardDimension
    utility: float
    confidence: float
    causal_credit: float
    evidence_class: EvidenceClass
    verified: bool
    source_ref: str
    novelty: float = 0.0


@dataclass
class HorizonPrediction:
    mean: float = 0.0
    variance: float = 0.25


@dataclass
class DimensionState:
    predictions: Dict[str, HorizonPrediction] = field(default_factory=lambda: {
        "fast": HorizonPrediction(),
        "medium": HorizonPrediction(),
        "slow": HorizonPrediction(),
    })
    habituation: float = 0.0
    tonic: float = 0.0
    opponent: float = 0.0
    last_value: float = 0.0
    last_phasic: float = 0.0
    admitted_events: int = 0


@dataclass
class RewardState:
    dimensions: Dict[RewardDimension, DimensionState] = field(default_factory=lambda: {
        d: DimensionState() for d in RewardDimension
    })
    event_count: int = 0
    recent_admitted_dimensions: List[RewardDimension] = field(default_factory=list)
    recent_abs_phasic: List[float] = field(default_factory=list)


@dataclass(frozen=True)
class RewardPlasticityReceipt:
    episode_id: str
    outcome_id: str
    dimension: RewardDimension
    admitted: bool
    material_learning_weight: float
    exploration_nudge: float
    observed_value: float
    predicted_fast_before: float
    predicted_medium_before: float
    predicted_slow_before: float
    phasic_by_horizon: Mapping[str, float]
    phasic_aggregate: float
    tonic_after: float
    habituation_after: float
    reason: str
    provenance: Tuple[str, ...]


@dataclass(frozen=True)
class RewardControlReadout:
    persistence_bias: float
    disengagement_bias: float
    exploration_nudge: float
    stagnation_candidate: bool
    safety_veto: bool
    resource_brake: bool
    typed_tonic: Mapping[str, float]


class RewardKernel:
    """Executable research candidate for the FRANK reward-state successor.

    This is deliberately a research reference, not H1/H2/H3 runtime authority.
    Material plasticity requires verified outcome evidence and causal credit.
    """

    HORIZON_ALPHA = {"fast": 0.30, "medium": 0.09, "slow": 0.02}
    VAR_ALPHA = {"fast": 0.18, "medium": 0.06, "slow": 0.015}
    HORIZON_MIX = {"fast": 0.55, "medium": 0.30, "slow": 0.15}

    TONIC_ALPHA = {
        RewardDimension.TASK: 0.08,
        RewardDimension.EPISTEMIC: 0.06,
        RewardDimension.SOCIAL: 0.035,
        RewardDimension.SAFETY: 0.10,
        RewardDimension.RESOURCE: 0.08,
        RewardDimension.HOMEOSTATIC: 0.06,
        RewardDimension.NOVELTY: 0.02,
    }

    MATERIAL_CLASSES = {
        EvidenceClass.VERIFIED_OUTCOME,
        EvidenceClass.VERIFIED_USER_FEEDBACK,
        EvidenceClass.VERIFIED_EPISTEMIC,
    }

    def __init__(self, *, habituation_enabled: bool = True, opponent_enabled: bool = True):
        self.state = RewardState()
        self.habituation_enabled = habituation_enabled
        self.opponent_enabled = opponent_enabled

    @staticmethod
    def _clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, float(x)))

    def _material_weight(self, e: RewardOutcomeEvidence) -> float:
        if not e.verified or e.evidence_class not in self.MATERIAL_CLASSES:
            return 0.0
        return self._clip(e.confidence, 0.0, 1.0) * self._clip(e.causal_credit, 0.0, 1.0)

    def _exploration_nudge(self, e: RewardOutcomeEvidence) -> float:
        n = self._clip(e.novelty, 0.0, 1.0)
        if e.evidence_class in {EvidenceClass.SELF_PROPOSAL, EvidenceClass.ACTIVITY_ONLY, EvidenceClass.UNVERIFIED}:
            return min(0.12, 0.12 * n)
        return min(0.08, 0.08 * n)

    def observe(self, e: RewardOutcomeEvidence) -> RewardPlasticityReceipt:
        ds = self.state.dimensions[e.dimension]
        weight = self._material_weight(e)
        exploration = self._exploration_nudge(e)
        before = {h: ds.predictions[h].mean for h in self.HORIZON_ALPHA}

        if weight <= 0.0:
            self.state.event_count += 1
            return RewardPlasticityReceipt(
                episode_id=e.episode_id,
                outcome_id=e.outcome_id,
                dimension=e.dimension,
                admitted=False,
                material_learning_weight=0.0,
                exploration_nudge=exploration,
                observed_value=0.0,
                predicted_fast_before=before["fast"],
                predicted_medium_before=before["medium"],
                predicted_slow_before=before["slow"],
                phasic_by_horizon={h: 0.0 for h in self.HORIZON_ALPHA},
                phasic_aggregate=0.0,
                tonic_after=ds.tonic,
                habituation_after=ds.habituation,
                reason="not verified/causally admitted; exploration only",
                provenance=(e.source_ref,),
            )

        base_value = self._clip(e.utility) * weight
        sensitivity = 1.0 - ds.habituation if self.habituation_enabled else 1.0
        observed = base_value * sensitivity

        phasic: Dict[str, float] = {}
        for h, alpha in self.HORIZON_ALPHA.items():
            p = ds.predictions[h]
            err = observed - p.mean
            z = err / max(0.20, sqrt(max(1e-6, p.variance)))
            phasic[h] = self._clip(0.65 * err + 0.35 * z)
            old_mean = p.mean
            p.mean = old_mean + alpha * err
            residual2 = (observed - old_mean) ** 2
            va = self.VAR_ALPHA[h]
            p.variance = max(0.01, (1.0 - va) * p.variance + va * residual2)

        aggregate = sum(self.HORIZON_MIX[h] * phasic[h] for h in self.HORIZON_MIX)

        if self.habituation_enabled:
            repetition = 1.0 if (ds.admitted_events > 0 and abs(observed - ds.last_value) < 0.08) else 0.25
            ds.habituation = min(0.65, ds.habituation + 0.018 * repetition)

        if self.opponent_enabled:
            ds.opponent = min(1.0, ds.opponent * 0.92 + abs(aggregate) * 0.06)
            aggregate *= max(0.70, 1.0 - 0.20 * ds.opponent)

        tonic_alpha = self.TONIC_ALPHA[e.dimension]
        ds.tonic = self._clip(ds.tonic + tonic_alpha * (observed - ds.tonic), -1.0, 1.0)
        ds.last_value = observed
        ds.last_phasic = aggregate
        ds.admitted_events += 1

        self.state.event_count += 1
        self.state.recent_admitted_dimensions.append(e.dimension)
        self.state.recent_admitted_dimensions = self.state.recent_admitted_dimensions[-20:]
        self.state.recent_abs_phasic.append(abs(aggregate))
        self.state.recent_abs_phasic = self.state.recent_abs_phasic[-20:]

        return RewardPlasticityReceipt(
            episode_id=e.episode_id,
            outcome_id=e.outcome_id,
            dimension=e.dimension,
            admitted=True,
            material_learning_weight=weight,
            exploration_nudge=exploration,
            observed_value=observed,
            predicted_fast_before=before["fast"],
            predicted_medium_before=before["medium"],
            predicted_slow_before=before["slow"],
            phasic_by_horizon=phasic,
            phasic_aggregate=aggregate,
            tonic_after=ds.tonic,
            habituation_after=ds.habituation,
            reason="verified outcome + causal credit admitted",
            provenance=(e.source_ref,),
        )

    def tick(self, *, decay: float = 0.01, habituation_recovery: float = 0.01) -> None:
        for ds in self.state.dimensions.values():
            ds.tonic *= max(0.0, 1.0 - decay)
            ds.opponent *= 0.95
            if self.habituation_enabled:
                ds.habituation *= max(0.0, 1.0 - habituation_recovery)

    def control(self, *, unresolved_pressure: float, exploration_nudge: float = 0.0) -> RewardControlReadout:
        s = self.state.dimensions
        positive = (
            0.34 * s[RewardDimension.TASK].tonic
            + 0.24 * s[RewardDimension.EPISTEMIC].tonic
            + 0.10 * s[RewardDimension.SOCIAL].tonic
            + 0.20 * s[RewardDimension.HOMEOSTATIC].tonic
            + 0.12 * s[RewardDimension.NOVELTY].tonic
        )
        brakes = (
            0.72 * max(0.0, -s[RewardDimension.SAFETY].tonic)
            + 0.45 * max(0.0, -s[RewardDimension.RESOURCE].tonic)
        )
        persistence = self._clip(positive - brakes)
        disengagement = self._clip(brakes - positive, 0.0, 1.0)
        safety_veto = s[RewardDimension.SAFETY].tonic < -0.18
        resource_brake = s[RewardDimension.RESOURCE].tonic < -0.22

        recent = self.state.recent_abs_phasic
        mean_abs_phasic = sum(recent) / len(recent) if recent else 1.0
        dims = self.state.recent_admitted_dimensions[-10:]
        diversity = len(set(dims)) if dims else 0
        pressure = self._clip(unresolved_pressure, 0.0, 1.0)
        stagnation = pressure > 0.45 and mean_abs_phasic < 0.08 and diversity <= 2

        return RewardControlReadout(
            persistence_bias=persistence,
            disengagement_bias=disengagement,
            exploration_nudge=self._clip(exploration_nudge, 0.0, 0.12),
            stagnation_candidate=stagnation,
            safety_veto=safety_veto,
            resource_brake=resource_brake,
            typed_tonic={d.value: s[d].tonic for d in RewardDimension},
        )

    def compatibility_projection(self) -> Mapping[str, object]:
        s = self.state.dimensions
        phasic = sum(ds.last_phasic for ds in s.values()) / max(1, len(s))
        tonic = sum(ds.tonic for ds in s.values()) / max(1, len(s))
        hab = sum(ds.habituation for ds in s.values()) / max(1, len(s))
        return {
            "historical_nacc_projection": {
                "phasic": phasic,
                "tonic": tonic,
                "mean_habituation": hab,
                "typed_dimensions": {d.value: asdict(s[d]) for d in RewardDimension},
                "equivalence_status": "COMPATIBILITY_VIEW_NOT_SEMANTIC_IDENTITY",
            }
        }

    def snapshot(self) -> RewardState:
        return copy.deepcopy(self.state)
