#!/usr/bin/env python3
"""Stable FREE_ONLY entrypoint for run_research_distillery.py.

Adds typed provider boundaries plus successor-dynamic credential/model/route economic
binding, fail-soft reviewer fallback, and explicit near-miss/underfill instrumentation.
External LLM secrets are unavailable to generic helper paths. A provider request can
occur only through route_bound_chat(): provider admission -> selected credential
materialization -> exact credential/route binding -> pre-network revalidation ->
request -> post-call authority revalidation -> FREE_LANE_EXECUTION_RECEIPT/v1.

Question admission deliberately remains owned by run_research_distillery.add_question;
this wrapper must not create a second SQL authority. Correlated fallback reviewer lanes
remain provisional-only and cannot mint canonical Distillery dataset acceptance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sqlite3
import statistics
import subprocess
import sys
from typing import Any

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0,str(TOOLS))
import run_research_distillery as d
from free_provider_admission import provider_is_admitted_free
from free_lane_provenance import binding_still_current, current_lane_binding, emit_execution_receipt

LLM_PROVIDERS=frozenset({"groq","mistral","nvidia","openrouter"})
SECRET_PROVIDER={
    "GROQ_API_KEY":"groq","MISTRAL_API_KEY":"mistral","NVIDIA_API_KEY":"nvidia",
    "NVIDIA_NIM_API_KEY":"nvidia","NGC_API_KEY":"nvidia","OPENROUTER_API_KEY":"openrouter",
}
UNTYPED_CREDENTIALED_SECRETS=frozenset({"TAVILY_API_KEY","EXA_API_KEY"})
UNTYPED_CREDENTIALED_PROVIDERS=frozenset({"tavily","exa"})
PROVIDER_ENDPOINT={
    "openrouter":"https://openrouter.ai/api/v1/chat/completions",
    "nvidia":"https://integrate.api.nvidia.com/v1/chat/completions",
    "mistral":"https://api.mistral.ai/v1/chat/completions",
    "groq":"https://api.groq.com/openai/v1/chat/completions",
}
PROVIDER_SECRET_NAMES={
    "openrouter":("OPENROUTER_API_KEY",),
    "nvidia":("NVIDIA_API_KEY","NVIDIA_NIM_API_KEY","NGC_API_KEY"),
    "mistral":("MISTRAL_API_KEY",),
    "groq":("GROQ_API_KEY",),
}

_ORIGINAL_SECRET=d.secret
_ORIGINAL_REQUEST_JSON=d.request_json
_ORIGINAL_REVIEW=d.review_candidate


def _git_text(*args: str) -> str:
    try:
        proc=subprocess.run(
            ["git","-C",str(d.ROOT),*args],
            text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            timeout=5,check=False,
        )
        return proc.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _source_identity() -> dict[str,str]:
    return {"commit":_git_text("rev-parse","HEAD"),"tree":_git_text("rev-parse","HEAD^{tree}")}


def _key_fingerprint(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:10]


def _request_id(headers: dict[str,str], payload: Any) -> str | None:
    for key in ("x-request-id","request-id","x-groq-request-id","cf-ray"):
        if headers.get(key):
            return str(headers[key])
    if isinstance(payload,dict):
        for key in ("id","request_id"):
            if payload.get(key):
                return str(payload[key])
    return None


def admitted_secret(name: str) -> str:
    if name in SECRET_PROVIDER or name in UNTYPED_CREDENTIALED_SECRETS:
        return ""
    return _ORIGINAL_SECRET(name)


def admitted_request_json(provider: str, owner: str, url: str, *, key: str = "", payload: dict | None = None,
                          headers: dict[str,str] | None = None, timeout: float = 90.0):
    normalized=str(provider).strip().lower()
    if normalized in LLM_PROVIDERS:
        return 412, {}, {"error":"LLM_PROVIDER_CALL_REQUIRES_ROUTE_BOUND_CHAT"}
    if normalized in UNTYPED_CREDENTIALED_PROVIDERS:
        return 412, {}, {"error":"PROVIDER_NOT_IN_TYPED_FREE_ADMISSION_AUTHORITY"}
    if normalized=="github":
        if not url.startswith("https://api.github.com/"):
            return 412, {}, {"error":"PUBLIC_SOURCE_HOST_NOT_ADMITTED"}
        auth_headers={str(k).lower() for k in (headers or {})}
        if key or "authorization" in auth_headers:
            return 412, {}, {"error":"PUBLIC_SOURCE_CREDENTIALS_FORBIDDEN"}
    return _ORIGINAL_REQUEST_JSON(provider,owner,url,key=key,payload=payload,headers=headers,timeout=timeout)


def _provider_secret(provider: str) -> str:
    for name in PROVIDER_SECRET_NAMES.get(provider,()):
        value=str(_ORIGINAL_SECRET(name) or "").strip()
        if value:
            return value
    return ""


def _result_digest(status: int, body: Any) -> tuple[int | str,str]:
    if status == 0:
        error_class="UNKNOWN"
        if isinstance(body,dict):
            error_class=str(body.get("error") or "UNKNOWN").split(":",1)[0][:120]
        compact={"outcome":"UNKNOWN","transport_error_class":error_class}
        digest=hashlib.sha256(json.dumps(compact,sort_keys=True).encode("utf-8")).hexdigest()
        return "TRANSPORT_EXCEPTION_UNKNOWN_OUTCOME",digest
    digest=hashlib.sha256(
        json.dumps(body,sort_keys=True,ensure_ascii=False,default=str).encode("utf-8")
    ).hexdigest()
    return status,digest


def route_bound_chat(provider: str, model: str, prompt: str, max_tokens: int = 700,
                     temperature: float = 0.3) -> tuple[bool,str,dict,str]:
    normalized=str(provider).strip().lower()
    if normalized not in LLM_PROVIDERS:
        return False,"",{},"PROVIDER_NOT_ROUTE_BOUND_LLM"
    if not provider_is_admitted_free(normalized):
        return False,"",{},"PROVIDER_NOT_TYPED_FREE_ADMITTED"

    endpoint=PROVIDER_ENDPOINT[normalized]
    key=_provider_secret(normalized)
    if not key:
        return False,"",{},"NO_KEY"
    fp=_key_fingerprint(key)

    binding=current_lane_binding(
        normalized,fp,model,endpoint,artifacts=d.WORKER_ROOT,
    )
    if not binding.get("ok"):
        return False,"",{},f"FREE_LANE_BINDING_BLOCKED:{binding.get('reason','UNKNOWN')}"
    if not binding_still_current(binding):
        return False,"",{},"FREE_LANE_BINDING_STALE_BEFORE_NETWORK"

    payload={
        "model":model,
        "messages":[{"role":"user","content":prompt}],
        "temperature":temperature,
        "max_tokens":max_tokens,
        "stream":False,
    }
    status,headers,body=_ORIGINAL_REQUEST_JSON(
        normalized,f"distillery:{model}",endpoint,key=key,payload=payload,timeout=150,
    )
    stable_after=binding_still_current(binding)
    usage=body.get("usage") if isinstance(body,dict) and isinstance(body.get("usage"),dict) else {}
    receipt_status,digest=_result_digest(status,body)
    emit_execution_receipt(
        provider=normalized,
        credential_fingerprint=fp,
        model_or_route=model,
        endpoint=endpoint,
        binding=binding,
        request_id=_request_id(headers,body),
        usage=usage,
        http_status=receipt_status,
        result_digest=digest,
        source_commit_and_tree=_source_identity(),
        binding_stable_after_call=stable_after,
        artifacts=d.WORKER_ROOT,
    )
    if status == 0:
        return False,"",usage,"TRANSPORT_EXCEPTION_UNKNOWN_OUTCOME"
    if not stable_after:
        return False,"",usage,"FREE_LANE_BINDING_CHANGED_DURING_NETWORK"
    if not (200 <= status < 300) or not isinstance(body,dict):
        return False,"",usage,f"HTTP_{status}"
    try:
        text=body["choices"][0]["message"]["content"] or ""
    except Exception:
        text=""
    return bool(text),str(text),usage,"OK"


def openrouter_catalog() -> list[dict]:
    return [{"id":"openrouter/free","pricing":{"prompt":"0","completion":"0"},
             "economic_source":"governance/FREE_LANE_ECONOMIC_PROVENANCE_2026-08-24.json"}]


d.secret=admitted_secret
d.request_json=admitted_request_json
d.chat=route_bound_chat
d.openrouter_catalog=openrouter_catalog


def _size_hint(model_id: str) -> float | None:
    low=model_id.lower(); m=re.search(r"a(\d+(?:\.\d+)?)b",low)
    if m:return float(m.group(1))
    vals=[]
    for x in re.findall(r"(?:^|[-_/])(\d+(?:\.\d+)?)b(?:[-_/.:]|$)",low):
        try:vals.append(float(x))
        except ValueError:pass
    return min(vals) if vals else None


def select_small_models(catalog: list[dict]) -> list[str]:
    for card in catalog:
        if str(card.get("id") or "")=="openrouter/free" and d.price_zero(card):
            return ["openrouter/free"]
    return []


def select_reviewers(catalog: list[dict]) -> list[tuple[str,str,str]]:
    out=[]
    if provider_is_admitted_free("nvidia"):
        out.append(("nvidia_reviewer","nvidia","nvidia/llama-3.3-nemotron-super-49b-v1"))
    if provider_is_admitted_free("openrouter"):
        while len(out)<3:
            out.append((f"fallback_free_router_{len(out)}","openrouter","openrouter/free"))
    return out[:3]


def _bump(con: sqlite3.Connection,key: str,n: int=1) -> None:
    try:d.bump(con,key,n)
    except Exception:pass


def review_candidate(con: sqlite3.Connection, cid: str, reviewers: list[tuple[str,str,str]]):
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
    if not provisional["hard"] and sum(gaps)<=0.22:
        _bump(con,"near_miss_candidates"); con.commit(); provisional["near_miss"]=True
        d.emit("knowledge_near_miss",candidate=cid,review=provisional)
    else:
        _bump(con,"clear_reject_candidates"); con.commit(); provisional["near_miss"]=False
        d.emit("knowledge_clear_reject",candidate=cid,review=provisional)
    return False,provisional


d.select_small_models=select_small_models
d.select_reviewers=select_reviewers
d.review_candidate=review_candidate

if __name__=="__main__":
    raise SystemExit(d.main())
