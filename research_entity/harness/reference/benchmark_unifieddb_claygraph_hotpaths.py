from __future__ import annotations
import argparse, json, math, os, platform, random, sqlite3, statistics, sys, time
from pathlib import Path

from .state_ledger import StateLedger
from .unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane

ROOT=Path(__file__).resolve().parents[3]
GRAPH_BASE=ROOT/'research_entity/runtime/RAE_CLAYGRAPH_SCHEMA.sql'
GRAPH_V3=ROOT/'research_entity/runtime/RAE_CLAYGRAPH_V3_CURRENT_PROJECTIONS.sql'

def quantile(xs,q):
    ys=sorted(xs); p=(len(ys)-1)*q; a=math.floor(p); b=math.ceil(p)
    return ys[a] if a==b else ys[a]*(b-p)+ys[b]*(p-a)

def stats_us(xs):
    return {'n':len(xs),'p50_us':quantile(xs,.5),'p95_us':quantile(xs,.95),'p99_us':quantile(xs,.99),'min_us':min(xs),'max_us':max(xs),'mean_us':statistics.fmean(xs)}

def timed(fn,reps):
    out=[]
    for _ in range(reps):
        t=time.perf_counter_ns(); fn(); out.append((time.perf_counter_ns()-t)/1000)
    return stats_us(out)

def bench_udb(rows,reps):
    ledger=StateLedger(); plane=UnifiedDBQueryPlane(ledger)
    ops=[]
    epis=('KNOWN','UNKNOWN','CONFLICT')
    for i in range(rows):
        ops.append({'op':'SET','domain':f'd{i%20:02d}','key':f'k{i:06d}','value':{'i':i},'epistemic':epis[i%3],'status':'SUPERSEDED' if i%11==0 else 'CURRENT'})
    plane.transact(event_id='bench-seed',idem='bench-seed',base_epoch=0,event_type='BENCH_SEED',writer='benchmark',ops=ops)
    rng=random.Random(731)
    specs=[]
    for i in range(reps):
        mode=i%4
        if mode==0: spec=QuerySpec(f'q{i}',domains=(f'd{rng.randrange(20):02d}',),basis_epoch=ledger.epoch,limit=32)
        elif mode==1: spec=QuerySpec(f'q{i}',keys=(f'k{rng.randrange(rows):06d}',),basis_epoch=ledger.epoch,limit=32)
        elif mode==2: spec=QuerySpec(f'q{i}',domains=(f'd{rng.randrange(20):02d}',),epistemic=('KNOWN',),basis_epoch=ledger.epoch,limit=32)
        else: spec=QuerySpec(f'q{i}',domains=(f'd{rng.randrange(20):02d}',),keys=(f'k{rng.randrange(rows):06d}',),basis_epoch=ledger.epoch,limit=32)
        specs.append(spec)
    mismatches=[]; legacy=[]; fast=[]
    for spec in specs:
        t=time.perf_counter_ns(); a=plane._query_rows_legacy(spec); legacy.append((time.perf_counter_ns()-t)/1000)
        t=time.perf_counter_ns(); b=plane._query_rows_fast(spec); fast.append((time.perf_counter_ns()-t)/1000)
        if a!=b: mismatches.append(spec.query_id)
    result={'rows':rows,'legacy':stats_us(legacy),'candidate':stats_us(fast),'mismatches':mismatches}
    result['speedup_p50']=result['legacy']['p50_us']/result['candidate']['p50_us']
    result['speedup_p95']=result['legacy']['p95_us']/result['candidate']['p95_us']
    ledger.close(); return result

def graph_row(db,logical,version,epoch,status,src,dst,rel):
    db.execute('INSERT INTO graph_edges(edge_version_id,logical_edge_id,graph_epoch,source_logical_id,target_logical_id,relation_type,weight,confidence,provenance_clay,admissibility_clay,causal_class,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(version,logical,epoch,src,dst,rel,1.0,0.9,'{}','{}','ASSOCIATIVE',status,f'2026-08-10T00:00:{epoch:02d}Z'))

def bench_graph(logical_edges,versions,reps):
    db=sqlite3.connect(':memory:'); db.row_factory=sqlite3.Row
    db.executescript(GRAPH_BASE.read_text()); db.executescript(GRAPH_V3.read_text())
    for e in range(1,versions+1): db.execute('INSERT INTO graph_epochs VALUES(?,?,?,?,?)',(e,e,f'b{e}',f'2026-08-10T00:00:{e:02d}Z','CURRENT'))
    for i in range(logical_edges):
        for e in range(1,versions+1):
            st='RETRACTED' if e==versions and i%17==0 else 'CURRENT'
            graph_row(db,f'e{i:06d}',f'e{i:06d}-v{e}',e,st,f'n{i%97}',f'n{(i+1)%97}',f'r{i%7}')
    db.commit()
    ambiguous=db.execute('SELECT COUNT(*) FROM v_graph_projection_ambiguous_edge_epochs').fetchone()[0]
    legacy_all=[tuple(r) for r in db.execute('SELECT logical_edge_id,edge_version_id,graph_epoch,source_logical_id,target_logical_id,relation_type,status FROM v_latest_graph_edges ORDER BY logical_edge_id,edge_version_id')]
    fast_all=[tuple(r) for r in db.execute('SELECT logical_edge_id,edge_version_id,graph_epoch,source_logical_id,target_logical_id,relation_type,source_status FROM v_graph_current_edges_fast ORDER BY logical_edge_id,edge_version_id')]
    rng=random.Random(991); srcs=[f'n{rng.randrange(97)}' for _ in range(reps)]
    legacy=[]; fast=[]
    for src in srcs:
        t=time.perf_counter_ns(); list(db.execute('SELECT logical_edge_id,target_logical_id,relation_type FROM v_latest_graph_edges WHERE source_logical_id=? ORDER BY relation_type,target_logical_id,logical_edge_id',(src,))); legacy.append((time.perf_counter_ns()-t)/1000)
        t=time.perf_counter_ns(); list(db.execute('SELECT logical_edge_id,target_logical_id,relation_type FROM v_graph_current_edges_fast WHERE source_logical_id=? ORDER BY relation_type,target_logical_id,logical_edge_id',(src,))); fast.append((time.perf_counter_ns()-t)/1000)
    result={'logical_edges':logical_edges,'versions':versions,'history_rows':logical_edges*versions,'current_rows':len(fast_all),'ambiguous_epoch_heads':ambiguous,'differential_equal':legacy_all==fast_all,'legacy':stats_us(legacy),'candidate':stats_us(fast)}
    result['speedup_p50']=result['legacy']['p50_us']/result['candidate']['p50_us']; result['speedup_p95']=result['legacy']['p95_us']/result['candidate']['p95_us']
    db.close(); return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--state-rows',type=int,default=20000); ap.add_argument('--graph-logical-edges',type=int,default=8000); ap.add_argument('--graph-versions',type=int,default=7); ap.add_argument('--reps',type=int,default=100); a=ap.parse_args()
    out={'schema':'clay-udb-graph-hotpath-benchmark-1','timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'metadata':{'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform(),'machine':platform.machine(),'pid':os.getpid()},'unifieddb':bench_udb(a.state_rows,a.reps),'claygraph':bench_graph(a.graph_logical_edges,a.graph_versions,a.reps)}
    print(json.dumps(out,sort_keys=True,indent=2))

if __name__=='__main__': main()
