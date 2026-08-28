#!/usr/bin/env python3
"""Raw-evidence verifier for abstract Qwen3-0.6B native-cvec state control.

Recomputes claims that higher-level deconfound/scope envelopes may otherwise represent as
booleans/receipt hashes. No model execution and no credit minting occurs here; this only
verifies raw prompt/readout/intervention rows.
"""
from __future__ import annotations
import collections, math, re
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_RAW_EVIDENCE_GATE/v1"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_RAW_EVIDENCE/v1"
STATES = ("S0", "S1", "S2")
SPLITS = ("basis", "calibration", "holdout")
CODES = ("A", "B", "C")
CONTROLS = ("TARGET", "NULL", "SHUFFLED", "SIGN_FLIP")
MIN_FAMILIES = 6
MIN_ACC = 0.75
MIN_STATE_ACC = 2/3
MIN_TARGET_HIT = 0.75
MIN_MARGIN = 0.05
WORD_RE = re.compile(r"[a-z0-9]+", re.I)
FORBIDDEN = {
    "affirmative","negative","neutral","yes","no","agree","agreement","disagree",
    "accept","acceptance","reject","rejection","approve","approval","support","oppose",
    "allow","deny","grant","refuse","endorse","abstain","abstention","undecided",
}


def _words(s: str) -> set[str]:
    return {m.group(0).lower() for m in WORD_RE.finditer(s)}


def _num(x: Any) -> bool:
    return isinstance(x, (int,float)) and not isinstance(x,bool) and math.isfinite(float(x))


def _margin(scores: dict[str, Any], target: str, universe: tuple[str,...]) -> float:
    if not isinstance(scores, dict) or set(scores) != set(universe) or not all(_num(scores[x]) for x in universe):
        raise ValueError("SCORE_VECTOR_INVALID")
    others=[x for x in universe if x != target]
    return float(scores[target]) - sum(float(scores[x]) for x in others)/len(others)


def _prompts(a: dict[str,Any], failures:list[str]) -> dict[str,dict[str,Any]]:
    out={}; lex={}; design=a.get("prompt_design")
    if not isinstance(design,dict): failures.append("RAW_PROMPT_DESIGN_REQUIRED"); return out
    for split in SPLITS:
        rows=design.get(split)
        if not isinstance(rows,list) or not rows: failures.append(f"RAW_{split.upper()}_ROWS_REQUIRED"); continue
        case_ids=set(); families=collections.defaultdict(set); counts=collections.Counter(); words=set(); normalized=[]
        for i,row in enumerate(rows):
            p=f"RAW_{split.upper()}_{i}"; required=("case_id","family_id","state_id","scaffold_prefix","semantic_payload","scaffold_suffix","prompt")
            if not isinstance(row,dict): failures.append(p+"_OBJECT_REQUIRED"); continue
            if not all(isinstance(row.get(k),str) and row[k] for k in required): failures.append(p+"_FIELDS_REQUIRED"); continue
            if row["state_id"] not in STATES: failures.append(p+"_STATE_INVALID"); continue
            if row["case_id"] in case_ids: failures.append(p+"_DUPLICATE_CASE")
            case_ids.add(row["case_id"])
            if row["prompt"] != row["scaffold_prefix"]+row["semantic_payload"]+row["scaffold_suffix"]: failures.append(p+"_PROMPT_COMPOSITION_MISMATCH")
            bad=sorted(_words(row["prompt"]) & FORBIDDEN)
            if bad: failures.append(p+"_FORBIDDEN_LEXEME:"+",".join(bad))
            payload=_words(row["semantic_payload"])
            if not payload: failures.append(p+"_EMPTY_SEMANTIC_PAYLOAD")
            words |= payload; families[row["family_id"]].add(row["state_id"]); counts[row["state_id"]]+=1; normalized.append(row)
        if len(families) < MIN_FAMILIES: failures.append(f"RAW_{split.upper()}_MIN_FAMILIES")
        for fam,states in families.items():
            if states != set(STATES): failures.append(f"RAW_{split.upper()}_FAMILY_NOT_FULL:{fam}")
        c=[counts[s] for s in STATES]
        if min(c,default=0) <= 0 or len(set(c)) != 1: failures.append(f"RAW_{split.upper()}_STATE_IMBALANCE")
        out[split]={"rows":normalized,"case_ids":case_ids,"families":set(families)}; lex[split]=words
    for i,left in enumerate(SPLITS):
        for right in SPLITS[i+1:]:
            overlap=sorted(lex.get(left,set()) & lex.get(right,set()))
            if overlap: failures.append(f"RAW_LEXICAL_OVERLAP:{left.upper()}:{right.upper()}:{','.join(overlap[:24])}")
            if left in out and right in out:
                if out[left]["case_ids"] & out[right]["case_ids"]: failures.append(f"RAW_CASE_OVERLAP:{left.upper()}:{right.upper()}")
                if out[left]["families"] & out[right]["families"]: failures.append(f"RAW_FAMILY_OVERLAP:{left.upper()}:{right.upper()}")
    return out


