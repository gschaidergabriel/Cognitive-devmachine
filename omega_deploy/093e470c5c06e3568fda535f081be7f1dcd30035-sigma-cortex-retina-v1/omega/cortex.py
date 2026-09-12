from __future__ import annotations

import dataclasses
import hashlib
import json
from collections import deque
from typing import Any, Mapping

EVIDENCE_CLASSES = {
    "OBSERVED",
    "VERIFIED_DERIVED",
    "SIMULATED",
    "MODEL_GENERATED",
    "SELF_INTERVENTION",
    "UNKNOWN",
}

ADAPTER_STATES = {
    "NURSERY",
    "SHADOW",
    "CANARY",
    "ACTIVE",
    "QUARANTINED",
    "RETIRED",
}


def stable_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclasses.dataclass(frozen=True)
class CortexEvent:
    event_id: str
    kind: str
    causal_id: str
    meta_order: int
    evidence_class: str
    source: str
    payload: Mapping[str, Any]
    provenance: Mapping[str, Any]

    def validate(self) -> None:
        if not self.event_id or not self.kind or not self.causal_id:
            raise ValueError("event_identity_required")
        if self.meta_order < 0:
            raise ValueError("meta_order_must_be_nonnegative")
        if self.evidence_class not in EVIDENCE_CLASSES:
            raise ValueError(f"unsupported_evidence_class:{self.evidence_class}")
        if not self.source:
            raise ValueError("source_required")


@dataclasses.dataclass(frozen=True)
class StateAtom:
    atom_id: str
    role: str
    value: Any
    evidence_class: str
    source_event_id: str
    meta_order: int
    confidence: float = 1.0

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class RetinaFeedback:
    feedback_id: str
    causal_id: str
    priority: float
    mode: str
    request_ocr: bool
    request_faces: bool
    request_deep_features: bool
    expected_labels: tuple[str, ...]
    unresolved_visual_questions: tuple[str, ...]
    source_meta_order: int

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class AdapterCandidate:
    artifact_id: str
    base_model_hash: str
    scope: str
    parent_artifact_id: str | None
    training_cutoff_m: int
    training_data_hashes: tuple[str, ...]
    artifact_hash: str
    producer: str
    state: str = "NURSERY"

    def validate(self) -> None:
        if self.state not in ADAPTER_STATES:
            raise ValueError(f"bad_adapter_state:{self.state}")
        if not self.artifact_id or not self.base_model_hash or not self.artifact_hash:
            raise ValueError("artifact_identity_required")
        if self.training_cutoff_m < 0:
            raise ValueError("training_cutoff_m_must_be_nonnegative")
        if not self.scope:
            raise ValueError("adapter_scope_required")


