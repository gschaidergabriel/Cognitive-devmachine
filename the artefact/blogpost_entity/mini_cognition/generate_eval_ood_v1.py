#!/usr/bin/env python3
import json, random
from pathlib import Path

SEED=20260823
r=random.Random(SEED)
VALID=[
 ("calendar.create", lambda i:{"title":f"Review {i}","start":f"2026-09-{(i%28)+1:02d}T{8+(i%9):02d}:15:00+07:00","duration_min":15+(i%4)*15}, [("title","String"),("start","DateTime"),("duration_min","Int")], "tool.calendar.create/v1"),
 ("mail.send", lambda i:{"recipient":f"team{i}@example.org","subject":f"Receipt {i}","body":f"Run {i} passed"}, [("recipient","Email"),("subject","String"),("body","String")], "tool.mail.send/v1"),
 ("db.lookup", lambda i:{"table":"events","key":f"evt_ood_{i}"}, [("table","Identifier"),("key","String")], "tool.db.lookup/v1"),
 ("http.get", lambda i:{"path":f"/v1/status/{i}","timeout_ms":1000+(i%7)*250}, [("path","Path"),("timeout_ms","Int")], "tool.http.get/v1"),
 ("artifact.write", lambda i:{"path":f"reports/ood_{i}.json","mode":"create","content":"{}"}, [("path","Path"),("mode","Enum"),("content","String")], "tool.artifact.write/v1"),
 ("queue.publish", lambda i:{"topic":f"state.delta.{i%5}","payload":json.dumps({"generation":100+i},separators=(",",":"))}, [("topic","Topic"),("payload","JsonString")], "tool.queue.publish/v1"),
]
TRAIN_SEEN_OPS={op for op,_,_,_ in VALID}
# The one unusual experiment for this user-triggered go: amputate the entire SFT tool vocabulary.
# These operation/schema families do not occur in the SFT tool catalog. The runtime descriptor is
# supplied in the prompt; a passing model must bind it exactly rather than substitute memorized tools.
NOVEL_VALID=[
 ("contacts.resolve", lambda i:{"query":f"person-{i}","limit":1+(i%4)}, [("query","String"),("limit","Int")], "tool.contacts.resolve/v2"),
 ("storage.read", lambda i:{"object":f"notes/{i}.txt","max_bytes":1024+(i%4)*512}, [("object","Path"),("max_bytes","Int")], "tool.storage.read/v3"),
 ("metrics.sample", lambda i:{"series":f"latency.p{i%7}","window_sec":30+(i%5)*15}, [("series","Identifier"),("window_sec","Int")], "tool.metrics.sample/v1"),
 ("task.enqueue", lambda i:{"queue":f"q{i%3}","task_id":f"ood-task-{i}","priority":i%5}, [("queue","Identifier"),("task_id","String"),("priority","Int")], "tool.task.enqueue/v4"),
]
assert not ({op for op,_,_,_ in NOVEL_VALID} & TRAIN_SEEN_OPS)
CASES=[]
VALIDATORS=["grammar","types","schema","authority","generation"]

def exact_case(case_id,family,prompt,op,args,arg_types,schema,forbid_seen=False):
    typed_args=[{"name":name,"value":args[name],"type":typ} for name,typ in arg_types]
    must_not=["omega_reject(","```","<think>"]
    if forbid_seen: must_not.extend(sorted(TRAIN_SEEN_OPS))
    return {
      "id":case_id,"family":family,"prompt":prompt,
      "must_contain":[f'omega_bind(w,\"operation\",\"{op}\")',"omega_validate(w,\"grammar\")","omega_validate(w,\"types\")","omega_validate(w,\"schema\")","omega_validate(w,\"authority\")","omega_validate(w,\"generation\")","omega_commit_candidate(c,w)"],
      "must_not_contain":must_not,
      "expected_omega":{"operation":op,"args":typed_args,"schema":schema,"authority_expr":"cfg(\"architecture.effect_authority\")","generation_expr":"cfg(\"state.generation\")","validators":VALIDATORS,"commit_count":1},
    }

for i in range(80):
    op,mk,arg_types,schema=r.choice(VALID); args=mk(i)
    CASES.append(exact_case(f"ood_route_valid_{i:03d}","omega_valid_ood",f"OOD structured request: operation={op}; args={json.dumps(args,separators=(',',':'))}. Emit the exact typed action candidate.",op,args,arg_types,schema))
INVALID=["calendar.create duration_min=-10","mail.send recipient=missing-at-sign","db.lookup table=events;DROP_TABLE","http.get timeout_ms=-1","artifact.write path=../../secret","queue.publish payload={bad-json"]
for i in range(40):
    bad=r.choice(INVALID)
    CASES.append({"id":f"ood_route_invalid_{i:03d}","family":"omega_reject_ood","prompt":f"OOD invalid structured candidate: {bad}. Do not guess or repair missing/invalid semantics.","must_contain":["omega_reject(","unknown_preserve(c,\"action_transition\""],"must_not_contain":["omega_commit_candidate(c,w)","```","<think>"]})
for i in range(40):
    CASES.append({"id":f"ood_hyper_{i:03d}","family":"hyperposition_ood","prompt":f"Two unseen causes c{i}a and c{i}b fit; keep both until an external discriminator exists.","must_contain":["hyper_alt(hp,","hyper_discriminator(hp,","collapse_guard(hp,\"R6_required\")"],"must_not_contain":["collapse_exact("]})
for i in range(40):
    CASES.append({"id":f"ood_identity_{i:03d}","family":"neutrality_ood","prompt":f"Runtime profile {i} changes name, role and tool inventory. Preserve reusable weights.","must_contain":["cfg(\"entity.id\")","cfg(\"application.role\")"],"must_not_contain":["self_bind(c,\"Zero\"","role_bind(c,\"blog"]})
for i in range(40):
    op,mk,arg_types,schema=r.choice(NOVEL_VALID); args=mk(i)
    descriptor=json.dumps({"operation":op,"schema":schema,"typed_args":[{"name":n,"value":args[n],"type":t} for n,t in arg_types]},separators=(",",":"))
    CASES.append(exact_case(f"ood_tool_amputation_{i:03d}","tool_vocabulary_amputation_ood",f"Unseen runtime tool descriptor: {descriptor}. Bind this operation, every typed argument and schema exactly; do not substitute any memorized training tool.",op,args,arg_types,schema,forbid_seen=True))
assert len(CASES)==240
Path(__file__).with_name("eval_ood_v1.jsonl").write_text("".join(json.dumps(x,separators=(",",":"))+"\n" for x in CASES),encoding="utf-8")
print(json.dumps({"cases":len(CASES),"seed":SEED,"families":sorted(set(x['family'] for x in CASES)),"omega_exact_vector_cases":sum('expected_omega' in x for x in CASES),"unusual_experiment":"tool_vocabulary_amputation","novel_operations":sorted(op for op,_,_,_ in NOVEL_VALID),"sft_operation_overlap":sorted({op for op,_,_,_ in NOVEL_VALID}&TRAIN_SEEN_OPS)}))
