#!/usr/bin/env python3
"""Clay-owned pull ingest for Frank bug exports.

The process reads Frank's export surface only. It never writes the Frank repo.
Each valid bug becomes an idempotent Clay UnifiedDB record and a READY dynamic
research work item. ``--watch`` provides a lightweight Ubuntu-local continuous
pull loop without granting Frank any Clay write authority.
"""
from __future__ import annotations
import argparse,hashlib,json,sqlite3,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DB=ROOT/'research_entity/state/RAE_UNIFIED.sqlite'
SCHEMA9=ROOT/'research_entity/runtime/RAE_UNIFIEDDB_V9_DYNAMIC_WORK_FABRIC.sql'
SCHEMA10=ROOT/'research_entity/runtime/RAE_UNIFIEDDB_V10_FRANK_BUG_FEEDBACK.sql'
FRANK_REPO='gschaidergabriel/frankv0.1'

def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def J(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def canonical_bytes(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def open_db():
    DB.parent.mkdir(parents=True,exist_ok=True);c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=10000');c.executescript(SCHEMA9.read_text());c.executescript(SCHEMA10.read_text());c.commit();return c

def verify_payload(p):
    claimed=p.get('payload_hash');q=dict(p);q.pop('payload_hash',None);actual=hashlib.sha256(canonical_bytes(q)).hexdigest();return bool(claimed and claimed==actual),actual

def ingest_one(c,path):
    try:p=json.loads(path.read_text(encoding='utf-8'))
    except Exception:return {'path':str(path),'state':'INVALID'}
    ok,actual=verify_payload(p)
    if not ok:return {'path':str(path),'state':'REJECTED_HASH','actual':actual}
    if p.get('kind')!='FRANK_RESEARCH_BUG_REPORT' or p.get('trigger')!='bug':return {'path':str(path),'state':'INVALID'}
    bug=p['bug_id'];pair=p.get('captured_pair') or {};prov=p.get('provenance') or {};rel='exports/clay_pull/bugs/'+path.name;ts=now();work_id='work:frank-bug:'+bug.split(':',1)[-1]
    if c.execute('SELECT 1 FROM clay_frank_bug_reports WHERE bug_id=?',(bug,)).fetchone():return {'bug_id':bug,'state':'DUPLICATE','work_id':work_id}
    c.execute('''INSERT INTO clay_frank_bug_reports(bug_id,source_repository,source_path,payload_hash,previous_andreas_input,previous_frank_output,session_ref,source_cycle_id,source_frank_epoch,source_frank_repo_head,redaction_applied,research_state,ingested_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,'NEW',?)''',(bug,FRANK_REPO,rel,p['payload_hash'],pair.get('previous_andreas_input',''),pair.get('previous_frank_output',''),prov.get('session_ref'),prov.get('source_cycle_id'),prov.get('semantic_epoch'),prov.get('source_repo_head'),1 if p.get('redaction_applied') else 0,ts))
    c.execute('INSERT OR IGNORE INTO clay_work_items(work_id,goal_ref,origin_class,created_by,created_at) VALUES(?,?,?,?,?)',(work_id,'FRANK_V0_1_ANDREAS_PC','FRANK_EXPLICIT_BUG_FEEDBACK','frank-bug-ingest',ts))
    c.execute('''INSERT OR IGNORE INTO clay_work_spec_revisions(work_id,spec_rev,parent_rev,title,work_clay,reason_clay,completion_clay,evidence_need_clay,executor_policy_clay,required_capabilities_clay,write_scope_clay,dependency_clay,invalidation_clay,base_priority,expected_impact,urgency,information_gain,status,source_ref,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
        work_id,1,None,'Investigate Frank bug '+bug,
        J({'bug_id':bug,'task':'Reproduce, causal-localize, regressionize and propose/implement Research-Entity-owned repair if evidence supports it.','andreas_input':pair.get('previous_andreas_input',''),'frank_output':pair.get('previous_frank_output','')}),
        J({'origin':'ANDREAS_EXPLICIT_BUG_TRIGGER','report_only_from_frank':True}),
        J({'done_when':['bug reproduced or classified non-reproducible','cause/evidence recorded','affected tests added','repair decision and rollback recorded']}),
        J([f'{FRANK_REPO}:{rel}']),
        J({'prefer':'best-current-Clay-organ','frank_self_harness_authority':'PROPOSAL_ONLY'}),
        J([]),J(['research_entity/**']),J([]),J(['source payload hash mismatch','newer report supersedes exact same pair']),
        0.98,0.95,0.90,0.95,'READY',f'{FRANK_REPO}:{rel}','frank-bug-ingest',ts))
    receipt='bug-ingest:'+hashlib.sha256((bug+'|'+p['payload_hash']).encode()).hexdigest()[:24]
    c.execute("INSERT OR IGNORE INTO clay_frank_bug_ingest_receipts(receipt_id,bug_id,source_path,source_payload_hash,work_id,ingest_state,evidence_clay,created_at) VALUES(?,?,?,?,?,'INGESTED',?,?)",(receipt,bug,rel,p['payload_hash'],work_id,J({'hash_verified':True,'frank_repo_write':False}),ts))
    return {'bug_id':bug,'state':'INGESTED','work_id':work_id}

def ingest(frank_root):
    root=frank_root.resolve();src=root/'exports/clay_pull/bugs';c=open_db();out=[]
    try:
        if src.is_dir():
            for p in sorted(src.glob('*.json')):out.append(ingest_one(c,p))
        c.commit()
    finally:c.close()
    return out

def watch(frank_root,interval=1.0):
    while True:
        results=ingest(frank_root)
        fresh=[r for r in results if r.get('state') not in ('DUPLICATE',)]
        if fresh:print(json.dumps({'observed_at':now(),'results':fresh},ensure_ascii=False),flush=True)
        time.sleep(max(0.25,float(interval)))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--frank-root',type=Path,required=True);ap.add_argument('--watch',action='store_true');ap.add_argument('--interval',type=float,default=1.0);a=ap.parse_args()
    if a.watch:watch(a.frank_root,a.interval)
    else:print(json.dumps({'results':ingest(a.frank_root)},ensure_ascii=False))
if __name__=='__main__':main()
