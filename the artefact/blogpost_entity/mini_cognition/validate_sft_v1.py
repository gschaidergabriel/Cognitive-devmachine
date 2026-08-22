#!/usr/bin/env python3
import json, sys
from pathlib import Path
from claycode_syntax_v1 import outside_strings, statement_lines, top_level_statements, call_set, fn_counts

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


def validate_code(s):
    e=[]; low=s.lower()
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    structural, unterminated_string=outside_strings(s)
    if unterminated_string: e.append("unterminated_string")
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")

    rows,lexical_error=statement_lines(s)
    if lexical_error:
        if lexical_error not in e: e.append(lexical_error)
        top=()
    else:
        top=top_level_statements(rows)

    all_counts=fn_counts(s)
    top_calls=call_set(s,depth=1)
    for name,canonical in BINDINGS:
        calls=all_counts.get(name,0)
        exact=top.count(canonical)
        if calls != 1: e.append(f"binding_call_count:{name}:{calls}")
        if exact != 1: e.append(f"binding_not_exact_runtime_cfg:{name}:{exact}")

    return_count=top.count('return c')
    if return_count != 1: e.append(f"return_not_exact_top_level:{return_count}")

    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)

    commit_calls=all_counts.get('omega_commit_candidate',0)
    reject_calls=all_counts.get('omega_reject',0)
    if commit_calls:
        if commit_calls != 1: e.append(f"omega_commit_call_count:{commit_calls}")
        if OMEGA_COMMIT not in top_calls: e.append("omega_commit_not_exact_top_level")
        validate_calls=all_counts.get('omega_validate',0)
        if validate_calls != len(OMEGA_GATES): e.append(f"omega_validate_call_count:{validate_calls}")
        for gate in OMEGA_GATES:
            if f'omega_validate(w,"{gate}")' not in top_calls:
                e.append("omega_gate_not_exact_top_level:"+gate)
        authority_calls=all_counts.get('omega_authority',0)
        generation_calls=all_counts.get('omega_generation',0)
        if authority_calls != 1: e.append(f"omega_authority_call_count:{authority_calls}")
        if generation_calls != 1: e.append(f"omega_generation_call_count:{generation_calls}")
        if OMEGA_AUTHORITY not in top_calls: e.append("omega_authority_not_exact_top_level")
        if OMEGA_GENERATION not in top_calls: e.append("omega_generation_not_exact_top_level")
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
