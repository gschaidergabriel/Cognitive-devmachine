import hashlib, json, random
from dataclasses import dataclass
from collections import defaultdict, deque

SEED = 20260809
R = random.Random(SEED)
TYPES = ['I32','I64','F32','F64','Bool','String','Bytes','Unit']
EFFECTS = ['fs.read','fs.write','net.connect','db.read','db.write','proc.spawn']

def H(tag, *parts):
    s = tag + '\x1f' + '\x1f'.join(json.dumps(p, sort_keys=True, separators=(',',':')) for p in parts)
    return hashlib.sha256(s.encode()).hexdigest()

@dataclass(frozen=True)
class Decl:
    module: str
    name: str
    params: tuple
    ret: str
    body: str
    inferred_effects: tuple
    abi: str = 'clay'
    provenance: str = 'src'

    def binding_key(self):
        return H('clay.binding.v1', self.module, self.name)
    def type_id(self):
        return H('clay.fntype.v1', self.params, self.ret)
    def definition_id(self):
        return H('clay.definition.v1', self.binding_key(), self.type_id(), self.body)
    def contract_id(self):
        return H('clay.contract.v1', self.definition_id(), self.abi, self.provenance)
    def monolithic_effect_binding_key(self):
        return H('bad.binding.effect.v0', self.module, self.name, self.params, self.ret, self.inferred_effects)

# Property 1: mutation partitioning
N = 50000
p = defaultdict(int)
for i in range(N):
    d = Decl(f'm{R.randrange(100)}', f'f{R.randrange(1000000)}', tuple(R.choice(TYPES) for _ in range(R.randrange(0,5))), R.choice(TYPES), f'body:{R.getrandbits(96)}', tuple(sorted(R.sample(EFFECTS, R.randrange(0,4)))))
    mut = R.choice(['body','effects','abi','provenance','signature','rename'])
    kw = d.__dict__.copy()
    if mut=='body': kw['body'] = d.body + ':mut'
    elif mut=='effects': kw['inferred_effects'] = tuple(sorted(set(d.inferred_effects) ^ {R.choice(EFFECTS)}))
    elif mut=='abi': kw['abi'] = 'c' if d.abi!='c' else 'clay'
    elif mut=='provenance': kw['provenance'] = d.provenance + ':mut'
    elif mut=='signature':
        params=list(d.params)
        if params: params[0] = R.choice([t for t in TYPES if t != params[0]])
        else: params=['I32']
        kw['params']=tuple(params)
    elif mut=='rename': kw['name'] = d.name + '_x'
    d2=Decl(**kw)
    for label, a,b in [
        ('binding', d.binding_key(), d2.binding_key()),
        ('type', d.type_id(), d2.type_id()),
        ('definition', d.definition_id(), d2.definition_id()),
        ('contract', d.contract_id(), d2.contract_id()),
        ('bad_effect_binding', d.monolithic_effect_binding_key(), d2.monolithic_effect_binding_key()),
    ]:
        p[f'{mut}:{label}:changed' if a!=b else f'{mut}:{label}:stable'] += 1

# Property 2: resolver behavior
class UniqueNameResolver:
    def __init__(self): self.tab={}
    def add(self,d):
        k=(d.module,d.name)
        if k in self.tab: return 'DUPLICATE_NAME'
        self.tab[k]=d; return 'OK'
    def resolve(self,module,name,argtypes):
        d=self.tab.get((module,name))
        if not d: return 'MISSING'
        if tuple(argtypes)!=d.params: return 'TYPE_MISMATCH'
        return d.definition_id()

class OverloadResolver:
    def __init__(self): self.tab=defaultdict(dict)
    def add(self,d):
        k=(d.module,d.name); s=(d.params,d.ret)
        if s in self.tab[k]: return 'DUPLICATE_SIGNATURE'
        self.tab[k][s]=d; return 'OK'
    def resolve_exact(self,module,name,argtypes):
        cand=[d for d in self.tab.get((module,name),{}).values() if d.params==tuple(argtypes)]
        if len(cand)==1:return cand[0].definition_id()
        if len(cand)==0:return 'NO_EXACT_MATCH'
        return 'AMBIGUOUS'
    def resolve_partial(self,module,name,argtypes):
        cand=[]
        for d in self.tab.get((module,name),{}).values():
            if len(d.params)!=len(argtypes): continue
            if all(a=='?' or a==b for a,b in zip(argtypes,d.params)): cand.append(d)
        if len(cand)==1:return cand[0].definition_id()
        if len(cand)==0:return 'NO_MATCH'
        return 'AMBIGUOUS'

