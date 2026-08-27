#!/usr/bin/env python3
"""Merge sandbox Evidence Forge evaluations into the dashboard ledger, deduplicated."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

def key(x:dict)->str:
    stable={k:x.get(k) for k in ("delta_id","worker_sha","provider","model","status","evaluated_at")}
    return hashlib.sha256(json.dumps(stable,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo",default="/workspace/clay-global-research-entity");ap.add_argument("--artifacts",default="/artifacts/clay-entityos-swarm");args=ap.parse_args()
    src=Path(args.artifacts)/"forge/architecture_delta_evaluations.jsonl"; dst=Path(args.repo)/"free swarm/architecture_delta_evaluations.jsonl"
    if not src.exists():print('{"merged":0}');return
    existing=[];seen=set()
    if dst.exists():
        for line in dst.read_text(encoding="utf-8",errors="replace").splitlines():
            try:o=json.loads(line)
            except Exception:continue
            if isinstance(o,dict):existing.append(o);seen.add(key(o))
    merged=0
    for line in src.read_text(encoding="utf-8",errors="replace").splitlines():
        try:o=json.loads(line)
        except Exception:continue
        if not isinstance(o,dict):continue
        o.setdefault("source_class","free_swarm");o.setdefault("record_type","forge_evaluation")
        k=key(o)
        if k in seen:continue
        existing.append(o);seen.add(k);merged+=1
    if merged:
        dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text("\n".join(json.dumps(x,ensure_ascii=False,separators=(",",":")) for x in existing)+"\n",encoding="utf-8")
    print(json.dumps({"merged":merged,"total":len(existing)}))
if __name__=="__main__":main()
