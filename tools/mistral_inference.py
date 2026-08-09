#!/usr/bin/env python3
"""FREE_ONLY Mistral reasoning adapter for Clay research.

The adapter uses only the account's existing Free Mode. HTTP 402/payment-required is a
hard stop and is never converted into paid usage. HTTP 429 is a cooldown condition.
Provider reasoning traces are intentionally not returned/persisted; only final text and
usage metadata leave this adapter.
"""
from __future__ import annotations
import json, urllib.error, urllib.request
from typing import Any
from rae_secret_loader import get_secret

BASE="https://api.mistral.ai/v1"
class FreeOnlyViolation(RuntimeError): pass
class RateLimited(RuntimeError): pass


def _request(path:str, body:dict[str,Any]|None=None, timeout:int=120)->Any:
    key=get_secret("MISTRAL_API_KEY")
    data=None if body is None else json.dumps(body).encode("utf-8")
    req=urllib.request.Request(BASE+path,data=data,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","Accept":"application/json","User-Agent":"Clay/0.1 FREE_ONLY research runtime"},method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as resp:return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text=exc.read().decode("utf-8",errors="replace")[:2000]
        if exc.code==402: raise FreeOnlyViolation(f"Mistral FREE_ONLY rejected paid usage: HTTP 402: {text}") from exc
        if exc.code==429: raise RateLimited(f"Mistral rate limited: {text}") from exc
        raise RuntimeError(f"Mistral HTTP {exc.code}: {text}") from exc


def list_models()->list[dict[str,Any]]:
    raw=_request("/models")
    return list(raw.get("data",raw if isinstance(raw,list) else []))


def _answer_text(content:Any)->str:
    if isinstance(content,str): return content
    out=[]
    if isinstance(content,list):
        for c in content:
            if isinstance(c,dict) and c.get("type")=="text": out.append(str(c.get("text") or ""))
    return "".join(out)


def chat(prompt:str,*,model:str="mistral-small-latest",system:str|None=None,max_tokens:int=2048,temperature:float=0.1,reasoning_effort:str="high",n:int=1,json_mode:bool=False,prompt_cache_key:str|None="claycode-base-v1")->dict[str,Any]:
    msgs=[]
    if system: msgs.append({"role":"system","content":system})
    msgs.append({"role":"user","content":prompt})
    body={"model":model,"messages":msgs,"max_tokens":max(1,min(int(max_tokens),4096)),"temperature":max(0.0,min(float(temperature),1.0)),"reasoning_effort":reasoning_effort,"n":max(1,min(int(n),4))}
    if prompt_cache_key: body["prompt_cache_key"]=prompt_cache_key
    if json_mode: body["response_format"]={"type":"json_object"}
    raw=_request("/chat/completions",body)
    choices=raw.get("choices") or []
    return {"provider":"Mistral","model":model,"answers":[{"content":_answer_text((c.get("message") or {}).get("content")),"finish_reason":c.get("finish_reason")} for c in choices],"usage":raw.get("usage") or {},"reasoning_trace_persisted":False}


def capabilities()->dict[str,Any]:
    models=list_models()
    return {"provider":"Mistral","free_only":True,"models":[{"id":m.get("id"),"capabilities":m.get("capabilities") or {},"max_context_length":m.get("max_context_length")} for m in models]}

if __name__=="__main__": print(json.dumps(capabilities(),ensure_ascii=False,indent=2))
