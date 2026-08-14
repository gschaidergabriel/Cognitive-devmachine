#!/usr/bin/env python3
"""Deterministic synthetic proxy for ATOMIC-CANDIDATE-CCF-001.

Scope: pure deterministic local state transitions only. This does not model opaque LLM calls,
external effects, stochastic transitions, target-VPS performance, or full Frank cognition.
"""
from __future__ import annotations
import math, random, time, json, platform, sys, os
import numpy as np

D=512
N=30000
SEED=42
KINDS=["ADD","MUL","AFFINE","SET","COPY_ADD","SWAP","COND_ADD"]

def make_op(rng, force_idx=None):
    k=rng.choice(KINDS)
    if k in ("ADD","MUL","AFFINE","SET","COND_ADD"):
        w=int(force_idx if force_idx is not None else rng.integers(D))
        if k=="ADD": return {"kind":k,"w":w,"a":float(rng.normal()),"reads":{w},"writes":{w}}
        if k=="MUL": return {"kind":k,"w":w,"a":float(rng.uniform(.5,1.5)),"reads":{w},"writes":{w}}
        if k=="AFFINE": return {"kind":k,"w":w,"a":float(rng.uniform(.5,1.5)),"b":float(rng.normal()),"reads":{w},"writes":{w}}
        if k=="SET": return {"kind":k,"w":w,"a":float(rng.normal()),"reads":set(),"writes":{w}}
        r=int(rng.integers(D)); return {"kind":k,"w":w,"r":r,"a":float(rng.normal()),"reads":{w,r},"writes":{w}}
    if k=="COPY_ADD":
        w=int(force_idx if force_idx is not None else rng.integers(D)); r=int(rng.integers(D))
        return {"kind":k,"w":w,"r":r,"a":float(rng.normal()),"reads":{w,r},"writes":{w}}
    i=int(force_idx if force_idx is not None else rng.integers(D)); j=int(rng.integers(D)); j=(j+1)%D if j==i else j
    return {"kind":k,"i":i,"j":j,"reads":{i,j},"writes":{i,j}}

def eval_vec(s,o):
    s=s.copy(); k=o["kind"]
    if k=="ADD": s[o["w"]]+=o["a"]
    elif k=="MUL": s[o["w"]]*=o["a"]
    elif k=="AFFINE": s[o["w"]]=o["a"]*s[o["w"]]+o["b"]
    elif k=="SET": s[o["w"]]=o["a"]
    elif k=="COPY_ADD": s[o["w"]]+=s[o["r"]]+o["a"]
    elif k=="SWAP": s[o["i"]],s[o["j"]]=s[o["j"]],s[o["i"]]
    elif k=="COND_ADD" and s[o["r"]]>0: s[o["w"]]+=o["a"]
    return s

def eval_map(d,o):
    d=dict(d); k=o["kind"]
    if k=="ADD": d[o["w"]]+=o["a"]
    elif k=="MUL": d[o["w"]]*=o["a"]
    elif k=="AFFINE": d[o["w"]]=o["a"]*d[o["w"]]+o["b"]
    elif k=="SET": d[o["w"]]=o["a"]
    elif k=="COPY_ADD": d[o["w"]]+=d[o["r"]]+o["a"]
    elif k=="SWAP": d[o["i"]],d[o["j"]]=d[o["j"]],d[o["i"]]
    elif k=="COND_ADD" and d[o["r"]]>0: d[o["w"]]+=o["a"]
    return d

def conflict(a,b):
    return bool((a["writes"]&(b["reads"]|b["writes"])) or (b["writes"]&(a["reads"]|a["writes"])))

def full_noncommute(s,a,b):
    return not np.allclose(eval_vec(eval_vec(s,a),b),eval_vec(eval_vec(s,b),a),rtol=0,atol=1e-12)

def local_noncommute(s,a,b):
    if not conflict(a,b): return False
    idx=a["reads"]|a["writes"]|b["reads"]|b["writes"]
    d={i:float(s[i]) for i in idx}
    ab=eval_map(eval_map(d,a),b); ba=eval_map(eval_map(d,b),a)
    return any(not math.isclose(ab[i],ba[i],rel_tol=0,abs_tol=1e-12) for i in idx)

def score(pred,truth):
    pred=np.array(pred,bool); truth=np.array(truth,bool)
    tp=int(np.sum(pred&truth)); fp=int(np.sum(pred&~truth)); fn=int(np.sum(~pred&truth)); tn=int(np.sum(~pred&~truth))
    p=tp/(tp+fp) if tp+fp else 1.; r=tp/(tp+fn) if tp+fn else 1.; f=2*p*r/(p+r) if p+r else 0.
    return {"tp":tp,"fp":fp,"fn":fn,"tn":tn,"precision":p,"recall":r,"f1":f,"safe_parallel_fraction":float(np.mean(~pred)),"unsafe_parallel_rate":float(np.mean((~pred)&truth))}

def run():
    rng=np.random.default_rng(SEED); random.seed(SEED); states=[]; pairs=[]
    for _ in range(N):
        s=rng.normal(size=D); a=make_op(rng)
        b=make_op(rng,int(rng.choice(list(a["reads"]|a["writes"])))) if rng.random()<.65 else make_op(rng)
        states.append(s); pairs.append((a,b))
    def timed(fn):
        t=time.perf_counter(); y=[fn(s,a,b) for s,(a,b) in zip(states,pairs)]; return y,time.perf_counter()-t
    truth,tf=timed(full_noncommute); rw,trw=timed(lambda s,a,b:conflict(a,b)); local,tl=timed(local_noncommute)
    stale=[]
    for s in states:
        q=s.copy(); ids=rng.choice(D,size=D//4,replace=False); q[ids]=rng.normal(size=len(ids)); stale.append(q)
    stale_pred=[local_noncommute(s,a,b) for s,(a,b) in zip(stale,pairs)]
    shuffled=list(local); rng.shuffle(shuffled)
    out={"config":{"D":D,"N":N,"seed":SEED,"overlap_bias":.65},"environment":{"python":sys.version,"platform":platform.platform(),"numpy":np.__version__,"cpu_count":os.cpu_count()},"total_seconds":{"full_replay":tf,"rw_conflict":trw,"local_commutator":tl},"metrics":{"full_replay":score(truth,truth),"rw_conflict":score(rw,truth),"local_commutator":score(local,truth),"stale_epoch_control":score(stale_pred,truth),"shuffled_control":score(shuffled,truth)},"derived":{"true_noncommute_rate":float(np.mean(truth)),"safe_independence_gain_pp_vs_rw":100*(score(local,truth)["safe_parallel_fraction"]-score(rw,truth)["safe_parallel_fraction"]),"speedup_vs_full":tf/tl,"stale_label_change_rate":float(np.mean(np.array(stale_pred)!=np.array(truth)))}}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__": run()
