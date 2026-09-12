#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, json, os, sqlite3, sys, time, uuid
from pathlib import Path
from router import DynamicOrganRouter, OrganTelemetry, TaskRequest

ROOT=Path(os.getenv('OMEGA_RUNTIME_ROOT','/workspace/omega_runtime/state'))
CFG=Path(os.getenv('OMEGA_ROUTER_CONFIG','/workspace/omega_runtime/config/organ_router.json'))
INTERVAL=float(os.getenv('OMEGA_GRID_INTERVAL','30'))
CELLS=('REENTRY','RESEARCH','WORLD_MODEL','HOST_SCOUT','SELF_IMPROVE','FALSIFIER','MAINTENANCE','MEMORY_COMPRESSION','EFFECT_RECONCILIATION','MASTER_BRIDGE')

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(x): return hashlib.sha256(canon(x).encode()).hexdigest()

class Omega:
 def __init__(self):
  for n in ('inbox','outbox','telemetry','receipts','candidates','master_bridge'): (ROOT/n).mkdir(parents=True,exist_ok=True)
  self.db=ROOT/'omega_runtime.sqlite3'; self.router=DynamicOrganRouter.from_path(CFG); self.initdb()
 def con(self): c=sqlite3.connect(self.db); c.row_factory=sqlite3.Row; return c
 def initdb(self):
  with self.con() as c:c.executescript('''PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS epoch(epoch_id TEXT PRIMARY KEY,started_at TEXT,predecessor_epoch_id TEXT,status TEXT,state_digest TEXT);
CREATE TABLE IF NOT EXISTS frame(frame_id TEXT PRIMARY KEY,epoch_id TEXT,predecessor_frame_id TEXT,created_at TEXT,selected_cell TEXT,score REAL,broadcast_json TEXT,state_digest TEXT);
CREATE TABLE IF NOT EXISTS proposal(proposal_id TEXT PRIMARY KEY,frame_id TEXT,cell_id TEXT,score REAL,payload_json TEXT,selected INTEGER);
CREATE TABLE IF NOT EXISTS task(task_id TEXT PRIMARY KEY,payload_json TEXT,state TEXT,created_at TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS effect_intent(effect_id TEXT PRIMARY KEY,frame_id TEXT,organ_id TEXT,request_sha256 TEXT,payload_json TEXT,state TEXT,created_at TEXT,updated_at TEXT);''')
 def latest(self,t,idc,tc):
  with self.con() as c:r=c.execute(f'SELECT {idc} FROM {t} ORDER BY {tc} DESC LIMIT 1').fetchone();return r[0] if r else None
 def telemetry(self):
  out={}
  for p in (ROOT/'telemetry').glob('*.json'):
   try:
    d=json.loads(p.read_text()); out[str(d.get('organ_id') or p.stem)]=d
   except Exception:pass
  return out
 def route_telemetry(self):
  raw=self.telemetry(); arr=[]
  for oid,cfg in self.router.organs.items():
   if oid==self.router.central:
    arr.append(OrganTelemetry(oid,now(),'GREEN',frozenset(cfg.get('capabilities',())),frozenset({'omega-central'}),.3,.3,None,1.0,.6,.3,1.0));continue
   d=raw.get(oid)
   if not isinstance(d,dict) or not d.get('observed_at'):continue
   arr.append(OrganTelemetry(oid,str(d['observed_at']),str(d.get('health','UNKNOWN')),frozenset(d.get('capabilities',())),frozenset(d.get('data_domains',())),d.get('cpu_load'),d.get('ram_load'),d.get('gpu_load'),float(d.get('bridge_health',1)),float(d.get('information_gain',.5)),float(d.get('independence',.5)),float(d.get('latency_score',.5))))
  return arr
 def ingest(self):
  for p in (ROOT/'inbox').glob('*.json'):
   try:
    d=json.loads(p.read_text()); tid=str(d.get('task_id') or 'task_'+sha(d)[:24]); t=now()
    with self.con() as c:c.execute('INSERT OR IGNORE INTO task VALUES(?,?,?,?,?)',(tid,canon(d),'OPEN',t,t))
    p.rename(p.with_suffix('.consumed'))
   except Exception:pass
 def tasks(self):
  with self.con() as c:rows=c.execute("SELECT task_id,payload_json FROM task WHERE state='OPEN' ORDER BY created_at").fetchall()
  out=[]
  for r in rows:
   d=json.loads(r['payload_json']);d['task_id']=r['task_id'];out.append(d)
  return out
 def effects(self):
  with self.con() as c:return [dict(r) for r in c.execute('SELECT effect_id,organ_id,state,updated_at FROM effect_intent ORDER BY updated_at DESC LIMIT 32')]
 def free_available(self):
  tools=Path('/workspace/clay-global-research-entity/tools')
  if not tools.exists():return False
  try:
   sys.path.insert(0,str(tools));from run_free_go_swarm import PROVIDERS,provider_execution_admitted
   return any(provider_execution_admitted(s) for s in PROVIDERS)
  except Exception:return False
 def out(self,kind,payload):
  d={'schema':'OMEGA_OUTBOX/v1','message_id':'msg_'+uuid.uuid4().hex,'created_at':now(),'kind':kind,'payload':payload}
  (ROOT/'outbox'/f"{d['message_id']}.json").write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');return d['message_id']
 def route(self,task):
  req=TaskRequest(str(task.get('task_id') or 'grid_'+uuid.uuid4().hex),frozenset(task.get('required_capabilities',())),frozenset(task.get('preferred_data_domains',())),bool(task.get('heavy',False)),bool(task.get('high_risk_effect',False)),bool(task.get('wants_independent_falsifier',False)),max(1,int(task.get('max_organs',1))))
  return self.router.choose(req,self.route_telemetry()).as_dict()
 def proposals(self):
  tasks=self.tasks(); tele=self.telemetry(); free=self.free_available(); unknown=any(e['state']=='UNKNOWN' for e in self.effects()); missing=len({'host:ai-core-node','host:andreas-maco'}-set(tele))
  s={'REENTRY':.30,'RESEARCH':.25+(.25 if free else 0),'WORLD_MODEL':.22,'HOST_SCOUT':.20+min(.35,.12*missing),'SELF_IMPROVE':.28 if not tasks else .18,'FALSIFIER':.24,'MAINTENANCE':.18,'MEMORY_COMPRESSION':.16,'EFFECT_RECONCILIATION':.75 if unknown else .10,'MASTER_BRIDGE':.20}
  if tasks:s['RESEARCH']+=.10;s['HOST_SCOUT']+=.10;s['FALSIFIER']+=.08
  task=tasks[0] if tasks else {'task_id':'background_host_scout','required_capabilities':['local_state'],'max_organs':1}
  return [{'proposal_id':'prop_'+uuid.uuid4().hex,'cell_id':x,'score':round(s[x],6),'payload':{'task':task,'free':free}} for x in CELLS]
 def realize(self,p,frame):
  cell=p['cell_id'];payload=p['payload']
  if cell=='HOST_SCOUT':
   try:r=self.route(payload['task'])
   except Exception as e:self.out('GRID_ROUTE_BLOCKED',{'frame_id':frame,'error':f'{type(e).__name__}:{e}'});return {'blocked':str(e)}
   ids=[]
   for oid in r['selected_organs']:
    req={'schema':'OMEGA_GRID_EFFECT_INTENT/v1','effect_id':'effect_'+uuid.uuid4().hex,'frame_id':frame,'organ_id':oid,'task':payload['task'],'route':r,'authority':'NOT_YET_GRANTED'};dig=sha(req);t=now()
    with self.con() as c:c.execute('INSERT INTO effect_intent VALUES(?,?,?,?,?,?,?,?)',(req['effect_id'],frame,oid,dig,canon(req),'PROPOSED',t,t))
    self.out('GRID_EFFECT_INTENT',{**req,'request_sha256':dig});ids.append(req['effect_id'])
   return {'route':r,'effect_intents':ids}
  if cell=='RESEARCH':self.out('FREE_WORKER_REQUEST' if payload['free'] else 'RESEARCH_ADMISSION_NEEDED',{'frame_id':frame,**payload});return {'research_requested':True,'free':payload['free']}
  if cell=='MASTER_BRIDGE':self.out('MASTER_COGNITION_UPDATE',{'frame_id':frame,'tasks':self.tasks(),'effects':self.effects()});return {'master_update':True}
  if cell=='SELF_IMPROVE':
   d={'candidate_id':'cand_'+uuid.uuid4().hex,'created_at':now(),'state':'PROPOSED','rule':'candidate_only_no_self_promotion'};(ROOT/'candidates'/f"{d['candidate_id']}.json").write_text(json.dumps(d,indent=2)+'\n');return d
  return {'maintenance':cell}
 def start_epoch(self):
  prev=self.latest('epoch','epoch_id','started_at');eid='epoch_'+uuid.uuid4().hex
  with self.con() as c:c.execute('INSERT INTO epoch VALUES(?,?,?,?,?)',(eid,now(),prev,'RUNNING',sha({'tasks':self.tasks(),'effects':self.effects()})))
  return eid
 def frame(self,eid):
  self.ingest();ps=self.proposals();win=max(ps,key=lambda x:x['score']);fid='frame_'+uuid.uuid4().hex;prev=self.latest('frame','frame_id','created_at');res=self.realize(win,fid);state={'tasks':self.tasks(),'effects':self.effects(),'telemetry':self.telemetry()}
  with self.con() as c:
   c.execute('INSERT INTO frame VALUES(?,?,?,?,?,?,?,?)',(fid,eid,prev,now(),win['cell_id'],win['score'],canon(res),sha(state)))
   for p in ps:c.execute('INSERT INTO proposal VALUES(?,?,?,?,?,?)',(p['proposal_id'],fid,p['cell_id'],p['score'],canon(p['payload']),1 if p is win else 0))
  (ROOT/'STATUS.json').write_text(json.dumps({'schema':'OMEGA_GRID_STATUS/v1','updated_at':now(),'epoch_id':eid,'frame_id':fid,'selected':win,'result':res},indent=2,ensure_ascii=False)+'\n')
 def run(self):
  eid=self.start_epoch()
  while True:
   try:self.frame(eid)
   except Exception as e:self.out('RUNTIME_ERROR',{'error':f'{type(e).__name__}:{e}'})
   time.sleep(INTERVAL)

if __name__=='__main__':Omega().run()
