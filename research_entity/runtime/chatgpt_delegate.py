#!/usr/bin/env python3
"""RAE Claude->ChatGPT work-package bridge."""
from __future__ import annotations
import argparse, hashlib, json, sqlite3, time, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'research_entity'/'state'
REQ=STATE/'requests'/'chatgpt'
REC=STATE/'receipts'/'chatgpt'
MIG=ROOT/'research_entity'/'runtime'/'RAE_UNIFIEDDB_V8_CHATGPT_DELEGATION.sql'
DB=STATE/'RAE_UNIFIED.sqlite'
PROJECT='clay science pipeline'

def now(): return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def uid(prefix): return f"{prefix}:{uuid.uuid4().hex}"
def j(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def open_db():
    STATE.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;c.execute('PRAGMA busy_timeout=10000');c.execute('PRAGMA foreign_keys=ON')
    if MIG.exists(): c.executescript(MIG.read_text(encoding='utf-8'))
    return c

def create_package(args):
    REQ.mkdir(parents=True,exist_ok=True)
    pid=uid('rae-chatgpt-work');short=hashlib.sha256(pid.encode()).hexdigest()[:10];trigger=f'raejob-{short}'
    row={'schema_version':'1.0','package_id':pid,'trigger_token':trigger,'project_target':PROJECT,'requester_node':args.requester,'task_class':args.task_class,'goal_clay':args.goal,'context_refs':args.context_ref or [],'capability_plan':args.capability or [],'required_outputs':args.output or [],'write_scope':args.write_scope or [],'completion_test_clay':args.completion_test,'privacy_class':args.privacy,'priority':args.priority,'status':'READY','created_at':now(),'return_path':f'research_entity/state/receipts/chatgpt/{pid}.json'}
    p=REQ/f'{pid}.json';p.write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
    c=open_db()
    try:
      c.execute('''INSERT OR REPLACE INTO rae_chatgpt_work_packages(package_id,trigger_token,project_target,requester_node,task_class,goal_clay,context_refs_clay,capability_plan_clay,required_outputs_clay,write_scope_clay,completion_test_clay,privacy_class,priority,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(pid,trigger,PROJECT,args.requester,args.task_class,args.goal,j(args.context_ref or []),j(args.capability or []),j(args.output or []),j(args.write_scope or []),args.completion_test,args.privacy,args.priority,'READY',row['created_at']))
      c.execute('INSERT INTO rae_chatgpt_delegation_receipts VALUES(?,?,?,?,?)',(uid('rae-delegation-receipt'),pid,'PACKAGE_CREATED',j({'request_ref':str(p.relative_to(ROOT)),'trigger':trigger}),args.requester,now()));c.commit()
    finally:c.close()
    print(json.dumps({'package_id':pid,'trigger_token':trigger,'request_ref':str(p.relative_to(ROOT)),'human_instruction':f'Projekt clay science pipeline öffnen und exakt eingeben: {trigger}'},ensure_ascii=False))

def ingest():
    REC.mkdir(parents=True,exist_ok=True);c=open_db();out=[]
    try:
      for p in sorted(REC.glob('*.json')):
        try:r=json.loads(p.read_text(encoding='utf-8'))
        except Exception:continue
        pid=r.get('package_id');rid=r.get('result_id') or uid('rae-chatgpt-result')
        if not pid:continue
        if c.execute('SELECT 1 FROM rae_chatgpt_work_results WHERE result_id=?',(rid,)).fetchone():continue
        if not c.execute('SELECT 1 FROM rae_chatgpt_work_packages WHERE package_id=?',(pid,)).fetchone():continue
        c.execute('''INSERT INTO rae_chatgpt_work_results(result_id,package_id,executor_node,provider,result_clay,evidence_refs_clay,artifact_refs_clay,web_refs_clay,media_refs_clay,unresolved_clay,completion_clay,verification_clay,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(rid,pid,r.get('executor_node','chatgpt-remote'),'ChatGPT',j(r.get('result_clay',{})),j(r.get('evidence_refs',[])),j(r.get('artifact_refs',[])),j(r.get('web_refs',[])),j(r.get('media_refs',[])),j(r.get('unresolved_clay',{})),j(r.get('completion_clay',{})),j(r.get('verification_clay',{})),r.get('status','POSTED'),r.get('created_at') or now()))
        c.execute("UPDATE rae_chatgpt_work_packages SET status='INGESTED',result_ref=?,result_posted_at=COALESCE(result_posted_at,?),ingested_at=? WHERE package_id=?",(str(p.relative_to(ROOT)),r.get('created_at') or now(),now(),pid))
        c.execute('INSERT INTO rae_chatgpt_delegation_receipts VALUES(?,?,?,?,?)',(uid('rae-delegation-receipt'),pid,'RESULT_INGESTED',j({'result_id':rid,'receipt_ref':str(p.relative_to(ROOT))}),'SYSTEM',now()));out.append({'package_id':pid,'result_id':rid,'receipt_ref':str(p.relative_to(ROOT))})
      c.commit()
    finally:c.close()
    print(json.dumps({'ingested':out},ensure_ascii=False))

def pending(limit=8):
    c=open_db()
    try:rows=[dict(x) for x in c.execute("SELECT package_id,trigger_token,task_class,goal_clay,priority,status,created_at FROM rae_chatgpt_work_packages WHERE status IN ('READY','CLAIMED','RUNNING','RESULT_POSTED','INGESTED') ORDER BY priority DESC,created_at LIMIT ?",(limit,))]
    finally:c.close()
    print(json.dumps(rows,ensure_ascii=False))

def consume(pid):
    c=open_db()
    try:c.execute("UPDATE rae_chatgpt_work_packages SET status='CONSUMED',consumed_at=? WHERE package_id=? AND status='INGESTED'",(now(),pid));c.commit()
    finally:c.close()

if __name__=='__main__':
  ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
  c=sub.add_parser('create');c.add_argument('--requester',default='claude-code-lead');c.add_argument('--task-class',default='RESEARCH');c.add_argument('--goal',required=True);c.add_argument('--context-ref',action='append');c.add_argument('--capability',action='append');c.add_argument('--output',action='append');c.add_argument('--write-scope',action='append');c.add_argument('--completion-test',required=True);c.add_argument('--privacy',default='PROJECT_INTERNAL_MINIMIZED');c.add_argument('--priority',type=int,default=50)
  sub.add_parser('ingest');p=sub.add_parser('pending');p.add_argument('--limit',type=int,default=8);x=sub.add_parser('consume');x.add_argument('package_id')
  a=ap.parse_args();{'create':create_package,'ingest':lambda _:ingest(),'pending':lambda _:pending(a.limit),'consume':lambda _:consume(a.package_id)}[a.cmd](a)
