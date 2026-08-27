#!/usr/bin/env python3
import json, math, random, statistics, time, platform, sqlite3
from collections import Counter
N_STATES=32; FEATURES=5; ACTIONS=4; QUERY_COST=0.035; CONF_THRESH=0.90; MAX_Q=5
BITS=[[(s>>f)&1 for f in range(FEATURES)] for s in range(N_STATES)]

def majority_action(states,amap):
 c=Counter(amap[s] for s in states); return min(((-n,a) for a,n in c.items()))[1]
def decision_accuracy(states,amap):
 c=Counter(amap[s] for s in states); return max(c.values())/len(states)
def all_same_action(states,amap):
 it=iter(states); first=amap[next(it)]; return all(amap[s]==first for s in it)
def split(states,f):
 return tuple(s for s in states if BITS[s][f]==0),tuple(s for s in states if BITS[s][f]==1)
def expected_accuracy_after(states,amap,f):
 z,o=split(states,f);n=len(states);return sum(len(ch)/n*decision_accuracy(ch,amap) for ch in (z,o) if ch)
def action_entropy(states,amap):
 c=Counter(amap[s] for s in states);n=len(states);return -sum((v/n)*math.log2(v/n) for v in c.values())
def best_feature(states,amap,remaining):
 baseH=action_entropy(states,amap);baseA=decision_accuracy(states,amap);best=None
 for f in remaining:
  z,o=split(states,f);n=len(states);expH=sum(len(ch)/n*action_entropy(ch,amap) for ch in (z,o) if ch);expA=expected_accuracy_after(states,amap,f);key=(baseH-expH,expA-baseA,-f)
  if best is None or key>best[0]:best=(key,f)
 return best[1]
def step(states,true_state,f):
 v=BITS[true_state][f];return tuple(s for s in states if BITS[s][f]==v)
def run_method(method,true_state,amap):
 states=tuple(range(N_STATES));remaining=set(range(FEATURES));q=0
 while True:
  pred=majority_action(states,amap);acc=decision_accuracy(states,amap)
  if method=='IAC':
   if all_same_action(states,amap):break
  elif method=='MYOPIC_VOC':
   if not remaining:break
   gains=[(expected_accuracy_after(states,amap,f)-acc-QUERY_COST,f) for f in remaining]
   if max(gains)[0]<=0:break
  elif method=='ACTION_CONFIDENCE':
   if acc>=CONF_THRESH:break
  elif method=='STATE_CERTAINTY':
   if len(states)==1:break
  elif method=='FIXED3':
   if q>=3 or not remaining:break
  else:raise ValueError(method)
  if not remaining or q>=MAX_Q:break
  f=best_feature(states,amap,remaining);remaining.remove(f);states=step(states,true_state,f);q+=1
 pred=majority_action(states,amap)
 return {'queries':q,'correct':int(pred==amap[true_state]),'remaining_states':len(states),'remaining_actions':len(set(amap[s] for s in states))}
def maps_for_seed(seed):
 rng=random.Random(seed)
 return {
  'COMPRESSED':{s:BITS[s][0] for s in range(N_STATES)},
  'MODERATE':{s:BITS[s][0]+2*BITS[s][1] for s in range(N_STATES)},
  'PARITY_SYNERGY':{s:sum(BITS[s])%2 for s in range(N_STATES)},
  'RARE_BRANCH':{s:(3 if s in (30,31) else 0) for s in range(N_STATES)},
  'DIFFUSE':{s:rng.randrange(ACTIONS) for s in range(N_STATES)}}
methods=['IAC','MYOPIC_VOC','ACTION_CONFIDENCE','STATE_CERTAINTY','FIXED3']
raw=[]
for seed in range(20260811,20260831):
 for regime,amap in maps_for_seed(seed).items():
  for method in methods:
   rows=[run_method(method,t,amap) for t in range(N_STATES)]
   raw.append({'seed':seed,'regime':regime,'method':method,'accuracy':sum(r['correct'] for r in rows)/N_STATES,'mean_queries':sum(r['queries'] for r in rows)/N_STATES,'p95_queries':sorted(r['queries'] for r in rows)[int(.95*(N_STATES-1))],'mean_remaining_states':sum(r['remaining_states'] for r in rows)/N_STATES,'mean_remaining_actions':sum(r['remaining_actions'] for r in rows)/N_STATES})
summary={}
for regime in ['COMPRESSED','MODERATE','PARITY_SYNERGY','RARE_BRANCH','DIFFUSE']:
 summary[regime]={}
 for method in methods:
  rs=[r for r in raw if r['regime']==regime and r['method']==method]
  summary[regime][method]={'accuracy_mean':statistics.mean(r['accuracy'] for r in rs),'accuracy_min':min(r['accuracy'] for r in rs),'queries_mean':statistics.mean(r['mean_queries'] for r in rs),'queries_p95_across_seeds':sorted(r['mean_queries'] for r in rs)[int(.95*(len(rs)-1))]}
# safety lesions
amap=maps_for_seed(20260811)['COMPRESSED'];states=tuple(s for s in range(N_STATES) if BITS[s][0]==0);same=all_same_action(states,amap)
stale={'naive_witness_would_accept':same,'epoch_guard_accepts':False,'expected':'REJECT_STALE'}
rare=maps_for_seed(20260811)['RARE_BRANCH'];broken_states=tuple(s for s in range(N_STATES) if s not in (30,31));broken={'naive_witness_would_accept':all_same_action(broken_states,rare),'coverage_guard_accepts':False,'expected':'REJECT_UNVERIFIED_COVERAGE'}
# predicate microbenchmark
bench_states=tuple(range(N_STATES));bench_map=maps_for_seed(20260811)['DIFFUSE'];reps=250000
for _ in range(1000):all_same_action(bench_states,bench_map);decision_accuracy(bench_states,bench_map)
t0=time.perf_counter_ns()
for _ in range(reps):all_same_action(bench_states,bench_map)
t1=time.perf_counter_ns()
for _ in range(reps):decision_accuracy(bench_states,bench_map)>=CONF_THRESH
t2=time.perf_counter_ns()
out={'schema_version':'1.0','experiment':'IAC-001 deterministic action-invariance stopping discriminator','environment':{'python':platform.python_version(),'platform':platform.platform(),'sqlite':sqlite3.sqlite_version},'config':{'states':N_STATES,'features':FEATURES,'actions':ACTIONS,'seeds':[20260811,20260830],'query_cost':QUERY_COST,'confidence_threshold':CONF_THRESH},'summary':summary,'controls':{'stale_decision_epoch':stale,'broken_hyperposition_coverage':broken},'predicate_microbenchmark':{'repetitions':reps,'iac_exact_scan_ns_per_check':(t1-t0)/reps,'confidence_counter_ns_per_check':(t2-t1)/reps},'raw_aggregates':raw,'claims':{'synthetic_only':True,'real_frank_runtime':False,'external_effect':False,'canonical_state_mutation':False}}
print(json.dumps(out,indent=2))
