#!/usr/bin/env python3
"""Fail-closed leakage guard for Needle-style JSONL rows.

Rows need an `id` and at least one model-visible text field. The guard rejects
cross-split duplicate ids and exact normalized text surfaces. Passing this guard
does NOT prove statistical independence, semantic independence, or training readiness.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

TEXT_KEYS=("text","u","prompt","input","output","answer","response","instruction","context","piece","pieces")
WS=re.compile(r"\s+")

def _collect_text(v, key=""):
    out=[]
    if isinstance(v,str) and (key.lower() in TEXT_KEYS or any(tok in key.lower() for tok in TEXT_KEYS)):
        out.append(v)
    elif isinstance(v,list):
        for x in v: out.extend(_collect_text(x,key))
    elif isinstance(v,dict):
        for k,x in v.items(): out.extend(_collect_text(x,k))
    return out

def surface(row: dict) -> str:
    vals=_collect_text(row)
    if not vals:
        raise ValueError("row has no recognized text field")
    return WS.sub(" "," \n ".join(vals)).strip().casefold()

def load(path: Path) -> list[dict]:
    rows=[]
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        obj=json.loads(line)
        if not isinstance(obj,dict) or not isinstance(obj.get("id"),str) or not obj["id"]:
            raise ValueError(f"{path}:{n}: id required")
        rows.append(obj)
    return rows

def adjudicate(splits: dict[str,list[dict]]) -> dict:
    failures=[]; seen_ids={}; seen_surface={}; counts={}
    for split,rows in splits.items():
        counts[split]=len(rows)
        if not rows: failures.append(f"EMPTY_SPLIT:{split}")
        local=set()
        for i,row in enumerate(rows):
            rid=row["id"]
            if rid in local: failures.append(f"DUPLICATE_ID_WITHIN:{split}:{rid}")
            local.add(rid)
            if rid in seen_ids and seen_ids[rid]!=split: failures.append(f"ID_OVERLAP:{seen_ids[rid]}:{split}:{rid}")
            seen_ids[rid]=split
            try: s=surface(row)
            except Exception as e:
                failures.append(f"TEXT_SURFACE_FAIL:{split}:{i}:{type(e).__name__}"); continue
            h=hashlib.sha256(s.encode()).hexdigest()
            if h in seen_surface and seen_surface[h]!=split: failures.append(f"TEXT_OVERLAP:{seen_surface[h]}:{split}:{h}")
            seen_surface[h]=split
    return {"schema":"NEEDLE_SPLIT_GUARD/v1","pass":not failures,"failures":sorted(set(failures)),"rows_by_split":counts,"independence_credit_minted":False,"training_credit_minted":False}

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--train",type=Path,required=True); ap.add_argument("--validation",type=Path,required=True); ap.add_argument("--holdout",type=Path,required=True)
    a=ap.parse_args(); r=adjudicate({"TRAIN":load(a.train),"VALIDATION":load(a.validation),"HOLDOUT":load(a.holdout)})
    print(json.dumps(r,sort_keys=True)); return 0 if r["pass"] else 2
if __name__=="__main__": raise SystemExit(main())
