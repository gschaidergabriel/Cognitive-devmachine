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
FORBIDDEN=(
  '```','<think>','</think>',
  'self_bind(c,"zero"','self_bind(c,"mini_entity"',
  'role_bind(c,"blog','goal_bind(c,"write blog','personality_bind(c,"zero"',
  'omega_execute(','tool_execute(','api_call(',
)
OMEGA_GATES=("grammar","types","schema","authority","generation")

def outside_strings(s):
    """Mask literal payload while retaining one passive token per literal."""
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

def statement_lines(s):
    """Return (statement, brace_depth_before_line); comments/lexical ambiguity fail closed."""
    lines=[]; depth=0
    for raw in s.splitlines():
        structural,unterminated=outside_strings(raw)
        if unterminated: return None,"multiline_or_unclosed_string"
        if "//" in structural or "/*" in structural or "*/" in structural:
            return None,"comment_syntax_forbidden"
        stripped=raw.strip()
        if stripped: lines.append((stripped,depth))
        depth+=structural.count("{")-structural.count("}")
        if depth<0: return None,"brace_depth_underflow"
    return tuple(lines),None

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

def iter_calls(structural):
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

def _has_call(statements,prefix):
    return any(x.startswith(prefix) and x.endswith(")") for x in statements)

def validate_code(s):
    e=[]
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    structural,unterminated=outside_strings(s)
    compact=''.join(structural.split())
    if unterminated: e.append("unterminated_string")
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")

    info,lexical_error=statement_lines(s)
    if lexical_error:
        e.append(lexical_error); statements=()
    else:
        statements=tuple(x for x,depth in info if depth==1)

    for name,canonical in BINDINGS:
        call_count=compact.count(name+'(')
        canonical_count=statements.count(canonical)
        if call_count!=1: e.append(f"binding_call_count:{name}:{call_count}")
        if canonical_count!=1: e.append(f"binding_not_exact_runtime_cfg:{name}:{canonical_count}")
    if statements.count('return c')!=1: e.append(f"return_not_exact_top_level:{statements.count('return c')}")

    structural_low=structural.lower()
    for x in FORBIDDEN:
        if x.lower() in structural_low: e.append("forbidden:"+x)

    if not lexical_error and not unterminated:
        for name,arity in iter_calls(structural):
            expected=INTRINSIC_ARITY.get(name)
            if expected is None: e.append("unknown_intrinsic:"+name)
            elif arity is None: e.append("unterminated_call:"+name)
            elif arity!=expected: e.append(f"arity:{name}:{arity}!={expected}")

    any_commit='omega_commit_candidate(' in structural
    has_commit='omega_commit_candidate(c,w)' in statements
    if any_commit and not has_commit: e.append("omega_commit_not_exact_top_level")
    has_reject=_has_call(statements,'omega_reject(')
    if has_commit:
        for g in OMEGA_GATES:
            if f'omega_validate(w,"{g}")' not in statements: e.append("omega_missing_gate:"+g)
        if not _has_call(statements,'omega_authority(w,'): e.append("omega_missing_authority")
        if not _has_call(statements,'omega_generation(w,'): e.append("omega_missing_generation")
    if has_reject and has_commit: e.append("reject_and_commit")
    return sorted(set(e))

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
    print(json.dumps({"lines":n,"bad":bad,"ok":bad==0,"validator":"claycog-canonical-language/v1"}))
    return 1 if bad else 0

if __name__=="__main__": raise SystemExit(main(sys.argv[1]))
