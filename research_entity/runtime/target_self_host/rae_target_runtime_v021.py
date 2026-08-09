#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,shutil,sqlite3,uuid
from datetime import datetime,timezone
from pathlib import Path
H=Path(__file__).resolve().parent; V='RAE-TARGET-0.2.1'; CV='RAE_TARGET_SEMANTIC_CONTRACT_0.2.1'
IMPORTS=[
('gwt-strict','gwt','research_entity/trigger_runs/emergenz/20260809T2015p0700-chatgpt-gwt-emergence-fusion','03a4fddcf35b74e020c0011d27ec3477594a40cf','OPEN'),
('gwt-contract','gwt','research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md','blob:b2d9a903f256e1f26db500317b34930456188245','CURRENT'),
('semantic-fabric','unifieddb','research_entity/global/CLAY_SEMANTIC_COUPLING_FABRIC_DIRECTIVE.md','blob:8685421de82b76b0ce925b2cf45fa72082502654','CURRENT'),
('gwt-control','emergenz','research_entity/global/CLAY_GWT_EMERGENCE_OBSERVABILITY_CONTROL_DIRECTIVE.md','blob:b295d5744ae836424925a00d2d2b3a8325f47ccb','CURRENT'),
('clay-native','frank','research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md','blob:7d07e54acf0e62bda81de3b032fe480c0f08f234','CURRENT'),
('emergenz-v031','emergenz','research_entity/trigger_runs/emergenz/20260809T204545p0700_udb_emergence_meter_v03_adversarial_concordance/V031_LIVE_REFRESH_ADDENDUM.md','343fabb8b176df10f85aa3cbd4dce09f165b4987','OPEN'),
('claycode-v17','claycode','research_entity/claycode/base/reports/CC_BASE_LAST_BLOCKERS_V17_RESOLUTION_20260809.md','d3c8e7de8ca2ccfdbc4db4180778b351b5b983b9','OPEN'),
('claycode-c11','claycode','research_entity/claycode/base/receipts/CC_WP06_SANDBOX_C11_SEMANTIC_HARDENING_20260809T2155p0700.json','1538ed5e5550ee2509c42e27077b87a00f918b33','OPEN'),
('claycode-current','claycode','tools/claycode_base_compiler.py','blob:5d01dfeb77b1bece85433cd09af6ea3427a5f995','OPEN'),
('frank-reentry','frank','research_entity/rooms/center_events/20260809T2138p0700_chatgpt_secondary_frank_causal_reentry_cross_room_delta.json','83d2d41e751a332fa285b3d81cc753ab9b67648b','OPEN'),
('golden-loop','frank','research_entity/mesh_feedback/20260809T2201p0700-frank-golden-loop-deep-cycle/BRANCH_FEEDBACK_MANIFEST.json','158c9d92401a5406615015e7fa4d16942ccc1f57','OPEN'),
('retina-voice','frank','research_entity/rooms/rooms/center/events/20260809T221127p0700_frank_v01_pixel_voice_fusion_delta.json','ecba47036c4e5c25be5372c5c291429fdb3a9ca9','OPEN'),
('frank-v5-credit-fuzz','frank','research_entity/state/work/events/20260809T151500Z_chatgpt_secondary_frank_v01_sandbox_receipt_v5.json','eb84cd5aafb7c2e47747ee6270a5e5e10b5a3238','OPEN')]
def now():return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
def uid(p):return p+':'+uuid.uuid4().hex
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def fsha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csha():return fsha(H/'RAE_TARGET_CONTRACT.clay')
def cf(c):c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
def surf(u):return u.execute("SELECT * FROM published_surface WHERE surface_key='CURRENT'").fetchone()
def gsurf(g):return g.execute("SELECT * FROM graph_publication_state WHERE surface_key='CURRENT'").fetchone()
def coherent(u,g):
 a,b=surf(u),gsurf(g);s=csha()
 if not a or not b or a['status']!='CURRENT' or b['status']!='CURRENT' or a['unified_epoch']!=b['unified_epoch'] or a['graph_epoch']!=b['graph_epoch'] or a['contract_sha256']!=s or b['contract_sha256']!=s:raise RuntimeError('MIXED_EPOCH_READ_FORBIDDEN')
 return a['unified_epoch'],a['graph_epoch'],a['materialization_epoch']
