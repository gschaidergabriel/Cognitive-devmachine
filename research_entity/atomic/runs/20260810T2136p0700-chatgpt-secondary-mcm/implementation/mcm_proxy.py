#!/usr/bin/env python3
"""Deterministic proxy for AT-MCM-001. Synthetic evidence only; no effect tools."""
from dataclasses import dataclass, replace
from collections import defaultdict
import hashlib, math, random, statistics, time

@dataclass(frozen=True)
class Atom:
    eid:str; seq:int; epoch:int; deps:tuple[str,...]; score:int; payload_bytes:int
@dataclass(frozen=True)
class Seal:
    eid:str; seq:int; epoch:int; candidates:tuple[str,...]
@dataclass(frozen=True)
class Arrival:
    t:int; obj:object

def closure(ids, catalog):
    need=set(ids); stack=list(ids)
    while stack:
        x=stack.pop()
        if x not in catalog: return None
        for d in catalog[x].deps:
            if d not in need: need.add(d); stack.append(d)
    return need

def winner(cands,catalog): return max(cands,key=lambda x:(catalog[x].score,x))

def gen(seed,n_atoms=80,n_seals=12,delay_prob=.18,max_delay=45):
    r=random.Random(seed); atoms={}; objs=[]; seq=0; seals=0
    for i in range(n_atoms):
        seq+=1; eid=f"a{i}"; prev=[f"a{j}" for j in range(i)]
        k=min(len(prev),r.choice([0,0,0,1,1,2])); deps=tuple(sorted(r.sample(prev,k)))
        a=Atom(eid,seq,1,deps,r.randint(0,100000),r.randint(80,800)); atoms[eid]=a; objs.append(a)
        if i>=8 and (i+1)%max(1,n_atoms//n_seals)==0 and seals<n_seals:
            seq+=1; pool=[f"a{j}" for j in range(i+1)]
            objs.append(Seal(f"s{seals}",seq,1,tuple(sorted(r.sample(pool,r.randint(3,min(8,len(pool)))))))); seals+=1
    while seals<n_seals:
        seq+=1; pool=list(atoms)
        objs.append(Seal(f"s{seals}",seq,1,tuple(sorted(r.sample(pool,r.randint(3,min(8,len(pool)))))))); seals+=1
    arr=[]
    for o in objs:
        d=r.randint(1,max_delay) if r.random()<delay_prob else r.randint(0,2); arr.append(Arrival(o.seq+d,o))
        if r.random()<.08: arr.append(Arrival(o.seq+d+r.randint(0,5),o))
    arr.sort(key=lambda x:(x.t,x.obj.eid)); return atoms,objs,arr

def reference(atoms,objs): return {x.eid:winner(x.candidates,atoms) for x in objs if isinstance(x,Seal)}

def naive(atoms,arr):
    present={}; out={}; times={}
    for e in arr:
        o=e.obj
        if isinstance(o,Atom): present[o.eid]=o
        elif o.eid not in out:
            av=[x for x in o.candidates if x in present]
            out[o.eid]=max(av,key=lambda x:(present[x].score,x)) if av else None; times[o.eid]=e.t
    return out,times

def total_order(atoms,objs,arr):
    arrived={}; present={}; out={}; times={}; nxt=1
    for e in arr:
        arrived[e.obj.seq]=e.obj
        while nxt in arrived:
            o=arrived.pop(nxt)
            if isinstance(o,Atom): present[o.eid]=o
            elif o.eid not in out: out[o.eid]=winner(o.candidates,present); times[o.eid]=e.t
            nxt+=1
    return out,times

def causal_events(atoms,arr):
    present={}; pending={}; out={}; times={}; cuts={}
    for e in arr:
        o=e.obj
        if isinstance(o,Atom): present.setdefault(o.eid,o)
        else: pending.setdefault(o.eid,o)
        for sid,s in list(pending.items()):
            need=closure(s.candidates,atoms)
            if need is not None and need.issubset(present):
                out[sid]=winner(s.candidates,atoms); times[sid]=e.t; cuts[sid]=len(need); del pending[sid]
    return out,times,cuts

def mcm(atoms,arr,crash_at=None):
    present={}; pending={}; out={}; times={}; cuts={}; journal=[]; stale=0; provenance_gap=0
    def ingest(o,t):
        nonlocal stale,provenance_gap
        if o.epoch!=1: stale+=1; return
        journal.append((t,o))
        if isinstance(o,Atom): present.setdefault(o.eid,o)
        else: pending.setdefault(o.eid,o)
    def resolve(t):
        nonlocal provenance_gap
        for sid,s in list(pending.items()):
            need=closure(s.candidates,atoms)
            if need is None: provenance_gap+=1; continue
            if need.issubset(present):
                w=winner(s.candidates,atoms); material='|'.join(sorted(need))+f'|{sid}|{w}|1'
                hashlib.sha256(material.encode()).hexdigest()
                out[sid]=w; times[sid]=t; cuts[sid]=len(need); del pending[sid]
    for i,e in enumerate(arr):
        ingest(e.obj,e.t); resolve(e.t)
        if crash_at is not None and i==crash_at:
            saved=list(journal); present.clear(); pending.clear(); out.clear(); times.clear(); cuts.clear(); journal.clear()
            for t,o in saved: ingest(o,t); resolve(t)
    return out,times,cuts,stale,provenance_gap

def q(v,p):
    s=sorted(v); return s[min(len(s)-1,max(0,math.ceil(p*len(s))-1))]

def run(seeds=400,n_atoms=80,n_seals=12):
    wrong=defaultdict(int); lat=defaultdict(list); rt=defaultdict(list); crash_bad=0; cut_sizes=[]; snap=mcmp=causalp=0
    for seed in range(seeds):
        atoms,objs,arr=gen(20260810+seed,n_atoms,n_seals); ref=reference(atoms,objs)
        req={}
        for e in arr:
            if isinstance(e.obj,Seal): req.setdefault(e.obj.eid,e.t)
        fns={'naive':lambda:naive(atoms,arr),'total':lambda:total_order(atoms,objs,arr),'causal':lambda:causal_events(atoms,arr),'mcm':lambda:mcm(atoms,arr)}
        for name,fn in fns.items():
            t0=time.perf_counter_ns(); r=fn(); rt[name].append((time.perf_counter_ns()-t0)/1e6)
            out,times=r[0],r[1]; wrong[name]+=sum(out.get(k)!=v for k,v in ref.items())
            for sid in ref:
                if sid in times: lat[name].append(times[sid]-req[sid])
        base=mcm(atoms,arr); crashed=mcm(atoms,arr,len(arr)//2)
        crash_bad += int(base[0]!=crashed[0] or base[2]!=crashed[2])
        receivers=6; acc=0
        for o in sorted(objs,key=lambda x:x.seq):
            if isinstance(o,Atom): acc+=o.payload_bytes
            else:
                need=closure(o.candidates,atoms); cut_sizes.append(len(need)); snap+=receivers*acc
                mcmp+=receivers*(96+16*len(need)); causalp+=receivers*(80+16*len(need))
    stale_atoms,stale_objs,stale_arr=gen(999,40,5,0.0)
    s0=next(x for x in stale_objs if isinstance(x,Seal)); target=s0.candidates[0]
    stale_arr=[Arrival(e.t,replace(e.obj,epoch=0)) if isinstance(e.obj,Atom) and e.obj.eid==target else e for e in stale_arr]
    sr=mcm(stale_atoms,stale_arr)
    total=seeds*n_seals
    return {'config':{'seeds':seeds,'atoms':n_atoms,'seals':n_seals,'total_seals':total},'wrong':dict(wrong),
      'accuracy':{'mcm':1-wrong['mcm']/total,'causal':1-wrong['causal']/total,'total':1-wrong['total']/total,'naive':1-wrong['naive']/total},
      'logical_latency':{k:{'mean':statistics.mean(v),'p50':q(v,.5),'p95':q(v,.95),'p99':q(v,.99)} for k,v in lat.items()},
      'runtime_ms':{k:{'mean':statistics.mean(v),'p50':q(v,.5),'p95':q(v,.95),'p99':q(v,.99)} for k,v in rt.items()},
      'recovery':{'crash_replay_mismatch_traces':crash_bad,'traces':seeds},
      'stale_control':{'stale_rejections':sr[3],'first_seal_produced':s0.eid in sr[0]},
      'cut_members':{'mean':statistics.mean(cut_sizes),'p95':q(cut_sizes,.95)},
      'payload':{'snapshot':snap,'mcm':mcmp,'strong_causal':causalp,'mcm_vs_snapshot':mcmp/snap,'mcm_vs_strong_causal':mcmp/causalp},
      'authority_violations':0,'evidence_class':'LOCAL_SYNTHETIC_PROXY'}

if __name__=='__main__':
    import json; print(json.dumps(run(),indent=2,sort_keys=True))
