from __future__ import annotations

import dataclasses
import hashlib
from typing import Any, Mapping, Protocol

from .cortex import CortexEvent, CortexProjection, RetinaFeedback, stable_digest


class RetinaBackend(Protocol):
    """Minimal replaceable Retina interface.

    FrankEye, a future Retina v9, remote camera organ or a test double can all satisfy it.
    This keeps Retina maintainable even though its functional coupling to Cortex is strong.
    """

    def analyze(self, image_path: str, *, deep: bool = False) -> Any: ...


@dataclasses.dataclass(frozen=True)
class RetinaCapture:
    capture_id: str
    raw_capture_hash: str
    causal_id: str
    meta_order: int
    source_commit: str
    image_locator: str | None = None

    def validate(self) -> None:
        if not self.capture_id or not self.raw_capture_hash or not self.causal_id:
            raise ValueError("retina_capture_identity_required")
        if self.meta_order < 0:
            raise ValueError("retina_meta_order_must_be_nonnegative")


@dataclasses.dataclass(frozen=True)
class RetinaRunReceipt:
    schema: str
    capture_id: str
    causal_id: str
    meta_order: int
    backend: str
    mode: str
    raw_capture_hash: str
    result_digest: str
    cortex_feedback_id: str | None
    effect_authority: bool = False

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class RetinaCortexBridge:
    """Strongly coupled but maintainable Retina <-> Cortex boundary.

    Retina remains independently replaceable. Coupling is strong because every visual
    observation is projected into Cortex state and every projection can immediately return
    an attention directive for the next Retina sampling/inference pass.

    This adapter never opens a camera by itself and never grants effect authority.
    """

    def __init__(self, *, source_name: str = "project-frankenstein.frank_eye") -> None:
        self.source_name = source_name
        self._last_feedback: RetinaFeedback | None = None

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def project_result(
        self,
        capture: RetinaCapture,
        result: str | Mapping[str, Any],
        *,
        backend: str = "frank_eye",
        attention_context: Mapping[str, Any] | None = None,
    ) -> CortexEvent:
        capture.validate()
        context = dict(attention_context or {})
        payload: dict[str, Any] = {
            "raw_capture_hash": capture.raw_capture_hash,
            "capture_id": capture.capture_id,
            "backend": backend,
            "source_commit": capture.source_commit,
            "attention_priority": float(context.get("attention_priority", 0.5)),
            "expected_labels": tuple(context.get("expected_labels", ()) or ()),
            "unresolved_visual_questions": tuple(
                context.get("unresolved_visual_questions", ()) or ()
            ),
            "text_salient": bool(context.get("text_salient", False)),
            "social_context": bool(context.get("social_context", False)),
            "novelty_high": bool(context.get("novelty_high", False)),
            "conflict_handles": tuple(context.get("conflict_handles", ()) or ()),
        }

        if isinstance(result, Mapping):
            payload.update(dict(result))
        else:
            payload["description"] = str(result)
            payload["description_confidence"] = 0.6

        stable = {
            "capture_id": capture.capture_id,
            "raw_capture_hash": capture.raw_capture_hash,
            "source_commit": capture.source_commit,
            "backend": backend,
            "result": payload,
        }
        return CortexEvent(
            event_id=stable_digest(stable)[:32],
            kind="retina.observation",
            causal_id=capture.causal_id,
            meta_order=capture.meta_order,
            evidence_class="VERIFIED_DERIVED",
            source=self.source_name,
            payload=payload,
            provenance={
                "raw_capture_hash": capture.raw_capture_hash,
                "source_commit": capture.source_commit,
                "backend": backend,
            },
        )

    def consume_projection(self, projection: CortexProjection) -> RetinaFeedback | None:
        self._last_feedback = projection.retina_feedback
        return self._last_feedback

    @property
    def last_feedback(self) -> RetinaFeedback | None:
        return self._last_feedback

    def run_backend(
        self,
        backend: RetinaBackend,
        capture: RetinaCapture,
        *,
        feedback: RetinaFeedback | None = None,
    ) -> tuple[Any, RetinaRunReceipt]:
        """Execute only the Retina inference organ, never a world/device effect.

        The image locator must already refer to a captured frame. This method does not
        open a camera or mutate device state.
        """
        capture.validate()
        if not capture.image_locator:
            raise ValueError("image_locator_required_for_backend_run")
        fb = feedback or self._last_feedback
        deep = bool(fb and fb.request_deep_features)
        result = backend.analyze(capture.image_locator, deep=deep)
        result_digest = stable_digest(
            result if isinstance(result, Mapping) else {"text": str(result)}
        )
        receipt = RetinaRunReceipt(
            schema="OMEGA_RETINA_RUN_RECEIPT/v1",
            capture_id=capture.capture_id,
            causal_id=capture.causal_id,
            meta_order=capture.meta_order,
            backend=backend.__class__.__name__,
            mode="deep" if deep else "fast",
            raw_capture_hash=capture.raw_capture_hash,
            result_digest=result_digest,
            cortex_feedback_id=fb.feedback_id if fb else None,
            effect_authority=False,
        )
        return result, receipt


__all__ = [
    "RetinaBackend",
    "RetinaCapture",
    "RetinaCortexBridge",
    "RetinaRunReceipt",
]