def _readout(a:dict[str,Any], splits:dict[str,dict[str,Any]], failures:list[str]) -> dict[str,Any]:
    r=a.get("holdout_internal_readout")
    if not isinstance(r,list) or not r: failures.append("RAW_INTERNAL_READOUT_REQUIRED"); return {}
    expected=splits.get("holdout",{}).get("case_ids",set()); design={x["case_id"]:x for x in splits.get("holdout",{}).get("rows",[])}
    seen=set(); total=correct=0; t=collections.Counter(); c=collections.Counter()
    for i,row in enumerate(r):
        p=f"RAW_READOUT_{i}"
        if not isinstance(row,dict): failures.append(p+"_OBJECT_REQUIRED"); continue
        cid=row.get("case_id"); truth=row.get("true_state_id"); scores=row.get("scores")
        if cid not in expected or cid in seen: failures.append(p+"_CASE_INVALID"); continue
        seen.add(cid)
        if design[cid]["state_id"] != truth: failures.append(p+"_TRUTH_BINDING_MISMATCH"); continue
        try: pred=max(STATES,key=lambda s:float(scores[s])); _margin(scores,truth,STATES)
        except Exception: failures.append(p+"_SCORES_INVALID"); continue
        total+=1; t[truth]+=1; correct+=int(pred==truth); c[truth]+=int(pred==truth)
    if seen != expected: failures.append("RAW_READOUT_CASE_UNIVERSE_MISMATCH")
    acc=correct/total if total else 0.0; per={s:c[s]/t[s] if t[s] else 0.0 for s in STATES}
    if acc < MIN_ACC: failures.append("RAW_READOUT_ACCURACY_LOW")
    if any(per[s] < MIN_STATE_ACC for s in STATES): failures.append("RAW_READOUT_PER_STATE_ACCURACY_LOW")
    return {"accuracy":acc,"per_state_accuracy":per,"n":total}


def _causal(a:dict[str,Any], failures:list[str]) -> dict[str,Any]:
    rows=a.get("native_internal_causal_rows")
    if not isinstance(rows,list) or not rows: failures.append("RAW_NATIVE_CAUSAL_ROWS_REQUIRED"); return {}
    groups=collections.defaultdict(dict); hits=tot=0
    for i,row in enumerate(rows):
        p=f"RAW_CAUSAL_{i}"
        if not isinstance(row,dict): failures.append(p+"_OBJECT_REQUIRED"); continue
        carrier,target,control=row.get("carrier_case_id"),row.get("vector_state_id"),row.get("control")
        if not isinstance(carrier,str) or target not in STATES or control not in CONTROLS: failures.append(p+"_IDENTITY_INVALID"); continue
        try: m=_margin(row.get("scores"),target,STATES); pred=max(STATES,key=lambda s:float(row["scores"][s]))
        except Exception: failures.append(p+"_SCORES_INVALID"); continue
        if control in groups[(carrier,target)]: failures.append(p+"_DUPLICATE_CONTROL")
        groups[(carrier,target)][control]=m
        if control=="TARGET": tot+=1; hits+=int(pred==target)
    deltas={x:[] for x in CONTROLS if x!="TARGET"}
    for key,g in groups.items():
        if set(g)!=set(CONTROLS): failures.append("RAW_CAUSAL_CONTROL_SET_INCOMPLETE:"+":".join(key)); continue
        for ctrl in deltas: deltas[ctrl].append(g["TARGET"]-g[ctrl])
    for carrier in {x[0] for x in groups}:
        if {target for c,target in groups if c==carrier} != set(STATES): failures.append("RAW_CAUSAL_TARGET_SET_INCOMPLETE:"+carrier)
    hit=hits/tot if tot else 0.0; means={k:sum(v)/len(v) if v else None for k,v in deltas.items()}
    if hit < MIN_TARGET_HIT: failures.append("RAW_CAUSAL_TARGET_HIT_LOW")
    for k,v in means.items():
        if v is None or v < MIN_MARGIN: failures.append("RAW_CAUSAL_MARGIN_LOW:"+k)
    return {"target_hit_rate":hit,"mean_margin_delta":means,"groups":len(groups)}


