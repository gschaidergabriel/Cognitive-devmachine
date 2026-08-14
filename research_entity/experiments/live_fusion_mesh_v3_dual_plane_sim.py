#!/usr/bin/env python3
"""Deterministic synthetic experiment for CLAY_LIVE_FUSION_MESH_V3_DUAL_PLANE_CANDIDATE.

Evidence class: SIMULATION_ONLY. It does not claim real worker/repo/runtime evidence.
The deliberately unusual go experiment is the fully-correlated projection blind-spot run.
"""
from collections import defaultdict, deque
import json
import random

SEED=20260810
N=5000
CENTRAL_MISSING=0.08
LOCAL_MISSING=0.08
DIGEST_UNIT=0.03
BRANCHES=["clayresearch","frank","gwt","emergenz","claycode","hyperposition","claygraph","unifieddb","harness"]
BRANCH_TAGS={
 "clayresearch":{"architecture","fusion","research","coordination"},
 "frank":{"frank","loop","reward","runtime","architecture"},
 "gwt":{"gwt","workspace","reentry","attention","loop"},
 "emergenz":{"emergence","causal","lesion","dynamics","gwt"},
 "claycode":{"claycode","ir","compiler","types","runtime"},
 "hyperposition":{"alternatives","topology","uncertainty","causal"},
 "claygraph":{"graph","topology","retrieval","dependencies","reentry"},
 "unifieddb":{"database","persistence","query","events","epochs","dependencies"},
 "harness":{"harness","test","runtime","replay","recovery","compiler"},
}
ALL_TAGS=sorted(set().union(*BRANCH_TAGS.values()))


def build(seed=SEED):
    random.seed(seed)
    claims=[]
    for b in BRANCHES:
        for i in range(10):
            tags=set(random.sample(sorted(BRANCH_TAGS[b]),2))
            if random.random()<0.30:
                tags.add(random.choice(ALL_TAGS))
            claims.append({"id":f"{b}:{i}","branch":b,"tags":tags})
    claim={c["id"]:c for c in claims}
    deps=defaultdict(set)
    for c in claims:
        n=random.choice([1,1,2,2,3])
        candidates=[x for x in claims if x["id"]!=c["id"] and x["branch"]!=c["branch"]]
        weights=[4 if c["tags"] & x["tags"] else 1 for x in candidates]
        chosen=random.choices(candidates,weights=weights,k=n*2)
        seen=set()
        for x in chosen:
            if x["id"] in seen:
                continue
            seen.add(x["id"])
            deps[c["id"]].add(x["id"])
            if len(seen)>=n:
                break
    reverse=defaultdict(set)
    for child in sorted(deps):
        for premise in sorted(deps[child]):
            reverse[premise].add(child)
    return claims,claim,reverse

CLAIMS,CLAIM,REVERSE=build()


def reach(start,graph,depth):
    seen=set(start)
    q=deque((x,0) for x in sorted(start))
    while q:
        x,d=q.popleft()
        if d>=depth:
            continue
        for y in sorted(graph.get(x,set())):
            if y not in seen:
                seen.add(y)
                q.append((y,d+1))
    return seen


def semantic_branches(tags):
    return {b for b,t in BRANCH_TAGS.items() if t & tags}


def required(origin,tags,kind):
    out={CLAIM[origin]["branch"]}|semantic_branches(tags)
    if kind in {"CONTRADICTS","SUPERSEDES"}:
        out|={CLAIM[x]["branch"] for x in reach({origin},REVERSE,3)}
    elif kind=="REFINES":
        out|={CLAIM[x]["branch"] for x in reach({origin},REVERSE,1)}
    elif kind=="NO_MATERIAL_CHANGE":
        out={CLAIM[origin]["branch"]}
    return out


def make_observed(rng,missing,common_missing):
    obs=defaultdict(set)
    all_edges=sum(len(v) for v in REVERSE.values())
    common_fraction=len(common_missing)/max(1,all_edges)
    adjusted=max(0.0,(missing-common_fraction)/max(1e-9,1.0-common_fraction))
    for premise in sorted(REVERSE):
        for child in sorted(REVERSE[premise]):
            if (premise,child) in common_missing:
                continue
            if rng.random()>adjusted:
                obs[premise].add(child)
    return obs

