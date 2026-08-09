#!/usr/bin/env python3
"""Synthetic contract sanity test for FRANK loop-dynamics halt semantics.

This does NOT estimate live FRANK performance. It checks whether a state-delta-only
halting rule can distinguish convergence from stagnation under explicit toy regimes,
and whether adding residual-pressure/divergence checks preserves the distinctions
required by FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md.
"""
import random, math, statistics, json

SEED=5606
N=4000
T=20
REGIMES=["CONVERGING_FIXED_POINT","STALLED","PRODUCTIVE_LIMIT_CYCLE","DIVERGING_OR_OVERTHINKING"]
random.seed(SEED)

cases=[]
for i in range(N):
    regime=REGIMES[i % 4]
    residual=[]; state_delta=[]; utility=[]
    base=random.uniform(.6,1.0)
    for t in range(T):
        noise=random.uniform(-.006,.006)
        if regime=="CONVERGING_FIXED_POINT":
            e=max(0, base*(0.70**t)+noise)
            d=max(0, .22*(0.62**t)+abs(noise)/2)
            u=1-e
        elif regime=="STALLED":
            e=max(.48, base*(0.82**t))+noise
            d=max(0, .18*(0.55**t)+abs(noise)/2)
            u=max(0, .3-e*.1)
        elif regime=="PRODUCTIVE_LIMIT_CYCLE":
            e=max(.04, base*(0.90**t)+noise)
            d=.10+.055*abs(math.sin(t*math.pi/2))+abs(noise)
            u=1-e+0.015*t
        else:
            e=min(1.8, base*(1.07**t)+abs(noise))
            d=min(.8, .07*(1.10**t)+abs(noise))
            u=max(-1, 1-e)
        residual.append(float(e)); state_delta.append(float(d)); utility.append(float(u))
    cases.append((regime,state_delta,residual,utility))

def delta_only(d,e,u):
    low=0
    for t in range(T):
        low = low+1 if d[t] < .03 else 0
        if low >= 2:
            return "HALT", t+1
    return "BUDGET", T

def pressure_aware(d,e,u):
    low=0; rising=0
    for t in range(T):
        if t and e[t] > e[t-1] + .025: rising += 1
        else: rising=max(0,rising-1)
        low = low+1 if d[t] < .03 else 0
        if low >= 2 and e[t] < .08:
            return "HALT", t+1
        if low >= 2 and e[t] > .35:
            return "ESCALATE_STALL", t+1
        if rising >= 3 and e[t] > .8:
            return "ESCALATE_DIVERGE", t+1
    return "BUDGET", T

EXPECTED={
    "CONVERGING_FIXED_POINT":{"HALT"},
    "STALLED":{"ESCALATE_STALL"},
    "PRODUCTIVE_LIMIT_CYCLE":{"BUDGET"},
    "DIVERGING_OR_OVERTHINKING":{"ESCALATE_DIVERGE"},
}

out={"schema_version":"1.0","seed":SEED,"n":N,"steps_per_trace":T,
     "evidence_class":"LOCAL_CONTAINER_SYNTHETIC_CONTRACT_SANITY",
     "promotion_allowed":False,"policies":{}}
for name,policy in [("delta_only",delta_only),("pressure_aware",pressure_aware)]:
    correct=0; false_halt=0; steps=[]
    by={r:{"n":0,"correct":0,"actions":{}} for r in REGIMES}
    for regime,d,e,u in cases:
        action,used=policy(d,e,u); steps.append(used)
        by[regime]["n"]+=1
        by[regime]["actions"][action]=by[regime]["actions"].get(action,0)+1
        ok=action in EXPECTED[regime]
        correct+=int(ok); by[regime]["correct"]+=int(ok)
        if action=="HALT" and regime!="CONVERGING_FIXED_POINT": false_halt+=1
    out["policies"][name]={
        "contract_classification_accuracy":correct/N,
        "false_halt_rate":false_halt/N,
        "mean_recurrence_steps":statistics.mean(steps),
        "by_regime":by,
    }
print(json.dumps(out,indent=2,sort_keys=True))
