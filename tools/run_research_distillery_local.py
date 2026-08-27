#!/usr/bin/env python3
"""Local-model fallback entrypoint for the Clay Research Distillery.

Imports the canonical typed-admission distillery entrypoint and adds one strictly
loopback model lane. External provider secret/network boundaries remain unchanged.
The local same-model reviewer panel is explicitly correlated/provisional and uses
stricter thresholds; it cannot masquerade as NVIDIA+Mistral independent evidence.
Local availability is re-evaluated each cycle so a model that becomes healthy after
Distillery startup can enter the noncanonical research lane without a process restart.
"""
from __future__ import annotations

import ipaddress
import json
import os
import sqlite3
import statistics
import sys
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:sys.path.insert(0,str(TOOLS))
import run_research_distillery as d
import run_research_distillery_entry as e  # installs canonical external-provider gates first


def _validated_loopback_base(raw:str)->str:
    """Return one unambiguous HTTP loopback origin or fail closed.

    The local lane is intentionally narrower than a generic OpenAI-compatible URL:
    it accepts only literal loopback IPs, so DNS, LAN/private hosts, userinfo tricks,
    paths, query strings and fragments cannot turn a local fallback into an external
    network/provider path.
    """
    value=str(raw or "").strip()
    try:
        parts=urllib.parse.urlsplit(value)
        port=parts.port  # force malformed-port validation now, before network I/O
    except (TypeError,ValueError) as ex:
        raise RuntimeError("CLAY_LOCAL_RESEARCH_BASE must be a valid HTTP loopback IP origin") from ex
    if parts.scheme.lower()!="http" or not parts.hostname:
        raise RuntimeError("CLAY_LOCAL_RESEARCH_BASE must use http:// with a loopback IP literal")
    if parts.username is not None or parts.password is not None:
        raise RuntimeError("CLAY_LOCAL_RESEARCH_BASE must not contain userinfo")
    if parts.path not in ("","/") or parts.query or parts.fragment:
        raise RuntimeError("CLAY_LOCAL_RESEARCH_BASE must be an origin without path, query, or fragment")
    if "%" in parts.hostname:
        raise RuntimeError("CLAY_LOCAL_RESEARCH_BASE must not use a scoped/zone-qualified address")
    try:
        addr=ipaddress.ip_address(parts.hostname)
    except ValueError as ex:
        raise RuntimeError("CLAY_LOCAL_RESEARCH_BASE hostname must be a literal loopback IP") from ex
    if not addr.is_loopback:
        raise RuntimeError("CLAY_LOCAL_RESEARCH_BASE must stay on the loopback interface")
    _=port
    return value.rstrip("/")


