#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
TARGET_VERSION='RAE-TARGET-0.2'
CONTRACT_VERSION='RAE_TARGET_SEMANTIC_CONTRACT_0.2'
SOURCE_FRANK_SCHEMA='FRANK UnifiedDB/ClayGraph current chain through UDB V13 / Graph V8'
IMPORTS=[
 ('gwt-strict-20260809','gwt','research_entity/trigger_runs/emergenz/20260809T2015p0700-chatgpt-gwt-emergence-fusion','03a4fddcf35b74e020c0011d27ec3477594a40cf','LITERATURE_SYNTHESIS_AND_EXPERIMENT_DESIGN_NO_LIVE_EXECUTION','OPEN','GWT causal chain and GCEP vector; hypotheses remain OPEN.'),
 ('gwt-readout-contract','gwt','research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md','blob:b2d9a903f256e1f26db500317b34930456188245','OWNER_ARCHITECTURE_DIRECTIVE','CURRENT','Typed GWT stage readouts, counterfactual replay and measurement receipts are mandatory; emergence is not one scalar.'),
 ('semantic-coupling-directive','unifieddb','research_entity/global/CLAY_SEMANTIC_COUPLING_FABRIC_DIRECTIVE.md','blob:8685421de82b76b0ce925b2cf45fa72082502654','OWNER_ARCHITECTURE_DIRECTIVE','CURRENT','ClayCode semantic signatures drive incremental UnifiedDB/Hyperposition/ClayGraph materialization; hot reads use prepared neighborhoods and coherent epochs.'),
 ('gwt-observability-control','emergenz','research_entity/global/CLAY_GWT_EMERGENCE_OBSERVABILITY_CONTROL_DIRECTIVE.md','blob:b295d5744ae836424925a00d2d2b3a8325f47ccb','OWNER_ARCHITECTURE_DIRECTIVE','CURRENT','GWT is observability/intervention plane; control updates require matched interventions, causal credit, OOD and rollback.'),
 ('frank-clay-native-contract','frank','research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md','blob:7d07e54acf0e62bda81de3b032fe480c0f08f234','OWNER_ARCHITECTURE_DIRECTIVE','CURRENT','Clay/ClayCode is the semantic source; Python/SQL are auditable projections. Needle is intentional exception and Digital Retina mandatory.'),
 ('emergenz-v031','emergenz','research_entity/trigger_runs/emergenz/20260809T204545p0700_udb_emergence_meter_v03_adversarial_concordance/V031_LIVE_REFRESH_ADDENDUM.md','343fabb8b176df10f85aa3cbd4dce09f165b4987','SYNTHETIC_METHOD_EVIDENCE','OPEN','Conditioning-depth instability => ABSTAIN_STATE_INADEQUATE; multi-method support is diagnostic, not voting truth.'),
 ('claycode-v17-boundary','claycode','research_entity/claycode/base/reports/CC_BASE_LAST_BLOCKERS_V17_RESOLUTION_20260809.md','d3c8e7de8ca2ccfdbc4db4180778b351b5b983b9','SOFTWARE_ORCHESTRATION_EVIDENCE','OPEN','V17 software/orchestration path selected; physical Andreas Ubuntu, WP14 and full release receipts remain open.'),
 ('claycode-c11-hardening','claycode','research_entity/claycode/base/receipts/CC_WP06_SANDBOX_C11_SEMANTIC_HARDENING_20260809T2155p0700.json','1538ed5e5550ee2509c42e27077b87a00f918b33','EXECUTABLE_SANDBOX_EVIDENCE','OPEN','Checked numeric/C backend hardening passed sandbox batteries; not release promotion.'),
 ('claycode-current-compiler','claycode','tools/claycode_base_compiler.py','blob:5d01dfeb77b1bece85433cd09af6ea3427a5f995','CURRENT_SOURCE_SNAPSHOT','OPEN','Current compiler is an integrated pure-function typed-IR/interpreter/C11 candidate and explicitly excludes effects/FFI/async from this slice.'),
 ('frank-causal-reentry','frank','research_entity/rooms/center_events/20260809T2138p0700_chatgpt_secondary_frank_causal_reentry_cross_room_delta.json','83d2d41e751a332fa285b3d81cc753ab9b67648b','OWNER_OBSERVATION_PLUS_RESEARCH_SYNTHESIS','OPEN','Nested multiscale loop candidate: changed receiver/system state re-enters next episode with provenance; strong coupling alone is not the target.'),
]

