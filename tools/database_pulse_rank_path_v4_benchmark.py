#!/usr/bin/env python3
from __future__ import annotations

"""Measure hidden cold-build cost eliminated by adaptive Pulse rank path V4.

Matched arms use identical authoritative StateLedger semantic content and identical SCORE_EXPR
candidate ordering. V3 forces index creation before selection. V4-sparse keeps the correct
online ordered scan because Pulse lifetime history is insufficient. V4-stable later admits the
index only when U16 economics say the conservative horizon amortizes it.
"""

import argparse, json, math, statistics, sys, time
from pathlib import Path
from typing import Callable, Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger  # noqa:E402
from research_entity.runtime.database_pulse_rank_index_v3 import AuthoritativeRankIndexV3  # noqa:E402
from research_entity.runtime.database_pulse_rank_path_v4 import AdaptiveAuthoritativeRankPathV4  # noqa:E402
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics  # noqa:E402
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime  # noqa:E402


def quantile(xs,p):
    ys=sorted(xs); return ys[min(len(ys)-1,max(0,math.ceil(p*len(ys))-1))] if ys else 0.0

def stats(xs):
    return {"n":len(xs),"min_ms":round(min(xs),6),"p50_ms":round(statistics.median(xs),6),
            "p90_ms":round(quantile(xs,.9),6),"p95_ms":round(quantile(xs,.95),6),
            "p99_ms":round(quantile(xs,.99),6),"max_ms":round(max(xs),6),"mean_ms":round(statistics.mean(xs),6)}

def timed(fn:Callable[[],Any]):
    t=time.perf_counter_ns(); out=fn(); return out,(time.perf_counter_ns()-t)/1_000_000.0


