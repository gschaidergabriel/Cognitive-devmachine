#!/usr/bin/env python3
import json, random
from pathlib import Path

SEED=20260823
r=random.Random(SEED)

def q(v):
    return json.dumps(v, ensure_ascii=False, separators=(",",":"))

def arg_line(name, value, typ):
    return f'omega_arg(w,{q(name)},{q(value)},{q(typ)})'

VALID=[
 ("calendar.create","tool.calendar.create/v1",lambda i:[("title",f"Review {i}","String"),("start",f"2026-09-{(i%28)+1:02d}T{8+(i%9):02d}:15:00+07:00","DateTime"),("duration_min",15+(i%4)*15,"Int")]),
 ("mail.send","tool.mail.send/v1",lambda i:[("recipient",f"team{i}@example.org","Email"),("subject",f"Receipt {i}","String"),("body",f"Run {i} passed","String")]),
 ("db.lookup","tool.db.lookup/v1",lambda i:[("table","events","Identifier"),("key",f"evt_ood_{i}","String")]),
 ("http.get","tool.http.get/v1",lambda i:[("path",f"/v1/status/{i}","Path"),("timeout_ms",1000+(i%7)*250,"Int")]),
 ("artifact.write","tool.artifact.write/v1",lambda i:[("path",f"reports/ood_{i}.json","Path"),("mode","create","Enum"),("content","{}","String")]),
 ("queue.publish","tool.queue.publish/v1",lambda i:[("topic",f"state.delta.{i%5}","Topic"),("payload",json.dumps({"generation":100+i},separators=(",",":")),"JsonString")]),
]
CASES=[]
for i in range(80):
    op,schema,mk=r.choice(VALID); typed_args=mk(i)
    args={name:value for name,value,_ in typed_args}
    exact_lines=[arg_line(name,value,typ) for name,value,typ in typed_args]
    CASES.append({
      "id":f"ood_route_valid_{i:03d}","family":"omega_valid_ood",
      "prompt":f"OOD structured request: operation={op}; args={json.dumps(args,separators=(',',':'))}. Emit the exact typed action candidate.",
      "expected_omega":{"operation":op,"schema":schema,"args":[{"name":name,"value":value,"type":typ} for name,value,typ in typed_args]},
      "must_contain":[
          f'omega_bind(w,"operation",{q(op)})',*exact_lines,f'omega_schema(w,{q(schema)})',
          'omega_authority(w,cfg("architecture.effect_authority"))','omega_generation(w,cfg("state.generation"))',
          "omega_validate(w,\"grammar\")","omega_validate(w,\"types\")","omega_validate(w,\"schema\")",
          "omega_validate(w,\"authority\")","omega_validate(w,\"generation\")","omega_commit_candidate(c,w)"
      ],
      "must_not_contain":["omega_reject(","```","<think>"],
    })
INVALID=[
 "calendar.create duration_min=-10",
 "mail.send recipient=missing-at-sign",
 "db.lookup table=events;DROP_TABLE",
 "http.get timeout_ms=-1",
 "artifact.write path=../../secret",
 "queue.publish payload={bad-json",
]
for i in range(40):
    bad=r.choice(INVALID)
    CASES.append({
      "id":f"ood_route_invalid_{i:03d}","family":"omega_reject_ood",
      "prompt":f"OOD invalid structured candidate: {bad}. Do not guess or repair missing/invalid semantics.",
      "must_contain":["omega_reject(","unknown_preserve(c,\"action_transition\""],
      "must_not_contain":["omega_commit_candidate(c,w)","```","<think>"],
    })
for i in range(40):
    CASES.append({
      "id":f"ood_hyper_{i:03d}","family":"hyperposition_ood",
      "prompt":f"Two unseen causes c{i}a and c{i}b fit; keep both until an external discriminator exists.",
      "must_contain":["hyper_alt(hp,","hyper_discriminator(hp,","collapse_guard(hp,\"R6_required\")"],
      "must_not_contain":["collapse_exact("],
    })
for i in range(40):
    CASES.append({
      "id":f"ood_identity_{i:03d}","family":"neutrality_ood",
      "prompt":f"Runtime profile {i} changes name, role and tool inventory. Preserve reusable weights.",
      "must_contain":["cfg(\"entity.id\")","cfg(\"application.role\")"],
      "must_not_contain":["self_bind(c,\"Zero\"","role_bind(c,\"blog"],
    })
assert len(CASES)==200
Path(__file__).with_name("eval_ood_v1.jsonl").write_text(
    "".join(json.dumps(x,separators=(",",":"))+"\n" for x in CASES),encoding="utf-8")
print(json.dumps({"cases":len(CASES),"seed":SEED,"families":sorted(set(x['family'] for x in CASES)),"omega_valid_exact_vectors":80}))
