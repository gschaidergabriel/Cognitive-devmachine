from __future__ import annotations

"""Harness-side model-organ quarantine for Database Pulse research candidates.

A model is an optional replaceable organ, never the persistent FRANK entity. Provider/model
identity is bound outside model output. The wrapped inference result is returned as a candidate
envelope suitable for DatabasePulseRuntime V1/V2/V3, which persists it as epistemic UNKNOWN.
Nothing in this adapter grants semantic mutation or effect authority.
"""

from dataclasses import asdict, dataclass
from typing import Any, Callable

from research_entity.harness.reference.state_ledger import cjson, h


@dataclass(frozen=True)
class ModelOrganIdentity:
    provider: str
    model: str
    revision: str
    organ_id: str

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"model organ {name} required")


class QuarantinedModelOrgan:
    """Callable adapter accepted by Database Pulse's optional model_assistant slot."""

    def __init__(
        self,
        identity: ModelOrganIdentity,
        infer: Callable[[dict[str, Any]], Any],
        *,
        call_id_factory: Callable[[dict[str, Any]], str] | None = None,
    ):
        identity.validate()
        if not callable(infer):
            raise TypeError("infer must be callable")
        self.identity = identity
        self.infer = infer
        self.call_id_factory = call_id_factory or (
            lambda ctx: f"{identity.organ_id}:{ctx.get('pulse_id','UNKNOWN')}"
        )

    def __call__(self, context: dict[str, Any]) -> dict[str, Any]:
        if context.get("authority") != "CONTEXT_ONLY_NO_EFFECT_AUTHORITY":
            raise ValueError("model organ requires explicit context-only authority boundary")
        call_id = self.call_id_factory(context)
        if not isinstance(call_id, str) or not call_id.strip():
            raise ValueError("model organ call_id required")
        raw = self.infer(context)
        cjson(raw)  # canonicalize/finite-check before returning anything to Pulse
        identity_body = asdict(self.identity)
        envelope = {
            "model_organ": identity_body,
            "model_organ_identity_hash": h(identity_body),
            "call_id": call_id,
            "pulse_id": context.get("pulse_id"),
            "basis_epoch": context.get("basis_epoch"),
            "assembly_hash": context.get("assembly_hash"),
            "candidate": raw,
            "candidate_hash": h(raw),
            "semantic_mutation_authority": "NONE",
            "effect_authority": "NONE",
            "authority": "MODEL_ORGAN_CANDIDATE_ONLY_REQUIRES_EXTERNAL_ADMISSION",
        }
        cjson(envelope)
        return envelope
