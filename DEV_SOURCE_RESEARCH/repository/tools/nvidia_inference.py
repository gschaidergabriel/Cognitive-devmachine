#!/usr/bin/env python3
"""FREE_ONLY facade over the canonical NVIDIA NIM adapter.

Canonical transport/model semantics live in tools/nvidia_nim.py. This facade exists only
for the autonomous ClayCode controller and adds a strict no-paid-fallback policy plus
code-retrieval defaults. It intentionally never returns provider reasoning traces.
"""
from __future__ import annotations
import json
from typing import Any
import nvidia_nim as nim

DEFAULT_EMBED_MODEL="nvidia/nv-embedcode-7b-v1"
DEFAULT_RERANK_MODEL="nvidia/llama-nemotron-rerank-vl-1b-v2"
class FreeOnlyViolation(RuntimeError): pass
class RateLimited(RuntimeError): pass


def _free_guard(fn,*args,**kwargs):
    try:return fn(*args,**kwargs)
    except Exception as exc:
        text=str(exc)
        if "HTTP 402" in text or "payment required" in text.lower():raise FreeOnlyViolation("NVIDIA FREE_ONLY endpoint refused request; paid fallback forbidden") from exc
        if "HTTP 429" in text or "rate limit" in text.lower():raise RateLimited(text[:600]) from exc
        raise


def list_models()->list[dict[str,Any]]:return _free_guard(nim.list_models)


def chat(prompt:str,*,model:str,system:str|None=None,max_tokens:int=2048,temperature:float=0.1)->dict[str,Any]:
    raw=_free_guard(nim.chat,prompt,model=model,system=system,max_tokens=max_tokens,temperature=temperature)
    return {"provider":"NVIDIA Hosted NIM","model":model,"content":raw.get("content") or "","finish_reason":raw.get("finish_reason"),"usage":raw.get("usage") or {},"reasoning_trace_persisted":False}


def embed(inputs:list[str]|str,*,model:str=DEFAULT_EMBED_MODEL,input_type:str="query")->dict[str,Any]:
    vals=[inputs] if isinstance(inputs,str) else list(inputs)
    raw=_free_guard(nim.embeddings,vals,model=model,input_type=input_type,truncate="END")
    return {"provider":"NVIDIA Hosted NIM","model":model,"input_type":input_type,"data":raw.get("data") or [],"usage":raw.get("usage") or {}}


def rerank(query:str,passages:list[str],*,model:str=DEFAULT_RERANK_MODEL)->dict[str,Any]:
    return _free_guard(nim.rerank,query,passages[:512],model=model,truncate="END")


def family(model_id:str)->str:
    x=model_id.lower()
    for key in ("nemotron","deepseek","qwen","glm","mistral","llama","gemma","phi","devstral","codestral","kimi","gpt-oss","poolside","granite"):
        if key in x:return key
    return x.split("/")[0]


def smoke_test()->dict[str,Any]:
    models=list_models(); ids=[str(x.get("id")) for x in models if x.get("id")]
    return {"status":"RUNTIME_VERIFIED_FREE_ENDPOINT_DISCOVERY","provider":"NVIDIA Hosted NIM","model_count":len(ids),"sample_models":ids[:20],"free_only":True,"canonical_adapter":"tools/nvidia_nim.py","reranker":DEFAULT_RERANK_MODEL}

if __name__=="__main__":print(json.dumps(smoke_test(),ensure_ascii=False,indent=2))