def seed_events(rows:int):
    ledger=StateLedger(); ops=[]
    for i in range(rows):
        ops.append({"op":"SET","domain":"memory","key":f"k{i:06d}",
                    "value":{"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0,"fact":i},
                    "epistemic":"KNOWN","status":"CURRENT"})
    ops.append({"op":"SET","domain":"memory","key":"zzzzzz-critical",
                "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                "epistemic":"KNOWN","status":"CURRENT"})
    ledger.append_event(event_id="seed",idem="seed",base_epoch=ledger.epoch,event_type="V4_BENCH_SEED",
                        writer="benchmark",ops=ops,committed_at="2026-08-10T02:20:00Z")
    events=ledger.export_events(); ledger.close(); return events


def economics(build_us:float,online_us:float,compiled_us:float):
    return CompileEconomics(build_cost_us=build_us,online_query_us=online_us,compiled_query_us=compiled_us,
                            online_quality=1.0,compiled_quality=1.0,expected_reads_before_invalidation=0.0,safety_factor=1.2)


def bench(rows:int,repeats:int,budget:int):
    events=seed_events(rows); target="memory:zzzzzz-critical"

    # Arm 1: current V3 hidden cold build.
    l3=StateLedger.replay(events); v3=AuthoritativeRankIndexV3(l3)
    try:
        first3,first3_ms=timed(lambda:v3.select(source_domains=("memory",),basis_epoch=l3.epoch,max_candidates=budget,max_focus=1))
        hot3=[]
        for _ in range(repeats):
            _,ms=timed(lambda:v3.select(source_domains=("memory",),basis_epoch=l3.epoch,max_candidates=budget,max_focus=1)); hot3.append(ms)
    finally: l3.close()

    # Arm 2: V4 with insufficient history must remain uncompiled yet correct.
    l4=StateLedger.replay(events); v4=AdaptiveAuthoritativeRankPathV4(l4)
    sparse=[EpochReadLifetime(1,50),EpochReadLifetime(2,50)]
    # Initial economics here are intentionally only a routing placeholder; sparse history is the gate.
    provisional=economics(1000.0,100.0,10.0)
    try:
        first4,first4_ms=timed(lambda:v4.select(source_domains=("memory",),basis_epoch=l4.epoch,max_candidates=budget,max_focus=1,
                                              economics_without_horizon=provisional,pulse_history=sparse))
        online=[]
        for _ in range(repeats):
            _,ms=timed(lambda:v4.select(source_domains=("memory",),basis_epoch=l4.epoch,max_candidates=budget,max_focus=1,
                                           economics_without_horizon=provisional,pulse_history=sparse)); online.append(ms)

        # Measure real build and compiled hot costs on a matched clone, then use those measured
        # values to decide a later stable-horizon admission instead of inventing economics.
        m=StateLedger.replay(events); vm=AuthoritativeRankIndexV3(m)
        try:
            _,build_ms=timed(vm.ensure_index)
            compiled=[]
            for _ in range(repeats):
                _,ms=timed(lambda:vm.select(source_domains=("memory",),basis_epoch=m.epoch,max_candidates=budget,max_focus=1)); compiled.append(ms)
        finally: m.close()
        online_stats=stats(online); compiled_stats=stats(compiled)
        measured=economics(build_ms*1000.0,online_stats["p50_ms"]*1000.0,compiled_stats["p50_ms"]*1000.0)
        stable_reads=max(10000,int((build_ms*1000.0/max(1e-9,(online_stats["p50_ms"]-compiled_stats["p50_ms"])*1000.0))*2)+10)
        stable=[EpochReadLifetime(i,stable_reads) for i in range(8)]
        admitted,admitted_ms=timed(lambda:v4.select(source_domains=("memory",),basis_epoch=l4.epoch,max_candidates=budget,max_focus=1,
                                                   economics_without_horizon=measured,pulse_history=stable))
        post=[]
        for _ in range(repeats):
            _,ms=timed(lambda:v4.select(source_domains=("memory",),basis_epoch=l4.epoch,max_candidates=budget,max_focus=1,
                                           economics_without_horizon=measured,pulse_history=stable)); post.append(ms)
        return {
            "schema_version":"1.0","benchmark_class":"PULSE_ADAPTIVE_RANK_COMPILE_V4_ENGINEERING_PROXY",
            "fixture":{"authoritative_rows":rows+1,"candidate_budget":budget,"repeats":repeats,"target":target},
            "correctness":{"v3_first_focus":first3.focus_refs[0],"v4_sparse_first_focus":first4.focus_refs[0],
                           "v4_admitted_focus":admitted.focus_refs[0],"all_correct":all(x==target for x in [first3.focus_refs[0],first4.focus_refs[0],admitted.focus_refs[0]])},
            "v3_forced_index":{"cold_first_select_ms":round(first3_ms,6),"hot_select":stats(hot3)},
            "v4_sparse_history":{"cold_first_select_ms":round(first4_ms,6),"online_select":online_stats,
                                 "physical_mode":first4.physical_mode,"index_built":first4.index_present_after,
                                 "horizon_status":first4.horizon_status},
            "measured_index_economics":{"build_ms":round(build_ms,6),"compiled_select":compiled_stats,
                                        "online_p50_ms":online_stats["p50_ms"],"compiled_p50_ms":compiled_stats["p50_ms"],
                                        "stable_history_reads":stable_reads},
            "v4_stable_history_admission":{"admission_call_ms":round(admitted_ms,6),"physical_mode":admitted.physical_mode,
                                           "index_present_after":admitted.index_present_after,"compile_reason":admitted.compile_reason,
                                           "guarded_break_even_reads":admitted.guarded_break_even_reads,"hot_after_admission":stats(post)},
            "cold_latency_delta_ms_v3_minus_v4_online":round(first3_ms-first4_ms,6),
            "authority_boundary":"performance routing only; all arms use authoritative StateLedger semantics and no effect authority",
            "limitations":["Synthetic in-memory StateLedger fixture, not Andreas target hardware.",
                           "Stable horizon is constructed from measured break-even to test controller behavior, not a forecast of Frank usage.",
                           "StateLedger write amplification from retaining the expression index is measured separately by V3 update benchmarks."],
        }
    finally: l4.close()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--rows',type=int,default=3000); ap.add_argument('--repeats',type=int,default=200)
    ap.add_argument('--budget',type=int,default=64); ap.add_argument('--output'); a=ap.parse_args()
    out=bench(max(100,a.rows),max(10,a.repeats),max(8,min(512,a.budget))); text=json.dumps(out,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
    print(text,end='')

if __name__=='__main__': main()
