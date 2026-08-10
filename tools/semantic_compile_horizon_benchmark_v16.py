#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import (
    EpochReadLifetime,
    decide_compile_from_pulse_history,
)

BUILD_US=72295.54633333333
ONLINE_US=60.76010636666667
COMPILED_US=4.294575966666667


def quantile(xs,p):
    ys=sorted(xs)
    pos=(len(ys)-1)*p
    lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi:return ys[lo]
    f=pos-lo
    return ys[lo]*(1-f)+ys[hi]*f


def stats(xs):
    return {
        'n':len(xs),
        'min_ns':min(xs) if xs else 0,
        'p50_ns':quantile(xs,.50) if xs else 0,
        'p95_ns':quantile(xs,.95) if xs else 0,
        'p99_ns':quantile(xs,.99) if xs else 0,
        'max_ns':max(xs) if xs else 0,
        'mean_ns':statistics.mean(xs) if xs else 0,
    }


def online_cost(reads): return reads*ONLINE_US
def compiled_cost(reads): return BUILD_US+reads*COMPILED_US

def run_sequence(name,reads):
    history=[]
    policy_cost=0.0; online_total=0.0; compile_total=0.0; oracle_total=0.0
    compile_decisions=0; shock_bound_decisions=0; decision_lat=[]; rows=[]
    for index,actual in enumerate(reads,1):
        economics=CompileEconomics(
            build_cost_us=BUILD_US,
            online_query_us=ONLINE_US,
            compiled_query_us=COMPILED_US,
            online_quality=1.0,
            compiled_quality=1.0,
            expected_reads_before_invalidation=0.0,
            safety_factor=1.20,
        )
        t0=time.perf_counter_ns()
        estimate,decision=decide_compile_from_pulse_history(economics,history)
        decision_lat.append(time.perf_counter_ns()-t0)
        c_online=online_cost(actual); c_compile=compiled_cost(actual)
        c_policy=c_compile if decision.mode=='COMPILE' else c_online
        policy_cost+=c_policy; online_total+=c_online; compile_total+=c_compile
        oracle_total+=min(c_online,c_compile)
        compile_decisions+=int(decision.mode=='COMPILE')
        shock_bound_decisions+=int(estimate.churn_shock)
        rows.append({
            'epoch':index,
            'actual_reads':actual,
            'estimated_lower_bound':estimate.expected_reads_lower_bound,
            'estimate_status':estimate.status,
            'decision':decision.mode,
            'policy_cost_us':c_policy,
            'oracle_mode':'COMPILE' if c_compile<c_online else 'ONLINE',
            'oracle_cost_us':min(c_online,c_compile),
        })
        history.append(EpochReadLifetime(index,actual,completed=True))
    return {
        'name':name,
        'epochs':len(reads),
        'reads_total':sum(reads),
        'compile_decisions':compile_decisions,
        'shock_bound_decisions':shock_bound_decisions,
        'total_work_us':{
            'pulse_horizon_policy':policy_cost,
            'always_online':online_total,
            'always_compile':compile_total,
            'oracle_per_epoch':oracle_total,
        },
        'regret_vs_oracle_us':{
            'pulse_horizon_policy':policy_cost-oracle_total,
            'always_online':online_total-oracle_total,
            'always_compile':compile_total-oracle_total,
        },
        'policy_savings_vs_always_online_us':online_total-policy_cost,
        'policy_savings_vs_always_compile_us':compile_total-policy_cost,
        'decision_latency':stats(decision_lat),
        'trace':rows,
    }


def build_scenarios(seed):
    rng=random.Random(seed)
    def jitter(center,span,n):
        return [max(0,int(round(center+rng.uniform(-span,span)))) for _ in range(n)]
    stable_long=jitter(2300,250,40)
    stable_short=jitter(1000,180,40)
    shock=jitter(5000,250,12)+jitter(110,30,20)+jitter(2200,250,18)
    alternating=[]
    for _ in range(10): alternating+=jitter(2400,200,3)+jitter(700,100,3)
    return {
        'STABLE_LONG':stable_long,
        'STABLE_SHORT':stable_short,
        'CHURN_SHOCK_AND_RECOVERY':shock,
        'ALTERNATING_REGIME':alternating,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seeds',type=int,default=5)
    ap.add_argument('--output')
    args=ap.parse_args()
    if args.seeds<1 or args.seeds>100: raise SystemExit('--seeds must be 1..100')
    runs=[]
    for offset in range(args.seeds):
        seed=20260810+offset
        for name,reads in build_scenarios(seed).items():
            row=run_sequence(name,reads); row['seed']=seed; runs.append(row)
    policy_regret=[r['regret_vs_oracle_us']['pulse_horizon_policy'] for r in runs]
    online_regret=[r['regret_vs_oracle_us']['always_online'] for r in runs]
    compile_regret=[r['regret_vs_oracle_us']['always_compile'] for r in runs]
    output={
        'schema_version':'1.0',
        'benchmark':'U16_PULSE_INFORMED_COMPILE_HORIZON_REGRET',
        'evidence_class':'SYNTHETIC_EXECUTED_ENGINEERING_PROXY',
        'measured_cost_inputs_us':{
            'build':BUILD_US,'online_query':ONLINE_US,'compiled_query':COMPILED_US,
            'source':'V16_COMPILE_AMORTIZATION_GATE_FROM_V14_MEASURED_COSTS',
        },
        'configuration':{
            'seeds':args.seeds,
            'scenario_runs':len(runs),
            'min_completed_epochs':5,
            'history_window':32,
            'recent_window':3,
            'lower_quantile':0.20,
            'churn_drop_ratio':0.50,
            'compile_safety_factor':1.20,
        },
        'aggregate':{
            'policy_regret_vs_oracle_us_mean':statistics.mean(policy_regret),
            'always_online_regret_vs_oracle_us_mean':statistics.mean(online_regret),
            'always_compile_regret_vs_oracle_us_mean':statistics.mean(compile_regret),
            'policy_beats_or_equals_always_online_runs':sum(r['total_work_us']['pulse_horizon_policy']<=r['total_work_us']['always_online'] for r in runs),
            'policy_beats_or_equals_always_compile_runs':sum(r['total_work_us']['pulse_horizon_policy']<=r['total_work_us']['always_compile'] for r in runs),
            'policy_decision_p50_ns':statistics.median(r['decision_latency']['p50_ns'] for r in runs),
        },
        'runs':runs,
        'authority':'PERFORMANCE_ROUTING_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY',
        'limitations':[
            'Synthetic epoch-lifetime regimes; live Frank Pulse read/invalidation traces are not yet available.',
            'Cost inputs come from current local V14 measurements and are fixture/hardware specific.',
            'Oracle sees actual epoch lifetime after the fact and is an unattainable lower-bound comparator.',
            'The simple empirical estimator is a lesionable baseline, not a claim that q20/recent-floor is globally optimal.',
        ],
    }
    text=json.dumps(output,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
    print(text,end='')

if __name__=='__main__': main()
