#!/usr/bin/env python3
import json, sys
from pathlib import Path

PREFIX='module clay.cog.turn\nfn think(i:Map)->Map {\n'
REQUIRED_STATEMENTS=(
  'self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
  'role_bind(c,cfg("application.role"))',
  'goal_bind(c,cfg("application.goal"))',
  'personality_bind(c,cfg("application.personality"))',
  'return c',
)
FORBIDDEN=(
  '```','<think>','</think>',
  'self_bind(c,"zero"','self_bind(c,"mini_entity"',
  'role_bind(c,"blog','goal_bind(c,"write blog','personality_bind(c,"zero"',
  'omega_execute(','tool_execute(','api_call(',
)
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
    return "".join(out)

def statement_lines(s):
    """Return standalone ClayCode statements; reject strings spanning line boundaries."""
    lines=[]
    for raw in s.splitlines():
        quoted=False; esc=False
        for ch in raw:
            if quoted:
                if esc:
                    esc=False
                elif ch=="\\":
                    esc=True
                elif ch=='"':
                    quoted=False
            elif ch=='"':
                quoted=True
        if quoted or esc:
            return None
        stripped=raw.strip()
        if stripped:
            lines.append(stripped)
    return tuple(lines)

def has_call(lines,prefix):
    return any(line.startswith(prefix) and line.endswith(")") for line in lines)

def validate_code(s):
    e=[]; low=s.lower()
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    structural=outside_strings(s)
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")
    statements=statement_lines(s)
    if statements is None:
        e.append("multiline_or_unclosed_string")
        statements=()
    for x in REQUIRED_STATEMENTS:
        if x not in statements: e.append("missing_statement:"+x)
    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)
    has_commit="omega_commit_candidate(c,w)" in statements
    has_reject=has_call(statements,"omega_reject(")
    if has_commit:
        for g in OMEGA_GATES:
            if f'omega_validate(w,"{g}")' not in statements: e.append("omega_missing_gate:"+g)
        if not has_call(statements,'omega_authority(w,'): e.append("omega_missing_authority")
        if not has_call(statements,'omega_generation(w,'): e.append("omega_missing_generation")
    if has_reject and has_commit:
        e.append("reject_and_commit")
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
    print(json.dumps({"lines":n,"bad":bad,"ok":bad==0}))
    return 1 if bad else 0

if __name__=="__main__": raise SystemExit(main(sys.argv[1]))
