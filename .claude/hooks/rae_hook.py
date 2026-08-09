#!/usr/bin/env python3
"""Clay Claude-Code lifecycle adapter.

One Clay entity. Claude is temporary local execution/research organ. Each substantive
round resolves latest ClayCode/UnifiedDB/ClayGraph, syncs revisioned work, observes real
local capability state, ingests ChatGPT receipts and injects only compact current deltas.
"""
from __future__ import annotations
import hashlib,json,os,pathlib,sqlite3,subprocess,sys,time

ROOT=pathlib.Path(os.environ.get('CLAUDE_PROJECT_DIR',pathlib.Path(__file__).resolve().parents[2])).resolve()
RUNTIME=ROOT/'.rae_runtime';RUNTIME.mkdir(exist_ok=True)
LOG=RUNTIME/'claude_hooks.jsonl'
TRIGGERS=ROOT/'research_entity/global/RESEARCH_TRIGGER_REGISTRY.json'
STATE=ROOT/'research_entity/runtime/claude_state_bridge.py'
STACK=ROOT/'research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay'
DELEGATE=ROOT/'research_entity/runtime/chatgpt_delegate.py'
WORK=ROOT/'research_entity/runtime/dynamic_work_runtime_v2.py'
UDB=ROOT/'research_entity/state/RAE_UNIFIED.sqlite'
CRITICAL=('/research_entity/continuity/research_entity_canonical.json','/research_entity/ledgers/claims.jsonl','/research_entity/ledgers/claim_status_events.jsonl','/research_entity/events/')

def inp():
    try:return json.load(sys.stdin)
    except Exception:return {}
def log(ev,d,**x):
    with LOG.open('a',encoding='utf-8') as f:f.write(json.dumps({'t':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'ev':ev,'sid':d.get('session_id'),**x},ensure_ascii=False,separators=(',',':'))+'\n')
def py(path,*args,timeout=75):
    if not path.exists():return 2,'','missing'
    try:
        p=subprocess.run([sys.executable,str(path),*args],cwd=ROOT,text=True,capture_output=True,timeout=timeout);return p.returncode,p.stdout.strip(),p.stderr.strip()
    except Exception as e:return 3,'',type(e).__name__
def run_rae(*a,timeout=30):
    p=subprocess.run([sys.executable,str(ROOT/'rae.py'),*a],cwd=ROOT,text=True,capture_output=True,timeout=timeout);return p.returncode,p.stdout.strip(),p.stderr.strip()
def bridge(d,prompt=''):
    ev=str(d.get('hook_event_name') or 'PROMPT');sid=str(d.get('session_id') or 'unknown');model=str(d.get('model') or d.get('model_name') or 'claude')
    return py(STATE,'context','--event',ev,'--prompt',prompt,'--session-id',sid,'--model',model,'--mode','compact',timeout=30)
def refresh():py(STATE,'refresh',timeout=25)
def close(d):py(STATE,'close','--session-id',str(d.get('session_id') or 'unknown'),timeout=25)
def reg():
    try:return json.loads(TRIGGERS.read_text())
    except Exception:return {'triggers':{}}
def trig(prompt):
    k=prompt.strip().lower();return k,(reg().get('triggers') or {}).get(k)
def norm(x):return str(x or '').replace('\\','/').lower()
def safe_cmd(c):return ('python rae.py' in c or 'python3 rae.py' in c or './rae.py' in c or ' rae ' in c)
def deny(reason):print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':reason}}))
def emit(ev,ctx,title=None):
    o={'hookEventName':ev,'additionalContext':ctx}
    if title:o['sessionTitle']=title
    print(json.dumps({'hookSpecificOutput':o},ensure_ascii=False,separators=(',',':')))

def stack_marker():
    try:
        raw=STACK.read_bytes();h=hashlib.sha256(raw).hexdigest()[:12];epoch='?'
        for line in raw.decode('utf-8','replace').splitlines():
            if line.strip().startswith('epoch '):epoch=line.strip().split(None,1)[1];break
        return f'STACK{{ptr=@research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay;epoch:{epoch};sha:{h};resolve_each_turn:1}}'
    except Exception:return 'STACK{state:DEGRADED_STALE_STACK}'

def sync_remote_state(observe_local=False):
    # Work first: this can invalidate or reprioritize jobs before Claude sees them.
    py(WORK,'sync',*(['--observe-local'] if observe_local else []),timeout=75)
    py(DELEGATE,'ingest',timeout=75)

