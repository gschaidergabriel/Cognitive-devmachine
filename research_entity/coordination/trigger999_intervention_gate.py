"""Deterministic reference gate for TRIGGER 999 conversational intervention.

This is a research/coordination prototype, not production activation.
It deliberately has no audio, network, memory, tool, or effect side effects.
The surrounding Frankenstein runtime remains authoritative for those scopes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional, Sequence, Tuple


class SpeechAct(str, Enum):
    ANSWER = "ANSWER"
    CLARIFY = "CLARIFY"
    OBJECT = "OBJECT"
    PROPOSE = "PROPOSE"
    WISH = "WISH"
    BACKCHANNEL = "BACKCHANNEL"
    SELF_COMMENT = "SELF_COMMENT"
    TOOL = "TOOL"
    WAIT = "WAIT"
    CLOSE = "CLOSE"


@dataclass(frozen=True)
class ConversationFloorState:
    now_ms: int
    current_floor_owner: str = "UNKNOWN"
    last_speaker: str = "UNKNOWN"
    likely_addressee: str = "UNKNOWN"
    speaker_confidence: float = 0.0
    addressee_confidence: float = 0.0
    speech_active: bool = False
    overlap_active: bool = False
    silence_duration_ms: int = 0
    frankenstein_speaking: bool = False
    frankenstein_interrupted: bool = False
    last_frankenstein_act: Optional[SpeechAct] = None
    last_frankenstein_end_ms: Optional[int] = None
    recent_backchannel_count: int = 0
    recent_intervention_count: int = 0
    conversation_tension: float = 0.0
    humor_receptivity: float = 0.0
    user_interruptibility: float = 0.5
    urgency: float = 0.0
    unfinished_intent: Optional[str] = None


@dataclass(frozen=True)
class ExpressionEnvelope:
    valence: float = 0.0
    arousal: float = 0.0
    confidence: float = 0.5
    warmth: float = 0.0
    irony: float = 0.0
    amusement: float = 0.0
    irritation: float = 0.0
    urgency: float = 0.0
    volume: float = 0.5
    pace: float = 0.5
    whisper: float = 0.0
    emphasis: float = 0.0
    laugh_probability: float = 0.0


@dataclass(frozen=True)
class InterventionCandidate:
    candidate_id: str
    speech_act: SpeechAct
    semantic_intent: str
    reason: str
    expected_task_value: float = 0.0
    expected_social_value: float = 0.0
    urgency: float = 0.0
    novelty: float = 0.0
    invitation_strength: float = 0.0
    repair_need: float = 0.0
    overlap_cost: float = 0.0
    intrusion_risk: float = 0.0
    uncertainty_cost: float = 0.0
    repetition_cost: float = 0.0
    expression: ExpressionEnvelope = field(default_factory=ExpressionEnvelope)
    expires_at_ms: Optional[int] = None


@dataclass(frozen=True)
class GateConfig:
    enter_threshold: float = 1.80
    backchannel_threshold: float = 1.05
    urgent_override_threshold: float = 0.90
    active_human_floor_penalty: float = 1.45
    overlap_penalty: float = 0.75
    unknown_addressee_penalty: float = 0.25
    unsolicited_cooldown_ms: int = 3200
    max_recent_backchannels: int = 2
    max_recent_interventions: int = 4
    chatter_penalty: float = 0.35
    backchannel_spam_penalty: float = 0.65


@dataclass(frozen=True)
class ScoreBreakdown:
    positive: float
    negative: float
    floor_penalty: float
    overlap_penalty: float
    uncertainty_penalty: float
    cooldown_penalty: float
    chatter_penalty: float
    total: float


@dataclass(frozen=True)
class GateDecision:
    speech_act: SpeechAct
    selected_candidate_id: Optional[str]
    speak: bool
    reason: str
    score: float
    breakdown: Optional[ScoreBreakdown]
    yield_to_human: bool = False


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _score(candidate: InterventionCandidate, state: ConversationFloorState, cfg: GateConfig) -> ScoreBreakdown:
    positive = sum(
        _clamp01(v)
        for v in (
            candidate.expected_task_value,
            candidate.expected_social_value,
            candidate.urgency,
            candidate.novelty,
            candidate.invitation_strength,
            candidate.repair_need,
        )
    )
    negative = sum(
        _clamp01(v)
        for v in (
            candidate.overlap_cost,
            candidate.intrusion_risk,
            candidate.uncertainty_cost,
            candidate.repetition_cost,
        )
    )

    human_has_floor = state.speech_active and state.current_floor_owner not in ("FRANKENSTEIN", "UNKNOWN")
    floor_penalty = cfg.active_human_floor_penalty if human_has_floor else 0.0
    overlap_penalty = cfg.overlap_penalty if state.overlap_active else 0.0

    uncertainty_penalty = 0.0
    if state.likely_addressee == "UNKNOWN" or state.addressee_confidence < 0.35:
        uncertainty_penalty = cfg.unknown_addressee_penalty

    cooldown_penalty = 0.0
    if state.last_frankenstein_end_ms is not None:
        elapsed = max(0, state.now_ms - state.last_frankenstein_end_ms)
        if elapsed < cfg.unsolicited_cooldown_ms and candidate.invitation_strength < 0.8:
            cooldown_penalty = 1.0 - (elapsed / cfg.unsolicited_cooldown_ms)

    chatter_penalty = 0.0
    if state.recent_intervention_count >= cfg.max_recent_interventions:
        chatter_penalty += cfg.chatter_penalty
    if candidate.speech_act == SpeechAct.BACKCHANNEL and state.recent_backchannel_count >= cfg.max_recent_backchannels:
        chatter_penalty += cfg.backchannel_spam_penalty

    total = positive - negative - floor_penalty - overlap_penalty - uncertainty_penalty - cooldown_penalty - chatter_penalty
    return ScoreBreakdown(
        positive=positive,
        negative=negative,
        floor_penalty=floor_penalty,
        overlap_penalty=overlap_penalty,
        uncertainty_penalty=uncertainty_penalty,
        cooldown_penalty=cooldown_penalty,
        chatter_penalty=chatter_penalty,
        total=total,
    )


def choose_intervention(
    state: ConversationFloorState,
    candidates: Sequence[InterventionCandidate],
    cfg: GateConfig = GateConfig(),
) -> GateDecision:
    """Choose SPEAK/BACKCHANNEL/WAIT deterministically.

    Human barge-in has priority: while Frankenstein is speaking, newly active human
    speech causes an immediate yield decision unless a candidate carries genuinely
    high urgency. The function never performs the effect; it only emits the decision.
    """

    live_candidates = [
        c for c in candidates
        if c.speech_act != SpeechAct.WAIT
        and (c.expires_at_ms is None or c.expires_at_ms >= state.now_ms)
    ]

    scored: list[Tuple[InterventionCandidate, ScoreBreakdown]] = [
        (c, _score(c, state, cfg)) for c in live_candidates
    ]
    scored.sort(key=lambda pair: (pair[1].total, pair[0].candidate_id), reverse=True)

    if state.frankenstein_speaking and state.speech_active and state.current_floor_owner != "FRANKENSTEIN":
        urgent = [pair for pair in scored if _clamp01(pair[0].urgency) >= cfg.urgent_override_threshold]
        if not urgent:
            return GateDecision(
                speech_act=SpeechAct.WAIT,
                selected_candidate_id=None,
                speak=False,
                reason="human_barge_in_yield",
                score=0.0,
                breakdown=None,
                yield_to_human=True,
            )

    if not scored:
        return GateDecision(
            speech_act=SpeechAct.WAIT,
            selected_candidate_id=None,
            speak=False,
            reason="no_live_candidate",
            score=0.0,
            breakdown=None,
        )

    candidate, breakdown = scored[0]
    threshold = cfg.backchannel_threshold if candidate.speech_act == SpeechAct.BACKCHANNEL else cfg.enter_threshold

    # Urgent correction may cross an active human floor, but urgency alone is not
    # enough: the final score must still be non-negative after intrusion costs.
    urgent_override = (
        _clamp01(candidate.urgency) >= cfg.urgent_override_threshold
        and breakdown.total >= 0.0
    )

    if breakdown.total >= threshold or urgent_override:
        return GateDecision(
            speech_act=candidate.speech_act,
            selected_candidate_id=candidate.candidate_id,
            speak=True,
            reason="urgent_override" if urgent_override and breakdown.total < threshold else "score_threshold",
            score=breakdown.total,
            breakdown=breakdown,
        )

    return GateDecision(
        speech_act=SpeechAct.WAIT,
        selected_candidate_id=candidate.candidate_id,
        speak=False,
        reason="wait_has_higher_expected_value",
        score=breakdown.total,
        breakdown=breakdown,
    )
