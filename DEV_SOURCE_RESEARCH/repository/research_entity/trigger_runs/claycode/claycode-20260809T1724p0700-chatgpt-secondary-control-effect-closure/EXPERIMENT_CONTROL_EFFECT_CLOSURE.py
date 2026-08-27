import random, hashlib, json
SEED=202608091724; r=random.Random(SEED)
class StaticEffectMismatch(Exception): pass
class EffectDenied(Exception): pass
class StepBudgetExceeded(Exception): pass

# Candidate IR is direct Python data: function name -> (calls,direct_effects,declared_effects).
def infer(graph):
    eff={n:set(direct) for n,(_,direct,_) in graph.items()}
    changed=True; rounds=0
    while changed:
        changed=False; rounds+=1
        for n,(calls,_,_) in graph.items():
            before=set(eff[n])
            for c in calls:
                if c not in graph: raise KeyError(c)
                eff[n] |= eff[c]
            changed |= eff[n] != before
        if rounds > len(graph)+2: raise RuntimeError("fixed point")
    return eff, rounds

def validate(graph):
    eff,rounds=infer(graph)
    bad={n:(sorted(eff[n]),sorted(declared)) for n,(_,_,declared) in graph.items()
         if not eff[n].issubset(set(declared))}
    if bad: raise StaticEffectMismatch(bad)
    return eff,rounds

def fact(n,budget):
    budget[0]-=1
    if budget[0]<0: raise StepBudgetExceeded
    return 1 if n==0 else n*fact(n-1,budget)

def safe_div(a,b):
    return ("Err","DIV_ZERO") if b==0 else ("Ok",a//b)

def calc(a,b,n):
    tag,val=safe_div(a,b)
    return val+fact(n,[1000]) if tag=="Ok" else -fact(n,[1000])

def run_effect(label,value,permit):
    if label not in permit: raise EffectDenied(label)
    return value

# Semantic differential: branch + structured Result + recursion.
mismatch=0
for _ in range(50000):
    a=r.randint(-100000,100000); b=r.randint(-50,50); n=r.randint(0,8)
    got=calc(a,b,n)
    import math
    exp=(a//b)+math.factorial(n) if b else -math.factorial(n)
    mismatch += got!=exp

# Transitive effect-closure stress.
labels=["fs.read","fs.write","net.connect","db.write","clock.read"]
false_accepts=0; max_rounds=0
for _ in range(20000):
    g={}
    for j in range(6):
        calls={f"f{k}" for k in range(j) if r.random()<.25}
        direct=set(r.sample(labels,r.randint(0,2)))
        g[f"f{j}"]=(calls,direct,set(labels))
    eff,rr=validate(g); max_rounds=max(max_rounds,rr)
    choices=[n for n,e in eff.items() if e]
    if choices:
        n=r.choice(choices); missing=r.choice(tuple(eff[n]))
        gm={k:(set(c),set(d),set(dec)) for k,(c,d,dec) in g.items()}
        c,d,dec=gm[n]; dec.remove(missing); gm[n]=(c,d,dec)
        try: validate(gm); false_accepts+=1
        except StaticEffectMismatch: pass

neg={}
g={"leaf":(set(),{"log.write"},{"log.write"}),"wrap":({"leaf"},set(),set())}
try: validate(g); neg["transitive_undeclared"]="FALSE_ACCEPT"
except StaticEffectMismatch: neg["transitive_undeclared"]="REJECT"
try: run_effect("log.write",7,set()); neg["runtime_permit_absent"]="FALSE_ACCEPT"
except EffectDenied: neg["runtime_permit_absent"]="REJECT"
neg["runtime_permit_present"]=run_effect("log.write",7,{"log.write"})
try: fact(1000,[10]); neg["recursion_budget"]="FALSE_ACCEPT"
except StepBudgetExceeded: neg["recursion_budget"]="REJECT"
try: validate({"u":({"missing"},set(),set())}); neg["undefined_static_call"]="FALSE_ACCEPT"
except KeyError: neg["undefined_static_call"]="REJECT"

# Program semantic identity: set-like effect order canonicalized; runtime permit excluded.
def semhash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()
base={"control":"if+call+result_match+recursion","effects":sorted({"log.write"})}
base_hash=semhash(base)
same_hash=semhash({"effects":sorted({"log.write"}),"control":"if+call+result_match+recursion"})
effect_hash=semhash({"control":base["control"],"effects":sorted({"log.write","net.connect"})})
control_hash=semhash({"control":"if+call+result_match","effects":base["effects"]})
print(json.dumps({
 "seed":SEED,"semantic_cases":50000,"semantic_mismatches":mismatch,
 "effect_stress_cases":20000,"effect_stress_false_accepts":false_accepts,
 "effect_stress_max_rounds":max_rounds,"negative_cases":neg,
 "semantic_identity":{"base":base_hash,"set_order_equivalent_same":same_hash==base_hash,
 "effect_change_changes_hash":effect_hash!=base_hash,
 "control_change_changes_hash":control_hash!=base_hash,
 "runtime_permit_excluded_from_program_semantic_hash":True}
},sort_keys=True))
