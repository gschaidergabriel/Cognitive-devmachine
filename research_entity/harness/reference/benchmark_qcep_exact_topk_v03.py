from __future__ import annotations

"""Three-way QCEP-0.3 falsifier on the current H1 StateLedger/QueryPlane.

Methods:
1. current main EAP-EXACT-TOPK static monotone ranking;
2. QCEP-0.3 query-conditioned ranking with full expansion;
3. QCEP-0.3 query-conditioned ranking with exact score-bound Top-K stop.

The fixture deliberately mixes high-weight generic hub drift, clean graphs, missing-edge-label
OOD controls and CONFLICT laundering traps. It is synthetic mechanism evidence, but it runs
through the real current StateLedger transaction and current exact-TopK EAP implementation.
"""

import json,math,random,statistics,time
from typing import Any

from .state_ledger import StateLedger
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_exact_topk import ExactTopKUnifiedDBEmergentPlane
from .unifieddb_emergent_preprocessor import PossibilitySpec
from .query_conditioned_evidence_projection import QueryConditionedEvidenceProjector,QueryEvidenceSpec

POISON=45
CLEAN=30
UNLABELED=15
K=4
MAX_HOPS=3
FRONTIER=512


def percentile(xs,q):
    ys=sorted(xs); p=(len(ys)-1)*q; lo=math.floor(p); hi=math.ceil(p)
    return ys[lo] if lo==hi else ys[lo]*(hi-p)+ys[hi]*(p-lo)

def stats(xs):
    return {'min':min(xs),'p50':percentile(xs,.5),'p95':percentile(xs,.95),'p99':percentile(xs,.99),'max':max(xs),'mean':statistics.mean(xs)}

def quality(got,truth):
    got=got[:K]; ts=set(truth); gs=set(got); hit=len(gs&ts)
    precision=hit/max(1,len(gs)); recall=hit/len(ts); complete=float(ts.issubset(gs))
    dcg=sum((1.0 if ref in ts else 0.0)/math.log2(i+2) for i,ref in enumerate(got))
    idcg=sum(1.0/math.log2(i+2) for i in range(len(truth)))
    return {'precision':precision,'recall':recall,'complete':complete,'ndcg':dcg/idcg}

def build_ops_and_cases():
    ops=[]; cases=[]; total=POISON+CLEAN+UNLABELED
    for i in range(total):
        family='poison' if i<POISON else ('clean' if i<POISON+CLEAN else 'unlabeled')
        p=f'v03_{i:03d}'; root=f'semantic:{p}_root'; truth=[root]
        def sem(key,value,epistemic='KNOWN',status='CURRENT'):
            ops.append({'op':'SET','domain':'semantic','key':key,'value':value,'epistemic':epistemic,'status':status})
        def dep(key,value):
            ops.append({'op':'SET','domain':'dependency','key':key,'value':value,'epistemic':'KNOWN','status':'CURRENT'})
        sem(f'{p}_root',{'text':'neutral anchor'})
        cue=f'zircon{i:03d} target constraint evidence'; prev=root
        for hop in range(3):
            ref=f'semantic:{p}_rel{hop}'; truth.append(ref); sem(f'{p}_rel{hop}',{'text':'neutral payload'})
            weight=(.72,.91,.89)[hop] if family=='poison' else (.96,.93,.90)[hop]
            value={'source':prev,'target':ref,'strength':weight,'relation_type':'SUPPORTS'}
            if family!='unlabeled': value['query_cue']=cue
            dep(f'{p}_chain{hop}',value); prev=ref
        hub=f'semantic:{p}_hub'; sem(f'{p}_hub',{'text':'generic association hub'})
        dep(f'{p}_hubedge',{'source':root,'target':hub,'strength':.99 if family=='poison' else .60,'relation_type':'RELATED','query_cue':'generic association'})
        for j in range(12):
            d=f'semantic:{p}_d{j:02d}'; sem(f'{p}_d{j:02d}',{'text':'generic unrelated'})
            dep(f'{p}_hd{j:02d}',{'source':hub,'target':d,'strength':.98,'relation_type':'RELATED','query_cue':'generic association'})
        conflict=f'semantic:{p}_conflict'; launder=f'semantic:{p}_launder'
        sem(f'{p}_conflict',{'text':'uncertain'},'CONFLICT'); sem(f'{p}_launder',{'text':'must not relay'})
        dep(f'{p}_conflictedge',{'source':root,'target':conflict,'strength':1.0,'relation_type':'SUPPORTS','query_cue':cue})
        dep(f'{p}_launderedge',{'source':conflict,'target':launder,'strength':1.0,'relation_type':'SUPPORTS','query_cue':cue})
        cases.append({'id':p,'family':family,'query':cue,'seed':root,'truth':truth,'launder':launder})
    return ops,cases

def summarize(rows):
    families={}
    for fam in ('poison','clean','unlabeled'):
        xs=[r for r in rows if r['family']==fam]
        families[fam]={k:statistics.mean(r[k] for r in xs) for k in ('precision','recall','complete','ndcg')}
    return families

