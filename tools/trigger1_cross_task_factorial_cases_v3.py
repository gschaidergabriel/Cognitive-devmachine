#!/usr/bin/env python3
"""Generate preregistration-grade cross-task structural J-Space cases.

Execution-free. Semantic class stays evaluator-side. Model prompts contain only
opaque formal demonstrations and probes. The design is exactly factorial in
semantic target x opaque output code x query polarity, with independent
replication and task-family separation.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any, Callable

SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_FACTORIAL_CASESET/v3"
CASE_SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_FACTORIAL_CASE/v3"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
POLARITIES = (0, 1)
REPLICATES = (0, 1)
CAL_FAMILIES = ("IMP", "TEMP", "SET")
HOLD_FAMILIES = ("ROUTE", "INHERIT", "BALANCE")
BANNED_MODEL_FACING = (
    "affirmative", "negative", "neutral", "approve", "approval", "approved",
    "reject", "rejection", "rejected", "accept", "accepted", "decline", "declined",
    "grant", "granted", "refuse", "refused", "support", "oppose", "yes", "no",
    "entail", "entailed", "contradict", "contradiction", "unknown", "undecided",
    "defer", "deferred", "allow", "allowed", "disallow", "disallowed",
)
STRUCTURAL_WHITELIST = {"no_think", "A", "B", "C", "d", "d1", "d2", "d3", "x", "q"}


def _sha(v: Any) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _psha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _perm_for(target: str, code: str, variant: int) -> dict[str, str]:
    others_t = [t for t in TARGETS if t != target]
    others_c = [c for c in CODES if c != code]
    if variant % 2:
        others_c.reverse()
    m = {target: code}
    m.update(zip(others_t, others_c))
    assert set(m) == set(TARGETS) and set(m.values()) == set(CODES)
    return m


def _bank(prefix: str, family: str, replicate: int) -> list[str]:
    return [f"{prefix}{family.lower()}{replicate}{chr(107+i)}" for i in range(12)]


def _imp(target: str, pol: int, z: list[str]) -> str:
    a,b,c,d = z[:4]; q=c; nq=f"!{c}"; ask=nq if pol else q
    if target == "AFFIRMATIVE": body=f"{a};{a}>{b};{b}>{'!'+c if pol else c}"
    elif target == "NEGATIVE": body=f"{a};{a}>{b};{b}>{c if pol else '!'+c}"
    else: body=f"{a};{a}>{b};{d}"
    return f"{{{body}?{ask}}}"


def _temp(target: str, pol: int, z: list[str]) -> str:
    a,b,c,d = z[:4]; q=f"{a}<{c}"; nq=f"!({q})"; ask=nq if pol else q
    if target == "AFFIRMATIVE": body=f"{a}<{b};{b}<{c}" if not pol else f"{c}<{b};{b}<{a}"
    elif target == "NEGATIVE": body=f"{c}<{b};{b}<{a}" if not pol else f"{a}<{b};{b}<{c}"
    else: body=f"{a}<{b};{d}<{c}"
    return f"[{body}??{ask}]"


def _set(target: str, pol: int, z: list[str]) -> str:
    e,s,t,u = z[:4]; q=f"{e}@{t}"; nq=f"!{q}"; ask=nq if pol else q
    if target == "AFFIRMATIVE": body=f"{e}@{s};{s}^{t}" if not pol else f"!{e}@{s};{s}^{t}"
    elif target == "NEGATIVE": body=f"!{e}@{s};{s}^{t}" if not pol else f"{e}@{s};{s}^{t}"
    else: body=f"{e}@{s};{s}^{u}"
    return f"<{body}::{ask}>"


def _route(target: str, pol: int, z: list[str]) -> str:
    a,b,c,d = z[:4]; q=f"{a}~{c}"; nq=f"!{q}"; ask=nq if pol else q
    if target == "AFFIRMATIVE": body=f"{a}~{b};{b}~{c}" if not pol else f"{c}~{b};{b}~{a}"
    elif target == "NEGATIVE": body=f"{c}~{b};{b}~{a}" if not pol else f"{a}~{b};{b}~{c}"
    else: body=f"{a}~{b};{d}~{c}"
    return f"({body}|?{ask})"


def _inherit(target: str, pol: int, z: list[str]) -> str:
    e,a,b,c = z[:4]; q=f"{e}:{b}"; nq=f"!{q}"; ask=nq if pol else q
    if target == "AFFIRMATIVE": body=f"{e}:{a};{a}/{b}" if not pol else f"!{e}:{a};{a}/{b}"
    elif target == "NEGATIVE": body=f"!{e}:{a};{a}/{b}" if not pol else f"{e}:{a};{a}/{b}"
    else: body=f"{e}:{a};{a}/{c}"
    return f"%{body}%{ask}%"


def _balance(target: str, pol: int, z: list[str]) -> str:
    a,b,c,d = z[:4]; q=f"{a}={c}"; nq=f"!{q}"; ask=nq if pol else q
    if target == "AFFIRMATIVE": body=f"{a}={b};{b}={c}" if not pol else f"{a}!={b};{b}={c}"
    elif target == "NEGATIVE": body=f"{a}!={b};{b}={c}" if not pol else f"{a}={b};{b}={c}"
    else: body=f"{a}={b};{d}={c}"
    return f"${body}$?${ask}$"


RENDERERS: dict[str, Callable[[str,int,list[str]],str]] = {
    "IMP": _imp, "TEMP": _temp, "SET": _set,
    "ROUTE": _route, "INHERIT": _inherit, "BALANCE": _balance,
}


def _demo(mapping: dict[str,str], family: str, prefix: str, rep: int) -> str:
    render=RENDERERS[family]; chunks=[]
    for i,t in enumerate(TARGETS):
        pol=(i+rep)%2
        z=_bank(prefix+"dm", family, rep+i)
        chunks.append(f"d{i+1}{render(t,pol,z)}={mapping[t]}")
    return "|".join(chunks)


def _content_tokens(prompt: str) -> set[str]:
    raw=set(re.findall(r"[A-Za-z_]+[A-Za-z0-9_]*", prompt))
    return {x for x in raw if x not in STRUCTURAL_WHITELIST}


def build_family(split: str, family: str) -> dict[str,Any]:
    prefix = "c" if split == "CALIBRATION" else "h"
    cases=[]
    for ti,target in enumerate(TARGETS):
      for ci,code in enumerate(CODES):
       for pol in POLARITIES:
        for rep in REPLICATES:
         mapping=_perm_for(target,code,variant=rep)
         demo=_demo(mapping,family,prefix,rep)
         z=_bank(prefix+"pb",family,rep)
         probe=RENDERERS[family](target,pol,z)
         prompt=f"/no_think\n{demo}|x{probe}="
         toks=set(re.findall(r"[a-z_]+",prompt.lower()))
         leaked=[w for w in BANNED_MODEL_FACING if w in toks]
         if leaked:
             raise AssertionError((family,target,leaked,prompt))
         cid=f"{split.lower()}-{family.lower()}-t{ti}-c{ci}-p{pol}-r{rep}"
         cases.append({
           "schema":CASE_SCHEMA,"case_id":cid,"split":split,"task_family":family,
           "semantic_target":target,"output_code_identity":code,"probe_query_negated":bool(pol),
           "replicate":rep,"polarity_pair_id":f"{split.lower()}-{family.lower()}-t{ti}-c{ci}-r{rep}",
           "prompt":prompt,"prompt_sha256":_psha(prompt),"codebook":mapping,
           "model_facing_explicit_semantic_labels":False,
         })
    cells={}
    for c in cases:
      k=(c["semantic_target"],c["output_code_identity"],c["probe_query_negated"])
      cells[k]=cells.get(k,0)+1
    expected={(t,c,bool(p)) for t in TARGETS for c in CODES for p in POLARITIES}
    assert set(cells)==expected and set(cells.values())=={len(REPLICATES)}, cells
    return {"task_family":family,"split":split,"case_count":len(cases),"cell_counts":{"|".join(map(str,k)):v for k,v in sorted(cells.items())},"cases":cases}


def build_bundle() -> dict[str,Any]:
    cal=[build_family("CALIBRATION",f) for f in CAL_FAMILIES]
    hold=[build_family("HOLDOUT",f) for f in HOLD_FAMILIES]
    cal_vocab=set().union(*(_content_tokens(c["prompt"]) for fam in cal for c in fam["cases"]))
    hold_vocab=set().union(*(_content_tokens(c["prompt"]) for fam in hold for c in fam["cases"]))
    overlap=sorted(cal_vocab & hold_vocab)
    if overlap:
        raise AssertionError(f"CAL_HOLD_CONTENT_OVERLAP:{overlap}")
    prompts=[c["prompt_sha256"] for fam in cal+hold for c in fam["cases"]]
    assert len(prompts)==len(set(prompts))
    out={
      "schema":SCHEMA,
      "design":{
        "targets":list(TARGETS),"codes":list(CODES),"polarities":[False,True],
        "replicates_per_target_code_polarity_cell":len(REPLICATES),
        "cases_per_family":len(TARGETS)*len(CODES)*len(POLARITIES)*len(REPLICATES),
        "calibration_task_families":list(CAL_FAMILIES),"holdout_task_families":list(HOLD_FAMILIES),
        "semantic_target_model_facing":False,"gain_selection_on_holdout":False,
      },
      "calibration":cal,"holdout":hold,
      "lexical_disjointness":{"content_overlap":overlap,"pass":not overlap,"calibration_vocab_sha256":_sha(sorted(cal_vocab)),"holdout_vocab_sha256":_sha(sorted(hold_vocab))},
      "runtime_credit_minted":False,"holdout_opened_by_generator":False,"model_executed":False,
    }
    out["bundle_sha256"]=_sha(out)
    return out


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output"); a=ap.parse_args()
    b=build_bundle(); text=json.dumps(b,sort_keys=True,indent=2)+"\n"
    if a.output: Path(a.output).write_text(text)
    else: print(text,end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
