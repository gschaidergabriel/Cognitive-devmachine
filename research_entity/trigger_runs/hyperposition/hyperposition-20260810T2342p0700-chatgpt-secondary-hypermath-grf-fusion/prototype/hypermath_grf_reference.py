#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from random import Random
from statistics import median
from time import perf_counter
from typing import Callable, Dict, Mapping, Sequence, Tuple
import json


@dataclass(frozen=True)
class LawCertificate:
    carrier: str
    exact_rewrites: frozenset[str]
    forbidden_rewrites: frozenset[str] = frozenset()
    def licenses(self, rewrite: str) -> bool:
        return rewrite in self.exact_rewrites and rewrite not in self.forbidden_rewrites


@dataclass(frozen=True)
class Semiring:
    name: str
    add: Callable[[float,float],float]
    mul: Callable[[float,float],float]
    zero: float
    one: float
    law: LawCertificate


SUM_PRODUCT = Semiring(
    "sum_product", lambda a,b:a+b, lambda a,b:a*b, 0.0, 1.0,
    LawCertificate("probability", frozenset({"VARIABLE_ELIMINATION"})))

UNSAFE_MEAN_PRODUCT = Semiring(
    "mean_product", lambda a,b:(a+b)/2.0, lambda a,b:a*b, 0.0, 1.0,
    LawCertificate("unsafe_mean", frozenset(), frozenset({"VARIABLE_ELIMINATION"})))


@dataclass(frozen=True)
class Factor:
    vars: Tuple[str,...]
    table: Mapping[Tuple[int,...],float]
    def get(self, a: Mapping[str,int]) -> float:
        return self.table[tuple(a[v] for v in self.vars)]


def multiply(fs: Sequence[Factor], domains, s: Semiring) -> Factor:
    vs=[]
    for f in fs:
        for v in f.vars:
            if v not in vs: vs.append(v)
    table={}
    for vals in product(*(domains[v] for v in vs)):
        a=dict(zip(vs,vals)); x=s.one
        for f in fs: x=s.mul(x,f.get(a))
        table[vals]=x
    return Factor(tuple(vs),table)


def eliminate(fs: Sequence[Factor], var: str, domains, s: Semiring):
    hit=[f for f in fs if var in f.vars]; rest=[f for f in fs if var not in f.vars]
    if not hit: return list(fs)
    joint=multiply(hit,domains,s); out=tuple(v for v in joint.vars if v!=var); table={}
    for vals in product(*(domains[v] for v in out)):
        base=dict(zip(out,vals)); first=True; acc=s.zero
        for x in domains[var]:
            a=dict(base); a[var]=x; y=joint.get(a)
            acc=y if first else s.add(acc,y); first=False
        table[vals]=acc
    return rest+[Factor(out,table)]


def variable_elimination(fs, domains, s: Semiring):
    if not s.law.licenses("VARIABLE_ELIMINATION"):
        raise ValueError("UNLICENSED_REWRITE")
    cur=list(fs)
    for v in domains: cur=eliminate(cur,v,domains,s)
    return next(iter(multiply(cur,domains,s).table.values()))


def flat(fs, domains, s: Semiring):
    vs=tuple(domains); first=True; total=s.zero
    for vals in product(*(domains[v] for v in vs)):
        a=dict(zip(vs,vals)); x=s.one
        for f in fs: x=s.mul(x,f.get(a))
        total=x if first else s.add(total,x); first=False
    return total


def chain(n: int, rng: Random):
    domains={f"x{i}":(0,1) for i in range(n)}; fs=[]
    for i in range(n):
        p=.15+.7*rng.random(); fs.append(Factor((f"x{i}",),{(0,):1-p,(1,):p}))
    for i in range(n-1):
        a,b=f"x{i}",f"x{i+1}"; t={}
        for va,vb in product((0,1),repeat=2):
            x=.5+rng.random(); t[(va,vb)]=x*(1.35 if va==vb else 1.0)
        fs.append(Factor((a,b),t))
    return domains,fs


@dataclass(frozen=True)
class HHandle:
    href: str
    semantic_root: str
    state_epoch: int
    execution_generation: int
    delivery_generation: int


def resolve(h: HHandle, *, semantic_root, state_epoch, execution_generation, delivery_generation):
    checks=[
        (h.semantic_root==semantic_root,"SEMANTIC_ROOT_MISMATCH"),
        (h.state_epoch==state_epoch,"STATE_EPOCH_MISMATCH"),
        (h.execution_generation==execution_generation,"EXECUTION_GENERATION_MISMATCH"),
        (h.delivery_generation==delivery_generation,"DELIVERY_GENERATION_MISMATCH")]
    for ok,reason in checks:
        if not ok: raise ValueError(reason)
    return True


