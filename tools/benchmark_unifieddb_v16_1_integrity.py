#!/usr/bin/env python3
from __future__ import annotations
import json, math, statistics, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'research_entity'/'runtime'
sys.path.insert(0,str(RUNTIME))
from semantic_access_pulse_v12 import AccessPath, PulsePlan, SegmentedPulseProjection  # noqa:E402
from semantic_access_pulse_v16_1_integrity import IntegrityGuardedSegmentedPulseProjection  # noqa:E402

SEEDS=[f'seed:{c}:{i}' for c in range(20) for i in range(5)]
VERSIONS={s:0 for s in SEEDS}

def paths_for(seed):
    _,cluster,_=seed.split(':'); v=VERSIONS[seed]
    deps=(seed,f'cluster:{cluster}',f'service:{cluster}',f'resource:{cluster}')
    return [
        AccessPath(f'rec:{seed}:svc:v{v}',f'service:{cluster}',1,1,1.0+v/1000,dependencies=deps),
        AccessPath(f'rec:{seed}:res:v{v}',f'resource:{cluster}',2,2,.8+v/1000,dependencies=deps),
        AccessPath(f'rec:{seed}:aux:v{v}',f'aux:{cluster}',3,2,.6+v/1000,dependencies=deps+(f'aux:{cluster}',)),
        AccessPath(f'rec:{seed}:far:v{v}',f'far:{cluster}',4,3,.4+v/1000,dependencies=deps+(f'far:{cluster}',)),
    ]

def q(xs,p):
    ys=sorted(xs); return ys[min(len(ys)-1,max(0,math.ceil(p*len(ys))-1))]
def stats(xs): return {'n':len(xs),'p50_ms':statistics.median(xs),'p95_ms':q(xs,.95),'min_ms':min(xs),'max_ms':max(xs)}

def run(cls,label):
    for s in VERSIONS: VERSIONS[s]=0
    t=time.perf_counter_ns(); x=cls(); x.bootstrap(event_id='boot',source_epoch=1,graph_epoch=1,seeds=SEEDS,recompute_seed=paths_for); bootstrap=(time.perf_counter_ns()-t)/1e6
    query=[]
    for i in range(1000):
        seed=SEEDS[i%len(SEEDS)]; t=time.perf_counter_ns(); x.query(seed,limit=4); query.append((time.perf_counter_ns()-t)/1e6)
    impacted=tuple(f'seed:7:{i}' for i in range(5))
    for s in impacted: VERSIONS[s]=1
    t=time.perf_counter_ns(); r=x.apply_pulse(PulsePlan('local','VALUE_UPDATE',('cluster:7',),impacted,True,2,1),recompute_seed=paths_for,recompute_all_seeds=lambda:SEEDS,incremental_fraction_limit=.25); pulse=(time.perf_counter_ns()-t)/1e6
    out={'label':label,'bootstrap_ms':bootstrap,'query':stats(query),'local_pulse_ms':pulse,'mode':r.mode,'reused_segments':r.reused_segment_count,'new_segments':r.new_segment_count,'storage':x.storage_counts()}
    if isinstance(x,IntegrityGuardedSegmentedPulseProjection):
        seed='seed:3:0'; head=x._head(); seg=x.con.execute("SELECT segment_id FROM access_generation_seed WHERE generation_id=? AND seed_id=?",(head['generation_id'],seed)).fetchone()[0]
        x.con.execute("DELETE FROM access_segment_dependency WHERE segment_id=? AND dependency_logical_id='cluster:3'",(seg,)); x.con.commit()
        t=time.perf_counter_ns(); rr=x.apply_pulse(PulsePlan('repair','VALUE_UPDATE',('cluster:8',),tuple(f'seed:8:{i}' for i in range(5)),True,3,1),recompute_seed=paths_for,recompute_all_seeds=lambda:SEEDS,incremental_fraction_limit=.25); repair=(time.perf_counter_ns()-t)/1e6
        out['tamper_repair_ms']=repair; out['tamper_repair_mode']=rr.mode; out['post_repair_integrity']=x.integrity_state(); out['post_repair_audit']=x.deep_verify_current()
    x.close(); return out

def main():
    base=[]; guard=[]
    for _ in range(7): base.append(run(SegmentedPulseProjection,'v16-base')); guard.append(run(IntegrityGuardedSegmentedPulseProjection,'v16.1-integrity'))
    result={
      'schema':'clay.unifieddb.v16_1.integrity.benchmark.v1',
      'scope':'synthetic engineering proxy; not live Frank outcome evidence',
      'fixture':{'seeds':len(SEEDS),'paths_per_seed':4,'queries_per_run':1000,'repeats':7,'local_changed_seeds':5},
      'v16_base':{'bootstrap_ms':stats([x['bootstrap_ms'] for x in base]),'query_ms':stats([x['query']['p50_ms'] for x in base]),'local_pulse_ms':stats([x['local_pulse_ms'] for x in base])},
      'v16_1_guard':{'bootstrap_ms':stats([x['bootstrap_ms'] for x in guard]),'query_ms':stats([x['query']['p50_ms'] for x in guard]),'local_pulse_ms':stats([x['local_pulse_ms'] for x in guard]),'tamper_repair_ms':stats([x['tamper_repair_ms'] for x in guard])},
      'ratios':{
        'query_p50_guard_over_base':statistics.median([x['query']['p50_ms'] for x in guard])/statistics.median([x['query']['p50_ms'] for x in base]),
        'local_pulse_p50_guard_over_base':statistics.median([x['local_pulse_ms'] for x in guard])/statistics.median([x['local_pulse_ms'] for x in base]),
        'bootstrap_p50_guard_over_base':statistics.median([x['bootstrap_ms'] for x in guard])/statistics.median([x['bootstrap_ms'] for x in base]),
      },
      'all_guard_repairs_full_fallback':all(x['tamper_repair_mode']=='FULL_FALLBACK' for x in guard),
      'all_guard_post_repair_clean':all(x['post_repair_integrity']['status']=='CLEAN' and x['post_repair_audit']['verified'] for x in guard),
      'limitations':['Integrity verification deliberately adds segment-local query work; the ratio is a promotion cost, not a hidden detail.','Fixture uses in-memory SQLite and deterministic synthetic locality.','Real Frank dependency fan-out, filesystem I/O, WAL concurrency, RSS and downstream cognition remain separate gates.'],
    }
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