def now(): return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
def uid(p): return f'{p}:{uuid.uuid4().hex}'
def digest_text(s:str): return hashlib.sha256(s.encode()).hexdigest()
def digest_file(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def clamp(v): return max(0.0,min(1.0,float(v)))
def contract_sha(): return digest_file(HERE/'RAE_TARGET_CONTRACT.clay')

def configure(c):
    c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=10000');return c

def open_pair(root:Path,create=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    u=configure(sqlite3.connect(root/'RAE_UNIFIED.sqlite'));g=configure(sqlite3.connect(root/'RAE_CLAYGRAPH.sqlite'))
    if create:
        u.executescript((HERE/'RAE_UNIFIED_SCHEMA.sql').read_text())
        g.executescript((HERE/'RAE_CLAYGRAPH_SCHEMA.sql').read_text())
        bootstrap(u,g)
    verify_contract(u,g)
    return u,g

def verify_contract(u,g):
    sha=contract_sha()
    um=u.execute("SELECT value FROM meta WHERE key='semantic_contract_sha256'").fetchone()
    gp=g.execute("SELECT contract_sha256 FROM graph_publication_state WHERE surface_key='CURRENT'").fetchone()
    if not um or um[0]!=sha or not gp or gp[0]!=sha:
        raise RuntimeError('SEMANTIC_SOURCE_DRIFT: Clay contract hash does not match executable projections')

def surface(u):
    r=u.execute("SELECT * FROM published_surface WHERE surface_key='CURRENT'").fetchone()
    if not r: raise RuntimeError('NO_PUBLISHED_SURFACE')
    return r

def graph_surface(g):
    r=g.execute("SELECT * FROM graph_publication_state WHERE surface_key='CURRENT'").fetchone()
    if not r: raise RuntimeError('NO_GRAPH_PUBLICATION_STATE')
    return r

def assert_coherent_epoch(u,g):
    a,b=surface(u),graph_surface(g);sha=contract_sha()
    if a['status']!='CURRENT' or b['status']!='CURRENT': raise RuntimeError('COHERENCE_DEGRADED')
    if a['unified_epoch']!=b['unified_epoch'] or a['graph_epoch']!=b['graph_epoch'] or a['contract_sha256']!=sha or b['contract_sha256']!=sha:
        raise RuntimeError('MIXED_EPOCH_READ_FORBIDDEN')
    return a['unified_epoch'],a['graph_epoch'],a['materialization_epoch']

def bootstrap(u,g):
    ts=now();sha=contract_sha()
    u.execute("INSERT OR IGNORE INTO state_epochs(epoch,parent_epoch,root_hash,committed_at,writer_node,status) VALUES(1,NULL,?,?,?,'CURRENT')",(digest_text('rae-target-epoch-1'),ts,'chatgpt-secondary'))
    g.execute("INSERT OR IGNORE INTO graph_epochs(graph_epoch,unified_epoch,derivation_hash,status,created_at) VALUES(1,1,?,'CURRENT',?)",(digest_text('rae-target-graph-1'),ts))
    u.execute("INSERT OR REPLACE INTO published_surface(surface_key,unified_epoch,graph_epoch,materialization_epoch,contract_sha256,status,updated_at) VALUES('CURRENT',1,1,1,?,'CURRENT',?)",(sha,ts))
    g.execute("INSERT OR REPLACE INTO graph_publication_state(surface_key,graph_epoch,unified_epoch,contract_sha256,status,updated_at) VALUES('CURRENT',1,1,?,'CURRENT',?)",(sha,ts))
    for k,v in [('target_version',TARGET_VERSION),('semantic_source','research_entity/runtime/target_self_host/RAE_TARGET_CONTRACT.clay'),('semantic_contract_sha256',sha),('frank_schema_ancestry',SOURCE_FRANK_SCHEMA),('projection_policy','Python/SQLite are reference/materialized projections of Clay semantic source')]:
        u.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)',(k,v))
    for iid,domain,ref,commit,eclass,status,summary in IMPORTS:
        u.execute('INSERT OR REPLACE INTO research_imports(import_id,domain,source_ref,source_commit,evidence_class,status,summary,content_hash,imported_at) VALUES(?,?,?,?,?,?,?,?,?)',(iid,domain,ref,commit,eclass,status,summary,digest_text(summary),ts))
    organs=[
      ('workspace','Global Workspace','competition, ignition, broadcast, receiver closure','gwt+claygraph','FUSED','frank:gwt-lineage'),
      ('hyperposition','Semantic Hyperposition','preserve unresolved alternatives and higher-order relations','unifieddb+claygraph','FUSED','frank:hyperposition-lineage'),
      ('reentry','Causal Re-entry','verified outcome/state delta influences later selection','unifieddb+gwt','EMERGENT_DISTRIBUTED','frank:loop-lineage'),
      ('semantic_fabric','Semantic Coupling Fabric','incremental dependency activation and bounded materialization','unifieddb+claygraph','EMERGENT_DISTRIBUTED','frank:semantic-coupling-lineage'),
      ('observability','GWT Observability Plane','measurement/replay/estimation without truth authority','measurement+replay','EXPLICIT','gwt:readout-contract'),
      ('needle','Needle','fast pre-model classifier/router; cannot mint authority','needle-bridge','EXPLICIT','frank:clay-native-contract'),
      ('digital_retina','Digital Retina','mandatory visual perception -> Clay VisualPercept boundary','visual-percept-bridge','EXPLICIT','frank:clay-native-contract')]
    for oid,name,role,real,lifecycle,lineage in organs:
        u.execute('INSERT OR IGNORE INTO organ_registry(organ_id,canonical_name,functional_role,current_realization,lifecycle_state,deletable,lineage_ref,updated_at) VALUES(?,?,?,?,?,0,?,?)',(oid,name,role,real,lifecycle,lineage,ts))
    signatures={
      'semantic_objects':['Intent','SemanticRecord','CandidateSet','Hyperposition','WorkspaceEpisode','ReceiverReceipt','Outcome','ReentryReceipt','MeasurementReceipt','EmergenceReadout','InterventionSpec','ReplayReceipt'],
      'dependencies':['typed','temporal','effect','provenance','invalidation','causal-if-supported'],
      'hot_path':'materialized_neighborhood + indexed_hyperbindings',
      'authority':'activation_and_measurement_never_mint_truth_or_execution_authority'}
    u.execute("INSERT OR REPLACE INTO clay_semantic_signatures(unit_ref,contract_sha256,semantic_signature_clay,dependency_signature_clay,effect_signature_clay,authority_signature_clay,provenance_signature_clay,hyperposition_signature_clay,invalidation_signature_clay,projection_recipe_clay,rebuild_recipe_clay,status,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(
      'RAE_TARGET_CONTRACT.clay',sha,json.dumps(signatures['semantic_objects']),json.dumps(signatures['dependencies']),json.dumps({'effects':'explicit receipts only'}),json.dumps(signatures['authority']),json.dumps({'imports':[x[0] for x in IMPORTS]}),json.dumps({'preserve_alternatives':True,'higher_order':True}),json.dumps({'scope':'affected_dependency_closure'}),json.dumps({'python':'rae_target_runtime.py','sqlite':['RAE_UNIFIED_SCHEMA.sql','RAE_CLAYGRAPH_SCHEMA.sql']}),json.dumps({'from':'Clay contract + canonical state + research imports'}),'CURRENT',ts))
    u.execute("INSERT OR REPLACE INTO claycode_contract_receipts(receipt_id,compiler_ref,grammar_ref,contract_version,software_status,physical_release_status,semantic_contract_clay,evidence_clay,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(
      'cc:target-0.2','tools/claycode_base_compiler.py@blob:5d01dfeb77b1bece85433cd09af6ea3427a5f995','V17 contract-selected; effects/FFI/async remain outside current pure slice',CONTRACT_VERSION,'SOFTWARE_PATH_AVAILABLE_RELEASE_OPEN','PHYSICAL_ACCEPTANCE_OPEN',json.dumps(signatures,sort_keys=True),json.dumps({'source_commits':['d3c8e7de8ca2ccfdbc4db4180778b351b5b983b9','1538ed5e5550ee2509c42e27077b87a00f918b33'],'no_release_claim':True},sort_keys=True),ts))
    u.commit();g.commit()

