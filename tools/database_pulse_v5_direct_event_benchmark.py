#!/usr/bin/env python3
from __future__ import annotations

"""Matched engineering benchmark: current semantic Pulse V4 vs direct-event execution V5.

This benchmark is intentionally narrow. It tests architecture claims introduced by V5:

H1  Idle endogenous Pulse execution must not advance StateLedger semantic epoch/root.
H2  A prepared semantic QueryReceipt must survive idle V5 Pulses but is expected to become
    stale after semantic V4 writes its pulse:* event.
H3  One StateLedger transaction containing many ops is one V5 source event, not a duplicate
    per-op Pulse delta log.
H4  Many source events are drained in whole-event batches with source_epoch/hash bound to the
    last fully acknowledged event.
H5  The remaining full canonical integrity audit cost is measured separately rather than
    hidden inside a generic Pulse latency number.

The benchmark does not claim external database superiority or final Frank task quality.
"""

import argparse
import json
import math
import os
import platform
import resource
import sqlite3
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch  # noqa:E402
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane  # noqa:E402
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec  # noqa:E402
from research_entity.runtime.database_pulse_runtime_v4 import DatabasePulseRuntimeV4  # noqa:E402
from research_entity.runtime.database_pulse_execution_plane_v5 import (  # noqa:E402
    DatabasePulseExecutionPlaneV5,
    PulseSpecV5,
)


def quantile(xs: list[float], p: float) -> float:
    ys = sorted(xs)
    return ys[min(len(ys)-1, max(0, math.ceil(p*len(ys))-1))]


def stats(xs: list[float]) -> dict[str, float | int]:
    return {
        "n": len(xs),
        "min_ms": round(min(xs), 6),
        "p50_ms": round(statistics.median(xs), 6),
        "p90_ms": round(quantile(xs, .90), 6),
        "p95_ms": round(quantile(xs, .95), 6),
        "p99_ms": round(quantile(xs, .99), 6),
        "max_ms": round(max(xs), 6),
        "mean_ms": round(statistics.mean(xs), 6),
    }


def timed(fn):
    t0=time.perf_counter_ns(); out=fn(); return out,(time.perf_counter_ns()-t0)/1_000_000.0


def db_bytes(ledger: StateLedger) -> int:
    page_size=int(ledger.conn.execute('PRAGMA page_size').fetchone()[0])
    pages=int(ledger.conn.execute('PRAGMA page_count').fetchone()[0])
    return page_size*pages


def seed(path: str, rows: int) -> StateLedger:
    ledger=StateLedger(path)
    ops=[
        {
            'op':'SET','domain':'memory','key':f'k{i:08d}',
            'value':{'i':i,'priority':0.0,'urgency':0.0,'salience':0.0,'novelty':0.0,'payload':'x'*24},
            'epistemic':'KNOWN','status':'CURRENT',
        }
        for i in range(rows)
    ]
    ops.append({
        'op':'SET','domain':'memory','key':'zzzz-critical',
        'value':{'priority':1.0,'urgency':1.0,'salience':1.0,'novelty':1.0},
        'epistemic':'KNOWN','status':'CURRENT',
    })
    ledger.append_event(
        event_id='seed',idem='seed',base_epoch=0,event_type='V5_BENCH_SEED',writer='benchmark',
        ops=ops,committed_at='2026-08-10T02:20:00Z',
    )
    return ledger


