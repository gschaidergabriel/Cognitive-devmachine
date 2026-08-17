from __future__ import annotations

from typing import Any

from .identity import CANONICAL_TERMINAL_NAMES, CANONICAL_USER_IDS, IdentityRouter
from .mistral_inference import MistralTokenInference
from .store import UnifiedDB
from .turn_lifecycle import TurnLifecycle


class MistralCanonicalTurnError(RuntimeError):
    """Fail-closed error for the canonical Mistral turn adapter."""


class MistralCanonicalTurn:
    """Run Mistral cognition through the existing UnifiedDB causal lifecycle.

    The model is inference only. Any ``effect`` supplied to ``run`` is a trusted
    caller-side request and is never parsed or inferred from model output. The
    provider response is durably re-ingested into UnifiedDB before EffectGate may
    execute that request.
    """

    def __init__(
        self,
        db: UnifiedDB,
        user_id: str,
        inference: MistralTokenInference,
        *,
        entityos_bridge=None,
    ):
        if user_id not in CANONICAL_USER_IDS:
            raise PermissionError("invalid canonical user")
        IdentityRouter(db, {})
        session_id = db.ensure_session(user_id, CANONICAL_TERMINAL_NAMES[user_id])
        self.db = db
        self.user_id = user_id
        self.session_id = session_id
        self.inference = inference
        self.lifecycle = TurnLifecycle(
            db,
            user_id,
            session_id,
            entityos_bridge=entityos_bridge,
        )

    @staticmethod
    def _provider_world(begin: dict[str, Any]) -> dict[str, Any]:
        return {
            "authority": "UnifiedDB",
            "identity": {
                "user_id": begin["user_id"],
                "session_id": begin["session_id"],
            },
            "causal": {
                "turn_id": begin["turn_id"],
                "episode_id": begin["episode_id"],
                "causal_id": begin["causal_id"],
                "generation": begin["generation"],
            },
            "resources": begin["resources"],
            "workspace": begin["workspace"],
            "needle": begin.get("needle", {}),
            "hyperpositions": begin.get("hyperpositions", []),
            "context": begin["context"],
            "effect_law": (
                "Model output has no effect authority. A trusted caller may request "
                "EffectGate only after this provider response is re-ingested."
            ),
        }

    def _validate_decision(self, decision: Any) -> tuple[str, str]:
        if not isinstance(decision, dict):
            raise MistralCanonicalTurnError("Mistral decision must be an object")
        if decision.get("provider") != "mistral":
            raise MistralCanonicalTurnError("Mistral provider identity mismatch")
        if decision.get("selection") != "respond":
            raise MistralCanonicalTurnError("Mistral selection is outside inference-only boundary")
        if decision.get("effect") is not None:
            raise MistralCanonicalTurnError("Mistral model attempted to carry effect authority")
        text = decision.get("text")
        model = decision.get("model")
        if not isinstance(text, str) or not text.strip() or len(text) > 200_000:
            raise MistralCanonicalTurnError("Mistral text is outside admitted bound")
        if not isinstance(model, str) or not model.strip():
            raise MistralCanonicalTurnError("Mistral model identity is missing")
        expected_model = getattr(self.inference, "model", None)
        if not isinstance(expected_model, str) or model != expected_model:
            raise MistralCanonicalTurnError("Mistral model identity changed across inference boundary")
        return text, model

    @staticmethod
    def _validate_trusted_effect(effect: Any) -> tuple[str, str, list[str] | None]:
        if not isinstance(effect, dict):
            raise MistralCanonicalTurnError("trusted effect must be an object")
        extra = set(effect) - {"capability", "target", "argv"}
        if extra:
            raise MistralCanonicalTurnError("trusted effect contains unknown fields")
        capability = effect.get("capability")
        target = effect.get("target")
        argv = effect.get("argv")
        if not isinstance(capability, str) or not capability:
            raise MistralCanonicalTurnError("trusted effect capability is invalid")
        if not isinstance(target, str) or not target:
            raise MistralCanonicalTurnError("trusted effect target is invalid")
        if argv is not None and (
            not isinstance(argv, list)
            or any(not isinstance(item, str) for item in argv)
        ):
            raise MistralCanonicalTurnError("trusted effect argv is invalid")
        return capability, target, argv

    def run(
        self,
        prompt: str,
        *,
        resources: list[str] | None = None,
        effect: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        begin: dict[str, Any] | None = None
        reingested: dict[str, Any] | None = None
        effect_result: dict[str, Any] | None = None
        try:
            begin = self.lifecycle.begin(
                prompt,
                resources,
                input_source="mistral-runtime:input",
            )
            decision = self.inference.reason(self._provider_world(begin), prompt)
            text, model = self._validate_decision(decision)
            reingested = self.lifecycle.reingest_provider_response(
                text,
                provider="mistral",
                model=model,
                expected_causal_id=begin["causal_id"],
                expected_generation=begin["generation"],
            )
            if effect is not None:
                capability, target, argv = self._validate_trusted_effect(effect)
                effect_result = self.lifecycle.request_effect(
                    capability,
                    target,
                    argv,
                    expected_causal_id=begin["causal_id"],
                    expected_generation=begin["generation"],
                )
            completed = self.lifecycle.complete_reingested_provider_response(
                expected_causal_id=begin["causal_id"],
                expected_generation=begin["generation"],
            )
            if not completed.get("completed"):
                raise MistralCanonicalTurnError("canonical Mistral turn did not complete")
            return {
                "user_id": begin["user_id"],
                "session_id": begin["session_id"],
                "turn_id": begin["turn_id"],
                "assistant_turn_id": completed["assistant_turn_id"],
                "episode_id": begin["episode_id"],
                "causal_id": begin["causal_id"],
                "generation": begin["generation"],
                "provider": "mistral",
                "model": model,
                "text": text,
                "response_reingested": bool(reingested.get("reingested")),
                "effect": effect_result,
            }
        except Exception:
            if begin is not None:
                try:
                    self.lifecycle.abort(
                        "mistral_turn_failed",
                        provenance_source="mistral-runtime:failure",
                        expected_causal_id=begin["causal_id"],
                    )
                except Exception as abort_exc:
                    raise MistralCanonicalTurnError(
                        "Mistral turn failed and its exact canonical turn could not be aborted"
                    ) from abort_exc
            raise
