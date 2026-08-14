#!/usr/bin/env python3
"""Counterhypothesis: can explicit epoch pinning make two attached WAL DBs safe enough?

The guard is a fair mitigation for the cross-file snapshot skew demonstrated by
benchmark_snapshot_coherence_v1.py. A state row carries authoritative epoch E and the graph
projection carries source_epoch E. A mixed snapshot is rejected instead of admitted.

This benchmark measures both adversarial detection/retry and steady-state guarded read cost.
It does not claim that these two integer markers implement the complete Clay receipt contract.
"""
from __future__ import annotations
import argparse, json, platform, sqlite3, statistics, tempfile, threading, time
from pathlib import Path


def wal(c): c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=FULL')

def setup_two(td):
    s=Path(td)/'state.sqlite'; g=Path(td)/'graph.sqlite'
    c=sqlite3.connect(s); wal(c); c.executescript('CREATE TABLE state_marker(v INTEGER NOT NULL,epoch INTEGER NOT NULL); INSERT INTO state_marker VALUES(0,0);'); c.commit(); c.close()
    c=sqlite3.connect(g); wal(c); c.executescript('CREATE TABLE graph_marker(v INTEGER NOT NULL,source_epoch INTEGER NOT NULL); INSERT INTO graph_marker VALUES(0,0);'); c.commit(); c.close(); return s,g

def setup_one(td):
    p=Path(td)/'unified.sqlite'; c=sqlite3.connect(p); wal(c); c.executescript('CREATE TABLE state_marker(v INTEGER NOT NULL,epoch INTEGER NOT NULL); INSERT INTO state_marker VALUES(0,0); CREATE TABLE graph_marker(v INTEGER NOT NULL,source_epoch INTEGER NOT NULL); INSERT INTO graph_marker VALUES(0,0);'); c.commit(); c.close(); return p

def connect_two(state,graph):
    c=sqlite3.connect(state,timeout=5); c.execute('ATTACH DATABASE ? AS g',(str(graph),)); return c

def adversarial_guard_trial():
    with tempfile.TemporaryDirectory() as td:
        state,graph=setup_two(td); state_seen=threading.Event(); writer_done=threading.Event(); out={}
        def reader():
            c=connect_two(state,graph); c.execute('BEGIN')
            sv,se=c.execute('SELECT v,epoch FROM state_marker').fetchone(); state_seen.set()
            if not writer_done.wait(5): raise RuntimeError('writer timeout')
            gv,ge=c.execute('SELECT v,source_epoch FROM g.graph_marker').fetchone(); c.rollback()
            out['first']={'state_v':sv,'state_epoch':se,'graph_v':gv,'graph_source_epoch':ge,'accepted':se==ge}
            if se!=ge:
                c.execute('BEGIN'); sv,se=c.execute('SELECT v,epoch FROM state_marker').fetchone(); gv,ge=c.execute('SELECT v,source_epoch FROM g.graph_marker').fetchone(); c.rollback()
                out['retry']={'state_v':sv,'state_epoch':se,'graph_v':gv,'graph_source_epoch':ge,'accepted':se==ge}
            c.close()
        def writer():
            if not state_seen.wait(5): raise RuntimeError('reader timeout')
            c=connect_two(state,graph); c.execute('BEGIN IMMEDIATE'); c.execute('UPDATE state_marker SET v=1,epoch=1'); c.execute('UPDATE g.graph_marker SET v=1,source_epoch=1'); c.commit(); c.close(); writer_done.set()
        r=threading.Thread(target=reader); w=threading.Thread(target=writer); r.start(); w.start(); r.join(); w.join(); return out

def percentile(xs,p):
    xs=sorted(xs); return xs[int(p*(len(xs)-1))]

def steady_two(reads):
    with tempfile.TemporaryDirectory() as td:
        state,graph=setup_two(td); c=connect_two(state,graph); xs=[]; rejects=0
        for _ in range(reads):
            t=time.perf_counter_ns(); c.execute('BEGIN'); _sv,se=c.execute('SELECT v,epoch FROM state_marker').fetchone(); _gv,ge=c.execute('SELECT v,source_epoch FROM g.graph_marker').fetchone(); c.rollback(); xs.append((time.perf_counter_ns()-t)/1000); rejects+=int(se!=ge)
        c.close(); return {'p50_us':statistics.median(xs),'p95_us':percentile(xs,.95),'rejects':rejects}

def steady_one(reads):
    with tempfile.TemporaryDirectory() as td:
        path=setup_one(td); c=sqlite3.connect(path); xs=[]
        for _ in range(reads):
            t=time.perf_counter_ns(); c.execute('BEGIN'); c.execute('SELECT v,epoch FROM state_marker').fetchone(); c.execute('SELECT v,source_epoch FROM graph_marker').fetchone(); c.rollback(); xs.append((time.perf_counter_ns()-t)/1000)
        c.close(); return {'p50_us':statistics.median(xs),'p95_us':percentile(xs,.95)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--trials',type=int,default=100); ap.add_argument('--steady-reads',type=int,default=5000); ap.add_argument('--output'); a=ap.parse_args()
    trials=[adversarial_guard_trial() for _ in range(a.trials)]
    first_accept=sum(int(x['first']['accepted']) for x in trials); retries=[x.get('retry') for x in trials if 'retry' in x]; retry_accept=sum(int(x['accepted']) for x in retries)
    two=steady_two(a.steady_reads); one=steady_one(a.steady_reads)
    out={'schema':'clay.cross_store_epoch_guard.v1','scope':'counterhypothesis to physical co-location; marker-level epoch guard only','environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.platform()},'adversarial':{'trials':a.trials,'unsafe_first_reads_accepted':first_accept,'unsafe_first_reads_rejected':a.trials-first_accept,'retries':len(retries),'retry_accepts':retry_accept,'retry_success_rate':(retry_accept/len(retries) if retries else 1.0)},'steady_state':{'two_file_epoch_guard':two,'single_file_same_fields':one,'two_over_single_p50_ratio':two['p50_us']/one['p50_us']},'interpretation':'Explicit source-epoch pinning can fail-closed on cross-file snapshot skew. It is therefore the correct strong separate-store counterbaseline. Compare its retries/latency/receipt complexity against same-file snapshot coherence rather than comparing co-location to an unguarded strawman.','promotion':'COUNTERHYPOTHESIS_EVIDENCE'}
    text=json.dumps(out,indent=2,sort_keys=True); print(text)
    if a.output: Path(a.output).write_text(text+'\n')
    if first_accept or retry_accept!=len(retries) or two['rejects']: raise SystemExit(2)
if __name__=='__main__': main()