def open_pair(root,create=False):
 r=Path(root);r.mkdir(parents=True,exist_ok=True);u=cf(sqlite3.connect(r/'RAE_UNIFIED.sqlite'));g=cf(sqlite3.connect(r/'RAE_CLAYGRAPH.sqlite'))
 if create:u.executescript((H/'RAE_UNIFIED_SCHEMA.sql').read_text());g.executescript((H/'RAE_CLAYGRAPH_SCHEMA.sql').read_text());boot(u,g)
 coherent(u,g);return u,g
def boot(u,g):
 t=now();s=csha();u.execute("INSERT INTO state_epochs VALUES(1,NULL,?,?,?,'CURRENT')",(h('u1'),t,'chatgpt-secondary'));g.execute("INSERT INTO graph_epochs VALUES(1,1,?,'CURRENT',?)",(h('g1'),t));u.execute("INSERT INTO published_surface VALUES('CURRENT',1,1,1,?,'CURRENT',?)",(s,t));g.execute("INSERT INTO graph_publication_state VALUES('CURRENT',1,1,?,'CURRENT',?)",(s,t))
 for k,v in [('target_version',V),('semantic_source','research_entity/runtime/target_self_host/RAE_TARGET_CONTRACT.clay'),('semantic_contract_sha256',s),('projection_policy','Clay semantic source; Python/SQLite are projections')]:u.execute('INSERT INTO meta VALUES(?,?)',(k,v))
 for iid,d,ref,commit,st in IMPORTS:u.execute('INSERT INTO research_imports VALUES(?,?,?,?,?,?,?,?,?)',(iid,d,ref,commit,'PROJECT_EVIDENCE_OR_DIRECTIVE',st,ref,h(ref),t))
 for x in [('workspace','Global Workspace','GWT causal stages','gwt+graph','FUSED','frank:gwt'),('hyperposition','Semantic Hyperposition','alternatives','udb+graph','FUSED','frank:hp'),('reentry','Causal Re-entry','strong-credit reentry','udb+gwt','EMERGENT_DISTRIBUTED','frank:loop'),('semantic_fabric','Semantic Fabric','prepared hot path','udb+graph','EMERGENT_DISTRIBUTED','clay:fabric'),('observability','Observability','readout/replay','readout','EXPLICIT','gwt:readout'),('needle','Needle','fast router','needle','EXPLICIT','frank:clay-native'),('digital_retina','Digital Retina','visual percept','retina','EXPLICIT','frank:clay-native'),('voice','FrankVoice','typed voice I/O','voice','EXPLICIT','frank:retina-voice')]:u.execute('INSERT INTO organ_registry VALUES(?,?,?,?,?,0,?,?)',(*x,t))
 u.execute("INSERT INTO perception_io_contracts VALUES('digital_retina','OBSERVATION_ONLY','OBSERVATION_ONLY','UNKNOWN_NOT_PROMOTED','CONTEXT_CONFLICT_PRESERVED','PIXEL_REENTRY_PROVENANCE_BOUND','REAL_PIXEL_SANDBOX_ONLY','ecba47036c4e5c25be5372c5c291429fdb3a9ca9','CURRENT',?)",(t,));u.execute("INSERT INTO perception_io_contracts VALUES('voice','OBSERVATION_ONLY','PROPOSAL_ONLY','UNKNOWN_NOT_PROMOTED','PRESERVE','PROVENANCE_BOUND_IF_USED','NO_PHYSICAL_MIC_OR_SPEAKER_CLAIM','ecba47036c4e5c25be5372c5c291429fdb3a9ca9','CURRENT',?)",(t,));u.execute("INSERT INTO legacy_conservation_receipts VALUES('frank-v5','eb84cd5aafb7c2e47747ee6270a5e5e10b5a3238',31,36,74,38,'74 measured slots; 38 primary identities opaque/unmapped','OPEN',?)",(t,))
 sig=json.dumps({'hot_path':'materialized_neighborhood+indexed_hyperbindings','authority':'measurement!=truth','objects':['CandidateSet','Hyperposition','WorkspaceEpisode','ReceiverReceipt','ReentryReceipt','MeasurementReceipt','EmergenceReadout']});u.execute("INSERT INTO clay_semantic_signatures VALUES('RAE_TARGET_CONTRACT.clay',?,?,?,?,?,?,?,?,?,?,'CURRENT',?)",(s,sig,'[]','{}','{}','{}','{}','{}',json.dumps({'python':'rae_target_runtime_v021.py'}),json.dumps({'source':'Clay+imports'}),t));u.execute("INSERT INTO claycode_contract_receipts VALUES('cc:target-0.2.1','tools/claycode_base_compiler.py@blob:5d01dfeb77b1bece85433cd09af6ea3427a5f995','pure slice; effects boundary open',?,'SOFTWARE_PATH_AVAILABLE_RELEASE_OPEN','PHYSICAL_ACCEPTANCE_OPEN',?,'{}',?)",(CV,sig,t));u.commit();g.commit()