def compact_operational():
    try:
        if not UDB.exists():return 'OPS{state=NO_DB}'
        c=sqlite3.connect(UDB,timeout=5);c.execute('PRAGMA busy_timeout=5000')
        work=c.execute("SELECT work_id,spec_rev,title,priority_score,eligibility_state,selected_executor FROM v_clay_dynamic_work_queue LIMIT 6").fetchall()
        poss=c.execute("SELECT resource_id,resource_class,label,effective_availability,capability_key,capability_state,confidence FROM v_clay_system_possibility_table LIMIT 24").fetchall()
        remote=c.execute("SELECT package_id,trigger_token,goal_clay,result_id,result_status FROM v_rae_chatgpt_results_unconsumed ORDER BY created_at DESC LIMIT 3").fetchall();c.close()
        return 'OPS{work='+json.dumps([{'id':r[0],'rev':r[1],'t':r[2],'p':r[3],'s':r[4],'x':r[5]} for r in work],ensure_ascii=False,separators=(',',':'))+';poss='+json.dumps([{'r':r[0],'c':r[1],'a':r[3],'cap':r[4],'cs':r[5],'q':r[6]} for r in poss],ensure_ascii=False,separators=(',',':'))+';remote='+json.dumps([{'p':r[0],'tr':r[1],'g':r[2],'rid':r[3],'s':r[4]} for r in remote],ensure_ascii=False,separators=(',',':'))+'}'
    except Exception:return 'OPS{state=DEGRADED}'

def turn_kernel():
    return (stack_marker()+'\n'
      'TURN{E=Clay;ID=frank-project-global-research-entity;GOAL="Frank v0.1 voll lauffähig auf Andreas PC";THINK=STACK.claycode;TRACE=STACK.claycode;USER=EN_CAVEMAN;'
      'GWT=[rel,impact,unc,novel,info,deliv,recon,use,effect,reentry];'
      'READ=T0(identity+persona+STACK)>T1(dynamic-raejob+registry)>T2(UnifiedDB+ClayGraph+SystemPossibility+DynamicWork)>T3(deep_if_needed);'
      'LOCAL_TRUTH=verified_local_execution_receipt_for_exact_effect;CLAUDE_OPINION!=truth;'
      'WORK=revisioned_dynamic;REVALIDATE_BEFORE_EFFECT=1;CENTER=STACK.research_center;ROOM_COORD=STACK.claycode;'
      'DELEGATE=max_useful(ChatGPT);META_CLAYCODE_RESEARCH=OFF_FOR_CLAUDE;STATUS=CLAY_STATUS;NO_AFTER=1}')

def main():
    d=inp();ev=d.get('hook_event_name','')
    if ev in {'SessionStart','UserPromptSubmit','PreCompact'}:sync_remote_state(observe_local=ev in {'SessionStart','UserPromptSubmit'})
    log(ev,d,stack=stack_marker())
    if ev=='SessionStart':
        rc,c,e=bridge(d,'');src=c if rc==0 else '{state:DEGRADED}'
        emit(ev,turn_kernel()+'\n'+src+'\n'+compact_operational()+'\nPTR=@CLAUDE.md,@research_entity/identity/CLAY_PERSONA.clay,@research_entity/global/CLAY_SYSTEM_WORK_FABRIC.clay','Clay organ');return
    if ev=='UserPromptSubmit':
        prompt=d.get('prompt','')
        if not prompt.strip():return
        k,s=trig(prompt);rc,c,e=bridge(d,prompt);base=c if rc==0 else '{state:DEGRADED}';ops=compact_operational()
        if s:
            purpose=s.get('purpose',k);protocol=s.get('protocol');rr,ro,re=run_rae('run','start','--actor','claude-code-lead','--task',f'trigger:{k} {purpose}','--capture-level','L2')
            emit(ev,turn_kernel()+'\n'+base+'\n'+ops+f'\ntrigger{{id:{k};protocol:@{protocol};run:{ro[:500] if rr==0 else "START_FAIL"}}\nDO=latest ClayCode; execute current dynamic work only after rev/authority revalidation; delegate useful remote work; persist local receipts; reenter G0');return
        br,bo,be=run_rae('boot','--actor','claude-code-lead','--task',prompt,'--max-claims','4','--max-packets','2','--max-chunks','1');task=bo[:1800] if br==0 else 'boot=DEGRADED'
        emit(ev,turn_kernel()+'\n'+base+'\n'+ops+'\nTASK='+task+'\nDO=think ClayCode; map user idea to current possibility space/work; run local discriminating work when appropriate; use raejob delegation when ChatGPT advantage; final caveman English');return
    if ev=='PreToolUse':
        tool=d.get('tool_name','');ti=d.get('tool_input') or {}
        if tool in {'Write','Edit'}:
            p=norm(ti.get('file_path'))
            if any(x in p for x in CRITICAL):deny('Protected Clay canonical/ledger state. Use Clay runtime.');return
        if tool in {'Bash','PowerShell'}:
            c=norm(ti.get('command'))
            if any(x.lstrip('/') in c for x in CRITICAL) and not safe_cmd(c):deny('Protected Clay state. Use rae.py/runtime.');return
        return
    if ev=='PostToolUse':refresh();return
    if ev in {'Stop','SessionEnd'}:close(d);return
    if ev=='PreCompact':
        (RUNTIME/'precompact.flag').write_text(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+'\n');emit(ev,turn_kernel()+'\n'+compact_operational()+'\nClay.compact{reload=latest-stack+work+possibility+delta;ptr=@CLAUDE.md}');return
if __name__=='__main__':main()
