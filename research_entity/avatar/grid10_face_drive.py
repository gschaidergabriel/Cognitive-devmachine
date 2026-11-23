"""GRID10 -> facial dynamics adapter for FranKenstein Avatar.

This module deliberately extracts *structural* dynamics from GRID10 and does not
pretend that G1..G10 have fixed emotion meanings. Cell identities may matter to
GRID causality, but the face adapter only consumes permutation-safe geometry
(entropy, dominance, transition, broadcast magnitude) plus explicit winner
change. Semantic valence/playfulness must come from an actually typed state
source, not invented from a cell number.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Mapping, Optional

CELLS = tuple(f"G{i}" for i in range(1, 11))
EPS = 1e-12


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def _vec(states: Mapping[str, float]) -> list[float]:
    return [float(states.get(k, 0.0) or 0.0) for k in CELLS]


def _cosine_transition(a: list[float], b: list[float]) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na < EPS and nb < EPS:
        return 0.0
    if na < EPS or nb < EPS:
        return 1.0
    c = sum(x * y for x, y in zip(a, b)) / (na * nb)
    c = max(-1.0, min(1.0, c))
    return _clamp((1.0 - c) / 2.0)


@dataclass(frozen=True)
class GridFaceDrive:
    entropy: float
    dominance: float
    participation: float
    broadcast_strength: float
    transition: float
    winner_changed: bool
    arousal: float
    tension: float
    curiosity: float
    dispersion: float
    novelty_kick: float
    event_rate_multiplier: float
    hold_scale: float

    def to_dict(self) -> dict:
        return asdict(self)


def derive_grid_face_drive(
    cell_states: Mapping[str, float],
    broadcast_value: float,
    winner: Optional[str] = None,
    previous_cell_states: Optional[Mapping[str, float]] = None,
    previous_winner: Optional[str] = None,
) -> GridFaceDrive:
    """Derive bounded facial *dynamics* from a GRID10 frame.

    Invariants:
    - no hard-coded Gx -> emotion mapping;
    - scale robust: broadcast magnitude is measured relative to current RMS;
    - entropy/dominance are invariant to cell permutation;
    - transition is invariant when the same permutation is applied to both frames.
    """
    v = _vec(cell_states)
    mags = [abs(x) for x in v]
    mass = sum(mags)
    if mass < EPS:
        p = [0.1] * 10
        entropy = 1.0
        dominance = 0.1
        participation = 1.0
    else:
        p = [x / mass for x in mags]
        raw_h = -sum(x * math.log(x) for x in p if x > EPS)
        entropy = _clamp(raw_h / math.log(10.0))
        dominance = _clamp(max(p))
        # Effective-number participation, normalized to [0.1, 1].
        participation = _clamp(math.exp(raw_h) / 10.0)

    rms = math.sqrt(sum(x * x for x in v) / 10.0)
    broadcast_strength = _clamp(math.tanh(abs(float(broadcast_value or 0.0)) / (rms + EPS)))

    transition = 0.0
    if previous_cell_states is not None:
        transition = _cosine_transition(_vec(previous_cell_states), v)
    winner_changed = bool(previous_winner and winner and previous_winner != winner)
    winner_impulse = 1.0 if winner_changed else 0.0

    # Dynamics only. These names describe motor drives, not claimed emotions.
    arousal = _clamp(0.14 + 0.52 * broadcast_strength + 0.27 * transition + 0.07 * winner_impulse)
    tension = _clamp(0.10 + 0.34 * dominance + 0.34 * transition + 0.10 * winner_impulse)
    curiosity = _clamp(0.12 + 0.46 * entropy + 0.32 * transition + 0.08 * winner_impulse)
    dispersion = _clamp(0.72 * entropy + 0.28 * (1.0 - dominance))
    novelty_kick = _clamp(0.70 * transition + 0.30 * winner_impulse)

    event_rate_multiplier = max(0.55, min(1.60, 0.55 + 0.58 * arousal + 0.30 * novelty_kick))
    hold_scale = max(0.72, min(1.22, 1.16 - 0.38 * arousal + 0.08 * dispersion))

    return GridFaceDrive(
        entropy=entropy,
        dominance=dominance,
        participation=participation,
        broadcast_strength=broadcast_strength,
        transition=transition,
        winner_changed=winner_changed,
        arousal=arousal,
        tension=tension,
        curiosity=curiosity,
        dispersion=dispersion,
        novelty_kick=novelty_kick,
        event_rate_multiplier=event_rate_multiplier,
        hold_scale=hold_scale,
    )
