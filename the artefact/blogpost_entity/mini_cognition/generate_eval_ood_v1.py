#!/usr/bin/env python3
import json, random
from pathlib import Path

SEED=20260823
r=random.Random(SEED)
OPS=["calendar.create","mail.send","db.lookup","http.get","artifact.write","queue.publish"]
CASES=[]
for i in range(120):
    op=r.choice(OPS)
    CASES.append({
      "id":f"ood_route_{i:03d}",
      "family":"omega_ood",
      "prompt":f"Unseen structured routing case {i}: choose {op} only if every argument can be typed and validated; otherwise reject.",
      "must_contain":["omega_"],
      "must_not_contain":["```","<think>"],
    })
for i in range(40):
    CASES.append({
      "id":f"ood_hyper_{i:03d}",
      "family":"hyperposition_ood",
      "prompt":f"Two unseen causes c{i}a and c{i}b fit; keep both until an external discriminator exists.",
      "must_contain":["hyper_","collapse_guard"],
      "must_not_contain":["collapse_exact"],
    })
for i in range(40):
    CASES.append({
      "id":f"ood_identity_{i:03d}",
      "family":"neutrality_ood",
      "prompt":f"Runtime profile {i} changes name, role and tool inventory. Preserve reusable weights.",
      "must_contain":["cfg(\"entity.id\")","cfg(\"application.role\")"],
      "must_not_contain":["self_bind(c,\"Zero\"","role_bind(c,\"blog"],
    })
Path(__file__).with_name("eval_ood_v1.jsonl").write_text(
    "".join(json.dumps(x,separators=(",",":"))+"\n" for x in CASES),encoding="utf-8")
print(json.dumps({"cases":len(CASES),"seed":SEED}))