KINDS=["NEW","REFINES","CONFIRMS","CONTRADICTS","SUPERSEDES","NO_MATERIAL_CHANGE"]
PROB=[.18,.25,.15,.14,.08,.20]

def pick_kind(rng):
    r=rng.random(); total=0.0
    for k,p in zip(KINDS,PROB):
        total+=p
        if r<=total:
            return k
    return KINDS[-1]


def run(correlation):
    rng=random.Random(SEED)
    # Canonicalize the edge stream before assigning RNG draws. REVERSE values are sets;
    # unsorted iteration made the correlated fault selection depend on PYTHONHASHSEED.
    edges=sorted((p,c) for p in REVERSE for c in REVERSE[p])
    common=set()
    for edge in edges:
        if rng.random()<min(CENTRAL_MISSING,LOCAL_MISSING)*correlation:
            common.add(edge)
    central=make_observed(rng,CENTRAL_MISSING,common)
    local={b:make_observed(rng,LOCAL_MISSING,common) for b in BRANCHES}
    result={m:{"full":0,"beacon":0,"required":0,"tp":0,"missed":0,"perfect":0} for m in ["broadcast","tag_only","v2","v3_dual_plane"]}
    for _ in range(N):
        c=rng.choice(CLAIMS)
        kind=pick_kind(rng)
        tags={rng.choice(sorted(c["tags"]))}
        if rng.random()<0.35:
            tags.add(rng.choice(ALL_TAGS))
        need=required(c["id"],tags,kind)
        base={CLAIM[c["id"]]["branch"]} if kind=="NO_MATERIAL_CHANGE" else {CLAIM[c["id"]]["branch"]}|semantic_branches(tags)
        routes={"broadcast":set(BRANCHES),"tag_only":set(base)}
        v2=set(base)
        depth=3 if kind in {"CONTRADICTS","SUPERSEDES"} else (1 if kind=="REFINES" else 0)
        if depth:
            v2|={CLAIM[x]["branch"] for x in reach({c["id"]},central,depth)}
        routes["v2"]=v2
        v3=set(v2)
        beacon=len(BRANCHES) if kind!="NO_MATERIAL_CHANGE" else 0
        if depth:
            for b in BRANCHES:
                shadow=reach({c["id"]},local[b],depth)
                if any(CLAIM[x]["branch"]==b for x in shadow):
                    v3.add(b)
        routes["v3_dual_plane"]=v3
        for name,delivered in routes.items():
            tp=len(delivered & need)
            row=result[name]
            row["full"]+=len(delivered)
            row["beacon"]+=beacon if name=="v3_dual_plane" else 0
            row["required"]+=len(need)
            row["tp"]+=tp
            row["missed"]+=len(need-delivered)
            row["perfect"]+=int(need<=delivered)
    for row in result.values():
        row["full_per_delta"]=row["full"]/N
        row["beacon_per_delta"]=row["beacon"]/N
        row["weighted_network_cost_per_delta"]=row["full_per_delta"]+DIGEST_UNIT*row["beacon_per_delta"]
        row["micro_recall"]=row["tp"]/row["required"]
        row["perfect_event_recall"]=row["perfect"]/N
    return result

normal=run(0.0)
out_of_box=run(1.0)
print(json.dumps({
 "schema_version":"1.0",
 "evidence_class":"SIMULATION_ONLY",
 "seed":SEED,
 "n_deltas":N,
 "central_dependency_edge_missing_rate":CENTRAL_MISSING,
 "local_shadow_missing_rate":LOCAL_MISSING,
 "beacon_relative_cost_unit":DIGEST_UNIT,
 "normal_independent_shadow":normal,
 "out_of_box":{
   "count":1,
   "name":"fully_correlated_projection_blind_spot",
   "purpose":"Falsify the assumption that a second routing projection helps when both projections share the same missing-edge ancestry.",
   "correlation":1.0,
   "results":out_of_box,
 },
},sort_keys=True,indent=2))
