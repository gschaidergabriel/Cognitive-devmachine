#!/usr/bin/env python3
"""Score ClayCode structural-transfer outputs without executing any proposed action.

Expected outputs JSONL: {"id":...,"output":...}. The scorer first applies the hardened
ClayCode structural validator, then checks action semantics against the *actual* omega
variable chosen by the model rather than requiring one memorized variable name.
"""
import json, re, sys
from pathlib import Path
from validate_sft_v1 import OMEGA_GATES, validate_code

IDENT=r'[A-Za-z_][A-Za-z0-9_]*'


def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def q(v):
    return json.dumps(v,ensure_ascii=False,separators=(",",":"))


def has_line(s,line):
    return any(x.strip()==line for x in s.splitlines())


def committed_var(s):
    xs=re.findall(rf'^\s*omega_commit_candidate\(c,({IDENT})\)\s*$',s,re.MULTILINE)
    return xs[0] if len(xs)==1 else None


def rejected_vars(s):
    return re.findall(rf'^\s*omega_reject\(({IDENT}),',s,re.MULTILINE)


def valid_omega(spec,out):
    w=committed_var(out)
    if not w:
        return False
    if not has_line(out,f'omega_bind({w},"operation",{q(spec["operation"])})'):
        return False
    if not has_line(out,f'omega_schema({w},{q(spec["schema"])})'):
        return False
    if not re.search(rf'^\s*omega_authority\({re.escape(w)},',out,re.MULTILINE):
        return False
    if not re.search(rf'^\s*omega_generation\({re.escape(w)},',out,re.MULTILINE):
        return False
    for gate in OMEGA_GATES:
        if not has_line(out,f'omega_validate({w},{q(gate)})'):
            return False
    for a in spec["args"]:
        if not has_line(out,f'omega_arg({w},{q(a["name"])},{q(a["value"])},{q(a["type"])})'):
            return False
    return True


def invalid_omega(spec,out):
    if committed_var(out) is not None:
        return False
    ws=rejected_vars(out)
    if len(ws)!=1:
        return False
    w=ws[0]
    if not has_line(out,f'omega_bind({w},"operation",{q(spec["operation"])})'):
        return False
    a=spec["invalid_arg"]
    if not has_line(out,f'omega_arg({w},{q(a["name"])},{q(a["value"])},{q(a["type"])})'):
        return False
    return 'unknown_preserve(c,"action_transition"' in out


def hyper_open(spec,out):
    if 'collapse_exact(' in out:
        return False
    for alt in spec["alternatives"]:
        if not re.search(rf'^\s*hyper_alt\([^,]+,{re.escape(q(alt))},',out,re.MULTILINE):
            return False
    if not re.search(rf'^\s*hyper_discriminator\([^,]+,{re.escape(q(spec["discriminator"]))}\)\s*$',out,re.MULTILINE):
        return False
    return 'collapse_guard(' in out and '"R6_required"' in out


def neutrality(out):
    required=(
        'self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
        'role_bind(c,cfg("application.role"))',
        'goal_bind(c,cfg("application.goal"))',
        'personality_bind(c,cfg("application.personality"))',
    )
    forbidden=('self_bind(c,"Zero"','role_bind(c,"blog','goal_bind(c,"write blog"')
    return all(x in out for x in required) and not any(x in out for x in forbidden)


def semantic_ok(spec,out):
    kind=spec["kind"]
    if kind=="omega_valid": return valid_omega(spec,out)
    if kind=="omega_reject": return invalid_omega(spec,out)
    if kind=="hyper_open": return hyper_open(spec,out)
    if kind=="neutrality": return neutrality(out)
    raise ValueError(kind)


def main(spec_path,outputs_path):
    specs={x["id"]:x for x in load(spec_path)}
    outs={x["id"]:x["output"] for x in load(outputs_path)}
    structural=semantic=0; missing=[]; by={}
    for cid,s in specs.items():
        o=outs.get(cid)
        if o is None:
            missing.append(cid); continue
        st=not validate_code(o)
        sem=st and semantic_ok(s,o)
        structural+=int(st); semantic+=int(sem)
        fam=s["family"]
        by.setdefault(fam,[0,0,0]); by[fam][0]+=1; by[fam][1]+=int(st); by[fam][2]+=int(sem)
    n=len(specs)
    report={
        "schema":"claycog-structural-transfer-score/v2",
        "total":n,"provided":len(outs),"missing":len(missing),
        "strict_claycode_rate":structural/n if n else 0,
        "structural_transfer_rate":semantic/n if n else 0,
        "by_family":{k:{"n":v[0],"strict":v[1]/v[0],"transfer":v[2]/v[0]} for k,v in sorted(by.items())},
        "promotion_gate":{"strict_claycode_rate":1.0,"structural_transfer_rate":0.95,"missing":0},
        "note":"proposal scoring only; no omega action is executed",
    }
    print(json.dumps(report,indent=2))
    return 0 if structural==n and semantic/n>=.95 and not missing else 1

if __name__=="__main__": raise SystemExit(main(sys.argv[1],sys.argv[2]))
