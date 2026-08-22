#!/usr/bin/env python3
import json, sys
from pathlib import Path

PREFIX="module clay.cog.turn\nfn think(i:Map)->Map {\n"
REQUIRED=('self_bind(c,"mini_entity","persistent_entity")','return c\n}')
FORBIDDEN=("```","<think>","</think>")


def validate_code(s):
    errors=[]
    if not s.startswith(PREFIX): errors.append("bad_prefix")
    for item in REQUIRED:
        if item not in s: errors.append("missing:"+item)
    for item in FORBIDDEN:
        if item in s: errors.append("forbidden:"+item)
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
            errors=validate_code(messages[-1]["content"])
            if errors:
                bad+=1; print(line_no,errors)
        except Exception as exc:
            bad+=1; print(line_no,"json/schema",repr(exc))
    print({"lines":n,"bad":bad,"ok":bad==0})
    return 1 if bad else 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1]))
