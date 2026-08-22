#!/usr/bin/env python3
"""Score saved completions without executing any proposed action."""
import json, sys
from pathlib import Path
from validate_sft_v2 import validate_code

def load(path): return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
def main(spec_path, outputs_path):
    specs={x["id"]:x for x in load(spec_path)}; outs={x["id"]:x["output"] for x in load(outputs_path)}
    total=len(specs); strict=semantic=0; missing=[]; by={}
    for i,s in specs.items():
        o=outs.get(i)
        if o is None: missing.append(i); continue
        structural=(validate_code(o)==[])
        semantic_ok=all(x in o for x in s["must_contain"]) and all(x not in o for x in s["must_not_contain"])
        strict+=int(structural); semantic+=int(structural and semantic_ok)
        fam=s["family"]; by.setdefault(fam,[0,0,0]); by[fam][0]+=1; by[fam][1]+=int(structural); by[fam][2]+=int(structural and semantic_ok)
    report={"total":total,"provided":len(outs),"missing":len(missing),"strict_claycode_rate":strict/total if total else 0,"semantic_gate_rate":semantic/total if total else 0,"by_family":{k:{"n":v[0],"strict":v[1]/v[0],"semantic":v[2]/v[0]} for k,v in by.items()},"promotion_requires":{"strict_claycode_rate":1.0,"semantic_gate_rate":0.95,"identity_literal_leakage":0}}
    print(json.dumps(report,indent=2)); return 0 if report["strict_claycode_rate"]==1 and report["semantic_gate_rate"]>=.95 and not missing else 1
if __name__=="__main__": raise SystemExit(main(sys.argv[1],sys.argv[2]))
