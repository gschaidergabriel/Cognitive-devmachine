#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from preimage_guard import evaluate, sha256_text
from source_identity import identity
from split_guard import adjudicate, load
from validate import validate_obj
from receipt import make_receipt

TESTS=[]
def check(component,name,cond):
    TESTS.append((component,name,bool(cond)))
    if not cond: raise AssertionError(f"{component}:{name}")

def jline(obj): return json.dumps(obj,ensure_ascii=False)+"\n"

def main()->int:
    # 1. preimage guard: one positive + one negative
    pre="a\nb\nc\n"; good="a\nB\nc\n"; bad="A\nb\nc\n"; h=sha256_text(pre)
    check("preimage_guard","positive",evaluate("x.txt",pre,good,h,[[2,2]])["pass"])
    check("preimage_guard","negative",not evaluate("x.txt",pre,bad,h,[[2,2]])["pass"])

    # 2. source identity: clean positive + dirty negative using a throwaway git repo
    with tempfile.TemporaryDirectory() as td:
        r=Path(td); subprocess.run(["git","init","-q",str(r)],check=True)
        subprocess.run(["git","-C",str(r),"config","user.email","selftest@example.invalid"],check=True)
        subprocess.run(["git","-C",str(r),"config","user.name","Acceptance Kit Selftest"],check=True)
        (r/"a.txt").write_text("alpha\n",encoding="utf-8"); subprocess.run(["git","-C",str(r),"add","a.txt"],check=True); subprocess.run(["git","-C",str(r),"commit","-qm","init"],check=True)
        check("source_identity","positive",identity(r)["dirty_state"]["dirty"] is False)
        (r/"a.txt").write_text("beta\n",encoding="utf-8")
        check("source_identity","negative",identity(r)["dirty_state"]["dirty"] is True)

    # 3. split guard: fixtures adapted directly from oMEGAcV1 needle task T-0074 input rows.
    with tempfile.TemporaryDirectory() as td:
        r=Path(td)
        train={"id":"ud0c89f294f44","text":"Zwei Wochen ohne deine Stimme, walking in the park like a Ghost."}
        val={"id":"u2b038323932b","text":"i need a chorus for a song about loving something that’s already gone"}
        hold={"id":"u612a5d626df2","text":"does love survive beyond myths?"}
        for name,row in (("tr",train),("va",val),("ho",hold)): (r/f"{name}.jsonl").write_text(jline(row),encoding="utf-8")
        clean=adjudicate({"TRAIN":load(r/"tr.jsonl"),"VALIDATION":load(r/"va.jsonl"),"HOLDOUT":load(r/"ho.jsonl")})
        check("split_guard","positive",clean["pass"])
        (r/"ho.jsonl").write_text(jline({"id":"u-new","text":train["text"]}),encoding="utf-8")
        leaked=adjudicate({"TRAIN":load(r/"tr.jsonl"),"VALIDATION":load(r/"va.jsonl"),"HOLDOUT":load(r/"ho.jsonl")})
        check("split_guard","negative",not leaked["pass"] and any(x.startswith("TEXT_OVERLAP") for x in leaked["failures"]))

    # 4. Draft 2020-12 schemas: valid and invalid cases for both schemas.
    hex64="a"*64
    packet={"schema":"NEEDLE_ENTITY_PACKET/v1","task_id":"task-x","spec_sha256":hex64,"inputs":[{"id":"x1","text":"hello"}]}
    result={"schema":"needle-entity-result/v1","task_id":"task-x","spec_sha256":hex64,"outputs_sha256":{"out.jsonl":hex64},"environment":{"kind":"sandbox"},"fidelity":"approximate","status":"PASS"}
    check("schema_packet","positive",validate_obj("packet",packet)==[])
    bad_packet=dict(packet); bad_packet.pop("spec_sha256")
    check("schema_packet","negative",bool(validate_obj("packet",bad_packet)))
    check("schema_result","positive",validate_obj("result",result)==[])
    bad_result=dict(result); bad_result["fidelity"]="final"
    check("schema_result","negative",bool(validate_obj("result",bad_result)))

    # 5. receipt: zero credit positive + forbidden nonzero negative.
    rcpt=make_receipt(command="python3 run_selftest.py",exit_code=0,tested_blobs={"x":hex64},unproven_layers=["TARGET_RUNTIME"],runtime_credit=0)
    check("receipt","positive",rcpt["runtime_credit"]==0 and rcpt["verdict"]=="PASS")
    rejected=False
    try: make_receipt(command="x",exit_code=0,tested_blobs={"x":hex64},unproven_layers=["TARGET_RUNTIME"],runtime_credit=1)
    except ValueError: rejected=True
    check("receipt","negative",rejected)

    by={}
    for component,name,ok in TESTS: by.setdefault(component,[]).append({"name":name,"pass":ok})
    components={k:{"positive":any(t["name"]=="positive" and t["pass"] for t in v),"negative":any(t["name"]=="negative" and t["pass"] for t in v)} for k,v in by.items()}
    overall=all(x["positive"] and x["negative"] for x in components.values())
    print(json.dumps({"schema":"ACCEPTANCE_KIT_SELFTEST/v1","pass":overall,"components":components,"tests":len(TESTS)},sort_keys=True))
    return 0 if overall else 1
if __name__=="__main__": raise SystemExit(main())
