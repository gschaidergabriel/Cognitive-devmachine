#!/usr/bin/env python3
"""Clay dynamic work fabric v2. Named-column SQL only; repo events -> local UnifiedDB."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, sqlite3, subprocess, time, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DB=ROOT/'research_entity/state/RAE_UNIFIED.sqlite'
SCHEMA=ROOT/'research_entity/runtime/RAE_UNIFIEDDB_V9_DYNAMIC_WORK_FABRIC.sql'
REMOTE='origin';BRANCH='main';EVENT_PREFIX='research_entity/state/work/events/'

def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def uid(p):return f'{p}:{uuid.uuid4().hex}'
def J(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'),sort_keys=True)
def P(x,d):
    try:return json.loads(x)
    except Exception:return d

def open_db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=10000');c.executescript(SCHEMA.read_text());c.execute('CREATE TABLE IF NOT EXISTS clay_work_event_ingest(event_id TEXT PRIMARY KEY,event_hash TEXT NOT NULL,source_ref TEXT,ingested_at TEXT NOT NULL)');c.commit();return c

def git(*a,timeout=40):
    e=os.environ.copy();e.setdefault('GIT_TERMINAL_PROMPT','0');return subprocess.run(['git',*a],cwd=ROOT,text=True,capture_output=True,timeout=timeout,env=e)
def remote_paths():
    if git('fetch','--quiet',REMOTE,BRANCH,timeout=50).returncode:return []
    p=git('ls-tree','-r','--name-only',f'{REMOTE}/{BRANCH}',EVENT_PREFIX.rstrip('/'))
    return [x for x in p.stdout.splitlines() if x.endswith('.json')] if p.returncode==0 else []
def remote_event(path):
    p=git('show',f'{REMOTE}/{BRANCH}:{path}')
    if p.returncode:return None
    try:return json.loads(p.stdout)
    except Exception:return None

def apply_event(c,e,source_ref):
    eid=e.get('event_id');kind=e.get('kind');p=e.get('payload') or {};actor=e.get('actor','UNKNOWN');ts=e.get('created_at',now())
    if not eid or c.execute('SELECT 1 FROM clay_work_event_ingest WHERE event_id=?',(eid,)).fetchone():return False
    wid=p.get('work_id')
    if kind=='WORK_CREATE':
        c.execute('INSERT OR IGNORE INTO clay_work_items(work_id,goal_ref,origin_class,created_by,created_at) VALUES(?,?,?,?,?)',(wid,p.get('goal_ref','FRANK_V0_1_ANDREAS_PC'),p.get('origin_class','DERIVED'),actor,ts))
        c.execute('''INSERT OR IGNORE INTO clay_work_spec_revisions(
          work_id,spec_rev,parent_rev,title,work_clay,reason_clay,completion_clay,evidence_need_clay,executor_policy_clay,required_capabilities_clay,write_scope_clay,dependency_clay,invalidation_clay,base_priority,expected_impact,urgency,information_gain,status,source_ref,created_by,created_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(wid,1,None,p['title'],J(p.get('work_clay',{})),J(p.get('reason_clay',{})),J(p.get('completion_clay',{})),J(p.get('evidence_need',[])),J(p.get('executor_policy',{})),J(p.get('required_capabilities',[])),J(p.get('write_scope',[])),J(p.get('dependencies',[])),J(p.get('invalidators',[])),float(p.get('base_priority',.5)),float(p.get('expected_impact',.5)),float(p.get('urgency',0)),float(p.get('information_gain',0)),p.get('status','READY'),source_ref,actor,ts))
    elif kind in ('WORK_REVISE','WORK_CANCEL','WORK_DEFER'):
        prev=c.execute('SELECT * FROM v_clay_current_work_specs WHERE work_id=?',(wid,)).fetchone()
        if not prev:return False
        rev=int(prev['spec_rev'])+1;status=('CANCELLED' if kind=='WORK_CANCEL' else 'DEFERRED' if kind=='WORK_DEFER' else p.get('status','READY'))
        def old(col,default):return P(prev[col],default)
        c.execute('''INSERT INTO clay_work_spec_revisions(
          work_id,spec_rev,parent_rev,title,work_clay,reason_clay,completion_clay,evidence_need_clay,executor_policy_clay,required_capabilities_clay,write_scope_clay,dependency_clay,invalidation_clay,base_priority,expected_impact,urgency,information_gain,status,source_ref,created_by,created_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(wid,rev,prev['spec_rev'],p.get('title',prev['title']),J(p.get('work_clay',old('work_clay',{}))),J(p.get('reason_clay',{'event':kind})),J(p.get('completion_clay',old('completion_clay',{}))),J(p.get('evidence_need',old('evidence_need_clay',[]))),J(p.get('executor_policy',old('executor_policy_clay',{}))),J(p.get('required_capabilities',old('required_capabilities_clay',[]))),J(p.get('write_scope',old('write_scope_clay',[]))),J(p.get('dependencies',old('dependency_clay',[]))),J(p.get('invalidators',old('invalidation_clay',[]))),float(p.get('base_priority',prev['base_priority'])),float(p.get('expected_impact',prev['expected_impact'])),float(p.get('urgency',prev['urgency'])),float(p.get('information_gain',prev['information_gain'])),status,source_ref,actor,ts))
    elif kind=='WORK_EXECUTION_RECEIPT':
        c.execute('''INSERT OR IGNORE INTO clay_execution_receipts(
          execution_receipt_id,work_id,spec_rev,executor_node,executor_class,machine_ref,action_clay,observed_effect_clay,verification_clay,evidence_refs_clay,truth_class,success,created_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(p.get('execution_receipt_id',uid('exec')),wid,p.get('spec_rev'),actor,p.get('executor_class','UNKNOWN'),p.get('machine_ref'),J(p.get('action',{})),J(p.get('observed_effect',{})),J(p.get('verification',{})),J(p.get('evidence_refs',[])),p.get('truth_class','UNVERIFIED'),1 if p.get('success') else 0,ts))
        if p.get('success') and p.get('complete'):c.execute('UPDATE clay_work_items SET terminal_status=?,terminal_at=? WHERE work_id=?',('COMPLETE',ts,wid))
    else:return False
    c.execute('INSERT INTO clay_work_event_ingest VALUES(?,?,?,?)',(eid,hashlib.sha256(J(e).encode()).hexdigest(),source_ref,now()));return True

def ingest_remote():
    c=open_db();n=0
    try:
        for path in remote_paths():
            e=remote_event(path)
            if e and apply_event(c,e,f'git:{REMOTE}/{BRANCH}:{path}'):n+=1
        c.commit()
    finally:c.close()
    return n

def observe_local(actor='claude-code-lead'):
    c=open_db();ts=now();host=platform.node() or 'local';rid=f'host:{host}'
    mem=None
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'):mem=int(line.split()[1])*1024;break
    except Exception:pass
    details={'os':platform.platform(),'machine':platform.machine(),'cpu_count':os.cpu_count(),'memory_bytes':mem,'python':platform.python_version()}
    c.execute('''INSERT INTO clay_system_resource_observations(
      observation_id,resource_id,resource_class,label,host_or_surface,provider,details_clay,authority_clay,availability_state,evidence_class,evidence_ref,observed_at,freshness_seconds,writer_node)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(uid('resobs'),rid,'ANDREAS_OR_CLAY_LOCAL_HOST',host,host,None,J(details),J({'local_execution':True}),'AVAILABLE','VERIFIED_CURRENT_REALITY','runtime:observe_local',ts,300,actor))
    for tool in ('git','python','python3','claude','nvidia-smi','docker'):
        path=shutil.which(tool);state='CAN_NOW' if path else 'CANNOT_NOW';confidence=1.0 if path else .95
        c.execute('''INSERT INTO clay_capability_observations(
          observation_id,capability_instance_id,resource_id,capability_key,capability_class,state,modalities_clay,execution_scope_clay,authority_scope_clay,cost_clay,latency_clay,privacy_clay,trials,successes,confidence,evidence_clay,observed_at,freshness_seconds,writer_node)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(uid('capobs'),f'{rid}:tool:{tool}',rid,f'tool:{tool}','LOCAL_TOOL',state,J(['text']),J({'path':path}),J({'local':True}),J({}),J({}),J({'host_local':True}),0,0,confidence,J({'which':path}),ts,300,actor))
    c.commit();c.close();return details

def recompute(actor='clay-scheduler'):
    c=open_db();out=[]
    try:
        caps=[dict(x) for x in c.execute('SELECT capability_key,effective_state,resource_id,confidence FROM v_clay_current_capabilities')];by={}
        for x in caps:by.setdefault(x['capability_key'],[]).append(x)
        for s in c.execute("SELECT * FROM v_clay_current_work_specs WHERE status NOT IN ('CANCELLED','SUPERSEDED')"):
            req=P(s['required_capabilities_clay'],[]) or [];missing=[r for r in req if not any(x['effective_state'] in ('CAN_NOW','CAN_DELEGATE') for x in by.get(r,[]))]
            capfit=1.0 if not req else (len(req)-len(missing))/len(req);avail=1.0 if not missing else 0.0;elig='ELIGIBLE' if s['status']=='READY' and not missing else 'BLOCKED' if missing else 'DEFER'
            policy=P(s['executor_policy_clay'],{}) or {};selected=policy.get('prefer') if isinstance(policy,dict) else None
            if not selected and req:
                good=[x['resource_id'] for r in req for x in by.get(r,[]) if x['effective_state']=='CAN_NOW'];selected=good[0] if good else None
            goalfit=1.0 if s['goal_ref']=='FRANK_V0_1_ANDREAS_PC' else .7;dep=0.0;collision=.05;cost=0.0;stale=0.0
            score=(goalfit+s['expected_impact']+s['urgency']+s['information_gain']+capfit+avail+dep-collision-cost-stale)/7.0
            c.execute('''INSERT INTO clay_work_scheduler_receipts(
              scheduler_receipt_id,work_id,spec_rev,scheduler_node,goal_fit,capability_fit,availability_fit,dependency_pressure,urgency,information_gain,collision_risk,cost_pressure,stale_pressure,priority_score,eligibility_state,selected_executor,possibility_snapshot_clay,reason_clay,created_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(uid('sched'),s['work_id'],s['spec_rev'],actor,goalfit,capfit,avail,dep,s['urgency'],s['information_gain'],collision,cost,stale,score,elig,selected,J(caps[:80]),J({'required':req,'missing':missing,'spec_status':s['status']}),now()))
            out.append({'work_id':s['work_id'],'priority':round(score,4),'state':elig,'executor':selected,'missing':missing})
        c.commit();return out
    finally:c.close()

def sync(observe=False):
    n=ingest_remote();local=observe_local() if observe else None;return {'ingested':n,'local':local,'queue':recompute()}
def queue(limit=20):
    c=open_db()
    try:return [dict(x) for x in c.execute('SELECT * FROM v_clay_dynamic_work_queue LIMIT ?',(limit,))]
    finally:c.close()

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('init');sp.add_parser('ingest');s=sp.add_parser('sync');s.add_argument('--observe-local',action='store_true');sp.add_parser('observe-local');sp.add_parser('recompute');q=sp.add_parser('queue');q.add_argument('--limit',type=int,default=20);a=ap.parse_args()
    if a.cmd=='init':open_db().close();print('{}')
    elif a.cmd=='ingest':print(J({'ingested':ingest_remote()}))
    elif a.cmd=='sync':print(json.dumps(sync(a.observe_local),ensure_ascii=False,default=str))
    elif a.cmd=='observe-local':print(J(observe_local()))
    elif a.cmd=='recompute':print(json.dumps(recompute(),ensure_ascii=False))
    else:print(json.dumps(queue(a.limit),ensure_ascii=False,default=str))
if __name__=='__main__':main()
