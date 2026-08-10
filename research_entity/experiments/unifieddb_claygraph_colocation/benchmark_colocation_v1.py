#!/usr/bin/env python3
"""UnifiedDB + ClayGraph physical co-location falsifier.

Tests whether both logical planes can share one SQLite commit domain without merging semantic
authority. Detects the existing generic `meta` schema collision, applies a candidate namespace
fix only inside this experiment, compares matched commit latency/storage, and injects rollback
failures. Host-power-loss atomicity is not simulated here.
"""
from __future__ import annotations
import argparse, json, os, platform, sqlite3, statistics, tempfile, time
from pathlib import Path

from research_entity.harness.reference.state_ledger import SCHEMA as STATE_SCHEMA, cjson, h

ROOT=Path(__file__).resolve().parents[3]
GRAPH_SCHEMA_PATH=ROOT/'research_entity/runtime/RAE_CLAYGRAPH_SCHEMA.sql'
GRAPH_V3_PATH=ROOT/'research_entity/runtime/RAE_CLAYGRAPH_V3_CURRENT_PROJECTIONS.sql'

def graph_schema_colocated():
    s=GRAPH_SCHEMA_PATH.read_text()
    old="""CREATE TABLE IF NOT EXISTS meta(\n  key TEXT PRIMARY KEY,\n  value TEXT NOT NULL\n);"""
    if old not in s: raise RuntimeError('expected ClayGraph meta declaration changed; re-audit co-location transform')
    return s.replace(old,"""CREATE TABLE IF NOT EXISTS claygraph_meta(\n  key TEXT PRIMARY KEY,\n  value TEXT NOT NULL\n);""",1)

def pragmas(c):
    c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=FULL'); c.execute('PRAGMA foreign_keys=ON')

def seed_state(c,n=2000):
    c.execute('BEGIN IMMEDIATE')
    for d in range(8): c.execute('INSERT OR REPLACE INTO domain_epochs VALUES(?,?)',(f'd{d}',1))
    rows=[]
    for i in range(n):
        d=f'd{i%8}'; k=f'k{i:07d}'; value={'i':i}; rows.append((d,k,cjson(value),'KNOWN','CURRENT',1,h({'domain':d,'key':k,'value':value,'epistemic':'KNOWN','status':'CURRENT'})))
    c.executemany('INSERT INTO state VALUES(?,?,?,?,?,?,?)',rows); c.commit()

def seed_graph(c,prefix='',nodes=800):
    q=lambda table:f'{prefix}{table}'
    c.execute('BEGIN IMMEDIATE'); c.execute(f"INSERT INTO {q('graph_epochs')} VALUES(1,1,'seed','2026-08-10T00:00:00Z','CURRENT')")
    rows=[]
    for i in range(nodes): rows.append((f'n{i}@1',f'n{i}',1,'STATE',f'n{i}','{}',0.1,0.1,1.0,'bench','DERIVED','CURRENT','2026-08-10T00:00:00Z'))
    c.executemany(f"INSERT INTO {q('graph_nodes')} VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",rows); c.commit()

def stats(xs):
    xs=sorted(xs); return {'n':len(xs),'p50_us':statistics.median(xs),'p95_us':xs[int(.95*(len(xs)-1))],'p99_us':xs[int(.99*(len(xs)-1))],'min_us':xs[0],'max_us':xs[-1]}