res_counts=defaultdict(int)
for i in range(20000):
    module=f'm{i%37}'; name=f'op{i}'
    ar=R.randrange(1,4)
    sig1=tuple(R.choice(TYPES) for _ in range(ar))
    # ensure second signature differs in exactly one position
    j=R.randrange(ar); sig2=list(sig1); sig2[j]=R.choice([t for t in TYPES if t!=sig2[j]]); sig2=tuple(sig2)
    d1=Decl(module,name,sig1,R.choice(TYPES),f'b1:{i}',())
    d2=Decl(module,name,sig2,R.choice(TYPES),f'b2:{i}',())
    u=UniqueNameResolver(); o=OverloadResolver()
    res_counts['unique_add1_'+u.add(d1)] += 1
    res_counts['unique_add2_'+u.add(d2)] += 1
    res_counts['over_add1_'+o.add(d1)] += 1
    res_counts['over_add2_'+o.add(d2)] += 1
    if o.resolve_exact(module,name,sig1)==d1.definition_id(): res_counts['over_exact_resolve_ok'] += 1
    partial=list(sig1); partial[j]='?'
    r=o.resolve_partial(module,name,partial)
    res_counts['over_partial_'+('AMBIGUOUS' if r=='AMBIGUOUS' else 'OTHER')] += 1

# Property 3: dependency cycles in phase ordering
def has_cycle(edges):
    nodes=set(edges)
    for vs in edges.values():nodes.update(vs)
    indeg={n:0 for n in nodes}
    for u,vs in edges.items():
        for v in vs: indeg[v]+=1
    q=deque([n for n,d in indeg.items() if d==0]); seen=0
    while q:
        u=q.popleft(); seen+=1
        for v in edges.get(u,[]):
            indeg[v]-=1
            if indeg[v]==0:q.append(v)
    return seen != len(nodes)

# edge A->B means B depends on A / A must exist first
layered_edges={
 'Parse':['BindingKey','TypeId'],
 'BindingKey':['Resolve'],
 'Resolve':['CallGraph','TypeCheck'],
 'TypeId':['TypeCheck'],
 'CallGraph':['EffectClosure'],
 'TypeCheck':['EffectClosure'],
 'EffectClosure':['Lowering'],
 'Lowering':['RuntimeInvoke'],
 'RuntimeCapabilityContext':['RuntimeInvoke'],
}
# Bad design: binding key includes inferred EffectClosure, which itself needs resolved callgraph
bad_edges={k:list(v) for k,v in layered_edges.items()}
bad_edges.setdefault('EffectClosure',[]).append('BindingKey')

# Property 4: call target identity should remain stable under inferred-effect changes
M=50000
stable_layered=0; stable_bad=0
for i in range(M):
    d=Decl('m',f'f{i}',('I32',),'I32',f'b{i}',tuple(sorted(R.sample(EFFECTS,R.randrange(0,4)))))
    e=set(d.inferred_effects); e.symmetric_difference_update({R.choice(EFFECTS)})
    d2=Decl(d.module,d.name,d.params,d.ret,d.body,tuple(sorted(e)),d.abi,d.provenance)
    stable_layered += (d.binding_key()==d2.binding_key())
    stable_bad += (d.monolithic_effect_binding_key()==d2.monolithic_effect_binding_key())

# Property 5: collision sanity on generated layered IDs.
# Important: repeated identical preimages (especially common FunctionTypeIds) are NOT hash collisions.
seen = {}
true_collisions = 0
repeated_same_preimage = 0
for i in range(100000):
    d=Decl(f'm{R.randrange(1000)}',f'f{R.randrange(10**9)}',tuple(R.choice(TYPES) for _ in range(R.randrange(0,5))),R.choice(TYPES),f'b:{R.getrandbits(128)}',())
    vals=[
      ('binding',d.binding_key(),(d.module,d.name)),
      ('type',d.type_id(),(d.params,d.ret)),
      ('definition',d.definition_id(),(d.binding_key(),d.type_id(),d.body)),
      ('contract',d.contract_id(),(d.definition_id(),d.abi,d.provenance)),
    ]
    for kind,h,pre in vals:
        key=(kind,h)
        if key in seen:
            if seen[key] != pre: true_collisions += 1
            else: repeated_same_preimage += 1
        else:
            seen[key]=pre

out={
 'seed':SEED,
 'mutation_cases':N,
 'mutation_partition_counts':dict(sorted(p.items())),
 'resolver_cases':20000,
 'resolver_counts':dict(sorted(res_counts.items())),
 'phase_dependency':{
   'layered_has_cycle':has_cycle(layered_edges),
   'effect_in_binding_has_cycle':has_cycle(bad_edges),
   'layered_edges':layered_edges,
   'bad_extra_edge':'EffectClosure -> BindingKey'
 },
 'effect_mutation_binding_stability':{
   'cases':M,'layered_stable':stable_layered,'effect_in_binding_stable':stable_bad
 },
 'hash_sanity':{'unique_hash_slots':len(seen),'true_collisions_observed':true_collisions,'repeated_same_preimage':repeated_same_preimage},
 'method_negative_result':'FIRST_COLLISION_COUNTER_WAS_INVALID_BECAUSE_IT_COUNTED_REPEAT_IDENTICAL_PREIMAGES_AS_COLLISIONS; corrected by retaining hash->preimage map.',
}
print(json.dumps(out,indent=2,sort_keys=True))
