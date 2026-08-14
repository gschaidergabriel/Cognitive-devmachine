from __future__ import annotations
from dataclasses import dataclass
import time
from typing import Any
from unifieddb_claygraph_retrieval_candidate import ProjectionBasis

@dataclass(frozen=True)
class CascadeReceipt:
    query_id: str
    mode: str
    refs: tuple[str, ...]
    source_epoch: int
    graph_epoch: int
    semantic_state_hash: str
    latency_us: int
    fastpath_latency_ns: int
    fallback_latency_us: int | None
    authority: str = 'CONTEXT_ONLY'

class U11NLClayGraphCascadeCandidate:
    """Fuses a verified U11 coherent semantic fastpath with NL+ClayGraph fallback.

    The fastpath object must expose U11's query API. The fallback must expose the
    UnifiedDBClayGraphRetrievalCandidate query API. Neither access path mints truth.
    """
    def __init__(self, fastpath: Any, fallback: Any):
        self.fastpath=fastpath; self.fallback=fallback

    def query(self, *, query_id: str, text: str, basis: ProjectionBasis, limit: int=8) -> CascadeReceipt:
        if basis.source_epoch < 0 or basis.graph_epoch < 0:
            raise ValueError('invalid epoch')
        started=time.perf_counter_ns()
        fast=self.fastpath.query(text,source_epoch=basis.source_epoch,graph_epoch=basis.graph_epoch,limit=limit)
        if getattr(fast,'refs',()):
            refs=tuple(fast.refs)
            return CascadeReceipt(query_id,getattr(fast,'mode','COHERENT_SEMANTIC_FASTPATH'),refs,basis.source_epoch,basis.graph_epoch,basis.semantic_state_hash,(time.perf_counter_ns()-started)//1000,int(getattr(fast,'latency_ns',0)),None)
        fb=self.fallback.query(query_id=query_id,text=text,basis=basis,limit=limit)
        refs=tuple(r.record_id for r in fb.results)
        return CascadeReceipt(query_id,'NL_CLAYGRAPH_FALLBACK',refs,basis.source_epoch,basis.graph_epoch,basis.semantic_state_hash,(time.perf_counter_ns()-started)//1000,int(getattr(fast,'latency_ns',0)),int(fb.latency_us))