def semantic_v4_arm(path: str, rows: int, repeat: int) -> dict:
    ledger=seed(path,rows)
    runtime=DatabasePulseRuntimeV4(ledger)
    runtime.set_scheduler(
        enabled=True,event_id='v4-scheduler',base_epoch=ledger.epoch,
        actor='benchmark',reason='matched benchmark',committed_at='2026-08-10T02:20:01Z',
    )
    runtime.run_pulse(PulseSpec(
        'v4-warm',basis_epoch=ledger.epoch,source_domains=('memory',),
        max_candidates=64,max_focus=1,reentry_mode='NO_REENTRY',
    ),committed_at='2026-08-10T02:20:02Z')
    plane=UnifiedDBQueryPlane(ledger)
    prepared=plane.query(QuerySpec(
        'v4-prepared',domains=('memory',),limit=16,basis_epoch=ledger.epoch
    ))
    before_epoch=ledger.epoch
    before_bytes=db_bytes(ledger)
    lat=[]; focus_ok=True
    for i in range(repeat):
        out,ms=timed(lambda i=i: runtime.run_pulse(PulseSpec(
            f'v4-idle-{i}',basis_epoch=ledger.epoch,source_domains=('memory',),
            max_candidates=64,max_focus=1,reentry_mode='NO_REENTRY',
        )))
        lat.append(ms); focus_ok=focus_ok and out.focus_refs==('memory:zzzz-critical',)
    survives=True
    try:
        plane.select_for_assembly(prepared)
    except StaleEpoch:
        survives=False
    result={
        'idle_pulse':stats(lat),
        'semantic_epoch_advance_idle':ledger.epoch-before_epoch,
        'prepared_query_receipt_survived':survives,
        'tail_salience_focus_ok':focus_ok,
        'db_bytes_before_idle':before_bytes,
        'db_bytes_after_idle':db_bytes(ledger),
        'pulse_receipt_rows':int(ledger.conn.execute(
            "SELECT COUNT(*) FROM state WHERE domain='pulse'"
        ).fetchone()[0]),
    }
    ledger.close(); return result


