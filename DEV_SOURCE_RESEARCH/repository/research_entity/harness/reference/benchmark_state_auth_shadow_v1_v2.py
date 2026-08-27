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
from .state_auth_shadow_embedded_v2 import EmbeddedAuthenticatedStateShadowV2
from .state_ledger import StateLedger


def quantile(xs, p):
    ys=sorted(xs); k=(len(ys)-1)*p; lo=math.floor(k); hi=math.ceil(k)
    return ys[lo] if lo==hi else ys[lo]*(hi-k)+ys[hi]*(k-lo)


def stats_ms(xs):
    return {
        'n':len(xs),'p50_ms':quantile(xs,.5),'p95_ms':quantile(xs,.95),
        'p99_ms':quantile(xs,.99),'mean_ms':statistics.fmean(xs),
        'min_ms':min(xs),'max_ms':max(xs),
    }


def timed_ms(fn):
    started=time.perf_counter_ns(); out=fn()
    return out,(time.perf_counter_ns()-started)/1e6


def seed_ledger(rows):
    ledger=StateLedger(); ops=[]; epis=('KNOWN','UNKNOWN','CONFLICT')
    for i in range(rows):
        ops.append({
            'op':'SET','domain':f'd{i%20:02d}','key':f'k{i:06d}',
            'value':{'i':i,'u':'äλ✓','nested':[True,None,{'$kind':'set','items':[3,1,3,2]}]},
            'epistemic':epis[i%3],
            'status':'SUPERSEDED' if i%11==0 else 'CURRENT',
        })
    ledger.append_event(event_id='seed',idem='seed',base_epoch=0,event_type='BENCH_SEED',writer='benchmark',ops=ops)
    return ledger


def run_variant(name, shadow_cls, rows, updates, seed):
    ledger=seed_ledger(rows)
    page_size=int(ledger.conn.execute('PRAGMA page_size').fetchone()[0])
    pages_before=int(ledger.conn.execute('PRAGMA page_count').fetchone()[0])
    canonical_before=ledger.semantic_state_hash
    shadow=shadow_cls(ledger)
    rebuild,rebuild_ms=timed_ms(lambda:shadow.full_rebuild(now=f'{name}-rebuild-0'))
    pages_after=int(ledger.conn.execute('PRAGMA page_count').fetchone()[0])
    verify0,verify0_ms=timed_ms(shadow.verify_full)
    assert verify0.passed
    assert ledger.semantic_state_hash==canonical_before
    assert ledger._roots()[0]==canonical_before

    rng=random.Random(seed); commit_ms=[]; refresh_ms=[]
    for i in range(updates):
        idx=rng.randrange(rows); domain=f'd{idx%20:02d}'; key=f'k{idx:06d}'
        def commit_one(i=i,idx=idx,domain=domain,key=key):
            return ledger.append_event(
                event_id=f'u{i}',idem=f'u{i}',base_epoch=ledger.epoch,event_type='BENCH_UPDATE',writer='benchmark',
                ops=[{'op':'SET','domain':domain,'key':key,'value':{'i':idx,'update':i,'u':'✓'},'epistemic':'KNOWN','status':'CURRENT'}],
            )
        _,dt=timed_ms(commit_one); commit_ms.append(dt)
        out,dt=timed_ms(lambda i=i:shadow.refresh(now=f'{name}-refresh-{i}'))
        assert out['mode']=='DELTA_REFRESH' and out['touched_refs']==1
        refresh_ms.append(dt)

    incremental_root=shadow.receipt().root_hash
    rebuilt,rebuild_after_ms=timed_ms(lambda:shadow.full_rebuild(now=f'{name}-rebuild-after'))
    rebuild_equal=(rebuilt['root_hash']==incremental_root)
    verify1,verify1_ms=timed_ms(shadow.verify_full)

    full_root_ms=[]
    for _ in range(8):
        _,dt=timed_ms(ledger._roots); full_root_ms.append(dt)

    ledger.conn.execute('BEGIN IMMEDIATE')
    row=ledger.conn.execute('SELECT domain,k FROM state ORDER BY domain,k LIMIT 1').fetchone()
    ledger.conn.execute('UPDATE state SET value_json=? WHERE domain=? AND k=?',('{"tampered":true}',row[0],row[1]))
    tamper_detected=not shadow.verify_full().passed
    ledger.conn.rollback()

    result={
        'variant':name,'rows':rows,'updates':updates,
        'bootstrap':{
            'rebuild_ms':rebuild_ms,'verify_ms':verify0_ms,
            'pages_before':pages_before,'pages_after':pages_after,
            'page_size':page_size,'page_ratio':pages_after/pages_before,
        },
        'steady_state':{
            'authoritative_commit':stats_ms(commit_ms),
            'shadow_refresh':stats_ms(refresh_ms),
            'canonical_full_root':stats_ms(full_root_ms),
            'root_speedup_p50':quantile(full_root_ms,.5)/quantile(refresh_ms,.5),
        },
        'recovery':{
            'rebuild_after_ms':rebuild_after_ms,
            'rebuild_equivalent':rebuild_equal,
            'verify_after_ms':verify1_ms,
            'verify_after_pass':verify1.passed,
            'tamper_detected':tamper_detected,
        },
    }
    ledger.close()
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--rows',type=int,default=20000); ap.add_argument('--updates',type=int,default=30); args=ap.parse_args()
    v1=run_variant('V1_SIDECAR',AuthenticatedStateShadowV1,args.rows,args.updates,20260810)
    v2=run_variant('V2_EMBEDDED',EmbeddedAuthenticatedStateShadowV2,args.rows,args.updates,20260810)
    comparison={
        'v2_vs_v1_refresh_p50_ratio':v2['steady_state']['shadow_refresh']['p50_ms']/v1['steady_state']['shadow_refresh']['p50_ms'],
        'v2_vs_v1_refresh_p95_ratio':v2['steady_state']['shadow_refresh']['p95_ms']/v1['steady_state']['shadow_refresh']['p95_ms'],
        'v2_vs_v1_page_ratio_ratio':v2['bootstrap']['page_ratio']/v1['bootstrap']['page_ratio'],
        'v2_page_overhead_reduction_fraction':1.0-(v2['bootstrap']['page_ratio']-1.0)/(v1['bootstrap']['page_ratio']-1.0),
        'both_rebuild_equivalent':v1['recovery']['rebuild_equivalent'] and v2['recovery']['rebuild_equivalent'],
        'both_verify_pass':v1['recovery']['verify_after_pass'] and v2['recovery']['verify_after_pass'],
        'both_tamper_detect':v1['recovery']['tamper_detected'] and v2['recovery']['tamper_detected'],
    }
    payload={
        'schema_version':'1.0','benchmark':'AUTH_STATE_SHADOW_V1_V2_MATCHED',
        'metadata':{'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform(),'rows':args.rows,'updates':args.updates},
        'v1':v1,'v2':v2,'comparison':comparison,
        'authority':'BENCHMARK_ONLY_NO_CANONICAL_ROOT_PROMOTION',
        'pass':comparison['both_rebuild_equivalent'] and comparison['both_verify_pass'] and comparison['both_tamper_detect'],
    }
    print(json.dumps(payload,indent=2,sort_keys=True))
    if not payload['pass']:
        raise SystemExit(2)


if __name__=='__main__': main()
