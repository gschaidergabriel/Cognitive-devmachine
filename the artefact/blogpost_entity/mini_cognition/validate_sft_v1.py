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
CALL_ARITY={
  'cog_new':0,'cfg':1,
  'self_bind':3,'role_bind':2,'goal_bind':2,'personality_bind':2,
  'grf_observe':4,'grf_infer':3,'grf_generate':3,'grf_counter':3,
  'grf_intervene':3,'grf_emergent':3,'grf_verify':4,
  'omega_new':2,'omega_bind':3,'omega_arg':4,'omega_schema':2,
  'omega_authority':2,'omega_generation':2,'omega_validate':2,
  'omega_reject':2,'omega_commit_candidate':2,
  'hyper_new':2,'hyper_alt':3,'hyper_discriminator':2,'hyper_invariant':2,
  'collapse_guard':2,'collapse_exact':3,
  'self_kind':2,'self_state':4,'self_scalar':4,
  'arch_bind':3,'authority_bind':3,'authority_deny':3,
  'state_note':4,'provenance':4,'unknown_preserve':3,
  'focus_set':2,'policy_select':2,'recovery_state':2,
}
IDENT_RE=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
LET_RE=re.compile(r'^let ([A-Za-z_][A-Za-z0-9_]*) = (.+)$')
NUM_RE=re.compile(r'^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$')

def outside_strings(s):
    out=[]; quoted=False; esc=False
    for ch in s:
        if quoted:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': quoted=False
            out.append(' ')
        else:
            if ch=='"': quoted=True; out.append(' ')
            else: out.append(ch)
    if quoted or esc:
        raise ValueError('unterminated_string')
    return ''.join(out)

def split_args(src):
    if not src.strip(): return []
    parts=[]; start=0; depth=0; quoted=False; esc=False
    for i,ch in enumerate(src):
        if quoted:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': quoted=False
            continue
        if ch=='"': quoted=True
        elif ch=='(': depth+=1
        elif ch==')':
            depth-=1
            if depth<0: raise ValueError('paren_underflow')
        elif ch==',' and depth==0:
            parts.append(src[start:i].strip()); start=i+1
    if quoted: raise ValueError('unterminated_string')
    if depth!=0: raise ValueError('nested_paren_balance')
    parts.append(src[start:].strip())
    if any(not p for p in parts): raise ValueError('empty_argument')
    return parts

def parse_call(expr):
    expr=expr.strip()
    m=re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\(',expr)
    if not m: raise ValueError('not_call')
    name=m.group(1)
    if name not in CALL_ARITY: raise ValueError('unknown_intrinsic:'+name)
    open_i=m.end()-1; depth=0; quoted=False; esc=False; close_i=None
    for i,ch in enumerate(expr[open_i:],open_i):
        if quoted:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': quoted=False
            continue
        if ch=='"': quoted=True
        elif ch=='(': depth+=1
        elif ch==')':
            depth-=1
            if depth==0:
                close_i=i; break
            if depth<0: raise ValueError('paren_underflow')
    if quoted: raise ValueError('unterminated_string')
    if close_i is None or depth!=0: raise ValueError('unterminated_call')
    if expr[close_i+1:].strip(): raise ValueError('trailing_after_call')
    args=split_args(expr[open_i+1:close_i])
    if len(args)!=CALL_ARITY[name]:
        raise ValueError(f'bad_arity:{name}:{len(args)}!={CALL_ARITY[name]}')
    for arg in args:
        validate_expr(arg)
    return name,args

def validate_expr(expr):
    expr=expr.strip()
    if not expr: raise ValueError('empty_expr')
    if expr.startswith('"'):
        try:
            v=json.loads(expr)
        except Exception as exc:
            raise ValueError('bad_string_literal') from exc
        if not isinstance(v,str): raise ValueError('non_string_json_literal')
        return
    if NUM_RE.fullmatch(expr): return
    if IDENT_RE.fullmatch(expr): return
    if '(' in expr:
        parse_call(expr); return
    raise ValueError('invalid_expr:'+expr[:40])

def validate_statement(line):
    if not line.startswith('  '): raise ValueError('body_indent')
    body=line[2:]
    if body=='return c': return ('return',['c'])
    m=LET_RE.fullmatch(body)
    if m:
        name,args=parse_call(m.group(2))
        return (name,args)
    return parse_call(body)

def validate_code(s):
    e=[]; low=s.lower()
    if not s.startswith(PREFIX): e.append('bad_prefix')
    if s.strip()!=s or not s.endswith('}'): e.append('outer_text')
    try:
        structural=outside_strings(s)
        if structural.count('{')!=structural.count('}'): e.append('brace_balance')
        if structural.count('(')!=structural.count(')'): e.append('paren_balance')
    except ValueError as exc:
        e.append(str(exc)); structural=''
    for x in REQUIRED:
        if x not in s: e.append('missing:'+x)
    for x in FORBIDDEN:
        if x.lower() in low: e.append('forbidden:'+x)

    lines=s.splitlines()
    calls=[]
    if len(lines)<4 or lines[0]!='module clay.cog.turn' or lines[1]!='fn think(i:Map)->Map {' or lines[-1]!='}':
        e.append('bad_outer_grammar')
    else:
        for no,line in enumerate(lines[2:-1],3):
            try:
                calls.append((no,*validate_statement(line)))
            except ValueError as exc:
                e.append(f'line_{no}:{exc}')

    for idx,(no,name,args) in enumerate(calls):
        if name!='omega_commit_candidate': continue
        w=args[1]
        prev=calls[:idx]
        seen_gates={a[1].strip('"') for _,n,a in prev if n=='omega_validate' and a[0]==w}
        for g in OMEGA_GATES:
            if g not in seen_gates: e.append('omega_missing_gate:'+g)
        if not any(n=='omega_authority' and a[0]==w for _,n,a in prev): e.append('omega_missing_authority')
        if not any(n=='omega_generation' and a[0]==w for _,n,a in prev): e.append('omega_missing_generation')
        if any(n=='omega_reject' and a[0]==w for _,n,a in calls): e.append('reject_and_commit')
    return sorted(set(e))

def main(path):
    n=bad=0
    for no,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
        n+=1
        try:
            row=json.loads(line); ms=row['messages']
            if [m['role'] for m in ms] != ['system','user','assistant']: raise ValueError('role order')
            errors=validate_code(ms[-1]['content'])
            if errors: bad+=1; print(no,errors)
        except Exception as exc:
            bad+=1; print(no,'schema',repr(exc))
    print(json.dumps({'lines':n,'bad':bad,'ok':bad==0}))
    return 1 if bad else 0

if __name__=='__main__': raise SystemExit(main(sys.argv[1]))
