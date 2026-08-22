#!/usr/bin/env python3
import json, sys
from pathlib import Path
from intrinsics_v1 import INTRINSIC_ARITY

PREFIX='module clay.cog.turn\nfn think(i:Map)->Map {\n'
REQUIRED=(
  'self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
  'role_bind(c,cfg("application.role"))',
  'goal_bind(c,cfg("application.goal"))',
  'personality_bind(c,cfg("application.personality"))',
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
    """Mask string payload while preserving one structural token per literal."""
    out=[]; quoted=False; esc=False
    for ch in s:
        if quoted:
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch=='"': quoted=False
            out.append(" ")
        else:
            if ch=='"':
                quoted=True
                # Keep a passive placeholder so f("x") still has arity 1 while
                # punctuation inside the literal cannot affect structural parsing.
                out.append("_")
            else: out.append(ch)
    return "".join(out)


def _call_arity(structural, open_pos):
    """Return top-level argument count for one call in string-masked source."""
    depth=1; commas=0; saw_token=False; i=open_pos+1
    while i < len(structural):
        ch=structural[i]
        if ch=='(':
            depth+=1
            if depth==2: saw_token=True
        elif ch==')':
            depth-=1
            if depth==0:
                return 0 if not saw_token else commas+1
        elif depth==1:
            if ch==',': commas+=1
            elif not ch.isspace(): saw_token=True
        i+=1
    return None


def iter_calls(structural):
    """Yield (name, arity) for call-like tokens outside string literals."""
    i=0; n=len(structural)
    while i<n:
        ch=structural[i]
        if ch.isalpha() or ch=='_':
            start=i; i+=1
            while i<n and (structural[i].isalnum() or structural[i]=='_'): i+=1
            name=structural[start:i]
            j=i
            while j<n and structural[j].isspace(): j+=1
            if j<n and structural[j]=='(':
                # `think(...)` is the declared ClayCode entry function, not an intrinsic.
                if name != 'think':
                    yield name,_call_arity(structural,j)
            continue
        i+=1


def validate_code(s):
    e=[]; low=s.lower()
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    structural=outside_strings(s)
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")
    for x in REQUIRED:
        if x not in s: e.append("missing:"+x)
    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)

    # Vocabulary closure: a target that teaches an undefined intrinsic is invalid even
    # when its punctuation and omega gates look correct. This binds SFT, OOD scoring,
    # and future runtime grammar to one explicit v1 vocabulary.
    for name,arity in iter_calls(structural):
        expected=INTRINSIC_ARITY.get(name)
        if expected is None:
            e.append("unknown_intrinsic:"+name)
        elif arity is None:
            e.append("unterminated_call:"+name)
        elif arity != expected:
            e.append(f"arity:{name}:{arity}!={expected}")

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
