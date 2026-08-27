#!/usr/bin/env python3
import hashlib,json,random
SEED=22091
N=100000

def h(tag,obj):
    return hashlib.sha256((tag+':'+json.dumps(obj,sort_keys=True,separators=(',',':'))).encode()).hexdigest()

def set_items(xs): return sorted(set(xs))
def ordered_items(xs): return list(xs)

def run():
    rng=random.Random(SEED); atoms=['a','b','c','d']; alias=0; nontrivial=0; typed_alias=0
    examples=[]
    for _ in range(N):
        xs=[rng.choice(atoms) for _ in range(rng.randint(0,8))]
        s=set_items(xs); o=ordered_items(xs)
        hu_s=h('untyped',s); hu_o=h('untyped',o)
        ht_s=h('typed',{'kind':'SET','items':s}); ht_o=h('typed',{'kind':'ORDERED','items':o})
        if hu_s==hu_o:
            alias+=1
            if len(xs)>1: nontrivial+=1
            if len(examples)<8: examples.append({'source':xs,'canonical_set':s,'ordered':o})
        if ht_s==ht_o: typed_alias+=1
    ok=typed_alias==0 and alias>0
    return {'status':'PASS' if ok else 'FAIL','seed':SEED,'iterations':N,'untyped_cross_kind_aliases':alias,'untyped_alias_rate':alias/N,'nontrivial_aliases':nontrivial,'typed_cross_kind_aliases':typed_alias,'examples':examples,'inference':'collection kind must participate in semantic identity/hash'}
if __name__=='__main__': print(json.dumps(run(),sort_keys=True))
