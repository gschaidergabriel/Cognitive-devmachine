#!/usr/bin/env python3
"""Claude Code lifecycle adapter for the shared FRANK Research Entity.

Joins/contextualizes sessions, blocks direct canonical-state edits, records operational
receipts, resolves exact project research triggers, and injects the central RAE
UnifiedDB/ClayGraph capsule before substantive work.
"""
from __future__ import annotations
import json, os, pathlib, subprocess, sys, time

ROOT=pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR", pathlib.Path(__file__).resolve().parents[2])).resolve()
RUNTIME=ROOT/".rae_runtime"; RUNTIME.mkdir(exist_ok=True)
LOG=RUNTIME/"claude_hooks.jsonl"
TRIGGERS=ROOT/"research_entity/global/RESEARCH_TRIGGER_REGISTRY.json"
MASTER=ROOT/"research_entity/triggers/MASTER_RESEARCH_TRIGGER_PROTOCOL.md"
FOOTER=ROOT/"research_entity/global/STATUS_FOOTER_PROTOCOL.md"
STATE_BRIDGE=ROOT/"research_entity/runtime/claude_state_bridge.py"
CRITICAL_PARTS=(
  "/research_entity/continuity/research_entity_canonical.json",
  "/research_entity/ledgers/claims.jsonl",
  "/research_entity/ledgers/claim_status_events.jsonl",
  "/research_entity/events/",
)

def load_input():
    try:return json.load(sys.stdin)
    except Exception:return {}

def append(event,data,**extra):
    row={"timestamp":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),"event":event,
         "session_id":data.get("session_id"),"agent_id":data.get("agent_id"),"agent_type":data.get("agent_type"),**extra}
    with LOG.open("a",encoding="utf-8") as f:f.write(json.dumps(row,ensure_ascii=False)+"\n")

def run_rae(*args):
    p=subprocess.run([sys.executable,str(ROOT/"rae.py"),*args],cwd=ROOT,text=True,capture_output=True,timeout=30)
    return p.returncode,p.stdout.strip(),p.stderr.strip()

def run_state_context(data,prompt=""):
    if not STATE_BRIDGE.exists(): return 2,"","central state bridge missing"
    ev=str(data.get("hook_event_name") or "PROMPT")
    sid=str(data.get("session_id") or "unknown-session")
    model=str(data.get("model") or data.get("model_name") or "claude-unknown")
    p=subprocess.run([sys.executable,str(STATE_BRIDGE),"context","--event",ev,"--prompt",prompt,"--session-id",sid,"--model",model],cwd=ROOT,text=True,capture_output=True,timeout=30)
    return p.returncode,p.stdout.strip(),p.stderr.strip()

def refresh_central_state():
    if not STATE_BRIDGE.exists(): return
    subprocess.run([sys.executable,str(STATE_BRIDGE),"refresh"],cwd=ROOT,text=True,capture_output=True,timeout=30)

def close_central_cycle(data):
    if not STATE_BRIDGE.exists(): return
    sid=str(data.get("session_id") or "unknown-session")
    subprocess.run([sys.executable,str(STATE_BRIDGE),"close","--session-id",sid],cwd=ROOT,text=True,capture_output=True,timeout=30)

def central_context(data,prompt=""):
    rc,out,err=run_state_context(data,prompt)
    if rc:
        return "RAE CENTRAL STATE DEGRADED: "+(err or out or "unknown error")[:1500]+". Do not create a provider/session fallback Research-Entity DB."
    return (
      "RAE CENTRAL STATE / CLAYGRAPH CAPSULE\n"
      "Identity boundary: this Claude session is a temporary research actor node, not Frank and not a separate Research Entity.\n"
      "Shared-state boundary: Claude Code and ChatGPT secondary operate against one repository-owned research state.\n"
      "Reference Harness: frankv0.1 is the live H1 baseline; Andreas is the longitudinal founding pilot user.\n"
      "Continuous repair: screen eligible live use for misunderstandings, wrong actions, retrieval/context/handoff/tool/recovery failures and success patterns; causal-localize and regressionize material cases.\n"
      "Generality: user-specific state may personalize; architecture changes require generalized evidence.\n"
      "ClayGraph activation/relevance is derived and never fact authority.\n"+out[:14000]
    )

def run_dump_prepare(data):
    cmd=[sys.executable,str(ROOT/"tools/dump_queue.py"),"prepare","--actor","claude-code-lead"]
    if data.get("session_id"):cmd.extend(["--session-id",str(data["session_id"])])
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=45)
    return p.returncode,p.stdout.strip(),p.stderr.strip()

def read_text(path,limit=16000):
    try:return path.read_text(encoding="utf-8")[:limit]
    except Exception as e:return f"UNAVAILABLE {path}: {e}"

def registry():
    try:return json.loads(TRIGGERS.read_text(encoding="utf-8"))
    except Exception:return {"triggers":{}}

def exact_trigger(prompt):
    key=prompt.strip().lower()
    return (key,registry().get("triggers",{}).get(key))

def deny(reason):
    print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":reason}}))

def norm(p):return str(p or "").replace('\\','/').lower()

