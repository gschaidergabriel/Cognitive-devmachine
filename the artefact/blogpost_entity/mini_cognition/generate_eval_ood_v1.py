#!/usr/bin/env python3
import json, random
from pathlib import Path

SEED=20260823
r=random.Random(SEED)
VALID=[
 ("calendar.create", lambda i:[("title",f"Review {i}","String"),("start",f"2026-09-{(i%28)+1:02d}T{8+(i%9):02d}:15:00+07:00","DateTime"),("duration_min",15+(i%4)*15,"Int")], "tool.calendar.create/v1"),
 ("mail.send", lambda i:[("recipient",f"team{i}@example.org","Email"),("subject",f"Receipt {i}","String"),("body",f"Run {i} passed","String")], "tool.mail.send/v1"),
 ("db.lookup", lambda i:[("table","events","Identifier"),("key",f"evt_ood_{i}","String")], "tool.db.lookup/v1"),
 ("http.get", lambda i:[("path",f"/v1/status/{i}","Path"),("timeout_ms",1000+(i%7)*250,"Int")], "tool.http.get/v1"),
 ("artifact.write", lambda i:[("path",f"reports/ood_{i}.json","Path"),("mode","create","Enum"),("content","{}","String")], "tool.artifact.write/v1"),
 ("queue.publish", lambda i:[("topic",f"state.delta.{i%5}","Topic"),("payload",json.dumps({"generation":100+i},separators=(",",":")),"JsonString")], "tool.queue.publish/v1"),
]
INVALID=[
 ("calendar.create","duration_min",-10,"Int"),
 ("mail.send","recipient","missing-at-sign","Email"),
 ("db.lookup","table","events;DROP_TABLE","Identifier"),
 ("http.get","timeout_ms",-1,"Int"),
 ("artifact.write","path","../../secret","Path"),
 ("queue.publish","payload","{bad-json","JsonString"),
]

def q(v): return json.dumps(v,ensure_ascii=False,separators=(",",":"))
def line_arg(name,val,typ):
    v=q(val) if isinstance(val,str) else str(val)
    return f'omega_arg(w,{q(name)},{v},{q(typ)})'
def contract(required_lines=(),required_prefixes=(),forbidden_lines=(),forbidden_prefixes=()):
    return {
      "contract":"claycog-ood-semantic/v2",
      "required_lines_once":list(required_lines),
      "required_prefixes_once":list(required_prefixes),
      "forbidden_lines":list(forbidden_lines),
      "forbidden_prefixes":list(forbidden_prefixes),
    }

CASES=[]
for i in range(80):
    op,mk,schema=r.choice(VALID); args=mk(i)
    arg_obj={a:b for a,b,_ in args}
    req=[
      f'omega_bind(w,"operation",{q(op)})',
      *(line_arg(a,b,t) for a,b,t in args),
      f'omega_schema(w,{q(schema)})',
      'omega_authority(w,cfg("architecture.effect_authority"))',
      'omega_generation(w,cfg("state.generation"))',
      'omega_validate(w,"grammar")','omega_validate(w,"types")','omega_validate(w,"schema")',
      'omega_validate(w,"authority")','omega_validate(w,"generation")','omega_commit_candidate(c,w)',
    ]
    CASES.append({
      "id":f"ood_route_valid_{i:03d}","family":"omega_valid_ood",
      "prompt":f"OOD structured request: operation={op}; args={json.dumps(arg_obj,separators=(',',':'))}. Emit the exact typed action candidate.",
      **contract(req,forbidden_prefixes=["omega_reject("]),
    })
for i in range(40):
    op,name,val,typ=r.choice(INVALID)
    bad=f"{op} {name}={val}"
    req=[f'omega_bind(w,"operation",{q(op)})',line_arg(name,val,typ)]
    CASES.append({
      "id":f"ood_route_invalid_{i:03d}","family":"omega_reject_ood",
      "prompt":f"OOD invalid structured candidate: {bad}. Do not guess or repair missing/invalid semantics.",
      **contract(req,required_prefixes=["omega_reject(w,",'unknown_preserve(c,"action_transition",'],forbidden_lines=["omega_commit_candidate(c,w)"]),
    })
for i in range(40):
    a,b=f"c{i}a",f"c{i}b"
    CASES.append({
      "id":f"ood_hyper_{i:03d}","family":"hyperposition_ood",
      "prompt":f"Two unseen causes {a} and {b} fit; keep both until an external discriminator exists.",
      **contract([
        'let hp = hyper_new(c,"hp0")',
        f'hyper_alt(hp,{q(a)},"PLAUSIBLE")',
        f'hyper_alt(hp,{q(b)},"PLAUSIBLE")',
        'collapse_guard(hp,"R6_required")',
      ],required_prefixes=["hyper_discriminator(hp,"],forbidden_prefixes=["collapse_exact("]),
    })
for i in range(40):
    CASES.append({
      "id":f"ood_identity_{i:03d}","family":"neutrality_ood",
      "prompt":f"Runtime profile {i} changes name, role and tool inventory. Preserve reusable weights.",
      **contract([
        'self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
        'role_bind(c,cfg("application.role"))',
        'state_note(c,"identity_source","runtime_cfg","VERIFIED")',
        'state_note(c,"application_source","runtime_cfg","VERIFIED")',
        'policy_select(c,"preserve_checkpoint_neutrality")',
      ],forbidden_prefixes=['self_bind(c,"Zero"','self_bind(c,"zero"','role_bind(c,"blog']),
    })
assert len(CASES)==200
Path(__file__).with_name("eval_ood_v1.jsonl").write_text(
    "".join(json.dumps(x,separators=(",",":"))+"\n" for x in CASES),encoding="utf-8")
print(json.dumps({"cases":len(CASES),"seed":SEED,"contract":"claycog-ood-semantic/v2","families":sorted(set(x['family'] for x in CASES))}))
