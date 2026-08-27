#!/usr/bin/env python3
"""Build Clay's token-efficient current-state layer from append-only FAST_RESULT receipts.

Generated outputs are caches only. They never outrank current owner/supervisor/executable evidence.
"""
from __future__ import annotations
import argparse, datetime as dt, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUR = ROOT / "research_entity" / "00_CURRENT"
UPDATES = CUR / "updates"
LATEST = CUR / "latest"
BASELINE = CUR / "BASELINE.json"
DIRECTIONS = CUR / "DIRECTIONS.json"

MAX_HEADLINE=190; MAX_STATE=560; MAX_NEXT=300; MAX_EVIDENCE=6; MAX_BRANCHES=20; MAX_COMMITS=12

def clip(s, n):
    s=" ".join(str(s or "").split())
    return s if len(s)<=n else s[:n-1]+"…"

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def dump(p,obj): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
def git(*a):
    try:return subprocess.check_output(["git",*a],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:return ""
def file_epoch(p):
    rel=str(p.relative_to(ROOT)); x=git("log","-1","--format=%ct","--",rel)
    if x.isdigit(): return int(x)
    try:
        v=load(p); s=v.get("created_at") or v.get("timestamp")
        if s:return int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
    except Exception:pass
    return int(p.stat().st_mtime)
def validate(v,p):
    if v.get("schema")!="CLAY_FAST_RESULT/v1": raise ValueError(f"{p}: bad schema")
    for k in ("receipt_id","direction","status","headline","observed_head"):
        if not isinstance(v.get(k),str) or not v[k].strip(): raise ValueError(f"{p}: missing {k}")
    if len(v["headline"])>500: raise ValueError(f"{p}: headline too long")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--check",action="store_true"); args=ap.parse_args()
    cfg=load(DIRECTIONS); defs={x["id"]:x for x in cfg["directions"]}; base=load(BASELINE)
    selected={}
    for did,d in defs.items():
        b=dict(base.get("directions",{}).get(did,{})); b.update({"schema":"CLAY_FAST_RESULT/v1","receipt_id":"BASELINE:"+did,"direction":did,"observed_head":base.get("as_of_head","UNKNOWN"),"created_at":"1970-01-01T00:00:00Z","active":{},"source_receipt":"BASELINE.json","_epoch":0}); selected[did]=b
    errors=[]
    if UPDATES.exists():
        for p in UPDATES.glob("*/*.json"):
            try:
                v=load(p); validate(v,p)
                if v["direction"] not in defs: raise ValueError(f"{p}: unknown direction")
                v["source_receipt"]=str(p.relative_to(ROOT)); v["_epoch"]=file_epoch(p)
                old=selected[v["direction"]]
                if (v["_epoch"],v["receipt_id"],v["source_receipt"])>(old.get("_epoch",0),old.get("receipt_id",""),old.get("source_receipt","")): selected[v["direction"]]=v
            except Exception as e: errors.append(str(e))
    head=git("rev-parse","HEAD") or "UNKNOWN"; tree=git("rev-parse","HEAD^{tree}") or "UNKNOWN"
    now=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    LATEST.mkdir(parents=True,exist_ok=True)
    index=["direction\tstatus\tobserved_head\theadline\tnext\tlatest"]
    active=["kind\tdirection\tref\tstatus\theadline"]
    rows=[]
    ordered=sorted(defs,key=lambda k:(-int(defs[k].get("priority",0)),k))
    for did in ordered:
        v=selected[did]; label=defs[did].get("label",did); ev=[str(x) for x in v.get("evidence",[])][:MAX_EVIDENCE]
        out={k:v.get(k) for k in ("schema","receipt_id","direction","created_at","observed_head","status")}; out.update({"headline":clip(v.get("headline"),MAX_HEADLINE),"state":clip(v.get("state"),MAX_STATE),"next":clip(v.get("next"),MAX_NEXT),"evidence":ev,"active":v.get("active",{}),"source_receipt":v.get("source_receipt"),"cache_generated_at":now,"cache_head":head})
        dump(LATEST/(did+".json"),out)
        md=[f"# {label}","",f"Status: `{out['status']}`  ",f"Observed head: `{out['observed_head']}`  ",f"Selected receipt: `{out['source_receipt']}`","",out["headline"]]
        if out["state"]: md += ["", "State: "+out["state"]]
        if out["next"]: md += ["", "Next: "+out["next"]]
        if ev: md += ["", "Evidence:"]+[f"- `{e}`" for e in ev]
        md += ["","> Cache only. Re-enter current authority/source before material claims.",""]
        (LATEST/(did+".md")).write_text("\n".join(md),encoding="utf-8")
        index.append("\t".join([did,str(out["status"]),str(out["observed_head"])[:12],clip(out["headline"],150),clip(out["next"],120),f"latest/{did}.md"]))
        a=out.get("active") or {}
        for kind in ("branch","pr","issue","request"):
            ref=a.get(kind)
            if ref: active.append("\t".join([kind,did,clip(ref,120),str(out["status"]),clip(out["headline"],120)]))
        rows.append((did,label,out))
    raw=git("for-each-ref","--sort=-committerdate","--format=%(refname:short)%09%(objectname:short)%09%(committerdate:iso8601)%09%(subject)","refs/remotes/origin","refs/heads")
    seen=set(); n=0
    for line in raw.splitlines():
        parts=line.split("\t",3)
        if len(parts)<4: continue
        ref,sha,date,subj=parts
        if ref in {"main","origin/main","origin/HEAD"} or ref.endswith("/HEAD") or ref in seen: continue
        seen.add(ref); active.append("\t".join(["branch","repo",ref,"RECENT",clip(f"{sha} {date} {subj}",150)])); n+=1
        if n>=MAX_BRANCHES: break
    recent=["sha\tdate\tsubject"]
    raw=git("log",f"-{MAX_COMMITS}","--date=iso-strict","--pretty=format:%H%x09%ad%x09%s")
    recent += [clip(x,320) for x in raw.splitlines() if x.strip()]
    blockers=[]
    for did,label,out in rows:
        st=str(out["status"]).upper()
        if any(x in st for x in ("BLOCK","NEEDS","REQUIRED","UNOBSERVED","HARD_OFF")): blockers.append((did,clip(out["headline"],170)))
    nowmd=["# CLAY NOW — token-efficient current-state cache","",f"Cache head: `{head}` · tree `{tree[:12]}` · generated `{now}`","","> **Cache, not authority.** Read current `SUPERVISOR_INBOX.json` / selected steering before material execution or current-state promotion.","","## Read path","","`NOW.md` → `INDEX.tsv` / `ACTIVE.tsv` → one `latest/<direction>.md` → cited evidence only if needed.","","## Current directions"]
    for did,label,out in rows:
        nowmd.append(f"- **{label}** `{out['status']}` — {clip(out['headline'],190)} → `latest/{did}.md`")
    if blockers:
        nowmd += ["","## Highest visible blockers"]+[f"- `{d}` — {h}" for d,h in blockers[:8]]
    if errors: nowmd += ["","## Index errors"]+[f"- {clip(e,220)}" for e in errors[:10]]
    nowmd += ["","## Fast files","","- `INDEX.tsv` — one line per research direction","- `ACTIVE.tsv` — active branch/PR/issue/request refs + recent branches","- `RECENT.tsv` — latest main/repo commits","- `latest/` — current compact result per research direction","- `updates/` — append-only worker receipts","","> If a substantive research result is missing here, emit a `CLAY_FAST_RESULT/v1` receipt; do not hand-edit generated caches.",""]
    outputs={CUR/"NOW.md":"\n".join(nowmd),CUR/"INDEX.tsv":"\n".join(index)+"\n",CUR/"ACTIVE.tsv":"\n".join(active)+"\n",CUR/"RECENT.tsv":"\n".join(recent)+"\n"}
    manifest={"schema":"CLAY_CURRENT_MANIFEST/v1","cache_head":head,"cache_tree":tree,"generated_at":now,"selected":{did:{"receipt_id":selected[did].get("receipt_id"),"source_receipt":selected[did].get("source_receipt"),"status":selected[did].get("status"),"observed_head":selected[did].get("observed_head")} for did in ordered},"errors":errors}
    if args.check:
        bad=[]
        for p,s in outputs.items():
            if not p.exists() or p.read_text(encoding="utf-8")!=s: bad.append(str(p.relative_to(ROOT)))
        print(json.dumps({"ok":not bad and not errors,"stale":bad,"errors":errors,"head":head},sort_keys=True)); return 1 if bad or errors else 0
    for p,s in outputs.items(): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding="utf-8")
    dump(CUR/"MANIFEST.json",manifest)
    print(json.dumps({"ok":not errors,"head":head,"directions":len(rows),"errors":errors},sort_keys=True))
    return 1 if errors else 0
if __name__=="__main__": raise SystemExit(main())