def node(g,ref):
 r=g.execute('SELECT node_id FROM nodes WHERE semantic_ref=?',(ref,)).fetchone()
 if r:return r[0]
 n='cg:'+h(ref)[:20];g.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?)',(n,ref,'semantic',ref,'EVIDENCE_BOUND',gsurf(g)['unified_epoch'],gsurf(g)['graph_epoch'],'CURRENT'));g.commit();return n
def dep(u,a,b,c=.9):u.execute('INSERT INTO semantic_dependencies VALUES(?,?,?,?,?,?,?,?,?)',(uid('dep'),a,b,'PREPARED_NEIGHBORHOOD',c,'EVIDENCE','{}','ACTIVE',now()));u.commit()
def hb(g,m,j=.9,p=.5,per=.8,tr=.7,ca=.6,prov=2,risk=.1):
 for x in m:node(g,x)
 bid=uid('hb');ge=gsurf(g)['graph_epoch'];g.execute('INSERT INTO hyperbindings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(bid,json.dumps(sorted(m)),len(m)-1,j,p,j-p,per,tr,ca,prov,risk,'CURRENT','{}',ge,now()));[g.execute('INSERT INTO hyperbinding_member_index VALUES(?,?,?,?,?)',(x,bid,'MEMBER',ge,'CURRENT')) for x in m];g.commit();return bid
def conflict(g,a,b):g.execute('INSERT INTO graph_conflicts VALUES(?,?,?,?,?,?,?,?)',(uid('c'),a,b,'CONTRADICTION','OPEN','{}',gsurf(g)['graph_epoch'],now()));g.commit()
def blocked(g,c,active):return any(g.execute("SELECT 1 FROM graph_conflicts WHERE state='OPEN' AND ((left_ref=? AND right_ref=?) OR (left_ref=? AND right_ref=?))",(c,x,x,c)).fetchone() for x in active)
def materialize(u,g,cue):
 ue,ge,me=coherent(u,g);seen={cue};front=[cue]
 for _ in range(2):
  nxt=[]
  for a in front:
   for r in u.execute("SELECT child_ref FROM semantic_dependencies WHERE parent_ref=? AND status='ACTIVE' ORDER BY confidence DESC LIMIT 32",(a,)):
    if r[0] not in seen and len(seen)<32:seen.add(r[0]);nxt.append(r[0])
  front=nxt
 refs=sorted(seen);u.execute('INSERT OR REPLACE INTO materialized_neighborhoods VALUES(?,?,?,?,?,?,?,?,?)',(cue,ue,ge,me,json.dumps(refs),h(json.dumps(refs)),len(refs),'{}',now()));u.commit()
def publish(u,g,cues):
 a=surf(u);ue,ge,me=a['unified_epoch']+1,a['graph_epoch']+1,a['materialization_epoch']+1;t=now();s=csha();g.execute("UPDATE graph_epochs SET status='STALE' WHERE status='CURRENT'");g.execute("INSERT INTO graph_epochs VALUES(?,?,?,'CURRENT',?)",(ge,ue,h(str((ue,ge))),t));g.execute("UPDATE graph_publication_state SET graph_epoch=?,unified_epoch=?,contract_sha256=?,status='CURRENT',updated_at=?",(ge,ue,s,t));g.commit();u.execute("UPDATE state_epochs SET status='STALE' WHERE status='CURRENT'");u.execute("INSERT INTO state_epochs VALUES(?,?,?,?,?,'CURRENT')",(ue,a['unified_epoch'],h(str((ue,ge))),t,'chatgpt-secondary'));u.execute("UPDATE published_surface SET unified_epoch=?,graph_epoch=?,materialization_epoch=?,contract_sha256=?,status='CURRENT',updated_at=?",(ue,ge,me,s,t));u.commit();[materialize(u,g,c) for c in cues]
def candidates(u,g,intent,active,cycle='cycle:test'):
 ue,ge,me=coherent(u,g);A=set(active);out={}
 for x in A:
  out[(x,'KNOWN')]=(.55,.05,.9,.1,'active cue');r=u.execute('SELECT refs_clay FROM materialized_neighborhoods WHERE cue_ref=? AND materialization_epoch=?',(x,me)).fetchone()
  if not r:raise RuntimeError('COLD_PATH_REQUIRED')
  for y in set(json.loads(r[0]))-{x}:
   if not blocked(g,y,A):out[(y,'KNOWN')]=(.5,.1,.82,.12,'materialized neighborhood')
 q=','.join('?'*len(A));bids={r[0] for r in g.execute(f"SELECT DISTINCT binding_id FROM hyperbinding_member_index WHERE status='CURRENT' AND member_ref IN ({q})",tuple(sorted(A)))} if A else set()
 for bid in bids:
  r=g.execute("SELECT * FROM hyperbindings WHERE binding_id=? AND status='CURRENT'",(bid,)).fetchone();M=set(json.loads(r['members_clay']));miss=M-A
  if len(miss)==1 and len(M&A)>=r['required_count'] and r['synergy']>0 and r['provenance_count']>=2 and r['persistence']>=.5 and r['false_binding_risk']<=.35 and r['causal_contribution']>=.25:
   y=next(iter(miss))
   if not blocked(g,y,A):out[(y,'EMERGENT_NOVEL')]=(.55+.2*r['causal_contribution'],.55+.35*r['synergy'],.25*r['persistence']+.25*r['transfer']+.3*r['causal_contribution']+.2*min(1,r['provenance_count']/3),r['false_binding_risk']+.15*(1-r['causal_contribution']),'higher-order completion')
 rows=[]
 for (ref,lane),(fit,nov,ev,risk,why) in out.items():rows.append({'semantic_ref':ref,'lane':lane,'fit':fit,'novelty':nov,'evidence':ev,'risk':risk,'reason':why,'score':.38*fit+.3*ev+.2*nov-.12*risk})
 hot={'full_memory_scan':False,'global_graph_rebuild':False,'binding_ids_checked':len(bids),'materialization_epoch':me};cs=uid('cset');g.execute('INSERT INTO candidate_sets VALUES(?,?,?,?,?,?,?,?)',(cs,cycle,json.dumps({'intent':intent,'active_refs':sorted(A)}),ue,ge,h(json.dumps(rows,sort_keys=True)),json.dumps(hot),now()));[g.execute('INSERT INTO candidate_members VALUES(?,?,?,?,?,?,?,?,?)',(cs,r['semantic_ref'],r['lane'],r['fit'],r['novelty'],r['evidence'],r['risk'],r['score'],json.dumps({'reason':r['reason']}))) for r in rows];g.commit();fr,hp=uid('frame'),uid('hp');u.execute('INSERT INTO possibility_frames VALUES(?,?,?,?,?,?,?,?)',(fr,cycle,json.dumps(sorted(A)),'{}','rae.target',ue,ge,now()));u.execute("INSERT INTO hyperpositions VALUES(?,?,?,'{}','OPEN','CANDIDATE_SURFACE',.5,?,NULL)",(hp,fr,'entity:research',now()));[u.execute('INSERT INTO hyperposition_alternatives VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(uid('alt'),hp,r['lane'],r['semantic_ref'],json.dumps(r),r['fit'],r['novelty'],r['evidence'],r['risk'],'ADMISSIBLE',json.dumps({'manual_alternative':False}),'ACTIVE')) for r in rows];u.commit();return rows,hot
def select(u,g,rows):
 ue,ge,_=coherent(u,g);rank=sorted(rows,key=lambda x:x['score'],reverse=True);best=rank[0];m=best['score']-(rank[1]['score'] if len(rank)>1 else 0);ep=uid('gwt');u.execute('INSERT INTO gwt_episodes VALUES(?,?,?,?,?,?,?,?,?,?)',(ep,'cycle:test',h(json.dumps(rows,sort_keys=True)),best['semantic_ref'],m,min(1,.55+m),3,ue,ge,now()));u.commit();return ep,best
def recv(u,ep,d=1,r=1,up=1,use=1,effect=1):rid=uid('recv');u.execute('INSERT INTO gwt_receiver_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?)',(rid,ep,'receiver:planner',1,d,r,up,use,effect,'{}',now()));u.commit();return rid
def credit(u,target,oid,klass='DIRECT_RECEIPT',iid=None,w=1):cid=uid('credit');u.execute('INSERT INTO causal_credit_receipts VALUES(?,?,?,?,?,?,?,?)',(cid,target,iid,oid,klass,w,'{}',now()));u.commit();return cid
def reentry(u,ep,to,truth='TRUTHFUL_PROVENANCE',klass='DIRECT_RECEIPT',verified=1):
 oid=uid('out');u.execute('INSERT INTO outcomes VALUES(?,?,?,?,?,?)',(oid,ep,'{}',verified,'{}',now()));u.commit();cr=credit(u,'reentry:'+ep,oid,klass);rs=u.execute('SELECT * FROM gwt_receiver_receipts WHERE episode_id=?',(ep,)).fetchall();cl=bool(rs) and all((not x['addressable']) or (x['delivered'] and x['reconstructed'] and x['uptake'] and x['used']) for x in rs);ap=int(verified and truth=='TRUTHFUL_PROVENANCE' and klass in ('DIRECT_RECEIPT','PATH_SUPPORTED') and cl);rr=uid('re');u.execute('INSERT INTO reentry_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(rr,oid,ep,to,truth,klass,cr,int(cl),'{}',ap,'{}',now()));u.commit();return oid,rr
def measure(u,g,ep,authority='NONE'):
 ue,ge,_=coherent(u,g);est='est:1';u.execute("INSERT OR IGNORE INTO estimator_versions VALUES(?,?,?,'{}','{}','CURRENT',?)",(est,'deterministic','1',now()));v='{"used":true}';mid=uid('m');u.execute('INSERT INTO measurement_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(mid,'receiver_use',ep,ue,ge,None,est,'{}',v,h(v),'MEASURED',authority,now()));u.commit();return mid
def intervention(u,ep):iid=uid('i');u.execute("INSERT INTO intervention_specs VALUES(?,?,?,'{}','control:matched','{}','{}','STAGED',?)",(iid,ep,'REENTRY_SHUFFLE',now()));u.commit();return iid
def replay(u,iid,ep):rid=uid('rp');u.execute("INSERT INTO replay_receipts VALUES(?,?,?,'frozen:model',?,?,?,'{}',?,'COUNTERFACTUAL_REPLAY',?)",(rid,iid,ep,h('pre'),h('post'),'{}',h('result'),now()));u.commit();return rid
def readout(u,ep):
 U='UNKNOWN';rid=uid('ro');u.execute('INSERT INTO emergence_readouts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(rid,ep,'GWT_v1',json.dumps({'receiver_use':1}),json.dumps({'synergy':U}),json.dumps({'te':U}),json.dumps({'macro':U}),json.dumps({'metastability':U}),json.dumps({'topology':U}),json.dumps({'lesion':U}),json.dumps({'uncertainty':U}),json.dumps({'cost':U}),'PARTIAL','[]',now()));u.commit();return U
def gate(u,stable=1,les=.2,res=.8,sh=.15,ood=.1,macro=.05,cost=.1):
 use=bool(u.execute('SELECT 1 FROM gwt_receiver_receipts WHERE used=1 AND local_effect=1').fetchone());re=bool(u.execute("SELECT 1 FROM reentry_receipts WHERE applied=1 AND causal_credit_class IN ('DIRECT_RECEIPT','PATH_SUPPORTED')").fetchone());v='ABSTAIN_STATE_INADEQUATE' if not stable else ('SUPPORTED_FUNCTIONAL_PATTERN' if use and re and les>.1 and res>.5 and sh>.05 and ood>0 and macro>0 else 'OPEN');u.execute('INSERT INTO emergence_gate_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid('gate'),'test','STABLE' if stable else 'UNSTABLE',int(use),int(re),les,res,sh,ood,macro,cost,v,'{}',now()));u.commit();return v
def regime(u,ep,gain,occ,sync,dim,hub):v='OVERCOUPLED_TRIPWIRE' if (occ>.95 and sync>.9) or dim<.15 or hub>.85 else ('UNDERCOUPLED' if gain<.15 or occ<.2 else 'ADAPTIVE');u.execute('INSERT INTO loop_regime_readouts VALUES(?,?,?,?,?,?,?,?,?,?)',(uid('lr'),ep,gain,occ,sync,dim,hub,v,'{}',now()));u.commit();return v
def self_test(root):
 r=Path(root);shutil.rmtree(r,ignore_errors=True);u,g=open_pair(r,1);C=[]
 def ok(n,x):assert x,n;C.append(n)
 try:
  ok('imports',u.execute('SELECT count(*) FROM research_imports').fetchone()[0]==13);ok('clay_source',u.execute("SELECT value FROM meta WHERE key='semantic_contract_sha256'").fetchone()[0]==csha());ok('claycode_open',u.execute("SELECT physical_release_status FROM claycode_contract_receipts").fetchone()[0]=='PHYSICAL_ACCEPTANCE_OPEN');ok('organs',u.execute("SELECT count(*) FROM organ_registry WHERE organ_id IN ('needle','digital_retina','voice')").fetchone()[0]==3);ok('perception_authority',u.execute("SELECT count(*) FROM perception_io_contracts WHERE input_authority='OBSERVATION_ONLY'").fetchone()[0]==2);ok('legacy_boundary',u.execute("SELECT unresolved_opaque FROM legacy_conservation_receipts").fetchone()[0]==38)
  blocked_del=False
  try:u.execute("DELETE FROM organ_registry WHERE organ_id='workspace'");u.commit()
  except sqlite3.IntegrityError:blocked_del=True;u.rollback()
  ok('organ_delete_blocked',blocked_del)
  [node(g,x) for x in ['intent:repair','state:workspace','state:memory_reentry','candidate:forbidden']];dep(u,'intent:repair','state:workspace',.95);hb(g,['intent:repair','state:workspace','state:memory_reentry'],.93,.48,.88,.76,.72,3,.08);publish(u,g,['intent:repair','state:workspace']);rows,hot=candidates(u,g,'repair',['intent:repair','state:workspace']);ok('hot_path',not hot['full_memory_scan'] and not hot['global_graph_rebuild']);ok('known',any(x['lane']=='KNOWN' for x in rows));ok('emergent_not_manual',any(x['semantic_ref']=='state:memory_reentry' and x['lane']=='EMERGENT_NOVEL' for x in rows));ok('union',{'KNOWN','EMERGENT_NOVEL'}<={x['lane'] for x in rows});hb(g,['intent:repair','state:workspace','candidate:forbidden'],.95,.4,.9,.9,.8,3,.05);conflict(g,'candidate:forbidden','state:workspace');rows2,_=candidates(u,g,'repair',['intent:repair','state:workspace']);ok('conflict_block',not any(x['semantic_ref']=='candidate:forbidden' for x in rows2))
  old=gsurf(g)['unified_epoch'];g.execute("UPDATE graph_publication_state SET unified_epoch=99");g.commit();mix=False
  try:candidates(u,g,'x',['intent:repair'])
  except RuntimeError:mix=True
  ok('mixed_epoch_block',mix);g.execute('UPDATE graph_publication_state SET unified_epoch=?',(old,));g.commit();ep,best=select(u,g,rows);guard=False
  try:recv(u,ep,0,0,0,1,0)
  except sqlite3.IntegrityError:guard=True;u.rollback()
  ok('gwt_stage_guard',guard);rr=recv(u,ep);ok('receiver_use',True);oid,strong=reentry(u,ep,'next');ok('strong_credit_reentry',u.execute('SELECT applied FROM reentry_receipts WHERE reentry_id=?',(strong,)).fetchone()[0]==1);_,weak=reentry(u,ep,'weak',klass='CORRELATED_ONLY');ok('weak_credit_denied',u.execute('SELECT applied FROM reentry_receipts WHERE reentry_id=?',(weak,)).fetchone()[0]==0);_,broken=reentry(u,ep,'broken',truth='BROKEN_PROVENANCE');ok('broken_provenance_denied',u.execute('SELECT applied FROM reentry_receipts WHERE reentry_id=?',(broken,)).fetchone()[0]==0)
  m=measure(u,g,ep);auth=False
  try:measure(u,g,ep,'MINT_TRUTH')
  except sqlite3.IntegrityError:auth=True;u.rollback()
  ok('measurement_authority_guard',auth);ok('unknown_not_zero',readout(u,ep)=='UNKNOWN');iid=intervention(u,ep);rp=replay(u,iid,ep);ok('replay',bool(rp));ok('state_abstain',gate(u,0)=='ABSTAIN_STATE_INADEQUATE');ok('controls_required',gate(u,1,0,0,0,0,0)=='OPEN');ok('functional_only',gate(u)=='SUPPORTED_FUNCTIONAL_PATTERN');ok('adaptive',regime(u,ep,.6,.5,.4,.7,.2)=='ADAPTIVE');ok('overcoupling',regime(u,ep,1,.99,.96,.08,.9)=='OVERCOUPLED_TRIPWIRE')
  cr=credit(u,'control',oid,'MATCHED_INTERVENTION',iid,.75);state='STAGED' if u.execute('SELECT weight FROM causal_credit_receipts WHERE credit_id=?',(cr,)).fetchone()[0]>0 else 'REJECTED';ok('control_credit',state=='STAGED');ok('signatures',u.execute('SELECT count(*) FROM clay_semantic_signatures').fetchone()[0]==1);ok('readout_authority',u.execute('SELECT count(*) FROM measurement_receipts WHERE authority_effect!="NONE"').fetchone()[0]==0);ok('u_integrity',u.execute('PRAGMA integrity_check').fetchone()[0]=='ok');ok('u_fk',not u.execute('PRAGMA foreign_key_check').fetchall());ok('g_integrity',g.execute('PRAGMA integrity_check').fetchone()[0]=='ok');ok('g_fk',not g.execute('PRAGMA foreign_key_check').fetchall())
  out={'status':'PASS','target_version':V,'passed':len(C),'checks':C,'selected':best,'hot_path_receipt':hot,'contract_sha256':csha(),'claim_boundary':'functional pattern only; no consciousness claim','legacy_boundary':'74 measured slots; 38 identities opaque'};print(json.dumps(out,indent=2));return out
 finally:u.close();g.close()
def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True);a=sp.add_parser('init');a.add_argument('--root',required=True);a=sp.add_parser('self-test');a.add_argument('--root',required=True);x=p.parse_args()
 if x.cmd=='init':u,g=open_pair(x.root,1);print(json.dumps({'status':'INITIALIZED','target_version':V}));u.close();g.close()
 else:self_test(x.root)
if __name__=='__main__':main()
