#!/usr/bin/env python3
"""Synthetic contract discriminator for receipt-sealed replay.
Not live FRANK evidence and not Ubuntu acceptance.
"""
import json, random, hashlib

def H(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def step(state, inp, r):
    x, score = state["x"], state["score"]
    x += 1 if r["clock_bucket"] % 2 == 0 else -1
    x += 3 if r["rng_bit"] else -2
    x += r["peer_delta"]
    score += r["tool_value"] + inp
    if r["schedule"] == "peer_then_tool": x = x * 2 + (r["tool_value"] % 7)
    else: x = (x + (r["tool_value"] % 7)) * 2
    return {"x":x,"score":score}

def generate(seed, n=12):
    q=random.Random(seed); s={"x":0,"score":0}; rows=[]
    for i in range(n):
        inp=q.randint(-4,4)
        r={"clock_bucket":q.randint(0,1000000),"rng_bit":q.randint(0,1),"peer_delta":q.randint(-5,5),"tool_value":q.randint(-20,20),"schedule":q.choice(["peer_then_tool","tool_then_peer"])}
        s=step(s,inp,r); rows.append({"input":inp,"receipt":r})
    return rows,s

def replay(rows, missing=(), seed=0):
    q=random.Random(seed); s={"x":0,"score":0}
    for row in rows:
        r=dict(row["receipt"])
        if "clock_bucket" in missing:r["clock_bucket"]=q.randint(0,1000000)
        if "rng_bit" in missing:r["rng_bit"]=q.randint(0,1)
        if "peer_delta" in missing:r["peer_delta"]=q.randint(-5,5)
        if "tool_value" in missing:r["tool_value"]=q.randint(-20,20)
        if "schedule" in missing:r["schedule"]=q.choice(["peer_then_tool","tool_then_peer"])
        s=step(s,row["input"],r)
    return s

def main():
    dims=["clock_bucket","rng_bit","peer_delta","tool_value","schedule"]
    n=5000; sealed=0; omit={d:0 for d in dims}; all_missing=0
    for k in range(n):
        rows,target=generate(100000+k)
        sealed += replay(rows,(),900000+k)!=target
        for d in dims: omit[d] += replay(rows,(d,),900000+k)!=target
        all_missing += replay(rows,dims,900000+k)!=target
    q=random.Random(20260809); full_diff=0
    for i in range(10000):
        state={"balance":q.randint(-1000,1000),"epoch":i}; sem=[{"effect_id":f"e{i}","outcome":"ok","value":q.randint(0,100)}]
        m1={"retries":q.randint(0,3),"latency_us":q.randint(100,10000),"worker":"H1"}
        m2={"retries":q.randint(0,3),"latency_us":q.randint(100,10000),"worker":"H2"}
        full_diff += H({"state":state,"sem":sem,"meta":m1}) != H({"state":state,"sem":sem,"meta":m2})
    result={"sealed_divergent":sealed,"omit_one":omit,"omit_all":all_missing,"dual_identity_full_trace_divergent":full_diff,"dual_identity_pairs":10000}
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__": main()
