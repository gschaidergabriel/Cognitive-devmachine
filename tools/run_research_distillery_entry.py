#!/usr/bin/env python3
"""Stable FREE_ONLY entrypoint for run_research_distillery.py.

Adds typed provider boundaries, efficient free-model selection, fail-soft reviewer
fallback, and explicit near-miss/underfill instrumentation. Thresholds are not
silently weakened: near misses are telemetry so a zero-yield pipeline is
explainable rather than opaque.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sqlite3
import statistics
import sys

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0,str(TOOLS))
import run_research_distillery as d
from free_provider_admission import provider_is_admitted_free

LLM_PROVIDERS=frozenset({"groq","mistral","nvidia","openrouter"})
SECRET_PROVIDER={
    "GROQ_API_KEY":"groq","MISTRAL_API_KEY":"mistral","NVIDIA_API_KEY":"nvidia",
    "NVIDIA_NIM_API_KEY":"nvidia","NGC_API_KEY":"nvidia","OPENROUTER_API_KEY":"openrouter",
}
UNTYPED_CREDENTIALED_SECRETS=frozenset({"TAVILY_API_KEY","EXA_API_KEY"})
UNTYPED_CREDENTIALED_PROVIDERS=frozenset({"tavily","exa"})

_ORIGINAL_SECRET=d.secret
_ORIGINAL_REQUEST_JSON=d.request_json
_ORIGINAL_SELECT_REVIEWERS=d.select_reviewers
_ORIGINAL_REVIEW=d.review_candidate


def admitted_secret(name: str) -> str:
    provider=SECRET_PROVIDER.get(name)
    if provider is not None:
        if not provider_is_admitted_free(provider): return ""
        return _ORIGINAL_SECRET(name)
    if name in UNTYPED_CREDENTIALED_SECRETS:return ""
    return _ORIGINAL_SECRET(name)


def admitted_request_json(provider: str, owner: str, url: str, *, key: str = "", payload: dict | None = None,
                          headers: dict[str,str] | None = None, timeout: float = 90.0):
    normalized=str(provider).strip().lower()
    if normalized in LLM_PROVIDERS and not provider_is_admitted_free(normalized):
        return 412, {}, {"error":"PROVIDER_NOT_TYPED_FREE_ADMITTED"}
    if normalized in UNTYPED_CREDENTIALED_PROVIDERS:
        return 412, {}, {"error":"PROVIDER_NOT_IN_TYPED_FREE_ADMISSION_AUTHORITY"}
    return _ORIGINAL_REQUEST_JSON(provider,owner,url,key=key,payload=payload,headers=headers,timeout=timeout)


d.secret=admitted_secret
d.request_json=admitted_request_json


def add_question(con: sqlite3.Connection, question: str, *, parent_id: str | None = None,
                 root_problem: str | None = None, depth: int = 0, priority: float = 1.0,
                 worker_sha: str | None = None) -> bool:
    q=re.sub(r"\s+"," ",question).strip()[:1200]
    if len(q)<20:return False
    for row in con.execute("SELECT question FROM questions ORDER BY created_at DESC LIMIT 1000"):
        if q.lower()==row[0].lower() or d.jaccard(q,row[0])>=0.88:return False
    qid="q-"+hashlib.sha256(q.encode()).hexdigest()[:16]; root=root_problem or q
    try:
        con.execute("INSERT INTO questions(id,parent_id,root_problem,question,depth,priority,status,created_at,last_touched,source_worker_sha) VALUES(?,?,?,?,?,?,'OPEN',?,?,?)",
                    (qid,parent_id,root,q,depth,float(priority),d.now_iso(),None,worker_sha))
    except sqlite3.IntegrityError:return False
    return True


def _size_hint(model_id: str) -> float | None:
    low=model_id.lower(); m=re.search(r"a(\d+(?:\.\d+)?)b",low)
    if m:return float(m.group(1))
    vals=[]
    for x in re.findall(r"(?:^|[-_/])(\d+(?:\.\d+)?)b(?:[-_/.:]|$)",low):
        try:vals.append(float(x))
        except ValueError:pass
    return min(vals) if vals else None


def select_small_models(catalog: list[dict]) -> list[str]:
    ranked=[]
    for card in catalog:
        mid=str(card.get("id") or ""); low=mid.lower()
        if not mid or not d.price_zero(card):continue
        if any(x in low for x in ("image","audio","embed","rerank","guard","moderation")):continue
        size=_size_hint(mid)
        rank=(0 if size is not None and abs(size-4.0)<0.6 else 1 if size is not None else 2,
              abs(size-4.0) if size is not None else 999.0,size or 999.0,mid)
        ranked.append((rank,mid))
    ranked.sort(key=lambda x:x[0]); out=[]
    for _,m in ranked:
        if m not in out:out.append(m)
    return out[:8]


def select_reviewers(catalog: list[dict]) -> list[tuple[str,str,str]]:
    preferred=_ORIGINAL_SELECT_REVIEWERS(catalog)
    preferred=[x for x in preferred if x[1] not in LLM_PROVIDERS or provider_is_admitted_free(x[1])]
    mistral=sum(1 for lane,provider,model in preferred if "mistral" in lane.lower() or "mistral" in model.lower())
    if mistral>=2:return preferred[:3]
    nvidia=next((x for x in preferred if x[0]=="nvidia_reviewer"),None)
    out=[nvidia] if nvidia else []
    if not provider_is_admitted_free("openrouter"):return out
    used={x[2] for x in out}
    for model in select_small_models(catalog):
        if model in used:continue
        out.append((f"fallback_reviewer_{len(out)}","openrouter",model)); used.add(model)
        if len(out)>=3:break
    return out


def _bump(con: sqlite3.Connection,key: str,n: int=1) -> None:
    try:d.bump(con,key,n)
    except Exception:pass


def review_candidate(con: sqlite3.Connection, cid: str, reviewers: list[tuple[str,str,str]]):
    reviewers=[r for r in reviewers if r[1] not in LLM_PROVIDERS or provider_is_admitted_free(r[1])]
    accepted,agg=_ORIGINAL_REVIEW(con,cid,reviewers)
    requested_mistral=sum(
        1 for lane,provider,model in reviewers
        if provider=="mistral" or "mistral" in lane.lower() or "mistral" in model.lower()
    )
    if accepted and requested_mistral>=2:
        agg=dict(agg or {}); agg["panel_class"]="PREFERRED_NVIDIA_PLUS_MISTRAL"; return True,agg
    rows=con.execute("SELECT lane,provider,model,intrinsic_consistency,grf_compatibility,project_fit,novelty,hard_contradiction FROM review_votes WHERE candidate_id=?",(cid,)).fetchall()
    latest={str(r[0]):r for r in rows}; votes=list(latest.values())
    if len(votes)<3:
        _bump(con,"review_underfilled"); con.commit()
        agg=dict(agg or {}); agg["panel_class"]="UNDERFILLED"; agg["votes_observed"]=len(votes)
        d.emit("review_underfilled",candidate=cid,votes=len(votes),required=3)
        return False,agg
    has_nvidia=any(str(r[0])=="nvidia_reviewer" for r in votes)
    actual_mistral=sum(1 for r in votes if str(r[1])=="mistral" or "mistral" in str(r[0]).lower() or "mistral" in str(r[2]).lower())
    if not has_nvidia:
        _bump(con,"review_underfilled_no_nvidia"); con.commit(); agg=dict(agg or {}); agg["panel_class"]="UNDERFILLED_NO_NVIDIA"; return False,agg
    def med(idx:int)->float:return float(statistics.median(float(r[idx] or 0.0) for r in votes))
    provisional={
        "votes":len(votes),"intrinsic":med(3),"grf":med(4),"fit":med(5),"novelty":med(6),
        "hard":any(bool(r[7]) for r in votes),"lanes":[str(r[0]) for r in votes],
        "panel_class":"PREFERRED_NVIDIA_PLUS_MISTRAL" if actual_mistral>=2 else "PROVISIONAL_NON_MISTRAL_FALLBACK",
        "independence_class":"PREFERRED_PANEL" if actual_mistral>=2 else "GOODMAN_COLLAPSED_FREE_ROUTER_FALLBACK",
    }
    thresholds=(0.72,0.65,0.55,0.45) if actual_mistral>=2 else (0.80,0.75,0.65,0.55)
    scores=(provisional["intrinsic"],provisional["grf"],provisional["fit"],provisional["novelty"])
    gaps=[max(0.0,t-s) for s,t in zip(scores,thresholds)]
    ok=(not provisional["hard"] and all(s>=t for s,t in zip(scores,thresholds)))
    provisional["thresholds"]={"intrinsic":thresholds[0],"grf":thresholds[1],"fit":thresholds[2],"novelty":thresholds[3]}
    provisional["score_gaps"]={"intrinsic":gaps[0],"grf":gaps[1],"fit":gaps[2],"novelty":gaps[3]}
    if ok:
        if actual_mistral>=2:
            con.execute("UPDATE candidates SET status='ACCEPTED' WHERE id=?",(cid,)); _bump(con,"review_pass"); con.commit(); return True,provisional
        con.execute("UPDATE candidates SET status='PROVISIONAL_ACCEPTED' WHERE id=?",(cid,))
        _bump(con,"review_provisional_pass"); con.commit()
        provisional["canonical_acceptance"]=False
        d.emit("knowledge_provisional_accept",candidate=cid,review=provisional)
        return False,provisional
    # Near miss = structurally sound, no hard contradiction, and total threshold gap small.
    if not provisional["hard"] and sum(gaps)<=0.22:
        _bump(con,"near_miss_candidates"); con.commit(); provisional["near_miss"]=True
        d.emit("knowledge_near_miss",candidate=cid,review=provisional)
    else:
        _bump(con,"clear_reject_candidates"); con.commit(); provisional["near_miss"]=False
        d.emit("knowledge_clear_reject",candidate=cid,review=provisional)
    return False,provisional


d.add_question=add_question
d.select_small_models=select_small_models
d.select_reviewers=select_reviewers
d.review_candidate=review_candidate

if __name__=="__main__":
    raise SystemExit(d.main())
