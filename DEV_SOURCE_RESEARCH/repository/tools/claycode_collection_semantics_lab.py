#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, random, time
from collections import Counter
from decimal import Decimal, InvalidOperation

VERSION='claycode-collection-lab-0.3-cc11'
KINDS={'SET','ORDERED','MULTISET','WEIGHTED'}
class CompileError(ValueError): pass

def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def hh(tag,o): return hashlib.sha256((tag+':'+canon(o)).encode()).hexdigest()
def dec(s):
    try: d=Decimal(str(s))
    except InvalidOperation as e: raise CompileError(f'invalid weight {s!r}') from e
    if not d.is_finite(): raise CompileError('non-finite weight')
    s=format(d.normalize(),'f')
    if '.' in s: s=s.rstrip('0').rstrip('.')
    return '0' if s in {'','-0'} else s

def collection(kind, vals):
    if kind not in KINDS: raise CompileError('unknown collection kind')
    if kind=='SET': items=sorted(set(map(str,vals)))
    elif kind=='ORDERED': items=list(map(str,vals))
    elif kind=='MULTISET':
        c=Counter(map(str,vals)); items=[[k,c[k]] for k in sorted(c)]
    else:
        d={}
        for raw in vals:
            if not isinstance(raw,(tuple,list)) or len(raw)!=2: raise CompileError('weighted entry')
            k,w=str(raw[0]),dec(raw[1])
            if k in d: raise CompileError('duplicate weighted key')
            d[k]=w
        items=[[k,d[k]] for k in sorted(d)]
    return {'kind':kind,'items':items}

def semantic_obj(fields):
    return {'schema':'ClayCode.CollectionSemantics/0.3','fields':fields}
def semantic_hash(fields): return hh('clay-semantic:v3',semantic_obj(fields))
def contract_hash(sem_hash,proposal_hash,adequacy_hash):
    return hh('clay-contract:v3',{'semantic_hash':sem_hash,'proposal_hash':proposal_hash,'adequacy_hash':adequacy_hash})
def view_hash(view): return hh('clay-view:v3',view)
def receipt(sem_hash,con_hash,view):
    return {'type':'ProjectionReceiptV3TripleBound','semantic_hash':sem_hash,'contract_hash':con_hash,'view_hash':view_hash(view),'compiler':VERSION}
def verify_receipt(sem_hash,con_hash,view,r):
    return r==receipt(sem_hash,con_hash,view)

def source_case(set_items=None,ordered=None,multi=None,weighted=None,source_nonce='base'):
    fields={
      'requirements':collection('SET',set_items or ['truth','provenance']),
      'steps':collection('ORDERED',ordered or ['read','compile','emit']),
      'observations':collection('MULTISET',multi or ['stale','stale','ambiguous']),
      'preferences':collection('WEIGHTED',weighted or [('latency','0.7'),('tokens','0.3')]),
    }
    sh=semantic_hash(fields)
    ph=hh('proposal:v3',{'nonce':source_nonce,'raw':{'set':set_items,'ordered':ordered,'multi':multi,'weighted':weighted}})
    ah=hh('adequacy:v3',{'proposal_hash':ph,'status':'VERIFIED_FOR_LAB'})
    ch=contract_hash(sh,ph,ah)
    view={'requirements':fields['requirements']['items'],'steps':fields['steps']['items']}
    return fields,sh,ch,view,receipt(sh,ch,view)

def deterministic_checks():
    checks={}
    checks['set_reorder']=collection('SET',['b','a'])==collection('SET',['a','b'])
    checks['set_duplicate']=collection('SET',['a','b'])==collection('SET',['a','b','b'])
    checks['ordered_reorder']=collection('ORDERED',['a','b'])!=collection('ORDERED',['b','a'])
    checks['multiset_reorder']=collection('MULTISET',['a','b','b'])==collection('MULTISET',['b','a','b'])
    checks['multiset_duplicate']=collection('MULTISET',['a','b'])!=collection('MULTISET',['a','b','b'])
    checks['weighted_reorder_normalize']=collection('WEIGHTED',[('a','.700'),('b','.30')])==collection('WEIGHTED',[('b','0.3'),('a','0.7')])
    checks['weighted_value']=collection('WEIGHTED',[('a','.7')])!=collection('WEIGHTED',[('a','.6')])
    checks['cross_kind_identity']=collection('SET',['a','b'])!=collection('ORDERED',['a','b'])
    try: collection('WEIGHTED',[('a','.7'),('a','.7')]); checks['weighted_dup_reject']=False
    except CompileError: checks['weighted_dup_reject']=True
    return checks

