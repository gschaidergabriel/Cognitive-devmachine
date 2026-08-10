#!/usr/bin/env python3
from __future__ import annotations

import argparse,json,math,statistics,tempfile,time
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME
from research_entity.runtime.database_pulse_rank_path_v4 import AdaptiveAuthoritativeRankPathV4
from research_entity.runtime.database_pulse_rank_path_v5 import AdaptiveAuthoritativeRankPathV5
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def stat(xs):
    ys=sorted(xs)
    def q(p):
        k=(len(ys)-1)*p;a=math.floor(k);b=math.ceil(k)
        return ys[a] if a==b else ys[a]*(b-k)+ys[b]*(k-a)
    return {'n':len(xs),'p50_ms':q(.5),'p95_ms':q(.95),'p99_ms':q(.99),'mean_ms':statistics.fmean(xs),'min_ms':min(xs),'max_ms':max(xs)}

def timed(fn):
    t=time.perf_counter_ns();out=fn();return out,(time.perf_counter_ns()-t)/1e6

def econ():
    return CompileEconomics(build_cost_us=1000.0,online_query_us=100.0,compiled_query_us=10.0,
        online_quality=1.0,compiled_quality=1.0,expected_reads_before_invalidation=0.0,safety_factor=1.0)

def long_hist():return [EpochReadLifetime(i+1,250) for i in range(8)]
def sparse_hist():return [EpochReadLifetime(1,250),EpochReadLifetime(2,250)]

def seed(path,rows):
    l=StateLedger(path);ops=[]
    for i in range(rows):
        ops.append({'op':'SET','domain':'memory','key':f'k{i:06d}',
            'value':{'priority':((i*17)%101)/100.0,'urgency':((i*29)%101)/100.0,
                     'salience':((i*43)%101)/100.0,'novelty':((i*61)%101)/100.0},
            'epistemic':'KNOWN','status':'CURRENT'})
    l.append_event(event_id='seed',idem='seed',base_epoch=0,event_type='SEED',writer='bench',ops=ops,
                   committed_at='2026-08-10T02:10:00Z')
    return l

def run(rows,repeats):
    with tempfile.TemporaryDirectory() as td:
        # Two physically independent but semantically identical ledgers.
        l4=seed(Path(td)/'v4.sqlite',rows); l5=seed(Path(td)/'v5.sqlite',rows)
        v4=AdaptiveAuthoritativeRankPathV4(l4);v5=AdaptiveAuthoritativeRankPathV5(l5)
        kwargs4=dict(source_domains=('memory',),basis_epoch=l4.epoch,max_candidates=64,max_focus=12,
                     economics_without_horizon=econ(),pulse_history=long_hist())
        kwargs5=dict(source_domains=('memory',),basis_epoch=l5.epoch,max_candidates=64,max_focus=12,
                     economics_without_horizon=econ(),pulse_history=long_hist())

        first4,t_first4=timed(lambda:v4.select(**kwargs4))
        first5,t_first5=timed(lambda:v5.select(**kwargs5))
        index_after_first4=v4.index_exists();index_after_first5=v5.index_exists()
        plan5=v5.plan_lifecycle(basis_epoch=l5.epoch,economics_without_horizon=econ(),pulse_history=long_hist())
        maint5,t_build5=timed(lambda:v5.apply_maintenance(plan5))
        compiled5,t_compiled5=timed(lambda:v5.select(**kwargs5))

        hot4=[];hot5=[]
        for _ in range(repeats):
            _,dt=timed(lambda:v4.select(**kwargs4));hot4.append(dt)
            _,dt=timed(lambda:v5.select(**kwargs5));hot5.append(dt)

        churn4,t_churn4=timed(lambda:v4.select(
            source_domains=('memory',),basis_epoch=l4.epoch,max_candidates=64,max_focus=12,
            economics_without_horizon=econ(),pulse_history=sparse_hist()))
        churn5,t_churn5=timed(lambda:v5.select(
            source_domains=('memory',),basis_epoch=l5.epoch,max_candidates=64,max_focus=12,
            economics_without_horizon=econ(),pulse_history=sparse_hist()))
        index_after_churn4=v4.index_exists();index_after_churn5=v5.index_exists()
        drop_plan=v5.plan_lifecycle(basis_epoch=l5.epoch,economics_without_horizon=econ(),pulse_history=sparse_hist())
        drop_receipt,t_drop5=timed(lambda:v5.apply_maintenance(drop_plan))
        index_after_drop5=v5.index_exists()

        out={
          'schema_version':'1.0','benchmark':'DATABASE_PULSE_RANK_PATH_V4_V5_LIFECYCLE',
          'rows':rows,'repeats':repeats,
          'correctness':{
            'first_focus_equal':first4.focus_refs==first5.focus_refs,
            'first_candidates_equal':first4.candidate_refs==first5.candidate_refs,
            'v5_online_compiled_equal':first5.candidate_refs==compiled5.candidate_refs and first5.focus_refs==compiled5.focus_refs,
            'churn_focus_equal':churn4.focus_refs==churn5.focus_refs,
          },
          'v4':{
            'first_select_ms':t_first4,'first_physical_mode':first4.physical_mode,
            'index_after_first_select':index_after_first4,
            'hot_select':stat(hot4),
            'churn_select_ms':t_churn4,'churn_physical_mode':churn4.physical_mode,
            'index_after_churn_online_decision':index_after_churn4,
            'churn_query_plan':list(churn4.query_plan),
          },
          'v5':{
            'first_select_ms':t_first5,'first_physical_mode':first5.physical_read_mode,
            'index_after_first_select':index_after_first5,
            'separate_build_ms':t_build5,'build_status':maint5.status,
            'first_compiled_select_ms':t_compiled5,
            'hot_select':stat(hot5),
            'churn_select_ms':t_churn5,'churn_physical_mode':churn5.physical_read_mode,
            'index_after_churn_before_maintenance':index_after_churn5,
            'churn_query_plan':list(churn5.query_plan),
            'separate_drop_ms':t_drop5,'drop_status':drop_receipt.status,
            'index_after_drop':index_after_drop5,
          },
          'falsifier':{
            'v4_inline_build_observed':not first4.index_present_before and first4.index_present_after,
            'v5_read_phase_schema_mutation_absent':not index_after_first5,
            'v4_online_after_churn_keeps_index':churn4.physical_mode=='ONLINE_NO_COMPILE' and index_after_churn4,
            'v5_online_after_churn_forces_no_index_plan':churn5.physical_read_mode=='ONLINE_PENDING_DECOMPILE' and not any(INDEX_NAME in x for x in churn5.query_plan),
            'v5_maintenance_removes_index':drop_receipt.status=='DROPPED' and not index_after_drop5,
          },
          'authority':'ENGINEERING_PERFORMANCE_EVIDENCE_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY',
          'limitations':['Synthetic StateLedger fixture.','No concurrent writer load.','Hostinger/Andreas target evidence must be classified separately.']
        }
        l4.close();l5.close();return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rows',type=int,default=5000);ap.add_argument('--repeats',type=int,default=100);ap.add_argument('--output')
    a=ap.parse_args();x=run(a.rows,a.repeats)
    assert all(x['correctness'].values()),x
    assert all(x['falsifier'].values()),x
    text=json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
    print(text,end='')
if __name__=='__main__':main()
