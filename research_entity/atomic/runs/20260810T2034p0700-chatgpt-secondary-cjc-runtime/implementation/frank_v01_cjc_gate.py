#!/usr/bin/env python3
"""Direct Frank v0.1 coordination gate for the ATOMIC CJC candidate.

Research-only executable discriminator. It consumes explicit, epoch-bound CJC transition
contracts and builds a conservative coordination fabric over the current Frank v0.1
transition batch. Harness/H1/H2/H3 are intentionally absent: Harness is only a validation
method under the current owner-fixed Frank-v0.1-only program.

Safety/authority laws:
- exact CJC independence is only usable for PURE/INTERNAL_STATE deterministic transitions;
- hidden counterfactual noncommutativity is treated as a real coordination edge;
- UNKNOWN/TRUNCATED/stale/effectful pairs never become safe parallel;
- this gate never mints effect authority or execution authority;
- external effects route to the normal deterministic Frank effect gate.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Sequence
from causal_jet_commutator import Exactness, JetPolicy, JetState, PairClass, StateIdentity, Transition, classify_cjc_context

DOMAIN = b"FrankV01CJCDecision/v1\x00"

class GateRoute(str, Enum):
    INDEPENDENT_EXACT = "INDEPENDENT_EXACT"
    COORDINATE_STATE_ORDER = "COORDINATE_STATE_ORDER"
    COORDINATE_HIDDEN_CAUSAL = "COORDINATE_HIDDEN_CAUSAL"
    FALLBACK_UNKNOWN = "FALLBACK_UNKNOWN"
    FALLBACK_EFFECT_GATE = "FALLBACK_EFFECT_GATE"
    REJECT_STALE_STATE = "REJECT_STALE_STATE"

@dataclass(frozen=True)
class FrankExecutionIdentity:
    program_semantic_id: str
    state_epoch: str
    state_version: str
    target_binary_sha256: str
    state_lineage_epoch: str
    work_revision: str
    @property
    def cjc_state_identity(self) -> StateIdentity:
        return StateIdentity.derive(program_semantic_id=self.program_semantic_id,state_epoch=self.state_epoch,state_version=self.state_version)
    @property
    def identity_hash(self) -> str:
        raw=json.dumps(asdict(self),sort_keys=True,separators=(",",":")).encode()
        return sha256(b"FrankExecutionIdentity/v1\x00"+raw).hexdigest()

@dataclass(frozen=True)
class PairGateDecision:
    a_use_ref: str
    b_use_ref: str
    route: GateRoute
    pair_class: str
    exactness: str
    state_instance_id: str
    commutator_terms: int
    max_degree: int
    observed_full_state_delta: dict[str,int]
    hidden_counterfactual_support: tuple[str,...]
    effect_authority_minted: bool=False
    @property
    def decision_hash(self)->str:
        raw=json.dumps(asdict(self),sort_keys=True,separators=(",",":")).encode()
        return sha256(DOMAIN+raw).hexdigest()

@dataclass(frozen=True)
class CoordinationComponent:
    use_refs: tuple[str,...]
    reasons: tuple[str,...]

@dataclass(frozen=True)
class FrankCoordinationFabric:
    execution_identity_hash: str
    state_instance_id: str
    pair_decisions: tuple[PairGateDecision,...]
    coordination_components: tuple[CoordinationComponent,...]
    independent_use_refs: tuple[str,...]
    unknown_or_effectful_use_refs: tuple[str,...]
    authority_minted: bool=False
    @property
    def semantic_hash(self)->str:
        payload={"execution_identity_hash":self.execution_identity_hash,"state_instance_id":self.state_instance_id,
            "pair_decisions":[asdict(x) for x in self.pair_decisions],"coordination_components":[asdict(x) for x in self.coordination_components],
            "independent_use_refs":list(self.independent_use_refs),"unknown_or_effectful_use_refs":list(self.unknown_or_effectful_use_refs),"authority_minted":self.authority_minted}
        return sha256(b"FrankCoordinationFabric/v1\x00"+json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def _is_effectful(op:Transition)->bool:
    return op.contract.effect_class.value not in {"PURE","INTERNAL_STATE"}

def _is_stale(op:Transition,identity:FrankExecutionIdentity)->bool:
    return str(op.contract.state_epoch)!=str(identity.state_epoch)

def classify_pair_for_frank(*,execution:FrankExecutionIdentity,initial_values:dict[str,int],prefix:Sequence[Transition],a:Transition,b:Transition,suffix:Sequence[Transition],policy:JetPolicy)->PairGateDecision:
    state_id=execution.cjc_state_identity
    if _is_stale(a,execution) or _is_stale(b,execution):
        return PairGateDecision(a.use_ref,b.use_ref,GateRoute.REJECT_STALE_STATE,PairClass.UNKNOWN.value,Exactness.UNKNOWN.value,state_id.state_instance_id,0,0,{},(),False)
    if _is_effectful(a) or _is_effectful(b):
        return PairGateDecision(a.use_ref,b.use_ref,GateRoute.FALLBACK_EFFECT_GATE,PairClass.UNKNOWN.value,Exactness.UNKNOWN.value,state_id.state_instance_id,0,0,{},(),False)
    receipt=classify_cjc_context(JetState.from_concrete(state_id,initial_values),prefix,a,b,suffix,policy)
    if receipt.exactness!=Exactness.EXACT or receipt.classification==PairClass.UNKNOWN: route=GateRoute.FALLBACK_UNKNOWN
    elif receipt.classification==PairClass.FULL_COMMUTE: route=GateRoute.INDEPENDENT_EXACT
    elif receipt.classification==PairClass.HIDDEN_CAUSAL_NONCOMMUTE: route=GateRoute.COORDINATE_HIDDEN_CAUSAL
    else: route=GateRoute.COORDINATE_STATE_ORDER
    return PairGateDecision(a.use_ref,b.use_ref,route,receipt.classification.value,receipt.exactness.value,receipt.state_instance_id,
        receipt.commutator_terms,receipt.max_degree,dict(receipt.observed_full_state_delta),tuple(receipt.hidden_counterfactual_support),False)

def contextual_pair(sequence:Sequence[Transition],i:int,j:int):
    if not (0<=i<j<len(sequence)): raise ValueError("require 0 <= i < j < len(sequence)")
    a,b=sequence[i],sequence[j]
    prefix=[x for k,x in enumerate(sequence) if k<i]
    suffix=[x for k,x in enumerate(sequence) if k>i and k!=j]
    return prefix,a,b,suffix

def _components(nodes:Iterable[str],edges:dict[tuple[str,str],str])->tuple[CoordinationComponent,...]:
    adjacency={n:set() for n in nodes}; reasons_by_node={n:set() for n in nodes}
    for (a,b),reason in edges.items():
        adjacency.setdefault(a,set()).add(b); adjacency.setdefault(b,set()).add(a)
        reasons_by_node.setdefault(a,set()).add(reason); reasons_by_node.setdefault(b,set()).add(reason)
    seen=set(); out=[]
    for n in sorted(adjacency):
        if n in seen or not adjacency[n]: continue
        stack=[n]; comp=set(); reasons=set()
        while stack:
            cur=stack.pop()
            if cur in seen: continue
            seen.add(cur); comp.add(cur); reasons|=reasons_by_node.get(cur,set()); stack.extend(sorted(adjacency[cur]-seen))
        out.append(CoordinationComponent(tuple(sorted(comp)),tuple(sorted(reasons))))
    return tuple(sorted(out,key=lambda c:c.use_refs))

def build_coordination_fabric(*,execution:FrankExecutionIdentity,initial_values:dict[str,int],sequence:Sequence[Transition],policy:JetPolicy|None=None)->FrankCoordinationFabric:
    policy=policy or JetPolicy()
    if len({op.use_ref for op in sequence})!=len(sequence): raise ValueError("use_ref must be unique within one coordination batch")
    decisions=[]; edges={}; unknown_or_effectful=set()
    for i in range(len(sequence)):
        for j in range(i+1,len(sequence)):
            prefix,a,b,suffix=contextual_pair(sequence,i,j)
            d=classify_pair_for_frank(execution=execution,initial_values=initial_values,prefix=prefix,a=a,b=b,suffix=suffix,policy=policy)
            decisions.append(d)
            if d.route!=GateRoute.INDEPENDENT_EXACT: edges[tuple(sorted((d.a_use_ref,d.b_use_ref)))]=d.route.value
            if d.route in {GateRoute.FALLBACK_UNKNOWN,GateRoute.FALLBACK_EFFECT_GATE,GateRoute.REJECT_STALE_STATE}: unknown_or_effectful|={d.a_use_ref,d.b_use_ref}
    nodes=[op.use_ref for op in sequence]; comps=_components(nodes,edges); coordinated={u for c in comps for u in c.use_refs}
    return FrankCoordinationFabric(execution.identity_hash,execution.cjc_state_identity.state_instance_id,tuple(decisions),comps,
        tuple(sorted(set(nodes)-coordinated)),tuple(sorted(unknown_or_effectful)),False)

def summarize_routes(fabric:FrankCoordinationFabric)->dict[str,int]:
    out={r.value:0 for r in GateRoute}
    for d in fabric.pair_decisions: out[d.route.value]+=1
    return out

def assert_no_authority_mint(fabric:FrankCoordinationFabric)->None:
    if fabric.authority_minted: raise AssertionError("coordination fabric minted authority")
    if any(d.effect_authority_minted for d in fabric.pair_decisions): raise AssertionError("pair decision minted authority")
