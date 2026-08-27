#!/usr/bin/env python3
from __future__ import annotations

"""Differential engineering benchmark for U12 segmented pulse vs U11-style full generations.

Synthetic deterministic scope only. It measures update amplification, coherent snapshot
equivalence and hot-read overhead. It is not universal database superiority and not live
FRANK outcome evidence.
"""
import argparse
import json
import math
import os
import platform
import random
import sqlite3
import statistics
import tempfile
import time
from pathlib import Path

from semantic_access_pulse_v12 import AccessPath, PulsePlan, SegmentedPulseProjection

def p95(xs):
    xs=sorted(xs)
    return xs[min(len(xs)-1,max(0,math.ceil(.95*len(xs))-1))] if xs else 0.0

class FullGenerationBaseline:
    def __init__(self,path):
        self.con=sqlite3.connect(path)
        self.con.execute("""
          CREATE TABLE generation(id INTEGER PRIMARY KEY,source_epoch INTEGER,graph_epoch INTEGER,current INTEGER)
        """)
        self.con.execute("""
          CREATE TABLE path(gen INTEGER,seed TEXT,target TEXT,target_logical TEXT,rank INTEGER,hop INTEGER,
                            weight REAL,authority REAL,path_clay TEXT,PRIMARY KEY(gen,seed,target))
        """)
        self.con.execute("CREATE INDEX path_hot ON path(gen,seed,rank,weight DESC,target)")
        self.gen=0
    def publish(self,source_epoch,graph_epoch,seeds,recompute_seed):
        t0=time.perf_counter_ns()
        self.gen += 1
        g=self.gen
        self.con.execute("BEGIN IMMEDIATE")
        try:
            self.con.execute("UPDATE generation SET current=0 WHERE current=1")
            self.con.execute("INSERT INTO generation VALUES(?,?,?,1)",(g,source_epoch,graph_epoch))
            rows=[]
            for seed in seeds:
                for p in recompute_seed(seed):
                    rows.append((g,seed,p.target_record_id,p.target_logical_id,p.path_rank,p.hop_count,p.path_weight,p.authority_rank,p.path_clay))
            self.con.executemany("INSERT INTO path VALUES(?,?,?,?,?,?,?,?,?)",rows)
            self.con.commit()
        except Exception:
            self.con.rollback(); raise
        return (time.perf_counter_ns()-t0)/1e6,len(rows)
    def query(self,seed,k=20):
        return tuple(r[0] for r in self.con.execute(
            "SELECT target FROM path WHERE gen=? AND seed=? ORDER BY rank,weight DESC,authority DESC,target LIMIT ?",
            (self.gen,seed,k)
        ))
    def snapshot(self):
        return list(self.con.execute(
            "SELECT seed,target,target_logical,rank,hop,round(weight,12),round(authority,12),path_clay FROM path WHERE gen=? ORDER BY seed,rank,target",
            (self.gen,)
        ))
    def counts(self):
        return {"generations":self.con.execute("SELECT count(*) FROM generation").fetchone()[0],
                "path_rows":self.con.execute("SELECT count(*) FROM path").fetchone()[0]}
    def close(self): self.con.close()

