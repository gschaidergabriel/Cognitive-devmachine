from __future__ import annotations

import re
from typing import Any

from .adapters import MistralInference
from .turn_lifecycle import TurnLifecycle, TurnLifecycleError


class MistralTurnError(RuntimeError):
    pass


_RECEIPT_KEYS = {
    "provider",
    "model_requested",
    "model_returned",
    "response_id",
    "finish_reason",
    "request_sha256",
    "response_sha256",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class MistralTurnRunner:
    """Bind Mistral inference to the existing UnifiedDB/TurnLifecycle causal spine.

    This runner deliberately has no effect API. A Mistral response is completed and
    persisted as a canonical assistant turn before any later, separately admitted
    EffectGate turn can occur. Mistral therefore cannot become an effect authority.
    """

    def __init__(self, inference: MistralInference):
        self.inference = inference

    @staticmethod
    def _bounded_text(value: Any, field: str, maximum: int) -> str:
        if (
            not isinstance(value, str)
            or not value
            or len(value) > maximum
            or "\x00" in value
            or "\r" in value
            or "\n" in value
        ):
            raise MistralTurnError(f"Mistral receipt {field} is invalid")
        return value

    @classmethod
    def _receipt(cls, decision: dict[str, Any]) -> dict[str, Any]:
        receipt = decision.get("inference_receipt")
        if not isinstance(receipt, dict) or set(receipt) != _RECEIPT_KEYS:
            raise MistralTurnError("Mistral inference receipt is missing or invalid")
        if receipt.get("provider") != "mistral":
            raise MistralTurnError("Mistral inference receipt provider is invalid")
        cls._bounded_text(receipt.get("model_requested"), "model_requested", 256)
        cls._bounded_text(receipt.get("model_returned"), "model_returned", 256)
        cls._bounded_text(receipt.get("response_id"), "response_id", 512)
        if receipt.get("finish_reason") != "stop":
            raise MistralTurnError("Mistral receipt finish_reason is invalid")
        for field in ("request_sha256", "response_sha256"):
            value = receipt.get(field)
            if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
                raise MistralTurnError(f"Mistral receipt {field} is invalid")
        return dict(receipt)

    def run(
        self,
        lifecycle: TurnLifecycle,
        prompt: str,
        resources: list[str] | None = None,
    ) -> dict[str, Any]:
        admission = lifecycle.begin(
            prompt,
            resources,
            source="mistral-api:request",
        )
        try:
            generation = int(admission["generation"])
            lifecycle.db.assert_live_generation(lifecycle.session_id, generation)
            decision = self.inference.reason(admission["context"], prompt)
            lifecycle.db.assert_live_generation(lifecycle.session_id, generation)

            if not isinstance(decision, dict):
                raise MistralTurnError("Mistral decision must be an object")
            if decision.get("selection") != "respond" or decision.get("effect") is not None:
                raise MistralTurnError("Mistral effect intent is not admitted by the canonical Mistral turn path")
            text = decision.get("text")
            if not isinstance(text, str) or len(text) > 200_000:
                raise MistralTurnError("Mistral response text is invalid")
            receipt = self._receipt(decision)

            completion = lifecycle.complete(
                text,
                source="mistral-api:response",
                provider_receipt=receipt,
            )
            if not completion.get("completed"):
                raise MistralTurnError("Mistral turn did not complete")
            if completion.get("causal_id") != admission["causal_id"]:
                raise MistralTurnError("Mistral response diverged from admitted causal identity")
            if completion.get("effect_id") is not None:
                raise MistralTurnError("Mistral cognition turn unexpectedly bound an effect")

            return {
                "user_id": admission["user_id"],
                "session_id": admission["session_id"],
                "turn_id": admission["turn_id"],
                "assistant_turn_id": completion["assistant_turn_id"],
                "causal_id": admission["causal_id"],
                "generation": generation,
                "text": text,
                "inference_receipt": receipt,
            }
        except Exception:
            try:
                if lifecycle.active() is not None:
                    lifecycle.abort("mistral_turn_failed_or_stale")
            except (TurnLifecycleError, RuntimeError):
                pass
            raise