def trigger_context(key,spec,data):
    purpose=spec.get("purpose",key)
    rc_boot,out_boot,err_boot=run_rae("boot","--actor","claude-code-lead","--task",f"Execute reserved RAE research trigger {key}: {purpose}","--max-claims","14","--max-packets","6","--max-chunks","4")
    rc_run,out_run,err_run=run_rae("run","start","--actor","claude-code-lead","--task",f"trigger:{key} {purpose}","--capture-level","L2")
    protocol=ROOT/spec.get("protocol","")
    ctx=(
      central_context(data,key)+"\n\n"
      f"RESERVED PROJECT RESEARCH TRIGGER `{key}` DETECTED. Execute it now; do not ask the user to restate the task.\n\n"
      "This is one shared Research Entity. Evidence outranks researcher rank. Preserve actor/model provenance.\n\n"
      "RAE task context:\n"+(out_boot if rc_boot==0 else "DEGRADED_UNJOINED: "+err_boot)[:7000]+"\n\n"
      "Trigger run start:\n"+(out_run if rc_run==0 else "RUN_START_FAILED: "+err_run)[:3500]+"\n\n"
      "MASTER_RESEARCH_TRIGGER_PROTOCOL:\n"+read_text(MASTER,12000)+"\n\n"
      f"TRIGGER-SPECIFIC PROTOCOL ({key}):\n"+read_text(protocol,12000)+"\n\n"
      "MANDATORY VISIBLE STATUS FOOTER:\n"+read_text(FOOTER,7000)
    )
    append("RESEARCH_TRIGGERED",data,command=key,protocol=str(protocol.relative_to(ROOT)) if protocol.exists() else str(protocol),run_start_ok=rc_run==0)
    return ctx

def main():
    data=load_input(); ev=data.get("hook_event_name",""); append(ev,data)
    if ev=="SessionStart":
        rc,out,err=run_rae("status")
        trigger_words=' · '.join(registry().get('triggers',{}).keys()) or 'registry unavailable'
        cctx=central_context(data,"")
        if rc:
            ctx=cctx+"\n\nRAE worker status DEGRADED_UNJOINED. rae status failed: "+err[:1200]
        else:
            ctx=(cctx+"\n\nResearch actor: claude-code-lead (Lead Researcher). Shared canonical state is external and evidence outranks researcher rank. "
                 f"Exact reserved research triggers: {trigger_words}. Every substantive visible response must follow STATUS_FOOTER_PROTOCOL.md.\n"+out[:7000])
        print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":ctx,"sessionTitle":data.get("session_title") or "FRANK RAE Lead"}}));return
    if ev=="UserPromptSubmit":
        prompt=data.get("prompt","")
        if not prompt.strip():return
        key,spec=exact_trigger(prompt)
        if spec:
            if key=="dump":
                append("DUMP_TRIGGERED",data,command="dump")
                rc_boot,out_boot,err_boot=run_rae("boot","--actor","claude-code-lead","--task","Execute project-wide DUMP research intake protocol","--max-claims","12","--max-packets","5","--max-chunks","4")
                rc_dump,out_dump,err_dump=run_dump_prepare(data)
                protocol=ROOT/spec.get("protocol","research_entity/global/DUMP_PROTOCOL.md")
                ctx=(central_context(data,prompt)+"\n\nRESERVED PROJECT COMMAND `dump` DETECTED. Execute the complete RAE Dump Protocol now; do not ask what dump means. "
                     "Dump material is hypothesis-generating intake, not canonical evidence. Only archive originals after the whole pipeline validates.\n\n"
                     "RAE task context:\n"+(out_boot if rc_boot==0 else "DEGRADED_UNJOINED: "+err_boot)[:6500]+"\n\n"
                     "Frozen local dump queue manifest:\n"+(out_dump if rc_dump==0 else "DUMP_PREPARE_FAILED: "+err_dump)[:6500]+"\n\n"
                     "DUMP_PROTOCOL:\n"+read_text(protocol,12000)+"\n\nMANDATORY STATUS FOOTER:\n"+read_text(FOOTER,7000))
                print(json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":ctx}}));return
            print(json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":trigger_context(key,spec,data)}}));return
        rc,out,err=run_rae("boot","--actor","claude-code-lead","--task",prompt,"--max-claims","10","--max-packets","4","--max-chunks","3")
        if rc:ctx="RAE task context unavailable; treat this turn as DEGRADED_UNJOINED/LOCAL_ONLY until canonical verification succeeds. "+err[:1200]
        else:ctx="Task-specific RAE context manifest (derived cache, not canonical truth):\n"+out[:9500]
        ctx=central_context(data,prompt)+"\n\n"+ctx+"\n\nEvery substantive visible response must end with research_entity/global/STATUS_FOOTER_PROTOCOL.md."
        print(json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":ctx}}));return
    if ev=="PreToolUse":
        tool=data.get("tool_name","");ti=data.get("tool_input") or {}
        if tool in {"Write","Edit"}:
            path=norm(ti.get("file_path"))
            if any(x in path for x in CRITICAL_PARTS):
                deny("Direct Research-Entity canonical/ledger edits are blocked. Use RAE runtime commands so validation, provenance and CAS can be enforced.");return
        if tool in {"Bash","PowerShell"}:
            cmd=norm(ti.get("command"));targets=any(x.lstrip('/') in cmd for x in CRITICAL_PARTS);safe=resemblish(cmd)
            if targets and not safe:
                deny("Shell command appears to modify protected Research-Entity state directly. Route the operation through rae.py/RAE core.");return
        return
    if ev=="PostToolUse":
        refresh_central_state(); return
    if ev in {"Stop","SessionEnd"}:
        close_central_cycle(data); return
    if ev=="PreCompact":
        with (RUNTIME/"precompact.flag").open("w",encoding="utf-8") as f:f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+'\n')
        print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreCompact","additionalContext":"RAE compaction boundary recorded. Re-verify task context/canonical state for high-impact research after compaction."}}));return

def resemblish(cmd):return ('python rae.py' in cmd or 'python3 rae.py' in cmd or './rae.py' in cmd or ' rae ' in cmd)

if __name__=="__main__":main()
