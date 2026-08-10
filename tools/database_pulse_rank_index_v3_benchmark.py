#!/usr/bin/env python3
from __future__ import annotations

"""Matched benchmark: legacy lexical pre-limit vs ActiveFieldV2 vs authoritative rank index V3.

Measures correctness, cold materialization/index build, hot selection, and real StateLedger
update-to-ready latency. Synthetic engineering proxy only; not live-FRANK cognitive quality.
"""

import argparse, json, math, statistics, sys, time
from pathlib import Path
from typing import Any, Callable

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger  # noqa:E402
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane  # noqa:E402
from research_entity.runtime.database_pulse_active_field_v2 import PulseActiveFieldV2, signal_score  # noqa:E402
from research_entity.runtime.database_pulse_rank_index_v3 import AuthoritativeRankIndexV3, INDEX_NAME  # noqa:E402


def quantile(xs,p):
    ys=sorted(xs); return ys[min(len(ys)-1,max(0,math.ceil(p*len(ys))-1))] if ys else 0.0

def stats(xs):
    return {"n":len(xs),"min_ms":round(min(xs),6) if xs else 0.0,
            "p50_ms":round(statistics.median(xs),6) if xs else 0.0,
            "p90_ms":round(quantile(xs,.90),6),"p95_ms":round(quantile(xs,.95),6),
            "p99_ms":round(quantile(xs,.99),6),"max_ms":round(max(xs),6) if xs else 0.0,
            "mean_ms":round(statistics.mean(xs),6) if xs else 0.0}

def timed(fn:Callable[[],Any]):
    t0=time.perf_counter_ns(); out=fn(); return out,(time.perf_counter_ns()-t0)/1_000_000.0


