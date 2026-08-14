from __future__ import annotations

"""Evidence-bound physical backend selector for the UnifiedDB / ClayGraph research candidate.

This is NOT a new semantic authority plane. It selects a physical executor only after the
caller has already classified the requested semantic access shape. UnifiedDB/Clay semantics,
query receipts, graph projection receipts and effect authority remain outside and above this
router.

Research invariant: there is no universally "best database" entry. The router chooses the
cheapest SAFE executor that satisfies the quality floor for the current query class and
basis. Missing/stale/proxy evidence causes abstention or a safer fallback, never invented
capability.
"""

from dataclasses import dataclass
from enum import Enum
import math
import time
from typing import Iterable


class QueryClass(str, Enum):
    DIRECT_KEYED = "DIRECT_KEYED"
    LEXICAL = "LEXICAL"
    VECTOR_SEMANTIC = "VECTOR_SEMANTIC"
    RELATIONAL_MULTIHOP = "RELATIONAL_MULTIHOP"
    COUNTEREVIDENCE_CLOSURE = "COUNTEREVIDENCE_CLOSURE"


class RouteStatus(str, Enum):
    SELECTED = "SELECTED"
    ABSTAIN = "ABSTAIN"
    BLOCKED_CONFLICT = "BLOCKED_CONFLICT"
    BLOCKED_STALE_BASIS = "BLOCKED_STALE_BASIS"


@dataclass(frozen=True)
class QueryEnvelope:
    query_id: str
    query_class: QueryClass
    basis_epoch: int
    current_epoch: int
    conflict: bool = False
    ambiguity: bool = False
    requires_production_embedding: bool = False


@dataclass(frozen=True)
class BackendEvidence:
    backend_id: str
    query_classes: frozenset[QueryClass]
    measured_epoch: int
    verified: bool
    provenance_valid: bool
    evidence_class: str
    p50_us: float
    recall_at_5: float = 1.0
    all_evidence_at_5: float = 1.0
    ndcg_at_5: float = 1.0
    hit_at_1: float = 1.0
    ann_recall_at_5_vs_exact: float | None = None
    production_embedding_validated: bool = False
    authority: str = "CONTEXT_ONLY_NO_EFFECT_AUTHORITY"

    def __post_init__(self):
        vals=(self.p50_us,self.recall_at_5,self.all_evidence_at_5,self.ndcg_at_5,self.hit_at_1)
        if not all(math.isfinite(v) for v in vals):
            raise ValueError("backend evidence metrics must be finite")
        if self.p50_us < 0:
            raise ValueError("p50_us must be non-negative")
        for v in (self.recall_at_5,self.all_evidence_at_5,self.ndcg_at_5,self.hit_at_1):
            if not 0.0 <= v <= 1.0:
                raise ValueError("quality metric outside [0,1]")
        if self.ann_recall_at_5_vs_exact is not None and not 0.0 <= self.ann_recall_at_5_vs_exact <= 1.0:
            raise ValueError("ANN recall outside [0,1]")


@dataclass(frozen=True)
class RoutePolicy:
    max_measurement_epoch_lag: int = 0
    min_direct_hit_at_1: float = 1.0
    min_lexical_recall_at_5: float = 0.90
    min_vector_recall_at_5: float = 0.90
    min_ann_recall_at_5_vs_exact: float = 0.95
    min_multihop_recall_at_5: float = 0.95
    min_multihop_all_evidence_at_5: float = 0.95
    min_multihop_ndcg_at_5: float = 0.90


@dataclass(frozen=True)
class RouteDecision:
    query_id: str
    status: RouteStatus
    selected_backend: str | None
    query_class: QueryClass
    basis_epoch: int
    candidate_backends: tuple[str,...]
    rejected: tuple[tuple[str,str],...]
    reason: str
    authority: str = "PHYSICAL_EXECUTOR_SELECTION_ONLY_NO_EFFECT_AUTHORITY"
    decided_at_monotonic_ns: int = 0


