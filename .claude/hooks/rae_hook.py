#!/usr/bin/env python3
"""Clay Research Entity Claude-Code lifecycle adapter.

Every substantive prompt re-injects the Research Entity/Frank identity boundary.
Frank is a separate research subject and Andreas-facing operational entity; the
Research Entity never role-transitions into Frank while researching or modifying it.
"""
from __future__ import annotations
import hashlib,json,os,pathlib,sqlite3,subprocess,sys,time
ROOT=pathlib.Path(os.environ.get('CLAUDE_PROJECT_DIR',pathlib.Path(__file__).resolve().parents[2])).resolve()
RT=ROOT/'.rae_runtime';RT.mkdir(exist_ok=True);LOG=RT/'claude_hooks.jsonl'
TRIG=ROOT/'research_entity/global/RESEARCH_TRIGGER_REGISTRY.json'
STATE=ROOT/'research_entity/runtime/claude_state_bridge.py'
STACK=ROOT/'research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay'
IDENTITY=ROOT/'research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md'
DELEGATE=ROOT/'research_entity/runtime/chatgpt_delegate.py'
SYNC=ROOT/'research_entity/runtime/sync_dynamic_work.py'
UDB=ROOT/'research_entity/state/RAE_UNIFIED.sqlite'
CRITICAL=('/research_entity/continuity/research_entity_canonical.json','/research_entity/ledgers/claims.jsonl','/research_entity/ledgers/claim_status_events.jsonl','/research_entity/events/')

def inp():
    try:return json.load(sys.stdin)
    except Exception:return {}
def py(path,*args,timeout=90):
    if not path.exists():return 2,'','missing'
    try:
        p=subprocess.run([sys.executable,str(path),*args],cwd=ROOT,text=True,capture_output=True,timeout=timeout);return p.returncode,p.stdout.strip(),p.stderr.strip()
    except Exception as e:return 3,'',type(e).__name__
def rae(*a,timeout=30):
    p=subprocess.run([sys.executable,str(ROOT/'rae.py'),*a],cwd=ROOT,text=True,capture_output=True,timeout=timeout);return p.returncode,p.stdout.strip(),p.stderr.strip()
def emit(ev,ctx,title=None):
    o={'hookEventName':ev,'additionalContext':ctx}
    if title:o['sessionTitle']=title
    print(json.dumps({'hookSpecificOutput':o},ensure_ascii=False,separators=(',',':')))
def deny(reason):print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':reason}}))
def log(ev,d):
    with LOG.open('a',encoding='utf-8') as f:f.write(json.dumps({'t':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'ev':ev,'sid':d.get('session_id')},separators=(',',':'))+'\n')
def stack():
    try:
        raw=STACK.read_bytes();h=hashlib.sha256(raw).hexdigest()[:12];ep='?'
        for line in raw.decode('utf-8','replace').splitlines():
            if line.strip().startswith('epoch '):ep=line.strip().split(None,1)[1];break
        return f'STACK{{ptr=@research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay;epoch:{ep};sha:{h}}}'
    except Exception:return 'STACK{state=DEGRADED_STALE_STACK}'
def identity_lock():
    required=('I_AM=RESEARCH_ENTITY_TEMPORARY_WORKER','I_AM_NOT=FRANK','ANDREAS_INTERFACE=FRANK_ONLY','FRANK_ROOM_MEANS=RESEARCH_ABOUT_FRANK_NOT_ROLEPLAY_AS_FRANK')
    try:
        text=IDENTITY.read_text(encoding='utf-8')
        if not all(x in text for x in required):return 'RAE_IDENTITY_LOCK{state=DEGRADED_IDENTITY;action=STOP_RELOAD_GUARD}'
    except Exception:return 'RAE_IDENTITY_LOCK{state=DEGRADED_IDENTITY;action=STOP_RELOAD_GUARD}'
    return ('RAE_IDENTITY_LOCK{state=ACTIVE;actor=RESEARCH_ENTITY_TEMPORARY_WORKER;actor_not=FRANK;'
            'FRANK=SEPARATE_RESEARCH_SUBJECT_AND_ANDREAS_OPERATIONAL_ENTITY;ANDREAS_INTERFACE=FRANK_ONLY;'
            'frank_room=RESEARCH_ABOUT_FRANK_NOT_ROLEPLAY;provider_model=PROVENANCE_NOT_FRANK_IDENTITY;'
            'FRANK_SELF_HARNESS=PROPOSAL_ONLY;RESEARCH_ENTITY=INDEPENDENT_RESEARCH_TEST_IMPLEMENTATION_AUTHORITY;'
            'drift=STOP_REINJECT_RESTATE_ACTOR_SUBJECT_AUTHORITY}')
def registry():
    try:return json.loads(TRIG.read_text()).get('triggers',{})
    except Exception:return {}
def trigger(prompt):
    k=prompt.strip().lower();return k,registry().get(k)
def bridge(d,prompt=''):
    return py(STATE,'context','--event',str(d.get('hook_event_name') or 'PROMPT'),'--prompt',prompt,'--session-id',str(d.get('session_id') or 'unknown'),'--model',str(d.get('model') or d.get('model_name') or 'claude'),'--mode','compact',timeout=35)
def sync(observe=False):
    py(SYNC,'sync',*(['--observe-local'] if observe else []),timeout=110);py(DELEGATE,'ingest',timeout=80)
