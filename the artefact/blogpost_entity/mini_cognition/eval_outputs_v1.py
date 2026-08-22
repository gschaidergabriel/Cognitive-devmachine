#!/usr/bin/env python3
"""Score saved model completions without executing any proposed action."""
import json, sys
from collections import Counter
from pathlib import Path
from validate_sft_v1 import validate_code

def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def q(v):
    return json.dumps(v, ensure_ascii=False, separators=(",",":"))

def exact_omega_ok(spec, output):
    expected=spec.get("expected_omega")
    if not expected:
        return True
    stripped=[line.strip() for line in output.splitlines()]
    op_line=f'omega_bind(w,"operation",{q(expected["operation"])})'
    schema_line=f'omega_schema(w,{q(expected["schema"])})'
    expected_args=[f'omega_arg(w,{q(a["name"])},{q(a["value"])},{q(a["type"])})' for a in expected["args"]]
    actual_args=[line for line in stripped if line.startswith("omega_arg(w,")]
    return (
        stripped.count(op_line)==1
        and stripped.count(schema_line)==1
        and Counter(actual_args)==Counter(expected_args)
    )

def unique_index(rows, label):
    out={}; duplicates=[]
    for row in rows:
        i=row["id"]
        if i in out: duplicates.append(i)
        out[i]=row
    return out, sorted(set(duplicates))

def score(spec_path, outputs_path):
    specs, spec_duplicates=unique_index(load(spec_path),"spec")
    outs_rows=load(outputs_path); outs, output_duplicates=unique_index(outs_rows,"output")
    if spec_duplicates:
        raise ValueError(f"duplicate spec ids: {spec_duplicates}")
    total=len(specs); strict=semantic=0; missing=[]; by={}
    omega_total=omega_exact=0
    unexpected=sorted(set(outs)-set(specs))
    for i,s in specs.items():
        row=outs.get(i); o=None if row is None else row["output"]
        if o is None:
            missing.append(i); continue
        structural=(validate_code(o)==[])
        vector_ok=exact_omega_ok(s,o)
        if s.get("expected_omega"):
            omega_total+=1; omega_exact+=int(structural and vector_ok)
        semantic_ok=(
            all(x in o for x in s["must_contain"])
            and all(x not in o for x in s["must_not_contain"])
            and vector_ok
        )
        strict+=int(structural); semantic+=int(structural and semantic_ok)
        fam=s["family"]; by.setdefault(fam,[0,0,0]); by[fam][0]+=1; by[fam][1]+=int(structural); by[fam][2]+=int(structural and semantic_ok)
    report={
      "total":total,"provided":len(outs),"missing":len(missing),
      "duplicate_output_ids":output_duplicates,"unexpected_output_ids":unexpected,
      "strict_claycode_rate":strict/total if total else 0,
      "semantic_gate_rate":semantic/total if total else 0,
      "omega_exact_vector_rate":omega_exact/omega_total if omega_total else 1.0,
      "by_family":{k:{"n":v[0],"strict":v[1]/v[0],"semantic":v[2]/v[0]} for k,v in by.items()},
      "promotion_requires":{"strict_claycode_rate":1.0,"semantic_gate_rate":0.95,"omega_exact_vector_rate":1.0,"no_duplicate_or_unexpected_ids":True},
    }
    return report

def main(spec_path, outputs_path):
    report=score(spec_path,outputs_path)
    print(json.dumps(report,indent=2))
    ok=(report["strict_claycode_rate"]==1 and report["semantic_gate_rate"]>=.95 and report["omega_exact_vector_rate"]==1 and report["missing"]==0 and not report["duplicate_output_ids"] and not report["unexpected_output_ids"])
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main(sys.argv[1],sys.argv[2]))