def seed_events(rows:int):
    ledger=StateLedger(); ops=[]
    for i in range(rows):
        ops.append({"op":"SET","domain":"memory","key":f"k{i:06d}",
                    "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
                    "epistemic":"KNOWN","status":"CURRENT"})
    ops.extend([
        {"op":"SET","domain":"memory","key":"zzzzzz-critical",
         "value":{"fact":"critical","priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
         "epistemic":"KNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"unknown","value":{"priority":1.0},"epistemic":"UNKNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"conflict","value":{"priority":1.0},"epistemic":"CONFLICT","status":"CURRENT"},
    ])
    ledger.append_event(event_id="seed",idem="seed",base_epoch=ledger.epoch,event_type="RANK_V3_BENCH_SEED",
                        writer="benchmark",ops=ops,committed_at="2026-08-10T01:20:00Z")
    events=ledger.export_events(); ledger.close(); return events


def wide_reference(ledger:StateLedger):
    rows=[]
    for r in ledger.conn.execute("SELECT domain,k,value_json,semantic_hash FROM state WHERE domain='memory' AND status='CURRENT' AND epistemic='KNOWN'"):
        value=json.loads(r["value_json"]) if r["value_json"] is not None else None
        score,_=signal_score(value); rows.append((float(score),f"{r['domain']}:{r['k']}",r["semantic_hash"]))
    rows.sort(key=lambda x:(-x[0],x[1],x[2])); return rows[0][1]


def update_op(i:int,rows:int):
    return {"op":"SET","domain":"memory","key":f"k{i%rows:06d}",
            "value":{"fact":i,"priority":0.25 if i%2 else 0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
            "epistemic":"KNOWN","status":"CURRENT"}


def benchmark(rows:int,budget:int,repeats:int,updates:int):
    events=seed_events(rows); target="memory:zzzzzz-critical"

    base=StateLedger.replay(events); active_ledger=StateLedger.replay(events); rank_ledger=StateLedger.replay(events)
    try:
        ref=wide_reference(base)
        qp=UnifiedDBQueryPlane(base)
        legacy_lat=[]; legacy_focus=None
        for i in range(repeats):
            receipt,ms=timed(lambda i=i:qp.query(QuerySpec(
                query_id=f"legacy-{i}",domains=("memory",),statuses=("CURRENT",),
                epistemic=("KNOWN",),limit=budget,basis_epoch=base.epoch,purpose="LEGACY_LEXICAL_PRELIMIT")))
            legacy_lat.append(ms)
            ranked=[]
            for row in receipt.rows:
                score,_=signal_score(row.get("value")); ranked.append((score,f"{row['domain']}:{row['key']}",row["semantic_hash"]))
            ranked.sort(key=lambda x:(-x[0],x[1],x[2])); legacy_focus=ranked[0][1] if ranked else None

        active=PulseActiveFieldV2(active_ledger)
        _,active_build_ms=timed(lambda:active.full_rebuild(now="build"))
        active_lat=[]; active_focus=None
        for i in range(repeats):
            sel,ms=timed(lambda i=i:active.select(source_domains=("memory",),basis_epoch=active_ledger.epoch,
                                                   max_candidates=budget,max_focus=1,now=f"r{i}"))
            active_lat.append(ms); active_focus=sel.focus_refs[0] if sel.focus_refs else None

        rank=AuthoritativeRankIndexV3(rank_ledger)
        _,rank_build_ms=timed(rank.ensure_index)
        rank_verify=rank.verify_index_semantics(domains=("memory",),max_candidates=min(512,budget))
        rank_lat=[]; rank_focus=None; plans=[]
        for _ in range(repeats):
            sel,ms=timed(lambda:rank.select(source_domains=("memory",),basis_epoch=rank_ledger.epoch,
                                            max_candidates=budget,max_focus=1))
            rank_lat.append(ms); rank_focus=sel.focus_refs[0] if sel.focus_refs else None
            plans.extend(sel.query_plan)

        # Real update-to-ready paths. Baseline is authoritative ledger only; ActiveField adds an
        # explicit refresh; RankIndex maintenance is paid inside the same authoritative write.
        base_updates=[]; active_write=[]; active_refresh=[]; active_ready=[]; rank_ready=[]
        for i in range(updates):
            op=update_op(i,rows)
            _,ms=timed(lambda i=i,op=op:base.append_event(event_id=f"b{i}",idem=f"b{i}",base_epoch=base.epoch,
                        event_type="BENCH_UPDATE",writer="benchmark",ops=[op],committed_at=f"2026-08-10T01:21:{i%60:02d}Z"))
            base_updates.append(ms)

            _,w=timed(lambda i=i,op=op:active_ledger.append_event(event_id=f"a{i}",idem=f"a{i}",base_epoch=active_ledger.epoch,
                      event_type="BENCH_UPDATE",writer="benchmark",ops=[op],committed_at=f"2026-08-10T01:22:{i%60:02d}Z"))
            _,r=timed(lambda i=i:active.refresh(now=f"refresh-{i}"))
            active_write.append(w); active_refresh.append(r); active_ready.append(w+r)

            _,rr=timed(lambda i=i,op=op:rank_ledger.append_event(event_id=f"v{i}",idem=f"v{i}",base_epoch=rank_ledger.epoch,
                       event_type="BENCH_UPDATE",writer="benchmark",ops=[op],committed_at=f"2026-08-10T01:23:{i%60:02d}Z"))
            rank_ready.append(rr)

        active_final=active.select(source_domains=("memory",),basis_epoch=active_ledger.epoch,
                                   max_candidates=budget,max_focus=1,now="final")
        rank_final=rank.select(source_domains=("memory",),basis_epoch=rank_ledger.epoch,max_candidates=budget,max_focus=1)
        active_verify=active.verify_projection()
        rank_verify_final=rank.verify_index_semantics(domains=("memory",),max_candidates=min(512,budget))
        base_stats=stats(base_updates); rank_update_stats=stats(rank_ready); active_ready_stats=stats(active_ready)
        rank_overhead=(rank_update_stats["p50_ms"]-base_stats["p50_ms"])
        active_overhead=(active_ready_stats["p50_ms"]-base_stats["p50_ms"])
        return {
            "schema_version":"1.0",
            "benchmark_class":"PULSE_CANDIDATE_GENERATION_SIMPLER_BASELINE",
            "fixture":{"low_rows":rows,"total_memory_rows":rows+3,"candidate_budget":budget,"read_repeats":repeats,"updates":updates},
            "correctness":{"expected_focus":target,"wide_reference_focus":ref,
                           "legacy_focus":legacy_focus,"active_field_focus":active_focus,"rank_index_focus":rank_focus,
                           "legacy_correct":legacy_focus==target,"active_field_correct":active_focus==target,"rank_index_correct":rank_focus==target,
                           "active_final_focus":active_final.focus_refs[0] if active_final.focus_refs else None,
                           "rank_final_focus":rank_final.focus_refs[0] if rank_final.focus_refs else None,
                           "active_projection_verify":active_verify,"rank_index_verify_initial":rank_verify,"rank_index_verify_final":rank_verify_final,
                           "rank_query_plan_uses_index":any(INDEX_NAME in p for p in plans)},
            "cold_build_ms":{"active_field":round(active_build_ms,6),"rank_index":round(rank_build_ms,6)},
            "hot_selection":{"legacy_query_only":stats(legacy_lat),"active_field_refresh_plus_select":stats(active_lat),"rank_index_select":stats(rank_lat)},
            "update_to_ready":{"authoritative_ledger_only":base_stats,"active_field_authoritative_write":stats(active_write),
                               "active_field_refresh_only":stats(active_refresh),"active_field_total":active_ready_stats,"rank_index_atomic_total":rank_update_stats,
                               "rank_index_p50_overhead_vs_noindex_ms":round(rank_overhead,6),
                               "active_field_p50_overhead_vs_noindex_ms":round(active_overhead,6)},
            "architecture_test":{
                "rank_index_is_simpler_semantic_surface":True,
                "rank_index_has_no_second_candidate_table":True,
                "promotion_rule":"prefer rank index only if correctness/replay/fail-closed remain equal and measured total cost is Pareto-competitive",
            },
            "authority_boundary":"all candidate ordering remains context-only; StateLedger is semantic authority; no effect authority",
            "limitations":[
                "Synthetic salience fixture, not downstream live-FRANK task accuracy.",
                "StateLedger semantic-root recomputation dominates write latency at scale; overhead deltas are hardware/fixture dependent.",
                "CREATE INDEX cold cost and steady-state write amplification must be remeasured on Andreas target hardware.",
                "SQLite JSON expression support/version is a runtime dependency and must be capability-gated.",
            ],
        }
    finally:
        base.close(); active_ledger.close(); rank_ledger.close()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--rows',type=int,default=3000); ap.add_argument('--budget',type=int,default=64)
    ap.add_argument('--repeats',type=int,default=200); ap.add_argument('--updates',type=int,default=100); ap.add_argument('--output')
    a=ap.parse_args(); out=benchmark(max(100,a.rows),max(8,min(512,a.budget)),max(10,a.repeats),max(1,a.updates))
    text=json.dumps(out,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
    print(text,end='')

if __name__=='__main__': main()
