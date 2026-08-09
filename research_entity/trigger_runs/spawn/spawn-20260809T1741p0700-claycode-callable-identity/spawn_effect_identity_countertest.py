import random, hashlib, json
from collections import defaultdict, deque
R=random.Random(202608091)
E=['fs.read','fs.write','net.connect','db.read','db.write','proc.spawn']
T=['I32','I64','Bool','String','Unit']

def H(tag,*x):
    return hashlib.sha256((tag+'|'+json.dumps(x,sort_keys=True,separators=(',',':'))).encode()).hexdigest()

def closure(call_edges,direct):
    eff={f:set(direct[f]) for f in direct}
    changed=True
    while changed:
        changed=False
        for f,cs in call_edges.items():
            n=set(eff[f])
            for c in cs:n |= eff[c]
            if n!=eff[f]: eff[f]=n;changed=True
    return {f:tuple(sorted(v)) for f,v in eff.items()}

# Random recursive graphs; compare layered binding vs effect-in-binding and declared effect contracts.
NGRAPHS=2000; NF=20
stats=defaultdict(int)
for g in range(NGRAPHS):
    names=[f'f{i}' for i in range(NF)]
    direct={f:set(R.sample(E,R.randrange(0,3))) for f in names}
    edges={f:set(R.sample(names,R.randrange(0,4))) for f in names}
    inf=closure(edges,direct)
    # Declared bound is either exact current closure or one conservative superset.
    declared={}
    for f in names:
        s=set(inf[f])
        if R.random()<0.5:
            s |= set(R.sample(E,R.randrange(0,2)))
        declared[f]=tuple(sorted(s))
    bind={f:H('bind','m',f) for f in names}
    ctype={f:H('contract_type',(('I32',),'I32'),declared[f]) for f in names}
    # mutate one direct effect, recompute closure
    target=R.choice(names); e=R.choice(E)
    direct2={f:set(v) for f,v in direct.items()}
    if e in direct2[target]: direct2[target].remove(e)
    else: direct2[target].add(e)
    inf2=closure(edges,direct2)
    for f in names:
        if bind[f]==H('bind','m',f): stats['binding_stable']+=1
        bad1=H('bad_bind','m',f,inf[f]); bad2=H('bad_bind','m',f,inf2[f])
        if bad1!=bad2: stats['bad_effect_binding_churn']+=1
        # current declared contract stays stable until source contract is edited
        if ctype[f]==H('contract_type',(('I32',),'I32'),declared[f]): stats['declared_contract_type_stable']+=1
        if set(inf2[f]).issubset(set(declared[f])): stats['mutated_effect_within_declared_bound']+=1
        else: stats['mutated_effect_exceeds_declared_bound_reject']+=1

# Phase dependency graph: declared effects may participate in type checking; inferred effects may not be prerequisite for lexical binding.
def cycle(edges):
    ns=set(edges)
    for vs in edges.values():ns|=set(vs)
    indeg={n:0 for n in ns}
    for u,vs in edges.items():
        for v in vs: indeg[v]+=1
    q=deque([n for n,d in indeg.items() if d==0]);seen=0
    while q:
        u=q.popleft();seen+=1
        for v in edges.get(u,[]):
            indeg[v]-=1
            if indeg[v]==0:q.append(v)
    return seen!=len(ns)
layered={
 'Parse':['BindingKey','ValueType','DeclaredEffectContract'],
 'BindingKey':['Resolve'],
 'Resolve':['CallGraph'],
 'ValueType':['TypeCheck'],
 'DeclaredEffectContract':['TypeCheck'],
 'CallGraph':['InferEffectSummary'],
 'TypeCheck':['InferEffectSummary'],
 'InferEffectSummary':['EffectConformanceCheck'],
 'DeclaredEffectContract':['EffectConformanceCheck'],
 'EffectConformanceCheck':['Lowering'],
}
bad={k:list(v) for k,v in layered.items()};bad['InferEffectSummary'].append('BindingKey')

print(json.dumps({
 'seed':202608091,
 'graphs':NGRAPHS,
 'functions_per_graph':NF,
 'observations':dict(stats),
 'layered_phase_cycle':cycle(layered),
 'effect_in_binding_phase_cycle':cycle(bad),
 'interpretation':{
  'binding':'module/scope + exact symbol identity only',
  'value_type':'params + result',
  'declared_effect_contract':'may be part of callable contract/type if known before body effect closure',
  'inferred_effect_summary':'analysis output checked against declared contract; never runtime authority and never lexical binding key',
  'runtime_capability':'fresh invocation context, separate from all static IDs'
 }
},indent=2,sort_keys=True))
