#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

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

# These semantic fields are runtime configuration, not checkpoint literals.  The direct
# *_bind calls above already require cfg(...), but ClayCode also has generic state/architecture
# intrinsics.  Without this gate a target can satisfy all canonical bindings and still smuggle a
# second fixed persona through e.g. self_state(c,"name","Zero","COMPUTED").
RESERVED_RUNTIME_KEYS=frozenset({
  'name','display_name','display.name',
  'entity_id','entity.id','identity','continuity','entity.continuity',
  'role','application.role','job','job_title',
  'goal','application.goal',
  'personality','application.personality','persona',
  'audience','application',
})
_JSON_STRING=r'"(?:[^"\\]|\\.)*"'
LITERAL_STATE_INTRINSIC_RE=re.compile(
  rf'^(?:self_state|state_note|arch_bind)\(\s*c\s*,\s*({_JSON_STRING})\s*,\s*({_JSON_STRING})'
)

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

def reserved_literal_errors(lines):
    errors=[]
    for line in lines:
        m=LITERAL_STATE_INTRINSIC_RE.match(line)
        if not m: continue
        try:
            key=json.loads(m.group(1))
            # Decode the value too: malformed JSON-like Clay string escapes must not create a
            # parser differential where the key is admitted but the value is interpreted later.
            json.loads(m.group(2))
        except (json.JSONDecodeError, TypeError):
            errors.append('malformed_literal_state_intrinsic')
            continue
        if isinstance(key,str) and key.lower() in RESERVED_RUNTIME_KEYS:
            errors.append('literal_reserved_runtime_key:'+key.lower())
    return errors

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
    e.extend(reserved_literal_errors(lines))
    for x in REQUIRED:
        if x not in s: e.append("missing:"+x)
    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)
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
