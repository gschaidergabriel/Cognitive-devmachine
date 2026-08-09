#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
TARGET_VERSION='RAE-TARGET-0.1'
SOURCE_FRANK_SCHEMA='FRANK UnifiedDB/ClayGraph current chain through UDB V13 / Graph V8'
IMPORTS=[
 ('gwt-strict-20260809','gwt','research_entity/trigger_runs/emergenz/20260809T2015p0700-chatgpt-gwt-emergence-fusion','03a4fddcf35b74e020c0011d27ec3477594a40cf','LITERATURE_SYNTHESIS_AND_EXPERIMENT_DESIGN_NO_LIVE_EXECUTION','OPEN','GWT causal chain: competition -> ignition -> delivery -> reconstruction -> use -> outcome -> provenance-bound re-entry; GCEP stays vector-valued.'),
 ('emergenz-v031','emergenz','research_entity/trigger_runs/emergenz/20260809T204545p0700_udb_emergence_meter_v03_adversarial_concordance/V031_LIVE_REFRESH_ADDENDUM.md','343fabb8b176df10f85aa3cbd4dce09f165b4987','SYNTHETIC_METHOD_EVIDENCE','OPEN','Fail-closed emergence gate; conditioning-depth instability => ABSTAIN_STATE_INADEQUATE; multi-method support is diagnostic, not voting truth.'),
 ('claycode-v17-boundary','claycode','research_entity/claycode/base/reports/CC_BASE_LAST_BLOCKERS_V17_RESOLUTION_20260809.md','d3c8e7de8ca2ccfdbc4db4180778b351b5b983b9','SOFTWARE_ORCHESTRATION_EVIDENCE','OPEN','V17 software/orchestration path selected; physical Andreas Ubuntu, WP14 and full release receipts still open.'),
 ('claycode-c11-hardening','claycode','research_entity/claycode/base/receipts/CC_WP06_SANDBOX_C11_SEMANTIC_HARDENING_20260809T2155p0700.json','1538ed5e5550ee2509c42e27077b87a00f918b33','EXECUTABLE_SANDBOX_EVIDENCE','OPEN','Checked numeric/C backend semantic hardening: 37/37 targeted, 20000/20000 random int64 evaluator and 180/180 native boundaries; not release promotion.'),
 ('frank-causal-reentry','frank','research_entity/rooms/center_events/20260809T2138p0700_chatgpt_secondary_frank_causal_reentry_cross_room_delta.json','83d2d41e751a332fa285b3d81cc753ab9b67648b','OWNER_OBSERVATION_PLUS_RESEARCH_SYNTHESIS','OPEN','Nested multiscale loop candidate: changed receiver/system state re-enters next episode with provenance; strong coupling alone is not the target.'),
]

def now(): return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
def uid(p): return f'{p}:{uuid.uuid4().hex}'
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def clamp(v): return max(0.0,min(1.0,float(v)))

def open_pair(root:Path,create=False):
 root=Path(root);root.mkdir(parents=True,exist_ok=True)
 u=sqlite3.connect(root/'RAE_UNIFIED.sqlite');g=sqlite3.connect(root/'RAE_CLAYGRAPH.sqlite')
 u.row_factory=g.row_factory=sqlite3.Row
 u.execute('PRAGMA foreign_keys=ON');g.execute('PRAGMA foreign_keys=ON')
 if create:
  u.executescript((HERE/'RAE_UNIFIED_SCHEMA.sql').read_text())
  g.executescript((HERE/'RAE_CLAYGRAPH_SCHEMA.sql').read_text())
  bootstrap(u,g)
 return u,g

