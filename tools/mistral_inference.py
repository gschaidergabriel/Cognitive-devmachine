#!/usr/bin/env python3
"""FREE_ONLY Mistral capability adapter for Clay research.

Uses only the account's existing Free Mode. HTTP 402/payment-required is a hard stop and
is never converted into paid usage. HTTP 429 is a cooldown condition. Provider reasoning
traces are intentionally not returned/persisted; only final text and usage metadata leave
this adapter.
"""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from rae_secret_loader import get_secret, secret_source

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/"research_entity/runtime/tool_results"
BASE="https://api.mistral.ai/v1"
ID_RE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
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


def fim(prefix:str,*,suffix:str="",model:str="codestral-latest",max_tokens:int=1024,prompt_cache_key:str|None="claycode-fim-v1")->dict[str,Any]:
    if not prefix: raise ValueError("prefix required")
    body={"model":model,"prompt":prefix,"suffix":suffix,"max_tokens":max(1,min(int(max_tokens),4096))}
    if prompt_cache_key: body["prompt_cache_key"]=prompt_cache_key
    raw=_request("/fim/completions",body)
    choice=(raw.get("choices") or [{}])[0]
    return {"provider":"Mistral","model":model,"capability":"fim","content":choice.get("text") or ((choice.get("message") or {}).get("content") or ""),"finish_reason":choice.get("finish_reason"),"usage":raw.get("usage") or {}}


def embeddings(inputs:list[str]|str,*,model:str="mistral-embed")->dict[str,Any]:
    vals=[inputs] if isinstance(inputs,str) else list(inputs)
    raw=_request("/embeddings",{"model":model,"input":vals,"encoding_format":"float"})
    return {"provider":"Mistral","model":model,"capability":"embeddings","data":raw.get("data") or [],"usage":raw.get("usage") or {}}


def capabilities()->dict[str,Any]:
    models=list_models()
    return {"provider":"Mistral","free_only":True,"credential_source":secret_source("MISTRAL_API_KEY"),"credential_value_exposed":False,"models":[{"id":m.get("id"),"capabilities":m.get("capabilities") or {},"max_context_length":m.get("max_context_length")} for m in models],"implemented_adapter_modes":["models","chat_reasoning","structured_json","multi_completion","prompt_cache","fim","embeddings"],"discovery_only_until_account_free_verified":["batch","ocr","vision","classification","conversations","hosted_tools/connectors"]}


def process_request(path:Path)->dict[str,Any]:
    req=json.loads(path.read_text(encoding="utf-8")); rid=str(req.get("request_id") or path.stem)
    if not ID_RE.fullmatch(rid):raise ValueError("invalid request_id")
    mode=str(req.get("mode") or "models")
    env={"schema_version":"1.0","request_id":rid,"tool":"mistral_inference","request_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"processed_at":datetime.now(timezone.utc).isoformat(),"free_only":True}
    try:
        if mode=="models": env["result"]=capabilities()
        elif mode=="chat": env["result"]=chat(str(req.get("prompt") or ""),model=str(req.get("model") or "mistral-small-latest"),system=str(req.get("system")) if req.get("system") else None,max_tokens=int(req.get("max_tokens") or 1024),temperature=float(req.get("temperature") or 0.05),reasoning_effort=str(req.get("reasoning_effort") or "high"),n=int(req.get("n") or 1),json_mode=bool(req.get("json_mode",False)),prompt_cache_key=str(req.get("prompt_cache_key") or "clay-research-v1"))
        elif mode=="fim": env["result"]=fim(str(req.get("prefix") or ""),suffix=str(req.get("suffix") or ""),model=str(req.get("model") or "codestral-latest"),max_tokens=int(req.get("max_tokens") or 1024))
        elif mode=="embeddings": env["result"]=embeddings(req.get("input") or [],model=str(req.get("model") or "mistral-embed"))
        else: raise ValueError(f"unsupported mode: {mode}")
        env["status"]="SUCCESS"
    except Exception as exc:
        env["status"]="FAILED"; env["error_type"]=type(exc).__name__; env["error"]=str(exc)[:2000]
    RESULTS.mkdir(parents=True,exist_ok=True); out=RESULTS/f"{rid}.json"; out.write_text(json.dumps(env,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"request_id":rid,"status":env["status"],"result_path":str(out.relative_to(ROOT))}


def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument("--request"); ap.add_argument("--capabilities",action="store_true"); a=ap.parse_args()
    if a.request: print(json.dumps(process_request(Path(a.request)),ensure_ascii=False,indent=2))
    else: print(json.dumps(capabilities(),ensure_ascii=False,indent=2))

if __name__=="__main__": main()
