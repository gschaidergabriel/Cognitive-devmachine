"""Ephemeral GRID/GWT/TITAN -> ChatGPT Live voice-expression adapter.

This module creates no durable mood, memory, audio renderer, or second turn loop.
It only turns canonical per-turn context into VOICE_EXPRESSION_INTENT/v1 for the
native ChatGPT Live voice organ.
"""
from __future__ import annotations

from typing import Any, Mapping

try:
    from .chatgpt_live_voice_expression import (
        EMOTIONS,
        SCHEMA,
        explicit_style_override,
        neutral_intent,
        normalize_expression_intent,
    )
except ImportError:  # deployed beside the runtime organ
    from chatgpt_live_voice_expression import (
        EMOTIONS,
        SCHEMA,
        explicit_style_override,
        neutral_intent,
        normalize_expression_intent,
    )

_DECLARED_KEYS = (
    "voice_expression_intent",
    "voice_expression",
    "expression_intent",
    "live_voice_expression",
)
_DIRECTIVE_WORDS = (
    "sprich", "rede", "kling", "sei", "sag", "mach", "stimme",
    "voice", "sound", "speak", "talk",
)
_ALIASES = {
    "warm": ("warm", "warmth", "freund", "affection"),
    "joy": ("joy", "freude", "happy", "glück", "glueck", "excite"),
    "amused": ("amused", "humor", "humour", "lachen", "laugh"),
    "teasing": ("teas", "spott", "mock", "neck"),
    "sarcastic": ("sarcas", "sarkas", "irony", "ironie"),
    "annoyed": ("annoy", "generv", "irrit"),
    "frustrated": ("frustr", "frust"),
    "angry": ("anger", "angry", "wut", "wuet", "wüt", "rage"),
    "concerned": ("concern", "sorge", "besorg", "worry"),
    "urgent": ("urgent", "dring", "alarm"),
    "surprised": ("surpris", "überrasch", "ueberrasch"),
    "tender": ("tender", "sanft", "zärt", "zaert"),
}

_PRESETS: dict[str, dict[str, Any]] = {
    "neutral": dict(v=0.0, a=0.0, d=0.0, sd=0.0, irony=0.0, pace="normal", energy="normal", volume="normal", whisper=0.0, laugh=0.0, pauses="normal", clipped=0.0),
    "warm": dict(v=0.65, a=0.15, d=0.05, sd=-0.45, irony=0.0, pace="normal", energy="normal", volume="normal", whisper=0.0, laugh=0.0, pauses="normal", clipped=0.0),
    "joy": dict(v=0.9, a=0.72, d=0.25, sd=-0.2, irony=0.0, pace="fast", energy="high", volume="normal", whisper=0.0, laugh=0.2, pauses="low", clipped=0.0),
    "amused": dict(v=0.78, a=0.5, d=0.15, sd=-0.25, irony=0.25, pace="normal", energy="normal", volume="normal", whisper=0.0, laugh=0.62, pauses="normal", clipped=0.0),
    "teasing": dict(v=0.55, a=0.48, d=0.35, sd=-0.15, irony=0.72, pace="normal", energy="normal", volume="normal", whisper=0.0, laugh=0.2, pauses="normal", clipped=0.15),
    "sarcastic": dict(v=-0.05, a=0.32, d=0.45, sd=0.05, irony=0.9, pace="normal", energy="normal", volume="normal", whisper=0.0, laugh=0.0, pauses="high", clipped=0.35),
    "annoyed": dict(v=-0.42, a=0.45, d=0.4, sd=0.12, irony=0.1, pace="normal", energy="normal", volume="normal", whisper=0.0, laugh=0.0, pauses="low", clipped=0.42),
    "frustrated": dict(v=-0.58, a=0.68, d=0.35, sd=0.1, irony=0.05, pace="normal", energy="high", volume="normal", whisper=0.0, laugh=0.0, pauses="low", clipped=0.62),
    "angry": dict(v=-0.82, a=0.92, d=0.78, sd=0.2, irony=0.0, pace="normal", energy="high", volume="raised", whisper=0.0, laugh=0.0, pauses="low", clipped=0.86),
    "concerned": dict(v=-0.2, a=0.42, d=0.05, sd=-0.12, irony=0.0, pace="slow", energy="normal", volume="normal", whisper=0.0, laugh=0.0, pauses="normal", clipped=0.0),
    "urgent": dict(v=-0.15, a=0.92, d=0.62, sd=0.0, irony=0.0, pace="fast", energy="high", volume="raised", whisper=0.0, laugh=0.0, pauses="low", clipped=0.55),
    "surprised": dict(v=0.15, a=0.82, d=0.05, sd=0.0, irony=0.0, pace="normal", energy="high", volume="normal", whisper=0.0, laugh=0.0, pauses="normal", clipped=0.0),
    "tender": dict(v=0.68, a=-0.12, d=-0.1, sd=-0.72, irony=0.0, pace="slow", energy="low", volume="quiet", whisper=0.35, laugh=0.0, pauses="high", clipped=0.0),
}


def _text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def _find_declared(value: Any) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    for key, candidate in value.items():
        if str(key).casefold() in _DECLARED_KEYS and isinstance(candidate, Mapping):
            return candidate
    for candidate in value.values():
        found = _find_declared(candidate)
        if found is not None:
            return found
    return None


def _walk(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, Mapping):
        for key, candidate in value.items():
            next_path = path + (str(key).casefold(),)
            yield ".".join(next_path), candidate
            yield from _walk(candidate, next_path)
    elif isinstance(value, (list, tuple)):
        for index, candidate in enumerate(value):
            yield from _walk(candidate, path + (str(index),))


