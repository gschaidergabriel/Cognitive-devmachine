#!/usr/bin/env python3
"""Publish safe compact derived work/capability projections for remote Clay organs."""
from __future__ import annotations
import hashlib,json,sqlite3,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research_entity/runtime'))
from chatgpt_delegate import publish_file,fetch_remote,remote_bytes

DB=ROOT/'research_entity/state/RAE_UNIFIED.sqlite'
OUT=ROOT/'research_entity/state/work/projections'
DENY=('secret','token','password','passwd','credential','api_key','apikey','private_key','cookie','authorization')

def scrub(x):
    if isinstance(x,dict):return {k:('[REDACTED]' if any(d in k.lower() for d in DENY) else scrub(v)) for k,v in x.items()}
    if isinstance(x,list):return [scrub(v) for v in x]
    return x

def parse(v):
    if not isinstance(v,str):return v
    try:return scrub(json.loads(v))
    except Exception:return v[:500]
def rows(c,sql):return [dict(r) for r in c.execute(sql)]
def content(module,data):
    safe=scrub(data);payload=json.dumps(safe,ensure_ascii=False,sort_keys=True,separators=(',',':'));h=hashlib.sha256(payload.encode()).hexdigest()
    return f'module {module}\nsource_hash "{h}"\nderived true\nauthority false\ndata {payload}\n'
def publish(path,txt):
    rel=path.relative_to(ROOT).as_posix();fetch_remote();old=remote_bytes(rel)
    if old is not None and old.decode('utf-8','replace')==txt:return {'status':'UNCHANGED','ref':rel}
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(txt,encoding='utf-8');r=publish_file(path,f'Update Clay derived projection {path.name}')
    if r.get('status')=='PUBLISHED':path.unlink(missing_ok=True)
    return r

def main():
    if not DB.exists():print(json.dumps({'status':'NO_DB'}));return
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
    try:
        w=rows(c,"SELECT work_id,goal_ref,spec_rev,title,work_clay,completion_clay,required_capabilities_clay,executor_policy_clay,priority_score,eligibility_state,selected_executor,reason_clay,spec_created_at,scheduled_at FROM v_clay_dynamic_work_queue LIMIT 40")
        p=rows(c,"SELECT resource_id,resource_class,label,host_or_surface,provider,details_clay,authority_clay,effective_availability,evidence_class,evidence_ref,resource_observed_at,capability_instance_id,capability_key,capability_class,capability_state,modalities_clay,execution_scope_clay,authority_scope_clay,cost_clay,latency_clay,privacy_clay,trials,successes,confidence,evidence_clay,capability_observed_at FROM v_clay_system_possibility_table LIMIT 200")
    finally:c.close()
    for r in w:
        for k in ('work_clay','completion_clay','required_capabilities_clay','executor_policy_clay','reason_clay'):r[k]=parse(r.get(k))
    for r in p:
        for k in ('details_clay','authority_clay','modalities_clay','execution_scope_clay','authority_scope_clay','cost_clay','latency_clay','privacy_clay','evidence_clay'):r[k]=parse(r.get(k))
    OUT.mkdir(parents=True,exist_ok=True)
    a=publish(OUT/'CURRENT_DYNAMIC_WORK.clay',content('clay.projection.current_dynamic_work',{'goal':'Frank v0.1 voll lauffähig auf Andreas PC','rows':w}))
    b=publish(OUT/'CURRENT_SYSTEM_POSSIBILITY.clay',content('clay.projection.current_system_possibility',{'rows':p}))
    print(json.dumps({'work':a,'possibility':b},ensure_ascii=False))
if __name__=='__main__':main()
