#!/usr/bin/env python3
"""Matched benchmark for legacy vs hash-identical streaming StateLedger roots.

Synthetic implementation benchmark only. The pass condition is exact root equality at every
size; speedup is reported, never used as a semantic correctness substitute.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sqlite3
import statistics
import tempfile
import time

from research_entity.harness.reference.state_ledger import StateLedger, cjson, h


def summary(values):
    xs=sorted(values)
    return {
        'n':len(xs),
        'min_ms':xs[0],
        'p50_ms':statistics.median(xs),
        'p95_ms':xs[int(.95*(len(xs)-1))],
        'max_ms':xs[-1],
        'mean_ms':statistics.fmean(xs),
    }


def timed(fn,reps):
    xs=[]; last=None
    for _ in range(reps):
        t=time.perf_counter_ns(); last=fn(); xs.append((time.perf_counter_ns()-t)/1_000_000)
    return last,summary(xs)


def seed(ledger: StateLedger, rows: int, domains: int=20):
    ledger.conn.execute('BEGIN IMMEDIATE')
    try:
        for d in range(domains):
            ledger.conn.execute('INSERT OR REPLACE INTO domain_epochs VALUES(?,?)',(f'd{d:02d}',d+7))
        batch=[]
        for i in range(rows):
            domain=f'd{i%domains:02d}'; key=f'k{i:08d}'
            value={'i':i,'text':'Grüße-'+str(i),'tags':{'$kind':'set','items':[i%7,i%13,i%7]},'nested':{'b':i%3,'a':bool(i%2)}}
            semantic_hash=h({'domain':domain,'key':key,'value':value,'epistemic':'KNOWN','status':'CURRENT'})
            batch.append((domain,key,cjson(value),'KNOWN','CURRENT',(i//domains)+1,semantic_hash))
        ledger.conn.executemany('INSERT INTO state VALUES(?,?,?,?,?,?,?)',batch)
        ledger._set('global_epoch',rows+1)
        ledger.conn.commit()
    except Exception:
        ledger.conn.rollback(); raise


def one_size(rows,reps):
    with tempfile.TemporaryDirectory() as td:
        path=os.path.join(td,'roots.sqlite')
        l=StateLedger(path); seed(l,rows)
        legacy0=l._roots_legacy(); stream0=l._roots()
        if legacy0 != stream0:
            raise AssertionError(f'root mismatch before benchmark at {rows} rows')
        legacy_hash,legacy=timed(l._roots_legacy,reps)
        stream_hash,stream=timed(l._roots,reps)
        if legacy_hash != stream_hash:
            raise AssertionError(f'root mismatch after benchmark at {rows} rows')
        db_bytes=os.path.getsize(path)
        l.close()
        return {
            'state_rows':rows,
            'root_equal':True,
            'semantic_state_hash':legacy_hash[0],
            'trace_root_hash':legacy_hash[1],
            'legacy':legacy,
            'streaming':stream,
            'p50_speedup':legacy['p50_ms']/stream['p50_ms'],
            'db_bytes':db_bytes,
        }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--sizes',default='1000,10000,50000')
    ap.add_argument('--reps',type=int,default=5)
    ap.add_argument('--output')
    a=ap.parse_args(); sizes=[int(x) for x in a.sizes.split(',') if x.strip()]
    out={
        'schema':'clay.stateledger_root_benchmark.v1',
        'scope':'synthetic matched implementation benchmark; same canonical SHA-256 contract',
        'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'environment':{
            'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,
            'platform':platform.platform(),'machine':platform.machine(),'processor':platform.processor() or 'UNKNOWN',
        },
        'results':[one_size(n,a.reps) for n in sizes],
    }
    text=json.dumps(out,indent=2,sort_keys=True); print(text)
    if a.output:
        from pathlib import Path
        Path(a.output).write_text(text+'\n')
    if not all(r['root_equal'] for r in out['results']):
        raise SystemExit(2)

if __name__=='__main__': main()
