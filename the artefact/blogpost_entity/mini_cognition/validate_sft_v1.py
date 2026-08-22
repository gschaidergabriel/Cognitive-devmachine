#!/usr/bin/env python3
import json, sys
from pathlib import Path
from claycode_calls_v2 import call_set, fn_counts

PREFIX='module clay.cog.turn\nfn think(i:Map)->Map {\n'
BINDINGS=(
  ('self_bind','self_bind(c,cfg("entity.id"),cfg("entity.continuity"))'),
  ('role_bind','role_bind(c,cfg("application.role"))'),
  ('goal_bind','goal_bind(c,cfg("application.goal"))'),
  ('personality_bind','personality_bind(c,cfg("application.personality"))'),
)
REQUIRED=tuple(x[1] for x in BINDINGS)+('return c\n}',)
FORBIDDEN=('```','<think>','</think>','self_bind(c,"zero"','self_bind(c,"mini_entity"','role_bind(c,"blog','goal_bind(c,"write blog','personality_bind(c,"zero"','omega_execute(','tool_execute(','api_call(',)
OMEGA_GATES=("grammar","types","schema","authority","generation")
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
    return "".join(out), quoted
def validate_code(s):
    e=[]; low=s.lower()
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    structural, unterminated_string=outside_strings(s); compact_structural=''.join(structural.split())
    if unterminated_string: e.append("unterminated_string")
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")
    lines=[line.strip() for line in s.splitlines()]
    for name,canonical in BINDINGS:
        call_count=compact_structural.count(name+'('); canonical_count=lines.count(canonical)
        if call_count != 1: e.append(f"binding_call_count:{name}:{call_count}")
        if canonical_count != 1: e.append(f"binding_not_exact_runtime_cfg:{name}:{canonical_count}")
    for x in REQUIRED:
        if x not in s: e.append("missing:"+x)
    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)
    calls=call_set(s); counts=fn_counts(s)
    if counts.get('omega_commit_candidate',0):
        if 'omega_commit_candidate(c,w)' not in calls: e.append('omega_bad_commit_signature')
        for g in OMEGA_GATES:
            if f'omega_validate(w,"{g}")' not in calls: e.append("omega_missing_gate:"+g)
        if counts.get('omega_schema',0)==0: e.append('omega_missing_schema')
        if counts.get('omega_authority',0)==0: e.append("omega_missing_authority")
        if counts.get('omega_generation',0)==0: e.append("omega_missing_generation")
    if counts.get('omega_reject',0) and counts.get('omega_commit_candidate',0): e.append("reject_and_commit")
    return e
def main(path):
    n=bad=0
    for no,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        n+=1
        try:
            row=json.loads(line); ms=row["messages"]
            if [m["role"] for m in ms] != ["system","user","assistant"]: raise ValueError("role order")
            errors=validate_code(ms[-1]["content"])
            if errors: bad+=1; print(no,errors)
        except Exception as exc:
            bad+=1; print(no,"schema",repr(exc))
    print(json.dumps({"lines":n,"bad":bad,"ok":bad==0})); return 1 if bad else 0
if __name__=="__main__": raise SystemExit(main(sys.argv[1]))