def v5_arm(path: str, rows: int, repeat: int, catchup_batch: int) -> dict:
    ledger=seed(path,rows)
    runtime,init_ms=timed(lambda: DatabasePulseExecutionPlaneV5(
        ledger,now='2026-08-10T02:20:01Z'
    ))
    epoch=ledger.epoch; semantic_hash=ledger.semantic_state_hash; trace_hash=ledger.trace_root_hash
    first,first_ms=timed(lambda: runtime.run_pulse(PulseSpecV5(
        'v5-warm',basis_epoch=epoch,source_domains=('memory',),
        max_candidates=64,max_focus=1,max_source_events=catchup_batch,
        reentry_mode='NO_REENTRY',full_audit_every=1024,
    ),now='2026-08-10T02:20:02Z'))
    plane=UnifiedDBQueryPlane(ledger)
    prepared=plane.query(QuerySpec(
        'v5-prepared',domains=('memory',),limit=16,basis_epoch=ledger.epoch
    ))
    before_bytes=db_bytes(ledger)
    lat=[]; focus_ok=first.focus_refs==('memory:zzzz-critical',)
    for i in range(repeat):
        out,ms=timed(lambda i=i: runtime.run_pulse(PulseSpecV5(
            f'v5-idle-{i}',basis_epoch=epoch,source_domains=('memory',),
            max_candidates=64,max_focus=1,max_source_events=catchup_batch,
            reentry_mode='NO_REENTRY',full_audit_every=1024,
        ),now=f'v5-idle-{i}'))
        lat.append(ms)
        focus_ok=focus_ok and out.focus_refs==('memory:zzzz-critical',)
        if out.source_event_count or out.model_call_count or out.tool_call_count or out.effect_count:
            raise AssertionError('idle V5 invariant failed')
    survives=bool(plane.select_for_assembly(prepared)['selected'])
    idle_root_pass=(
        ledger.epoch==epoch and ledger.semantic_state_hash==semantic_hash and ledger.trace_root_hash==trace_hash
    )

    integrity=[]
    for _ in range(repeat):
        _,ms=timed(runtime._full_integrity); integrity.append(ms)

    # One semantic transaction, many ops: direct event count must remain one.
    big_ops=[
        {'op':'SET','domain':'memory','key':f'bulk-{i:04d}','value':{'priority':0.0},
         'epistemic':'KNOWN','status':'CURRENT'}
        for i in range(180)
    ]
    ledger.append_event(
        event_id='one-big',idem='one-big',base_epoch=ledger.epoch,event_type='BIG_TRANSACTION',
        writer='benchmark',ops=big_ops,committed_at='2026-08-10T02:20:03Z',
    )
    big_epoch=ledger.epoch
    big,big_ms=timed(lambda: runtime.run_pulse(PulseSpecV5(
        'v5-big',basis_epoch=big_epoch,source_domains=('memory',),
        max_candidates=64,max_focus=1,max_source_events=1,
        reentry_mode='NO_REENTRY',full_audit_every=1024,
    ),now='v5-big'))

    # Separate events exercise bounded event-wise catch-up/source hashes.
    event_hashes=[]; event_epochs=[]
    many_count=catchup_batch*2+17
    for i in range(many_count):
        ledger.append_event(
            event_id=f'many-{i:05d}',idem=f'many-{i:05d}',base_epoch=ledger.epoch,
            event_type='ONE_EVENT',writer='benchmark',
            ops=[{'op':'SET','domain':'memory','key':f'many-{i:05d}','value':{'priority':0.0},
                  'epistemic':'KNOWN','status':'CURRENT'}],
            committed_at=f'many-{i:05d}',
        )
        event_epochs.append(ledger.epoch)
        event_hashes.append(str(ledger.conn.execute(
            'SELECT semantic_state_hash FROM events WHERE event_id=?',(f'many-{i:05d}',)
        ).fetchone()[0]))
    final_epoch=ledger.epoch
    blocked=False
    try:
        runtime.run_pulse(PulseSpecV5(
            'must-block',basis_epoch=final_epoch,source_domains=('memory',),
            max_candidates=64,max_focus=1,max_source_events=catchup_batch,
            reentry_mode='NO_REENTRY',
        ),now='must-block')
    except Exception:
        blocked=True
    catch_lat=[]; applied=0; boundary_pass=True; observed=[]
    while runtime._pending_event_count()>catchup_batch:
        r,ms=timed(lambda: runtime.drain_source_events(
            invocation_id=f'catch-{len(catch_lat)}',basis_epoch=final_epoch,
            max_source_events=catchup_batch,now=f'catch-{len(catch_lat)}'
        ))
        catch_lat.append(ms); applied+=r.source_event_count
        boundary_pass=boundary_pass and r.source_epoch_after==event_epochs[applied-1]
        boundary_pass=boundary_pass and r.source_semantic_state_hash_after==event_hashes[applied-1]
        observed.append({
            'source_epoch':r.source_epoch_after,
            'source_hash':r.source_semantic_state_hash_after,
            'source_event_seq':r.source_event_seq_after,
        })
    final,final_ms=timed(lambda: runtime.run_pulse(PulseSpecV5(
        'post-catch',basis_epoch=final_epoch,source_domains=('memory',),
        max_candidates=64,max_focus=1,max_source_events=catchup_batch,
        reentry_mode='NO_REENTRY',
    ),now='post-catch'))
    boundary_pass=boundary_pass and final.source_epoch_after==final_epoch
    boundary_pass=boundary_pass and final.source_semantic_state_hash_after==ledger.semantic_state_hash

    result={
        'initialization_ms':round(init_ms,6),
        'first_pulse_ms':round(first_ms,6),
        'idle_pulse':stats(lat),
        'full_integrity_only':stats(integrity),
        'semantic_epoch_advance_idle':0 if idle_root_pass else ledger.epoch-epoch,
        'idle_semantic_root_pass':idle_root_pass,
        'prepared_query_receipt_survived':survives,
        'tail_salience_focus_ok':focus_ok,
        'db_bytes_before_idle':before_bytes,
        'db_bytes_after_idle':db_bytes(ledger),
        'u12_pulse_receipt_count_after_all':int(ledger.conn.execute(
            'SELECT COUNT(*) FROM frank_database_pulse_receipts'
        ).fetchone()[0]),
        'u12_duplicate_delta_rows':int(ledger.conn.execute(
            'SELECT COUNT(*) FROM frank_database_pulse_delta_queue'
        ).fetchone()[0]),
        'one_big_event':{
            'ops':180,'pulse_ms':round(big_ms,6),'source_event_count':big.source_event_count,
            'memory_update_observed_count':big.memory_update_observed_count,
            'source_epoch_after':big.source_epoch_after,'event_epoch':big_epoch,
        },
        'many_event_catchup':{
            'event_count':many_count,'cognition_blocked_before_catchup':blocked,
            'catchup_pulse_count':len(catch_lat),'catchup_latency':stats(catch_lat) if catch_lat else None,
            'applied_before_final':applied,'observed_boundaries':observed,
            'event_boundary_hash_pass':boundary_pass,
            'final_source_event_count':final.source_event_count,
            'final_backlog':final.backlog_events_after,
            'final_pulse_ms':round(final_ms,6),
        },
    }
    ledger.close(); return result


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--rows',default='100,1000,10000')
    ap.add_argument('--repeat',type=int,default=7)
    ap.add_argument('--catchup-batch',type=int,default=16)
    ap.add_argument('--output')
    a=ap.parse_args(); repeat=max(1,min(30,a.repeat)); batch=max(4,min(256,a.catchup_batch))
    sizes=[int(x) for x in a.rows.split(',') if x.strip()]
    results=[]
    for rows in sizes:
        with tempfile.TemporaryDirectory() as td:
            v4=semantic_v4_arm(str(Path(td)/'v4.sqlite'),rows,repeat)
            v5=v5_arm(str(Path(td)/'v5.sqlite'),rows,repeat,batch)
        results.append({
            'rows':rows,
            'semantic_stateledger_pulse_v4':v4,
            'direct_event_execution_pulse_v5':v5,
            'v5_vs_v4_idle_p50_ratio':round(
                float(v5['idle_pulse']['p50_ms'])/max(float(v4['idle_pulse']['p50_ms']),1e-12),6
            ),
            'h1_no_semantic_self_churn':v5['idle_semantic_root_pass'],
            'h2_query_receipt_survives':v5['prepared_query_receipt_survived'] and not v4['prepared_query_receipt_survived'],
            'h3_one_transaction_one_source_event':(
                v5['one_big_event']['source_event_count']==1
                and v5['one_big_event']['memory_update_observed_count']==180
                and v5['u12_duplicate_delta_rows']==0
            ),
            'h4_event_boundary_hash_pass':v5['many_event_catchup']['event_boundary_hash_pass'],
        })
    ru=resource.getrusage(resource.RUSAGE_SELF)
    payload={
        'schema_version':'1.0',
        'benchmark_class':'CLAY_SELF_USE_ENGINEERING_DIFFERENTIAL',
        'implementation':'database_pulse_execution_plane_v5_direct_stateledger_events',
        'results':results,
        'runtime_metadata':{
            'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform(),
            'machine':platform.machine(),'pid':os.getpid(),'ru_maxrss':ru.ru_maxrss,
        },
        'limitations':[
            'Synthetic StateLedger fixture; not live-FRANK task accuracy or final Harness acceptance.',
            'Comparator is the current project semantic Pulse V4, not an external database product.',
            'V5 default rank policy remains online while compile economics are unmeasured; adaptive rank compilation is tested separately on main.',
            'Full root audit remains required on semantic changes and periodically on idle Pulses; its scaling cost is reported separately.',
            'Hostinger Ubuntu evidence is preliminary and cannot replace Andreas target-system acceptance.',
        ],
    }
    text=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
    print(text,end='')

if __name__=='__main__': main()
