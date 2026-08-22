#!/usr/bin/env python3
import json, sys
from pathlib import Path

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
OMEGA_AUTHORITY='omega_authority(w,cfg("architecture.effect_authority"))'
OMEGA_GENERATION='omega_generation(w,cfg("state.generation"))'
OMEGA_COMMIT='omega_commit_candidate(c,w)'

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

def statement_lines(s):
    """Return (raw standalone statement, brace depth); fail closed on lexical ambiguity."""
    lines=[]; depth=0
    for raw in s.splitlines():
        structural, unterminated=outside_strings(raw)
        if unterminated:
            return None,"unterminated_string"
        if "//" in structural or "/*" in structural or "*/" in structural:
            return None,"comment_syntax_forbidden"
        stripped=raw.strip()
        if stripped:
            lines.append((stripped,depth))
        depth += structural.count("{")-structural.count("}")
        if depth < 0:
            return None,"brace_depth_underflow"
    return tuple(lines),None

def top_level_statements(items):
    return tuple(statement for statement,depth in items if depth==1)

def call_count(compact_structural,name):
    return compact_structural.count(name+'(')

def validate_code(s):
    e=[]; low=s.lower()
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    structural, unterminated_string=outside_strings(s)
    compact_structural=''.join(structural.split())
    if unterminated_string: e.append("unterminated_string")
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")
    item_lines,lexical_error=statement_lines(s)
    if lexical_error:
        if lexical_error not in e: e.append(lexical_error)
        top=()
    else:
        top=top_level_statements(item_lines)

    for name,canonical in BINDINGS:
        calls=call_count(compact_structural,name)
        exact=top.count(canonical)
        if calls != 1: e.append(f"binding_call_count:{name}:{calls}")
        if exact != 1: e.append(f"binding_not_exact_runtime_cfg:{name}:{exact}")
    return_count=top.count('return c')
    if return_count != 1: e.append(f"return_not_exact_top_level:{return_count}")

    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)

    commit_calls=call_count(compact_structural,'omega_commit_candidate')
    reject_calls=call_count(compact_structural,'omega_reject')
    if commit_calls:
        exact_commit=top.count(OMEGA_COMMIT)
        if commit_calls != 1: e.append(f"omega_commit_call_count:{commit_calls}")
        if exact_commit != 1: e.append(f"omega_commit_not_exact_top_level:{exact_commit}")
        validate_calls=call_count(compact_structural,'omega_validate')
        if validate_calls != len(OMEGA_GATES): e.append(f"omega_validate_call_count:{validate_calls}")
        for gate in OMEGA_GATES:
            exact=top.count(f'omega_validate(w,"{gate}")')
            if exact != 1: e.append(f"omega_gate_not_exact_top_level:{gate}:{exact}")
        authority_calls=call_count(compact_structural,'omega_authority')
        authority_exact=top.count(OMEGA_AUTHORITY)
        if authority_calls != 1: e.append(f"omega_authority_call_count:{authority_calls}")
        if authority_exact != 1: e.append(f"omega_authority_not_exact_top_level:{authority_exact}")
        generation_calls=call_count(compact_structural,'omega_generation')
        generation_exact=top.count(OMEGA_GENERATION)
        if generation_calls != 1: e.append(f"omega_generation_call_count:{generation_calls}")
        if generation_exact != 1: e.append(f"omega_generation_not_exact_top_level:{generation_exact}")
    if reject_calls and commit_calls:
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
