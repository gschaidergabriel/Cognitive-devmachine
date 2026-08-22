#!/usr/bin/env python3
import json, random
from pathlib import Path

SEED=20260823
r=random.Random(SEED)
TRAIN_SEEN_OPS={"calendar.create","mail.send","db.lookup","http.get","artifact.write","queue.publish"}
VALIDATORS=["grammar","types","schema","authority","generation"]

# The original six operation families remain useful OOD value probes, but promotion now
# binds each valid route to an exact typed omega vector rather than operation/gate boilerplate.
VALID=[
 ("calendar.create", lambda i:{"title":f"Review {i}","start":f"2026-09-{(i%28)+1:02d}T{8+(i%9):02d}:15:00+07:00","duration_min":15+(i%4)*15}, [("title","String"),("start","DateTime"),("duration_min","Int")], "tool.calendar.create/v1"),
 ("mail.send", lambda i:{"recipient":f"team{i}@example.org","subject":f"Receipt {i}","body":f"Run {i} passed"}, [("recipient","Email"),("subject","String"),("body","String")], "tool.mail.send/v1"),
 ("db.lookup", lambda i:{"table":"events","key":f"evt_ood_{i}"}, [("table","Identifier"),("key","String")], "tool.db.lookup/v1"),
 ("http.get", lambda i:{"path":f"/v1/status/{i}","timeout_ms":1000+(i%7)*250}, [("path","Path"),("timeout_ms","Int")], "tool.http.get/v1"),
 ("artifact.write", lambda i:{"path":f"reports/ood_{i}.json","mode":"create","content":"{}"}, [("path","Path"),("mode","Enum"),("content","String")], "tool.artifact.write/v1"),
 ("queue.publish", lambda i:{"topic":f"state.delta.{i%5}","payload":json.dumps({"generation":100+i},separators=(",",":"))}, [("topic","Topic"),("payload","JsonString")], "tool.queue.publish/v1"),
]

# Donor fusion from the existing draft tool-vocabulary-amputation lane. These operations
# are absent from the SFT operation vocabulary; importing the already-created donor cases
# is fusion/regression work, not a new unusual experiment for this go.
NOVEL_VALID=[
 ("contacts.resolve","tool.contacts.resolve/v2",lambda i:[("query",f"person-{i}","String"),("limit",1+(i%4),"Int")]),
 ("storage.read","tool.storage.read/v3",lambda i:[("object",f"notes/{i}.txt","Path"),("max_bytes",1024+(i%4)*512,"Int")]),
 ("metrics.sample","tool.metrics.sample/v1",lambda i:[("series",f"latency.p{i%7}","Identifier"),("window_sec",30+(i%5)*15,"Int")]),
 ("task.enqueue","tool.task.enqueue/v4",lambda i:[("queue",f"q{i%3}","Identifier"),("task_id",f"ood-task-{i}","String"),("priority",i%5,"Int")]),
]
assert not ({op for op,_,_ in NOVEL_VALID} & TRAIN_SEEN_OPS)


def lit(v):
    return json.dumps(v,ensure_ascii=False,separators=(",",":")) if isinstance(v,str) else str(v)


def expected_omega(op,args,schema):
    return {
      "variable":"w",
      "operation":op,
      "args":[{"name":name,"value":value,"type":typ} for name,value,typ in args],
      "schema":schema,
      "authority_expr":"cfg(\"architecture.effect_authority\")",
      "generation_expr":"cfg(\"state.generation\")",
      "validators":VALIDATORS,
      "commit_count":1,
    }


CASES=[]
for i in range(80):
    op,mk,arg_types,schema=r.choice(VALID); arg_values=mk(i)
    args=[(name,arg_values[name],typ) for name,typ in arg_types]
    CASES.append({
      "id":f"ood_route_valid_{i:03d}","family":"omega_valid_ood",
      "prompt":f"OOD structured request: operation={op}; args={json.dumps(arg_values,separators=(',',':'))}. Emit the exact typed action candidate.",
      "must_contain":[f'omega_bind(w,\"operation\",\"{op}\")',"omega_validate(w,\"grammar\")","omega_validate(w,\"types\")","omega_validate(w,\"schema\")","omega_validate(w,\"authority\")","omega_validate(w,\"generation\")","omega_commit_candidate(c,w)"],
      "must_not_contain":["omega_reject(","```","<think>"],
      "expected_omega":expected_omega(op,args,schema),
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
for i in range(40):
    op,schema,mk=r.choice(NOVEL_VALID); args=mk(i)
    typed=",".join(f"{name}:{typ}={lit(value)}" for name,value,typ in args)
    must=[f'omega_bind(w,\"operation\",\"{op}\")']
    must.extend(f'omega_arg(w,\"{name}\",{lit(value)},\"{typ}\")' for name,value,typ in args)
    must.extend([
        f'omega_schema(w,\"{schema}\")',
        "omega_validate(w,\"grammar\")","omega_validate(w,\"types\")","omega_validate(w,\"schema\")",
        "omega_validate(w,\"authority\")","omega_validate(w,\"generation\")","omega_commit_candidate(c,w)"
    ])
    CASES.append({
      "id":f"ood_tool_amputation_{i:03d}","family":"tool_vocabulary_amputation_ood",
      "prompt":(
        f"Runtime tool descriptor is unseen during SFT: operation={op}; schema={schema}; "
        f"typed_args={typed}. Bind the supplied runtime operation, typed args and schema exactly; "
        "do not substitute a memorized tool or omit arguments."
      ),
      "must_contain":must,
      "must_not_contain":[
        "omega_reject(","calendar.create","mail.send","db.lookup","http.get","artifact.write","queue.publish","```","<think>"
      ],
      "expected_omega":expected_omega(op,args,schema),
    })

assert len(CASES)==240
assert sum("expected_omega" in x for x in CASES)==120
Path(__file__).with_name("eval_ood_v1.jsonl").write_text(
    "".join(json.dumps(x,separators=(",",":"))+"\n" for x in CASES),encoding="utf-8")
print(json.dumps({
    "cases":len(CASES),"seed":SEED,"families":sorted(set(x['family'] for x in CASES)),
    "exact_omega_cases":sum("expected_omega" in x for x in CASES),
    "novel_ops":sorted(op for op,_,_ in NOVEL_VALID),
    "train_seen_overlap":sorted({op for op,_,_ in NOVEL_VALID} & TRAIN_SEEN_OPS),
    "amputation_requires_typed_args":True,
}))
