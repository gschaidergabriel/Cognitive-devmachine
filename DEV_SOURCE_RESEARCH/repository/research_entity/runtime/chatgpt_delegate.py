#!/usr/bin/env python3
"""RAE Claude->ChatGPT work-package bridge.

Cross-provider transport uses repo semantic files. Requests publish to origin/main through a
temporary Git index, leaving Claude worktree/staging untouched. Results are read from the
remote branch with git-show and ingested directly into local RAE UnifiedDB.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sqlite3, subprocess, tempfile, time, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'research_entity'/'state'
REQ=STATE/'requests'/'chatgpt'
REC=STATE/'receipts'/'chatgpt'
MIG=ROOT/'research_entity'/'runtime'/'RAE_UNIFIEDDB_V8_CHATGPT_DELEGATION.sql'
DB=STATE/'RAE_UNIFIED.sqlite'
PROJECT='clay science pipeline'
REMOTE='origin';BRANCH='main'

def now(): return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def uid(prefix): return f"{prefix}:{uuid.uuid4().hex}"
def j(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha_bytes(b:bytes): return hashlib.sha256(b).hexdigest()
def git(*args,env=None,input_text=None,timeout=30):
    e=(env or os.environ.copy());e.setdefault('GIT_TERMINAL_PROMPT','0')
    return subprocess.run(['git',*args],cwd=ROOT,text=True,input=input_text,capture_output=True,timeout=timeout,env=e)
def open_db():
    STATE.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;c.execute('PRAGMA busy_timeout=10000');c.execute('PRAGMA foreign_keys=ON')
    if MIG.exists(): c.executescript(MIG.read_text(encoding='utf-8'))
    return c

def publish_file(path:Path,message:str)->dict:
    rel=path.relative_to(ROOT).as_posix();last='unknown'
    for attempt in range(1,4):
        f=git('fetch','--quiet',REMOTE,BRANCH,timeout=45)
        if f.returncode!=0:return {'status':'PUBLISH_FAILED','reason':(f.stderr or f.stdout)[-400:]}
        b=git('hash-object','-w','--',str(path))
        if b.returncode!=0:return {'status':'PUBLISH_FAILED','reason':(b.stderr or b.stdout)[-400:]}
        blob=b.stdout.strip();fd,idx=tempfile.mkstemp(prefix='rae-chatgpt-index-');os.close(fd);Path(idx).unlink(missing_ok=True)
        env=os.environ.copy();env.update({'GIT_INDEX_FILE':idx,'GIT_AUTHOR_NAME':'RAE ChatGPT Bridge','GIT_AUTHOR_EMAIL':'bridge@rae.local','GIT_COMMITTER_NAME':'RAE ChatGPT Bridge','GIT_COMMITTER_EMAIL':'bridge@rae.local','GIT_TERMINAL_PROMPT':'0'})
        try:
            if git('read-tree',f'{REMOTE}/{BRANCH}',env=env).returncode!=0:continue
            u=git('update-index','--add','--cacheinfo',f'100644,{blob},{rel}',env=env)
            if u.returncode!=0:last=(u.stderr or u.stdout)[-400:];continue
            t=git('write-tree',env=env);tree=t.stdout.strip()
            if t.returncode!=0:last=(t.stderr or t.stdout)[-400:];continue
            cc=git('commit-tree',tree,'-p',f'{REMOTE}/{BRANCH}',env=env,input_text=message+'\n')
            if cc.returncode!=0:last=(cc.stderr or cc.stdout)[-400:];continue
            commit=cc.stdout.strip();p=git('push','--quiet',REMOTE,f'{commit}:refs/heads/{BRANCH}',env=env,timeout=45)
            if p.returncode==0:return {'status':'PUBLISHED','commit':commit,'ref':f'{REMOTE}/{BRANCH}:{rel}','attempt':attempt}
            last=(p.stderr or p.stdout)[-400:]
        finally:Path(idx).unlink(missing_ok=True)
    return {'status':'PUBLISH_FAILED','reason':last}
def fetch_remote():
    try:return git('fetch','--quiet',REMOTE,BRANCH,timeout=45).returncode==0
    except Exception:return False
def remote_bytes(rel:str):
    p=git('show',f'{REMOTE}/{BRANCH}:{rel}',timeout=20)
    return p.stdout.encode('utf-8') if p.returncode==0 else None

def record_event(c,pid,event,payload,node='SYSTEM'):
    c.execute('INSERT INTO rae_chatgpt_delegation_receipts VALUES(?,?,?,?,?)',(uid('rae-delegation-receipt'),pid,event,j(payload),node,now()))

def create_package(args):
    REQ.mkdir(parents=True,exist_ok=True)
    pid=f'raejob-{uuid.uuid4().hex[:12]}';trigger=pid
    row={'schema_version':'1.2','package_id':pid,'trigger_token':trigger,'project_target':PROJECT,'requester_node':args.requester,'task_class':args.task_class,'goal_clay':args.goal,'context_refs':args.context_ref or [],'capability_plan':args.capability or [],'required_outputs':args.output or [],'write_scope':args.write_scope or [],'completion_test_clay':args.completion_test,'privacy_class':args.privacy,'priority':args.priority,'status':'READY','created_at':now(),'request_path':f'research_entity/state/requests/chatgpt/{trigger}.json','return_path':f'research_entity/state/receipts/chatgpt/{trigger}.json'}
    p=REQ/f'{trigger}.json';p.write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
    c=open_db()
    try:
      c.execute('''INSERT OR REPLACE INTO rae_chatgpt_work_packages(package_id,trigger_token,project_target,requester_node,task_class,goal_clay,context_refs_clay,capability_plan_clay,required_outputs_clay,write_scope_clay,completion_test_clay,privacy_class,priority,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(pid,trigger,PROJECT,args.requester,args.task_class,args.goal,j(args.context_ref or []),j(args.capability or []),j(args.output or []),j(args.write_scope or []),args.completion_test,args.privacy,args.priority,'READY',row['created_at']))
      record_event(c,pid,'PACKAGE_CREATED',{'request_ref':str(p.relative_to(ROOT)),'trigger':trigger},args.requester);c.commit()
    finally:c.close()
    pub=publish_file(p,f'Publish ChatGPT work package {pid}')
    c=open_db()
    try:record_event(c,pid,'PACKAGE_PUBLISHED' if pub['status']=='PUBLISHED' else 'PACKAGE_PUBLISH_FAILED',pub,args.requester);c.commit()
    finally:c.close()
    if pub['status']=='PUBLISHED':p.unlink(missing_ok=True)
    instruction=f'Projekt clay science pipeline öffnen und exakt eingeben: {trigger}' if pub['status']=='PUBLISHED' else None
    print(json.dumps({'package_id':pid,'trigger_token':trigger,'request_ref':row['request_path'],'publish':pub,'human_instruction':instruction},ensure_ascii=False))

def ingest_result(c,pid,r,receipt_ref,raw:bytes):
    rid=r.get('result_id') or f"rae-chatgpt-result:{sha_bytes(raw)[:24]}"
    if not c.execute('SELECT 1 FROM rae_chatgpt_work_packages WHERE package_id=?',(pid,)).fetchone():return None
    if c.execute('SELECT 1 FROM rae_chatgpt_work_results WHERE result_id=?',(rid,)).fetchone():return None
    c.execute('''INSERT INTO rae_chatgpt_work_results(result_id,package_id,executor_node,provider,result_clay,evidence_refs_clay,artifact_refs_clay,web_refs_clay,media_refs_clay,unresolved_clay,completion_clay,verification_clay,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(rid,pid,r.get('executor_node','chatgpt-remote'),'ChatGPT',j(r.get('result_clay',{})),j(r.get('evidence_refs',[])),j(r.get('artifact_refs',[])),j(r.get('web_refs',[])),j(r.get('media_refs',[])),j(r.get('unresolved_clay',{})),j(r.get('completion_clay',{})),j(r.get('verification_clay',{})),r.get('status','POSTED'),r.get('created_at') or now()))
    c.execute("UPDATE rae_chatgpt_work_packages SET status='INGESTED',result_ref=?,result_posted_at=COALESCE(result_posted_at,?),ingested_at=? WHERE package_id=?",(receipt_ref,r.get('created_at') or now(),now(),pid))
    record_event(c,pid,'RESULT_INGESTED',{'result_id':rid,'receipt_ref':receipt_ref});return {'package_id':pid,'result_id':rid,'receipt_ref':receipt_ref}

def ingest():
    REC.mkdir(parents=True,exist_ok=True);c=open_db();out=[]
    try:
      for p in sorted(REC.glob('raejob-*.json')):
        try:raw=p.read_bytes();r=json.loads(raw);pid=r.get('package_id') or p.stem
        except Exception:continue
        x=ingest_result(c,pid,r,str(p.relative_to(ROOT)),raw)
        if x:out.append(x)
      if fetch_remote():
        pending=[x[0] for x in c.execute("SELECT package_id FROM rae_chatgpt_work_packages WHERE status IN ('READY','CLAIMED','RUNNING','RESULT_POSTED')")]
        for pid in pending:
          rel=f'research_entity/state/receipts/chatgpt/{pid}.json';raw=remote_bytes(rel)
          if not raw:continue
          try:r=json.loads(raw)
          except Exception:continue
          x=ingest_result(c,pid,r,f'git:{REMOTE}/{BRANCH}:{rel}',raw)
          if x:out.append(x)
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
    try:c.execute("UPDATE rae_chatgpt_work_packages SET status='CONSUMED',consumed_at=? WHERE package_id=? AND status='INGESTED'",(now(),pid));record_event(c,pid,'RESULT_CONSUMED',{},'claude-code-lead');c.commit()
    finally:c.close()

if __name__=='__main__':
  ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
  c=sub.add_parser('create');c.add_argument('--requester',default='claude-code-lead');c.add_argument('--task-class',default='RESEARCH');c.add_argument('--goal',required=True);c.add_argument('--context-ref',action='append');c.add_argument('--capability',action='append');c.add_argument('--output',action='append');c.add_argument('--write-scope',action='append');c.add_argument('--completion-test',required=True);c.add_argument('--privacy',default='PROJECT_INTERNAL_MINIMIZED');c.add_argument('--priority',type=int,default=50)
  sub.add_parser('ingest');p=sub.add_parser('pending');p.add_argument('--limit',type=int,default=8);x=sub.add_parser('consume');x.add_argument('package_id')
  a=ap.parse_args();{'create':create_package,'ingest':lambda _:ingest(),'pending':lambda _:pending(a.limit),'consume':lambda _:consume(a.package_id)}[a.cmd](a)
