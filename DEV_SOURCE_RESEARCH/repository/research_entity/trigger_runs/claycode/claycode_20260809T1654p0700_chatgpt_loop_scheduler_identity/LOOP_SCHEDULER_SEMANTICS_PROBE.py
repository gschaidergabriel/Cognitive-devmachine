#!/usr/bin/env python3
"""ClayCode loop scheduler semantic-identity probe.
Synthetic mechanism test only; not FRANK runtime evidence.
"""
import hashlib, itertools, json, math, random, statistics

def run_param(params, periods=(1,2,5), mode="snapshot",
              order=("fast","mid","slow"), ticks=80,
              adaptive=True, fixed_fast=None):
    a,b,c,d,e=params
    specs={"fast":{"period":periods[0],"max":5},
           "mid":{"period":periods[1],"max":1},
           "slow":{"period":periods[2],"max":1}}
    state=[0.0,0.0,0.0]
    total=0
    semantic_trace=[]
    for t in range(ticks):
        u=0.0 if t<7 else (1.0 if t<48 else 0.35)
        pre=state[:]
        due=[lid for lid in ("fast","mid","slow")
             if t % specs[lid]["period"] == 0]
        events=[]
        def step(lid, st):
            p,w,g=st
            if lid=="fast": return [p+a*(u-p)+b*w,w,g]
            if lid=="mid": return [p,w+c*(p-w)+d*g,g]
            return [p,w,g+e*(w-g)]
        if mode=="snapshot":
            proposals={}
            for lid in order:
                if lid not in due: continue
                local=pre[:]
                niter=fixed_fast if (lid=="fast" and fixed_fast is not None) else specs[lid]["max"]
                used=0
                for _ in range(niter):
                    nxt=step(lid,local); used+=1
                    idx={"fast":0,"mid":1,"slow":2}[lid]
                    r=abs(nxt[idx]-local[idx]); local=nxt
                    if lid=="fast" and adaptive and fixed_fast is None and r<1e-4:
                        break
                idx={"fast":0,"mid":1,"slow":2}[lid]
                proposals[idx]=local[idx]
                total+=used
                events.append((lid,used,round(local[idx],12)))
            for idx,val in proposals.items():
                state[idx]=val
        elif mode=="sequential":
            for lid in order:
                if lid not in due: continue
                niter=fixed_fast if (lid=="fast" and fixed_fast is not None) else specs[lid]["max"]
                used=0
                for _ in range(niter):
                    nxt=step(lid,state); used+=1
                    idx={"fast":0,"mid":1,"slow":2}[lid]
                    r=abs(nxt[idx]-state[idx]); state=nxt
                    if lid=="fast" and adaptive and fixed_fast is None and r<1e-4:
                        break
                idx={"fast":0,"mid":1,"slow":2}[lid]
                total+=used
                events.append((lid,used,round(state[idx],12)))
        else:
            raise ValueError(mode)
        # same-tag snapshot events are semantically a set and canonicalized by loop_id
        semantic_trace.append((t,tuple(sorted(events)),
                               tuple(round(x,12) for x in state)))
    semhash=hashlib.sha256(repr(semantic_trace).encode()).hexdigest()
    return tuple(state), total, semhash

def schedule_blind_hash(params):
    return hashlib.sha256(json.dumps(
        {"loops":["fast","mid","slow"],
         "params":[round(x,6) for x in params]},
        sort_keys=True).encode()).hexdigest()

def schedule_aware_hash(params, periods, mode, order, adaptive):
    return hashlib.sha256(json.dumps(
        {"loops":["fast","mid","slow"],
         "params":[round(x,6) for x in params],
         "periods":periods,
         "commit":mode,
         "order":order if mode=="sequential" else "canonical-snapshot",
         "adaptive":adaptive},
        sort_keys=True).encode()).hexdigest()

rng=random.Random(20260809)
N=2000
flat_changed=seq_order_changed=snapshot_order_changed=snapshot_semhash_changed=0
adaptive_savings=[]
adaptive_l2=[]
adaptive_endpoint_changed=0

for _ in range(N):
    params=(rng.uniform(.12,.38),rng.uniform(.02,.12),
            rng.uniform(.12,.32),rng.uniform(.01,.08),
            rng.uniform(.04,.18))
    base=run_param(params,mode="snapshot",order=("fast","mid","slow"))
    flat=run_param(params,periods=(1,1,1),mode="snapshot")
    if math.dist(base[0],flat[0]) > 1e-6:
        flat_changed += 1
    seq_a=run_param(params,mode="sequential",order=("fast","mid","slow"))
    seq_b=run_param(params,mode="sequential",order=("slow","mid","fast"))
    if math.dist(seq_a[0],seq_b[0]) > 1e-9:
        seq_order_changed += 1
    perm=run_param(params,mode="snapshot",order=("slow","fast","mid"))
    if math.dist(base[0],perm[0]) > 1e-12:
        snapshot_order_changed += 1
    if base[2] != perm[2]:
        snapshot_semhash_changed += 1
    fixed=run_param(params,mode="snapshot",adaptive=False,fixed_fast=5)
    d=math.dist(base[0],fixed[0])
    if d > 1e-12:
        adaptive_endpoint_changed += 1
    adaptive_l2.append(d)
    adaptive_savings.append((fixed[1]-base[1])/fixed[1])

params=(.30,.10,.25,.05,.10)
variants=[
    ((1,2,5),"snapshot",("fast","mid","slow"),True),
    ((1,1,1),"snapshot",("fast","mid","slow"),True),
    ((1,2,5),"sequential",("fast","mid","slow"),True),
    ((1,2,5),"sequential",("slow","mid","fast"),True),
]
out={
    "seed":20260809,
    "cases":N,
    "timescale_flattening_changed_endpoint":flat_changed,
    "sequential_order_changed_endpoint":seq_order_changed,
    "snapshot_declaration_order_changed_endpoint":snapshot_order_changed,
    "snapshot_declaration_order_changed_semantic_hash":snapshot_semhash_changed,
    "adaptive_vs_fixed5_endpoint_changed":adaptive_endpoint_changed,
    "adaptive_recurrence_saving_mean":statistics.mean(adaptive_savings),
    "adaptive_recurrence_saving_median":statistics.median(adaptive_savings),
    "adaptive_recurrence_saving_min":min(adaptive_savings),
    "adaptive_recurrence_saving_max":max(adaptive_savings),
    "adaptive_vs_fixed5_l2_mean":statistics.mean(adaptive_l2),
    "adaptive_vs_fixed5_l2_max":max(adaptive_l2),
    "schedule_blind_hash_unique_for_4_variants":
        len({schedule_blind_hash(params) for _ in variants}),
    "schedule_aware_hash_unique_for_4_variants":
        len({schedule_aware_hash(params,*v) for v in variants}),
}
print(json.dumps(out,indent=2,sort_keys=True))
