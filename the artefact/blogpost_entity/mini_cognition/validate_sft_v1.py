#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
from intrinsics_v1 import INTRINSIC_ARITY

PREFIX='module clay.cog.turn\nfn think(i:Map)->Map {\n'
BINDINGS=(
  ('self_bind','self_bind(c,cfg("entity.id"),cfg("entity.continuity"))'),
  ('role_bind','role_bind(c,cfg("application.role"))'),
  ('goal_bind','goal_bind(c,cfg("application.goal"))'),
  ('personality_bind','personality_bind(c,cfg("application.personality"))'),
)
FORBIDDEN_CALLS=('omega_execute','tool_execute','api_call')
OMEGA_GATES=("grammar","types","schema","authority","generation")
IDENT_RE=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
LET_RE=re.compile(r'^let ([A-Za-z_][A-Za-z0-9_]*) = (.+)$')
NUM_RE=re.compile(r'^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$')


def structural_mask(s):
    """Mask string payload while preserving delimiters outside strings."""
    out=[]; quoted=False; esc=False
    for ch in s:
        if quoted:
            if esc:
                esc=False
            elif ch=='\\':
                esc=True
            elif ch=='"':
                quoted=False
            out.append(' ')
        else:
            if ch=='"':
                quoted=True; out.append(' ')
            else:
                out.append(ch)
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
    if quoted or esc: raise ValueError('unterminated_string')
    if depth!=0: raise ValueError('nested_paren_balance')
    parts.append(src[start:].strip())
    if any(not p for p in parts): raise ValueError('empty_argument')
    return parts


def parse_call(expr, collector=None):
    expr=expr.strip()
    m=re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\(',expr)
    if not m: raise ValueError('not_call')
    name=m.group(1)
    expected=INTRINSIC_ARITY.get(name)
    if expected is None: raise ValueError('unknown_intrinsic:'+name)
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
    if quoted or esc: raise ValueError('unterminated_string')
    if close_i is None or depth!=0: raise ValueError('unterminated_call:'+name)
    if expr[close_i+1:].strip(): raise ValueError('trailing_after_call')
    args=split_args(expr[open_i+1:close_i])
    if len(args)!=expected:
        raise ValueError(f'bad_arity:{name}:{len(args)}!={expected}')
    if collector is not None: collector.append((name,args))
    for arg in args: validate_expr(arg,collector)
    return name,args


def validate_expr(expr, collector=None):
    expr=expr.strip()
    if not expr: raise ValueError('empty_expr')
    if expr.startswith('"'):
        try: value=json.loads(expr)
        except Exception as exc: raise ValueError('bad_string_literal') from exc
        if not isinstance(value,str): raise ValueError('non_string_json_literal')
        return
    if NUM_RE.fullmatch(expr) or IDENT_RE.fullmatch(expr): return
    if '(' in expr:
        parse_call(expr,collector); return
    raise ValueError('invalid_expr:'+expr[:40])


def validate_statement(raw, all_calls):
    if not re.match(r'^  \S',raw): raise ValueError('body_indent')
    body=raw[2:]
    if body=='return c': return ('return',['c'],body)
    m=LET_RE.fullmatch(body)
    if m:
        name,args=parse_call(m.group(2),all_calls)
        return (name,args,body)
    name,args=parse_call(body,all_calls)
    return (name,args,body)


def literal_string(expr):
    expr=expr.strip()
    if not expr.startswith('"'): return None
    try:
        value=json.loads(expr)
        return value if isinstance(value,str) else None
    except Exception:
        return None


def validate_code(s):
    e=[]
    if not isinstance(s,str): return ['not_string']
    if not s.startswith(PREFIX): e.append('bad_prefix')
    if s.strip()!=s or not s.endswith('}'): e.append('outer_text')
    try:
        structural=structural_mask(s)
        if structural.count('{')!=structural.count('}'): e.append('brace_balance')
        if structural.count('(')!=structural.count(')'): e.append('paren_balance')
        if '//' in structural or '/*' in structural or '*/' in structural: e.append('comment_syntax_forbidden')
    except ValueError as exc:
        e.append(str(exc)); structural=''

    lines=s.splitlines()
    top=[]; all_calls=[]
    if len(lines)<4 or lines[0]!='module clay.cog.turn' or lines[1]!='fn think(i:Map)->Map {' or lines[-1]!='}':
        e.append('bad_outer_grammar')
    else:
        body=lines[2:-1]
        if not body or body[-1] != '  return c': e.append('return_not_final')
        if sum(1 for x in body if x=='  return c') != 1: e.append('return_count')
        for no,raw in enumerate(body,3):
            try:
                top.append((no,*validate_statement(raw,all_calls)))
            except ValueError as exc:
                e.append(f'line_{no}:{exc}')

    for forbidden in FORBIDDEN_CALLS:
        if any(name==forbidden for name,_ in all_calls): e.append('forbidden_call:'+forbidden)

    parsed_top=[(no,name,args,body) for no,name,args,body in top]
    for name,canonical in BINDINGS:
        total=sum(1 for n,_ in all_calls if n==name)
        exact=sum(1 for _,n,_,body in parsed_top if n==name and body==canonical)
        if total!=1: e.append(f'binding_call_count:{name}:{total}')
        if exact!=1: e.append(f'binding_not_exact_runtime_cfg:{name}:{exact}')

    for idx,(no,name,args,body) in enumerate(parsed_top):
        if name!='omega_commit_candidate': continue
        candidate=args[1].strip()
        prev=parsed_top[:idx]
        gates={literal_string(a[1]) for _,n,a,_ in prev if n=='omega_validate' and a[0].strip()==candidate}
        for gate in OMEGA_GATES:
            if gate not in gates: e.append('omega_missing_precommit_gate:'+gate)
        if not any(n=='omega_authority' and a[0].strip()==candidate for _,n,a,_ in prev):
            e.append('omega_missing_precommit_authority')
        if not any(n=='omega_generation' and a[0].strip()==candidate for _,n,a,_ in prev):
            e.append('omega_missing_precommit_generation')
        if any(n=='omega_reject' and a[0].strip()==candidate for _,n,a,_ in parsed_top):
            e.append('reject_and_commit:'+candidate)

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
