from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional
import random, time, statistics, json

ARG_TYPES = ("Int", "Bool", "String", "Bytes", "Float", "Ref", "List", "Map")
RET_TYPES = ARG_TYPES
EFFECTS = ("PURE", "READ_ONLY", "REVERSIBLE_WRITE", "EXTERNAL_COMMUNICATION", "PRIVILEGED_CHANGE", "UNKNOWN_EFFECT")

class ProbeMode(str, Enum):
    FIELD_VALUE = "FIELD_VALUE_WITNESS"
    FIELD_ONLY = "FIELD_ONLY_WITNESS"
    BOOL_ONLY = "BOOL_ONLY"

@dataclass(frozen=True)
class RuntimeWitness:
    native_self: str
    epoch: int
    current_epoch: int
    sandbox_dry_run: bool = True

@dataclass(frozen=True)
class Contract:
    args: Tuple[str, ...]
    ret: str
    effect: str

@dataclass(frozen=True)
class DiagnosticWitness:
    status: str
    field_index: Optional[int] = None
    observed_value: Optional[str] = None
    authority_minted: bool = False
    reason: str = ""

class SyntheticCallableOracle:
    """Synthetic reference oracle. It never executes an external effect."""
    def __init__(self, truth: Contract): self.truth = truth
    def fields(self, c: Contract): return list(c.args) + [c.ret, c.effect]
    def probe(self, candidate: Contract, witness: RuntimeWitness, mode: ProbeMode) -> DiagnosticWitness:
        if witness.native_self != "self.root": return DiagnosticWitness("REJECT_IDENTITY", reason="native_self_mismatch")
        if witness.epoch != witness.current_epoch: return DiagnosticWitness("REJECT_STALE", reason="epoch_mismatch")
        if not witness.sandbox_dry_run and self.truth.effect not in ("PURE", "READ_ONLY"):
            return DiagnosticWitness("UNKNOWN", reason="unsafe_probe_surface")
        q, t = self.fields(candidate), self.fields(self.truth)
        if q == t: return DiagnosticWitness("PASS", authority_minted=False)
        if mode == ProbeMode.BOOL_ONLY: return DiagnosticWitness("MISMATCH", authority_minted=False)
        idx = next(i for i,(a,b) in enumerate(zip(q,t)) if a != b)
        if mode == ProbeMode.FIELD_ONLY: return DiagnosticWitness("MISMATCH", field_index=idx, authority_minted=False)
        return DiagnosticWitness("MISMATCH", field_index=idx, observed_value=t[idx], authority_minted=False)

def default_contract(arity: int) -> Contract:
    return Contract(args=tuple(ARG_TYPES[0] for _ in range(arity)), ret=RET_TYPES[0], effect=EFFECTS[0])

def set_field(c: Contract, idx: int, value: str) -> Contract:
    vals = list(c.args) + [c.ret, c.effect]; vals[idx] = value; arity = len(c.args)
    return Contract(tuple(vals[:arity]), vals[arity], vals[arity+1])

def field_domain(arity: int, idx: int):
    if idx < arity: return ARG_TYPES
    if idx == arity: return RET_TYPES
    return EFFECTS

def contract_space_size(arity: int) -> int:
    return (len(ARG_TYPES) ** arity) * len(RET_TYPES) * len(EFFECTS)

def lexicographic_rank(c: Contract) -> int:
    vals = list(c.args) + [c.ret, c.effect]; domains = [ARG_TYPES]*len(c.args)+[RET_TYPES,EFFECTS]; rank = 0
    for v,d in zip(vals,domains): rank = rank*len(d)+d.index(v)
    return rank + 1

