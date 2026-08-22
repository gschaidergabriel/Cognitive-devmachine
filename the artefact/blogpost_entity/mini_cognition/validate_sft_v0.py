#!/usr/bin/env python3
import json, sys
from pathlib import Path

PREFIX="module c\nfn t(i:M)->M{\n"
SYSTEM_PREFIX="T0{R'=F(R,I,C);CC=1;GRF=1;HP=1;U!=Z!=E!=M;AUTH=EXT;ID=CFG}"
REQUIRED=(
    'id(c,cf("e.id"),cf("e.cont"))',
    'rl(c,cf("a.role"))',
    'gl(c,cf("a.goal"))',
    'ps(c,cf("a.persona"))',
    'nx(c,"R","F")',
    'return c\n}',
)
FORBIDDEN_MARKUP=("```","<think>","</think>")
FORBIDDEN_FIXED_IDENTITY=(
    'id(c,"zero"',
    'id(c,"mini_entity"',
    'rl(c,"blog',
    'rl(c,"blogger',
    'rl(c,"analyst',
    'ps(c,"zero',
)


def validate_code(s):
    errors=[]
    lower=s.lower()
    if not s.startswith(PREFIX): errors.append("bad_prefix")
    for item in REQUIRED:
        if item not in s: errors.append("missing:"+item)
    for item in FORBIDDEN_MARKUP:
        if item in s: errors.append("forbidden_markup:"+item)
    for item in FORBIDDEN_FIXED_IDENTITY:
        if item in lower: errors.append("fixed_identity_or_job:"+item)
    if s.count("{")!=s.count("}"): errors.append("brace_balance")
    if s.count("(")!=s.count(")"): errors.append("paren_balance")
    if s.strip()!=s or not s.rstrip().endswith("}"): errors.append("outer_text")
    return errors


def main(path):
    n=bad=0
    for line_no,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        n+=1
        try:
            row=json.loads(line); messages=row["messages"]
            if [m["role"] for m in messages] != ["system","user","assistant"]:
                raise ValueError("roles must be system,user,assistant")
            if messages[0]["content"] != SYSTEM_PREFIX:
                raise ValueError("noncanonical compact system state")
            errors=validate_code(messages[-1]["content"])
            if errors:
                bad+=1; print(line_no,errors)
        except Exception as exc:
            bad+=1; print(line_no,"json/schema",repr(exc))
    print({"lines":n,"bad":bad,"ok":bad==0})
    return 1 if bad else 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1]))
