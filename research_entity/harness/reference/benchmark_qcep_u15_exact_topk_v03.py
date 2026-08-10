from __future__ import annotations

"""QCEP-0.3.2 as the current U15 typed evidence-gap deepener.

Same authoritative H1 StateLedger/QueryPlane, same explicit U15 requirement, same item budget.
Control uses current static EAP-EXACT-TOPK. Candidate uses QCEP-0.3.2 exact Top-K and binds
U15's typed unresolved gap terms as explicit focus terms. Only CURRENT/KNOWN evidence tags can
close the gap; rank/text/focus activation itself never becomes proof.
"""

import json,math,random,statistics,time
from .state_ledger import StateLedger
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_exact_topk import ExactTopKUnifiedDBEmergentPlane
from .unifieddb_emergent_preprocessor import PossibilitySpec
from .query_conditioned_evidence_projection import QueryConditionedEvidenceProjector,QueryEvidenceSpec
from research_entity.runtime.semantic_gap_controller_v15 import EvidenceItem,EvidenceRequirement,SufficiencyGapControllerV15

POISON=45; CLEAN=30; UNLABELED=15; MAX_ITEMS=4

def percentile(xs,q):
    ys=sorted(xs); p=(len(ys)-1)*q; lo=math.floor(p); hi=math.ceil(p)
    return ys[lo] if lo==hi else ys[lo]*(hi-p)+ys[hi]*(p-lo)
def stats(xs): return {'p50':percentile(xs,.5),'p95':percentile(xs,.95),'p99':percentile(xs,.99),'mean':statistics.mean(xs),'min':min(xs),'max':max(xs)}
def tags(value):
    if not isinstance(value,dict): return frozenset()
    raw=value.get('evidence_tags',())
    return frozenset(str(x) for x in raw if str(x).strip()) if isinstance(raw,(list,tuple,set)) else frozenset()

def build():
    ops=[]; cases=[]; total=POISON+CLEAN+UNLABELED
    for i in range(total):
        fam='poison' if i<POISON else ('clean' if i<POISON+CLEAN else 'unlabeled'); p=f'u15v03_{i:03d}'
        root=f'semantic:{p}_root'; target=None
        def sem(key,value,epi='KNOWN',status='CURRENT'): ops.append({'op':'SET','domain':'semantic','key':key,'value':value,'epistemic':epi,'status':status})
        def dep(key,value): ops.append({'op':'SET','domain':'dependency','key':key,'value':value,'epistemic':'KNOWN','status':'CURRENT'})
        sem(f'{p}_root',{'text':'anchor','evidence_tags':['anchor']}); prev=root
        for hop in range(3):
            ref=f'semantic:{p}_rel{hop}'; target=ref if hop==2 else target
            sem(f'{p}_rel{hop}',{'text':'neutral payload','evidence_tags':['target'] if hop==2 else [f'bridge{hop}']})
            w=(.72,.91,.89)[hop] if fam=='poison' else (.96,.93,.90)[hop]
            v={'source':prev,'target':ref,'strength':w,'relation_type':'SUPPORTS'}
            if fam!='unlabeled': v['query_cue']='target evidence'
            dep(f'{p}_chain{hop}',v); prev=ref
        hub=f'semantic:{p}_hub'; sem(f'{p}_hub',{'text':'generic hub','evidence_tags':['background']})
        dep(f'{p}_hubedge',{'source':root,'target':hub,'strength':.99 if fam=='poison' else .60,'relation_type':'RELATED','query_cue':'generic association'})
        for j in range(12):
            d=f'semantic:{p}_d{j:02d}'; sem(f'{p}_d{j:02d}',{'text':'generic distractor','evidence_tags':['background']})
            dep(f'{p}_hd{j:02d}',{'source':hub,'target':d,'strength':.98,'relation_type':'RELATED','query_cue':'generic association'})
        conflict=f'semantic:{p}_conflict'; launder=f'semantic:{p}_launder'
        sem(f'{p}_conflict',{'text':'uncertain','evidence_tags':['target']},'CONFLICT'); sem(f'{p}_launder',{'text':'must not close gap','evidence_tags':['target']})
        dep(f'{p}_conflictedge',{'source':root,'target':conflict,'strength':1.0,'relation_type':'SUPPORTS','query_cue':'target evidence'})
        dep(f'{p}_launderedge',{'source':conflict,'target':launder,'strength':1.0,'relation_type':'SUPPORTS','query_cue':'target evidence'})
        cases.append({'id':p,'family':fam,'root':root,'target':target,'launder':launder,'query':'need target evidence'})
    return ops,cases

