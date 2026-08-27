"""Clay U14 adaptive semantic read plane candidate.

Routes each read to the cheapest already-validated mechanism capable of answering it.
This is a context/retrieval plane, never canonical truth or effect authority.

Hard invariant: every mode, including exact and compiled-semantic fast paths, is bound to
one verified source/graph read basis. A receipt may never merely echo requested epochs.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Sequence
import hashlib,time

class ReadBasisError(RuntimeError): pass
class UnverifiedReadBasis(ReadBasisError): pass
class StaleReadBasis(ReadBasisError): pass

@dataclass(frozen=True)
class VerifiedReadBasis:
    basis_id:str
    source_epoch:int
    graph_epoch:int
    derivation_hash:str
    verified:bool=True
    authority:str='CONTEXT_ONLY_NO_EFFECT_AUTHORITY'

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
    read_basis_id:str
    derivation_hash:str
    latency_ns:int
    authority:str='ASSEMBLY_CONTEXT_ONLY'

class AdaptiveSemanticReadPlaneV14:
    def __init__(self,*,
        verify_read_basis:Callable[[AdaptiveReadRequest],VerifiedReadBasis],
        exact_lookup:Callable[[str,VerifiedReadBasis,int],Sequence[str]],
        compiled_semantic_lookup:Callable[[str,VerifiedReadBasis,int],Sequence[str]],
        resolve_entity:Callable[[str,VerifiedReadBasis],str|None],
        graph_lookup:Callable[[str,str,VerifiedReadBasis,int],Sequence[str]],
        compositional_lookup:Callable[[str,VerifiedReadBasis,int],Sequence[str]],
        fallback_lookup:Callable[[str,VerifiedReadBasis,int],Sequence[str]]):
        self.verify_read_basis=verify_read_basis
        self.exact_lookup=exact_lookup; self.compiled_semantic_lookup=compiled_semantic_lookup
        self.resolve_entity=resolve_entity; self.graph_lookup=graph_lookup
        self.compositional_lookup=compositional_lookup; self.fallback_lookup=fallback_lookup

    def _basis(self,r:AdaptiveReadRequest)->VerifiedReadBasis:
        b=self.verify_read_basis(r)
        if not isinstance(b,VerifiedReadBasis) or not b.verified:
            raise UnverifiedReadBasis(r.query_id)
        if b.source_epoch!=r.source_epoch or b.graph_epoch!=r.graph_epoch:
            raise StaleReadBasis(
                f'basis {b.source_epoch}/{b.graph_epoch} != request {r.source_epoch}/{r.graph_epoch}'
            )
        if not b.basis_id.strip() or not b.derivation_hash.strip():
            raise UnverifiedReadBasis('basis identity/hash required')
        return b

    def query(self,r:AdaptiveReadRequest)->AdaptiveReadReceipt:
        if not r.query_id.strip() or not r.text.strip(): raise ValueError('query_id/text required')
        if r.limit<=0 or r.limit>128: raise ValueError('invalid limit')
        started=time.perf_counter_ns(); resolved=None
        basis=self._basis(r)
        if r.exact_normalized_key:
            refs=tuple(self.exact_lookup(r.exact_normalized_key,basis,r.limit))
            if refs:return self._receipt(r,basis,'EXACT_INDEX_LOOKUP',refs,None,True,started)
        refs=tuple(self.compiled_semantic_lookup(r.text,basis,r.limit))
        if refs:
            # Sufficiency-stop is causal: never pad an already complete verified field with lexical noise.
            return self._receipt(r,basis,'VERIFIED_SEMANTIC_SUFFICIENCY_STOP',refs,None,True,started)
        resolved=self.resolve_entity(r.text,basis)
        if r.compositional:
            refs=tuple(self.compositional_lookup(r.text,basis,r.limit))
            if refs:return self._receipt(r,basis,'COMPOSITIONAL_PARETO_FRONTIER',refs,resolved,True,started)
        if resolved:
            refs=tuple(self.graph_lookup(resolved,r.text,basis,r.limit))
            if refs:return self._receipt(r,basis,'ENTITY_RESOLVED_CLAYGRAPH',refs,resolved,True,started)
        refs=tuple(self.fallback_lookup(r.text,basis,r.limit))
        return self._receipt(r,basis,'CONVENTIONAL_FALLBACK' if refs else 'MISS',refs,resolved,False,started)

    @staticmethod
    def _receipt(r,basis,mode,refs,resolved,sufficient,started):
        return AdaptiveReadReceipt(r.query_id,hashlib.sha256(r.text.encode()).hexdigest(),mode,
            tuple(refs[:r.limit]),resolved,sufficient,False,r.source_epoch,r.graph_epoch,
            basis.basis_id,basis.derivation_hash,time.perf_counter_ns()-started)
