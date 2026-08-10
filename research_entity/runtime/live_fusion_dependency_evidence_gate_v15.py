from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

INDEX_ONLY = "INDEX_ONLY"
NEXT_CHECKPOINT = "NEXT_CHECKPOINT"
INTERRUPT_NEXT_SAFE_POINT = "INTERRUPT_NEXT_SAFE_POINT"
VALID_CLASSES = frozenset({INDEX_ONLY, NEXT_CHECKPOINT, INTERRUPT_NEXT_SAFE_POINT})

# Hard means sufficient to preserve a dependency-only blocking route in shadow evaluation.
# It still grants neither truth nor effect authority.
HARD_WITNESS_CLASSES = frozenset({
    "DECLARED_WORK_DEPENDENCY",
    "VERIFIED_CAUSAL",
    "REPLAY_CONFIRMED",
    "AUTHORITATIVE_REFERENCE",
    "RAW_CURRENT_WORK_MATCH",
    "UNIFIEDDB_DECLARED_DEPENDENCY",
    "MULTI_SOURCE_RECONCILED",
})
SOFT_WITNESS_CLASSES = frozenset({
    "CLAYGRAPH_CURRENT",
    "LOCAL_DEPENDENCY_INDEX",
    "ASSOCIATIVE_ONLY",
    "HEURISTIC",
    "EMBEDDING_NEIGHBOR",
    "LEXICAL",
    "UNKNOWN",
})

AUTHORITY = "SHADOW_ADJUDICATION_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY"


@dataclass(frozen=True)
class ParentRouteObservation:
    event_id: str
    worker_id: str
    base_class: str
    proposed_class: str
    direct_overlap: bool
    dependency_only: bool
    conflict: bool
    impact: float
    urgency: float
    projection_current: bool
    projection_worker_match: bool
    projection_epoch: str
    projection_state_hash: str
    v3_ack_verdict: str = "UNKNOWN"
    v3_ack_basis: str = "UNKNOWN"

    def normalized(self) -> "ParentRouteObservation":
        if not self.event_id or not self.worker_id:
            raise ValueError("event_id and worker_id required")
        if self.base_class not in VALID_CLASSES or self.proposed_class not in VALID_CLASSES:
            raise ValueError("invalid route class")
        if not 0.0 <= self.impact <= 1.0 or not 0.0 <= self.urgency <= 1.0:
            raise ValueError("impact/urgency must be within [0,1]")
        if not self.projection_epoch or not self.projection_state_hash:
            raise ValueError("projection identity required")
        if self.direct_overlap and self.dependency_only:
            raise ValueError("direct_overlap and dependency_only are mutually exclusive")
        return self


@dataclass(frozen=True)
class DependencyWitness:
    worker_id: str
    scope_id: str
    witness_class: str
    current: bool
    provenance_refs: tuple[str, ...] = ()

    def normalized(self) -> "DependencyWitness":
        if not self.worker_id or not self.scope_id or not self.witness_class:
            raise ValueError("worker_id, scope_id and witness_class required")
        if self.witness_class not in HARD_WITNESS_CLASSES | SOFT_WITNESS_CLASSES:
            raise ValueError("unknown witness_class")
        return DependencyWitness(
            worker_id=self.worker_id,
            scope_id=self.scope_id,
            witness_class=self.witness_class,
            current=bool(self.current),
            provenance_refs=tuple(sorted(set(self.provenance_refs))),
        )


@dataclass(frozen=True)
class EvidenceGatedRouteDecision:
    event_id: str
    worker_id: str
    parent_class: str
    gated_class: str
    hard_witness_count: int
    soft_witness_count: int
    stale_witness_count: int
    verification_required: bool
    projection_accepted: bool
    change: str
    reason: str
    authority: str = AUTHORITY


