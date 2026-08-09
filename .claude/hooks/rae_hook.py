#!/usr/bin/env python3
"""Ultra-compact Claude Code lifecycle adapter for one repo-native RAE hive.

Policy: every substantive round injects a tiny ClayCode cognition kernel: GWT tensor,
state-read ladder, output surface, status-footer invariant. Rich state remains in repo/DB
and is fetched by pointer/delta only when needed.
"""
from __future__ import annotations
import json, os, pathlib, subprocess, sys, time

ROOT=pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR",pathlib.Path(__file__).resolve().parents[2])).resolve()
RUNTIME=ROOT/".rae_runtime";RUNTIME.mkdir(exist_ok=True)
LOG=RUNTIME/"claude_hooks.jsonl"
TRIGGERS=ROOT/"research_entity/global/RESEARCH_TRIGGER_REGISTRY.json"
STATE=ROOT/"research_entity/runtime/claude_state_bridge.py"
CRITICAL=("/research_entity/continuity/research_entity_canonical.json","/research_entity/ledgers/claims.jsonl","/research_entity/ledgers/claim_status_events.jsonl","/research_entity/events/")


def inp():
    try:return json.load(sys.stdin)
    except Exception:return {}
def log(ev,d,**x):
    row={"t":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),"ev":ev,"sid":d.get("session_id"),**x}
    with LOG.open("a",encoding="utf-8") as f:f.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
def run(*a,timeout=30):
    p=subprocess.run([sys.executable,str(ROOT/"rae.py"),*a],cwd=ROOT,text=True,capture_output=True,timeout=timeout)
    return p.returncode,p.stdout.strip(),p.stderr.strip()
def bridge(d,prompt=""):
    if not STATE.exists():return 2,"","state_bridge_missing"
    ev=str(d.get("hook_event_name") or "PROMPT");sid=str(d.get("session_id") or "unknown");model=str(d.get("model") or d.get("model_name") or "claude")
    p=subprocess.run([sys.executable,str(STATE),"context","--event",ev,"--prompt",prompt,"--session-id",sid,"--model",model,"--mode","compact"],cwd=ROOT,text=True,capture_output=True,timeout=30)
    return p.returncode,p.stdout.strip(),p.stderr.strip()
def refresh():
    if STATE.exists():subprocess.run([sys.executable,str(STATE),"refresh"],cwd=ROOT,text=True,capture_output=True,timeout=20)
def close(d):
    if STATE.exists():subprocess.run([sys.executable,str(STATE),"close","--session-id",str(d.get("session_id") or "unknown")],cwd=ROOT,text=True,capture_output=True,timeout=20)
def reg():
    try:return json.loads(TRIGGERS.read_text(encoding="utf-8"))
    except Exception:return {"triggers":{}}
def trig(prompt):
    k=prompt.strip().lower();return k,(reg().get("triggers") or {}).get(k)
def norm(x):return str(x or "").replace('\\','/').lower()
def safe_cmd(c):return ('python rae.py' in c or 'python3 rae.py' in c or './rae.py' in c or ' rae ' in c)
def deny(reason):print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":reason}}))
def emit(ev,ctx,title=None):
    o={"hookEventName":ev,"additionalContext":ctx}
    if title:o["sessionTitle"]=title
    print(json.dumps({"hookSpecificOutput":o},ensure_ascii=False,separators=(",",":")))


def turn_kernel():
    # Intentionally repeated every round. ~small fixed semantic payload.
    return (
      "TURN{E=RAE;THINK=CLAYCODE;USER=EN_CAVEMAN;"
      "GWT=[rel,impact,unc,novel,info,deliv,recon,use,effect,reentry];"
      "FOCUS=argmax(admissible(GWT0..4));CREDIT=receipt(deliv,recon,use,effect,reentry);"
      "READ=T0verify(canonical)>T1route(registry)>T2assemble(current+open+negative+packets+experiments+handoffs)>T3deep?mutate|conflict|recovery|highimpact|insufficient;"
      "STATUS=final_plain_```text```:{RAE_STATUS,NEXT_LEVEL,DOOMSDAY};NO_AFTER=1;"
      "UX=[misunderstanding,good,friction,awkward,retrieval_miss,stale,wrong_route,repair,token_waste]->CLAYCODE_RESEARCH}"
    )


def main():
    d=inp();ev=d.get("hook_event_name","");log(ev,d)
    if ev=="SessionStart":
        rc,c,e=bridge(d,"");src=c if rc==0 else '{"E":"RAE","state":"DEGRADED"}'
        emit(ev,turn_kernel()+"\n"+src+"\nPTR=@CLAUDE.md,@research_entity/global/RAE_TURN_KERNEL.clay","RAE organ")
        return
    if ev=="UserPromptSubmit":
        prompt=d.get("prompt","")
        if not prompt.strip():return
        k,s=trig(prompt);rc,c,e=bridge(d,prompt);base=c if rc==0 else '{"E":"RAE","state":"DEGRADED"}'
        kernel=turn_kernel()
        if s:
            purpose=s.get("purpose",k);protocol=s.get("protocol")
            rr,ro,re=run("run","start","--actor","claude-code-lead","--task",f"trigger:{k} {purpose}","--capture-level","L2")
            ctx=kernel+"\n"+base+f"\ntrigger{{id:{k};protocol:@{protocol};run:{ro[:500] if rr==0 else 'START_FAIL'}}\nDO=read pointer sections on demand; execute now; persist ClayCode receipts"
            emit(ev,ctx);return
        br,bo,be=run("boot","--actor","claude-code-lead","--task",prompt,"--max-claims","4","--max-packets","2","--max-chunks","1")
        task=(bo[:2200] if br==0 else "boot=DEGRADED")
        emit(ev,kernel+"\n"+base+"\nTASK="+task+"\nDO=fetch only needed refs; machine traces ClayCode; final caveman English")
        return
    if ev=="PreToolUse":
        tool=d.get("tool_name","");ti=d.get("tool_input") or {}
        if tool in {"Write","Edit"}:
            p=norm(ti.get("file_path"))
            if any(x in p for x in CRITICAL):deny("Use RAE runtime for protected canonical/ledger state.");return
        if tool in {"Bash","PowerShell"}:
            c=norm(ti.get("command"))
            if any(x.lstrip('/') in c for x in CRITICAL) and not safe_cmd(c):deny("Protected RAE state. Use rae.py.");return
        return
    if ev=="PostToolUse":refresh();return
    if ev in {"Stop","SessionEnd"}:close(d);return
    if ev=="PreCompact":
        (RUNTIME/"precompact.flag").write_text(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+'\n')
        emit(ev,turn_kernel()+"\nRAE.compact{reload=delta;ptr=@CLAUDE.md}");return

if __name__=="__main__":main()
