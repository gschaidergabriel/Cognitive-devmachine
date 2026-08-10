"""Clay U14 adaptive semantic read plane candidate.

Routes each read to the cheapest already-validated mechanism capable of answering it.
This is a context/retrieval plane, never canonical truth or effect authority.

Measured design basis:
- exact resolved key: ordinary indexed lookup remains the latency floor;
- coherent compiled semantic field: return sufficient field without lexical padding;
- unresolved name/description: evidence-bound entity resolution before graph traversal;
- compositional route query: epoch-bound precompiled Pareto possibility frontier;
- unknown/uncompiled query: conventional lexical/hybrid fallback.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Sequence
import hashlib,time

@dataclass(frozen=True)
class AdaptiveReadRequest:
    query_id:str
    text:str
    source_epoch:int
    graph_epoch:int
    exact_normalized_key:str|None=None
    compositional:bool=False
    limit:int=8

@dataclass(frozen=True)
class AdaptiveReadReceipt:
    query_id:str
    query_hash:str
    mode:str
    refs:tuple[str,...]
    resolved_logical_id:str|None
    sufficient:bool
    lexical_padding_used:bool
    source_epoch:int
    graph_epoch:int
    latency_ns:int
    authority:str='ASSEMBLY_CONTEXT_ONLY'

class AdaptiveSemanticReadPlaneV14:
    def __init__(self,*,
        exact_lookup:Callable[[str,int],Sequence[str]],
        compiled_semantic_lookup:Callable[[str,int],Sequence[str]],
        resolve_entity:Callable[[str,int],str|None],
        graph_lookup:Callable[[str,str,int,int,int],Sequence[str]],
        compositional_lookup:Callable[[str,int,int,int],Sequence[str]],
        fallback_lookup:Callable[[str,int],Sequence[str]]):
        self.exact_lookup=exact_lookup; self.compiled_semantic_lookup=compiled_semantic_lookup
        self.resolve_entity=resolve_entity; self.graph_lookup=graph_lookup
        self.compositional_lookup=compositional_lookup; self.fallback_lookup=fallback_lookup

    def query(self,r:AdaptiveReadRequest)->AdaptiveReadReceipt:
        if not r.query_id.strip() or not r.text.strip(): raise ValueError('query_id/text required')
        if r.limit<=0 or r.limit>128: raise ValueError('invalid limit')
        started=time.perf_counter_ns(); resolved=None
        if r.exact_normalized_key:
            refs=tuple(self.exact_lookup(r.exact_normalized_key,r.limit))
            if refs:return self._receipt(r,'EXACT_INDEX_LOOKUP',refs,None,True,started)
        refs=tuple(self.compiled_semantic_lookup(r.text,r.limit))
        if refs:
            # Sufficiency-stop is causal: never pad an already complete verified field with lexical noise.
            return self._receipt(r,'VERIFIED_SEMANTIC_SUFFICIENCY_STOP',refs,None,True,started)
        resolved=self.resolve_entity(r.text,r.source_epoch)
        if r.compositional:
            refs=tuple(self.compositional_lookup(r.text,r.source_epoch,r.graph_epoch,r.limit))
            if refs:return self._receipt(r,'COMPOSITIONAL_PARETO_FRONTIER',refs,resolved,True,started)
        if resolved:
            refs=tuple(self.graph_lookup(resolved,r.text,r.source_epoch,r.graph_epoch,r.limit))
            if refs:return self._receipt(r,'ENTITY_RESOLVED_CLAYGRAPH',refs,resolved,True,started)
        refs=tuple(self.fallback_lookup(r.text,r.limit))
        return self._receipt(r,'CONVENTIONAL_FALLBACK' if refs else 'MISS',refs,resolved,False,started)

    @staticmethod
    def _receipt(r,mode,refs,resolved,sufficient,started):
        return AdaptiveReadReceipt(r.query_id,hashlib.sha256(r.text.encode()).hexdigest(),mode,
            tuple(refs[:r.limit]),resolved,sufficient,False,r.source_epoch,r.graph_epoch,
            time.perf_counter_ns()-started)
