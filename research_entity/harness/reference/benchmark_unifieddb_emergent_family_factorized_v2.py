from __future__ import annotations

import json, math, sqlite3, statistics, time
from dataclasses import replace

from .state_ledger import h
from .unifieddb_emergent_incremental import IncrementalEmergentAssemblyPreprocessor
from .unifieddb_emergent_preprocessor import PossibilitySpec
from .unifieddb_emergent_family_factorized_v2 import OnePassFamilyFactorizedEmergentAssemblyPreprocessor

EPOCH=19
K=12
FAMILIES=120

class SyntheticLedger:
    def __init__(self, rows):
        self._rows=rows; self.epoch=EPOCH
        self.semantic_state_hash=h([(r['domain'],r['key'],r['semantic_hash']) for r in rows])
    def materialized(self): return self._rows

def row(domain,key,value):
    return {'domain':domain,'key':key,'value':value,'epistemic':'KNOWN','status':'CURRENT','domain_epoch':EPOCH,'semantic_hash':h((domain,key,value))}

def fixture(bindings_per_family):
    rows=[row('semantic','root',{'label':'root'})]; sql=[]
    for fi in range(FAMILIES):
        family=f'family:{fi:03d}'; family_score=.999-fi*.005
        for bi in range(bindings_per_family):
            score=family_score-bi*.00001; key=f'f{fi:03d}_b{bi:02d}'; ref=f'possibility:{key}'
            rows.append(row('possibility',key,{'possibility_family_id':family,'binding_id':key,'synthetic_score':score}))
            rows.append(row('dependency',f'edge_{key}',{'source':'semantic:root','target':ref,'strength':score,'relation_type':'POSSIBILITY_BINDING'}))
            sql.append((family,ref,score))
    return rows,sql

def spec(tag,max_items=K):
    return PossibilitySpec(assembly_id=tag,seed_refs=('semantic:root',),allowed_domains=('possibility',),max_items=max_items,max_hops=1,frontier_budget=100000,min_edge_weight=0.0,basis_epoch=EPOCH)

def family_ids(items):
    out=[]
    for item in items:
        value=item.get('value'); fam=value.get('possibility_family_id') if isinstance(value,dict) else None
        if fam is not None and fam not in out: out.append(fam)
    return out

def factorize_items(items,k):
    selected=[]; seen=set()
    for item in items:
        value=item.get('value'); fam=value.get('possibility_family_id') if isinstance(value,dict) else None
        family=fam if isinstance(fam,str) and fam.strip() else f"__UNIQUE__:{item['ref']}"
        if family in seen: continue
        selected.append(item); seen.add(family)
        if len(selected)>=k: break
    return selected

def percentile(values,q):
    values=sorted(values); pos=(len(values)-1)*q; lo=math.floor(pos); hi=math.ceil(pos)
    return values[lo] if lo==hi else values[lo]*(hi-pos)+values[hi]*(pos-lo)

def timed(fn,reps=25):
    xs=[]; last=None
    for i in range(reps):
        t=time.perf_counter_ns(); last=fn(i); xs.append((time.perf_counter_ns()-t)/1000.0)
    return {'p50':statistics.median(xs),'p95':percentile(xs,.95),'mean':statistics.mean(xs),'last':last}

def sql_group_baseline(sql_rows):
    con=sqlite3.connect(':memory:'); con.execute('CREATE TABLE c(family TEXT,ref TEXT,score REAL)'); con.executemany('INSERT INTO c VALUES(?,?,?)',sql_rows); con.execute('CREATE INDEX c_family_score ON c(family,score DESC,ref)'); con.commit()
    query='''WITH ranked AS (SELECT family,ref,score,row_number() OVER(PARTITION BY family ORDER BY score DESC,ref) rn FROM c) SELECT family,ref,score FROM ranked WHERE rn=1 ORDER BY score DESC,ref LIMIT ?'''
    out=timed(lambda _:list(con.execute(query,(K,)))); families=[r[0] for r in out.pop('last')]; con.close(); out['families']=families; return out

def run_one(bindings):
    rows,sql_rows=fixture(bindings); ledger=SyntheticLedger(rows)
    base=IncrementalEmergentAssemblyPreprocessor(ledger); f2=OnePassFamilyFactorizedEmergentAssemblyPreprocessor(ledger,pool_cap=4096)
    base.compile_active_assembly(spec('warm-base')); f2.compile_active_assembly(spec('warm-f2'))
    tb=timed(lambda i:base.compile_active_assembly(spec(f'base-{i}')))
    tf1=timed(lambda i:factorize_items(base.compile_active_assembly(spec(f'f1-{i}',max_items=min(4096,K*4)))['selected'],K))
    tf2=timed(lambda i:f2.compile_active_assembly(spec(f'f2-{i}')))
    base_result=tb.pop('last'); f1_items=tf1.pop('last'); f2_result=tf2.pop('last'); sql=sql_group_baseline(sql_rows); sql_fams=sql.pop('families')
    gold=[f'family:{i:03d}' for i in range(K)]
    def rec(fams): return len(set(fams)&set(gold))/K
    base_f=family_ids(base_result['selected']); f1_f=family_ids(f1_items); f2_f=family_ids(f2_result['selected'])
    return {'bindings_per_family':bindings,'candidate_nodes':len(sql_rows),'baseline_eap':{'family_recall_at_12':rec(base_f),'unique_families':len(base_f),'latency_us':tb,'top1_ref':base_result['selected'][0]['ref']},'f1_fixed_4x_wrapper':{'family_recall_at_12':rec(f1_f),'unique_families':len(f1_f),'latency_us':tf1},'f2_one_pass_pool':{'family_recall_at_12':rec(f2_f),'unique_families':len(f2_f),'latency_us':tf2,'candidate_pool_items':f2_result['candidate_pool_items'],'pool_exhausted':f2_result['pool_exhausted_before_requested_family_budget'],'top1_ref':f2_result['selected'][0]['ref']},'sqlite_group_window':{'family_recall_at_12':rec(sql_fams),'unique_families':len(sql_fams),'latency_us':sql,'scope':'ALREADY_FLAT_CANDIDATE_ROWS_NOT_GRAPH_ASSEMBLY'},'top1_invariant':base_result['selected'][0]['ref']==f2_result['selected'][0]['ref']}

def main():
    results=[run_one(n) for n in (1,2,3,4,6,8,16)]
    print(json.dumps({'schema_version':'1.0','experiment':'EAP_FAMILY_F2_ONE_PASS_MULTIPLICITY','evidence_class':'SYNTHETIC_EXECUTED_MECHANISM_TEST_WHEN_RUN','k':K,'results':results,'scope_guard':'Compare model-input family coverage under fixed K. SQLite group-window is a strong flat-row counterbaseline and may be faster; no universal database superiority claim.'},indent=2,sort_keys=True))

if __name__=='__main__': main()
