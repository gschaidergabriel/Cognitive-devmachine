#!/usr/bin/env python3
"""Synthetic U11 full-generation rewrite vs U13 Pulse dependency invalidation benchmark.
Engineering proxy only; not a universal database benchmark and not live-FRANK outcome evidence.
"""
from __future__ import annotations
import json, sqlite3, statistics, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
U11=(HERE/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text()
U12=(HERE/'RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql').read_text()
U13=(HERE/'RAE_UNIFIEDDB_V13_PULSE_INCREMENTAL_ACCESS.sql').read_text()
N=2000; PATHS=8; CHANGED=20; REPEATS=9

def pct(xs,p):
    s=sorted(xs); return s[min(len(s)-1,max(0,int(round((len(s)-1)*p))))]

def build():
    c=sqlite3.connect(':memory:'); c.executescript(U11); c.executescript(U12); c.executescript(U13)
    c.execute("INSERT INTO frank_database_pulse_state VALUES(1,'frank','lineage','PULSING',0,0,0,0,1,1,NULL,'{}','h','t')")
    c.execute("INSERT INTO semantic_access_generations VALUES('g1',1,1,'bench','h',?,?, '{}','VERIFIED','t','t',NULL)",(N,N*PATHS))
    paths=[]; deps=[]; heads=[]
    for i in range(N):
        s=f's{i}'; heads.append((s,'g1','COMPLETE','CURRENT',1,1,None,None,None,'h','t')); deps.append(('g1',s,f'semantic:{s}','SEMANTIC','h',1))
        for j in range(PATHS): paths.append(('g1',s,f'r-{s}-{j}',f'l-{s}-{j}',j+1,1,1/(j+1),0.0,'{}'))
    c.executemany("INSERT INTO semantic_access_projection_v11 VALUES(?,?,?,?,?,?,?,?,?)",paths)
    c.executemany("INSERT INTO semantic_access_seed_dependencies_v13 VALUES(?,?,?,?,?,?)",deps)
    c.executemany("INSERT INTO semantic_access_seed_heads_v13 VALUES(?,?,?,?,?,?,?,?,?,?,?)",heads); c.commit(); return c

def main():
    u11=[]; u13=[]
    for rep in range(REPEATS):
        c=build(); c.execute("CREATE TEMP TABLE fullcopy AS SELECT * FROM semantic_access_projection_v11 WHERE 0")
        t=time.perf_counter_ns(); c.execute("INSERT INTO fullcopy SELECT * FROM semantic_access_projection_v11 WHERE generation_id='g1'"); c.commit(); u11.append((time.perf_counter_ns()-t)/1e6)
        for i in range(CHANGED): c.execute("INSERT INTO frank_database_pulse_delta_queue(delta_id,changed_ref,reason_class,payload_clay,payload_hash,source_epoch,graph_epoch,admitted_at) VALUES(?,?,?,?,?,?,?,?)",(f'd{i}',f'semantic:s{i}','STATE_UPDATE','{}','h',2,1,'t'))
        c.commit(); t=time.perf_counter_ns();
        c.execute('BEGIN')
        for i in range(CHANGED): c.execute("UPDATE frank_database_pulse_delta_queue SET applied_pulse_id='p1' WHERE delta_id=?",(f'd{i}',))
        c.execute("UPDATE frank_database_pulse_state SET source_epoch=2,pulse_count=1 WHERE singleton_id=1"); c.commit(); u13.append((time.perf_counter_ns()-t)/1e6)
        stale=c.execute("SELECT count(*) FROM semantic_access_seed_heads_v13 WHERE status='STALE'").fetchone()[0]
        if stale!=CHANGED: raise AssertionError(stale)
    result={'schema':'clay.database_pulse_incremental_access.v13.benchmark','scope':'synthetic deterministic update-amplification proxy; excludes expensive possibility compilation and does not prove universal DB superiority',
      'dataset':{'seeds':N,'paths_per_seed':PATHS,'path_rows':N*PATHS,'changed_seeds':CHANGED,'changed_fraction':CHANGED/N,'repeats':REPEATS},
      'u11_full_generation_copy':{'path_rows_rewritten':N*PATHS,'median_ms':statistics.median(u11),'p95_ms':pct(u11,.95),'runs_ms':u11},
      'u13_pulse_invalidation':{'seed_heads_invalidated':CHANGED,'unaffected_seed_heads_carried':N-CHANGED,'path_rows_requiring_recompile':CHANGED*PATHS,'path_recompile_reduction_x':N/CHANGED,'median_ms':statistics.median(u13),'p95_ms':pct(u13,.95),'runs_ms':u13},
      'interpretation':'U13 targets compile/rebuild amplification. SQLite bulk INSERT SELECT may still be faster than Python/trigger control at small scales; report both rather than claiming latency dominance.'}
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