class DependencyEvidenceGateV15:
    """V3-compatible shadow gate for dependency-aware live-fusion blocking routes.

    V3 improves recipient completeness with a compact beacon/ack control plane. This orthogonal
    gate asks a different question: when a route is dependency-only, is the dependency evidence
    strong enough to preserve blocking power? A current ClayGraph/local-index association is
    useful for visibility and reconciliation but is not, by itself, a hard causal witness.
    """

    @staticmethod
    def _rank(route_class: str) -> int:
        return {INDEX_ONLY: 0, NEXT_CHECKPOINT: 1, INTERRUPT_NEXT_SAFE_POINT: 2}[route_class]

    def adjudicate(
        self,
        observation: ParentRouteObservation,
        witnesses: Iterable[DependencyWitness] = (),
    ) -> EvidenceGatedRouteDecision:
        o = observation.normalized()
        rows = [w.normalized() for w in witnesses]
        if any(w.worker_id != o.worker_id for w in rows):
            raise ValueError("dependency witness worker mismatch")

        current = [w for w in rows if w.current]
        hard = [w for w in current if w.witness_class in HARD_WITNESS_CLASSES]
        soft = [w for w in current if w.witness_class in SOFT_WITNESS_CLASSES]
        stale = [w for w in rows if not w.current]
        projection_ok = o.projection_current and o.projection_worker_match

        # V3 UNKNOWN/STALE acknowledgements explicitly require repair and cannot become hard.
        v3_uncertain = o.v3_ack_verdict in {"UNKNOWN", "STALE"}

        # Direct parent routes remain parent responsibility. Do not weaken an observed direct
        # conflict merely because graph/dependency evidence is absent.
        if o.direct_overlap or not o.dependency_only:
            gated = o.proposed_class
            verify = False
            reason = "direct/non-dependency parent route preserved"
        elif not projection_ok:
            gated = o.base_class
            verify = self._rank(o.proposed_class) > self._rank(o.base_class)
            reason = "dependency-only upgrade rejected: projection stale or worker-mismatched"
        elif o.proposed_class == INTERRUPT_NEXT_SAFE_POINT:
            if hard and not v3_uncertain:
                gated = INTERRUPT_NEXT_SAFE_POINT
                verify = False
                reason = "blocking dependency upgrade retained by current hard witness"
            else:
                # Keep the event visible but do not let associative/current-only dependency
                # evidence mint blocking power. V3 reconciliation/anti-entropy may later harden it.
                gated = NEXT_CHECKPOINT
                verify = True
                reason = "dependency-only interrupt capped pending hard witness/V3 reconciliation"
        elif o.proposed_class == NEXT_CHECKPOINT:
            gated = NEXT_CHECKPOINT
            verify = not bool(hard) or v3_uncertain
            reason = (
                "dependency checkpoint retained by hard witness"
                if hard and not v3_uncertain else
                "dependency checkpoint retained as non-blocking verification request"
            )
        else:
            gated = INDEX_ONLY
            verify = False
            reason = "dependency route remains index-only"

        if gated == o.proposed_class:
            change = "UNCHANGED"
        elif o.proposed_class == INTERRUPT_NEXT_SAFE_POINT and gated == NEXT_CHECKPOINT:
            change = "BLOCKING_DOWNGRADED_PENDING_EVIDENCE"
        elif self._rank(gated) < self._rank(o.proposed_class):
            change = "DOWNGRADED"
        else:
            change = "CHANGED"

        return EvidenceGatedRouteDecision(
            event_id=o.event_id,
            worker_id=o.worker_id,
            parent_class=o.proposed_class,
            gated_class=gated,
            hard_witness_count=len(hard),
            soft_witness_count=len(soft),
            stale_witness_count=len(stale),
            verification_required=verify,
            projection_accepted=projection_ok,
            change=change,
            reason=reason,
        )

    @staticmethod
    def summarize(decisions: Iterable[EvidenceGatedRouteDecision]) -> dict[str, int]:
        rows = list(decisions)
        return {
            "rows": len(rows),
            "blocking_downgrades": sum(
                r.change == "BLOCKING_DOWNGRADED_PENDING_EVIDENCE" for r in rows
            ),
            "verification_required": sum(r.verification_required for r in rows),
            "interrupts_after_gate": sum(r.gated_class == INTERRUPT_NEXT_SAFE_POINT for r in rows),
            "checkpoints_after_gate": sum(r.gated_class == NEXT_CHECKPOINT for r in rows),
            "index_only_after_gate": sum(r.gated_class == INDEX_ONLY for r in rows),
        }
