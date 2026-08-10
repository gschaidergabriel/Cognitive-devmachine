from __future__ import annotations
import argparse,json,platform,sqlite3,time
from research_entity.harness.reference.state_ledger import StateLedger,h
from research_entity.runtime.database_pulse_rank_path_v6 import AdaptiveAuthoritativeRankPathV6
from research_entity.runtime.database_pulse_rank_path_v6_1_attested import AdaptiveAuthoritativeRankPathV61Attested
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime

def econ():return CompileEconomics(build_cost_us=1000,online_query_us=100,compiled_query_us=10,online_quality=1,compiled_quality=1,expected_reads_before_invalidation=0,safety_factor=1)
def hist():return [EpochReadLifetime(i+1,200) for i in range(8)]
def prov():return {"actor":"benchmark","policy_provenance_ref":"benchmark://v61","policy_decision_hash":h({"policy":"v61"})}
def seed(n):
 l=StateLedger();ops=[]
 for i in range(n):ops.append({"op":"SET","domain":"memory","key":f"k{i:08d}","value":{"priority":(i%101)/100,"urgency":(i%79)/78,"salience":(i%61)/60,"novelty":(i%43)/42},"epistemic":"KNOWN","status":"CURRENT"})
 l.append_event(event_id=f"seed-{n}",idem=f"seed-{n}",base_epoch=0,event_type="SEED",writer="bench",ops=ops,committed_at="2026-08-10T05:40:00Z");return l
def q6(v):return v.select(source_domains=("memory",),basis_epoch=v.ledger.epoch,max_candidates=64,max_focus=8,economics_without_horizon=econ(),pulse_history=hist())
def q61(v):return v.select(source_domains=("memory",),basis_epoch=v.ledger.epoch,max_candidates=64,max_focus=8,economics_without_horizon=econ(),pulse_history=hist(),**prov())
def quant(xs,p):
 xs=sorted(xs);return xs[min(len(xs)-1,int(round((len(xs)-1)*p)))]/1000
def bench(n,reps):
 l6=seed(n);v6=AdaptiveAuthoritativeRankPathV6(l6);p6=v6.plan_lifecycle(basis_epoch=l6.epoch,economics_without_horizon=econ(),pulse_history=hist());v6.apply_maintenance(p6,**prov());base=q6(v6)
 l61=seed(n);v61=AdaptiveAuthoritativeRankPathV61Attested(l61);p61=v61.plan_lifecycle(basis_epoch=l61.epoch,economics_without_horizon=econ(),pulse_history=hist(),**prov());v61.apply_maintenance(p61);att=q61(v61)
 equal=(base.candidate_refs==att.candidate_refs and base.candidate_scores==att.candidate_scores and base.focus_refs==att.focus_refs)
 a=[];b=[]
 for _ in range(reps):
  t=time.perf_counter_ns();q6(v6);a.append(time.perf_counter_ns()-t)
  t=time.perf_counter_ns();q61(v61);b.append(time.perf_counter_ns()-t)
 qa={k:quant(a,p) for k,p in (("p50",.5),("p95",.95),("p99",.99))};qb={k:quant(b,p) for k,p in (("p50",.5),("p95",.95),("p99",.99))}
 out={"rows":n,"repetitions":reps,"semantic_equivalence":equal,"v6_us":qa,"v6_1_attested_us":qb,"attestation_delta_p50_us":qb["p50"]-qa["p50"],"attestation_ratio_p50":qb["p50"]/qa["p50"] if qa["p50"] else None}
 l6.close();l61.close();return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--rows',default='100,1000');ap.add_argument('--reps',type=int,default=100);ap.add_argument('--output');a=ap.parse_args()
 r={"candidate":"PULSE_PROVENANCE_PLUS_ATTESTED_RANK_PATH_V6_1","metadata":{"platform":platform.platform(),"python":platform.python_version(),"sqlite":sqlite3.sqlite_version},"results":[bench(int(x),a.reps) for x in a.rows.split(',')],"authority":"PERFORMANCE_CONTINUITY_BENCHMARK_ONLY"};r['pass']=all(x['semantic_equivalence'] for x in r['results']);text=json.dumps(r,indent=2,sort_keys=True);print(text)
 if a.output:open(a.output,'w',encoding='utf-8').write(text+'\n')
if __name__=='__main__':main()
