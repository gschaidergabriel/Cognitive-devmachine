#!/usr/bin/env python3
"""Score saved model completions without executing any proposed action.

Preserves exact-omega-vector and ID-integrity gates from #802. OOD specs may additionally
set promotion_min_semantic_rate on cases; the strictest value in each family becomes a
hard per-family promotion requirement, preventing a high global average from masking a
catastrophic critical-family failure.
"""
import json, sys
from pathlib import Path
from validate_sft_v1 import validate_code

def load(path): return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
def q(v): return json.dumps(v,ensure_ascii=False,separators=(",",":"))

def exact_omega_ok(output,expected):
    operation=expected["operation"]; args=expected["args"]; schema=expected["schema"]; authority_expr=expected["authority_expr"]; generation_expr=expected["generation_expr"]; validators=expected["validators"]
    required=[f'omega_bind(w,"operation",{q(operation)})',f'omega_schema(w,{q(schema)})',f'omega_authority(w,{authority_expr})',f'omega_generation(w,{generation_expr})','omega_commit_candidate(c,w)']
    required.extend(f'omega_arg(w,{q(a["name"])},{q(a["value"])},{q(a["type"])})' for a in args)
    required.extend(f'omega_validate(w,{q(g)})' for g in validators)
    if any(output.count(x)!=1 for x in required): return False
    if output.count('omega_bind(w,"operation",')!=1:return False
    if output.count('omega_arg(w,')!=len(args):return False
    if output.count('omega_schema(w,')!=1 or output.count('omega_authority(w,')!=1 or output.count('omega_generation(w,')!=1:return False
    if output.count('omega_validate(w,')!=len(validators):return False
    if output.count('omega_commit_candidate(c,w)')!=int(expected.get("commit_count",1)):return False
    if 'omega_reject(' in output:return False
    return True

def semantic_ok(output,spec):
    if not (all(x in output for x in spec["must_contain"]) and all(x not in output for x in spec["must_not_contain"])):return False
    expected=spec.get("expected_omega")
    if expected is not None and not exact_omega_ok(output,expected):return False
    return True

def main(spec_path,outputs_path):
    spec_rows=load(spec_path); out_rows=load(outputs_path)
    spec_ids=[x["id"] for x in spec_rows]; out_ids=[x["id"] for x in out_rows]
    duplicate_spec_ids=sorted({x for x in spec_ids if spec_ids.count(x)>1}); duplicate_output_ids=sorted({x for x in out_ids if out_ids.count(x)>1})
    specs={x["id"]:x for x in spec_rows}; outs={x["id"]:x["output"] for x in out_rows}; unknown_output_ids=sorted(set(outs)-set(specs))
    total=len(specs); strict=semantic=0; missing=[]; by={}; family_min={}
    for s in spec_rows:
        if "promotion_min_semantic_rate" in s:
            fam=s["family"]; req=float(s["promotion_min_semantic_rate"])
            if not 0<=req<=1: raise SystemExit(f"invalid promotion_min_semantic_rate for {fam}: {req}")
            family_min[fam]=max(family_min.get(fam,0.0),req)
    for i,s in specs.items():
        fam=s["family"]; by.setdefault(fam,[0,0,0]); by[fam][0]+=1; o=outs.get(i)
        if o is None: missing.append(i); continue
        structural=(validate_code(o)==[]); sem=semantic_ok(o,s); strict+=int(structural); semantic+=int(structural and sem); by[fam][1]+=int(structural); by[fam][2]+=int(structural and sem)
    family_report={k:{"n":v[0],"strict":v[1]/v[0],"semantic":v[2]/v[0]} for k,v in by.items()}
    family_failures={fam:{"required":req,"actual":family_report.get(fam,{}).get("semantic",0.0)} for fam,req in sorted(family_min.items()) if family_report.get(fam,{}).get("semantic",0.0)<req}
    report={"total":total,"provided_rows":len(out_rows),"provided_unique":len(outs),"missing":len(missing),"duplicate_spec_ids":duplicate_spec_ids,"duplicate_output_ids":duplicate_output_ids,"unknown_output_ids":unknown_output_ids,"strict_claycode_rate":strict/total if total else 0,"semantic_gate_rate":semantic/total if total else 0,"by_family":family_report,"family_semantic_minimums":dict(sorted(family_min.items())),"family_semantic_failures":family_failures,"promotion_requires":{"strict_claycode_rate":1.0,"semantic_gate_rate":0.95,"exact_omega_vector":True,"no_duplicate_or_unknown_ids":True,"declared_family_minima":True}}
    print(json.dumps(report,indent=2)); clean_ids=not duplicate_spec_ids and not duplicate_output_ids and not unknown_output_ids
    return 0 if report["strict_claycode_rate"]==1 and report["semantic_gate_rate"]>=.95 and not missing and clean_ids and not family_failures else 1
if __name__=="__main__": raise SystemExit(main(sys.argv[1],sys.argv[2]))
