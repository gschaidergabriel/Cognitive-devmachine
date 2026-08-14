#!/usr/bin/env python3
"""Deterministic PSW synthetic discriminator.

This is a reference micro-harness, not Frank runtime code. It compares materialized branch worlds,
ordinary sparse overlays, exact-read-signature memoization, PSW-style explicit signature grouping,
and a guarded-field proxy. All external/effect authority is absent.
"""
from __future__ import annotations

from collections import defaultdict
import json
import random
import statistics
import time

MASK64=(1<<64)-1


def make_worlds(fields:int, branches:int, divergence:float, seed:int):
    rng=random.Random(seed)
    base={f"f{i}":rng.randrange(1_000_000) for i in range(fields)}
    d=max(0,min(fields,int(round(fields*divergence))))
    overlays=[]
    for _ in range(branches):
        ov={}
        for i in rng.sample(range(fields),d) if d else []:
            key=f"f{i}"; value=rng.randrange(1_000_000)
            if value==base[key]: value=(value+1)%1_000_000
            ov[key]=value
        overlays.append(ov)
    return base,overlays


def read(base,overlay,key):
    return overlay.get(key,base[key])


def materialize(base,overlay):
    out=base.copy(); out.update(overlay); return out


def pure_transition(values):
    x=0x9e3779b97f4a7c15
    for value in values:
        x ^= (value + 0x9e3779b97f4a7c15 + ((x<<6)&MASK64) + (x>>2)) & MASK64
        x &= MASK64
    return x,(x^(x>>17))&MASK64


def wire_bytes(obj):
    return len(json.dumps(obj,separators=(",",":"),sort_keys=True).encode())


def overlay_memo(base,overlays,read_keys):
    cache={}; out=[]
    for ov in overlays:
        signature=tuple(read(base,ov,key) for key in read_keys)
        if signature not in cache:
            cache[signature]=pure_transition(signature)
        out.append(cache[signature])
    return out,len(cache)


def psw_lift(base,overlays,read_keys):
    groups={}
    for branch_id,ov in enumerate(overlays):
        signature=tuple(read(base,ov,key) for key in read_keys)
        groups.setdefault(signature,[]).append(branch_id)
    out=[None]*len(overlays)
    for signature,branch_ids in groups.items():
        result=pure_transition(signature)
        for branch_id in branch_ids:
            out[branch_id]=result
    return out,len(groups)


def hidden_read_negative_control():
    base={"a":1,"b":10}; overlays=[{}, {"b":20}]
    truth=[pure_transition((read(base,o,"a"),read(base,o,"b"))) for o in overlays]
    # Deliberately unsound: key omits the material read of b.
    cache={}; unsafe=[]
    for ov in overlays:
        key=(read(base,ov,"a"),)
        if key not in cache:
            cache[key]=pure_transition((read(base,ov,"a"),read(base,ov,"b")))
        unsafe.append(cache[key])
    exact,_=overlay_memo(base,overlays,["a","b"])
    return {
        "unsafe_mismatch_count":sum(x!=y for x,y in zip(unsafe,truth)),
        "exact_mismatch_count":sum(x!=y for x,y in zip(exact,truth)),
    }


def identity_controls():
    a={"payload":(("x",1),),"self":"self.root","base_epoch":7,"rev":1,"hyp":"H:A","prov":"source:A"}
    b={"payload":(("x",1),),"self":"self.root","base_epoch":7,"rev":1,"hyp":"H:B","prov":"source:B"}
    naive_merge=a["payload"]==b["payload"]
    exact_key=lambda x:(x["payload"],x["self"],x["base_epoch"],x["rev"],x["hyp"],x["prov"])
    return {"payload_only_false_merge":naive_merge,"exact_identity_merge":exact_key(a)==exact_key(b),"stale_epoch_rejected":6!=7,"wrong_self_rejected":"Frank"!="self.root"}


def may_lift(effect_class:str,read_set_known:bool):
    return effect_class=="PURE" and read_set_known


def effect_controls():
    return {
        "pure_known_allowed":may_lift("PURE",True),
        "pure_unknown_readset_allowed":may_lift("PURE",False),
        "external_read_allowed":may_lift("EXTERNAL_READ",True),
        "external_write_allowed":may_lift("EXTERNAL_WRITE",True),
        "security_change_allowed":may_lift("SECURITY_CHANGE",True),
    }


def benchmark_cell(fields,branches,divergence,read_count,seed,repeats=3):
    base,overlays=make_worlds(fields,branches,divergence,seed)
    read_keys=[f"f{i}" for i in random.Random(seed+999).sample(range(fields),min(read_count,fields))]
    full=[materialize(base,o) for o in overlays]
    truth=[pure_transition(tuple(world[k] for k in read_keys)) for world in full]
    omemo,omemo_calls=overlay_memo(base,overlays,read_keys)
    psw,psw_calls=psw_lift(base,overlays,read_keys)
    assert omemo==truth and psw==truth and omemo_calls==psw_calls

    full_wire=wire_bytes(full)
    overlay_wire=wire_bytes({"base":base,"branches":[{"id":i,"epoch":7,"rev":1,"prov":f"p{i:08x}","ov":o} for i,o in enumerate(overlays)]})
    psw_wire=wire_bytes({"base":base,"base_epoch":7,"branches":[{"id":i,"guard":f"h{i}","rev":1,"prov":f"p{i:08x}","delta":o} for i,o in enumerate(overlays)]})

    loops=max(1,min(20,int(20000/max(branches,1))))
    def timed(fn):
        samples=[]
        for _ in range(repeats):
            t0=time.perf_counter_ns()
            for _ in range(loops): fn()
            samples.append((time.perf_counter_ns()-t0)/loops)
        return statistics.median(samples)

    def full_exec(): return [pure_transition(tuple(w[k] for k in read_keys)) for w in full]
    def omemo_exec(): return overlay_memo(base,overlays,read_keys)[0]
    def psw_exec(): return psw_lift(base,overlays,read_keys)[0]

    return {
        "fields":fields,"branches":branches,"divergence":divergence,"read_count":len(read_keys),
        "unique_read_signatures":omemo_calls,"sharing_factor":branches/omemo_calls,
        "wire_full":full_wire,"wire_overlay":overlay_wire,"wire_psw":psw_wire,
        "time_full_ns":timed(full_exec),"time_overlay_memo_ns":timed(omemo_exec),"time_psw_ns":timed(psw_exec),
    }


if __name__=="__main__":
    print(json.dumps({"hidden_read":hidden_read_negative_control(),"identity":identity_controls(),"effects":effect_controls()},indent=2,sort_keys=True))
