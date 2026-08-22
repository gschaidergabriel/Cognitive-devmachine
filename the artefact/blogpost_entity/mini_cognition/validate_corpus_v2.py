#!/usr/bin/env python3
"""Validate SFT v2 while delegating ClayCode semantics to the canonical validator.

This file owns corpus-level invariants (counts, uniqueness, split leakage and
campaign/provider/model neutrality). `validate_sft_v1.py` remains the single
ClayCode structural/runtime-binding admission implementation so later hardening
cannot silently diverge between corpus versions.
"""
import hashlib, importlib.util, json, re, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("claycog_core_validator",HERE/"validate_sft_v1.py")
CORE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CORE)

# Expose the canonical function for focused regression tests and callers.
validate_code=CORE.validate_code

# Reusable cognition rows must not acquire the current paid-campaign provider/model
# as fixed message content. Those choices belong to the external campaign descriptor.
CAMPAIGN_LITERAL_PATTERNS=(
    ("provider:together",re.compile(r"\btogether(?:\.ai)?\b",re.IGNORECASE)),
    ("model:qwen",re.compile(r"\bqwen(?:2(?:\.5)?|3(?:\.5)?)?(?:/|[-_])",re.IGNORECASE)),
)

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
def campaign_literal_leaks(rows):
    leaks=[]
    for no,row in enumerate(rows,1):
        raw=canon(row)
        hits=[label for label,pattern in CAMPAIGN_LITERAL_PATTERNS if pattern.search(raw)]
        if hits: leaks.append((no,hits))
    return leaks

def main(trp,vap):
    tr,tbad=load(trp); va,vbad=load(vap)
    tc=[canon(x) for x in tr]; vc=[canon(x) for x in va]
    tp={x["messages"][1]["content"] for x in tr}; vp={x["messages"][1]["content"] for x in va}
    tleaks=campaign_literal_leaks(tr); vleaks=campaign_literal_leaks(va)
    r={
        "schema":"claycog-corpus-validation/v2",
        "canonical_code_validator":"validate_sft_v1.py",
        "campaign_binding_layer":"external_campaign_descriptor",
        "train_lines":len(tr),"validation_lines":len(va),
        "train_structural_invalid":len(tbad),"validation_structural_invalid":len(vbad),
        "train_campaign_literal_leaks":len(tleaks),"validation_campaign_literal_leaks":len(vleaks),
        "campaign_literal_leak_examples":{"train":tleaks[:10],"validation":vleaks[:10]},
        "train_unique":len(set(tc)),"validation_unique":len(set(vc)),
        "exact_cross_split_overlap":len(set(tc)&set(vc)),"prompt_cross_split_overlap":len(tp&vp),
        "train_sha256":sha(trp),"validation_sha256":sha(vap),
    }
    r["ok"]=(
        len(tr)==1485 and len(va)==165 and not tbad and not vbad and not tleaks and not vleaks
        and len(set(tc))==len(tc) and len(set(vc))==len(vc)
        and r["exact_cross_split_overlap"]==0 and r["prompt_cross_split_overlap"]==0
    )
    print(json.dumps(r,indent=2,sort_keys=True))
    return 0 if r["ok"] else 1

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: validate_corpus_v2.py train.jsonl validation.jsonl")
    raise SystemExit(main(sys.argv[1],sys.argv[2]))
