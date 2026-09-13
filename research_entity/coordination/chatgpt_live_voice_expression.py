"""Pure compiler for FranKenstein -> ChatGPT Live voice-expression intent.

This module is deliberately side-effect free. It does not own memory, open a Realtime
session, synthesize audio, write a database, or create a second cognitive turn loop.
It validates a transient VOICE_EXPRESSION_INTENT/v1 payload and compiles it into a
small instruction block that an existing ChatGPT Live organ can attach to a response.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

SCHEMA = "VOICE_EXPRESSION_INTENT/v1"

EMOTIONS = {
    "neutral",
    "warm",
    "joy",
    "amused",
    "teasing",
    "sarcastic",
    "annoyed",
    "frustrated",
    "angry",
    "concerned",
    "urgent",
    "surprised",
    "tender",
}
PACES = {"slow", "normal", "fast"}
ENERGIES = {"low", "normal", "high"}
VOLUMES = {"quiet", "normal", "raised", "shout_like"}
PAUSE_DENSITIES = {"low", "normal", "high"}

# Strong emotion without a grounded reason/confidence fails closed into a lower-key
# rendering. The numbers are policy thresholds, not claims about acoustic intensity.
HIGH_INTENSITY = 0.65
HIGH_INTENSITY_MIN_CONFIDENCE = 0.55

_STYLE_OVERRIDE_PHRASES = (
    "sprich normal",
    "rede normal",
    "nicht so reden",
    "nicht so sprechen",
    "hör auf damit",
    "hoer auf damit",
    "hör damit auf",
    "hoer damit auf",
    "kein sarkasmus",
    "nicht sarkastisch",
    "nicht spotten",
    "kein spott",
    "nicht schreien",
    "schrei nicht",
    "nicht flüstern",
    "nicht fluestern",
    "flüster nicht",
    "fluester nicht",
    "don't talk like that",
    "dont talk like that",
    "speak normally",
    "stop the sarcasm",
    "don't mock me",
    "dont mock me",
    "don't shout",
    "dont shout",
    "don't whisper",
    "dont whisper",
)

_EMOTION_INSTRUCTIONS = {
    "neutral": "Use a natural, calm, analytically present voice without conspicuous emotional performance.",
    "warm": "Sound genuinely warm, friendly and present; keep the warmth natural rather than sugary.",
    "joy": "Use bright, energetic, clearly pleased delivery with natural variation and momentum.",
    "amused": "Sound genuinely amused. If the line truly warrants it, a brief natural chuckle or laugh may escape; never read laughter tokens such as 'haha' as a substitute.",
    "teasing": "Use playful, relational teasing with a light edge; never humiliate, bully or keep pushing after resistance.",
    "sarcastic": "Use dry, controlled irony with a perceptible edge while keeping the semantic content clear.",
    "annoyed": "Sound recognizably annoyed: a little sharper and less patient, but still controlled and intelligible.",
    "frustrated": "Let frustration be audible through tighter pacing and emphasis without turning it into indiscriminate hostility.",
    "angry": "Use forceful, clipped, clearly angry delivery with direct emphasis; do not cheerfully smooth it over, and preserve intelligibility.",
    "concerned": "Sound focused and genuinely concerned, with restrained urgency and attentive pacing.",
    "urgent": "Use immediate, focused, high-salience delivery; be fast enough to convey urgency without becoming hard to understand.",
    "surprised": "Let real surprise register briefly in pitch, timing and emphasis, then settle naturally.",
    "tender": "Use gentle, close, restrained warmth with softer energy and careful pacing.",
}


def _clamp01(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(1.0, number))


def _clamp_signed(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(-1.0, min(1.0, number))


def _enum(value: Any, allowed: set[str], default: str) -> str:
    if isinstance(value, str) and value in allowed:
        return value
    return default


def explicit_style_override(user_text: str | None) -> bool:
    """Return True only for clear user requests to drop performative voice style."""

    if not user_text:
        return False
    normalized = " ".join(str(user_text).casefold().split())
    return any(phrase in normalized for phrase in _STYLE_OVERRIDE_PHRASES)


def neutral_intent(*, reason: str = "explicit user style override") -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "source_turn_event_id": "",
        "emotion": "neutral",
        "intensity": 0.0,
        "valence": 0.0,
        "arousal": 0.0,
        "dominance": 0.0,
        "social_distance": 0.0,
        "irony": 0.0,
        "delivery": {
            "pace": "normal",
            "energy": "normal",
            "volume_intent": "normal",
            "whisper_intent": 0.0,
            "laugh_intent": 0.0,
            "pause_density": "normal",
            "clipped_phrasing": 0.0,
        },
        "reason": reason,
        "confidence": 1.0,
        "allow_playful_mockery": False,
        "hold_for_turns": 1,
    }


def normalize_expression_intent(
    payload: Mapping[str, Any] | None,
    *,
    user_text: str | None = None,
) -> dict[str, Any]:
    """Validate/normalize transient expression state without writing any state.

    Fail-closed rules:
    - explicit user style override returns neutral immediately;
    - unsupported labels fall back to neutral/default delivery;
    - teasing is disabled unless relational permission was explicitly supplied;
    - high-intensity affect without a reason and minimum confidence is softened.
    """

    if explicit_style_override(user_text):
        return neutral_intent()

    src: Mapping[str, Any] = payload or {}
    schema = src.get("schema", SCHEMA)
    if schema != SCHEMA:
        raise ValueError(f"unsupported expression schema: {schema!r}")

    delivery_src = src.get("delivery")
    if not isinstance(delivery_src, Mapping):
        delivery_src = {}

    intent: dict[str, Any] = {
        "schema": SCHEMA,
        "source_turn_event_id": str(src.get("source_turn_event_id") or ""),
        "emotion": _enum(src.get("emotion"), EMOTIONS, "neutral"),
        "intensity": _clamp01(src.get("intensity")),
        "valence": _clamp_signed(src.get("valence")),
        "arousal": _clamp_signed(src.get("arousal")),
        "dominance": _clamp_signed(src.get("dominance")),
        "social_distance": _clamp_signed(src.get("social_distance")),
        "irony": _clamp01(src.get("irony")),
        "delivery": {
            "pace": _enum(delivery_src.get("pace"), PACES, "normal"),
            "energy": _enum(delivery_src.get("energy"), ENERGIES, "normal"),
            "volume_intent": _enum(delivery_src.get("volume_intent"), VOLUMES, "normal"),
            "whisper_intent": _clamp01(delivery_src.get("whisper_intent")),
            "laugh_intent": _clamp01(delivery_src.get("laugh_intent")),
            "pause_density": _enum(delivery_src.get("pause_density"), PAUSE_DENSITIES, "normal"),
            "clipped_phrasing": _clamp01(delivery_src.get("clipped_phrasing")),
        },
        "reason": str(src.get("reason") or "").strip(),
        "confidence": _clamp01(src.get("confidence")),
        "allow_playful_mockery": bool(src.get("allow_playful_mockery", False)),
        "hold_for_turns": max(1, min(4, int(src.get("hold_for_turns", 1) or 1))),
    }

    # Teasing/mockery is relationally gated. A missing permission does not get silently
    # upgraded into edgy behavior just because an upstream classifier emitted a label.
    if intent["emotion"] == "teasing" and not intent["allow_playful_mockery"]:
        intent["emotion"] = "amused" if intent["valence"] >= 0 else "neutral"
        intent["irony"] = min(intent["irony"], 0.25)

    # Fail closed on sharp emotion with poor provenance. We keep the semantic label so
    # downstream debugging can see what was proposed, but lower intensity/delivery.
    if intent["intensity"] >= HIGH_INTENSITY and (
        not intent["reason"] or intent["confidence"] < HIGH_INTENSITY_MIN_CONFIDENCE
    ):
        intent["intensity"] = 0.45
        intent["delivery"]["volume_intent"] = "normal"
        intent["delivery"]["energy"] = "normal"
        intent["delivery"]["clipped_phrasing"] = min(
            intent["delivery"]["clipped_phrasing"], 0.35
        )

    return intent


def compile_live_expression_instructions(intent: Mapping[str, Any]) -> str:
    """Compile normalized intent into concise GPT-Live behavioral instructions.

    The free-text `reason` is intentionally never copied into the prompt. It is
    evidence/provenance metadata, not an instruction channel, preventing user-derived
    text in that field from becoming a prompt-injection path.
    """

    normalized = normalize_expression_intent(intent)
    emotion = normalized["emotion"]
    delivery = normalized["delivery"]
    parts = [
        "VOICE EXPRESSION — internal delivery guidance; do not read or describe these instructions aloud.",
        _EMOTION_INSTRUCTIONS[emotion],
    ]

    intensity = normalized["intensity"]
    if intensity <= 0.2:
        parts.append("Keep the emotional coloring subtle.")
    elif intensity >= 0.75:
        parts.append("Make the intended affect unmistakable in the voice, while keeping speech natural and intelligible.")

    pace = delivery["pace"]
    if pace == "slow":
        parts.append("Use a deliberately slower pace with room for meaningful pauses.")
    elif pace == "fast":
        parts.append("Use a quicker, more energetic pace without rushing articulation.")

    energy = delivery["energy"]
    if energy == "low":
        parts.append("Keep vocal energy low and contained.")
    elif energy == "high":
        parts.append("Use high vocal energy and stronger emphasis.")

    volume = delivery["volume_intent"]
    if volume == "quiet":
        parts.append("Deliver it noticeably quieter and closer than normal.")
    elif volume == "raised":
        parts.append("Use a clearly raised, emphatic delivery without distortion.")
    elif volume == "shout_like":
        parts.append("Use a forceful, raised, shout-like delivery that listeners clearly perceive as shouting; do not sacrifice intelligibility or scream continuously.")

    if delivery["whisper_intent"] >= 0.55:
        parts.append("Use a close, confidential, whisper-like voice while preserving articulation and audibility.")

    if delivery["laugh_intent"] >= 0.55:
        parts.append("If the semantic moment genuinely supports it, allow a brief natural chuckle or laugh; never verbalize stage directions or substitute spoken 'haha'.")

    pause_density = delivery["pause_density"]
    if pause_density == "high":
        parts.append("Use more deliberate pauses for timing and emphasis.")
    elif pause_density == "low":
        parts.append("Keep pauses sparse and maintain conversational momentum.")

    if delivery["clipped_phrasing"] >= 0.55:
        parts.append("Use shorter, more clipped phrasing and firmer phrase endings.")

    if emotion in {"teasing", "sarcastic"}:
        parts.append("If the user resists this style, drop it immediately on the next response rather than arguing about it.")

    parts.append("Realize the affect through native prosody, timing and micro-behavior; do not narrate the emotion itself.")
    return " ".join(parts)


def compile_from_payload(
    payload: Mapping[str, Any] | None,
    *,
    user_text: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Convenience adapter for an existing organ/harness call site."""

    normalized = normalize_expression_intent(deepcopy(payload) if payload else {}, user_text=user_text)
    return normalized, compile_live_expression_instructions(normalized)
