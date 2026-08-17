from __future__ import annotations

from typing import Any

from .adapters import MistralInference
from .turn_lifecycle import TurnLifecycle, TurnLifecycleError


class MistralTurnError(RuntimeError):
    pass


class MistralTurnRunner:
    """Bind Mistral inference to the existing UnifiedDB/TurnLifecycle causal spine.

    This runner deliberately has no effect API. A Mistral response is completed and
    persisted as a canonical assistant turn before any later, separately admitted
    EffectGate turn can occur. Mistral therefore cannot become an effect authority.
    """

    def __init__(self, inference: MistralInference):
        self.inference = inference

    @staticmethod
    def _receipt(decision: dict[str, Any]) -> dict[str, Any]:
        receipt = decision.get("inference_receipt")
        if not isinstance(receipt, dict) or receipt.get("provider") != "mistral":
            raise MistralTurnError("Mistral inference receipt is missing or invalid")
        return receipt

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