def context_guard(original,visible,hidden_reads,declared_reads):
    original=set(original); visible=set(visible); hidden=set(hidden_reads); declared=set(declared_reads)
    smuggled=bool((original-visible)&hidden); complete=hidden<=declared
    return {"context_smuggling_detected":smuggled,
            "material_read_signature_complete":complete,
            "semantic_reduction_admissible":complete and not smuggled,
            "operational_reduction_may_still_be_allowed":complete}


@dataclass(frozen=True)
class RealityCase:
    base: float
    actual_sim: float
    predicted_sim: float
    reward_good: float
    reward_bad: float
    sim_cost: float
    ood: float
    def utility(self, simulate: bool):
        p=self.actual_sim if simulate else self.base
        return p*self.reward_good+(1-p)*self.reward_bad-(self.sim_cost if simulate else 0.0)


def make_cases(n, rng):
    out=[]
    for _ in range(n):
        uncertainty=rng.random(); ood=rng.random(); base=.45+.4*rng.random()
        actual=min(.99,base+(.04+.42*uncertainty)*(1-.7*ood))
        noise=(rng.random()-.5)*(.04+.22*ood); pred=min(.99,max(.01,actual+noise))
        out.append(RealityCase(base,actual,pred,1.0,-.45-.8*rng.random(),.015+.28*rng.random(),ood))
    return out


def eval_policy(cases, policy):
    u=0.; n=0
    for c in cases:
        s=policy(c); n+=int(s); u+=c.utility(s)
    return {"mean_utility":u/len(cases),"simulation_rate":n/len(cases)}


def gate(mult,ood_discount):
    def f(c):
        gain=(c.predicted_sim-c.base)*(c.reward_good-c.reward_bad)
        return mult*gain*max(0.,1-ood_discount*c.ood)>c.sim_cost
    return f


def calibrate(cases):
    best=None
    for m in (.6,.8,1.,1.2,1.4):
        for d in (0.,.25,.5,.75,1.):
            r=eval_policy(cases,gate(m,d)); key=(r["mean_utility"],-r["simulation_rate"])
            if best is None or key>best[0]: best=(key,m,d,r)
    return best[1],best[2],best[3]


def thin_transport(n=10000):
    annotation={"epistemic":"HYPOTHETICAL","state_epoch":42,"execution_generation":7,
                "delivery_generation":11,"reality_class":"PREDICTED","provenance":["e1","e2"]}
    a=json.dumps(annotation,sort_keys=True,separators=(",",":")); href=sha256(a.encode()).hexdigest()
    full=thin=0
    for i in range(n):
        s=f"claim:{i}:payload:{i%97}"; full+=len((s+a).encode()); thin+=len((s+"^h{"+href+"}").encode())
    thin+=len(a.encode())
    return {"full_bytes":full,"thin_bytes":thin,"reduction_pct":100*(1-thin/full)}


def run():
    rng=Random(20260810); domains,fs=chain(15,rng); ft=[]; vt=[]; err=[]
    for _ in range(3):
        t=perf_counter(); a=flat(fs,domains,SUM_PRODUCT); ft.append(perf_counter()-t)
        t=perf_counter(); b=variable_elimination(fs,domains,SUM_PRODUCT); vt.append(perf_counter()-t); err.append(abs(a-b))
    rejected=False
    try: variable_elimination(fs,domains,UNSAFE_MEAN_PRODUCT)
    except ValueError: rejected=True

    node_hash=sha256(b"ALT:a:b:epoch42").hexdigest(); h=HHandle(node_hash,"root42",42,7,11); stale=[]
    for kw in [dict(semantic_root="root42",state_epoch=43,execution_generation=7,delivery_generation=11),
               dict(semantic_root="root42",state_epoch=42,execution_generation=8,delivery_generation=11),
               dict(semantic_root="root42",state_epoch=42,execution_generation=7,delivery_generation=12)]:
        try: resolve(h,**kw)
        except ValueError as e: stale.append(str(e))

    train=make_cases(20000,Random(920)); test=make_cases(50000,Random(921)); m,d,fit=calibrate(train); g=gate(m,d)
    return {
      "factorization":{"possible_worlds":2**15,"max_abs_error":max(err),"flat_median_seconds":median(ft),
                       "ve_median_seconds":median(vt),"speedup":median(ft)/median(vt),"unsafe_rewrite_rejected":rejected},
      "context_guard":context_guard(["a","b","c"],["a","b"],["c"],["c"]),
      "thin_net":{"current_resolves":resolve(h,semantic_root="root42",state_epoch=42,execution_generation=7,delivery_generation=11),
                  "stale_reasons":stale,"transport":thin_transport()},
      "grf":{"calibration":{"multiplier":m,"ood_discount":d,"train":fit},
             "heldout":{"never":eval_policy(test,lambda c:False),"always":eval_policy(test,lambda c:True),
                        "selective":eval_policy(test,g),"oracle":eval_policy(test,lambda c:c.utility(True)>c.utility(False))}}
    }

if __name__ == "__main__": print(json.dumps(run(),indent=2,sort_keys=True))
