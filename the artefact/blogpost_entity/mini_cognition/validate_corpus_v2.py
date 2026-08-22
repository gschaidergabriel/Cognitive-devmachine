#!/usr/bin/env python3
"""Leakage/diversity validator for canonical SFT v2.

ClayCode syntax/semantic admission is delegated to the single canonical validator in
validate_sft_v1.py so paid-training V2 cannot bypass the intrinsic/arity/statement gate.
"""
import hashlib, json, sys
from pathlib import Path
from validate_sft_v1 import validate_code


def load(path):
    rows=[]; bad=[]
    for no,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        try:
            row=json.loads(line); ms=row["messages"]
            if [m["role"] for m in ms] != ["system","user","assistant"]: raise ValueError("role order")
            errs=validate_code(ms[-1]["content"])
            if errs: bad.append((no,errs))
            rows.append(row)
        except Exception as exc:
            bad.append((no,["schema:"+repr(exc)]))
    return rows,bad


def canon(x): return json.dumps(x["messages"],ensure_ascii=False,separators=(",",":"))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(trp,vap):
    tr,tbad=load(trp); va,vbad=load(vap)
    tc=[canon(x) for x in tr]; vc=[canon(x) for x in va]
    tp={x["messages"][1]["content"] for x in tr}; vp={x["messages"][1]["content"] for x in va}
    r={
       "schema":"claycog-corpus-validation/v2",
       "claycode_admission":"validate_sft_v1.validate_code",
       "train_lines":len(tr),"validation_lines":len(va),
       "train_structural_invalid":len(tbad),"validation_structural_invalid":len(vbad),
       "train_unique":len(set(tc)),"validation_unique":len(set(vc)),
       "exact_cross_split_overlap":len(set(tc)&set(vc)),"prompt_cross_split_overlap":len(tp&vp),
       "train_sha256":sha(trp),"validation_sha256":sha(vap),
    }
    r["ok"]=(
        len(tr)==1485 and len(va)==165 and not tbad and not vbad
        and len(set(tc))==len(tc) and len(set(vc))==len(vc)
        and r["exact_cross_split_overlap"]==0 and r["prompt_cross_split_overlap"]==0
    )
    if tbad: r["train_invalid_sample"]=tbad[:20]
    if vbad: r["validation_invalid_sample"]=vbad[:20]
    print(json.dumps(r,indent=2,sort_keys=True))
    return 0 if r["ok"] else 1


if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: validate_corpus_v2.py train.jsonl validation.jsonl")
    raise SystemExit(main(sys.argv[1],sys.argv[2]))
