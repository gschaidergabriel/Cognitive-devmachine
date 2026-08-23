#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
from claycode_syntax_v1 import outside_strings, statement_lines, top_level_statements, fn_counts, extract_calls

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
SEMANTIC_SLOT_CALLS=('state_note','self_state','arch_bind','provenance')
RESERVED_SEMANTIC_SLOTS=frozenset({
  'name','identity','entity_name','entity_id','role','goal','personality','persona',
  'application','application_role','application_goal','application_personality','audience','domain',
  'provider','provider_name','provider_id','model','model_name','model_id',
  'checkpoint','checkpoint_name','checkpoint_id','job','job_name','job_id',
})
SEMANTIC_SLOT_RE=re.compile(r'^('+'|'.join(SEMANTIC_SLOT_CALLS)+r')\(c,("(?:\\.|[^"\\])*"),')
OMEGA_GATES=("grammar","types","schema","authority","generation")
OMEGA_AUTHORITY='omega_authority(w,cfg("architecture.effect_authority"))'
OMEGA_GENERATION='omega_generation(w,cfg("state.generation"))'
OMEGA_COMMIT='omega_commit_candidate(c,w)'


def _slot_key(raw):
    try:
        value=json.loads(raw)
    except (TypeError,ValueError,json.JSONDecodeError):
        return None
    if not isinstance(value,str):
        return None
    return re.sub(r'[^a-z0-9]+','_',value.strip().lower()).strip('_')


def validate_code(s):
    e=[]; low=s.lower()
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    structural, unterminated_string=outside_strings(s)
    if unterminated_string: e.append("unterminated_string")
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")
    item_lines,lexical_error=statement_lines(s)
    if lexical_error:
        if lexical_error not in e: e.append(lexical_error)
        top=()
    else:
        top=top_level_statements(item_lines)

    calls=extract_calls(s)
    counts=fn_counts(s)
    for name,canonical in BINDINGS:
        n=counts.get(name,0)
        exact=top.count(canonical)
        if n != 1: e.append(f"binding_call_count:{name}:{n}")
        if exact != 1: e.append(f"binding_not_exact_runtime_cfg:{name}:{exact}")
    return_count=top.count('return c')
    if return_count != 1: e.append(f"return_not_exact_top_level:{return_count}")

    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)

    for item in calls:
        m=SEMANTIC_SLOT_RE.match(item['call'])
        if not m:
            continue
        slot=_slot_key(m.group(2))
        if slot in RESERVED_SEMANTIC_SLOTS:
            e.append(f"reserved_semantic_slot:{m.group(1)}:{slot}")

    commit_calls=counts.get('omega_commit_candidate',0)
    reject_calls=counts.get('omega_reject',0)
    if commit_calls:
        exact_commit=top.count(OMEGA_COMMIT)
        if commit_calls != 1: e.append(f"omega_commit_call_count:{commit_calls}")
        if exact_commit != 1: e.append(f"omega_commit_not_exact_top_level:{exact_commit}")
        validate_calls=counts.get('omega_validate',0)
        if validate_calls != len(OMEGA_GATES): e.append(f"omega_validate_call_count:{validate_calls}")
        for gate in OMEGA_GATES:
            exact=top.count(f'omega_validate(w,"{gate}")')
            if exact != 1: e.append(f"omega_gate_not_exact_top_level:{gate}:{exact}")
        authority_calls=counts.get('omega_authority',0)
        authority_exact=top.count(OMEGA_AUTHORITY)
        if authority_calls != 1: e.append(f"omega_authority_call_count:{authority_calls}")
        if authority_exact != 1: e.append(f"omega_authority_not_exact_top_level:{authority_exact}")
        generation_calls=counts.get('omega_generation',0)
        generation_exact=top.count(OMEGA_GENERATION)
        if generation_calls != 1: e.append(f"omega_generation_call_count:{generation_calls}")
        if generation_exact != 1: e.append(f"omega_generation_not_exact_top_level:{generation_exact}")

        # Admission is ordered: grammar -> types -> schema -> authority -> generation
        # must all happen at the canonical top level before the one commit candidate.
        transition_sequence=[
            item['call'] for item in calls
            if item['depth']==1 and item['fn'] in {'omega_validate','omega_commit_candidate'}
        ]
        expected_sequence=[f'omega_validate(w,"{gate}")' for gate in OMEGA_GATES]+[OMEGA_COMMIT]
        if transition_sequence != expected_sequence:
            e.append("omega_validation_sequence_before_commit")
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