def bootstrap(u,g):
 ts=now()
 u.execute('INSERT OR IGNORE INTO state_epochs VALUES(1,NULL,?,?,?)',(digest('rae-target-epoch-1'),ts,'chatgpt-secondary'))
 g.execute('INSERT OR IGNORE INTO graph_epochs VALUES(1,1,?,?,?)',(digest('rae-target-graph-1'),'CURRENT',ts))
 u.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('target_version',TARGET_VERSION));u.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('frank_schema_ancestry',SOURCE_FRANK_SCHEMA))
 for iid,domain,ref,commit,eclass,status,summary in IMPORTS:
  u.execute('INSERT OR REPLACE INTO research_imports VALUES(?,?,?,?,?,?,?,?,?)',(iid,domain,ref,commit,eclass,status,summary,digest(summary),ts))
 for row in [
  ('workspace','Global Workspace','competition, ignition, broadcast, receiver closure','gwt+claygraph','FUSED','frank:gwt-lineage'),
  ('hyperposition','Semantic Hyperposition','preserve unresolved alternatives and higher-order relations','unifieddb+claygraph','FUSED','frank:hyperposition-lineage'),
  ('reentry','Causal Re-entry','verified outcome/state delta influences later selection','unifieddb+gwt','EMERGENT_DISTRIBUTED','frank:loop-lineage'),
  ('semantic_fabric','Semantic Coupling Fabric','incremental dependency activation and bounded materialization','unifieddb+claygraph','EMERGENT_DISTRIBUTED','frank:semantic-coupling-lineage')]:
  u.execute('INSERT OR IGNORE INTO organ_registry VALUES(?,?,?,?,?,?,?,?)',(*row[:5],0,row[5],ts))
 u.execute('INSERT OR IGNORE INTO claycode_contract_receipts VALUES(?,?,?,?,?,?,?,?,?)',(
  'cc:target-0.1','tools/claycode_base_compiler.py','V17 contract-selected; sandbox C11 hardening also observed','RAE_TARGET_SEMANTIC_CONTRACT_0.1','SOFTWARE_PATH_AVAILABLE_RELEASE_OPEN','PHYSICAL_ACCEPTANCE_OPEN',
  json.dumps({'types':['Episode','ReceiverReceipt','ReentryDelta','ReentryReceipt','Hyperposition','EmergenceGateReceipt'],'authority':'measured_values_do_not_mint_truth','candidate_set':'known_union_emergent'},sort_keys=True),
  json.dumps({'source_commits':['d3c8e7de8ca2ccfdbc4db4180778b351b5b983b9','1538ed5e5550ee2509c42e27077b87a00f918b33']},sort_keys=True),ts))
 u.commit();g.commit()

def ensure_entity(u,ref,label=None):
 ts=now();u.execute('INSERT OR IGNORE INTO entities VALUES(?,?,?,?,?,?)',(ref,'concept',label or ref,'CURRENT',ts,ts))
def add_node(g,ref,label=None):
 r=g.execute('SELECT node_id FROM nodes WHERE semantic_ref=?',(ref,)).fetchone()
 if r:return r['node_id']
 nid='cg:'+digest(ref)[:20];g.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?)',(nid,ref,'semantic',label or ref,'EVIDENCE_BOUND',1,1,'CURRENT'));g.commit();return nid