def make_model(seed_count=1200,cluster_count=60,paths_per_seed=20):
    seeds=[f"seed:{i:05d}" for i in range(seed_count)]
    cluster={s:i%cluster_count for i,s in enumerate(seeds)}
    versions={s:0 for s in seeds}
    def recompute(seed):
        c=cluster[seed]; v=versions[seed]
        dep_root=f"cluster:{c:03d}"
        out=[]
        for r in range(1,paths_per_seed+1):
            target_logical=f"node:{c:03d}:{r:03d}"
            target=f"rec:{seed}:v{v}:r{r:03d}"
            # deterministic compute shadow approximates relation/path proof assembly
            h=hash((seed,v,r,c)) & 0xffff
            weight=1.0/(1+r*.05)+(h%97)*1e-7
            deps=(seed,dep_root,target_logical,f"policy:{r%5}")
            out.append(AccessPath(target,target_logical,r,min(3,(r-1)//7+1),weight,0.1*(r%3),dependencies=deps))
        return out
    return seeds,cluster,versions,recompute

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seeds",type=int,default=1200)
    ap.add_argument("--clusters",type=int,default=60)
    ap.add_argument("--paths",type=int,default=20)
    ap.add_argument("--events",type=int,default=12)
    ap.add_argument("--query-repeats",type=int,default=500)
    ap.add_argument("--output")
    args=ap.parse_args()
    seeds,cluster,versions,recompute=make_model(args.seeds,args.clusters,args.paths)
    rng=random.Random(73419)
    with tempfile.TemporaryDirectory() as td:
        pulse=SegmentedPulseProjection(os.path.join(td,"pulse.sqlite"))
        full=FullGenerationBaseline(os.path.join(td,"full.sqlite"))
        t0=time.perf_counter_ns()
        boot=pulse.bootstrap(event_id="boot",source_epoch=1,graph_epoch=1,seeds=seeds,recompute_seed=recompute)
        pulse_boot_ms=(time.perf_counter_ns()-t0)/1e6
        full_boot_ms,full_boot_rows=full.publish(1,1,seeds,recompute)
        if pulse.snapshot()!=full.snapshot():
            raise AssertionError("bootstrap snapshots differ")

        local_rows=[]
        source_epoch=1
        graph_epoch=1
        for e in range(args.events):
            c=e % args.clusters
            impacted=[s for s in seeds if cluster[s]==c]
            for s in impacted: versions[s]+=1
            source_epoch += 1
            t0=time.perf_counter_ns()
            receipt=pulse.apply_pulse(
                PulsePlan(f"local-{e}","VALUE_UPDATE",(f"cluster:{c:03d}",),tuple(impacted),True,source_epoch,graph_epoch),
                recompute_seed=recompute,recompute_all_seeds=lambda:seeds,incremental_fraction_limit=.25,
            )
            pulse_ms=(time.perf_counter_ns()-t0)/1e6
            full_ms,rows=full.publish(source_epoch,graph_epoch,seeds,recompute)
            equal=pulse.snapshot()==full.snapshot()
            if not equal:
                raise AssertionError(f"snapshot mismatch after local event {e}")
            local_rows.append({
                "event":e,"impacted_seeds":len(impacted),"affected_fraction":receipt.affected_fraction,
                "mode":receipt.mode,"pulse_ms":pulse_ms,"full_ms":full_ms,
                "speedup":full_ms/pulse_ms if pulse_ms else None,
                "new_segments":receipt.new_segment_count,"new_paths":receipt.new_path_count,
                "full_path_rows_written":rows,"exact_snapshot_equal":equal,
            })

        # Unknown topology expansion must not take the incremental path.
        graph_epoch += 1
        topology_receipt=pulse.apply_pulse(
            PulsePlan("topology-add","TOPOLOGY_ADD",("new:edge",),(),False,source_epoch,graph_epoch),
            recompute_seed=recompute,recompute_all_seeds=lambda:seeds,incremental_fraction_limit=.25,
        )
        full.publish(source_epoch,graph_epoch,seeds,recompute)
        if pulse.snapshot()!=full.snapshot():
            raise AssertionError("topology fallback snapshot mismatch")

        # Last-known-good recovery: injected failure must leave head and snapshot unchanged.
        before_basis=pulse.head_basis(); before_hash=hash(tuple(pulse.snapshot()))
        bad_seed=seeds[0]
        versions[bad_seed]+=1
        source_epoch += 1
        recovery_preserved=False
        try:
            pulse.apply_pulse(
                PulsePlan("injected-failure","VALUE_UPDATE",(bad_seed,),(bad_seed,),True,source_epoch,graph_epoch),
                recompute_seed=lambda s: (_ for _ in ()).throw(RuntimeError("injected")) if s==bad_seed else recompute(s),
                recompute_all_seeds=lambda:seeds,
            )
        except RuntimeError:
            recovery_preserved=(pulse.head_basis()==before_basis and hash(tuple(pulse.snapshot()))==before_hash)
        versions[bad_seed]-=1
        if not recovery_preserved:
            raise AssertionError("last-known-good head changed after injected failure")

        sample=[seeds[rng.randrange(len(seeds))] for _ in range(args.query_repeats)]
        q_pulse=[]; q_full=[]
        for s in sample:
            t=time.perf_counter_ns(); a=pulse.query(s,args.paths); q_pulse.append((time.perf_counter_ns()-t)/1e6)
            t=time.perf_counter_ns(); b=full.query(s,args.paths); q_full.append((time.perf_counter_ns()-t)/1e6)
            if a!=b: raise AssertionError("read mismatch")

        out={
            "schema":"clay.unifieddb_pulse_v12.benchmark.v1",
            "truth_class":"LOCAL_OR_RUNNER_SYNTHETIC_ENGINEERING_ONLY",
            "dataset":{"seeds":args.seeds,"clusters":args.clusters,"paths_per_seed":args.paths,"local_events":args.events},
            "bootstrap":{"pulse_ms":round(pulse_boot_ms,3),"full_ms":round(full_boot_ms,3),"full_path_rows":full_boot_rows},
            "local_events":local_rows,
            "summary":{
                "pulse_local_p50_ms":round(statistics.median(r["pulse_ms"] for r in local_rows),3),
                "pulse_local_p95_ms":round(p95([r["pulse_ms"] for r in local_rows]),3),
                "full_local_p50_ms":round(statistics.median(r["full_ms"] for r in local_rows),3),
                "full_local_p95_ms":round(p95([r["full_ms"] for r in local_rows]),3),
                "median_update_speedup":round(statistics.median(r["speedup"] for r in local_rows),3),
                "exact_snapshot_fraction":sum(r["exact_snapshot_equal"] for r in local_rows)/len(local_rows),
                "topology_add_mode":topology_receipt.mode,
                "recovery_preserved":recovery_preserved,
                "pulse_query_p50_ms":round(statistics.median(q_pulse),4),
                "pulse_query_p95_ms":round(p95(q_pulse),4),
                "full_query_p50_ms":round(statistics.median(q_full),4),
                "full_query_p95_ms":round(p95(q_full),4),
                "query_join_overhead_p50_ms":round(statistics.median(q_pulse)-statistics.median(q_full),4),
            },
            "storage":{"pulse":pulse.storage_counts(),"full":full.counts()},
            "metadata":{
                "python":platform.python_version(),"sqlite":sqlite3.sqlite_version,
                "platform":platform.platform(),"machine":platform.machine(),
            },
            "limitations":[
                "Synthetic clustered topology is deliberately locality-friendly; real Clay/FRANK fan-out is not yet measured.",
                "Path compilation is deterministic Python proxy work; no downstream model outcome is measured.",
                "The benchmark compares physical full-generation copying with segmented copy-on-write; it does not compare all databases.",
                "Topology additions with incomplete impact closure intentionally fall back to full rebuild.",
            ],
        }
        text=json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
        if args.output:
            Path(args.output).write_text(text,encoding="utf-8")
        print(text,end="")
        pulse.close(); full.close()

if __name__=="__main__":
    main()