@dataclasses.dataclass(frozen=True)
class PromotionDecision:
    state: str
    eligible: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class CortexProjection:
    schema: str
    causal_id: str
    meta_order: int
    state_atoms: tuple[StateAtom, ...]
    grid_proposals: tuple[Mapping[str, Any], ...]
    retina_feedback: RetinaFeedback | None
    learning_candidates: tuple[Mapping[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "causal_id": self.causal_id,
            "meta_order": self.meta_order,
            "state_atoms": [x.as_dict() for x in self.state_atoms],
            "grid_proposals": [dict(x) for x in self.grid_proposals],
            "retina_feedback": self.retina_feedback.as_dict() if self.retina_feedback else None,
            "learning_candidates": [dict(x) for x in self.learning_candidates],
        }


class CortexCore:
    """OMEGA adaptive compiled cortex control plane.

    This class intentionally owns no external effect authority and does not initialize
    SOMA, Retina, GRID or UnifiedDB. Those remain replaceable organs/providers.

    The cortex is native OMEGA integration tissue:
      perception -> state atoms/world candidate -> attention feedback -> GRID proposal
      repeated successful trajectory -> adapter candidate -> independent harness -> promotion proposal
    """

    def __init__(self, *, history_limit: int = 512) -> None:
        self._history: deque[CortexEvent] = deque(maxlen=max(16, int(history_limit)))
        self._atoms: dict[str, StateAtom] = {}
        self._last_m = -1

    @property
    def last_meta_order(self) -> int:
        return self._last_m

    def ingest(self, event: CortexEvent) -> CortexProjection:
        event.validate()
        if event.meta_order < self._last_m:
            raise ValueError("causal_order_regression")
        self._last_m = max(self._last_m, event.meta_order)
        self._history.append(event)

        if event.kind.startswith("retina."):
            return self._ingest_retina(event)
        if event.kind.startswith("world."):
            return self._ingest_world(event)
        if event.kind.startswith("grid.reentry"):
            return self._ingest_reentry(event)
        return self._generic_projection(event)

    def _atom(
        self,
        event: CortexEvent,
        *,
        role: str,
        value: Any,
        confidence: float = 1.0,
        evidence_class: str | None = None,
    ) -> StateAtom:
        cls = evidence_class or event.evidence_class
        if cls not in EVIDENCE_CLASSES:
            raise ValueError(f"unsupported_evidence_class:{cls}")
        atom_id = stable_digest(
            {
                "role": role,
                "source_event_id": event.event_id,
                "meta_order": event.meta_order,
                "value": value,
            }
        )[:32]
        atom = StateAtom(
            atom_id=atom_id,
            role=role,
            value=value,
            evidence_class=cls,
            source_event_id=event.event_id,
            meta_order=event.meta_order,
            confidence=max(0.0, min(1.0, float(confidence))),
        )
        self._atoms[role] = atom
        return atom

    def _ingest_retina(self, event: CortexEvent) -> CortexProjection:
        p = dict(event.payload)
        capture_hash = str(p.get("raw_capture_hash") or "")
        if not capture_hash:
            raise ValueError("retina_raw_capture_hash_required")

        # The raw capture may be OBSERVED, VERIFIED_DERIVED or UNKNOWN. Derived visual
        # interpretation can become VERIFIED_DERIVED only when its source is already
        # OBSERVED/VERIFIED_DERIVED. UNKNOWN must remain UNKNOWN; recurrence, coherence
        # or model output never upgrades evidence class.
        if event.evidence_class not in {"VERIFIED_DERIVED", "OBSERVED", "UNKNOWN"}:
            raise ValueError("retina_invalid_evidence_class")
        derived_class = (
            "VERIFIED_DERIVED"
            if event.evidence_class in {"VERIFIED_DERIVED", "OBSERVED"}
            else "UNKNOWN"
        )

        atoms: list[StateAtom] = [
            self._atom(event, role="vision.capture_hash", value=capture_hash, confidence=1.0),
        ]

        description = p.get("description")
        if isinstance(description, str) and description.strip():
            atoms.append(
                self._atom(
                    event,
                    role="vision.description",
                    value=description.strip(),
                    confidence=float(p.get("description_confidence", 0.6)),
                    evidence_class=derived_class,
                )
            )

        labels = tuple(str(x) for x in p.get("labels", ()) if str(x).strip())
        if labels:
            atoms.append(
                self._atom(
                    event,
                    role="vision.labels",
                    value=labels,
                    confidence=float(p.get("label_confidence", 0.6)),
                    evidence_class=derived_class,
                )
            )

        ocr = tuple(str(x) for x in p.get("ocr", ()) if str(x).strip())
        if ocr:
            atoms.append(
                self._atom(
                    event,
                    role="vision.ocr",
                    value=ocr,
                    confidence=float(p.get("ocr_confidence", 0.7)),
                    evidence_class=derived_class,
                )
            )

        faces = int(p.get("face_count", 0) or 0)
        atoms.append(
            self._atom(
                event,
                role="vision.face_count",
                value=max(0, faces),
                confidence=float(p.get("face_confidence", 0.7)),
                evidence_class=derived_class,
            )
        )

        # Strong bidirectional coupling: perception immediately produces a feedback directive,
        # but the directive is a request to Retina, not a direct mutation of Retina internals.
        unresolved = tuple(
            str(x) for x in p.get("unresolved_visual_questions", ()) if str(x).strip()
        )
        expected = tuple(str(x) for x in p.get("expected_labels", ()) if str(x).strip())
        need_deep = bool(unresolved) or bool(p.get("novelty_high"))
        need_ocr = bool(p.get("text_salient")) or bool(ocr)
        need_faces = bool(p.get("social_context")) or faces > 0
        feedback = RetinaFeedback(
            feedback_id=stable_digest(
                {
                    "event_id": event.event_id,
                    "kind": "retina_feedback",
                    "m": event.meta_order,
                    "expected": expected,
                    "unresolved": unresolved,
                }
            )[:32],
            causal_id=event.causal_id,
            priority=max(0.0, min(1.0, float(p.get("attention_priority", 0.5)))),
            mode="deep" if need_deep else "fast",
            request_ocr=need_ocr,
            request_faces=need_faces,
            request_deep_features=need_deep,
            expected_labels=expected,
            unresolved_visual_questions=unresolved,
            source_meta_order=event.meta_order,
        )

        proposal = {
            "schema": "OMEGA_GRID_PROPOSAL/v1",
            "proposal_id": stable_digest(
                {"event_id": event.event_id, "kind": "visual_salience"}
            )[:32],
            "source": "omega.cortex",
            "role": "visual_perception",
            "causal_id": event.causal_id,
            "meta_order": event.meta_order,
            "evidence_class": derived_class,
            "utility": max(0.0, min(1.0, float(p.get("attention_priority", 0.5)))),
            "content_handles": tuple(a.atom_id for a in atoms),
            "conflict_handles": tuple(
                str(x) for x in p.get("conflict_handles", ()) if str(x).strip()
            ),
            "effect_authority": False,
        }

        return CortexProjection(
            schema="OMEGA_CORTEX_PROJECTION/v1",
            causal_id=event.causal_id,
            meta_order=event.meta_order,
            state_atoms=tuple(atoms),
            grid_proposals=(proposal,),
            retina_feedback=feedback,
            learning_candidates=(),
        )

    def _ingest_world(self, event: CortexEvent) -> CortexProjection:
        atom = self._atom(
            event,
            role=str(event.payload.get("role") or "world.state"),
            value=event.payload.get("value"),
            confidence=float(event.payload.get("confidence", 1.0)),
        )
        return CortexProjection(
            schema="OMEGA_CORTEX_PROJECTION/v1",
            causal_id=event.causal_id,
            meta_order=event.meta_order,
            state_atoms=(atom,),
            grid_proposals=(),
            retina_feedback=None,
            learning_candidates=(),
        )

    def _ingest_reentry(self, event: CortexEvent) -> CortexProjection:
        # Reentry is kept as state, not automatically converted into an adapter or truth.
        atom = self._atom(
            event,
            role="grid.reentry",
            value=dict(event.payload),
            confidence=1.0,
        )
        return CortexProjection(
            schema="OMEGA_CORTEX_PROJECTION/v1",
            causal_id=event.causal_id,
            meta_order=event.meta_order,
            state_atoms=(atom,),
            grid_proposals=(),
            retina_feedback=None,
            learning_candidates=(),
        )

    def _generic_projection(self, event: CortexEvent) -> CortexProjection:
        atom = self._atom(
            event,
            role=f"event.{event.kind}",
            value=dict(event.payload),
            confidence=1.0,
        )
        return CortexProjection(
            schema="OMEGA_CORTEX_PROJECTION/v1",
            causal_id=event.causal_id,
            meta_order=event.meta_order,
            state_atoms=(atom,),
            grid_proposals=(),
            retina_feedback=None,
            learning_candidates=(),
        )

    @staticmethod
    def evaluate_adapter_candidate(
        candidate: AdapterCandidate,
        harness_receipt: Mapping[str, Any],
    ) -> PromotionDecision:
        """Independent promotion pre-gate.

        This does not activate an adapter. It only determines whether the candidate is
        structurally eligible to be handed to the canonical independent promotion/effect path.
        """
        reasons: list[str] = []
        candidate.validate()

        if harness_receipt.get("independent") is not True:
            reasons.append("harness_not_independent")
        if harness_receipt.get("model_generated") is not False:
            reasons.append("harness_receipt_must_not_be_model_generated")
        if str(harness_receipt.get("candidate_artifact_hash", "")) != candidate.artifact_hash:
            reasons.append("artifact_hash_mismatch")
        if harness_receipt.get("hard_regressions"):
            reasons.append("hard_regression")
        improved_groups = {
            str(x) for x in harness_receipt.get("improved_groups", ()) if str(x).strip()
        }
        if len(improved_groups) < 2:
            reasons.append("insufficient_cross_group_progress")
        if not improved_groups.intersection({"capability", "epistemic", "architecture"}):
            reasons.append("no_core_cognitive_progress")
        if harness_receipt.get("fresh_holdout") is not True:
            reasons.append("fresh_holdout_missing")
        if harness_receipt.get("effect_authority") is True:
            reasons.append("candidate_attempted_effect_authority")

        if reasons:
            return PromotionDecision(
                state="NURSERY",
                eligible=False,
                reasons=tuple(sorted(set(reasons))),
            )
        return PromotionDecision(
            state="ELIGIBLE_FOR_CANARY_REVIEW",
            eligible=True,
            reasons=(
                "independent_harness_passed",
                "activation_still_requires_canonical_promotion_path",
            ),
        )

    def snapshot(self) -> dict[str, Any]:
        stable = {
            "schema": "OMEGA_CORTEX_STATE/v1",
            "last_meta_order": self._last_m,
            "atoms": {k: v.as_dict() for k, v in sorted(self._atoms.items())},
            "history_size": len(self._history),
        }
        return {**stable, "state_digest": stable_digest(stable)}


__all__ = [
    "AdapterCandidate",
    "CortexCore",
    "CortexEvent",
    "CortexProjection",
    "PromotionDecision",
    "RetinaFeedback",
    "StateAtom",
    "stable_digest",
]
