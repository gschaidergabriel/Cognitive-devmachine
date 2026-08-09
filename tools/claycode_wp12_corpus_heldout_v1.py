#!/usr/bin/env python3
"""Generate a deterministic, leak-audited ClayCode BASE train/heldout corpus.

Heldout families are structurally reserved rather than randomly split. Invalid examples
preserve expected diagnostic classes. This is executable evidence for CC-WP-12, not
training authorization and not a claim that the still-evolving full language is frozen.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from claycode_base_pure_toolchain import ClayError, compile_source

TRAIN = ROOT / "research_entity/claycode/corpus/base_train_v1.jsonl"
HELD = ROOT / "research_entity/claycode/corpus/base_heldout_v1.jsonl"
OUT = ROOT / "research_entity/claycode/autonomous/WP12_CORPUS_HELDOUT_RECEIPT.json"
SEED = 120012


def sh(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_surface(source: str) -> str:
    lines=[]
    for line in source.splitlines():
        line=line.split("//",1)[0]
        compact="".join(line.split())
        if compact: lines.append(compact)
    return "\n".join(lines)


def valid_record(split: str, family: str, source: str, entry: str, args: list[int | bool]) -> dict:
    compiled=compile_source(source)
    return {"split":split,"family":family,"kind":"POSITIVE","source":source,"entry":entry,"args":args,
            "source_sha256":sh(source),"surface_identity_sha256":sh(canonical_surface(source)),
            "semantic_hash":compiled["semantic_hash"],"expected":"COMPILE_PASS"}


def invalid_record(split: str, family: str, source: str) -> dict:
    error=None
    try: compile_source(source)
    except ClayError as exc: error=type(exc).__name__+":"+str(exc)
    if error is None: raise AssertionError(f"negative corpus unexpectedly compiled: {family}")
    return {"split":split,"family":family,"kind":"NEGATIVE","source":source,
            "source_sha256":sh(source),"surface_identity_sha256":sh(canonical_surface(source)),
            "semantic_hash":None,"expected":"COMPILE_REJECT","expected_error_prefix":error.split(":",1)[0],
            "observed_error":error}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in rows),encoding="utf-8")


def main() -> int:
    rng=random.Random(SEED); train=[]; held=[]
    for i in range(96):
        a=rng.randint(-50,50); b=rng.randint(-50,50); op=rng.choice(["+","-","*"])
        src=f"module corpus.train{i}\nfn f(x:Int,y:Int)->Int=x{op}y+{a}\n"
        train.append(valid_record("train","ARITH_COMPOSE",src,"f",[a,b]))
    for i in range(32):
        op=rng.choice([">","<"]); src=f"module corpus.cmptrain{i}\nfn f(x:Int,y:Int)->Bool=x{op}y\n"
        train.append(valid_record("train","STRICT_COMPARE",src,"f",[i,i-1]))
    for i in range(32):
        train.append(invalid_record("train","NEG_RETURN_TYPE",f"module corpus.badtrain{i}\nfn f(x:Int)->Bool=x+{i+1}\n"))

    for i in range(24):
        op=[">=","<=","==","!="][i%4]; src=f"module corpus.heldcmp{i}\nfn f(x:Int,y:Int)->Bool=x{op}y\n"
        held.append(valid_record("heldout","BOUNDARY_EQUALITY_COMPARE",src,"f",[i,i]))
    for i in range(24):
        k=i+2; src=f"module corpus.heldcall{i}\nfn g(x:Int)->Int=x*{k}\nfn f(x:Int)->Int=g(x)+1\n"
        held.append(valid_record("heldout","CROSS_FUNCTION_CALL",src,"f",[i]))
    for i in range(12):
        held.append(invalid_record("heldout","NEG_UNKNOWN_SYMBOL",f"module corpus.badheldsym{i}\nfn f(x:Int)->Int=x+unknown{i}\n"))
    for i in range(12):
        held.append(invalid_record("heldout","NEG_ARITY",f"module corpus.badheldarity{i}\nfn g(x:Int,y:Int)->Int=x+y\nfn f(x:Int)->Int=g(x)\n"))

    train_surface={x["surface_identity_sha256"] for x in train}; held_surface={x["surface_identity_sha256"] for x in held}
    train_source={x["source_sha256"] for x in train}; held_source={x["source_sha256"] for x in held}
    train_sem={x["semantic_hash"] for x in train if x["semantic_hash"]}; held_sem={x["semantic_hash"] for x in held if x["semantic_hash"]}
    train_families={x["family"] for x in train}; held_families={x["family"] for x in held}
    overlaps={"source_hash":sorted(train_source&held_source),"normalized_surface":sorted(train_surface&held_surface),
              "semantic_hash":sorted(train_sem&held_sem),"family":sorted(train_families&held_families)}
    leak_free=not any(overlaps.values())
    write_jsonl(TRAIN,train); write_jsonl(HELD,held)
    report={"schema_version":"1.0","generator":"claycode_wp12_corpus_heldout_v1.py","seed":SEED,
            "scope":"CURRENT_EXECUTABLE_PURE_CORE_CORPUS_NOT_FULL_LANGUAGE_FREEZE","counts_as_full_wp12_pass":False,
            "train_rows":len(train),"heldout_rows":len(held),
            "train_positive":sum(x["kind"]=="POSITIVE" for x in train),"train_negative":sum(x["kind"]=="NEGATIVE" for x in train),
            "heldout_positive":sum(x["kind"]=="POSITIVE" for x in held),"heldout_negative":sum(x["kind"]=="NEGATIVE" for x in held),
            "train_families":sorted(train_families),"heldout_families":sorted(held_families),"overlaps":overlaps,
            "leak_free":leak_free,"train_file_sha256":hashlib.sha256(TRAIN.read_bytes()).hexdigest(),
            "heldout_file_sha256":hashlib.sha256(HELD.read_bytes()).hexdigest(),"pass":leak_free,
            "promotion_dependency":"regenerate/freeze once full production language and negative diagnostic taxonomy are final; training authorization is separate"}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"pass":leak_free,"train":len(train),"heldout":len(held),"overlaps":{k:len(v) for k,v in overlaps.items()}}))
    return 0 if leak_free else 1

if __name__=="__main__": raise SystemExit(main())
