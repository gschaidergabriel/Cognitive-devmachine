#!/usr/bin/env python3
import json, hashlib, random
random.seed(20260809)
def cj(o): return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def sh(o): return hashlib.sha256(cj(o).encode()).hexdigest()
def canon(x):
    if isinstance(x,dict):
        if x.get("_type")=="Set":
            es=[canon(v) for v in x["items"]]; u={cj(e):e for e in es}; return {"_type":"Set","items":[u[k] for k in sorted(u)]}
        if x.get("_type")=="Ordered": return {"_type":"Ordered","items":[canon(v) for v in x["items"]]}
        return {k:canon(v) for k,v in sorted(x.items()) if k not in {"surface","source_text","provenance_instance"}}
    if isinstance(x,list): return [canon(v) for v in x]
    return x
def sem(x): return sh(canon(x))
def contract(x): return sh(x)
KNOWN={"never_implies","may_reference","includes","returns","lifecycle","cannot_authorize","requires","owns"}
def rel(r,l,x,t=None,s=None,p=None):
    if r not in KNOWN: raise ValueError("unknown RelationId")
    if t=="Set": x={"_type":"Set","items":x}
    elif t=="Ordered": x={"_type":"Ordered","items":x}
    return {"kind":"Relation","relation_id":r,"lhs":l,"rhs":x,"surface":s,"provenance_instance":p}
a=rel("never_implies","Delta","epistemic_upgrade",s="Delta never_implies epistemic_upgrade",p="A")
b=rel("never_implies","Delta","epistemic_upgrade",s='relation("never_implies",Delta,epistemic_upgrade)',p="B")
forbidden=["filesystem_search","api_selection","json_arguments","goal_list_recall"]
bs=rel("includes","NativeCognitionTask.forbidden_burden",forbidden,"Set"); hs=sem(bs); sp=0
for i in range(20000):
    v=forbidden[:]; random.shuffle(v)
    if i%2==0: v+=random.sample(v,k=random.randint(1,3)); random.shuffle(v)
    sp += sem(rel("includes","NativeCognitionTask.forbidden_burden",v,"Set"))==hs
life=["REQUESTED","AUTHORIZED","CLAIMED","EXECUTED","VERIFIED","DONE"]
bo=rel("lifecycle","external_effect",life,"Ordered"); ho=sem(bo); oc=0
for _ in range(20000):
    v=life[:]; i,j=random.sample(range(len(v)),2); v[i],v[j]=v[j],v[i]; oc += sem(rel("lifecycle","external_effect",v,"Ordered"))!=ho
def blind(x):
    if isinstance(x,dict): return {k:blind(v) for k,v in sorted(x.items()) if k not in {"surface","source_text","provenance_instance"}}
    if isinstance(x,list): return sorted([blind(v) for v in x],key=cj)
    return x
blind_collision=sh(blind(rel("lifecycle","external_effect",life)))==sh(blind(rel("lifecycle","external_effect",list(reversed(life)))))
members=[{"role":"source","logical_id":"A","ordinal":0},{"role":"context","logical_id":"B","ordinal":1},{"role":"target","logical_id":"C","ordinal":2}]
r1={"kind":"HyperRelation","relation_id":"couples","members":{"_type":"Ordered","items":members}}
r2={"kind":"HyperRelation","relation_id":"couples","members":{"_type":"Ordered","items":[members[1],members[0],members[2]]}}
mc=0
for i in range(50000):
    r=random.choice(sorted(KNOWN)); l=f"L{random.randint(0,999)}"; x=f"R{random.randint(0,999)}"; mc += sem(rel(r,l,x))!=sem(rel(r,l,x+"x"))
print(json.dumps({"surface_equivalence_same_semantic_hash":sem(a)==sem(b),"surface_instances_distinct_contract_hash":contract(a)!=contract(b),"set_trials":20000,"set_semantic_hash_preserved":sp,"ordered_trials":20000,"ordered_semantic_hash_changed":oc,"schema_blind_sorting_collides_ordered_lifecycle":blind_collision,"typed_canonicalization_distinguishes_ordered_lifecycle":sem(bo)!=sem(rel("lifecycle","external_effect",list(reversed(life)),"Ordered")),"hyperrelation_role_order_changes_semantic_hash":sem(r1)!=sem(r2),"semantic_mutation_trials":50000,"semantic_mutation_hash_changed":mc},sort_keys=True))
