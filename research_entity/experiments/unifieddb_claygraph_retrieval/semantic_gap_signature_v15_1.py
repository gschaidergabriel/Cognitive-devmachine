from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from typing import Callable,Sequence

@dataclass(frozen=True)
class TypedGapSignature:
    source_epoch:int
    graph_epoch:int
    resolved_logical_id:str
    gap_terms:tuple[str,...]
    signature_hash:str

def build_gap_signature(*,source_epoch:int,graph_epoch:int,resolved_logical_id:str|None,gap_terms:Sequence[str])->TypedGapSignature:
    if source_epoch<0 or graph_epoch<0: raise ValueError('invalid epoch')
    if not resolved_logical_id: raise ValueError('resolved logical id required before graph expansion')
    terms=tuple(sorted(set(str(t).strip() for t in gap_terms if str(t).strip())))
    if not terms: raise ValueError('non-empty typed gap required')
    body={'source_epoch':source_epoch,'graph_epoch':graph_epoch,'resolved_logical_id':resolved_logical_id,'gap_terms':terms}
    digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return TypedGapSignature(source_epoch,graph_epoch,resolved_logical_id,terms,digest)

class SurfaceInvariantExpansionAdapter:
    """U15 expand adapter whose structural plan key ignores query wording after typing.

    Surface text is allowed upstream for entity/intent/requirement resolution. Once those
    semantics are typed, structural traversal is keyed only by verified epochs, resolved
    identity and explicit evidence-gap terms. This is context routing only, never truth or
    effect authority.
    """
    def __init__(self,*,resolved_logical_id:str,expand_typed:Callable[[TypedGapSignature,tuple[str,...],int],Sequence[object]]):
        if not resolved_logical_id: raise ValueError('resolved logical id required')
        self.resolved_logical_id=resolved_logical_id; self.expand_typed=expand_typed
    def __call__(self,query_text:str,terms:tuple[str,...],selected:tuple[str,...],source_epoch:int,graph_epoch:int,budget:int):
        del query_text
        sig=build_gap_signature(source_epoch=source_epoch,graph_epoch=graph_epoch,resolved_logical_id=self.resolved_logical_id,gap_terms=terms)
        return self.expand_typed(sig,selected,budget)
