#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger  # noqa: E402
from research_entity.runtime.database_pulse_candidate_v1 import DatabasePulseRuntime, PulseSpec  # noqa: E402
from research_entity.runtime.database_pulse_runtime_v2 import DatabasePulseRuntimeV2  # noqa: E402


def quantile(xs,p):
    ys=sorted(xs)
    return ys[min(len(ys)-1,max(0,math.ceil(p*len(ys))-1))] if ys else 0.0


def stats(xs):
    return {
        "n":len(xs),
        "min_ms":round(min(xs),6) if xs else 0.0,
        "p50_ms":round(statistics.median(xs),6) if xs else 0.0,
        "p90_ms":round(quantile(xs,.90),6),
        "p95_ms":round(quantile(xs,.95),6),
        "p99_ms":round(quantile(xs,.99),6),
        "max_ms":round(max(xs),6) if xs else 0.0,
        "mean_ms":round(statistics.mean(xs),6) if xs else 0.0,
    }


def seed_events(rows:int):
    ledger=StateLedger()
    ops=[]
    for i in range(rows):
        ops.append({"op":"SET","domain":"memory","key":f"k{i:04d}",
                    "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
                    "epistemic":"KNOWN","status":"CURRENT"})
    ops.append({"op":"SET","domain":"memory","key":"zzzz-critical",
                "value":{"fact":"critical","priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                "epistemic":"KNOWN","status":"CURRENT"})
    ledger.append_event(event_id="seed",idem="seed",base_epoch=ledger.epoch,event_type="BENCHMARK_SEED",
                        writer="benchmark",ops=ops,committed_at="2026-08-10T01:00:00Z")
    rt=DatabasePulseRuntime(ledger)
    rt.set_scheduler(enabled=True,event_id="scheduler",base_epoch=ledger.epoch,actor="benchmark",
                     reason="benchmark",committed_at="2026-08-10T01:00:01Z")
    events=ledger.export_events(); ledger.close(); return events


def arm(events, cls, *, label:str, pulses:int, candidate_budget:int):
    ledger=StateLedger.replay(events)
    runtime=cls(ledger)
    target="memory:zzzz-critical"
    lat=[]; focus=[]; models=tools=effects=0
    for i in range(pulses):
        spec=PulseSpec(f"{label}-{i}",basis_epoch=ledger.epoch,source_domains=("memory",),
                       max_candidates=candidate_budget,max_focus=1,reentry_mode="NO_REENTRY")
        t0=time.perf_counter_ns()
        r=runtime.run_pulse(spec,committed_at=f"2026-08-10T01:{1+(i//60):02d}:{i%60:02d}Z")
        lat.append((time.perf_counter_ns()-t0)/1_000_000.0)
        focus.append(r.focus_refs[0] if r.focus_refs else None)
        models+=r.model_call_count; tools+=r.tool_call_count; effects+=r.effect_count
    expected_state=ledger.semantic_state_hash; expected_trace=ledger.trace_root_hash
    replay=StateLedger.replay(ledger.export_events())
    replay_ok=(replay.semantic_state_hash==expected_state and replay.trace_root_hash==expected_trace and replay.epoch==ledger.epoch)
    replay.close(); ledger.close()
    return {
        "latency_all":stats(lat),
        "latency_warm_excluding_first":stats(lat[1:]),
        "first_pulse_ms":round(lat[0],6),
        "correct_focus_count":sum(x==target for x in focus),
        "pulse_count":pulses,
        "focus_accuracy":round(sum(x==target for x in focus)/pulses,6),
        "first_focus":focus[0],
        "last_focus":focus[-1],
        "model_call_total":models,
        "tool_call_total":tools,
        "effect_total":effects,
        "event_replay_roots_pass":replay_ok,
    }


def benchmark(rows:int,pulses:int,candidate_budget:int):
    events=seed_events(rows)
    v1=arm(events,DatabasePulseRuntime,label="v1",pulses=pulses,candidate_budget=candidate_budget)
    v2=arm(events,DatabasePulseRuntimeV2,label="v2",pulses=pulses,candidate_budget=candidate_budget)
    ratio=(v2["latency_warm_excluding_first"]["p50_ms"] / v1["latency_warm_excluding_first"]["p50_ms"]
           if v1["latency_warm_excluding_first"]["p50_ms"]>0 else None)
    return {
        "schema_version":"1.0",
        "benchmark_class":"DATABASE_PULSE_V1_V2_MATCHED_ENGINEERING_PROXY",
        "fixture":{"low_rows":rows,"total_memory_rows":rows+1,"pulses_per_arm":pulses,"candidate_budget":candidate_budget,
                   "reentry_mode":"NO_REENTRY","model_assistant":False},
        "expected_focus":"memory:zzzz-critical",
        "v1_lexicographic_candidate_generation":v1,
        "v2_incremental_active_field":v2,
        "comparison":{
            "focus_accuracy_delta":round(v2["focus_accuracy"]-v1["focus_accuracy"],6),
            "warm_p50_latency_ratio_v2_over_v1":round(ratio,4) if ratio is not None else None,
            "v2_correctness_improved":v2["focus_accuracy"]>v1["focus_accuracy"],
            "both_zero_model_tool_effect":all([
                v1["model_call_total"]==0,v1["tool_call_total"]==0,v1["effect_total"]==0,
                v2["model_call_total"]==0,v2["tool_call_total"]==0,v2["effect_total"]==0,
            ]),
            "both_replay_roots_pass":v1["event_replay_roots_pass"] and v2["event_replay_roots_pass"],
        },
        "authority_boundary":"candidate/focus is context-only; neither arm has external effect authority",
        "limitations":[
            "Synthetic salience fixture; live-FRANK downstream task accuracy is not measured.",
            "v1 is intentionally resource-bounded and this fixture targets its lexicographic pre-ranking truncation failure mode.",
            "v2 first-pulse cost includes lazy Active Field rebuild; warm figures isolate recurrent operation.",
            "This is not a general database benchmark.",
        ],
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rows",type=int,default=180)
    ap.add_argument("--pulses",type=int,default=100)
    ap.add_argument("--candidate-budget",type=int,default=64)
    ap.add_argument("--output")
    args=ap.parse_args()
    out=benchmark(max(70,args.rows),max(3,args.pulses),max(8,min(128,args.candidate_budget)))
    text=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding="utf-8")
    print(text,end="")


if __name__=="__main__":
    main()
