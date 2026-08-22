#!/usr/bin/env python3
import json, sys
from pathlib import Path
from intrinsics_v1 import INTRINSIC_ARITY

PREFIX='module clay.cog.turn\nfn think(i:Map)->Map {\n'
BINDINGS=(
  ('self_bind','self_bind(c,cfg("entity.id"),cfg("entity.continuity"))'),
  ('role_bind','role_bind(c,cfg("application.role"))'),
  ('goal_bind','goal_bind(c,cfg("application.goal"))'),
  ('personality_bind','personality_bind(c,cfg("application.personality"))'),
)
REQUIRED=tuple(x[1] for x in BINDINGS)+(
  'return c\n}',
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
    return "".join(out), quoted

def structural_calls_source(s):
    """Mask literal payload/punctuation but retain one passive token per string argument."""
    out=[]; quoted=False; esc=False
    for ch in s:
        if quoted:
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch=='"': quoted=False
            out.append(" ")
        else:
            if ch=='"': quoted=True; out.append("_")
            else: out.append(ch)
    return "".join(out),quoted

def _call_arity(structural,open_pos):
    depth=1; commas=0; saw=False; i=open_pos+1
    while i<len(structural):
        ch=structural[i]
        if ch=='(':
            depth+=1
            if depth==2: saw=True
        elif ch==')':
            depth-=1
            if depth==0: return 0 if not saw else commas+1
        elif depth==1:
            if ch==',': commas+=1
            elif not ch.isspace(): saw=True
        i+=1
    return None

def iter_intrinsic_calls(structural):
    """Yield call-like identifiers outside string payloads with their top-level arity."""
    i=0; n=len(structural)
    while i<n:
        if structural[i].isalpha() or structural[i]=='_':
            start=i; i+=1
            while i<n and (structural[i].isalnum() or structural[i]=='_'): i+=1
            name=structural[start:i]; j=i
            while j<n and structural[j].isspace(): j+=1
            if j<n and structural[j]=='(' and name!='think':
                yield name,_call_arity(structural,j)
            continue
        i+=1

def validate_code(s):
    e=[]; low=s.lower()
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    structural, unterminated_string=outside_strings(s)
    compact_structural=''.join(structural.split())
    if unterminated_string: e.append("unterminated_string")
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")
    lines=[line.strip() for line in s.splitlines()]
    for name,canonical in BINDINGS:
        call_count=compact_structural.count(name+'(')
        canonical_count=lines.count(canonical)
        if call_count != 1: e.append(f"binding_call_count:{name}:{call_count}")
        if canonical_count != 1: e.append(f"binding_not_exact_runtime_cfg:{name}:{canonical_count}")
    for x in REQUIRED:
        if x not in s: e.append("missing:"+x)
    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)

    # The cognition language is closed: a target that teaches an undefined call or
    # wrong arity is invalid even if its envelope and omega substrings look correct.
    call_source,call_unterminated=structural_calls_source(s)
    if not call_unterminated:
        for name,arity in iter_intrinsic_calls(call_source):
            expected=INTRINSIC_ARITY.get(name)
            if expected is None: e.append("unknown_intrinsic:"+name)
            elif arity is None: e.append("unterminated_call:"+name)
            elif arity!=expected: e.append(f"arity:{name}:{arity}!={expected}")

    if "omega_commit_candidate(" in s:
        for g in OMEGA_GATES:
            if f'omega_validate(w,"{g}")' not in s: e.append("omega_missing_gate:"+g)
        if 'omega_authority(w,' not in s: e.append("omega_missing_authority")
        if 'omega_generation(w,' not in s: e.append("omega_missing_generation")
    if "omega_reject(" in s and "omega_commit_candidate(" in s:
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
