#!/usr/bin/env python3
"""Executable CJC public runtime facade."""
from cjc_core import *
from cjc_ops import *

def run_symbolic(initial:JetState,ops:Sequence[Transition],policy:JetPolicy)->JetState:
    state=initial
    for op in ops:
        try: state=op.symbolic(state,policy)
        except CJCError:
            out=state.copy()
            for field in op.contract.writes:
                if field in out.values: out.values[field]=BoolJet.unknown()
            state=out
    return state

def run_concrete(initial:Mapping[str,int],ops:Sequence[Transition],enabled_uses:Iterable[str])->dict[str,int]:
    enabled=set(enabled_uses); state=dict(initial)
    for op in ops: state=op.concrete(state,enabled)
    return state

def state_difference(a:Mapping[str,int],b:Mapping[str,int])->dict[str,int]:
    keys=sorted(set(a)|set(b)); return {k:a.get(k,0)-b.get(k,0) for k in keys if a.get(k,0)!=b.get(k,0)}

def jet_state_difference(a:JetState,b:JetState)->dict[str,BoolJet]:
    if a.identity!=b.identity: raise CJCError("cannot compare different state identities")
    keys=sorted(set(a.values)|set(b.values)); out={}
    for key in keys: out[key]=a.values.get(key,BoolJet.const(0))-b.values.get(key,BoolJet.const(0))
    return out

def exact_use_set(ops:Sequence[Transition])->frozenset[str]: return frozenset(op.use_ref for op in ops)

def all_use_subsets(uses:Iterable[str]):
    ordered=sorted(set(uses))
    for mask in range(1<<len(ordered)): yield frozenset(ordered[i] for i in range(len(ordered)) if (mask>>i)&1)

def ordered_context_sequences(prefix:Sequence[Transition],a:Transition,b:Transition,suffix:Sequence[Transition])->tuple[list[Transition],list[Transition]]:
    return ([*prefix,a,b,*suffix],[*prefix,b,a,*suffix])

def credit_signature_from_symbolic(state:JetState,use_refs:Iterable[str])->dict[tuple[str,str],int]:
    if state.exactness!=Exactness.EXACT: raise CJCError("credit signature requires exact symbolic state")
    uses=frozenset(use_refs); full=state.full_value(uses); out={}
    for use in sorted(uses):
        lesion=state.full_value(uses-{use})
        for field in sorted(full): out[(field,use)]=full[field]-lesion[field]
    return out

def credit_signature_replay(initial:Mapping[str,int],ops:Sequence[Transition])->dict[tuple[str,str],int]:
    uses=exact_use_set(ops); full=run_concrete(initial,ops,uses); out={}
    for use in sorted(uses):
        lesion=run_concrete(initial,ops,uses-{use})
        for field in sorted(full): out[(field,use)]=full[field]-lesion[field]
    return out

def classify_reference_context(initial:Mapping[str,int],prefix:Sequence[Transition],a:Transition,b:Transition,suffix:Sequence[Transition])->PairClass:
    left,right=ordered_context_sequences(prefix,a,b,suffix); uses=exact_use_set([*left,*right]); left_full=run_concrete(initial,left,uses); right_full=run_concrete(initial,right,uses)
    if left_full!=right_full:return PairClass.STATE_NONCOMMUTE
    for enabled in all_use_subsets(uses):
        if run_concrete(initial,left,enabled)!=run_concrete(initial,right,enabled):return PairClass.HIDDEN_CAUSAL_NONCOMMUTE
    return PairClass.FULL_COMMUTE

def classify_reference(initial,a,b):return classify_reference_context(initial,[],a,b,[])

def classify_state_only_context(initial,prefix,a,b,suffix):
    left,right=ordered_context_sequences(prefix,a,b,suffix); uses=exact_use_set([*left,*right]); lv=run_concrete(initial,left,uses); rv=run_concrete(initial,right,uses)
    return PairClass.FULL_COMMUTE if lv==rv else PairClass.STATE_NONCOMMUTE