def add_hyperbinding(g,members,joint=.9,pairwise=.5,persistence=.8,transfer=.7,causal=.6,prov_count=2,false_risk=.1):
 for m in members:add_node(g,m)
 bid=uid('hb');g.execute('INSERT INTO hyperbindings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(bid,json.dumps(sorted(members)),len(members)-1,joint,pairwise,joint-pairwise,persistence,transfer,causal,prov_count,false_risk,'CURRENT',json.dumps({'source':'verified_repeated_coactivity_or_intervention'}),1,now()));g.commit();return bid

def add_conflict(g,a,b):
 cid=uid('conflict');g.execute('INSERT INTO graph_conflicts VALUES(?,?,?,?,?,?,?,?)',(cid,a,b,'CONTRADICTION','OPEN','{}',1,now()));g.commit();return cid

def conflict_blocks(g,candidate,active):
 for ref in active:
  if g.execute("SELECT 1 FROM graph_conflicts WHERE state='OPEN' AND ((left_ref=? AND right_ref=?) OR (left_ref=? AND right_ref=?)) LIMIT 1",(candidate,ref,ref,candidate)).fetchone():return True
 return False

def token_overlap(intent,ref):
 tok=lambda x:{t for t in ''.join(c.lower() if c.isalnum() else ' ' for c in x).split() if len(t)>1}
 a,b=tok(intent),tok(ref);return len(a&b)/len(a|b) if a and b else 0.0

def generate_candidates(u,g,intent,active_refs,cycle='cycle:test'):
 active=set(active_refs);c={}
 for ref in active:
  c[(ref,'KNOWN')]={'fit':max(.55,token_overlap(intent,ref)),'novelty':.05,'evidence':.9,'risk':.1,'reason':'active semantic cue'}
  for r in u.execute("SELECT child_ref,confidence FROM semantic_dependencies WHERE parent_ref=? AND status='ACTIVE'",(ref,)):
   if not conflict_blocks(g,r['child_ref'],active):c[(r['child_ref'],'KNOWN')]={'fit':max(.5,token_overlap(intent,r['child_ref'])),'novelty':.1,'evidence':clamp(r['confidence']),'risk':.12,'reason':'prepared dependency neighborhood'}
 for r in g.execute("SELECT * FROM hyperbindings WHERE status='CURRENT'"):
  members=set(json.loads(r['members_clay']));present=members&active;missing=members-active
  if len(missing)!=1 or len(present)<r['required_count']:continue
  cand=next(iter(missing))
  if r['synergy']<=0 or r['provenance_count']<2 or r['persistence']<.5 or r['false_binding_risk']>.35 or conflict_blocks(g,cand,active):continue
  ev=clamp(.25*r['persistence']+.25*r['transfer']+.3*r['causal_contribution']+.2*min(1,r['provenance_count']/3));fit=clamp(.55+.25*token_overlap(intent,cand)+.2*r['causal_contribution']);nov=clamp(.55+.35*r['synergy']);risk=clamp(r['false_binding_risk']+.15*(1-r['causal_contribution']))
  c[(cand,'EMERGENT_NOVEL')]={'fit':fit,'novelty':nov,'evidence':ev,'risk':risk,'reason':f"higher-order completion of {sorted(present)}; synergy={r['synergy']:.3f}"}
 rows=[]
 for (ref,lane),m in c.items():rows.append({'semantic_ref':ref,'lane':lane,**m,'score':.38*m['fit']+.30*m['evidence']+.20*m['novelty']-.12*m['risk']})
 rows.sort(key=lambda x:(x['lane']!='KNOWN',-x['score']))
 cs=uid('cset');g.execute('INSERT INTO candidate_sets VALUES(?,?,?,?,?,?,?)',(cs,cycle,json.dumps({'intent':intent,'active_refs':sorted(active)}),1,1,digest(json.dumps([(r['semantic_ref'],r['lane']) for r in rows],sort_keys=True)),now()))
 for r in rows:g.execute('INSERT INTO candidate_members VALUES(?,?,?,?,?,?,?,?,?)',(cs,r['semantic_ref'],r['lane'],r['fit'],r['novelty'],r['evidence'],r['risk'],r['score'],json.dumps({'reason':r['reason']})))
 g.commit();frame,hp=uid('frame'),uid('hp');ts=now();u.execute('INSERT INTO possibility_frames VALUES(?,?,?,?,?,?,?,?)',(frame,cycle,json.dumps(sorted(active)),json.dumps({'consistency':'fail_closed'}),'rae.target::known_union_emergent',1,1,ts));u.execute('INSERT INTO hyperpositions VALUES(?,?,?,?,?,?,?,?,?)',(hp,frame,'entity:research','{}','OPEN','CANDIDATE_SURFACE',.5,ts,None))
 for i,r in enumerate(rows):u.execute('INSERT INTO hyperposition_alternatives VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(f'{hp}:alt:{i+1}',hp,r['lane'],r['semantic_ref'],json.dumps({'semantic_ref':r['semantic_ref'],'reason':r['reason']}),r['fit'],r['novelty'],r['evidence'],r['risk'],'ADMISSIBLE',json.dumps({'generator':'target_runtime'}),'ACTIVE'))
 u.commit();return cs,hp,rows

def gwt_select(u,rows,cycle='cycle:test'):
 ranked=sorted(rows,key=lambda r:r['score'],reverse=True);best=ranked[0];second=ranked[1]['score'] if len(ranked)>1 else 0;margin=best['score']-second;eid=uid('gwt');u.execute('INSERT INTO gwt_episodes VALUES(?,?,?,?,?,?,?,?)',(eid,cycle,digest(json.dumps([(r['semantic_ref'],r['lane']) for r in rows],sort_keys=True)),best['semantic_ref'],margin,clamp(.55+margin),3,now()));u.commit();return eid,best

def receiver_receipt(u,episode,receiver,delivered=1,reconstructed=1,used=1,effect=1):
 rid=uid('recv');u.execute('INSERT INTO gwt_receiver_receipts VALUES(?,?,?,?,?,?,?,?,?,?)',(rid,episode,receiver,1,delivered,reconstructed,used,effect,json.dumps({'measured':True}),now()));u.commit();return rid

def record_outcome_and_reentry(u,episode,to_cycle,verified=True,truth='TRUTHFUL_PROVENANCE'):
 oid=uid('out');u.execute('INSERT INTO outcomes VALUES(?,?,?,?,?,?)',(oid,episode,json.dumps({'result':'measured'}),int(verified),json.dumps({'sandbox':True}),now()));rr=uid('reentry');applied=int(verified and truth=='TRUTHFUL_PROVENANCE');u.execute('INSERT INTO reentry_receipts VALUES(?,?,?,?,?,?,?,?,?)',(rr,oid,episode,to_cycle,truth,json.dumps({'activation_delta':.17,'slow_state_delta':.04}),applied,json.dumps({'provenance_bound':truth=='TRUTHFUL_PROVENANCE'}),now()));u.commit();return oid,rr

def emergence_gate(u,subject,state_stable=True,lesion=.2,rescue=.8,shuffle=.15,ood=.1,macro=.05,cost=.1):
 use=bool(u.execute('SELECT 1 FROM gwt_receiver_receipts WHERE used=1 AND local_effect=1 LIMIT 1').fetchone());re=bool(u.execute("SELECT 1 FROM reentry_receipts WHERE truth_class='TRUTHFUL_PROVENANCE' AND applied=1 LIMIT 1").fetchone())
 verdict='ABSTAIN_STATE_INADEQUATE' if not state_stable else ('SUPPORTED_FUNCTIONAL_PATTERN' if use and re and lesion>.1 and rescue>.5 and shuffle>.05 and ood>0 and macro>0 else 'OPEN')
 u.execute('INSERT INTO emergence_gate_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid('gate'),subject,'STABLE' if state_stable else 'UNSTABLE',int(use),int(re),lesion,rescue,shuffle,ood,macro,cost,verdict,json.dumps({'claim_boundary':'functional_pattern_not_consciousness'}),now()));u.commit();return verdict

def self_test(root:Path):
 import shutil
 if root.exists():shutil.rmtree(root)
 u,g=open_pair(root,create=True);checks=[]
 def ok(name,cond):assert cond,name;checks.append(name)
 try:
  ok('imports_seeded',u.execute('SELECT COUNT(*) FROM research_imports').fetchone()[0]>=5);ok('claycode_release_fail_closed',u.execute("SELECT physical_release_status FROM claycode_contract_receipts WHERE receipt_id='cc:target-0.1'").fetchone()[0]=='PHYSICAL_ACCEPTANCE_OPEN')
  blocked=False
  try:u.execute("DELETE FROM organ_registry WHERE organ_id='workspace'");u.commit()
  except sqlite3.IntegrityError:blocked=True;u.rollback()
  ok('organ_delete_blocked',blocked)
  for ref in ['intent:repair','state:workspace','state:memory_reentry']:ensure_entity(u,ref);add_node(g,ref)
  u.execute('INSERT INTO semantic_dependencies VALUES(?,?,?,?,?,?,?,?,?)',(uid('dep'),'intent:repair','state:workspace','PREPARED_NEIGHBORHOOD',.95,'VERIFIED','{}','ACTIVE',now()));u.commit();add_hyperbinding(g,['intent:repair','state:workspace','state:memory_reentry'],.93,.48,.88,.76,.72,3,.08)
  _,_,rows=generate_candidates(u,g,'repair with workspace memory',['intent:repair','state:workspace']);ok('known_lane_present',any(r['lane']=='KNOWN' for r in rows));ok('emergent_not_manual',any(r['lane']=='EMERGENT_NOVEL' and r['semantic_ref']=='state:memory_reentry' for r in rows));ok('candidate_union_preserved',{'KNOWN','EMERGENT_NOVEL'}<={r['lane'] for r in rows})
  add_hyperbinding(g,['intent:repair','state:workspace','candidate:forbidden'],.95,.4,.9,.9,.8,3,.05);add_conflict(g,'candidate:forbidden','state:workspace');_,_,r2=generate_candidates(u,g,'repair',['intent:repair','state:workspace'],'cycle:2');ok('consistency_gate_blocks_conflict',not any(r['semantic_ref']=='candidate:forbidden' for r in r2))
  ep,best=gwt_select(u,rows);guard=False
  try:receiver_receipt(u,ep,'receiver:test',0,0,1,0)
  except sqlite3.IntegrityError:guard=True;u.rollback()
  ok('gwt_stage_guard',guard);receiver_receipt(u,ep,'receiver:planner');ok('receiver_use_measured',u.execute('SELECT COUNT(*) FROM gwt_receiver_receipts WHERE used=1 AND local_effect=1').fetchone()[0]==1);record_outcome_and_reentry(u,ep,'cycle:next');ok('truthful_reentry_applied',u.execute('SELECT COUNT(*) FROM reentry_receipts WHERE applied=1').fetchone()[0]==1)
  ok('state_adequacy_fail_closed',emergence_gate(u,'test',False)=='ABSTAIN_STATE_INADEQUATE');ok('functional_gate_requires_controls',emergence_gate(u,'test',True,0,0,0,0,0)=='OPEN');ok('functional_pattern_not_consciousness',emergence_gate(u,'test',True,.2,.8,.15,.1,.05)=='SUPPORTED_FUNCTIONAL_PATTERN');ok('unified_integrity',u.execute('PRAGMA integrity_check').fetchone()[0]=='ok');ok('graph_integrity',g.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
  result={'status':'PASS','target_version':TARGET_VERSION,'checks':checks,'passed':len(checks),'candidate_example':rows,'selected':best,'claim_boundary':'functional pattern only; no consciousness claim'};print(json.dumps(result,indent=2,ensure_ascii=False));return result
 finally:u.close();g.close()

def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True);x=s.add_parser('init');x.add_argument('--root',required=True);x=s.add_parser('self-test');x.add_argument('--root',required=True);a=p.parse_args()
 if a.cmd=='init':u,g=open_pair(Path(a.root),create=True);print(json.dumps({'status':'INITIALIZED','target_version':TARGET_VERSION}));u.close();g.close()
 else:self_test(Path(a.root))
if __name__=='__main__':main()
