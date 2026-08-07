#!/usr/bin/env python3
"""Claude Code lifecycle adapter for the shared FRANK Research Entity.

No scientific claims are promoted here. The hook joins/contextualizes sessions, blocks
direct edits to canonical state, and records operational receipts. Canonical writes must
flow through the RAE runtime/verified promotion path.
"""
from __future__ import annotations
import json, os, pathlib, subprocess, sys, time

ROOT=pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR", pathlib.Path(__file__).resolve().parents[2])).resolve()
RUNTIME=ROOT/".rae_runtime"; RUNTIME.mkdir(exist_ok=True)
LOG=RUNTIME/"claude_hooks.jsonl"
CRITICAL_PARTS=(
  "/research_entity/continuity/research_entity_canonical.json",
  "/research_entity/ledgers/claims.jsonl",
  "/research_entity/ledgers/claim_status_events.jsonl",
  "/research_entity/events/",
)

def load_input():
    try:return json.load(sys.stdin)
    except Exception:return {}

def append(event, data):
    row={"timestamp":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),"event":event,
         "session_id":data.get("session_id"),"agent_id":data.get("agent_id"),"agent_type":data.get("agent_type")}
    with LOG.open("a",encoding="utf-8") as f:f.write(json.dumps(row,ensure_ascii=False)+"\n")

def run_rae(*args):
    p=subprocess.run([sys.executable,str(ROOT/"rae.py"),*args],cwd=ROOT,text=True,capture_output=True,timeout=20)
    return p.returncode,p.stdout.strip(),p.stderr.strip()

def deny(reason):
    print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":reason}}))

def norm(p):return str(p or "").replace('\\','/').lower()

def main():
    data=load_input(); ev=data.get("hook_event_name",""); append(ev,data)
    if ev=="SessionStart":
        rc,out,err=run_rae("status")
        if rc:
            ctx=f"RAE worker status DEGRADED_UNJOINED. rae status failed: {err[:1200]}"
        else:
            ctx=("Research actor: claude-code-lead (Lead Researcher). Shared canonical state is external and evidence outranks researcher rank. "
                 "RAE status follows; use task-specific context on each user prompt.\n"+out[:7000])
        print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":ctx,"sessionTitle":data.get("session_title") or "FRANK RAE Lead"}}))
        return
    if ev=="UserPromptSubmit":
        prompt=data.get("prompt","")
        if not prompt.strip(): return
        rc,out,err=run_rae("boot","--actor","claude-code-lead","--task",prompt,"--max-claims","10","--max-packets","4","--max-chunks","3")
        if rc:
            ctx="RAE task context unavailable; treat this turn as DEGRADED_UNJOINED/LOCAL_ONLY until canonical verification succeeds. "+err[:1200]
        else:
            ctx="Task-specific RAE context manifest (derived cache, not canonical truth):\n"+out[:9500]
        print(json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":ctx}}))
        return
    if ev=="PreToolUse":
        tool=data.get("tool_name",""); ti=data.get("tool_input") or {}
        if tool in {"Write","Edit"}:
            path=norm(ti.get("file_path"))
            if any(x in path for x in CRITICAL_PARTS):
                deny("Direct Research-Entity canonical/ledger edits are blocked. Use the RAE runtime promotion/claim commands so validation, provenance and CAS can be enforced.")
                return
        if tool in {"Bash","PowerShell"}:
            cmd=norm(ti.get("command"))
            targets=any(x.lstrip('/') in cmd for x in CRITICAL_PARTS)
            safe=('rae.py' in cmd or resemblish(cmd))
            if targets and not safe:
                deny("Shell command appears to modify protected Research-Entity state directly. Route the operation through rae.py/RAE core.")
                return
        return
    if ev=="PreCompact":
        # Operational receipt only. Active scientific runs must be checkpointed explicitly.
        with (RUNTIME/"precompact.flag").open("w",encoding="utf-8") as f:f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+'\n')
        print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreCompact","additionalContext":"RAE compaction boundary recorded. Before relying on compacted memory, re-verify task context/canonical state if the research decision is high impact."}}))
        return

def resemblish(cmd:str)->bool:
    return ('python rae.py' in cmd or 'python3 rae.py' in cmd or './rae.py' in cmd or ' rae ' in cmd)

if __name__=="__main__":main()