class AdaptiveSemanticBackendRouterV1:
    def __init__(self, policy: RoutePolicy = RoutePolicy()):
        self.policy=policy

    def _reject_reason(self, q: QueryEnvelope, e: BackendEvidence) -> str | None:
        if not e.verified:
            return "UNVERIFIED_EVIDENCE"
        if not e.provenance_valid:
            return "INVALID_PROVENANCE"
        if e.authority != "CONTEXT_ONLY_NO_EFFECT_AUTHORITY":
            return "BACKEND_AUTHORITY_ESCALATION_FORBIDDEN"
        if q.query_class not in e.query_classes:
            return "QUERY_CLASS_UNSUPPORTED"
        lag=q.current_epoch-e.measured_epoch
        if lag < 0:
            return "FUTURE_MEASUREMENT_EPOCH"
        if lag > self.policy.max_measurement_epoch_lag:
            return "STALE_MEASUREMENT_EPOCH"

        if q.query_class is QueryClass.DIRECT_KEYED:
            if e.hit_at_1 < self.policy.min_direct_hit_at_1:
                return "DIRECT_ACCURACY_FLOOR"
        elif q.query_class is QueryClass.LEXICAL:
            if e.recall_at_5 < self.policy.min_lexical_recall_at_5:
                return "LEXICAL_RECALL_FLOOR"
        elif q.query_class is QueryClass.VECTOR_SEMANTIC:
            if q.requires_production_embedding and not e.production_embedding_validated:
                return "PROXY_OR_UNVALIDATED_EMBEDDING"
            if e.recall_at_5 < self.policy.min_vector_recall_at_5:
                return "VECTOR_RECALL_FLOOR"
            if e.ann_recall_at_5_vs_exact is not None and e.ann_recall_at_5_vs_exact < self.policy.min_ann_recall_at_5_vs_exact:
                return "ANN_RECALL_BELOW_EXACT_ORACLE_FLOOR"
        elif q.query_class in (QueryClass.RELATIONAL_MULTIHOP,QueryClass.COUNTEREVIDENCE_CLOSURE):
            if e.recall_at_5 < self.policy.min_multihop_recall_at_5:
                return "MULTIHOP_RECALL_FLOOR"
            if e.all_evidence_at_5 < self.policy.min_multihop_all_evidence_at_5:
                return "EVIDENCE_CLOSURE_FLOOR"
            if e.ndcg_at_5 < self.policy.min_multihop_ndcg_at_5:
                return "MULTIHOP_NDCG_FLOOR"
        return None

    @staticmethod
    def _quality_tuple(qclass: QueryClass, e: BackendEvidence) -> tuple[float,...]:
        if qclass is QueryClass.DIRECT_KEYED:
            return (e.hit_at_1,)
        if qclass is QueryClass.LEXICAL:
            return (e.recall_at_5,e.ndcg_at_5,e.hit_at_1)
        if qclass is QueryClass.VECTOR_SEMANTIC:
            ann=e.ann_recall_at_5_vs_exact if e.ann_recall_at_5_vs_exact is not None else 1.0
            return (e.recall_at_5,ann,e.ndcg_at_5)
        return (e.all_evidence_at_5,e.recall_at_5,e.ndcg_at_5)

    def route(self, q: QueryEnvelope, evidence: Iterable[BackendEvidence]) -> RouteDecision:
        now=time.monotonic_ns()
        if q.conflict or q.ambiguity:
            return RouteDecision(q.query_id,RouteStatus.BLOCKED_CONFLICT,None,q.query_class,q.basis_epoch,(),(),"CONFLICT_OR_AMBIGUITY_REQUIRES_REBUILD_OR_ADJUDICATION",decided_at_monotonic_ns=now)
        if q.basis_epoch != q.current_epoch:
            return RouteDecision(q.query_id,RouteStatus.BLOCKED_STALE_BASIS,None,q.query_class,q.basis_epoch,(),(),"QUERY_BASIS_NOT_CURRENT",decided_at_monotonic_ns=now)

        accepted=[]; rejected=[]
        for e in evidence:
            reason=self._reject_reason(q,e)
            if reason is None:
                accepted.append(e)
            else:
                rejected.append((e.backend_id,reason))
        if not accepted:
            return RouteDecision(q.query_id,RouteStatus.ABSTAIN,None,q.query_class,q.basis_epoch,(),tuple(sorted(rejected)),"NO_VERIFIED_BACKEND_MEETS_CURRENT_QUALITY_AND_SAFETY_FLOOR",decided_at_monotonic_ns=now)

        # First preserve quality: retain only the Pareto-front quality maximum for this query
        # class. Only then minimize measured latency. This prevents a fast but materially less
        # complete backend from silently winning a multi-hop/counterevidence query.
        scored=[(self._quality_tuple(q.query_class,e),e) for e in accepted]
        best_quality=max(s for s,_ in scored)
        quality_front=[e for s,e in scored if s==best_quality]
        selected=min(quality_front,key=lambda e:(e.p50_us,e.backend_id))
        return RouteDecision(
            query_id=q.query_id,
            status=RouteStatus.SELECTED,
            selected_backend=selected.backend_id,
            query_class=q.query_class,
            basis_epoch=q.basis_epoch,
            candidate_backends=tuple(sorted(e.backend_id for e in accepted)),
            rejected=tuple(sorted(rejected)),
            reason="MAX_VERIFIED_QUALITY_THEN_MIN_P50_LATENCY",
            decided_at_monotonic_ns=now,
        )
