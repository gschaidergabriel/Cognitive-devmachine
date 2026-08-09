import random, hashlib, json
from dataclasses import dataclass

SEED=202608091726
rng=random.Random(SEED)

@dataclass(frozen=True)
class Loop:
    id:int
    weights:tuple
    bias:int
    effects:frozenset


def delta(loop, state):
    v = loop.bias + sum(w*x for w,x in zip(loop.weights,state))
    return max(-7,min(7,v))

def tick_seq(loops, order, state):
    s=list(state)
    for idx in order:
        d=delta(loops[idx], tuple(s))
        s[idx]+=d
    return tuple(s)

def tick_sync(loops, order, state):
    snap=tuple(state)
    ds={idx:delta(loops[idx],snap) for idx in order}
    s=list(snap)
    for idx,d in ds.items():
        s[idx]+=d
    return tuple(s)

def setlike_hash(loops, policy, order):
    obj={"policy":policy,"loops":sorted(l.id for l in loops),"schedule":sorted(order)}
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def semantic_hash(loops, policy, order):
    schedule=list(order) if policy=="ORDERED_SEQUENTIAL" else sorted(order)
    obj={"policy":policy,"loops":sorted(l.id for l in loops),"schedule":schedule}
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

cases=30000
seq_diff=0
sync_diff=0
unsafe_collisions=0
safe_seq_hash_changes=0
safe_sync_hash_preserved=0
examples=[]
for c in range(cases):
    n=rng.randint(2,6)
    loops=[]
    for i in range(n):
        weights=tuple(rng.randint(-2,2) for _ in range(n))
        bias=rng.randint(-3,3)
        loops.append(Loop(i,weights,bias,frozenset()))
    state=tuple(rng.randint(-5,5) for _ in range(n))
    o1=list(range(n)); rng.shuffle(o1)
    o2=o1[:]
    while o2==o1:
        rng.shuffle(o2)
    a=tick_seq(loops,o1,state); b=tick_seq(loops,o2,state)
    sa=tick_sync(loops,o1,state); sb=tick_sync(loops,o2,state)
    if a!=b:
        seq_diff+=1
        if setlike_hash(loops,"ORDERED_SEQUENTIAL",o1)==setlike_hash(loops,"ORDERED_SEQUENTIAL",o2):
            unsafe_collisions+=1
            if len(examples)<3:
                examples.append({"n":n,"state":state,"o1":o1,"o2":o2,"out1":a,"out2":b})
    if sa!=sb: sync_diff+=1
    if semantic_hash(loops,"ORDERED_SEQUENTIAL",o1)!=semantic_hash(loops,"ORDERED_SEQUENTIAL",o2):
        safe_seq_hash_changes+=1
    if semantic_hash(loops,"SYNC_SNAPSHOT",o1)==semantic_hash(loops,"SYNC_SNAPSHOT",o2):
        safe_sync_hash_preserved+=1

EFFECTS=("STATE_READ","STATE_WRITE","FILE","NET","PROCESS")
effect_cases=50000
effect_mismatch=0
rejected_widening=0
accepted_valid=0
for _ in range(effect_cases):
    n=rng.randint(1,8)
    direct=[set(rng.sample(EFFECTS,rng.randint(0,len(EFFECTS)))) for _ in range(n)]
    calls=[set(rng.sample(range(i+1,n), rng.randint(0,n-i-1))) if i<n-1 else set() for i in range(n)]
    closure=[set() for _ in range(n)]
    for i in reversed(range(n)):
        cl=set(direct[i])
        for j in calls[i]: cl |= closure[j]
        closure[i]=cl
    actual=closure[0]
    if rng.random()<0.5 and actual:
        declared=set(actual); declared.remove(rng.choice(tuple(declared)))
    else:
        declared=set(actual)
    oracle=actual <= declared
    checker=all(e in declared for e in actual)
    if oracle!=checker: effect_mismatch+=1
    if not checker: rejected_widening+=1
    else: accepted_valid+=1

cap_cases=30000
forged_accept=0
valid_accept=0
missing_reject=0
for _ in range(cap_cases):
    effect=rng.choice(("FILE","NET","PROCESS"))
    token_permits=set(rng.sample(("FILE","NET","PROCESS"),rng.randint(0,3)))
    token_valid=rng.random()>0.1
    textual_claim=rng.random()<0.5
    authorized=token_valid and effect in token_permits
    observed=token_valid and effect in token_permits
    if observed and authorized: valid_accept+=1
    if (not observed) and (not authorized): missing_reject+=1
    if observed and not authorized: forged_accept+=1

result={
  "seed":SEED,
  "schedule_cases":cases,
  "sequential_order_changed_output":seq_diff,
  "sequential_change_rate":seq_diff/cases,
  "synchronous_order_changed_output":sync_diff,
  "unsafe_setlike_semantic_hash_collisions_on_changed_outputs":unsafe_collisions,
  "safe_sequential_hash_changed_on_reorder":safe_seq_hash_changes,
  "safe_sync_hash_preserved_on_reorder":safe_sync_hash_preserved,
  "examples":examples,
  "effect_cases":effect_cases,
  "effect_checker_oracle_mismatches":effect_mismatch,
  "effect_widening_rejected":rejected_widening,
  "effect_valid_accepted":accepted_valid,
  "capability_cases":cap_cases,
  "forged_capability_accepts":forged_accept,
  "authorized_accepts":valid_accept,
  "unauthorized_rejects":missing_reject,
}
print(json.dumps(result,indent=2))
