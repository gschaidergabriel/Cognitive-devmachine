#!/usr/bin/env python3
import argparse, hashlib, json, re
from pathlib import Path

PREFIX='module clay.cog.turn\nfn think(i:Map)->Map {\n'
REQUIRED=(
  'self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
  'role_bind(c,cfg("application.role"))',
  'goal_bind(c,cfg("application.goal"))',
  'personality_bind(c,cfg("application.personality"))',
  'return c\n}',
)
FORBIDDEN=('```','<think>','</think>','omega_execute(','tool_execute(','api_call(')
OMEGA_GATES=("grammar","types","schema","authority","generation")
RESERVED_LITERAL_KEYS={"name","entity_id","entity.id","identity","role","job","goal","personality","persona","audience","application"}
LITERAL_STATE_RE=re.compile(r'\b(?:self_state|state_note|arch_bind)\(c,"([^"]+)",("(?:[^"\\]|\\.)*")')

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
    e=[]
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    structural=outside_strings(s)
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")
    for x in REQUIRED:
        if x not in s: e.append("missing:"+x)
    low=s.lower()
    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)
    for m in LITERAL_STATE_RE.finditer(s):
        key=m.group(1).lower()
        if key in RESERVED_LITERAL_KEYS:
            e.append("weight_literal_reserved_key:"+key)
    if "omega_commit_candidate(" in s:
        for g in OMEGA_GATES:
            if f'omega_validate(w,"{g}")' not in s: e.append("omega_missing_gate:"+g)
        if 'omega_authority(w,' not in s: e.append("omega_missing_authority")
        if 'omega_generation(w,' not in s: e.append("omega_missing_generation")
    if "omega_reject(" in s and "omega_commit_candidate(" in s: e.append("reject_and_commit")
    return e

def fp_messages(messages):
    raw=json.dumps(messages,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()

def load(path):
    rows=[]; bad=0
    for no,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        try:
            row=json.loads(line); ms=row["messages"]
            if [m["role"] for m in ms] != ["system","user","assistant"]: raise ValueError("role order")
            errors=validate_code(ms[-1]["content"])
            if errors: bad+=1; print(no,errors)
            rows.append(ms)
        except Exception as exc:
            bad+=1; print(no,"schema",repr(exc))
    return rows,bad

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); ap.add_argument("--against")
    args=ap.parse_args(); rows,bad=load(args.path); fps=[fp_messages(x) for x in rows]
    duplicate_rows=len(fps)-len(set(fps)); overlap=0
    if args.against:
        other,other_bad=load(args.against); bad+=other_bad; overlap=len(set(fps)&{fp_messages(x) for x in other})
    report={"lines":len(rows),"structural_bad":bad,"duplicate_rows":duplicate_rows,"cross_overlap":overlap,"ok":bad==0 and duplicate_rows==0 and overlap==0}
    print(json.dumps(report,sort_keys=True))
    return 0 if report["ok"] else 1

if __name__=="__main__": raise SystemExit(main())