def _scores(capsule: Mapping[str, Any]) -> dict[str, float]:
    scores = {name: 0.0 for name in EMOTIONS}
    for path, value in _walk(capsule):
        affect_path = any(marker in path for marker in ("emotion", "affect", "mood", "expression", "prosody", "voice"))
        for emotion, aliases in _ALIASES.items():
            key_match = any(alias in path for alias in aliases)
            if key_match and isinstance(value, (int, float)) and not isinstance(value, bool):
                scores[emotion] = max(scores[emotion], max(0.0, min(1.0, float(value))))
            elif affect_path and isinstance(value, str) and any(alias in value.casefold() for alias in aliases):
                scores[emotion] = max(scores[emotion], 0.72)
    return scores


def _directive(text: str, roots: tuple[str, ...]) -> bool:
    return any(root in text for root in roots) and any(word in text for word in _DIRECTIVE_WORDS)


def _intent(
    emotion: str,
    intensity: float,
    confidence: float,
    turn_id: str,
    reason: str,
    allow_mockery: bool = False,
) -> dict[str, Any]:
    p = _PRESETS.get(emotion, _PRESETS["neutral"])
    return {
        "schema": SCHEMA,
        "source_turn_event_id": turn_id,
        "emotion": emotion if emotion in EMOTIONS else "neutral",
        "intensity": intensity,
        "valence": p["v"],
        "arousal": p["a"],
        "dominance": p["d"],
        "social_distance": p["sd"],
        "irony": p["irony"],
        "delivery": {
            "pace": p["pace"],
            "energy": p["energy"],
            "volume_intent": p["volume"],
            "whisper_intent": p["whisper"],
            "laugh_intent": p["laugh"],
            "pause_density": p["pauses"],
            "clipped_phrasing": p["clipped"],
        },
        "reason": reason,
        "confidence": confidence,
        "allow_playful_mockery": allow_mockery,
        "hold_for_turns": 1,
    }


def derive_expression_intent(
    user_text: str | None,
    capsule: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return one transient expression intent for the current turn only."""

    text = _text(user_text)
    context: Mapping[str, Any] = capsule or {}
    turn_id = str(context.get("turn_event_id") or "")

    if explicit_style_override(text) or any(
        phrase in text
        for phrase in ("nicht lachen", "lach nicht", "don't laugh", "dont laugh")
    ):
        result = neutral_intent(reason="explicit user style override")
        result["source_turn_event_id"] = turn_id
        return result

    declared = _find_declared(context)
    if declared is not None:
        payload = dict(declared)
        payload.setdefault("schema", SCHEMA)
        payload.setdefault("source_turn_event_id", turn_id)
        return normalize_expression_intent(payload, user_text=user_text)

    explicit_mockery = _directive(text, ("spött", "spoett", "sarkast", "sarcast", "mock", "teas"))
    whisper = any(root in text for root in ("flüster", "fluester", "whisper"))
    shout = any(root in text for root in ("schrei", "shout"))
    laugh = any(root in text for root in ("lach", "laugh", "chuckle"))

    emotion: str | None = None
    if _directive(text, ("wüt", "wuet", "angry", "rage")):
        emotion = "angry"
    elif _directive(text, ("sarkast", "sarcast")):
        emotion = "sarcastic"
    elif _directive(text, ("spött", "spoett", "mock", "teas")):
        emotion = "teasing"
    elif _directive(text, ("fröh", "froeh", "freud", "joy", "happy", "excited")):
        emotion = "joy"
    elif _directive(text, ("warm", "freundlich", "friendly")):
        emotion = "warm"
    elif _directive(text, ("sanft", "zärt", "zaert", "tender")):
        emotion = "tender"

    if whisper:
        emotion = emotion or "tender"
    if laugh:
        emotion = emotion or "amused"
    if shout:
        emotion = emotion or "urgent"

    if emotion:
        result = _intent(
            emotion,
            0.9 if (shout or emotion == "angry") else 0.78,
            0.98,
            turn_id,
            "explicit user delivery request",
            explicit_mockery,
        )
        if whisper:
            result["delivery"].update(volume_intent="quiet", whisper_intent=0.95, energy="low")
        if laugh:
            result["delivery"]["laugh_intent"] = 0.95
        if shout:
            result["delivery"].update(volume_intent="shout_like", energy="high")
            result["delivery"]["clipped_phrasing"] = max(result["delivery"]["clipped_phrasing"], 0.65)
        return normalize_expression_intent(result, user_text=user_text)

    scores = _scores(context)
    emotion, score = max(scores.items(), key=lambda item: item[1])
    if score >= 0.5:
        allow_mockery = bool(
            context.get("allow_playful_mockery")
            or context.get("playful_mockery_allowed")
            or context.get("relational_teasing_allowed")
        )
        result = _intent(
            emotion, max(0.5, min(0.95, score)), 0.82, turn_id,
            "explicit affect-labelled canonical state", allow_mockery,
        )
        if emotion in {"angry", "urgent"} and score >= 0.92:
            result["delivery"]["volume_intent"] = "shout_like"
        return normalize_expression_intent(result, user_text=user_text)

    # Deliberately do NOT map user profanity or user anger to assistant anger.
    if any(token in text for token in ("haha", "hahaha", "lol", "😂", "🤣")):
        return normalize_expression_intent(
            _intent("amused", 0.48, 0.62, turn_id, "lightweight amusement speech-act cue"),
            user_text=user_text,
        )
    if any(token in text for token in ("dringend", "sofort", "urgent", "asap")):
        return normalize_expression_intent(
            _intent("urgent", 0.58, 0.66, turn_id, "task urgency speech-act cue"),
            user_text=user_text,
        )

    result = neutral_intent(reason="no grounded expression signal")
    result["source_turn_event_id"] = turn_id
    result["confidence"] = 0.85
    return result
