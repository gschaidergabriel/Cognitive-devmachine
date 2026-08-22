#!/usr/bin/env python3
import hashlib, json, sys
from pathlib import Path
PREFIX='module clay.cog.turn\nfn think(i:Map)->Map {\n'
REQUIRED=('self_bind(c,cfg("entity.id"),cfg("entity.continuity"))','role_bind(c,cfg("application.role"))','goal_bind(c,cfg("application.goal"))','personality_bind(c,cfg("application.personality"))','return c\n}')
FORBIDDEN=('```','<think>','</think>','self_bind(c,"zero"','self_bind(c,"mini_entity"','role_bind(c,"blog','goal_bind(c,"write blog','personality_bind(c,"zero"','omega_execute(','tool_execute(','api_call(')
GATES=("grammar","types","schema","authority","generation")
def outside_strings(s):
    out=[]; quoted=False; esc=False
    for ch in s:
        if quoted:
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch=='"': quoted=False
            out.append(" ")
        else:
            if ch=='"': quoted=True; out.append(" ")
            else: out.append(ch)
    return "".join(out)
def validate_code(s):
    e=[]; low=s.lower(); structural=outside_strings(s)
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")
    for x in REQUIRED:
        if x not in s: e.append("missing:"+x)
    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)
    if "omega_commit_candidate(" in s:
        for g in GATES:
            if f'omega_validate(w,"{g}")' not in s: e.append("omega_missing_gate:"+g)
        if 'omega_authority(w,' not in s: e.append("omega_missing_authority")
        if 'omega_generation(w,' not in s: e.append("omega_missing_generation")
    if "omega_reject(" in s and "omega_commit_candidate(" in s: e.append("reject_and_commit")
    return e
def load(path):
    rows=[]; bad=[]
    for no,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        try:
            row=json.loads(line); ms=row["messages"]
            if [m["role"] for m in ms] != ["system","user","assistant"]: raise ValueError("role order")
            errs=validate_code(ms[-1]["content"])
            if errs: bad.append((no,errs))
            rows.append(row)
        except Exception as exc: bad.append((no,["schema:"+repr(exc)]))
    return rows,bad
def canon(x): return json.dumps(x["messages"],ensure_ascii=False,separators=(",",":"))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(trp,vap):
    tr,tbad=load(trp); va,vbad=load(vap)
    tc=[canon(x) for x in tr]; vc=[canon(x) for x in va]
    tp={x["messages"][1]["content"] for x in tr}; vp={x["messages"][1]["content"] for x in va}
    r={"schema":"claycog-corpus-validation/v2","train_lines":len(tr),"validation_lines":len(va),
       "train_structural_invalid":len(tbad),"validation_structural_invalid":len(vbad),
       "train_unique":len(set(tc)),"validation_unique":len(set(vc)),
       "exact_cross_split_overlap":len(set(tc)&set(vc)),"prompt_cross_split_overlap":len(tp&vp),
       "train_sha256":sha(trp),"validation_sha256":sha(vap)}
    r["ok"]=(len(tr)==1485 and len(va)==165 and not tbad and not vbad and len(set(tc))==len(tc) and len(set(vc))==len(vc) and r["exact_cross_split_overlap"]==0 and r["prompt_cross_split_overlap"]==0)
    print(json.dumps(r,indent=2,sort_keys=True))
    return 0 if r["ok"] else 1
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: validate_corpus_v2.py train.jsonl validation.jsonl")
    raise SystemExit(main(sys.argv[1],sys.argv[2]))