def main():
    ledger=StateLedger(); qp=UnifiedDBQueryPlane(ledger); ops,cases=build()
    qp.transact(event_id='qcep-u15-v03-seed',idem='qcep-u15-v03-seed',base_epoch=ledger.epoch,event_type='QCEP_U15_V03_SEED',writer='benchmark',ops=ops,provenance={'benchmark':'QCEP_U15_V03'})
    static=ExactTopKUnifiedDBEmergentPlane(qp); qcep=QueryConditionedEvidenceProjector(ledger)
    row_by_ref={f"{r['domain']}:{r['key']}":r for r in ledger.materialized()}
    def ev(refs):
        out=[]
        for ref in refs:
            r=row_by_ref.get(ref)
            if not r or r['domain']=='dependency': continue
            out.append(EvidenceItem(ref=ref,tags=tags(r.get('value')),provenance_valid=(r['epistemic']=='KNOWN' and r['status']=='CURRENT'),status=r['status']))
        return out
    def static_expand(query,gaps,selected,source_epoch,graph_epoch,budget):
        out=static.compile_active_assembly(PossibilitySpec('u15-static-'+str(abs(hash((query,gaps,selected)))),seed_refs=tuple(selected),query_text='',basis_epoch=source_epoch,max_items=max(1,budget+len(selected)),max_hops=3,frontier_budget=512,min_edge_weight=0.0))
        seen=set(selected); return ev([x['ref'] for x in out['selected'] if x['ref'] not in seen][:budget])
    def qcep_expand(query,gaps,selected,source_epoch,graph_epoch,budget):
        conditioned=' '.join([query,*gaps]); seen=set(selected)
        out=qcep.project(QueryEvidenceSpec('u15-qcep-'+str(abs(hash((query,gaps,selected)))),conditioned,tuple(selected),source_epoch,max_items=max(1,budget+len(selected)),max_hops=3,frontier_budget=512,min_edge_weight=0.0,exact_top_k_stop=True,focus_terms=tuple(gaps)))
        return ev([x['ref'] for x in out['selected'] if x['ref'] not in seen][:budget])
    methods={'u15_static_exact_topk':SufficiencyGapControllerV15(expand=static_expand,max_rounds=1,max_items=MAX_ITEMS),'u15_qcep_0_3_2_exact_topk':SufficiencyGapControllerV15(expand=qcep_expand,max_rounds=1,max_items=MAX_ITEMS)}
    order=cases[:]; random.Random(107).shuffle(order); result={}
    for name,ctl in methods.items():
        lat=[]; rows=[]
        for c in order:
            initial=[EvidenceItem(c['root'],frozenset({'anchor'}))]; t=time.perf_counter_ns()
            rec=ctl.assemble(query_id=name+':'+c['id'],query_text=c['query'],source_epoch=ledger.epoch,graph_epoch=ledger.epoch,initial_items=initial,requirements=[EvidenceRequirement('target_requirement',required_tags=frozenset({'target'}))])
            lat.append((time.perf_counter_ns()-t)/1000.0); rows.append({'family':c['family'],'sufficient':float(rec.final_sufficient),'target':float(c['target'] in rec.selected_refs),'launder':float(c['launder'] in rec.selected_refs),'rounds':rec.deepening_rounds})
        fam={}
        for f in ('poison','clean','unlabeled'):
            xs=[x for x in rows if x['family']==f]; fam[f]={k:statistics.mean(x[k] for x in xs) for k in ('sufficient','target','launder','rounds')}
        result[name]={'families':fam,'latency_us':stats(lat)}
    b=result['u15_static_exact_topk']; c=result['u15_qcep_0_3_2_exact_topk']
    gate={'poison_sufficiency_delta':c['families']['poison']['sufficient']-b['families']['poison']['sufficient'],'clean_sufficiency_delta':c['families']['clean']['sufficient']-b['families']['clean']['sufficient'],'unlabeled_sufficiency_delta':c['families']['unlabeled']['sufficient']-b['families']['unlabeled']['sufficient'],'qcep_max_launder_rate':max(c['families'][f]['launder'] for f in ('poison','clean','unlabeled'))}
    gate['promote_for_real_corpus_falsifier']=gate['poison_sufficiency_delta']>0 and gate['clean_sufficiency_delta']>=0 and gate['unlabeled_sufficiency_delta']>=0 and gate['qcep_max_launder_rate']==0
    print(json.dumps({'schema_version':'1.1','benchmark':'QCEP_0_3_2_U15_EXPLICIT_GAP_CLOSURE','evidence_class':'EXECUTED_CURRENT_H1_HARNESS_WHEN_RUN','pinned_baseline_sha':'5975dbd54478caf548fc6f4ee7f4c4bf95ab1a61','dataset':{'cases':len(cases),'poison':POISON,'clean':CLEAN,'unlabeled':UNLABELED,'max_items':MAX_ITEMS,'ops':len(ops)},'methods':result,'candidate_gate':gate,'candidate_rule':'U15 gap_terms are bound as QCEP focus_terms; focus activation affects rank only and does not satisfy U15 requirements itself.','scope_guard':'Explicit tagged U15 evidence-gap closure through current H1 StateLedger/QueryPlane. Rank/text/focus cannot itself close gaps. Synthetic mechanism evidence only.','limitations':['Synthetic graph/query cues expose hub drift deliberately.','Real Clay evidence tags and relation metadata can be sparser.','Downstream model/tool outcome quality is not measured.','Supported result advances to held-out real Clay and fair cross-engine tests only.']},indent=2,sort_keys=True)); ledger.close()

if __name__=='__main__': main()
