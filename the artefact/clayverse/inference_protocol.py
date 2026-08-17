from __future__ import annotations

import json
from typing import Any


class InferenceProtocolError(RuntimeError):
    pass


ALLOWED_INFERENCE_EFFECTS = {"entityos.exec", "state.noop"}


def _clean_string(value: Any, name: str, *, max_length: int) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length or "\x00" in value:
        raise InferenceProtocolError(f"invalid {name}")
    return value


def parse_claude_decision(result: str) -> dict[str, Any]:
    """Parse Claude's tool-less output into a bounded ClayVerse decision.

    Claude may request an effect, but this function never executes it. Only the
    canonical EffectGate can turn the returned intent into an external action.
    Unknown fields/capabilities fail closed instead of being guessed.
    """
    if not isinstance(result, str) or not result:
        raise InferenceProtocolError("empty inference result")
    try:
        payload = json.loads(result)
    except json.JSONDecodeError as exc:
        raise InferenceProtocolError("inference result is not JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"text", "effect"}:
        raise InferenceProtocolError("inference result must contain exactly text and effect")

    text = payload["text"]
    if not isinstance(text, str) or len(text) > 100_000 or "\x00" in text:
        raise InferenceProtocolError("invalid response text")

    effect = payload["effect"]
    if effect is None:
        return {"text": text, "selection": "respond", "effect": None}
    if not isinstance(effect, dict) or set(effect) != {"capability", "target", "argv"}:
        raise InferenceProtocolError("effect must contain exactly capability, target and argv")

    capability = effect["capability"]
    if capability not in ALLOWED_INFERENCE_EFFECTS:
        raise InferenceProtocolError("inference requested a forbidden capability")
    target = _clean_string(effect["target"], "effect target", max_length=2048)
    argv = effect["argv"]

    if capability == "entityos.exec":
        if not isinstance(argv, list) or not argv or len(argv) > 128:
            raise InferenceProtocolError("EntityOS effect requires bounded argv")
        clean_argv = [_clean_string(item, "effect argv", max_length=8192) for item in argv]
    else:
        if argv not in (None, []):
            raise InferenceProtocolError("state.noop does not accept argv")
        clean_argv = None

    return {
        "text": text,
        "selection": "request_effect",
        "effect": {"capability": capability, "target": target, "argv": clean_argv},
    }