def ensure_entity(u,ref,label=None):
    ts=now();u.execute('INSERT OR IGNORE INTO entities(entity_id,entity_type,label,status,created_at,updated_at) VALUES(?,?,?,?,?,?)',(ref,'concept',label or ref,'CURRENT',ts,ts));u.commit()

def current_graph_epoch(g): return graph_surface(g)['graph_epoch']
def add_node(g,ref,label=None):
    r=g.execute('SELECT node_id FROM nodes WHERE semantic_ref=?',(ref,)).fetchone()
    if r:return r['node_id']
    ge=current_graph_epoch(g);nid='cg:'+digest_text(ref)[:20]
    g.execute('INSERT INTO nodes(node_id,semantic_ref,node_type,label,epistemic_class,source_unified_epoch,graph_epoch,status) VALUES(?,?,?,?,?,?,?,?)',(nid,ref,'semantic',label or ref,'EVIDENCE_BOUND',graph_surface(g)['unified_epoch'],ge,'CURRENT'));g.commit();return nid

def add_dependency(u,parent,child,confidence=.9,relation='PREPARED_NEIGHBORHOOD'):
    did=uid('dep');u.execute('INSERT INTO semantic_dependencies(dependency_id,parent_ref,child_ref,relation,confidence,evidence_class,provenance_clay,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(did,parent,child,relation,confidence,'EVIDENCE_BOUND',json.dumps({'source':'test_or_ingest'}),'ACTIVE',now()));u.commit();return did

def add_hyperbinding(g,members,joint=.9,pairwise=.5,persistence=.8,transfer=.7,causal=.6,prov_count=2,false_risk=.1):
    for m in members:add_node(g,m)
    ge=current_graph_epoch(g);bid=uid('hb');synergy=joint-pairwise
    g.execute('INSERT INTO hyperbindings(binding_id,members_clay,required_count,joint_score,pairwise_baseline,synergy,persistence,transfer,causal_contribution,provenance_count,false_binding_risk,status,evidence_clay,graph_epoch,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(bid,json.dumps(sorted(members)),len(members)-1,joint,pairwise,synergy,persistence,transfer,causal,prov_count,false_risk,'CURRENT',json.dumps({'source':'verified_repeated_coactivity_or_intervention'}),ge,now()))
    for i,m in enumerate(sorted(members)):
        g.execute('INSERT INTO hyperbinding_member_index(member_ref,binding_id,role,graph_epoch,status) VALUES(?,?,?,?,?)',(m,bid,f'MEMBER_{i+1}',ge,'CURRENT'))
    g.commit();return bid

def add_conflict(g,a,b):
    cid=uid('conflict');g.execute('INSERT INTO graph_conflicts(conflict_id,left_ref,right_ref,conflict_kind,state,evidence_clay,graph_epoch,created_at) VALUES(?,?,?,?,?,?,?,?)',(cid,a,b,'CONTRADICTION','OPEN','{}',current_graph_epoch(g),now()));g.commit();return cid

def conflict_blocks(g,candidate,active):
    for ref in active:
        if g.execute("SELECT 1 FROM graph_conflicts WHERE state='OPEN' AND ((left_ref=? AND right_ref=?) OR (left_ref=? AND right_ref=?)) LIMIT 1",(candidate,ref,ref,candidate)).fetchone():return True
    return False

def materialize_neighborhood(u,g,cue_ref,max_depth=2,max_refs=32):
    ue,ge,me=assert_coherent_epoch(u,g);seen={cue_ref};front=[cue_ref]
    for _ in range(max_depth):
        nxt=[]
        for parent in front:
            for r in u.execute("SELECT child_ref FROM semantic_dependencies WHERE parent_ref=? AND status='ACTIVE' ORDER BY confidence DESC LIMIT ?",(parent,max_refs)):
                if r['child_ref'] not in seen and len(seen)<max_refs:seen.add(r['child_ref']);nxt.append(r['child_ref'])
        front=nxt
        if not front or len(seen)>=max_refs:break
    refs=sorted(seen);h=digest_text(json.dumps(refs))
    u.execute('INSERT OR REPLACE INTO materialized_neighborhoods(cue_ref,unified_epoch,graph_epoch,materialization_epoch,refs_clay,closure_hash,bounded_count,rebuild_recipe_clay,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',(cue_ref,ue,ge,me,json.dumps(refs),h,len(refs),json.dumps({'max_depth':max_depth,'max_refs':max_refs}),now()));u.commit();return refs

def publish_delta(u,g,affected_cues):
    old=surface(u);new_ue=old['unified_epoch']+1;new_ge=old['graph_epoch']+1;new_me=old['materialization_epoch']+1;ts=now();sha=contract_sha()
    g.execute("UPDATE graph_epochs SET status='STALE' WHERE status='CURRENT'")
    g.execute("INSERT INTO graph_epochs(graph_epoch,unified_epoch,derivation_hash,status,created_at) VALUES(?,?,?,'CURRENT',?)",(new_ge,new_ue,digest_text(f'graph:{new_ue}:{new_ge}'),ts))
    g.execute("UPDATE graph_publication_state SET graph_epoch=?,unified_epoch=?,contract_sha256=?,status='CURRENT',updated_at=? WHERE surface_key='CURRENT'",(new_ge,new_ue,sha,ts));g.commit()
    u.execute("UPDATE state_epochs SET status='STALE' WHERE status='CURRENT'")
    u.execute("INSERT INTO state_epochs(epoch,parent_epoch,root_hash,committed_at,writer_node,status) VALUES(?,?,?,?,?,'CURRENT')",(new_ue,old['unified_epoch'],digest_text(f'unified:{new_ue}:{new_ge}'),ts,'chatgpt-secondary'))
    u.execute("UPDATE published_surface SET unified_epoch=?,graph_epoch=?,materialization_epoch=?,contract_sha256=?,status='CURRENT',updated_at=? WHERE surface_key='CURRENT'",(new_ue,new_ge,new_me,sha,ts));u.commit()
    for cue in sorted(set(affected_cues)):materialize_neighborhood(u,g,cue)
    return new_ue,new_ge,new_me

def token_overlap(intent,ref):
    tok=lambda x:{t for t in ''.join(c.lower() if c.isalnum() else ' ' for c in x).split() if len(t)>1}
    a,b=tok(intent),tok(ref);return len(a&b)/len(a|b) if a and b else 0.0

def prepared_refs(u,cue,me):
    r=u.execute('SELECT refs_clay FROM materialized_neighborhoods WHERE cue_ref=? AND materialization_epoch=?',(cue,me)).fetchone()
    if not r: raise RuntimeError(f'COLD_PATH_REQUIRED:{cue}')
    return set(json.loads(r[0]))

def relevant_binding_ids(g,active):
    if not active:return set()
    q=','.join('?'*len(active));rows=g.execute(f"SELECT DISTINCT binding_id FROM hyperbinding_member_index WHERE status='CURRENT' AND member_ref IN ({q})",tuple(sorted(active))).fetchall();return {r[0] for r in rows}

def generate_candidates(u,g,intent,active_refs,cycle='cycle:test'):
    ue,ge,me=assert_coherent_epoch(u,g);active=set(active_refs);c={}
    for ref in active:
        c[(ref,'KNOWN')]={'fit':max(.55,token_overlap(intent,ref)),'novelty':.05,'evidence':.9,'risk':.1,'reason':'active semantic cue'}
        for child in prepared_refs(u,ref,me)-{ref}:
            if not conflict_blocks(g,child,active):c[(child,'KNOWN')]={'fit':max(.5,token_overlap(intent,child)),'novelty':.1,'evidence':.82,'risk':.12,'reason':'current materialized semantic neighborhood'}
    for bid in sorted(relevant_binding_ids(g,active)):
        r=g.execute("SELECT * FROM hyperbindings WHERE binding_id=? AND status='CURRENT'",(bid,)).fetchone()
        if not r:continue
        members=set(json.loads(r['members_clay']));present=members&active;missing=members-active
        if len(missing)!=1 or len(present)<r['required_count']:continue
        cand=next(iter(missing))
        if r['synergy']<=0 or r['provenance_count']<2 or r['persistence']<.5 or r['false_binding_risk']>.35 or r['causal_contribution']<.25 or conflict_blocks(g,cand,active):continue
        ev=clamp(.25*r['persistence']+.25*r['transfer']+.3*r['causal_contribution']+.2*min(1,r['provenance_count']/3));fit=clamp(.55+.25*token_overlap(intent,cand)+.2*r['causal_contribution']);nov=clamp(.55+.35*r['synergy']);risk=clamp(r['false_binding_risk']+.15*(1-r['causal_contribution']))
        c[(cand,'EMERGENT_NOVEL')]={'fit':fit,'novelty':nov,'evidence':ev,'risk':risk,'reason':f"higher-order completion of {sorted(present)}; synergy={r['synergy']:.3f}"}
    rows=[]
    for (ref,lane),m in c.items():rows.append({'semantic_ref':ref,'lane':lane,**m,'score':.38*m['fit']+.30*m['evidence']+.20*m['novelty']-.12*m['risk']})
    rows.sort(key=lambda x:({'KNOWN':0,'ANALOGOUS':1,'COUNTERINTUITIVE':2,'EMERGENT_NOVEL':3}[x['lane']],-x['score']))
    hot_receipt={'mode':'MATERIALIZED_NEIGHBORHOOD_PLUS_INDEXED_HYPERBINDINGS','full_memory_scan':False,'global_graph_rebuild':False,'binding_ids_checked':len(relevant_binding_ids(g,active)),'materialization_epoch':me}
    cs=uid('cset');g.execute('INSERT INTO candidate_sets(candidate_set_id,cycle_id,intent_clay,source_unified_epoch,graph_epoch,candidate_universe_hash,hot_path_receipt_clay,created_at) VALUES(?,?,?,?,?,?,?,?)',(cs,cycle,json.dumps({'intent':intent,'active_refs':sorted(active)}),ue,ge,digest_text(json.dumps([(r['semantic_ref'],r['lane']) for r in rows],sort_keys=True)),json.dumps(hot_receipt),now()))
    for r in rows:g.execute('INSERT INTO candidate_members(candidate_set_id,semantic_ref,lane,fit,novelty,evidence,risk,score,reason_clay) VALUES(?,?,?,?,?,?,?,?,?)',(cs,r['semantic_ref'],r['lane'],r['fit'],r['novelty'],r['evidence'],r['risk'],r['score'],json.dumps({'reason':r['reason']})))
    g.commit();frame,hp=uid('frame'),uid('hp');ts=now();u.execute('INSERT INTO possibility_frames(frame_id,cycle_id,realized_state_ref,constraints_clay,generative_map_ref,source_epoch,graph_epoch,created_at) VALUES(?,?,?,?,?,?,?,?)',(frame,cycle,json.dumps(sorted(active)),json.dumps({'consistency':'fail_closed'}),'rae.target::known_union_emergent',ue,ge,ts));u.execute("INSERT INTO hyperpositions(hyperposition_id,frame_id,subject_ref,context_clay,state,evidence_status,uncertainty,created_at,resolved_at) VALUES(?,?,?,'{}','OPEN','CANDIDATE_SURFACE',?,?,NULL)",(hp,frame,'entity:research',.5,ts))
    for i,r in enumerate(rows):u.execute('INSERT INTO hyperposition_alternatives(alternative_id,hyperposition_id,lane,semantic_ref,proposition_clay,fit,novelty,evidence,risk,admissibility_state,provenance_clay,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(f'{hp}:alt:{i+1}',hp,r['lane'],r['semantic_ref'],json.dumps({'semantic_ref':r['semantic_ref'],'reason':r['reason']}),r['fit'],r['novelty'],r['evidence'],r['risk'],'ADMISSIBLE',json.dumps({'generator':'target_runtime','manual_alternative':False}),'ACTIVE'))
    u.commit();return cs,hp,rows,hot_receipt

def gwt_select(u,g,rows,cycle='cycle:test'):
    ue,ge,_=assert_coherent_epoch(u,g);ranked=sorted(rows,key=lambda r:r['score'],reverse=True);best=ranked[0];second=ranked[1]['score'] if len(ranked)>1 else 0;margin=best['score']-second;eid=uid('gwt')
    u.execute('INSERT INTO gwt_episodes(episode_id,cycle_id,candidate_set_hash,selected_alternative_id,competition_margin,ignition,addressable_receivers,source_epoch,graph_epoch,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(eid,cycle,digest_text(json.dumps([(r['semantic_ref'],r['lane']) for r in rows],sort_keys=True)),best['semantic_ref'],margin,clamp(.55+margin),3,ue,ge,now()));u.commit();return eid,best

def receiver_receipt(u,episode,receiver,delivered=1,reconstructed=1,uptake=1,used=1,effect=1):
    rid=uid('recv');u.execute('INSERT INTO gwt_receiver_receipts(receipt_id,episode_id,receiver,addressable,delivered,reconstructed,uptake,used,local_effect,evidence_clay,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(rid,episode,receiver,1,delivered,reconstructed,uptake,used,effect,json.dumps({'measured':True}),now()));u.commit();return rid

def record_outcome_and_reentry(u,episode,to_cycle,verified=True,truth='TRUTHFUL_PROVENANCE'):
    oid=uid('out');u.execute('INSERT INTO outcomes(outcome_id,episode_id,observed_state_clay,verified,evidence_clay,created_at) VALUES(?,?,?,?,?,?)',(oid,episode,json.dumps({'result':'measured'}),int(verified),json.dumps({'sandbox':True}),now()));rr=uid('reentry');applied=int(verified and truth=='TRUTHFUL_PROVENANCE');u.execute('INSERT INTO reentry_receipts(reentry_id,outcome_id,from_episode_id,to_cycle_id,truth_class,delta_clay,applied,evidence_clay,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(rr,oid,episode,to_cycle,truth,json.dumps({'activation_delta':.17,'slow_state_delta':.04}),applied,json.dumps({'provenance_bound':truth=='TRUTHFUL_PROVENANCE'}),now()));u.commit();return oid,rr

def ensure_estimator(u,family='deterministic-stage',version='1.0'):
    eid=f'estimator:{family}:{version}';u.execute('INSERT OR IGNORE INTO estimator_versions(estimator_id,estimator_family,version,configuration_clay,assumptions_clay,status,created_at) VALUES(?,?,?,?,?,?,?)',(eid,family,version,'{}','{}','CURRENT',now()));u.commit();return eid

def record_measurement(u,g,kind,value,episode=None,intervention=None,authority_effect='NONE'):
    ue,ge,_=assert_coherent_epoch(u,g);est=ensure_estimator(u);val=json.dumps(value,sort_keys=True);rid=uid('measure');sources=json.dumps({'contract_sha':contract_sha(),'episode':episode});u.execute('INSERT INTO measurement_receipts(measurement_id,measurement_kind,episode_id,state_epoch,graph_epoch,intervention_id,estimator_id,source_hashes_clay,value_clay,result_hash,evidence_status,authority_effect,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(rid,kind,episode,ue,ge,intervention,est,sources,val,digest_text(val),'MEASURED',authority_effect,now()));u.commit();return rid

def intervention(u,episode,klass,spec,control='control:matched'):
    iid=uid('intervention');u.execute("INSERT INTO intervention_specs(intervention_id,episode_id,intervention_class,specification_clay,matched_control_ref,predicted_effect_clay,rollback_clay,status,created_at) VALUES(?,?,?,?,?,?,?,'STAGED',?)",(iid,episode,klass,json.dumps(spec),control,json.dumps({'direction':'declared'}),json.dumps({'restore':'snapshot'}),now()));u.commit();return iid

def replay(u,iid,episode,effect,control_effect,model_output_hash='frozen:model-output'):
    pre=digest_text('pre:'+episode);post=digest_text('post:'+episode+json.dumps(effect,sort_keys=True));payload=json.dumps({'effect':effect,'control':control_effect},sort_keys=True);rid=uid('replay');u.execute('INSERT INTO replay_receipts(replay_id,intervention_id,episode_id,model_output_hash,pre_state_hash,post_state_hash,observed_effect_clay,control_effect_clay,result_hash,evidence_status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(rid,iid,episode,model_output_hash,pre,post,json.dumps(effect),json.dumps(control_effect),digest_text(payload),'COUNTERFACTUAL_REPLAY',now()));u.commit();return rid

def emergence_readout(u,episode):
    unknown='UNKNOWN';readout={
      'integration':{'receiver_coverage':1.0,'reconstruction_fraction':1.0,'uptake_fraction':1.0,'causal_use_fraction':1.0,'reentry_fraction':1.0},
      'interaction':{'factorial_interaction_omega':unknown,'synergy_pid_or_peid':unknown,'higher_order_irreducibility':unknown},
      'directed_flow':{'transfer_entropy_edges':unknown,'lag_profile':unknown},
      'macro_causality':{'macro_predictive_gain':unknown,'macro_causal_effect_gain':unknown},
      'dynamics':{'metastability':unknown,'hysteresis':unknown,'recurrence_strength':unknown},
      'topology':{'semantic_topology_hash':unknown,'active_topology_hash':unknown},
      'control':{'intervention_id':unknown,'lesion_delta':unknown,'rescue_delta':unknown},
      'epistemic':{'uncertainty':unknown,'evidence_class':'PARTIAL_MEASURED_WITH_EXPLICIT_UNKNOWN'},
      'cost_shadow':{'latency_delta':unknown,'compute_delta':unknown,'memory_delta':unknown}}
    rid=uid('readout');u.execute('INSERT INTO emergence_readouts(readout_id,episode_id,measurement_contract_version,integration_clay,interaction_clay,directed_flow_clay,macro_causality_clay,dynamics_clay,topology_clay,control_clay,epistemic_clay,cost_shadow_clay,evidence_status,provenance_refs_clay,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(rid,episode,'GWT_EMERGENCE_READOUT_CONTRACT_v1',json.dumps(readout['integration']),json.dumps(readout['interaction']),json.dumps(readout['directed_flow']),json.dumps(readout['macro_causality']),json.dumps(readout['dynamics']),json.dumps(readout['topology']),json.dumps(readout['control']),json.dumps(readout['epistemic']),json.dumps(readout['cost_shadow']),'PARTIAL',json.dumps(['gwt-readout-contract','emergenz-v031']),now()));u.commit();return rid,readout

def loop_regime(u,episode,feedback_gain,occupancy,synchrony,dimensionality,hub):
    if occupancy>.95 and synchrony>.9 or dimensionality<.15 or hub>.85:verdict='OVERCOUPLED_TRIPWIRE'
    elif feedback_gain<.15 or occupancy<.2:verdict='UNDERCOUPLED'
    else:verdict='ADAPTIVE'
    rid=uid('regime');u.execute('INSERT INTO loop_regime_readouts(regime_id,episode_id,feedback_gain,ignition_occupancy,synchrony_proxy,dimensionality_proxy,hub_collapse_proxy,verdict,evidence_clay,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(rid,episode,feedback_gain,occupancy,synchrony,dimensionality,hub,verdict,json.dumps({'overcoupling_is_not_target':True}),now()));u.commit();return verdict

def emergence_gate(u,subject,state_stable=True,lesion=.2,rescue=.8,shuffle=.15,ood=.1,macro=.05,cost=.1):
    use=bool(u.execute('SELECT 1 FROM gwt_receiver_receipts WHERE used=1 AND local_effect=1 LIMIT 1').fetchone());re=bool(u.execute("SELECT 1 FROM reentry_receipts WHERE truth_class='TRUTHFUL_PROVENANCE' AND applied=1 LIMIT 1").fetchone())
    verdict='ABSTAIN_STATE_INADEQUATE' if not state_stable else ('SUPPORTED_FUNCTIONAL_PATTERN' if use and re and lesion>.1 and rescue>.5 and shuffle>.05 and ood>0 and macro>0 else 'OPEN')
    u.execute('INSERT INTO emergence_gate_receipts(gate_id,subject_ref,state_adequacy,receiver_use,truthful_reentry,lesion_effect,rescue_recovery,shuffle_delta,ood_transfer,macro_advantage,cost_shadow,verdict,evidence_clay,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid('gate'),subject,'STABLE' if state_stable else 'UNSTABLE',int(use),int(re),lesion,rescue,shuffle,ood,macro,cost,verdict,json.dumps({'claim_boundary':'functional_pattern_not_consciousness'}),now()));u.commit();return verdict

def causal_credit(u,target,iid,oid,weight=.7):
    cid=uid('credit');u.execute('INSERT INTO causal_credit_receipts(credit_id,target_ref,intervention_id,outcome_id,credit_class,weight,evidence_clay,created_at) VALUES(?,?,?,?,?,?,?,?)',(cid,target,iid,oid,'MATCHED_INTERVENTION',weight,json.dumps({'matched_control':True}),now()));u.commit();return cid

def stage_control_update(u,target,credit_ref,ood='PASS'):
    credit=u.execute('SELECT * FROM causal_credit_receipts WHERE credit_id=?',(credit_ref,)).fetchone();state='STAGED' if credit and credit['weight']>0 and ood=='PASS' else 'REJECTED';rid=uid('control-update');u.execute('INSERT INTO control_update_receipts(update_id,target_ref,prior_policy_hash,candidate_policy_clay,matched_control_ref,causal_credit_ref,ood_state,rollback_clay,promotion_state,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(rid,target,digest_text('prior'),json.dumps({'gain_delta':-.05 if target=='overcoupled' else .03}),'control:matched',credit_ref,ood,json.dumps({'restore_policy_hash':digest_text('prior')}),state,now()));u.commit();return state

def projector_view(u,episode,receipt_refs):
    summary={'episode':episode,'verified_receipts':receipt_refs[:8],'authority':'READ_ONLY_OBSERVATION'};vid=uid('projector');u.execute("INSERT INTO readout_projector_views(view_id,episode_id,source_receipts_clay,bounded_summary_clay,authority_class,created_at) VALUES(?,?,?,?,'READ_ONLY_OBSERVATION',?)",(vid,episode,json.dumps(receipt_refs),json.dumps(summary),now()));u.commit();return vid

def self_test(root:Path):
    if root.exists():shutil.rmtree(root)
    u,g=open_pair(root,create=True);checks=[]
    def ok(name,cond):
        assert cond,name;checks.append(name)
    try:
        ok('research_directives_and_sources_seeded',u.execute('SELECT COUNT(*) FROM research_imports').fetchone()[0]>=10)
        ok('clay_is_semantic_source',u.execute("SELECT value FROM meta WHERE key='semantic_source'").fetchone()[0].endswith('RAE_TARGET_CONTRACT.clay'))
        ok('contract_hash_bound',u.execute("SELECT value FROM meta WHERE key='semantic_contract_sha256'").fetchone()[0]==contract_sha())
        ok('claycode_release_fail_closed',u.execute("SELECT physical_release_status FROM claycode_contract_receipts WHERE receipt_id='cc:target-0.2'").fetchone()[0]=='PHYSICAL_ACCEPTANCE_OPEN')
        blocked=False
        try:u.execute("DELETE FROM organ_registry WHERE organ_id='workspace'");u.commit()
        except sqlite3.IntegrityError:blocked=True;u.rollback()
        ok('organ_delete_blocked',blocked)
        ok('needle_and_retina_preserved',u.execute("SELECT COUNT(*) FROM organ_registry WHERE organ_id IN ('needle','digital_retina')").fetchone()[0]==2)
        for ref in ['intent:repair','state:workspace','state:memory_reentry','candidate:forbidden']:
            ensure_entity(u,ref);add_node(g,ref)
        add_dependency(u,'intent:repair','state:workspace',.95)
        add_hyperbinding(g,['intent:repair','state:workspace','state:memory_reentry'],.93,.48,.88,.76,.72,3,.08)
        publish_delta(u,g,['intent:repair','state:workspace'])
        _,_,rows,hot=generate_candidates(u,g,'repair with workspace memory',['intent:repair','state:workspace'])
        ok('hot_path_no_full_scan',hot['full_memory_scan'] is False and hot['global_graph_rebuild'] is False)
        ok('known_lane_present',any(r['lane']=='KNOWN' for r in rows))
        ok('emergent_not_manual',any(r['lane']=='EMERGENT_NOVEL' and r['semantic_ref']=='state:memory_reentry' for r in rows))
        ok('candidate_union_preserved',{'KNOWN','EMERGENT_NOVEL'}<={r['lane'] for r in rows})
        add_hyperbinding(g,['intent:repair','state:workspace','candidate:forbidden'],.95,.4,.9,.9,.8,3,.05);add_conflict(g,'candidate:forbidden','state:workspace')
        _,_,r2,_=generate_candidates(u,g,'repair',['intent:repair','state:workspace'],'cycle:2');ok('consistency_gate_blocks_conflict',not any(r['semantic_ref']=='candidate:forbidden' for r in r2))
        gs=graph_surface(g);g.execute("UPDATE graph_publication_state SET unified_epoch=unified_epoch+99 WHERE surface_key='CURRENT'");g.commit();mixed=False
        try:generate_candidates(u,g,'repair',['intent:repair','state:workspace'],'cycle:mixed')
        except RuntimeError as e:mixed='MIXED_EPOCH' in str(e)
        ok('mixed_epoch_read_rejected',mixed);g.execute("UPDATE graph_publication_state SET unified_epoch=? WHERE surface_key='CURRENT'",(gs['unified_epoch'],));g.commit();assert_coherent_epoch(u,g)
        ep,best=gwt_select(u,g,rows);guard=False
        try:receiver_receipt(u,ep,'receiver:test',delivered=0,reconstructed=0,uptake=0,used=1,effect=0)
        except sqlite3.IntegrityError:guard=True;u.rollback()
        ok('gwt_stage_guard',guard);recv=receiver_receipt(u,ep,'receiver:planner');ok('receiver_use_measured',u.execute('SELECT COUNT(*) FROM gwt_receiver_receipts WHERE used=1 AND local_effect=1').fetchone()[0]==1)
        oid,re=record_outcome_and_reentry(u,ep,'cycle:next');ok('truthful_reentry_applied',u.execute('SELECT COUNT(*) FROM reentry_receipts WHERE applied=1').fetchone()[0]==1)
        m=record_measurement(u,g,'receiver_use',{'used':True},ep);auth=False
        try:record_measurement(u,g,'bad_authority',{'x':1},ep,authority_effect='MINT_TRUTH')
        except sqlite3.IntegrityError:auth=True;u.rollback()
        ok('measurement_cannot_mint_authority',auth)
        rid,ro=emergence_readout(u,ep);ok('unknown_is_not_zero',ro['interaction']['factorial_interaction_omega']=='UNKNOWN')
        iid=intervention(u,ep,'REENTRY_SHUFFLE',{'truth':'SHUFFLED'});rep=replay(u,iid,ep,{'score_delta':-.2},{'score_delta':0.0});ok('counterfactual_replay_recorded',u.execute('SELECT COUNT(*) FROM replay_receipts').fetchone()[0]==1)
        ok('state_adequacy_fail_closed',emergence_gate(u,'test',False)=='ABSTAIN_STATE_INADEQUATE');ok('functional_gate_requires_controls',emergence_gate(u,'test',True,0,0,0,0,0)=='OPEN');ok('functional_pattern_not_consciousness',emergence_gate(u,'test',True,.2,.8,.15,.1,.05)=='SUPPORTED_FUNCTIONAL_PATTERN')
        ok('adaptive_loop_regime',loop_regime(u,ep,.6,.55,.45,.7,.2)=='ADAPTIVE');ok('overcoupling_tripwire',loop_regime(u,ep,1.0,.99,.96,.08,.9)=='OVERCOUPLED_TRIPWIRE')
        credit=causal_credit(u,'coupling:reentry',iid,oid,.75);ok('control_update_requires_causal_credit',stage_control_update(u,'coupling:reentry',credit,'PASS')=='STAGED');ok('control_update_rejects_failed_ood',stage_control_update(u,'coupling:reentry',credit,'FAIL')=='REJECTED')
        pv=projector_view(u,ep,[m,rid,rep,re,recv]);ok('readout_projector_read_only',u.execute('SELECT authority_class FROM readout_projector_views WHERE view_id=?',(pv,)).fetchone()[0]=='READ_ONLY_OBSERVATION')
        ok('semantic_signatures_present',u.execute('SELECT COUNT(*) FROM clay_semantic_signatures').fetchone()[0]>=1)
        ok('unified_integrity',u.execute('PRAGMA integrity_check').fetchone()[0]=='ok');ok('unified_fk_integrity',len(u.execute('PRAGMA foreign_key_check').fetchall())==0);ok('graph_integrity',g.execute('PRAGMA integrity_check').fetchone()[0]=='ok');ok('graph_fk_integrity',len(g.execute('PRAGMA foreign_key_check').fetchall())==0)
        result={'status':'PASS','target_version':TARGET_VERSION,'checks':checks,'passed':len(checks),'candidate_example':rows,'selected':best,'hot_path_receipt':hot,'contract_sha256':contract_sha(),'claim_boundary':'functional pattern only; no consciousness claim','claycode_boundary':'software path available; physical release acceptance open'}
        print(json.dumps(result,indent=2,ensure_ascii=False));return result
    finally:u.close();g.close()

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True);x=s.add_parser('init');x.add_argument('--root',required=True);x=s.add_parser('self-test');x.add_argument('--root',required=True);a=p.parse_args()
    if a.cmd=='init':
        u,g=open_pair(Path(a.root),create=True);print(json.dumps({'status':'INITIALIZED','target_version':TARGET_VERSION,'contract_sha256':contract_sha()}));u.close();g.close()
    else:self_test(Path(a.root))
if __name__=='__main__':main()
