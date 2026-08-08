#!/usr/bin/env python3
import json, random, sqlite3, time
from collections import Counter

SEED=44119
KINDS=('SET','ORDERED','MULTISET')

def reference(kind, xs):
    if kind=='SET': return sorted(set(xs))
    if kind=='ORDERED': return list(xs)
    if kind=='MULTISET':
        c=Counter(xs); return [[k,c[k]] for k in sorted(c)]
    raise ValueError(kind)

def sql_for(kind):
    if kind=='SET': return 'select distinct value from t order by value'
    if kind=='ORDERED': return 'select value from t order by pos'
    if kind=='MULTISET': return 'select value,count(*) from t group by value order by value'
    raise ValueError(kind)

def decode(kind, rows):
    if kind in {'SET','ORDERED'}: return [r[0] for r in rows]
    return [[r[0],r[1]] for r in rows]

def weighted(rows):
    seen={}
    for key,weight in rows:
        if key in seen: raise ValueError('duplicate weighted key')
        seen[key]=weight
    return sorted(seen.items())

def run(n=30000):
    rng=random.Random(SEED); atoms=['a','b','c','d','e']
    con=sqlite3.connect(':memory:'); con.execute('create table t(pos integer,value text,weight text)')
    mismatch=wrong_distinct=wrong_bag=0
    by={k:{'n':0,'correct_mismatch':0,'distinct_mismatch':0,'bag_mismatch':0} for k in KINDS}
    t0=time.perf_counter()
    for _ in range(n):
        kind=rng.choice(KINDS); xs=[rng.choice(atoms) for _ in range(rng.randint(0,10))]
        con.execute('delete from t'); con.executemany('insert into t(pos,value,weight) values(?,?,NULL)',enumerate(xs))
        expected=reference(kind,xs)
        got=decode(kind,con.execute(sql_for(kind)).fetchall())
        ok=got==expected; mismatch+=not ok; by[kind]['n']+=1; by[kind]['correct_mismatch']+=not ok
        naive_distinct=[r[0] for r in con.execute('select distinct value from t order by value')]
        d_ok=naive_distinct==expected; wrong_distinct+=not d_ok; by[kind]['distinct_mismatch']+=not d_ok
        naive_bag=[r[0] for r in con.execute('select value from t order by pos')]
        b_ok=naive_bag==expected; wrong_bag+=not b_ok; by[kind]['bag_mismatch']+=not b_ok
    weighted_reject=False
    try: weighted([('latency','0.7'),('latency','0.3')])
    except ValueError: weighted_reject=True
    return {'status':'PASS' if mismatch==0 and weighted_reject else 'FAIL','seed':SEED,'operations':n,'correct_lowering_mismatches':mismatch,'type_erased_distinct_mismatches':wrong_distinct,'type_erased_bag_mismatches':wrong_bag,'by_kind':by,'weighted_duplicate_key_rejected':weighted_reject,'elapsed_s':time.perf_counter()-t0}

if __name__=='__main__': print(json.dumps(run(),sort_keys=True))