def classify_state_only(initial,a,b):return classify_state_only_context(initial,[],a,b,[])

def rw_conflict(a:Transition,b:Transition)->bool:
    aw,ar=set(a.contract.writes),set(a.contract.reads); bw,br=set(b.contract.writes),set(b.contract.reads)
    return bool((aw&(br|bw)) or (bw&(ar|aw)))

def classify_cjc_context(initial:JetState,prefix:Sequence[Transition],a:Transition,b:Transition,suffix:Sequence[Transition],policy:JetPolicy)->JetCommutatorReceipt:
    left,right=ordered_context_sequences(prefix,a,b,suffix); ab=run_symbolic(initial.copy(),left,policy); ba=run_symbolic(initial.copy(),right,policy)
    exactness=Exactness.UNKNOWN if Exactness.UNKNOWN in {ab.exactness,ba.exactness} else Exactness.TRUNCATED if Exactness.TRUNCATED in {ab.exactness,ba.exactness} else Exactness.EXACT
    if exactness!=Exactness.EXACT:
        return JetCommutatorReceipt((a.use_ref,b.use_ref),initial.identity.state_instance_id,(a.contract.semantic_hash,b.contract.semantic_hash),exactness,PairClass.UNKNOWN,{},(),0,max(ab.max_degree,ba.max_degree))
    uses=exact_use_set([*left,*right]); ab_full=ab.full_value(uses); ba_full=ba.full_value(uses); full_delta=state_difference(ab_full,ba_full)
    comm=jet_state_difference(ab,ba); nonzero_poly_fields=tuple(sorted(k for k,p in comm.items() if not p.is_zero_polynomial())); comm_terms=sum(p.term_count for p in comm.values()); max_degree=max((p.degree for p in comm.values()),default=0)
    cls=PairClass.STATE_NONCOMMUTE if full_delta else PairClass.HIDDEN_CAUSAL_NONCOMMUTE if nonzero_poly_fields else PairClass.FULL_COMMUTE
    return JetCommutatorReceipt((a.use_ref,b.use_ref),initial.identity.state_instance_id,(a.contract.semantic_hash,b.contract.semantic_hash),exactness,cls,full_delta,nonzero_poly_fields if not full_delta else (),comm_terms,max_degree)

def classify_cjc(initial,a,b,policy):return classify_cjc_context(initial,[],a,b,[],policy)
def receipt_is_current(receipt,identity):return receipt.state_instance_id==identity.state_instance_id

def pair_demo()->dict:
    identity=StateIdentity.derive(program_semantic_id="clayir:demo",state_epoch="7",state_version="3"); initial_values={"x":1}; initial=JetState.from_concrete(identity,initial_values)
    def c(use,tid):return TransitionContract(tid,use,"1","7",EffectClass.INTERNAL_STATE,frozenset({"x"}),frozenset({"x"}),(f"fixture:{use}",))
    a=Scale(c("A","scale-a"),"x",2); b=Add(c("B","add-b"),"x",1); mask=SetValue(c("C","mask-c"),"x",0)
    cjc=classify_cjc_context(initial,[],a,b,[mask],JetPolicy()); left,right=ordered_context_sequences([],a,b,[mask]); uses=exact_use_set([*left,*right])
    return {"observed_all_present_left":run_concrete(initial_values,left,uses),"observed_all_present_right":run_concrete(initial_values,right,uses),"lesion_C_left":run_concrete(initial_values,left,uses-{"C"}),"lesion_C_right":run_concrete(initial_values,right,uses-{"C"}),"state_only":classify_state_only_context(initial_values,[],a,b,[mask]).value,"reference":classify_reference_context(initial_values,[],a,b,[mask]).value,"cjc":{"classification":cjc.classification.value,"exactness":cjc.exactness.value,"receipt_hash":cjc.receipt_hash,"authority_minted":cjc.authority_minted}}

if __name__=="__main__": print(json.dumps(pair_demo(),indent=2,sort_keys=True))