def _behavior(a:dict[str,Any], failures:list[str]) -> dict[str,Any]:
    rows=a.get("opaque_code_rows")
    if not isinstance(rows,list) or not rows: failures.append("RAW_OPAQUE_CODE_ROWS_REQUIRED"); return {}
    groups=collections.defaultdict(dict); mappings={}; counts=collections.Counter()
    for i,row in enumerate(rows):
        p=f"RAW_OPAQUE_{i}"
        if not isinstance(row,dict): failures.append(p+"_OBJECT_REQUIRED"); continue
        carrier,target,mid,control=row.get("carrier_case_id"),row.get("vector_state_id"),row.get("mapping_id"),row.get("control")
        mp=row.get("state_to_code"); logits=row.get("code_logits")
        if not isinstance(carrier,str) or target not in STATES or not isinstance(mid,str) or control not in CONTROLS: failures.append(p+"_IDENTITY_INVALID"); continue
        if not isinstance(mp,dict) or set(mp)!=set(STATES) or set(mp.values())!=set(CODES): failures.append(p+"_MAPPING_INVALID"); continue
        try: m=_margin(logits,mp[target],CODES)
        except Exception: failures.append(p+"_LOGITS_INVALID"); continue
        key=(carrier,target,mid); groups[key][control]=m; mappings[key]=mp[target]
        if control=="TARGET": counts[(target,mp[target])]+=1
    deltas={x:[] for x in CONTROLS if x!="TARGET"}; bycode={c:[] for c in CODES}
    for key,g in groups.items():
        if set(g)!=set(CONTROLS): failures.append("RAW_OPAQUE_CONTROL_SET_INCOMPLETE:"+":".join(key)); continue
        for ctrl in deltas: deltas[ctrl].append(g["TARGET"]-g[ctrl])
        bycode[mappings[key]].append(g["TARGET"]-g["NULL"])
    for s in STATES:
        vals=[counts[(s,c)] for c in CODES]
        if min(vals,default=0)<=0 or len(set(vals))!=1: failures.append("RAW_OPAQUE_COUNTERBALANCE_FAIL:"+s)
    means={k:sum(v)/len(v) if v else None for k,v in deltas.items()}; code_means={k:sum(v)/len(v) if v else None for k,v in bycode.items()}
    for k,v in means.items():
        if v is None or v < MIN_MARGIN: failures.append("RAW_OPAQUE_MARGIN_LOW:"+k)
    if any(v is None or v <= 0 for v in code_means.values()): failures.append("RAW_OPAQUE_CODE_IDENTITY_REPLICATION_FAIL")
    return {"mean_margin_delta":means,"mean_target_vs_null_by_code":code_means,"groups":len(groups)}


def adjudicate(candidate:Any) -> dict[str,Any]:
    failures=[]
    if not isinstance(candidate,dict): candidate={}; failures.append("RAW_ATTESTATION_OBJECT_REQUIRED")
    if candidate.get("schema") != ATTESTATION_SCHEMA: failures.append("RAW_ATTESTATION_SCHEMA_MISMATCH")
    if candidate.get("token_scope") != "ALL_PROMPT_TOKENS": failures.append("RAW_NATIVE_ALL_PROMPT_TOKENS_REQUIRED")
    if candidate.get("historical_last_token_used_as_identity_premise") is not False: failures.append("RAW_LAST_TOKEN_IDENTITY_PREMISE_FORBIDDEN")
    splits=_prompts(candidate,failures); readout=_readout(candidate,splits,failures); causal=_causal(candidate,failures); behavior=_behavior(candidate,failures)
    passed=not failures
    return {"schema":SCHEMA,"raw_abstract_state_evidence_pass":passed,"failures":sorted(set(failures)),"readout":readout,"native_causal":causal,"opaque_code":behavior,"canonical_credit_minted":False,"jspace_model_runtime_credit":False,"canonical_semantics_promotion":False,"evidence_boundary":"Recomputed raw-evidence authenticity only. PASS does not execute a model or mint runtime/product/semantic credit."}
