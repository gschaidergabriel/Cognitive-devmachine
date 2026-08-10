#!/usr/bin/env python3
"""Synthetic U11 full-generation row-copy vs real U12+U13 incremental Pulse benchmark.
Engineering proxy only; not a universal database benchmark and not live-FRANK outcome evidence.
The expensive possibility/graph recompilation itself is deliberately excluded and reported as a
separate downstream cost obligation.
"""
from __future__ import annotations
import json, sqlite3, statistics, time
from pathlib import Path
from database_pulse_v0 import DatabasePulseV0
HERE=Path(__file__).resolve().parent
U11=(HERE/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text()
U12=(HERE/'RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql').read_text()
U13=(HERE/'RAE_UNIFIEDDB_V13_PULSE_INCREMENTAL_ACCESS.sql').read_text()
N=2000; PATHS=8; CHANGED=20; REPEATS=9

def pct(xs,p):
    s=sorted(xs); return s[min(len(s)-1,max(0,int(round((len(s)-1)*p))))]

def build():
    c=sqlite3.connect(':memory:'); c.executescript(U11); c.executescript(U12); c.executescript(U13)
    pulse=DatabasePulseV0(c); pulse.bootstrap(entity_id='frank',lineage_id='bench-lineage',source_epoch=1,graph_epoch=1,now='boot')
    c.execute("INSERT INTO semantic_access_generations VALUES('g1',1,1,'bench','h',?,?, '{}','VERIFIED','t','t',NULL)",(N,N*PATHS))
    paths=[]; deps=[]; heads=[]
    for i in range(N):
        s=f's{i}'; heads.append((s,'g1','COMPLETE','CURRENT',1,1,None,None,None,'bench-head','t')); deps.append(('g1',s,f'semantic:{s}','SEMANTIC','h',1))
        for j in range(PATHS): paths.append(('g1',s,f'r-{s}-{j}',f'l-{s}-{j}',j+1,1,1/(j+1),0.0,'{}'))
    c.executemany("INSERT INTO semantic_access_projection_v11 VALUES(?,?,?,?,?,?,?,?,?)",paths)
    c.executemany("INSERT INTO semantic_access_seed_dependencies_v13 VALUES(?,?,?,?,?,?)",deps)
    c.executemany("INSERT INTO semantic_access_seed_heads_v13 VALUES(?,?,?,?,?,?,?,?,?,?,?)",heads); c.commit(); return c,pulse

def main():
    u11=[]; admission=[]; u13=[]
    for rep in range(REPEATS):
        c,pulse=build(); c.execute("CREATE TEMP TABLE fullcopy AS SELECT * FROM semantic_access_projection_v11 WHERE 0")
        t=time.perf_counter_ns(); c.execute("INSERT INTO fullcopy SELECT * FROM semantic_access_projection_v11 WHERE generation_id='g1'"); c.commit(); u11.append((time.perf_counter_ns()-t)/1e6)
        t=time.perf_counter_ns()
        for i in range(CHANGED):
            pulse.admit_delta(delta_id=f'd{i}',changed_ref=f'semantic:s{i}',reason_class='STATE_UPDATE',payload={'v':2},source_epoch=2,graph_epoch=1,now='admit')
        admission.append((time.perf_counter_ns()-t)/1e6)
        t=time.perf_counter_ns(); receipt=pulse.pulse(max_deltas=CHANGED,now='pulse',model_call_count=0); u13.append((time.perf_counter_ns()-t)/1e6)
        if receipt.applied_delta_count!=CHANGED or receipt.model_call_count!=0: raise AssertionError(receipt)
        stale=c.execute("SELECT count(*) FROM semantic_access_seed_heads_v13 WHERE status='STALE'").fetchone()[0]
        invalid=c.execute("SELECT count(*) FROM semantic_access_seed_invalidations_v13").fetchone()[0]
        if stale!=CHANGED or invalid!=CHANGED: raise AssertionError((stale,invalid))
        if c.execute("SELECT count(*) FROM semantic_access_seed_heads_v13 WHERE status='CURRENT'").fetchone()[0] != N-CHANGED: raise AssertionError('unaffected heads lost')
        c.close()
    result={'schema':'clay.database_pulse_incremental_access.v13.benchmark',
      'scope':'synthetic deterministic update-amplification proxy using real DatabasePulseV0; excludes expensive possibility/graph recompilation and does not prove universal DB superiority',
      'dataset':{'seeds':N,'paths_per_seed':PATHS,'path_rows':N*PATHS,'changed_seeds':CHANGED,'changed_fraction':CHANGED/N,'repeats':REPEATS},
      'u11_full_generation_row_copy_proxy':{'path_rows_rewritten':N*PATHS,'median_ms':statistics.median(u11),'p95_ms':pct(u11,.95),'runs_ms':u11},
      'u12_delta_admission_20':{'median_ms':statistics.median(admission),'p95_ms':pct(admission,.95),'runs_ms':admission},
      'u13_real_zero_model_pulse':{'seed_heads_invalidated':CHANGED,'unaffected_seed_heads_carried':N-CHANGED,'path_rows_requiring_recompile':CHANGED*PATHS,
        'path_recompile_reduction_x':N/CHANGED,'median_ms':statistics.median(u13),'p95_ms':pct(u13,.95),'runs_ms':u13},
      'interpretation':'U13 targets downstream compile/rebuild amplification, not raw SQLite row-copy dominance. The U11 copy proxy may be faster than Pulse control at small scales; the decisive later metric is avoided possibility/graph compilation under real change locality.'}
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
