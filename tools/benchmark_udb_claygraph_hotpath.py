#!/usr/bin/env python3
"""Reproducible shadow benchmark for UnifiedDB query pushdown + ClayGraph V3.

This benchmark is intentionally synthetic and does not promote architecture. It measures
implementation hot paths, checks exact set-equivalence of current graph projections, and
emits raw metadata/results as JSON for comparison across machines.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import sqlite3
import statistics
import tempfile
import time
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane

ROOT = Path(__file__).resolve().parents[1]


def us(fn, n: int):
    xs=[]
    for _ in range(n):
        t=time.perf_counter_ns(); fn(); xs.append((time.perf_counter_ns()-t)/1000.0)
    xs.sort()
    def q(p): return xs[min(len(xs)-1, int((len(xs)-1)*p))]
    return {'n':len(xs),'min_us':xs[0],'p50_us':statistics.median(xs),'p95_us':q(.95),'p99_us':q(.99),'max_us':xs[-1],'mean_us':statistics.fmean(xs)}


def old_python_query(ledger: StateLedger, spec: QuerySpec):
    domains=set(spec.domains); keys=set(spec.keys); statuses={x.upper() for x in spec.statuses}; epistemic={x.upper() for x in spec.epistemic}
    rows=[]
    for row in ledger.materialized():
        if domains and row['domain'] not in domains: continue
        if keys and row['key'] not in keys: continue
        if row['status'].upper() not in statuses: continue
        if row['epistemic'].upper() not in epistemic: continue
        rows.append(row)
    rows.sort(key=lambda x:(x['domain'],x['key'],x['domain_epoch'],x['semantic_hash']))
    return rows[:spec.limit], len(rows)>spec.limit


def bench_udb(state_rows: int, reps: int):
    fd,path=tempfile.mkstemp(prefix='clay-udb-',suffix='.sqlite'); os.close(fd)
    try:
        ledger=StateLedger(path); plane=UnifiedDBQueryPlane(ledger)
        domains=('semantic','memory','world','self','goal','capability','peer','episode')
        ops=[]
        for i in range(state_rows):
            d=domains[i % len(domains)]
            ops.append({'op':'SET','domain':d,'key':f'k{i:07d}','value':{'i':i,'text':f'value-{i}'},'epistemic':'KNOWN' if i%11 else 'UNKNOWN','status':'CURRENT'})
        ledger.append_event(event_id='bench-seed',idem='bench-seed',base_epoch=0,event_type='BENCH_SEED',writer='benchmark',ops=ops)
        target=(state_rows//2)
        target_domain=domains[target % len(domains)]; target_key=f'k{target:07d}'
        selective=QuerySpec('selective',domains=(target_domain,),keys=(target_key,),statuses=('CURRENT',),epistemic=('KNOWN','UNKNOWN','CONFLICT'),limit=8,basis_epoch=ledger.epoch)
        domain_scan=QuerySpec('domain-scan',domains=('memory',),statuses=('CURRENT',),epistemic=('KNOWN','UNKNOWN','CONFLICT'),limit=64,basis_epoch=ledger.epoch)
        old_rows,old_tr=old_python_query(ledger,selective); new=plane.query(selective)
        selective_equal=(list(new.rows)==old_rows and new.truncated==old_tr)
        old_rows2,old_tr2=old_python_query(ledger,domain_scan); new2=plane.query(domain_scan)
        domain_equal=(list(new2.rows)==old_rows2 and new2.truncated==old_tr2)
        old_sel=us(lambda: old_python_query(ledger,selective),reps)
        new_sel=us(lambda: plane.query(selective),reps)
        old_dom=us(lambda: old_python_query(ledger,domain_scan),max(10,reps//3))
        new_dom=us(lambda: plane.query(domain_scan),max(10,reps//3))
        return {
            'state_rows':state_rows,'selective_equivalent':selective_equal,'domain_scan_equivalent':domain_equal,
            'old_selective':old_sel,'sql_pushdown_selective':new_sel,'selective_p50_speedup':old_sel['p50_us']/new_sel['p50_us'],
            'old_domain_scan':old_dom,'sql_pushdown_domain_scan':new_dom,'domain_scan_p50_speedup':old_dom['p50_us']/new_dom['p50_us'],
        }
    finally:
        try: ledger.close()
        except Exception: pass
        for suffix in ('','-wal','-shm'):
            try: os.remove(path+suffix)
            except FileNotFoundError: pass


def bench_graph(logical_nodes: int, logical_edges: int, versions: int, reps: int):
    fd,path=tempfile.mkstemp(prefix='clay-graph-',suffix='.sqlite'); os.close(fd)
    try:
        c=sqlite3.connect(path)
        c.executescript((ROOT/'research_entity/runtime/RAE_CLAYGRAPH_SCHEMA.sql').read_text())
        now='2026-08-10T00:00:00Z'
        for ge in range(1,versions+1): c.execute('INSERT INTO graph_epochs VALUES(?,?,?,?,?)',(ge,ge,'benchmark',now,'CURRENT'))
        nodes=[]
        for i in range(logical_nodes):
            lid=f'n{i:07d}'
            for v in range(1,versions+1):
                st='CURRENT' if v==versions else 'SUPERSEDED'
                nodes.append((f'{lid}@{v}',lid,v,'BENCH',lid,'{}',(i%1000)/1000.0,0.0,1.0,'bench','DERIVED',st,now))
        c.executemany('INSERT INTO graph_nodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',nodes)
        random.seed(7); edges=[]
        for i in range(logical_edges):
            src=f'n{random.randrange(logical_nodes):07d}'; dst=f'n{random.randrange(logical_nodes):07d}'; eid=f'e{i:08d}'
            for v in range(1,versions+1):
                st='CURRENT' if v==versions else 'SUPERSEDED'
                edges.append((f'{eid}@{v}',eid,v,src,dst,'REL',(i%1000)/1000.0,1.0,'{}','{}',None,st,now))
        c.executemany('INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',edges); c.commit()
        bytes_before=os.path.getsize(path)
        c.executescript((ROOT/'research_entity/runtime/RAE_CLAYGRAPH_V3_CURRENT_HOTPATH_CANDIDATE.sql').read_text()); c.commit()
        bytes_after=os.path.getsize(path)
        node_diff_a=c.execute('SELECT COUNT(*) FROM (SELECT node_version_id FROM v_latest_graph_nodes EXCEPT SELECT node_version_id FROM v_candidate_current_graph_nodes_v3)').fetchone()[0]
        node_diff_b=c.execute('SELECT COUNT(*) FROM (SELECT node_version_id FROM v_candidate_current_graph_nodes_v3 EXCEPT SELECT node_version_id FROM v_latest_graph_nodes)').fetchone()[0]
        edge_diff_a=c.execute('SELECT COUNT(*) FROM (SELECT edge_version_id FROM v_latest_graph_edges EXCEPT SELECT edge_version_id FROM v_candidate_current_graph_edges_v3)').fetchone()[0]
        edge_diff_b=c.execute('SELECT COUNT(*) FROM (SELECT edge_version_id FROM v_candidate_current_graph_edges_v3 EXCEPT SELECT edge_version_id FROM v_latest_graph_edges)').fetchone()[0]
        src=c.execute("SELECT source_logical_id FROM v_candidate_current_graph_edges_v3 GROUP BY source_logical_id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()[0]
        old_adj=lambda: c.execute('SELECT target_logical_id,relation_type,weight FROM v_latest_graph_edges WHERE source_logical_id=? ORDER BY weight DESC LIMIT 32',(src,)).fetchall()
        new_adj=lambda: c.execute('SELECT target_logical_id,relation_type,weight FROM v_candidate_current_graph_edges_v3 WHERE source_logical_id=? ORDER BY weight DESC LIMIT 32',(src,)).fetchall()
        old_top=lambda: c.execute('SELECT logical_id,activation FROM v_latest_graph_nodes ORDER BY activation DESC LIMIT 32').fetchall()
        new_top=lambda: c.execute('SELECT logical_id,activation FROM v_candidate_current_graph_nodes_v3 ORDER BY activation DESC LIMIT 32').fetchall()
        old_a=us(old_adj,reps); new_a=us(new_adj,reps); old_t=us(old_top,reps); new_t=us(new_top,reps)
        duplicate_current_blocked=False
        try:
            c.execute('INSERT INTO graph_nodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',('dup@x','n0000000',versions,'BENCH','dup','{}',0,0,1,'bench','DERIVED','CURRENT',now)); c.commit()
        except sqlite3.IntegrityError:
            c.rollback(); duplicate_current_blocked=True
        return {
            'logical_nodes':logical_nodes,'logical_edges':logical_edges,'versions':versions,
            'node_differential':[node_diff_a,node_diff_b],'edge_differential':[edge_diff_a,edge_diff_b],
            'exact_current_projection':node_diff_a==node_diff_b==edge_diff_a==edge_diff_b==0,
            'duplicate_current_blocked':duplicate_current_blocked,
            'old_adjacency':old_a,'v3_adjacency':new_a,'adjacency_p50_speedup':old_a['p50_us']/new_a['p50_us'],
            'old_top_activation':old_t,'v3_top_activation':new_t,'top_activation_p50_speedup':old_t['p50_us']/new_t['p50_us'],
            'db_bytes_before_indexes':bytes_before,'db_bytes_after_indexes':bytes_after,'index_size_overhead_fraction':(bytes_after-bytes_before)/bytes_before,
        }
    finally:
        try: c.close()
        except Exception: pass
        for suffix in ('','-wal','-shm'):
            try: os.remove(path+suffix)
            except FileNotFoundError: pass


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--state-rows',type=int,default=10000); ap.add_argument('--nodes',type=int,default=1500); ap.add_argument('--edges',type=int,default=7500); ap.add_argument('--versions',type=int,default=5); ap.add_argument('--reps',type=int,default=60); ap.add_argument('--output')
    a=ap.parse_args()
    out={'schema_version':'1.0','evidence_class':'SYNTHETIC_IMPLEMENTATION_BENCHMARK','promotion_authority':'NONE','timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'platform':platform.platform(),'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'udb':bench_udb(a.state_rows,a.reps),'claygraph':bench_graph(a.nodes,a.edges,a.versions,a.reps)}
    text=json.dumps(out,indent=2,sort_keys=True); print(text)
    if a.output: Path(a.output).write_text(text+'\n')
    if not out['udb']['selective_equivalent'] or not out['udb']['domain_scan_equivalent'] or not out['claygraph']['exact_current_projection'] or not out['claygraph']['duplicate_current_blocked']:
        raise SystemExit(2)

if __name__=='__main__': main()
