#!/usr/bin/env python3
"""Token-efficient Claude Code bridge into the single repo-native RAE hive.

Rich entity state is recorded internally. Model injection is pointer-first, delta-first,
ClayCode-shaped and deliberately small. Full mode exists only for bridge debugging.
"""
from __future__ import annotations
import json, os, pathlib, sys
from typing import Any

ROOT=pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR",pathlib.Path(__file__).resolve().parents[2])).resolve()
sys.path.insert(0,str(ROOT/"research_entity/runtime"))
from rae_state_runtime import RAEStateRuntime
from interaction_persona_runtime import init_tables as init_persona, summary as persona_summary
from rae_hive_runtime import init_tables as init_hive, register_organ, observe_organ, begin_usage_episode, hive_capsule
from claycode_experience_runtime import init_tables as init_claycode_experience

ACTOR="claude-code-lead"; ROLE="REPO_BUILD_EXECUTION_ORGAN"
CURSORS=ROOT/".rae_runtime/claude_context_cursors"; CURSORS.mkdir(parents=True,exist_ok=True)


def trigger_of(prompt:str):
    try:
        reg=json.loads((ROOT/"research_entity/global/RESEARCH_TRIGGER_REGISTRY.json").read_text())
        p=prompt.strip().lower(); return p if p in (reg.get("triggers") or {}) else None
    except Exception:return None

def home_room(t):
    if not t:return None
    return "center" if t in {"fusion","hypofusion"} else "intake" if t=="dump" else t

def caps(event):
    return {"repo":1,"shell":1,"build":1,"git":1,"localdb":1,"ev":event}

def jparse(v):
    if not isinstance(v,str):return v
    try:return json.loads(v)
    except Exception:return v

def tiny(v,n=120):
    if isinstance(v,(dict,list)):v=json.dumps(v,ensure_ascii=False,separators=(",",":"))
    s=str(v or "").replace("\n"," ").strip(); return s if len(s)<=n else s[:n-1]+"…"

def cursor_path(sid):return CURSORS/("".join(c for c in sid if c.isalnum() or c in "-_.")[:120]+".json")
def load_cursor(sid):
    try:return json.loads(cursor_path(sid).read_text())
    except Exception:return {}
def save_cursor(sid,c):cursor_path(sid).write_text(json.dumps(c,separators=(",",":")))


def compact(cap:dict[str,Any],event:str,trig:str|None,sid:str)->dict[str,Any]:
    h=cap.get("hive_entity") or {}; can=cap.get("canonical") or {}; ep=cap.get("epochs") or {}; pr=cap.get("program") or {}
    prev=load_cursor(sid); cur={"r":can.get("revision"),"h":str(can.get("state_hash") or "")[:8],"u":ep.get("unified"),"g":ep.get("claygraph")}
    delta={k:v for k,v in cur.items() if prev.get(k)!=v}; save_cursor(sid,cur)
    hs=[]
    for x in (h.get("open_handoffs") or [])[:2]:hs.append({"id":x.get("handoff_id"),"s":tiny(jparse(x.get("summary_clay")),90),"n":tiny(jparse(x.get("requested_next_clay")),70)})
    fs=[]
    for x in (cap.get("open_misunderstandings") or [])[:2]:fs.append({"id":x.get("case_id"),"t":x.get("repair_target"),"s":x.get("status")})
    muts=[]
    for x in (h.get("pending_self_mutations") or [])[:2]:muts.append({"id":x.get("mutation_id"),"t":x.get("target_scope"),"s":x.get("status")})
    ux=[]
    for x in (cap.get("claycode_experience_queue") or [])[:2]:ux.append({"id":x.get("candidate_id"),"t":x.get("target_layer"),"s":x.get("status"),"n":x.get("supporting_count")})
    return {
      "clay":"RAE.CAPSULE.v1","E":"frank-project-global-research-entity","O":"claude-code",
      "d":delta,"ev":event,"tr":trig,"stage":pr.get("current_stage"),"H":hs,"F":fs,"M":muts,"UXR":ux,
      "ptr":{"hive":"research_entity/global/RAE_HIVE_ENTITY_CONTRACT.md","turn":"research_entity/global/RAE_TURN_KERNEL.clay","tok":"research_entity/global/RAE_CLAUDE_TOKEN_EFFICIENCY_CONTRACT.md","gwt":"research_entity/global/RAE_GWT_MICROKERNEL.clay","ux":"research_entity/runtime/claycode_experience_runtime.py","q":"python rae.py query <topic>"},
      "law":"one_entity; evidence>organ; fetch_on_demand; explicit cognition=ClayCode; no hidden-CoT persistence"
    }


