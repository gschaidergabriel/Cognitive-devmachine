#!/usr/bin/env python3
"""Compact reproducible CJC benchmark: exact replay, state-only, and context scaling."""
from __future__ import annotations
import argparse,json,random,time,statistics
from causal_jet_commutator import *

def c(use,tid,field='x'):
    return TransitionContract(tid,use,'1','7',EffectClass.INTERNAL_STATE,frozenset({field}),frozenset({field}),(f'bench:{tid}',),True,True)
def fixture(rng,i,ctx):
    initial={'x':rng.randint(-3,3)}; a=Scale(c(f'A{i}',f's{i}'),'x',rng.choice([-2,-1,0,2,3])); b=Add(c(f'B{i}',f'a{i}'),'x',rng.randint(-3,3)); suffix=[]
    for j in range(ctx):
        u=f'C{i}_{j}'; suffix.append(SetValue(c(u,f'm{i}_{j}'),'x',rng.randint(-2,2)) if rng.random()<0.25 else Add(c(u,f'd{i}_{j}'),'x',rng.randint(-2,2)))
    return initial,a,b,suffix
def one(initial,a,b,suffix):
    ident=StateIdentity.derive(program_semantic_id='clayir:bench',state_epoch='7',state_version='1'); js=JetState.from_concrete(ident,initial)
    t0=time.perf_counter_ns(); got=classify_cjc_context(js,[],a,b,suffix,JetPolicy(max_degree=12,max_terms=65536)); t1=time.perf_counter_ns()
    t2=time.perf_counter_ns(); truth=classify_reference_context(initial,[],a,b,suffix); t3=time.perf_counter_ns(); state=classify_state_only_context(initial,[],a,b,suffix)
    return got,truth,state,t1-t0,t3-t2
def run(seed=20260810,n=2000,contexts=(0,2,4,6,8)):
    rng=random.Random(seed); rows=[]
    for ctx in contexts:
        acc=[]; cj=[]; ref=[]; hidden=0; false_safe=0; exact=0
        for i in range(n):
            initial,a,b,suffix=fixture(rng,i,ctx); got,truth,state,tc,tr=one(initial,a,b,suffix); cj.append(tc); ref.append(tr)
            if got.exactness==Exactness.EXACT: exact+=1; acc.append(got.classification==truth)
            if truth==PairClass.HIDDEN_CAUSAL_NONCOMMUTE: hidden+=1; false_safe+=int(state==PairClass.FULL_COMMUTE)
        rows.append({'context_length':ctx,'cases':n,'exact_rate':exact/n,'accuracy_when_exact':sum(acc)/len(acc) if acc else None,'hidden_rate':hidden/n,'state_only_false_safe_rate':false_safe/n,'cjc_mean_ns':statistics.mean(cj),'reference_mean_ns':statistics.mean(ref),'reference_over_cjc':statistics.mean(ref)/statistics.mean(cj),'truth_table_points':2**(ctx+2)})
    return {'schema_version':'1.0','candidate':'ATOMIC-CANDIDATE-CJC-001','seed':seed,'rows':rows,'scope':'generic Python local proxy; not target VPS','architecture_promotion':False,'effect_authority_minted':False}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,default=20260810); ap.add_argument('--n',type=int,default=2000); ap.add_argument('--out'); a=ap.parse_args(); out=run(a.seed,a.n); text=json.dumps(out,indent=2,sort_keys=True)+'\n'; open(a.out,'w').write(text) if a.out else print(text,end='')
if __name__=='__main__':main()
