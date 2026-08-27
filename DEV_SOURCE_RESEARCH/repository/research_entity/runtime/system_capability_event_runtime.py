#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,sqlite3,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DB=ROOT/'research_entity/state/RAE_UNIFIED.sqlite';SCHEMA=ROOT/'research_entity/runtime/RAE_UNIFIEDDB_V9_DYNAMIC_WORK_FABRIC.sql';REMOTE='origin';BRANCH='main';PREFIX='research_entity/state/system/events/'
def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def uid(p):return f'{p}:{uuid.uuid4().hex}'
def J(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def db():
    c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;c.execute('PRAGMA busy_timeout=10000');c.executescript(SCHEMA.read_text());c.execute('CREATE TABLE IF NOT EXISTS clay_system_event_ingest(event_id TEXT PRIMARY KEY,event_hash TEXT NOT NULL,source_ref TEXT,ingested_at TEXT NOT NULL)');c.commit();return c
def git(*a,timeout=40):
    e=os.environ.copy();e.setdefault('GIT_TERMINAL_PROMPT','0');return subprocess.run(['git',*a],cwd=ROOT,text=True,capture_output=True,timeout=timeout,env=e)
def paths():
    if git('fetch','--quiet',REMOTE,BRANCH,timeout=50).returncode:return []
    p=git('ls-tree','-r','--name-only',f'{REMOTE}/{BRANCH}',PREFIX.rstrip('/'));return [x for x in p.stdout.splitlines() if x.endswith('.json')] if p.returncode==0 else []
def read(path):
    p=git('show',f'{REMOTE}/{BRANCH}:{path}')
    if p.returncode:return None
    try:return json.loads(p.stdout)
    except Exception:return None
def apply(c,e,path):
    eid=e.get('event_id');kind=e.get('kind');p=e.get('payload') or {};actor=e.get('actor','UNKNOWN');ts=e.get('created_at',now())
    if not eid or c.execute('SELECT 1 FROM clay_system_event_ingest WHERE event_id=?',(eid,)).fetchone():return False
    if kind=='RESOURCE_OBSERVATION':
        c.execute('''INSERT INTO clay_system_resource_observations(observation_id,resource_id,resource_class,label,host_or_surface,provider,details_clay,authority_clay,availability_state,evidence_class,evidence_ref,observed_at,freshness_seconds,writer_node) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(uid('resobs'),p['resource_id'],p['resource_class'],p['label'],p.get('host_or_surface'),p.get('provider'),J(p.get('details',{})),J(p.get('authority',{})),p.get('availability_state','UNKNOWN'),p.get('evidence_class','EXTERNAL_EVIDENCE'),p.get('evidence_ref',path),ts,int(p.get('freshness_seconds',900)),actor))
    elif kind=='CAPABILITY_OBSERVATION':
        c.execute('''INSERT INTO clay_capability_observations(observation_id,capability_instance_id,resource_id,capability_key,capability_class,state,modalities_clay,execution_scope_clay,authority_scope_clay,cost_clay,latency_clay,privacy_clay,trials,successes,confidence,evidence_clay,observed_at,freshness_seconds,writer_node) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(uid('capobs'),p['capability_instance_id'],p['resource_id'],p['capability_key'],p['capability_class'],p.get('state','UNKNOWN'),J(p.get('modalities',[])),J(p.get('execution_scope',{})),J(p.get('authority_scope',{})),J(p.get('cost',{})),J(p.get('latency',{})),J(p.get('privacy',{})),int(p.get('trials',0)),int(p.get('successes',0)),float(p.get('confidence',0.5)),J(p.get('evidence',{})),ts,int(p.get('freshness_seconds',900)),actor))
    else:return False
    c.execute('INSERT INTO clay_system_event_ingest VALUES(?,?,?,?)',(eid,hashlib.sha256(J(e).encode()).hexdigest(),f'git:{REMOTE}/{BRANCH}:{path}',now()));return True
def ingest():
    c=db();n=0
    try:
        for path in paths():
            e=read(path)
            if e and apply(c,e,path):n+=1
        c.commit();return n
    finally:c.close()
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('cmd',choices=['ingest']);a=ap.parse_args();print(json.dumps({'ingested':ingest()}))