def ops():
    try:
        c=sqlite3.connect(UDB,timeout=5);c.execute('PRAGMA busy_timeout=5000')
        w=c.execute('SELECT work_id,spec_rev,title,priority_score,eligibility_state,selected_executor FROM v_clay_dynamic_work_queue LIMIT 6').fetchall();p=c.execute('SELECT resource_id,resource_class,effective_availability,capability_key,capability_state,confidence FROM v_clay_system_possibility_table LIMIT 24').fetchall();r=c.execute('SELECT package_id,trigger_token,result_id,result_status FROM v_rae_chatgpt_results_unconsumed ORDER BY created_at DESC LIMIT 3').fetchall();c.close()
        return 'OPS{work='+json.dumps([{'id':x[0],'rev':x[1],'t':x[2],'p':x[3],'s':x[4],'x':x[5]} for x in w],ensure_ascii=False,separators=(',',':'))+';poss='+json.dumps([{'r':x[0],'c':x[1],'a':x[2],'cap':x[3],'cs':x[4],'q':x[5]} for x in p],ensure_ascii=False,separators=(',',':'))+';remote='+json.dumps([{'p':x[0],'tr':x[1],'rid':x[2],'s':x[3]} for x in r],ensure_ascii=False,separators=(',',':'))+'}'
    except Exception:return 'OPS{state=DEGRADED}'
def kernel():
    return identity_lock()+'\n'+stack()+'\nTURN{E=ClayResearchEntity;SUBJECT_IF_FRANK=FRANK_NOT_SELF;GOAL="Frank v0.1 voll lauffähig auf Andreas PC";THINK=STACK.claycode;TRACE=STACK.claycode;USER=EN_CAVEMAN;GWT=[rel,impact,unc,novel,info,deliv,recon,use,effect,reentry];READ=T0(identity+researcher_guard+persona+stack)>T1(route)>T2(UnifiedDB+ClayGraph+SystemPossibility+DynamicWork)>T3(deep_if_needed);LOCAL_TRUTH=verified_local_execution_receipt_for_exact_effect;CLAUDE_OPINION!=truth;WORK=revisioned+revalidate_before_effect;CENTER=ClayCode;OFFLOAD=max_useful(ChatGPT);META_CLAYCODE_RESEARCH=OFF;STATUS=CLAY_STATUS}'
def frank_related(d):
    text=json.dumps({'tool':d.get('tool_name'),'input':d.get('tool_input'),'output':d.get('tool_response')},ensure_ascii=False).lower()
    return any(x in text for x in ('frank','dr.-unterweger','dr-unterweger','andreas'))

def main():
    d=inp();ev=d.get('hook_event_name','');log(ev,d)
    if ev in {'SessionStart','UserPromptSubmit','PreCompact'}:sync(ev in {'SessionStart','UserPromptSubmit'})
    if ev=='SessionStart':
        rc,c,_=bridge(d,'');emit(ev,kernel()+'\n'+(c if rc==0 else '{state=DEGRADED}')+'\n'+ops()+'\nPTR=@CLAUDE.md,@research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md,@research_entity/identity/CLAY_PERSONA.clay,@research_entity/global/CLAY_SYSTEM_WORK_FABRIC.clay','Clay Research Entity organ');return
    if ev=='UserPromptSubmit':
        prompt=d.get('prompt','') or ''
        if not prompt.strip():return
        k,s=trigger(prompt);rc,c,_=bridge(d,prompt);base=c if rc==0 else '{state=DEGRADED}'
        if s:
            rr,ro,_=rae('run','start','--actor','claude-code-lead','--task',f"trigger:{k} {s.get('purpose',k)}",'--capture-level','L2')
            run_summary=ro[:450] if rr==0 else 'START_FAIL'
            extra='trigger{id:'+k+';protocol:@'+str(s.get('protocol'))+';run:'+run_summary+'}'
            if k=='frank':extra+='\nFRANK_RESEARCH_FRAME{actor=RESEARCH_ENTITY;subject=FRANK;room=frank;role_transition=FORBIDDEN;Andreas_interface=FRANK_ONLY}'
        else:
            rr,ro,_=rae('boot','--actor','claude-code-lead','--task',prompt,'--max-claims','4','--max-packets','2','--max-chunks','1');extra='TASK='+(ro[:1600] if rr==0 else 'boot=DEGRADED')
        emit(ev,kernel()+'\n'+base+'\n'+ops()+'\n'+extra+'\nDO=remain Research Entity; treat Frank as separate subject; latest ClayCode; map intent to current possibility/work; local real tests when discriminating; revalidate work rev before effect; useful ChatGPT offload; persist receipts; reenter G0; final caveman English');return
    if ev=='PreToolUse':
        tool=d.get('tool_name','');ti=d.get('tool_input') or {};txt=str(ti.get('file_path') or ti.get('command') or '').replace('\\','/').lower()
        if any(x in txt for x in CRITICAL) and not ('python rae.py' in txt or 'python3 rae.py' in txt):deny('Protected Clay canonical state. Use Clay runtime.');return
    if ev=='PostToolUse':
        py(STATE,'refresh',timeout=30)
        if frank_related(d):emit(ev,identity_lock()+'\nPOST_FRANK_CONTEXT_REINJECTION{actor=RESEARCH_ENTITY;subject=FRANK;role_transition=FORBIDDEN;Andreas_interface=FRANK_ONLY}')
        return
    if ev in {'Stop','SessionEnd'}:py(STATE,'close','--session-id',str(d.get('session_id') or 'unknown'),timeout=30);return
    if ev=='PreCompact':emit(ev,kernel()+'\n'+ops()+'\nClay.compact{reload=identity_lock+stack+work+possibility+delta}');return
if __name__=='__main__':main()