def tx_single(c,i):
    c.execute('BEGIN IMMEDIATE')
    c.execute("UPDATE state SET value_json=? WHERE domain='d0' AND k=?",(cjson({'tx':i}),f'k{(i%250)*8:07d}'))
    ge=i+2; c.execute('INSERT INTO graph_epochs VALUES(?,?,?,?,?)',(ge,ge,'bench','2026-08-10T00:00:00Z','CURRENT'))
    c.execute('INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(f'e{i}@{ge}',f'e{i}',ge,'n0',f'n{i%800}','TOUCH',.5,1.0,'{}','{}',None,'CURRENT','2026-08-10T00:00:00Z'))
    c.commit()

def tx_attached(c,i):
    c.execute('BEGIN IMMEDIATE')
    c.execute("UPDATE state SET value_json=? WHERE domain='d0' AND k=?",(cjson({'tx':i}),f'k{(i%250)*8:07d}'))
    ge=i+2; c.execute('INSERT INTO g.graph_epochs VALUES(?,?,?,?,?)',(ge,ge,'bench','2026-08-10T00:00:00Z','CURRENT'))
    c.execute('INSERT INTO g.graph_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(f'e{i}@{ge}',f'e{i}',ge,'n0',f'n{i%800}','TOUCH',.5,1.0,'{}','{}',None,'CURRENT','2026-08-10T00:00:00Z'))
    c.commit()

def inject_rollback(c,attached=False):
    edge_table='g.graph_edges' if attached else 'graph_edges'; before_state=c.execute("SELECT value_json FROM state WHERE domain='d0' AND k='k0000000'").fetchone()[0]; before_edges=c.execute(f'SELECT count(*) FROM {edge_table}').fetchone()[0]
    try:
        c.execute('BEGIN IMMEDIATE'); c.execute("UPDATE state SET value_json='\"CORRUPT\"' WHERE domain='d0' AND k='k0000000'");
        if attached:c.execute("INSERT INTO g.graph_epochs VALUES(999999,999999,'rollback','x','CURRENT')")
        else:c.execute("INSERT INTO graph_epochs VALUES(999999,999999,'rollback','x','CURRENT')")
        c.execute(f"INSERT INTO {edge_table} VALUES('rollback-edge','rollback-edge',999999,'n0','n1','FAIL',1,1,'{{}}','{{}}',NULL,'CURRENT','x')")
        raise RuntimeError('injected')
    except RuntimeError:c.rollback()
    after_state=c.execute("SELECT value_json FROM state WHERE domain='d0' AND k='k0000000'").fetchone()[0]; after_edges=c.execute(f'SELECT count(*) FROM {edge_table}').fetchone()[0]
    return before_state==after_state and before_edges==after_edges

def size(paths):
    total=0
    for p in paths:
        for suffix in ('','-wal','-shm'):
            q=p+suffix
            if os.path.exists(q): total+=os.path.getsize(q)
    return total

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--transactions',type=int,default=1000); ap.add_argument('--output'); a=ap.parse_args()
    raw_graph=GRAPH_SCHEMA_PATH.read_text(); collision=('CREATE TABLE IF NOT EXISTS meta(' in raw_graph and 'CREATE TABLE IF NOT EXISTS meta(' in STATE_SCHEMA)
    with tempfile.TemporaryDirectory() as td:
        single=os.path.join(td,'unified.sqlite'); s=sqlite3.connect(single); pragmas(s); s.executescript(STATE_SCHEMA); s.executescript(graph_schema_colocated()); s.executescript(GRAPH_V3_PATH.read_text()); seed_state(s); seed_graph(s)
        state=os.path.join(td,'state.sqlite'); graph=os.path.join(td,'graph.sqlite'); t=sqlite3.connect(state); pragmas(t); t.executescript(STATE_SCHEMA); seed_state(t); g=sqlite3.connect(graph); pragmas(g); g.executescript(raw_graph); g.executescript(GRAPH_V3_PATH.read_text()); seed_graph(g); g.close(); t.execute("ATTACH DATABASE ? AS g",(graph,)); t.execute('PRAGMA g.journal_mode=WAL'); t.execute('PRAGMA g.synchronous=FULL')
        one=[]; two=[]
        for i in range(a.transactions):
            z=time.perf_counter_ns(); tx_single(s,i); one.append((time.perf_counter_ns()-z)/1000)
            z=time.perf_counter_ns(); tx_attached(t,i); two.append((time.perf_counter_ns()-z)/1000)
        sr=inject_rollback(s,False); tr=inject_rollback(t,True)
        s.execute('PRAGMA wal_checkpoint(TRUNCATE)'); t.execute('PRAGMA wal_checkpoint(TRUNCATE)'); t.execute('PRAGMA g.wal_checkpoint(TRUNCATE)')
        out={'schema':'clay.udb_claygraph_colocation.v1','scope':'matched SQLite WAL/FULL local commit-domain experiment','environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.platform()},'schema_collision_detected':collision,'collision':'StateLedger meta(k,v) vs ClayGraph meta(key,value)' if collision else None,'candidate_fix':'namespace ClayGraph generic meta as claygraph_meta; graph_* objects unchanged','single_file':{'commit_latency':stats(one),'rollback_injection_pass':sr,'bytes':size([single])},'two_file_attach':{'commit_latency':stats(two),'rollback_injection_pass':tr,'bytes':size([state,graph])},'single_vs_two_p50_speedup':statistics.median(two)/statistics.median(one),'storage_ratio_single_over_two':size([single])/size([state,graph]),'crash_atomicity_note':'Host/power-loss atomicity across attached WAL databases is NOT tested here; use SQLite official transaction documentation as external evidence.','promotion':'CANDIDATE_ONLY'}
        text=json.dumps(out,indent=2,sort_keys=True); print(text)
        if a.output:Path(a.output).write_text(text+'\n')
        s.close(); t.close()
if __name__=='__main__':main()