def main():
    ledger=StateLedger(); plane=UnifiedDBQueryPlane(ledger); ops,cases=build_ops_and_cases()
    plane.transact(event_id='qcep-v03-seed',idem='qcep-v03-seed',base_epoch=ledger.epoch,event_type='QCEP_V03_SEED',writer='benchmark',ops=ops,provenance={'benchmark':'QCEP_V03_EXACT_TOPK'})
    static=ExactTopKUnifiedDBEmergentPlane(plane); qcep=QueryConditionedEvidenceProjector(ledger)
    order=cases[:]; random.Random(103).shuffle(order)

    def run_static(c):
        return static.compile_active_assembly(PossibilitySpec('static-'+c['id'],seed_refs=(c['seed'],),query_text=c['query'],basis_epoch=ledger.epoch,max_items=K,max_hops=MAX_HOPS,frontier_budget=FRONTIER,min_edge_weight=0.0))
    def run_qcep(c,exact):
        return qcep.project(QueryEvidenceSpec('qcep-'+('exact-' if exact else 'full-')+c['id'],c['query'],(c['seed'],),ledger.epoch,max_items=K,max_hops=MAX_HOPS,frontier_budget=FRONTIER,min_edge_weight=0.0,exact_top_k_stop=exact))
    methods={'static_exact_topk':run_static,'qcep_full':lambda c:run_qcep(c,False),'qcep_exact_topk':lambda c:run_qcep(c,True)}
    result={}
    signatures={}
    for name,fn in methods.items():
        lat=[]; expansions=[]; rows=[]; sig={}; launder=0; stops={}
        for c in order:
            t=time.perf_counter_ns(); out=fn(c); lat.append((time.perf_counter_ns()-t)/1000.0)
            got=[x['ref'] for x in out['selected']]; expansions.append(out['frontier_expansions']); q=quality(got,c['truth']); q['family']=c['family']; rows.append(q)
            sig[c['id']]=[(x['ref'],x['activation_score'],x['hop']) for x in out['selected']]
            launder+=int(c['launder'] in got); reason=out.get('frontier_stop_reason','UNKNOWN'); stops[reason]=stops.get(reason,0)+1
        result[name]={'families':summarize(rows),'overall':{k:statistics.mean(r[k] for r in rows) for k in ('precision','recall','complete','ndcg')},'latency_us':stats(lat),'frontier_expansions':stats(expansions),'laundered_conflict_descendants':launder,'stop_reasons':stops}
        signatures[name]=sig

    static_r=result['static_exact_topk']; full=result['qcep_full']; exact=result['qcep_exact_topk']
    exact_equivalent=signatures['qcep_full']==signatures['qcep_exact_topk']
    gate={
        'qcep_exact_equals_qcep_full_all_queries':exact_equivalent,
        'poison_complete_delta_vs_static':exact['families']['poison']['complete']-static_r['families']['poison']['complete'],
        'clean_recall_delta_vs_static':exact['families']['clean']['recall']-static_r['families']['clean']['recall'],
        'unlabeled_recall_delta_vs_static':exact['families']['unlabeled']['recall']-static_r['families']['unlabeled']['recall'],
        'frontier_p50_reduction_vs_qcep_full':1.0-(exact['frontier_expansions']['p50']/full['frontier_expansions']['p50']),
        'latency_p50_ratio_vs_qcep_full':exact['latency_us']['p50']/full['latency_us']['p50'],
        'qcep_laundered_conflict_descendants':exact['laundered_conflict_descendants'],
    }
    gate['promote_for_u15_falsifier']=(exact_equivalent and gate['poison_complete_delta_vs_static']>0 and gate['clean_recall_delta_vs_static']>=0 and gate['unlabeled_recall_delta_vs_static']>=0 and gate['frontier_p50_reduction_vs_qcep_full']>0 and gate['qcep_laundered_conflict_descendants']==0)
    output={'schema_version':'1.0','benchmark':'QCEP_0_3_QUERY_CONDITIONED_EXACT_TOPK','evidence_class':'EXECUTED_CURRENT_H1_HARNESS_WHEN_RUN','pinned_baseline_sha':'5975dbd54478caf548fc6f4ee7f4c4bf95ab1a61','dataset':{'cases':len(cases),'poison':POISON,'clean':CLEAN,'unlabeled':UNLABELED,'k':K,'max_hops':MAX_HOPS,'ops':len(ops)},'methods':result,'candidate_gate':gate,'scope_guard':'Synthetic mechanism stress through current H1 StateLedger/QueryPlane and current EAP ExactTopK. Not universal DB superiority, not real Clay NL corpus, not downstream Frank quality.','limitations':['Dependency query cues are deliberately constructed to expose hub drift.','Real graph edge metadata may be sparser; unlabeled/OOD family tests fail-open-to-static semantics only.','QCEP relevance computation adds CPU work; exact stop must be judged on total latency as well as frontier expansion.','A supported result advances only to U15/real-corpus falsification, not architecture promotion.']}
    print(json.dumps(output,indent=2,sort_keys=True)); ledger.close()

if __name__=='__main__': main()