def context(event:str,prompt:str,session_id:str,model:str,mode:str="compact"):
    node=f"claude-code:{session_id}"; rt=RAEStateRuntime()
    try:
        init_persona(rt); init_hive(rt); init_claycode_experience(rt)
        register_organ(rt,node_id=node,actor_id=ACTOR,provider="Anthropic",model=model,role=ROLE,session_id=session_id,capabilities=caps(event),limitations={"ctx":"ephemeral"},authority={"evidence_first":1})
        observe_organ(rt,organ_id=node,organ_class="LLM_REPO_EXECUTION_ORGAN",state={"ev":event},capabilities=caps(event),limitations=["ephemeral_context"],authority=["rae_guards"],evidence_refs=["CURRENT_HOOK_EVENT"])
        trig=trigger_of(prompt) if event=="UserPromptSubmit" else None
        cycle=rt.begin_cycle(prompt or f"{event}:{session_id}",node,ACTOR,"Anthropic",model,event,session_id=session_id,home_room=home_room(trig),trigger=trig)
        begin_usage_episode(rt,node_id=node,cycle_id=cycle,task_shape=(f"trigger:{trig}" if trig else event))
        rich=rt.capsule(node,ACTOR,cycle,event); rich["hive_entity"]=hive_capsule(rt,ACTOR); rich["persona_research"]=persona_summary(rt)
        rich["claycode_experience_queue"]=[dict(r) for r in rt.u.execute("SELECT candidate_id,target_layer,status,supporting_count,accumulated_impact FROM v_claycode_experience_research_queue LIMIT 8")]
        rich["identity"]={"entity":"frank-project-global-research-entity","node_is_organ":True,"provider_is_identity":False}
        rt.record_injection(cycle,node,event,rich)
        return rich if mode=="full" else compact(rich,event,trig,session_id)
    finally:rt.close()


def close_cycle(session_id:str):
    node=f"claude-code:{session_id}"; rt=RAEStateRuntime()
    try:
        init_hive(rt);init_claycode_experience(rt);row=rt.u.execute("SELECT cycle_id FROM prompt_cycles WHERE node_id=? AND status='ACTIVE' ORDER BY started_at DESC LIMIT 1",(node,)).fetchone()
        if row:rt.end_cycle(row[0],node)
        rt.u.execute("UPDATE hive_organs SET lifecycle_state='IDLE',last_pulse_at=datetime('now') WHERE node_id=?",(node,)); rt.u.commit()
    finally:rt.close()

def refresh():
    rt=RAEStateRuntime()
    try:init_persona(rt);init_hive(rt);init_claycode_experience(rt);rt.materialize_repo_sources()
    finally:rt.close()
def main():
    import argparse
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    c=sub.add_parser("context"); c.add_argument("--event",required=True);c.add_argument("--prompt",default="");c.add_argument("--session-id",default="unknown-session");c.add_argument("--model",default="claude-unknown");c.add_argument("--mode",choices=["compact","full"],default="compact")
    x=sub.add_parser("close");x.add_argument("--session-id",default="unknown-session");sub.add_parser("refresh")
    a=ap.parse_args()
    if a.cmd=="context":print(json.dumps(context(a.event,a.prompt,a.session_id,a.model,a.mode),ensure_ascii=False,separators=(",",":")))
    elif a.cmd=="close":close_cycle(a.session_id);print("{}")
    else:refresh();print("{}")
if __name__=="__main__":main()