class _NoLocalRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow redirects: a loopback response must not redirect externally."""
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


# Ignore HTTP(S)_PROXY environment variables and reject redirects before a second socket
# can be opened. Combined with an IP-literal loopback base, this keeps the local lane
# local at the transport boundary rather than relying on provider-layer intent.
_LOCAL_OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}),_NoLocalRedirect())


def _local_urlopen(req,timeout:float):
    return _LOCAL_OPENER.open(req,timeout=timeout)


LOCAL_BASE=_validated_loopback_base(os.getenv("CLAY_LOCAL_RESEARCH_BASE","http://127.0.0.1:8088"))
LOCAL_LOGICAL_ID="local/Qwen3-4B-GGUF-Q4_K_M"
LOCAL_REVIEWERS=(
    ("local_reviewer_logic","local",LOCAL_LOGICAL_ID),
    ("local_reviewer_grf","local",LOCAL_LOGICAL_ID),
    ("local_reviewer_falsifier","local",LOCAL_LOGICAL_ID),
)
_PREV_CHAT=d.chat
_PREV_SMALL=d.select_small_models
_PREV_REVIEWERS=d.select_reviewers
_PREV_REVIEW=d.review_candidate
_PREV_ONE_CYCLE=d.one_cycle
_PREV_WRITE_STATUS=d.write_status

# Enables the FREE_ONLY loop but does not admit any external provider. External
# secret/socket access remains gated by run_research_distillery_entry.py.
os.environ.setdefault("CLAY_FREE_ONLY_ATTESTED","1")


def local_health()->bool:
    try:
        with _local_urlopen(LOCAL_BASE+"/health",timeout=1.5) as r:return 200<=int(r.status)<300
    except Exception:return False


def server_model_id()->str:
    try:
        with _local_urlopen(LOCAL_BASE+"/v1/models",timeout=2) as r:
            obj=json.loads(r.read().decode("utf-8",errors="replace"))
        data=obj.get("data") if isinstance(obj,dict) else None
        if isinstance(data,list) and data and isinstance(data[0],dict) and data[0].get("id"):return str(data[0]["id"])
    except Exception:pass
    return LOCAL_LOGICAL_ID


def local_chat(model:str,prompt:str,max_tokens:int=700,temperature:float=0.3):
    if "local_reviewer_logic" in prompt:temperature=0.0
    elif "local_reviewer_grf" in prompt:temperature=0.18
    elif "local_reviewer_falsifier" in prompt:temperature=0.38
    payload={"model":server_model_id(),"messages":[{"role":"user","content":prompt}],"temperature":temperature,"max_tokens":max_tokens,"stream":False}
    req=urllib.request.Request(LOCAL_BASE+"/v1/chat/completions",data=json.dumps(payload).encode(),method="POST",headers={"Content-Type":"application/json","User-Agent":"clay-local-distillery/1"})
    try:
        with _local_urlopen(req,timeout=240) as r:
            obj=json.loads(r.read().decode("utf-8",errors="replace"));status=int(r.status)
    except urllib.error.HTTPError as ex:return False,"",{},f"LOCAL_HTTP_{ex.code}"
    except Exception as ex:return False,"",{},f"LOCAL_{type(ex).__name__}"
    try:text=str(obj["choices"][0]["message"]["content"] or "")
    except Exception:text=""
    usage=obj.get("usage") if isinstance(obj,dict) and isinstance(obj.get("usage"),dict) else {}
    return bool(text) and 200<=status<300,text,usage,"OK"


def chat(provider:str,model:str,prompt:str,max_tokens:int=700,temperature:float=0.3):
    if provider=="local" or str(model).startswith("local/"):return local_chat(model,prompt,max_tokens,temperature)
    return _PREV_CHAT(provider,model,prompt,max_tokens=max_tokens,temperature=temperature)


def select_small_models(catalog:list[dict])->list[str]:
    out=[]
    if local_health():out.append(LOCAL_LOGICAL_ID)
    for m in _PREV_SMALL(catalog):
        if m not in out:out.append(m)
    return out[:8]


def select_reviewers(catalog:list[dict])->list[tuple[str,str,str]]:
    out=_PREV_REVIEWERS(catalog)
    if out:return out
    if local_health():return list(LOCAL_REVIEWERS)
    return []


def refresh_local_lanes(small_models:list[str],reviewers:list[tuple[str,str,str]])->tuple[list[str],list[tuple[str,str,str]]]:
    """Project current loopback health into the per-cycle research lane set.

    This is availability only, never provider/canonical authority. Existing external
    reviewer panels are preserved; a correlated local panel is used only when no
    external reviewer panel is present. A failed health check removes stale local
    lanes so a dead loopback model is not treated as available.
    """
    small=list(dict.fromkeys(str(m) for m in small_models if str(m)))
    rev=[tuple(r) for r in reviewers if isinstance(r,(tuple,list)) and len(r)==3]
    healthy=local_health()
    if healthy:
        if LOCAL_LOGICAL_ID not in small:small.insert(0,LOCAL_LOGICAL_ID)
        if not rev:rev=list(LOCAL_REVIEWERS)
    else:
        small=[m for m in small if m!=LOCAL_LOGICAL_ID]
        rev=[r for r in rev if str(r[1])!="local" and not str(r[2]).startswith("local/")]
    return small[:8],rev[:3]


def dynamic_one_cycle(con:sqlite3.Connection,small_models:list[str],reviewers:list[tuple[str,str,str]])->bool:
    live_small,live_reviewers=refresh_local_lanes(small_models,reviewers)
    return _PREV_ONE_CYCLE(con,live_small,live_reviewers)


def dynamic_write_status(con:sqlite3.Connection,reviewers:list[tuple[str,str,str]],small_models:list[str])->None:
    live_small,live_reviewers=refresh_local_lanes(small_models,reviewers)
    return _PREV_WRITE_STATUS(con,live_reviewers,live_small)


def review_candidate(con:sqlite3.Connection,cid:str,reviewers:list[tuple[str,str,str]]):
    accepted,agg=_PREV_REVIEW(con,cid,reviewers)
    if accepted:return True,agg
    if not reviewers or not all(r[1]=="local" for r in reviewers):return False,agg
    rows=con.execute("SELECT lane,provider,model,intrinsic_consistency,grf_compatibility,project_fit,novelty,hard_contradiction FROM review_votes WHERE candidate_id=?",(cid,)).fetchall()
    latest={str(r[0]):r for r in rows};votes=list(latest.values())
    if len(votes)<3:return False,{**(agg or {}),"panel_class":"PROVISIONAL_LOCAL_CORRELATED_UNDERFILLED"}
    def med(i:int)->float:return float(statistics.median(float(r[i] or 0.0) for r in votes))
    x={"votes":len(votes),"intrinsic":med(3),"grf":med(4),"fit":med(5),"novelty":med(6),"hard":any(bool(r[7]) for r in votes),"lanes":[str(r[0]) for r in votes],"panel_class":"PROVISIONAL_LOCAL_CORRELATED","independence_class":"CORRELATED_SAME_MODEL_MULTI_PASS"}
    thresholds=(0.90,0.85,0.75,0.65);scores=(x["intrinsic"],x["grf"],x["fit"],x["novelty"]);gaps=[max(0.0,t-s) for s,t in zip(scores,thresholds)]
    x["thresholds"]={k:v for k,v in zip(("intrinsic","grf","fit","novelty"),thresholds)};x["score_gaps"]={k:v for k,v in zip(("intrinsic","grf","fit","novelty"),gaps)}
    ok=(not x["hard"] and all(s>=t for s,t in zip(scores,thresholds)))
    if ok:
        con.execute("UPDATE candidates SET status='PROVISIONAL_ACCEPTED' WHERE id=?",(cid,))
        d.bump(con,"provisional_local_accept",1)
        x["canonical_dataset_commit_allowed"]=False
        con.commit()
        d.emit("knowledge_provisional_local_not_canonical",candidate=cid,review=x)
        return False,x
    if not x["hard"] and sum(gaps)<=0.22:d.bump(con,"near_miss_candidates",1);x["near_miss"]=True
    else:d.bump(con,"clear_reject_candidates",1);x["near_miss"]=False
    con.commit();return False,x


d.chat=chat
d.select_small_models=select_small_models
d.select_reviewers=select_reviewers
d.review_candidate=review_candidate
d.one_cycle=dynamic_one_cycle
d.write_status=dynamic_write_status
d.LOCAL_LANE_REFRESH_BINDING="LOCAL_HEALTH_REEVALUATED_EACH_CYCLE_V1"

if __name__=="__main__":raise SystemExit(d.main())