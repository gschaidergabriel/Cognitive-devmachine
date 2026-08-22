#!/usr/bin/env python3
import json, sys
from pathlib import Path

PREFIX='module clay.cog.turn\nfn think(i:Map)->Map {\n'
REQUIRED=(
  'self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
  'role_bind(c,cfg("application.role"))',
  'goal_bind(c,cfg("application.goal"))',
  'personality_bind(c,cfg("application.personality"))',
  'return c',
)
FORBIDDEN=(
  '```','<think>','</think>',
  'self_bind(c,"zero"','self_bind(c,"mini_entity"',
  'role_bind(c,"blog','goal_bind(c,"write blog','personality_bind(c,"zero"',
  'omega_execute(','tool_execute(','api_call(',
)
OMEGA_GATES=("grammar","types","schema","authority","generation")
STATEMENT_PREFIXES=(
  'self_bind(','role_bind(','goal_bind(','personality_bind(',
  'grf_','hyper_','collapse_','omega_','unknown_preserve(',
  'authority_bind(','authority_deny(','recovery_state(','policy_select(',
  'state_note(','provenance(','self_state(','self_scalar(','self_kind(',
  'arch_bind(','focus_set(','return c',
)

def strip_comments(s):
    """Remove comments without touching quoted strings; report comment presence/lexical errors."""
    out=[]; i=0; quoted=False; esc=False; line=False; block=False; had_comment=False
    while i < len(s):
        ch=s[i]; nxt=s[i+1] if i+1 < len(s) else ''
        if line:
            had_comment=True
            if ch=='\n':
                line=False; out.append('\n')
            else:
                out.append(' ')
            i+=1; continue
        if block:
            had_comment=True
            if ch=='*' and nxt=='/':
                out.extend('  '); i+=2; block=False; continue
            out.append('\n' if ch=='\n' else ' '); i+=1; continue
        if quoted:
            out.append(ch)
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': quoted=False
            i+=1; continue
        if ch=='"':
            quoted=True; out.append(ch); i+=1; continue
        if ch=='/' and nxt=='/':
            had_comment=True; line=True; out.extend('  '); i+=2; continue
        if ch=='/' and nxt=='*':
            had_comment=True; block=True; out.extend('  '); i+=2; continue
        out.append(ch); i+=1
    lexical_error = quoted or block
    return ''.join(out), had_comment, lexical_error

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

def active_lines(s):
    clean, _, _ = strip_comments(s)
    return [line.strip() for line in clean.splitlines() if line.strip()]

def active_prefix(s, token):
    return any(line.startswith(token) for line in active_lines(s))

def semantic_token_present(s, token):
    clean, _, lexical_error = strip_comments(s)
    if lexical_error: return False
    stripped=token.lstrip()
    if stripped.startswith(STATEMENT_PREFIXES):
        return any(line.startswith(stripped) for line in active_lines(clean))
    return token in clean

def semantic_token_absent(s, token):
    return not semantic_token_present(s, token)

def semantic_token_count(s, token):
    clean, _, lexical_error = strip_comments(s)
    if lexical_error: return 0
    stripped=token.lstrip()
    if stripped.startswith(STATEMENT_PREFIXES):
        return sum(1 for line in active_lines(clean) if line.startswith(stripped))
    return clean.count(token)

def validate_code(s):
    e=[]; low=s.lower()
    clean, had_comment, lexical_error = strip_comments(s)
    if not s.startswith(PREFIX): e.append("bad_prefix")
    if s.strip()!=s or not s.endswith("}"): e.append("outer_text")
    if had_comment: e.append("comments_forbidden")
    if lexical_error: e.append("lexical_state")
    structural=outside_strings(clean)
    if "'" in structural: e.append("single_quote_forbidden")
    if structural.count("{")!=structural.count("}"): e.append("brace_balance")
    if structural.count("(")!=structural.count(")"): e.append("paren_balance")
    for x in REQUIRED:
        if not semantic_token_present(clean,x): e.append("missing:"+x)
    for x in FORBIDDEN:
        if x.lower() in low: e.append("forbidden:"+x)
    commit=active_prefix(clean,"omega_commit_candidate(")
    reject=active_prefix(clean,"omega_reject(")
    if commit:
        for g in OMEGA_GATES:
            if not active_prefix(clean,f'omega_validate(w,"{g}")'): e.append("omega_missing_gate:"+g)
        if not active_prefix(clean,'omega_authority(w,'): e.append("omega_missing_authority")
        if not active_prefix(clean,'omega_generation(w,'): e.append("omega_missing_generation")
    if reject and commit: e.append("reject_and_commit")
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
    print(json.dumps({"lines":n,"bad":bad,"ok":bad==0,"validator":"claycog-lexical-semantic-v2"}))
    return 1 if bad else 0

if __name__=="__main__": raise SystemExit(main(sys.argv[1]))
