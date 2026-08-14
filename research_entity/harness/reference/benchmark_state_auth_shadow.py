from __future__ import annotations

import argparse
import json
import math
import platform
import random
import sqlite3
import statistics
import sys
import time

from .state_auth_shadow import AuthenticatedStateShadowV1
from .state_ledger import StateLedger


def q(xs, p):
    ys = sorted(xs); k = (len(ys)-1)*p; a = math.floor(k); b = math.ceil(k)
    return ys[a] if a == b else ys[a]*(b-k)+ys[b]*(k-a)


def stats_ms(xs):
    return {
        'n': len(xs), 'p50_ms': q(xs,.5), 'p95_ms': q(xs,.95), 'p99_ms': q(xs,.99),
        'mean_ms': statistics.fmean(xs), 'min_ms': min(xs), 'max_ms': max(xs),
    }


def timed_ms(fn):
    started = time.perf_counter_ns(); out = fn()
    return out, (time.perf_counter_ns()-started)/1e6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rows', type=int, default=20000)
    ap.add_argument('--updates', type=int, default=30)
    args = ap.parse_args()

    ledger = StateLedger()
    ops=[]
    epis=('KNOWN','UNKNOWN','CONFLICT')
    for i in range(args.rows):
        ops.append({
            'op':'SET','domain':f'd{i%20:02d}','key':f'k{i:06d}',
            'value':{'i':i,'u':'äλ✓','nested':[True,None,{'$kind':'set','items':[3,1,3,2]}]},
            'epistemic':epis[i%3], 'status':'SUPERSEDED' if i%11==0 else 'CURRENT',
        })
    ledger.append_event(event_id='seed',idem='seed',base_epoch=0,event_type='BENCH_SEED',writer='benchmark',ops=ops)
    page_size=int(ledger.conn.execute('PRAGMA page_size').fetchone()[0])
    pages_before_shadow=int(ledger.conn.execute('PRAGMA page_count').fetchone()[0])

    shadow=AuthenticatedStateShadowV1(ledger)
    rebuild_out,rebuild_ms=timed_ms(lambda:shadow.full_rebuild(now='rebuild-0'))
    pages_after_shadow=int(ledger.conn.execute('PRAGMA page_count').fetchone()[0])
    verification,verify_ms=timed_ms(shadow.verify_full)
    if not verification.passed: raise RuntimeError(verification)

    rng=random.Random(20260810)
    commit_ms=[]; refresh_ms=[]
    for i in range(args.updates):
        idx=rng.randrange(args.rows); domain=f'd{idx%20:02d}'; key=f'k{idx:06d}'
        _,dt=timed_ms(lambda i=i,idx=idx,domain=domain,key=key: ledger.append_event(
            event_id=f'u{i}',idem=f'u{i}',base_epoch=ledger.epoch,event_type='BENCH_UPDATE',writer='benchmark',
            ops=[{'op':'SET','domain':domain,'key':key,'value':{'i':idx,'update':i,'u':'✓'},'epistemic':'KNOWN','status':'CURRENT'}]))
        commit_ms.append(dt)
        out,dt=timed_ms(lambda i=i:shadow.refresh(now=f'refresh-{i}'))
        if out['mode']!='DELTA_REFRESH' or out['touched_refs']!=1: raise RuntimeError(out)
        refresh_ms.append(dt)

    current_root=shadow.receipt().root_hash
    rebuilt,rebuild_after_ms=timed_ms(lambda:shadow.full_rebuild(now='rebuild-after'))
    rebuild_equivalent=(rebuilt['root_hash']==current_root)
    verification_after,verify_after_ms=timed_ms(shadow.verify_full)

    full_root_times=[]
    for _ in range(min(12,max(4,args.updates//2))):
        _,dt=timed_ms(ledger._roots); full_root_times.append(dt)

    ledger.conn.execute('BEGIN IMMEDIATE')
    row=ledger.conn.execute('SELECT domain,k FROM state ORDER BY domain,k LIMIT 1').fetchone()
    ledger.conn.execute("UPDATE state SET value_json='{" + '"tampered":true' + "}' WHERE domain=? AND k=?",(row[0],row[1]))
    tamper_detected=not shadow.verify_full().passed
    ledger.conn.rollback()

    out={
        'schema':'clay-auth-state-shadow-benchmark-1',
        'metadata':{
            'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform(),
            'rows':args.rows,'updates':args.updates,'page_size':page_size,
        },
        'bootstrap':{
            'full_rebuild_ms':rebuild_ms,'full_verify_ms':verify_ms,
            'pages_before_shadow':pages_before_shadow,'pages_after_shadow':pages_after_shadow,
            'page_ratio':pages_after_shadow/pages_before_shadow,
            'root_hash':rebuild_out['root_hash'],
        },
        'updates':{
            'authoritative_commit':stats_ms(commit_ms),
            'shadow_delta_refresh':stats_ms(refresh_ms),
            'full_canonical_root_recompute':stats_ms(full_root_times),
            'root_refresh_vs_full_root_p50_ratio':q(full_root_times,.5)/q(refresh_ms,.5),
        },
        'recovery':{
            'rebuild_after_ms':rebuild_after_ms,'rebuild_equivalent':rebuild_equivalent,
            'verify_after_ms':verify_after_ms,'verify_after_pass':verification_after.passed,
            'raw_state_tamper_detected':tamper_detected,
        },
        'authority':'CANDIDATE_SHADOW_ONLY_NOT_CANONICAL_STATE_ROOT',
    }
    print(json.dumps(out,indent=2,sort_keys=True))
    if not rebuild_equivalent or not verification_after.passed or not tamper_detected:
        raise SystemExit(2)
    ledger.close()


if __name__=='__main__': main()
