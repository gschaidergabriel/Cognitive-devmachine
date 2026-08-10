#!/usr/bin/env python3
"""Deterministic synthetic routing experiment for CLAY_LIVE_FUSION_MESH_V2_CANDIDATE.

Evidence class: SIMULATION_ONLY. This script does not claim live worker/runtime evidence.
"""
from collections import defaultdict, deque
import json
import random

SEED = 20260810
N = 5000
MISSING_OBSERVED_EDGE_RATE = 0.08
random.seed(SEED)

BRANCHES = ["clayresearch","frank","gwt","emergenz","claycode","hyperposition","claygraph","unifieddb","harness"]
BRANCH_TAGS = {
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
ALL_TAGS = sorted(set().union(*BRANCH_TAGS.values()))

claims=[]
for b in BRANCHES:
    for i in range(10):
        t=set(random.sample(sorted(BRANCH_TAGS[b]),2))
        if random.random()<0.30:
            t.add(random.choice(ALL_TAGS))
        claims.append({"id":f"{b}:{i}","branch":b,"tags":t})
CLAIM={c["id"]:c for c in claims}

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

observed_reverse=defaultdict(set)
for premise in sorted(reverse):
    for child in sorted(reverse[premise]):
        if random.random()>MISSING_OBSERVED_EDGE_RATE:
            observed_reverse[premise].add(child)

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

def semantic_branches(delta_tags):
    return {b for b,t in BRANCH_TAGS.items() if t & delta_tags}

def truth(origin,delta_tags,kind):
    out={CLAIM[origin]["branch"]}|semantic_branches(delta_tags)
    if kind in {"CONTRADICTS","SUPERSEDES"}:
        out|={CLAIM[x]["branch"] for x in reach({origin},reverse,3)}
    elif kind=="REFINES":
        out|={CLAIM[x]["branch"] for x in reach({origin},reverse,1)}
    elif kind=="NO_MATERIAL_CHANGE":
        out={CLAIM[origin]["branch"]}
    return out

def broadcast(origin,delta_tags,kind):
    return set(BRANCHES)

def tag_only(origin,delta_tags,kind):
    if kind=="NO_MATERIAL_CHANGE":
        return {CLAIM[origin]["branch"]}
    return {CLAIM[origin]["branch"]}|semantic_branches(delta_tags)

def candidate(origin,delta_tags,kind):
    out=tag_only(origin,delta_tags,kind)
    if kind in {"CONTRADICTS","SUPERSEDES"}:
        out|={CLAIM[x]["branch"] for x in reach({origin},observed_reverse,3)}
    elif kind=="REFINES":
        out|={CLAIM[x]["branch"] for x in reach({origin},observed_reverse,1)}
    return out

KINDS=["NEW","REFINES","CONFIRMS","CONTRADICTS","SUPERSEDES","NO_MATERIAL_CHANGE"]
PROB=[.18,.25,.15,.14,.08,.20]
def pick_kind():
    r=random.random(); total=0.0
    for k,p in zip(KINDS,PROB):
        total+=p
        if r<=total:
            return k
    return KINDS[-1]

results={m:{"deliveries":0,"required":0,"tp":0,"missed":0,"redundant":0,"perfect_events":0} for m in ["broadcast","tag_only","candidate"]}
for _ in range(N):
    c=random.choice(claims)
    kind=pick_kind()
    delta_tags={random.choice(sorted(c["tags"]))}
    if random.random()<0.35:
        delta_tags.add(random.choice(ALL_TAGS))
    required=truth(c["id"],delta_tags,kind)
    for name,router in [("broadcast",broadcast),("tag_only",tag_only),("candidate",candidate)]:
        delivered=router(c["id"],delta_tags,kind)
        tp=len(delivered & required)
        results[name]["deliveries"]+=len(delivered)
        results[name]["required"]+=len(required)
        results[name]["tp"]+=tp
        results[name]["missed"]+=len(required-delivered)
        results[name]["redundant"]+=len(delivered-required)
        results[name]["perfect_events"]+=int(required<=delivered)

for v in results.values():
    v["messages_per_delta"]=v["deliveries"]/N
    v["micro_recall"]=v["tp"]/v["required"]
    v["micro_precision"]=v["tp"]/v["deliveries"]
    v["perfect_event_recall"]=v["perfect_events"]/N

# Exactly one deliberately unusual go-experiment: invert the highest-reach premise whose
# local vocabulary under-represents its transitive dependency impact.
scores=[]
for c in claims:
    affected={CLAIM[x]["branch"] for x in reach({c["id"]},reverse,3)}|{c["branch"]}
    semantic=semantic_branches(c["tags"])|{c["branch"]}
    scores.append((len(affected)-len(semantic),len(affected),c))
scores.sort(reverse=True,key=lambda x:(x[0],x[1],x[2]["id"]))
central=scores[0][2]
oob_tags=set(central["tags"])
oob_required=truth(central["id"],oob_tags,"CONTRADICTS")
oob={}
for name,router in [("broadcast",broadcast),("tag_only",tag_only),("candidate",candidate)]:
    delivered=router(central["id"],oob_tags,"CONTRADICTS")
    oob[name]={"messages":len(delivered),"recall":len(delivered&oob_required)/len(oob_required),"missed":sorted(oob_required-delivered)}

print(json.dumps({
    "schema_version":"1.0",
    "evidence_class":"SIMULATION_ONLY",
    "seed":SEED,
    "n_deltas":N,
    "observed_dependency_edge_missing_rate":MISSING_OBSERVED_EDGE_RATE,
    "results":results,
    "out_of_box":{
        "name":"high_centrality_premise_inversion",
        "origin_claim":central["id"],
        "origin_branch":central["branch"],
        "semantic_tags":sorted(oob_tags),
        "required_branches":sorted(oob_required),
        "routes":oob,
    }
},sort_keys=True,indent=2))
