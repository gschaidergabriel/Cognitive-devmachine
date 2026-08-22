#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

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
ALLOWED_CALLS={
  'self_bind','role_bind','goal_bind','personality_bind',
  'grf_observe','grf_infer','grf_generate','grf_counter','grf_intervene','grf_emergent','grf_verify',
  'hyper_alt','hyper_discriminator','hyper_invariant','collapse_guard','collapse_exact',
  'omega_bind','omega_arg','omega_schema','omega_authority','omega_generation','omega_validate',
  'omega_reject','omega_commit_candidate',
  'self_state','self_scalar','self_kind','arch_bind','authority_bind','authority_deny',
  'state_note','unknown_preserve','provenance','policy_select','focus_set','recovery_state',
}
ALLOWED_CONSTRUCTORS={'cog_new','omega_new','hyper_new'}
IDENT=r'[A-Za-z_][A-Za-z0-9_]*'


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


def full_line(pattern,s):
    return re.search(r'^\s*'+pattern+r'\s*$',s,re.MULTILINE) is not None


def executable_surface_errors(s):
    """Reject comment/prose smuggling and unknown top-level ClayCode statements.

    This is intentionally a small validator for the emitted ClayCode subset, not a full
    language compiler. It exists so promotion scoring cannot be won by placing expected
    gate strings inside comments/prose/unknown statements.
    """
    e=[]
    surface=outside_strings(s)
    if '//' in surface or '/*' in surface or '*/' in surface:
        e.append('comment_surface')
    if "'" in surface:
        e.append('single_quote_surface')
    for no,line in enumerate(s.splitlines(),1):
        t=line.strip()
        if not t:
            continue
        if t in ('module clay.cog.turn','fn think(i:Map)->Map {','return c','}'):
            continue
        m=re.fullmatch(rf'let ({IDENT}) = ({IDENT})\(.*\)',t)
        if m:
            if m.group(2) not in ALLOWED_CONSTRUCTORS:
                e.append(f'unknown_constructor:{no}:{m.group(2)}')
            continue
        m=re.fullmatch(rf'({IDENT})\(.*\)',t)
        if m:
            if m.group(1) not in ALLOWED_CALLS:
                e.append(f'unknown_call:{no}:{m.group(1)}')
            continue
        e.append(f'unknown_statement:{no}')
    return e


def omega_binding_errors(s):
    """Bind commit/reject semantics to the same omega variable on real call lines."""
    e=[]
    commits=re.findall(rf'^\s*omega_commit_candidate\(c,({IDENT})\)\s*$',s,re.MULTILINE)
    rejects=set(re.findall(rf'^\s*omega_reject\(({IDENT}),',s,re.MULTILINE))
    for w in commits:
        for g in OMEGA_GATES:
            if not full_line(rf'omega_validate\({re.escape(w)},"{g}"\)',s):
                e.append(f'omega_missing_gate:{w}:{g}')
        if not re.search(rf'^\s*omega_authority\({re.escape(w)},',s,re.MULTILINE):
            e.append(f'omega_missing_authority:{w}')
        if not re.search(rf'^\s*omega_generation\({re.escape(w)},',s,re.MULTILINE):
            e.append(f'omega_missing_generation:{w}')
        if w in rejects:
            e.append(f'reject_and_commit:{w}')
    return e


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
    e.extend(executable_surface_errors(s))
    e.extend(omega_binding_errors(s))
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