def ect_recover(truth: Contract, mode: ProbeMode, witness: RuntimeWitness, budget: int=128):
    oracle = SyntheticCallableOracle(truth); c = default_contract(len(truth.args))
    eliminated = {i:set() for i in range(len(truth.args)+2)}; bound_values = {}; trace=[]
    for qn in range(1,budget+1):
        d = oracle.probe(c,witness,mode); trace.append(d)
        if d.status == "PASS": return {"status":"ADMITTED", "contract":c, "queries":qn, "trace":trace, "authority_minted":False}
        if d.status in ("REJECT_IDENTITY","REJECT_STALE","UNKNOWN"):
            return {"status":"UNKNOWN", "contract":None, "queries":qn, "trace":trace, "authority_minted":False}
        if mode == ProbeMode.BOOL_ONLY:
            return {"status":"UNKNOWN", "contract":None, "queries":qn, "trace":trace, "authority_minted":False}
        idx=d.field_index; assert idx is not None
        if mode == ProbeMode.FIELD_VALUE:
            if d.observed_value is None: return {"status":"QUARANTINED", "contract":None, "queries":qn, "trace":trace, "authority_minted":False}
            if idx in bound_values and bound_values[idx] != d.observed_value:
                return {"status":"QUARANTINED", "contract":None, "queries":qn, "trace":trace, "authority_minted":False}
            bound_values[idx] = d.observed_value; c = set_field(c,idx,d.observed_value)
        else:
            vals=list(c.args)+[c.ret,c.effect]; current=vals[idx]; eliminated[idx].add(current)
            choices=[x for x in field_domain(len(c.args),idx) if x not in eliminated[idx]]
            if not choices: return {"status":"QUARANTINED", "contract":None, "queries":qn, "trace":trace, "authority_minted":False}
            c=set_field(c,idx,choices[0])
    return {"status":"UNKNOWN", "contract":None, "queries":budget, "trace":trace, "authority_minted":False}

def random_contract(rng: random.Random, arity: int) -> Contract:
    return Contract(tuple(rng.choice(ARG_TYPES) for _ in range(arity)), rng.choice(RET_TYPES), rng.choice(EFFECTS))

def quantiles(xs):
    s=sorted(xs)
    def q(p):
        if not s:return None
        i=int(round((len(s)-1)*p)); return s[i]
    return {"p50":q(.5),"p95":q(.95),"p99":q(.99),"min":s[0],"max":s[-1],"mean":statistics.fmean(s)}

def benchmark(seed=20260810, n=50000):
    rng=random.Random(seed); q_full=[]; q_field=[]; q_lex=[]; q_random=[]; sizes=[]; full_ok=field_ok=0; t0=time.perf_counter()
    for _ in range(n):
        arity=rng.randrange(0,6); truth=random_contract(rng,arity); w=RuntimeWitness("self.root",7,7,True)
        r1=ect_recover(truth,ProbeMode.FIELD_VALUE,w,64); r2=ect_recover(truth,ProbeMode.FIELD_ONLY,w,128)
        full_ok += int(r1["status"]=="ADMITTED" and r1["contract"]==truth); field_ok += int(r2["status"]=="ADMITTED" and r2["contract"]==truth)
        q_full.append(r1["queries"]); q_field.append(r2["queries"]); size=contract_space_size(arity); sizes.append(size)
        q_lex.append(lexicographic_rank(truth)); q_random.append(rng.randint(1,size))
    return {"seed":seed,"n":n,"elapsed_s":time.perf_counter()-t0,
      "field_value":{"exact_recovery_rate":full_ok/n,"queries":quantiles(q_full)},
      "field_only":{"exact_recovery_rate":field_ok/n,"queries":quantiles(q_field)},
      "lexicographic_exhaustive":{"queries":quantiles(q_lex)},
      "random_without_replacement_proxy":{"queries":quantiles(q_random)},
      "contract_space_size":quantiles(sizes),
      "trusted_metadata_baseline":{"queries":1,"note":"dominates ECT when exact authenticated metadata already exists"}}

def negative_tests():
    truth=Contract(("Int","String"),"Bool","REVERSIBLE_WRITE"); good=RuntimeWitness("self.root",9,9,True)
    stale=RuntimeWitness("self.root",8,9,True); wrong=RuntimeWitness("Frank.id",9,9,True); unsafe=RuntimeWitness("self.root",9,9,False)
    a=ect_recover(truth,ProbeMode.FIELD_VALUE,good)
    assert a["status"]=="ADMITTED" and a["contract"]==truth and not a["authority_minted"]
    assert ect_recover(truth,ProbeMode.FIELD_VALUE,stale)["status"]=="UNKNOWN"
    assert ect_recover(truth,ProbeMode.FIELD_VALUE,wrong)["status"]=="UNKNOWN"
    assert ect_recover(truth,ProbeMode.FIELD_VALUE,unsafe)["status"]=="UNKNOWN"
    assert ect_recover(truth,ProbeMode.BOOL_ONLY,good)["status"] in ("ADMITTED","UNKNOWN")
    b=ect_recover(truth,ProbeMode.BOOL_ONLY,good); assert b["status"]=="UNKNOWN"
    return {"tests":6,"passed":6}

if __name__ == '__main__':
    out={"negative_tests":negative_tests(),"benchmark":benchmark()}
    print(json.dumps(out,indent=2))
