from __future__ import annotations

"""Differential stress for query-conditioned ephemeral evidence projection.

The fixture intentionally contains high-weight generic hubs that are semantically plausible
but wrong for the query. We compare unchanged EAP-1.3 with QCEP on the SAME epoch-bound rows.
A clean/unlabeled control family checks that query conditioning does not buy poisoned-graph
accuracy by destroying ordinary traversal. This is synthetic mechanism evidence only.
"""

import hashlib, json, math, random, statistics, time

from .unifieddb_emergent_preprocessor import EmergentAssemblyPreprocessor, PossibilitySpec
from .query_conditioned_evidence_projection import QueryConditionedEvidenceProjector, QueryEvidenceSpec

K=4
POISON_CASES=120
CLEAN_CASES=80
UNLABELED_CASES=40


def h(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def row(domain,key,value,epistemic='KNOWN',status='CURRENT'):
    return {'domain':domain,'key':key,'value':value,'epistemic':epistemic,'status':status,'domain_epoch':1,'semantic_hash':h([domain,key,value,epistemic,status])}
class Ledger:
    def __init__(self,rows): self._rows=list(rows); self.epoch=1; self.semantic_state_hash=h([(r['domain'],r['key'],r['semantic_hash']) for r in rows])
    def materialized(self): return list(self._rows)

def pct(xs,q):
    ys=sorted(xs); p=(len(ys)-1)*q; lo=math.floor(p); hi=math.ceil(p)
    return ys[lo] if lo==hi else ys[lo]*(hi-p)+ys[hi]*(p-lo)

def quality(got, truth):
    got=got[:K]; ts=set(truth); gs=set(got); hit=len(gs&ts)
    recall=hit/len(ts); precision=hit/max(1,len(gs)); complete=float(ts.issubset(gs))
    dcg=sum((1.0 if ref in ts else 0.0)/math.log2(i+2) for i,ref in enumerate(got))
    idcg=sum(1.0/math.log2(i+2) for i in range(len(truth)))
    return {'recall':recall,'precision':precision,'complete':complete,'ndcg':dcg/idcg}

def build():
    rows=[]; cases=[]
    total=POISON_CASES+CLEAN_CASES+UNLABELED_CASES
    for i in range(total):
        family='poison' if i<POISON_CASES else ('clean' if i<POISON_CASES+CLEAN_CASES else 'unlabeled')
        prefix=f'q{i:03d}'; root=f'semantic:{prefix}_root'; truth=[root]
        rows.append(row('semantic',f'{prefix}_root',{'text':'neutral anchor'}))
        cue=f'zircon{i:03d} constraint evidence'
        prev=root
        for j in range(3):
            ref=f'semantic:{prefix}_rel{j}'; truth.append(ref)
            rows.append(row('semantic',f'{prefix}_rel{j}',{'text':'neutral payload'}))
            if family=='poison': w=(.72,.91,.89)[j]
            else: w=(.96,.93,.90)[j]
            dep={'source':prev,'target':ref,'strength':w,'relation_type':'SUPPORTS'}
            if family!='unlabeled': dep['query_cue']=cue
            rows.append(row('dependency',f'{prefix}_re{j}',dep)); prev=ref
        hub=f'semantic:{prefix}_hub'; rows.append(row('semantic',f'{prefix}_hub',{'text':'generic association hub'}))
        hub_w=.99 if family=='poison' else .60
        rows.append(row('dependency',f'{prefix}_hubedge',{'source':root,'target':hub,'strength':hub_w,'relation_type':'RELATED','query_cue':'generic common association'}))
        for j in range(12):
            d=f'semantic:{prefix}_d{j:02d}'; rows.append(row('semantic',f'{prefix}_d{j:02d}',{'text':'generic unrelated'}))
            rows.append(row('dependency',f'{prefix}_hd{j:02d}',{'source':hub,'target':d,'strength':.98,'relation_type':'RELATED','query_cue':'generic common association'}))
        # Conflict path contains the query cue but must never launder activation.
        conflict=f'semantic:{prefix}_conflict'; launder=f'semantic:{prefix}_launder'
        rows.append(row('semantic',f'{prefix}_conflict',{'text':'uncertain'},'CONFLICT'))
        rows.append(row('semantic',f'{prefix}_launder',{'text':'should not relay'}))
        rows.append(row('dependency',f'{prefix}_conflictedge',{'source':root,'target':conflict,'strength':1.0,'relation_type':'SUPPORTS','query_cue':cue}))
        rows.append(row('dependency',f'{prefix}_launderedge',{'source':conflict,'target':launder,'strength':1.0,'relation_type':'SUPPORTS','query_cue':cue}))
        cases.append({'id':prefix,'family':family,'query':cue,'seed':root,'truth':truth,'launder':launder})
    return rows,cases

def main():
    rows,cases=build(); ledger=Ledger(rows); eap=EmergentAssemblyPreprocessor(ledger); qcep=QueryConditionedEvidenceProjector(ledger)
    # Warm both epoch projections and EAP lazy lexical index.
    first=cases[0]
    eap.compile_active_assembly(PossibilitySpec('warm-eap',seed_refs=(first['seed'],),query_text=first['query'],basis_epoch=1,max_items=K,max_hops=3,frontier_budget=256,min_edge_weight=0.0))
    qcep.project(QueryEvidenceSpec('warm-qcep',first['query'],(first['seed'],),1,max_items=K,max_hops=3,frontier_budget=256,min_edge_weight=0.0))
    order=cases[:]; random.Random(23).shuffle(order)
    modes={
        'eap_1_3':lambda c:[x['ref'] for x in eap.compile_active_assembly(PossibilitySpec('e-'+c['id'],seed_refs=(c['seed'],),query_text=c['query'],basis_epoch=1,max_items=K,max_hops=3,frontier_budget=256,min_edge_weight=0.0))['selected']],
        'qcep_0_1':lambda c:[x['ref'] for x in qcep.project(QueryEvidenceSpec('q-'+c['id'],c['query'],(c['seed'],),1,max_items=K,max_hops=3,frontier_budget=256,min_edge_weight=0.0))['selected']],
    }
    result={}
    for name,fn in modes.items():
        latency=[]; per=[]; laundered=0
        for c in order:
            t=time.perf_counter_ns(); got=fn(c); latency.append((time.perf_counter_ns()-t)/1000)
            q=quality(got,c['truth']); q['family']=c['family']; per.append(q); laundered+=int(c['launder'] in got)
        fam={}
        for family in ('poison','clean','unlabeled'):
            xs=[x for x in per if x['family']==family]
            fam[family]={k:statistics.mean(x[k] for x in xs) for k in ('recall','precision','complete','ndcg')}
        result[name]={
            'overall':{k:statistics.mean(x[k] for x in per) for k in ('recall','precision','complete','ndcg')},
            'families':fam,
            'laundered_conflict_descendants':laundered,
            'latency_us':{'p50':pct(latency,.5),'p95':pct(latency,.95),'p99':pct(latency,.99),'mean':statistics.mean(latency),'min':min(latency),'max':max(latency)},
        }
    base=result['eap_1_3']; cand=result['qcep_0_1']
    out={
        'schema_version':'1.0',
        'benchmark':'QUERY_CONDITIONED_EPHEMERAL_EVIDENCE_GRAPH_STRESS',
        'evidence_class':'SYNTHETIC_EXECUTED_MECHANISM_DIFFERENTIAL',
        'scope_guard':'Poisoned/hub-rich graph navigation mechanism only; not universal database superiority and not downstream FRANK answer quality.',
        'dataset':{'cases':len(cases),'poison_cases':POISON_CASES,'clean_cases':CLEAN_CASES,'unlabeled_cases':UNLABELED_CASES,'rows':len(rows),'k':K},
        'methods':result,
        'candidate_vs_eap':{
            'poison_complete_delta':cand['families']['poison']['complete']-base['families']['poison']['complete'],
            'poison_recall_delta':cand['families']['poison']['recall']-base['families']['poison']['recall'],
            'clean_recall_delta':cand['families']['clean']['recall']-base['families']['clean']['recall'],
            'unlabeled_recall_delta':cand['families']['unlabeled']['recall']-base['families']['unlabeled']['recall'],
            'p50_latency_ratio_qcep_over_eap':cand['latency_us']['p50']/base['latency_us']['p50'],
            'promote_for_further_testing': cand['families']['poison']['complete']>base['families']['poison']['complete'] and cand['families']['clean']['recall']>=base['families']['clean']['recall'] and cand['families']['unlabeled']['recall']>=base['families']['unlabeled']['recall'] and cand['laundered_conflict_descendants']==0,
        },
        'limitations':[
            'The poisoned graph and query cues are model-authored and deliberately expose the tested failure mode.',
            'The comparison isolates graph-navigation behavior; it does not compare against dense/late-interaction retrieval.',
            'The query cue stored on dependency edges is richer than many real graphs; missing/incorrect edge labels can reduce the gain.',
            'Self-hosted Ubuntu replication is required before any integration claim.',
        ],
    }
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__': main()
