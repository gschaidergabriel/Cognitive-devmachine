#!/usr/bin/env python3
"""Compare canonical flat root, rejected sparse tree, and compressed Merkle-treap shadow."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, random, sqlite3, statistics, tempfile, time
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger, cjson, h
from research_entity.experiments.unifieddb_sparse_merkle.state_sparse_merkle_shadow import SparseMerkleStateShadow
from research_entity.experiments.unifieddb_sparse_merkle.state_merkle_treap_shadow import MerkleTreapStateShadow

def ms(fn,reps):
    xs=[]; ret=None
    for _ in range(reps):
        t=time.perf_counter_ns(); ret=fn(); xs.append((time.perf_counter_ns()-t)/1e6)
    xs.sort(); return ret,{'n':len(xs),'p50_ms':statistics.median(xs),'p95_ms':xs[int(.95*(len(xs)-1))],'min_ms':xs[0],'max_ms':xs[-1]}

def us(fn,reps):
    xs=[]
    for _ in range(reps):
        t=time.perf_counter_ns(); fn(); xs.append((time.perf_counter_ns()-t)/1e3)
    xs.sort(); return {'n':len(xs),'p50_us':statistics.median(xs),'p95_us':xs[int(.95*(len(xs)-1))],'min_us':xs[0],'max_us':xs[-1]}

def row_commit(domain,key,value_json,epistemic,status,domain_epoch,semantic_hash):
    # Shadow commitment includes every canonical materialized-row field, including the
    # per-row domain_epoch that StateLedger.semantic_hash alone intentionally omits.
    payload=cjson({'domain':domain,'key':key,'value_json':value_json,'epistemic':epistemic,'status':status,'domain_epoch':int(domain_epoch),'semantic_hash':semantic_hash})
    return hashlib.sha256(('CLAY_AUTH_ROW_V1\0'+payload).encode()).hexdigest()

def seed(l,n,domains=20):
    l.conn.execute('BEGIN IMMEDIATE')
    batch=[]
    for d in range(domains): l.conn.execute('INSERT OR REPLACE INTO domain_epochs VALUES(?,?)',(f'd{d:02d}',n//domains+1))
    for i in range(n):
        domain=f'd{i%domains:02d}'; key=f'k{i:08d}'; value={'i':i,'text':'Grüße-'+str(i),'tags':{'$kind':'set','items':[i%7,i%13,i%7]}}; vj=cjson(value); de=i//domains+1
        sh=h({'domain':domain,'key':key,'value':value,'epistemic':'KNOWN','status':'CURRENT'}); batch.append((domain,key,vj,'KNOWN','CURRENT',de,sh))
    l.conn.executemany('INSERT INTO state VALUES(?,?,?,?,?,?,?)',batch); l._set('global_epoch',n+1); l.conn.commit()

def raw_rows(l):
    return list(l.conn.execute('SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash FROM state ORDER BY domain,k'))

def treap_rows(rows):
    return [(r[0],r[1],row_commit(*r)) for r in rows]

def one(n,reps,updates):
    with tempfile.TemporaryDirectory() as td:
        l=StateLedger(os.path.join(td,'x.sqlite')); seed(l,n); rows=raw_rows(l)
        flat_hash,flat=ms(l._roots,reps)
        t=MerkleTreapStateShadow(); treap_root,build=ms(lambda:t.rebuild(treap_rows(rows)),reps)
        # Rebuild object one final time after repeated benchmark to make update state explicit.
        t.rebuild(treap_rows(rows)); current={(r[0],r[1]):list(r) for r in rows}; rng=random.Random(20260810+n)
        upd=[]; rebuild_checks=0
        for i in range(updates):
            dk=rng.choice(list(current)); r=current[dk]; new_value=cjson({'iteration':i,'old':r[2],'nonce':rng.randrange(1_000_000)}); r[2]=new_value; r[5]=int(r[5])+1; r[6]=hashlib.sha256((r[0]+'|'+r[1]+'|'+new_value+'|'+r[3]+'|'+r[4]).encode()).hexdigest()
            rc=row_commit(*r); start=time.perf_counter_ns(); t.update_hash(domain=r[0],key=r[1],row_hash_hex=rc); upd.append((time.perf_counter_ns()-start)/1e3)
            if i in {0,updates//2,updates-1}:
                chk=MerkleTreapStateShadow(); chk.rebuild((x[0],x[1],row_commit(*x)) for x in current.values()); assert chk.map_root()==t.map_root(); rebuild_checks+=1
        upd.sort(); proof=t.proof(domain=current[dk][0],key=current[dk][1]); assert MerkleTreapStateShadow.verify(proof)
        l.close()
        return {'state_rows':n,'canonical_flat_root':flat,'treap_full_rebuild':build,'treap_update':{'n':len(upd),'p50_us':statistics.median(upd),'p95_us':upd[int(.95*(len(upd)-1))]},'treap_nodes':t.node_count(),'incremental_vs_rebuild_checks':rebuild_checks,'proof_verified':True,'flat_semantic_state_hash':flat_hash[0],'shadow_map_root':treap_root.hex(),'p50_flat_root_vs_incremental_update_ratio':flat['p50_ms']*1000/statistics.median(upd)}

def sparse_shadow(n=1000):
    s=SparseMerkleStateShadow(); start=time.perf_counter()
    for i in range(n): s.update_hash(domain='d',key=f'k{i}',row_hash_hex=hashlib.sha256(f'r{i}'.encode()).hexdigest())
    return {'rows':n,'stored_nodes':len(s.nodes),'nodes_per_row':len(s.nodes)/n,'build_ms':(time.perf_counter()-start)*1000,'decision':'REJECT_MEMORY_AMPLIFICATION'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--sizes',default='1000,10000,50000'); ap.add_argument('--reps',type=int,default=3); ap.add_argument('--updates',type=int,default=120); ap.add_argument('--output'); a=ap.parse_args()
    out={'schema':'clay.authenticated_state_root_shadow.v1','scope':'synthetic implementation benchmark; canonical StateLedger root unchanged','environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.platform(),'machine':platform.machine()},'sparse_negative':sparse_shadow(),'treap':[one(int(n),a.reps,a.updates) for n in a.sizes.split(',') if n.strip()],'promotion':'SHADOW_ONLY'}
    text=json.dumps(out,indent=2,sort_keys=True); print(text)
    if a.output: Path(a.output).write_text(text+'\n')
if __name__=='__main__':main()
