"""Deterministic synthetic benchmark for FRANK ActiveAssembly context selection.

Purpose: compare selection mechanisms under a matched model-facing context-cost budget.
This is H1 synthetic mechanism evidence only; it is not a target-4B outcome benchmark.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import math
import random
from typing import Iterable

from research_entity.harness.reference.active_assembly import (
    AssemblyPacket,
    compile_active_assembly,
    packet_score,
)


@dataclass(frozen=True)
class BenchPacket:
    packet: AssemblyPacket
    vector: tuple[float, ...]
    fact_id: str | None
    truth_value: str | None
    is_required_truth: bool
    unresolved_conflict: bool = False


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


def _eligible(xs: Iterable[BenchPacket], epoch: int) -> list[BenchPacket]:
    return [x for x in xs if x.packet.valid_epoch == epoch and not x.packet.proposed_authority]


def topk_cost(xs: Iterable[BenchPacket], *, epoch: int, budget: int, max_items: int) -> list[BenchPacket]:
    out=[]; used=0
    for x in sorted(_eligible(xs, epoch), key=lambda z: (-packet_score(z.packet), z.packet.packet_id)):
        if len(out) >= max_items:
            break
        if used + x.packet.context_cost <= budget:
            out.append(x); used += x.packet.context_cost
    return out


def mmr_cost(xs: Iterable[BenchPacket], *, epoch: int, budget: int, max_items: int, lam: float=.72) -> list[BenchPacket]:
    remaining = _eligible(xs, epoch)
    selected=[]; used=0
    while remaining and len(selected) < max_items:
        feasible=[x for x in remaining if used + x.packet.context_cost <= budget]
        if not feasible:
            break
        def marginal(x: BenchPacket):
            redundancy=max((cosine(x.vector, y.vector) for y in selected), default=0.0)
            # light value-density term: fixed context is a resource constraint.
            density = packet_score(x.packet) / max(1, x.packet.context_cost)
            return lam*packet_score(x.packet) - (1-lam)*redundancy + 0.08*density
        chosen=max(feasible, key=lambda x: (marginal(x), -x.packet.context_cost, x.packet.packet_id))
        selected.append(chosen); used += chosen.packet.context_cost
        remaining.remove(chosen)
    return selected


def active_cost(xs: Iterable[BenchPacket], *, epoch: int, budget: int, max_items: int, max_per_ancestry: int=2) -> list[BenchPacket]:
    lookup={x.packet.packet_id:x for x in xs}
    out=compile_active_assembly(
        [x.packet for x in xs], current_epoch=epoch, max_items=max_items,
        max_per_ancestry=max_per_ancestry, max_context_cost=budget,
    )
    return [lookup[i["packet_id"]] for i in out["items"]]


def active_count_only(xs: Iterable[BenchPacket], *, epoch: int, max_items: int, max_per_ancestry: int=2) -> list[BenchPacket]:
    lookup={x.packet.packet_id:x for x in xs}
    out=compile_active_assembly(
        [x.packet for x in xs], current_epoch=epoch, max_items=max_items,
        max_per_ancestry=max_per_ancestry,
    )
    return [lookup[i["packet_id"]] for i in out["items"]]


def utility(selected: list[BenchPacket], all_packets: list[BenchPacket]) -> dict[str,float]:
    required = sorted({x.fact_id for x in all_packets if x.is_required_truth and x.fact_id is not None})
    by_fact=defaultdict(list)
    for x in selected:
        if x.fact_id is not None:
            by_fact[x.fact_id].append(x)
    total=0.0; covered=0; conflict_visible=0; false_only=0
    for fact in required:
        chosen=by_fact.get(fact, [])
        true_seen=any(x.is_required_truth for x in chosen)
        false_seen=any((x.truth_value is not None and not x.is_required_truth) for x in chosen)
        unresolved=any(x.unresolved_conflict for x in all_packets if x.fact_id == fact)
        if unresolved:
            if true_seen and false_seen:
                total += 1.0; conflict_visible += 1
            elif true_seen:
                total += .72
            elif false_seen:
                total += .30; false_only += 1
        else:
            if true_seen:
                total += 1.0; covered += 1
            elif false_seen:
                total -= .25; false_only += 1
    # Redundancy means multiple packets supporting the same fact/value and same ancestry.
    sigs=[(x.fact_id,x.truth_value,x.packet.ancestry_family) for x in selected if x.fact_id]
    redundancy = 0 if not sigs else 1 - len(set(sigs))/len(sigs)
    cost=sum(x.packet.context_cost for x in selected)
    return {
        "utility": total/max(1,len(required)),
        "fact_coverage": covered/max(1,len(required)),
        "conflict_visibility": conflict_visible/max(1,len(required)),
        "false_only": false_only/max(1,len(required)),
        "redundancy": redundancy,
        "cost": cost,
        "items": len(selected),
    }


def _vec(base: tuple[float,...], rng: random.Random, noise=.08):
    return tuple(v + rng.uniform(-noise,noise) for v in base)


def make_episode(rng: random.Random, i: int, scenario: str, epoch: int=1) -> list[BenchPacket]:
    facts=["f0","f1","f2"]
    bases={f:tuple(1.0 if j==k else 0.08 for j in range(4)) for k,f in enumerate(facts)}
    out=[]
    def add(pid,fam,fact,val,is_true,score,cost,unresolved=False,stale=False,noise=.08):
        relevance=max(0,min(1,score+rng.uniform(-.04,.04)))
        impact=max(0,min(1,score+rng.uniform(-.08,.08)))
        novelty=max(0,min(1,.55+rng.uniform(-.25,.25)))
        uncertainty=max(0,min(1,(.28 if unresolved else .12)+rng.uniform(-.08,.08)))
        p=AssemblyPacket(pid,fam,"knowledge",relevance,impact,novelty,uncertainty,
                         epoch-1 if stale else epoch,fact,val,f"detail:{pid}",context_cost=cost)
        out.append(BenchPacket(p,_vec(bases.get(fact,(.1,.1,.1,1.0)),rng,noise),fact,val,is_true,unresolved))

    if scenario == "echo_conflict":
        # Many same-ancestry high-score echoes versus independent conflicting evidence.
        for j in range(rng.randint(4,8)):
            add(f"e{i}_{j}","echo", "f0","A",True,.90,rng.randint(3,7),unresolved=True,noise=.03)
        add(f"c{i}","independent","f0","B",False,.83,rng.randint(3,6),unresolved=True,noise=.03)
        add(f"t1{i}","fam1","f1","T",True,.78,rng.randint(2,6))
        add(f"t2{i}","fam2","f2","T",True,.76,rng.randint(2,6))
    elif scenario == "variable_cost":
        # One expensive high-score fact competes with several cheaper useful facts.
        add(f"big{i}","fam0","f0","T",True,.98,rng.randint(14,20))
        add(f"cheap0{i}","alt0","f0","T",True,.80,rng.randint(3,5))
        add(f"cheap1{i}","fam1","f1","T",True,.86,rng.randint(3,5))
        add(f"cheap2{i}","fam2","f2","T",True,.84,rng.randint(3,5))
    elif scenario == "concentrated_family":
        # Countercase for hard ancestry caps: different required facts legitimately share one source family.
        for k,f in enumerate(facts):
            add(f"same{i}_{k}","single_authoritative_family",f,"T",True,.88-.02*k,rng.randint(3,5),noise=.12)
        for j in range(3):
            add(f"d{i}_{j}",f"d{j}",None,None,False,.72,rng.randint(2,5),noise=.4)
    elif scenario == "misinfo_swarm":
        # Shared misinformation has high raw score; independent truth is slightly lower.
        for j in range(rng.randint(4,9)):
            add(f"m{i}_{j}","shared_misinfo","f0","F",False,.92,rng.randint(2,5),unresolved=False,noise=.03)
        add(f"truth{i}","independent_truth","f0","T",True,.80,rng.randint(3,5),noise=.03)
        add(f"t1{i}","fam1","f1","T",True,.79,rng.randint(2,5))
        add(f"t2{i}","fam2","f2","T",True,.77,rng.randint(2,5))
    elif scenario == "clean":
        for k,f in enumerate(facts):
            add(f"t{i}_{k}",f"fam{k}",f,"T",True,.88-.03*k,rng.randint(2,6))
        for j in range(5):
            add(f"d{i}_{j}",f"d{j}",None,None,False,.55+rng.random()*.12,rng.randint(2,6),noise=.4)
    else:
        raise ValueError(scenario)

    # Stale high-score packet tests epoch filter without defining the winner.
    add(f"stale{i}","stale","f1","OLD",False,.99,rng.randint(2,5),stale=True)
    return out


def run_benchmark(*, trials_per_scenario: int=5000, seed: int=20260809, budget: int=18, max_items: int=6):
    rng=random.Random(seed)
    scenarios=["echo_conflict","variable_cost","concentrated_family","misinfo_swarm","clean"]
    methods=["topk_cost","mmr_cost","active_cost","active_count_only"]
    agg={s:{m:defaultdict(float) for m in methods} for s in scenarios}
    overflow={s:0 for s in scenarios}
    for s in scenarios:
        for i in range(trials_per_scenario):
            xs=make_episode(rng,i,s)
            selections={
                "topk_cost":topk_cost(xs,epoch=1,budget=budget,max_items=max_items),
                "mmr_cost":mmr_cost(xs,epoch=1,budget=budget,max_items=max_items),
                "active_cost":active_cost(xs,epoch=1,budget=budget,max_items=max_items,max_per_ancestry=2),
                "active_count_only":active_count_only(xs,epoch=1,max_items=max_items,max_per_ancestry=2),
            }
            for m,sel in selections.items():
                metrics=utility(sel,xs)
                for k,v in metrics.items(): agg[s][m][k]+=v
            if sum(x.packet.context_cost for x in selections["active_count_only"]) > budget:
                overflow[s]+=1
    result={}
    for s in scenarios:
        result[s]={}
        for m in methods:
            result[s][m]={k:round(v/trials_per_scenario,5) for k,v in agg[s][m].items()}
        result[s]["count_only_overflow_rate"]=round(overflow[s]/trials_per_scenario,5)
    return result


if __name__ == "__main__":
    import json
    print(json.dumps(run_benchmark(),indent=2,sort_keys=True))
