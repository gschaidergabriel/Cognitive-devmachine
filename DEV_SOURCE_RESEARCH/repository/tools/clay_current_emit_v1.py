#!/usr/bin/env python3
"""Emit one append-only CLAY_FAST_RESULT/v1 receipt, then refresh local current-state cache."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CUR=ROOT/"research_entity"/"00_CURRENT"
def git(*a):
    try:return subprocess.check_output(["git",*a],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:return "UNKNOWN"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--direction",required=True); ap.add_argument("--status",required=True); ap.add_argument("--headline",required=True)
    ap.add_argument("--state",default=""); ap.add_argument("--next",default=""); ap.add_argument("--evidence",action="append",default=[])
    ap.add_argument("--branch",default=""); ap.add_argument("--pr",default=""); ap.add_argument("--issue",default=""); ap.add_argument("--request",default="")
    ap.add_argument("--organ",default="unspecified-organ")
    a=ap.parse_args(); cfg=json.loads((CUR/"DIRECTIONS.json").read_text()); valid={x["id"] for x in cfg["directions"]}
    if a.direction not in valid: raise SystemExit(f"unknown direction {a.direction}; valid={','.join(sorted(valid))}")
    now=dt.datetime.now(dt.timezone.utc).replace(microsecond=0); stamp=now.strftime("%Y%m%dT%H%M%SZ"); head=git("rev-parse","HEAD")
    core={"schema":"CLAY_FAST_RESULT/v1","direction":a.direction,"created_at":now.isoformat().replace("+00:00","Z"),"observed_head":head,"status":a.status,"headline":a.headline,"state":a.state,"next":a.next,"evidence":a.evidence[:8],"active":{k:v for k,v in {"branch":a.branch,"pr":a.pr,"issue":a.issue,"request":a.request}.items() if v},"organ":a.organ}
    rid=stamp+"-"+a.direction+"-"+hashlib.sha256(json.dumps(core,sort_keys=True).encode()).hexdigest()[:10]; core["receipt_id"]=rid
    p=CUR/"updates"/a.direction/(rid+".json"); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(core,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    refresh=ROOT/"tools"/"clay_current_refresh_v1.py"; subprocess.run(["python3",str(refresh)],cwd=ROOT,check=True)
    print(p.relative_to(ROOT)); return 0
if __name__=="__main__": raise SystemExit(main())
