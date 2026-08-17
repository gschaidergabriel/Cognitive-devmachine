from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class NeedleDecision:
    route: str
    score: float
    context_budget: int
    collision_risk: bool
    unresolved_hyperposition: bool
    effect_candidate: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


class NeedleRouter:
    """Small deterministic routing hint; it does not mint permissions or truth.

    In the single-Claude ClayVerse target, Needle is not a model chooser. It estimates
    context/coordination pressure so the main reasoning loop can distinguish ordinary
    turns from collision-heavy, unresolved or likely-effectful work while all real
    authority remains in EffectGate/EntityOS.
    """

    EFFECT_WORDS = (
        "write", "change", "edit", "delete", "deploy", "install", "restart", "stop",
        "start", "send", "create", "commit", "push", "merge", "run", "execute",
        "ändern", "loeschen", "löschen", "bauen", "deployen", "installieren", "starten",
        "stoppen", "senden", "erstellen", "committen", "ausführen", "ausfuehren",
    )

    @classmethod
    def analyze(cls, prompt: str, world: dict, hyperpositions: list[dict], resources: list[str]) -> dict:
        collision_count = len(world.get("cross_session_collision", []))
        memory_count = len(world.get("durable_memory", []))
        tokenish = len(prompt.split())
        effect_candidate = any(word in prompt.lower() for word in cls.EFFECT_WORDS)
        unresolved = bool(hyperpositions)
        reasons: list[str] = []
        score = 0.10
        score += min(0.25, tokenish / 800)
        score += min(0.20, len(resources) * 0.04)
        score += min(0.20, memory_count / 250)
        if collision_count:
            score += 0.25
            reasons.append("cross_session_collision")
        if unresolved:
            score += 0.20
            reasons.append("unresolved_hyperposition")
        if effect_candidate:
            score += 0.15
            reasons.append("effect_language")
        if len(resources) > 3:
            reasons.append("multi_resource")
        if tokenish > 300:
            reasons.append("long_input")
        score = min(1.0, score)

        if collision_count or unresolved:
            route = "deep_shared_state"
            budget = 24000
        elif effect_candidate:
            route = "effect_aware"
            budget = 16000
        elif score >= 0.45:
            route = "deep_local"
            budget = 16000
        else:
            route = "direct_local"
            budget = 8000
        return NeedleDecision(
            route=route,
            score=round(score, 4),
            context_budget=budget,
            collision_risk=collision_count > 0,
            unresolved_hyperposition=unresolved,
            effect_candidate=effect_candidate,
            reasons=tuple(reasons),
        ).as_dict()