def identity_checks():
    _,s0,c0,v0,r0=source_case(source_nonce='p0')
    _,sr,cr,_,_=source_case(set_items=['provenance','truth'],source_nonce='p1')
    _,sd,cd,_,_=source_case(set_items=['truth','provenance','provenance'],source_nonce='p2')
    _,so,co,_,_=source_case(ordered=['compile','read','emit'],source_nonce='p3')
    _,sm,cm,_,_=source_case(multi=['stale','ambiguous'],source_nonce='p4')
    mutated=dict(v0); mutated['steps']=['read','emit','compile']
    return {
      'set_reorder_semantic_equal':s0==sr,
      'set_reorder_contract_distinct':c0!=cr,
      'set_duplicate_semantic_equal':s0==sd,
      'set_duplicate_contract_distinct':c0!=cd,
      'ordered_change_semantic_distinct':s0!=so,
      'multiset_multiplicity_change_semantic_distinct':s0!=sm,
      'view_mutation_rejected':not verify_receipt(s0,c0,mutated,r0),
      'base_receipt_valid':verify_receipt(s0,c0,v0,r0),
    }

def fuzz(n=100000,seed=17731):
    rng=random.Random(seed); atoms=[f'x{i}' for i in range(25)]; failures=[]; tested=Counter()
    def ck(name,ok,detail=None):
        tested[name]+=1
        if not ok and len(failures)<25: failures.append({'class':name,'detail':detail})
    for _ in range(n):
        kind=rng.choice(['SET','ORDERED','MULTISET'])
        xs=[rng.choice(atoms) for _ in range(rng.randint(0,12))]
        base=collection(kind,xs); ys=list(xs); rng.shuffle(ys)
        if kind=='ORDERED':
            if ys!=xs: ck('ordered_permutation_changes',base!=collection(kind,ys))
        else: ck(kind.lower()+'_permutation_invariant',base==collection(kind,ys))
        if xs:
            zs=xs+[rng.choice(xs)]
            ck(kind.lower()+'_duplicate_rule',(base==collection(kind,zs))==(kind=='SET'))
    return {'status':'PASS' if not failures else 'FAIL','iterations':n,'seed':seed,'checks':dict(tested),'failure_count':len(failures),'failures':failures}

def bench(rounds=50000):
    fields,sh,ch,view,_=source_case()
    t=time.perf_counter()
    for _ in range(rounds):
        _=semantic_hash(fields); _=contract_hash(sh,'p','a'); _=view_hash(view)
    cold=time.perf_counter()-t
    t=time.perf_counter()
    for _ in range(rounds): _=(sh,ch,view_hash(view))
    hot=time.perf_counter()-t
    dual={'contract_hash':ch,'view_hash':view_hash(view)}; triple=receipt(sh,ch,view)
    return {'rounds':rounds,'cold_us':cold/rounds*1e6,'hot_us':hot/rounds*1e6,'dual_json_bytes':len(canon(dual).encode()),'triple_json_bytes':len(canon(triple).encode()),'extra_json_bytes':len(canon(triple).encode())-len(canon(dual).encode()),'note':'CPython/E2B proxy; semantic+contract hashes should be commit-time cached IDs'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--iterations',type=int,default=100000); a=ap.parse_args()
    d=deterministic_checks(); i=identity_checks(); f=fuzz(max(100,min(a.iterations,500000))); b=bench()
    ok=all(d.values()) and all(i.values()) and f['status']=='PASS'
    print(json.dumps({'status':'PASS' if ok else 'FAIL','version':VERSION,'deterministic':d,'identity':i,'fuzz':f,'benchmark':b},sort_keys=True))
    raise SystemExit(0 if ok else 1)
if __name__=='__main__': main()
