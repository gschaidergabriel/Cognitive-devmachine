from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from unifieddb_claygraph_retrieval_candidate import ProjectionBasis

@dataclass(frozen=True)
class EntityResolvedRetrievalReceipt:
    query_id: str
    resolution_class: str
    resolution_confidence: float
    resolved_logical_id: str | None
    resolution_candidates: tuple[str, ...]
    refs: tuple[str, ...]
    latency_us: int
    authority: str = 'CONTEXT_ONLY'

class EntityResolvedNLClayGraphCandidate:
    """Evidence-bound entity resolution wrapper for the NL+ClayGraph fallback.

    Only EXACT_LOGICAL_ID/EVIDENCE_ALIAS may seed graph traversal. Ambiguous,
    low-confidence and missing identities abstain from graph anchoring and fall back to
    lexical retrieval. Resolution never mints identity, truth or effect authority.
    """
    def __init__(self, resolver: Any, fallback: Any):
        self.resolver = resolver
        self.fallback = fallback

    def query(self, *, query_id: str, text: str, basis: ProjectionBasis, limit: int = 8):
        r = self.resolver.resolve(text, source_epoch=basis.source_epoch)
        admitted = r.logical_id if r.resolution_class in ('EXACT_LOGICAL_ID', 'EVIDENCE_ALIAS') else None
        enriched = text if admitted is None else f'{text} {admitted}'
        fb = self.fallback.query(
            query_id=query_id,
            text=enriched,
            basis=basis,
            limit=limit,
            graph_enabled=admitted is not None,
        )
        return EntityResolvedRetrievalReceipt(
            query_id,
            r.resolution_class,
            float(r.confidence),
            admitted,
            tuple(r.candidates),
            tuple(x.record_id for x in fb.results),
            int(fb.latency_us + r.latency_ns // 1000),
        )
