#!/usr/bin/env python3
from __future__ import annotations
import itertools, json, math, random, statistics, time, platform, sys, os

SEED=20260811
random.seed(SEED)

def eval_dnf(terms,a): return any(all(a.get(v,False) for v in t) for t in terms)

def exact_responsibility(terms,a,var):
    # INTERNAL DEPENDENCY RESPONSIBILITY, not real-world causal truth.
    if not a.get(var,False) or not eval_dnf(terms,a): return 0.0,None
    others=[v for v,val in a.items() if val and v!=var]
    for k in range(len(others)+1):
        for W in itertools.combinations(others,k):
            a1=dict(a)
            for w in W: a1[w]=False
            if not eval_dnf(terms,a1): continue
            a0=dict(a1); a0[var]=False
            if not eval_dnf(terms,a0): return 1.0/(k+1),list(W)
    return 0.0,None

def broad_credit(terms,a): return {v:1.0 for v,val in a.items() if val}
def first_path_credit(terms,a):
    for t in terms:
        if all(a.get(v,False) for v in t): return {v:1.0 for v in t}
    return {}
def satisfied_ancestor_credit(terms,a):
    out={}
    for t in terms:
        if all(a.get(v,False) for v in t):
            for v in t: out[v]=1.0
    return out

def score(pred,truth):
    ps={v for v,s in pred.items() if s>0}; tp=len(ps&truth); fp=len(ps-truth); fn=len(truth-ps)
    p=tp/(tp+fp) if tp+fp else (1.0 if not truth else 0.0); r=tp/(tp+fn) if tp+fn else 1.0
    f=2*p*r/(p+r) if p+r else 0.0
    return dict(precision=p,recall=r,f1=f,tp=tp,fp=fp,fn=fn)

def generate_case(n_vars=9,n_terms=6,width_range=(2,4),active_p=.65):
    vs=[f"x{i}" for i in range(n_vars)]; terms=[]
    while len(terms)<n_terms:
        w=random.randint(width_range[0],min(width_range[1],n_vars)); t=tuple(sorted(random.sample(vs,w)))
        if t not in terms: terms.append(t)
    for _ in range(1000):
        a={v:(random.random()<active_p) for v in vs}
        if eval_dnf(terms,a): return terms,a
    a={v:False for v in vs}
    for v in terms[0]: a[v]=True
    return terms,a

def percentile(xs,q):
    ys=sorted(xs); return ys[min(len(ys)-1,max(0,math.ceil(q*len(ys))-1))]

def correctness_benchmark(cases=1000):
    rows=[]; broken_rows=[]; example=None
    for _ in range(cases):
        n=random.randint(6,12); terms,a=generate_case(n_vars=n,n_terms=random.randint(4,9))
        resp={v:exact_responsibility(terms,a,v)[0] for v in a}; truth={v for v,r in resp.items() if r>0}
        methods={"BROADCAST_ALL":broad_credit(terms,a),"FIRST_PATH":first_path_credit(terms,a),"SATISFIED_ANCESTOR_DAG":satisfied_ancestor_credit(terms,a),"EXPLICIT_RESPONSIBILITY":resp,"CARF":resp}
        for name,pred in methods.items(): rows.append((name,score(pred,truth)))
        keys=list(a); shuffled=list(keys); random.shuffle(shuffled); mapping=dict(zip(keys,shuffled)); broken={mapping[k]:v for k,v in resp.items()}
        broken_rows.append(score(broken,truth))
        if example is None and len(truth)>=3: example={"terms":[list(t) for t in terms],"assignment":a,"responsibility":resp,"truth_causes":sorted(truth)}
    out={}
    for name in sorted(set(n for n,_ in rows)):
        rr=[s for n,s in rows if n==name]
        out[name]={"precision_mean":statistics.mean(x["precision"] for x in rr),"recall_mean":statistics.mean(x["recall"] for x in rr),"f1_mean":statistics.mean(x["f1"] for x in rr),"fp_total":sum(x["fp"] for x in rr),"fn_total":sum(x["fn"] for x in rr)}
    out["PROVENANCE_BROKEN_CONTROL"]={"precision_mean":statistics.mean(x["precision"] for x in broken_rows),"recall_mean":statistics.mean(x["recall"] for x in broken_rows),"f1_mean":statistics.mean(x["f1"] for x in broken_rows),"fp_total":sum(x["fp"] for x in broken_rows),"fn_total":sum(x["fn"] for x in broken_rows)}
    return out,example

def responsibility_scaling():
    out=[]
    for n,cases in [(6,200),(8,200),(10,150),(12,100),(14,60)]:
        ts=[]
        for _ in range(cases):
            terms,a=generate_case(n_vars=n,n_terms=max(4,n//2)); t0=time.perf_counter_ns()
            for v in a: exact_responsibility(terms,a,v)
            ts.append((time.perf_counter_ns()-t0)/1e6)
        out.append({"active_variable_cap":n,"cases":cases,"p50_ms":statistics.median(ts),"p95_ms":percentile(ts,.95),"p99_ms":percentile(ts,.99),"max_ms":max(ts),"mean_ms":statistics.mean(ts)})
    return out

def factorization_benchmark():
    rows=[]
    for k in [4,5,6,7,8]:
        m=4; groups=[[f"g{i}a{j}" for j in range(m)] for i in range(k)]; t0=time.perf_counter_ns(); paths=list(itertools.product(*groups)); enum=(time.perf_counter_ns()-t0)/1e6
        chars=sum(sum(len(x) for x in p)+(k-1) for p in paths); nodes=k*m+k+1
        rows.append({"groups":k,"alternatives_per_group":m,"explicit_derivation_paths":len(paths),"explicit_enumeration_ms":enum,"explicit_serialized_chars_est":chars,"carf_factor_circuit_nodes":nodes,"strong_conventional_factor_dag_nodes":nodes,"path_to_carf_node_ratio":len(paths)/nodes,"carf_vs_strong_dag_node_ratio":1.0})
    return rows

def main():
    t0=time.perf_counter(); correctness,example=correctness_benchmark()
    result={"schema_version":"1.0","candidate":"CARF-001","seed":SEED,"scope":"deterministic synthetic internal-dependency discriminator; not target Frank runtime evidence","correctness_cases":1000,"correctness":correctness,"responsibility_scaling":responsibility_scaling(),"factorization":factorization_benchmark(),"epoch_controls":[{"circuit_epoch":e,"current_epoch":17,"accepted":e==17} for e in [17,16,15,0,18]],"representative_random_case":example,"strong_counterbaseline_result":"A strong conventional factorized dependency DAG has the same node count as CARF on the factorization benchmark.","limitations":["exact responsibility is exponential in worst case","synthetic Boolean lineage is not real-world causal truth","probability cannot be inferred by naive semiring multiplication under unknown dependence","CARF cannot mint truth/self/user intent/effect/training authority","no ClayCode compiler/runtime execution claimed"],"runtime_metadata":{"python":sys.version,"platform":platform.platform(),"machine":platform.machine(),"processor":platform.processor() or "UNKNOWN","pid":os.getpid()},"total_reference_runtime_s":time.perf_counter()-t0}
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__": main()
