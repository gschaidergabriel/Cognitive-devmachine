#!/usr/bin/env python3
"""Synthetic falsifier for FRANK H1 ActiveAssembly conflict-budget scheduling.

Evidence class: SYNTHETIC. This experiment deliberately labels three packets per trial
as task-critical and therefore cannot calibrate a production conflict quota. It tests a
narrow mechanism question: can unconditional conflict-first reservation starve high-value
non-conflict evidence under a hard Assembly budget?
"""
from __future__ import annotations
from dataclasses import dataclass
import random

@dataclass(frozen=True)
class P:
    packet_id: str
    ancestry_family: str
    kind: str
    relevance: float
    impact: float
    novelty: float
    uncertainty: float
    valid_epoch: int
    claim_key: str | None = None
    claim_value: str | None = None

def score(p: P) -> float:
    return round(.45*p.relevance + .25*p.impact + .15*p.novelty + .15*(1-p.uncertainty), 12)

def select(candidates, *, max_items=8, max_per_ancestry=2, conflict_cap=None):
    eligible = sorted(candidates, key=lambda p: (-score(p), p.packet_id))
    selected, ids, counts = [], set(), {}
    def add(p):
        if p.packet_id in ids or len(selected) >= max_items:
            return False
        if counts.get(p.ancestry_family, 0) >= max_per_ancestry:
            return False
        selected.append(p); ids.add(p.packet_id)
        counts[p.ancestry_family] = counts.get(p.ancestry_family, 0) + 1
        return True
    by_claim = {}
    for p in eligible:
        if p.claim_key is not None and p.claim_value is not None:
            by_claim.setdefault(p.claim_key, {}).setdefault(p.claim_value, p)
    reps = []
    for values in by_claim.values():
        if len(values) > 1:
            reps.extend(values.values())
    reps.sort(key=lambda p: (-score(p), p.packet_id))
    for p in reps:
        if conflict_cap is not None and len(selected) >= conflict_cap:
            break
        add(p)
    seen = set()
    for p in eligible:
        if p.ancestry_family not in seen:
            add(p); seen.add(p.ancestry_family)
    for p in eligible:
        add(p)
    return selected

def direct_counterexample():
    fixture = []
    for i in range(4):
        fixture += [
            P(f"c{i}a", f"ca{i}", "knowledge", .55,.55,.55,.25,1,f"claim{i}","A"),
            P(f"c{i}b", f"cb{i}", "knowledge", .54,.54,.54,.25,1,f"claim{i}","B"),
        ]
    for i in range(3):
        fixture.append(P(f"critical{i}", f"crit{i}", "knowledge", .99,.99,.95,.02,1))
    current = select(fixture)
    quota = select(fixture, conflict_cap=4)
    return {
        "current_selected": [p.packet_id for p in current],
        "quota_selected": [p.packet_id for p in quota],
        "current_critical": sum(p.packet_id.startswith("critical") for p in current),
        "quota_critical": sum(p.packet_id.startswith("critical") for p in quota),
    }

def sweep(seed=20260809, trials=10000):
    rng = random.Random(seed)
    stats = {k:{"crit":0,"allcrit":0,"fullpairs":0,"claims":0} for k in ("current","quota")}
    for t in range(trials):
        cand=[]; nclaims=rng.randint(0,7)
        for i in range(nclaims):
            base=rng.uniform(.45,.88)
            for v in ("A","B"):
                cand.append(P(f"{t}-c{i}-{v}",f"{t}-cfam{i}-{v}","knowledge",
                    min(1,base+rng.uniform(-.04,.04)),rng.uniform(.45,.9),rng.uniform(.25,.85),rng.uniform(.05,.35),1,
                    f"claim{i}",v))
        critical=[]
        for i in range(3):
            p=P(f"{t}-critical{i}",f"{t}-crit{i}","knowledge",rng.uniform(.91,1),rng.uniform(.90,1),rng.uniform(.75,1),rng.uniform(.01,.10),1)
            critical.append(p); cand.append(p)
        for i in range(rng.randint(2,8)):
            cand.append(P(f"{t}-d{i}",f"{t}-dfam{i}","knowledge",rng.uniform(.35,.85),rng.uniform(.3,.85),rng.uniform(.1,.8),rng.uniform(.05,.45),1))
        for name, chosen in (("current",select(cand)),("quota",select(cand, conflict_cap=4))):
            ids={p.packet_id for p in chosen}; c=sum(p.packet_id in ids for p in critical)
            stats[name]["crit"] += c; stats[name]["allcrit"] += (c == 3); stats[name]["claims"] += nclaims
            for i in range(nclaims):
                stats[name]["fullpairs"] += (f"{t}-c{i}-A" in ids and f"{t}-c{i}-B" in ids)
    out={}
    for name,s in stats.items():
        out[name]={
            "critical_recall": s["crit"]/(trials*3),
            "all_3_critical_rate": s["allcrit"]/trials,
            "complete_conflict_pair_rate_per_generated_claim": s["fullpairs"]/s["claims"] if s["claims"] else 1,
            "trials": trials,
            "generated_conflict_claims": s["claims"],
        }
    return out

if __name__ == "__main__":
    import json
    print(json.dumps({"direct":direct_counterexample(),"sweep":sweep()}, indent=2, sort_keys=True))
