#!/usr/bin/env python3
"""Score saved model completions without executing any proposed action.
Expected JSONL: {"id":..., "output":...}. OOD specs are generated separately.
"""
import json, sys
from pathlib import Path
from validate_sft_v1 import (
    validate_code, semantic_token_present, semantic_token_absent, semantic_token_count,
)

def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def semantic_match(output, spec):
    if not all(semantic_token_present(output,x) for x in spec.get("must_contain",[])): return False
    if not all(semantic_token_absent(output,x) for x in spec.get("must_not_contain",[])): return False
    for token,n in spec.get("min_occurrences",{}).items():
        if semantic_token_count(output,token) < int(n): return False
    for token,n in spec.get("max_occurrences",{}).items():
        if semantic_token_count(output,token) > int(n): return False
    return True

def main(spec_path, outputs_path):
    specs={x["id"]:x for x in load(spec_path)}
    outs={x["id"]:x["output"] for x in load(outputs_path)}
    total=len(specs); strict=semantic=0; missing=[]; by={}
    for i,s in specs.items():
        o=outs.get(i)
        if o is None:
            missing.append(i); continue
        structural=(validate_code(o)==[])
        semantic_ok=semantic_match(o,s)
        strict+=int(structural); semantic+=int(structural and semantic_ok)
        fam=s["family"]; by.setdefault(fam,[0,0,0]); by[fam][0]+=1; by[fam][1]+=int(structural); by[fam][2]+=int(structural and semantic_ok)
    report={
      "total":total,"provided":len(outs),"missing":len(missing),
      "strict_claycode_rate":strict/total if total else 0,
      "semantic_gate_rate":semantic/total if total else 0,
      "by_family":{k:{"n":v[0],"strict":v[1]/v[0],"semantic":v[2]/v[0]} for k,v in by.items()},
      "promotion_requires":{"strict_claycode_rate":1.0,"semantic_gate_rate":0.95},
      "semantic_matcher":"comment_aware_active_statement_v2",
    }
    print(json.dumps(report,indent=2))
    return 0 if report["strict_claycode_rate"]==1 and report["semantic_gate_rate"]>=.95 and not missing else 1

if __name__=="__main__": raise SystemExit(main(sys.argv[1],sys.argv[2]))
