#!/usr/bin/env python3
"""FREE_ONLY NVIDIA API adapter for Clay research.

Supports hosted NVIDIA development endpoints only. HTTP 402/payment-required is a hard
provider stop. HTTP 429 is surfaced as a cooldown signal. No paid fallback exists here.
"""
from __future__ import annotations
import json, time, urllib.error, urllib.request
from typing import Any
from rae_secret_loader import get_secret

LLM_BASE = "https://integrate.api.nvidia.com/v1"
RERANK_URL = "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-3_2-nv-rerankqa-1b-v2/reranking"
DEFAULT_EMBED_MODEL = "nvidia/nv-embedcode-7b-v1"
DEFAULT_RERANK_MODEL = "nvidia/llama-3.2-nv-rerankqa-1b-v2"

class FreeOnlyViolation(RuntimeError): pass
class RateLimited(RuntimeError): pass


def _request(url: str, body: dict[str, Any] | None = None, timeout: int = 90) -> Any:
    key = get_secret("NVIDIA_API_KEY")
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json",
        "User-Agent": "Clay/0.1 FREE_ONLY research runtime"
    }, method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")[:2000]
        if exc.code == 402:
            raise FreeOnlyViolation(f"NVIDIA FREE_ONLY rejected paid endpoint: HTTP 402: {text}") from exc
        if exc.code == 429:
            raise RateLimited(f"NVIDIA rate limited: {text}") from exc
        raise RuntimeError(f"NVIDIA HTTP {exc.code}: {text}") from exc


def list_models() -> list[dict[str, Any]]:
    raw = _request(LLM_BASE + "/models")
    return list(raw.get("data", [])) if isinstance(raw, dict) else []


def chat(prompt: str, *, model: str, system: str | None = None, max_tokens: int = 2048, temperature: float = 0.1) -> dict[str, Any]:
    msgs=[]
    if system: msgs.append({"role":"system","content":system})
    msgs.append({"role":"user","content":prompt})
    raw=_request(LLM_BASE+"/chat/completions", {"model":model,"messages":msgs,"max_tokens":max(1,min(int(max_tokens),4096)),"temperature":max(0.0,min(float(temperature),1.0)),"stream":False})
    choice=(raw.get("choices") or [{}])[0]
    return {"provider":"NVIDIA","model":model,"content":((choice.get("message") or {}).get("content") or ""),"finish_reason":choice.get("finish_reason"),"usage":raw.get("usage") or {}}


def embed(inputs: list[str] | str, *, model: str = DEFAULT_EMBED_MODEL, input_type: str = "query") -> dict[str, Any]:
    if input_type not in {"query","passage"}: raise ValueError("input_type must be query|passage")
    raw=_request(LLM_BASE+"/embeddings", {"model":model,"input":inputs,"input_type":input_type,"encoding_format":"float","truncate":"END"})
    return {"provider":"NVIDIA","model":model,"input_type":input_type,"data":raw.get("data") or [],"usage":raw.get("usage") or {}}


def rerank(query: str, passages: list[str], *, model: str = DEFAULT_RERANK_MODEL) -> dict[str, Any]:
    if not passages: return {"provider":"NVIDIA","model":model,"rankings":[]}
    body={"model":model,"query":{"text":query},"passages":[{"text":p} for p in passages[:512]],"truncate":"END"}
    raw=_request(RERANK_URL, body)
    return {"provider":"NVIDIA","model":model,"rankings":raw.get("rankings") or raw.get("data") or raw}


def family(model_id: str) -> str:
    x=model_id.lower()
    for key in ("nemotron","deepseek","qwen","glm","mistral","llama","gemma","phi"):
        if key in x: return key
    return x.split("/")[0]


def smoke_test() -> dict[str, Any]:
    models=list_models()
    ids=[str(x.get("id")) for x in models if x.get("id")]
    return {"status":"RUNTIME_VERIFIED_FREE_ENDPOINT_DISCOVERY","provider":"NVIDIA","model_count":len(ids),"sample_models":ids[:20],"free_only":True}

if __name__ == "__main__":
    print(json.dumps(smoke_test(), ensure_ascii=False, indent=2))
