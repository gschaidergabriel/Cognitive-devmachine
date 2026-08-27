#!/usr/bin/env python3
"""Clay dynamic work fabric.

Local UnifiedDB is the materialized operational state. Cross-provider work changes travel
as append-only repo events under research_entity/state/work/events/. The runtime can read
remote events with git-show without merging Claude's worktree.
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, sqlite3, subprocess, time, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DB=ROOT/'research_entity/state/RAE_UNIFIED.sqlite'
SCHEMA=ROOT/'research_entity/runtime/RAE_UNIFIEDDB_V9_DYNAMIC_WORK_FABRIC.sql'
EVENT_DIR=ROOT/'research_entity/state/work/events'
REMOTE='origin';BRANCH='main'

def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def uid(p):return f'{p}:{uuid.uuid4().hex}'
def jd(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'),sort_keys=True)
def jp(x,d=None):
    try:return json.loads(x)
    except Exception:return d if d is not None else x
def db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;c.execute('PRAGMA busy_timeout=10000');c.execute('PRAGMA foreign_keys=ON')
    c.executescript(SCHEMA.read_text(encoding='utf-8'));c.commit();return c

def git(*a,timeout=40):
    e=os.environ.copy();e.setdefault('GIT_TERMINAL_PROMPT','0')
    return subprocess.run(['git',*a],cwd=ROOT,text=True,capture_output=True,timeout=timeout,env=e)

def remote_event_paths():
    if git('fetch','--quiet',REMOTE,BRANCH,timeout=50).returncode:return []
    p=git('ls-tree','-r','--name-only',f'{REMOTE}/{BRANCH}','research_entity/state/work/events',timeout=20)
    return [x.strip() for x in p.stdout.splitlines() if x.strip().endswith('.json')] if p.returncode==0 else []
def remote_json(path):
    p=git('show',f'{REMOTE}/{BRANCH}:{path}',timeout=20)
    if p.returncode:return None
    try:return json.loads(p.stdout)
    except Exception:return None

def event_seen(c,event_id):
    try:
        return c.execute("SELECT 1 FROM semantic_records WHERE record_kind='CLAY_WORK_EVENT' AND record_key=? AND status='CURRENT'",(event_id,)).fetchone() is not None
    except sqlite3.Error:
        c.execute('CREATE TABLE IF NOT EXISTS clay_work_event_ingest(event_id TEXT PRIMARY KEY,event_hash TEXT,ingested_at TEXT)')
        return c.execute('SELECT 1 FROM clay_work_event_ingest WHERE event_id=?',(event_id,)).fetchone() is not None

def mark_event(c,event_id,h):
    try:
        c.execute("INSERT OR IGNORE INTO semantic_records(record_id,record_kind,record_key,scope,epistemic_class,payload_clay,source_ref,source_hash,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                  (uid('rec'),'CLAY_WORK_EVENT',event_id,'CLAY','EXACT_DERIVED',jd({'hash':h}),f'repo:event:{event_id}',h,'CURRENT',now(),now()))
    except sqlite3.Error:
        c.execute('CREATE TABLE IF NOT EXISTS clay_work_event_ingest(event_id TEXT PRIMARY KEY,event_hash TEXT,ingested_at TEXT)')
        c.execute('INSERT OR IGNORE INTO clay_work_event_ingest VALUES(?,?,?)',(event_id,h,now()))

def apply_event(c,e,source='repo'):
    eid=e.get('event_id');kind=e.get('kind');p=e.get('payload') or {};ts=e.get('created_at') or now();actor=e.get('actor') or 'UNKNOWN'
    if not eid:return False
    h=hashlib.sha256(jd(e).encode()).hexdigest()
    if event_seen(c,eid):return False
    wid=p.get('work_id')
    if kind=='WORK_CREATE':
        c.execute('INSERT OR IGNORE INTO clay_work_items(work_id,goal_ref,origin_class,created_by,created_at) VALUES(?,?,?,?,?)',(wid,p['goal_ref'],p.get('origin_class','CHATGPT_OR_CLAUDE'),actor,ts))
        c.execute('''INSERT OR IGNORE INTO clay_work_spec_revisions(work_id,spec_rev,parent_rev,title,work_clay,reason_clay,completion_clay,evidence_need_clay,executor_policy_clay,required_capabilities_clay,write_scope_clay,dependency_clay,invalidation_clay,base_priority,expected_impact,urgency,information_gain,status,source_ref,created_by,created_at)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(wid,int(p.get('spec_rev',1)),None,p['title'],jd(p.get('work_clay',{})),jd(p.get('reason_clay',{})),jd(p.get('completion_clay',{})),jd(p.get('evidence_need',[])),jd(p.get('executor_policy',{})),jd(p.get('required_capabilities',[])),jd(p.get('write_scope',[])),jd(p.get('dependencies',[])),jd(p.get('invalidators',[])),float(p.get('base_priority',.5)),float(p.get('expected_impact',.5)),float(p.get('urgency',0)),float(p.get('information_gain',0)),p.get('status','READY'),source,actor,ts))
    elif kind in {'WORK_REVISE','WORK_CANCEL','WORK_DEFER'}:
        cur=c.execute('SELECT MAX(spec_rev) FROM clay_work_spec_revisions WHERE work_id=?',(wid,)).fetchone()[0] or 0
        rev=int(p.get('spec_rev',cur+1));prev=c.execute('SELECT * FROM clay_work_spec_revisions WHERE work_id=? AND spec_rev=?',(wid,cur)).fetchone()
        if not prev:return False
        status='CANCELLED' if kind=='WORK_CANCEL' else 'DEFERRED' if kind=='WORK_DEFER' else p.get('status','READY')
        def val(k,col,default=None):return p[k] if k in p else (prev[col] if prev else default)
        c.execute('''INSERT OR IGNORE INTO clay_work_spec_revisions(work_id,spec_rev,parent_rev,title,work_clay,reason_clay,completion_clay,evidence_need_clay,executor_policy_clay,required_capabilities_clay,write_scope_clay,dependency_clay,invalidation_clay,base_priority,expected_impact,urgency,information_gain,status,source_ref,created_by,created_at)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(wid,rev,cur,val('title','title'),jd(p.get('work_clay',jp(prev['work_clay'],{}))),jd(p.get('reason_clay',{'event':kind})),jd(p.get('completion_clay',jp(prev['completion_clay'],{}))),jd(p.get('evidence_need',jp(prev['evidence_need_clay'],[]))),jd(p.get('executor_policy',jp(prev['executor_policy_clay'],{}))),jd(p.get('required_capabilities',jp(prev['required_capabilities_clay'],[]))),jd(p.get('write_scope',jp(prev['write_scope_clay'],[]))),jd(p.get('dependencies',jp(prev['dependency_clay'],[]))),jd(p.get('invalidators',jp(prev['invalidation_clay'],[]))),float(p.get('base_priority',prev['base_priority'])),float(p.get('expected_impact',prev['expected_impact'])),float(p.get('urgency',prev['urgency'])),float(p.get('information_gain',prev['information_gain'])),status,source,actor,ts))
    elif kind=='WORK_EXECUTION_RECEIPT':
        c.execute('''INSERT OR IGNORE INTO clay_execution_receipts(execution_receipt_id,work_id,spec_rev,executor_node,executor_class,machine_ref,action_clay,observed_effect_clay,verification_clay,evidence_refs_clay,truth_class,success,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(p.get('execution_receipt_id') or uid('exec'),wid,p.get('spec_rev'),actor,p.get('executor_class','UNKNOWN'),p.get('machine_ref'),jd(p.get('action',{})),jd(p.get('observed_effect',{})),jd(p.get('verification',{})),jd(p.get('evidence_refs',[])),p.get('truth_class','UNVERIFIED'),1 if p.get('success') else 0,ts))
        if p.get('success') and p.get('complete'):
            c.execute('UPDATE clay_work_items SET terminal_status=?,terminal_at=? WHERE work_id=?',('COMPLETE',ts,wid))
    else:return False
    mark_event(c,eid,h);return True

def ingest_remote():
    c=db();n=0
    try:
        for path in remote_event_paths():
            e=remote_json(path)
            if e and apply_event(c,e,f'git:{REMOTE}/{BRANCH}:{path}'):n+=1
        c.commit()
    finally:c.close()
    return n

def emit_event(kind,payload,actor='chatgpt-secondary',write_local=True):
    EVENT_DIR.mkdir(parents=True,exist_ok=True);e={'schema_version':'2.0','event_id':uid('clay-work-event'),'kind':kind,'actor':actor,'payload':payload,'created_at':now()}
    path=EVENT_DIR/(e['event_id'].replace(':','_')+'.json')
    if write_local:path.write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf-8')
    c=db();apply_event(c,e,str(path.relative_to(ROOT)));c.commit();c.close();return e,path

def observe_local(actor='claude-code-lead'):
    c=db();ts=now();host=platform.node() or 'local';rid=f'host:{host}'
    mem=None
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'):mem=int(line.split()[1])*1024;break
    except Exception:pass
    details={'os':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),'cpu_count':os.cpu_count(),'memory_bytes':mem}
    c.execute('INSERT INTO clay_system_resource_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid('resobs'),rid,'LOCAL_HOST',host,host,None,jd(details),jd({'local_execution':True}),'AVAILABLE','VERIFIED_CURRENT_REALITY','runtime:observe_local',ts,300,actor))
    tools=['git','python','python3','claude','nvidia-smi','docker']
    for t in tools:
        p=shutil.which(t);state='CAN_NOW' if p else 'CANNOT_NOW';conf=1.0 if p else .95
        c.execute('INSERT INTO clay_capability_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid('capobs'),f'{rid}:{t}',rid,f'tool:{t}','LOCAL_TOOL',state,jd(['text']),jd({'path':p}),jd({'local':True}),jd({}),jd({}),jd({'local_only':True}),0,0,conf,jd({'which':p}),ts,300,actor))
    c.commit();c.close();return details

def recompute(actor='scheduler'):
    c=db();out=[]
    try:
        caps=[dict(r) for r in c.execute("SELECT capability_key,effective_state,resource_id,confidence FROM v_clay_current_capabilities")]
        by={}
        for x in caps:by.setdefault(x['capability_key'],[]).append(x)
        for s in c.execute('SELECT * FROM v_clay_current_work_specs'):
            req=jp(s['required_capabilities_clay'],[]) or [];policy=jp(s['executor_policy_clay'],{}) or {};missing=[];resources=[]
            for cap in req:
                good=[x for x in by.get(cap,[]) if x['effective_state'] in ('CAN_NOW','CAN_DELEGATE')]
                if good:resources+=good
                else:missing.append(cap)
            capability_fit=1.0 if not req else (len(req)-len(missing))/len(req)
            availability_fit=1.0 if (not req or resources) else 0.0
            eligibility='ELIGIBLE' if not missing and s['status']=='READY' else 'BLOCKED' if missing else 'DEFER'
            preferred=policy.get('prefer') if isinstance(policy,dict) else None
            selected=preferred or (resources[0]['resource_id'] if resources else None)
            goal_fit=1.0 if s['goal_ref']=='FRANK_V0_1_ANDREAS_PC' else .7
            collision=.05;cost=0.0;stale=.0;dep=0.0
            score=(goal_fit+s['expected_impact']+s['urgency']+s['information_gain']+capability_fit+availability_fit+dep-collision-cost-stale)/7.0
            reason={'required':req,'missing':missing,'selected':selected,'status':s['status']}
            c.execute('''INSERT INTO clay_work_scheduler_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(uid('sched'),s['work_id'],s['spec_rev'],actor,goal_fit,capability_fit,availability_fit,dep,s['urgency'],s['information_gain'],collision,cost,stale,score,eligibility,selected,jd({'caps':caps[:64]}),jd(reason),now()))
            out.append({'work_id':s['work_id'],'score':round(score,3),'eligibility':eligibility,'selected':selected,'missing':missing})
        c.commit()
    finally:c.close()
    return out

def queue(limit=20):
    c=db()
    try:return [dict(r) for r in c.execute('SELECT * FROM v_clay_dynamic_work_queue LIMIT ?',(limit,))]
    finally:c.close()

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('init');sp.add_parser('ingest');sp.add_parser('observe-local');sp.add_parser('recompute');q=sp.add_parser('queue');q.add_argument('--limit',type=int,default=20)
    c=sp.add_parser('create');c.add_argument('--title',required=True);c.add_argument('--work',required=True);c.add_argument('--complete',required=True);c.add_argument('--goal-ref',default='FRANK_V0_1_ANDREAS_PC');c.add_argument('--require-cap',action='append');c.add_argument('--prefer');c.add_argument('--priority',type=float,default=.5);c.add_argument('--impact',type=float,default=.5);c.add_argument('--urgency',type=float,default=0);c.add_argument('--info',type=float,default=0);c.add_argument('--actor',default='chatgpt-secondary')
    r=sp.add_parser('revise');r.add_argument('work_id');r.add_argument('--work');r.add_argument('--reason',required=True);r.add_argument('--actor',default='chatgpt-secondary')
    x=sp.add_parser('cancel');x.add_argument('work_id');x.add_argument('--reason',required=True);x.add_argument('--actor',default='chatgpt-secondary')
    a=ap.parse_args()
    if a.cmd=='init':db().close();print('{}')
    elif a.cmd=='ingest':print(jd({'ingested':ingest_remote()}))
    elif a.cmd=='observe-local':print(jd(observe_local()))
    elif a.cmd=='recompute':print(jd(recompute()))
    elif a.cmd=='queue':print(json.dumps(queue(a.limit),ensure_ascii=False,default=str))
    elif a.cmd=='create':
        wid=f'work:{uuid.uuid4().hex}';payload={'work_id':wid,'goal_ref':a.goal_ref,'origin_class':'USER_OR_RESEARCH_DERIVED','title':a.title,'work_clay':{'task':a.work},'completion_clay':{'test':a.complete},'required_capabilities':a.require_cap or [],'executor_policy':({'prefer':a.prefer} if a.prefer else {}),'base_priority':a.priority,'expected_impact':a.impact,'urgency':a.urgency,'information_gain':a.info,'status':'READY'};e,p=emit_event('WORK_CREATE',payload,a.actor);print(jd({'work_id':wid,'event':e['event_id'],'file':str(p.relative_to(ROOT))}))
    elif a.cmd=='revise':
        payload={'work_id':a.work_id,'reason_clay':{'reason':a.reason}};
        if a.work:payload['work_clay']={'task':a.work}
        e,p=emit_event('WORK_REVISE',payload,a.actor);print(jd({'event':e['event_id'],'file':str(p.relative_to(ROOT))}))
    else:
        e,p=emit_event('WORK_CANCEL',{'work_id':a.work_id,'reason_clay':{'reason':a.reason}},a.actor);print(jd({'event':e['event_id'],'file':str(p.relative_to(ROOT))}))
if __name__=='__main__':main()
