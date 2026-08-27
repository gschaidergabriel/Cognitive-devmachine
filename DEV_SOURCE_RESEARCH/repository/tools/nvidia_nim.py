#!/usr/bin/env python3
"""NVIDIA hosted NIM adapter for Clay research.

Exposes separated capabilities for model catalog, chat, embeddings, embedding similarity
and reranking. Credentials are loaded only through the secret loader and never emitted.
Provider reasoning traces are deliberately not returned or persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rae_secret_loader import get_secret, secret_source

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research_entity" / "runtime" / "tool_results"
BASE_URL = "https://integrate.api.nvidia.com/v1"
USER_AGENT = "Clay/0.1 research-runtime"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
MAX_RATE_RETRIES = 8

DEFAULT_EMBED_MODEL = "nvidia/nv-embedqa-e5-v5"
DEFAULT_RERANK_MODEL = "nvidia/llama-nemotron-rerank-vl-1b-v2"
RERANK_ENDPOINTS = {
    # Current NVIDIA hosted route (2026-08 verification target).
    "nvidia/llama-nemotron-rerank-vl-1b-v2": "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-vl-1b-v2/reranking",
    "nvidia/llama-nemotron-rerank-1b-v2": "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-1b-v2/reranking",
    # Historical routes retained only for reproducibility of old receipts; not defaults.
    "nvidia/rerank-qa-mistral-4b": "https://ai.api.nvidia.com/v1/retrieval/nvidia/rerank-qa-mistral-4b/reranking",
    "nvidia/llama-3.2-nv-rerankqa-1b-v2": "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-3_2-nv-rerankqa-1b-v2/reranking",
}


def _retry_seconds(exc: urllib.error.HTTPError, body: str, attempt: int) -> float:
    header = exc.headers.get("Retry-After") if exc.headers else None
    if header:
        try:
            return max(0.5, min(float(header) + 0.25, 60.0))
        except ValueError:
            pass
    match = re.search(r"(?:try again in|retry after)\s+([0-9.]+)\s*(ms|s)", body, flags=re.I)
    if match:
        value = float(match.group(1)) / (1000.0 if match.group(2).lower() == "ms" else 1.0)
        return max(0.5, min(value + 0.25, 60.0))
    return min(2.0 + attempt * 2.0, 30.0)


def _request_url(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    key = get_secret("NVIDIA_API_KEY")
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    for attempt in range(MAX_RATE_RETRIES + 1):
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="GET" if payload is None else "POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:3000]
            if exc.code == 429 and attempt < MAX_RATE_RETRIES:
                time.sleep(_retry_seconds(exc, body, attempt))
                continue
            raise RuntimeError(f"NVIDIA HTTP {exc.code}: {body[:1500]}") from exc
    raise RuntimeError("NVIDIA request retry loop exhausted")


def _request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _request_url(BASE_URL + path, payload)


def list_models() -> list[dict[str, Any]]:
    raw = _request("/models")
    return raw.get("data", []) if isinstance(raw, dict) else []


def model_ids() -> list[str]:
    return [str(x.get("id")) for x in list_models() if x.get("id")]


def chat(prompt: str, *, model: str, max_tokens: int = 512, temperature: float = 0.0, system: str | None = None) -> dict[str, Any]:
    if not prompt.strip():
        raise ValueError("prompt required")
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    raw = _request(
        "/chat/completions",
        {
            "model": model,
            "messages": messages,
            "max_tokens": max(1, min(int(max_tokens), 8192)),
            "temperature": max(0.0, min(float(temperature), 2.0)),
            "stream": False,
        },
    )
    choice = (raw.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    return {
        "provider": "NVIDIA Hosted NIM",
        "capability": "chat_completions",
        "model": model,
        "content": message.get("content") or "",
        "finish_reason": choice.get("finish_reason"),
        "usage": raw.get("usage") or {},
        "reasoning_trace_persisted": False,
        "evidence_role": "external_model_runtime",
    }


def embeddings(inputs: list[str], *, model: str = DEFAULT_EMBED_MODEL, input_type: str = "query", truncate: str = "END") -> dict[str, Any]:
    if not inputs or any(not str(x).strip() for x in inputs):
        raise ValueError("non-empty inputs required")
    if input_type not in {"query", "passage"}:
        raise ValueError("input_type must be query or passage")
    raw = _request(
        "/embeddings",
        {
            "model": model,
            "input": [str(x) for x in inputs],
            "input_type": input_type,
            "truncate": truncate,
            "encoding_format": "float",
        },
    )
    vectors = []
    for row in raw.get("data") or []:
        vector = row.get("embedding") or []
        vectors.append({"index": row.get("index"), "dimensions": len(vector), "embedding": vector})
    return {
        "provider": "NVIDIA Hosted NIM",
        "capability": "embeddings",
        "model": model,
        "input_type": input_type,
        "data": vectors,
        "usage": raw.get("usage") or {},
        "evidence_role": "external_embedding_runtime",
    }


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def embedding_similarity(texts: list[str], pairs: list[list[int]], *, model: str = DEFAULT_EMBED_MODEL) -> dict[str, Any]:
    embedded = embeddings(texts, model=model, input_type="passage", truncate="END")
    rows = embedded["data"]
    vecs = [row["embedding"] for row in rows]
    out = []
    for pair in pairs:
        if len(pair) != 2:
            raise ValueError("each pair must contain exactly two indices")
        i, j = int(pair[0]), int(pair[1])
        if i < 0 or j < 0 or i >= len(vecs) or j >= len(vecs):
            raise ValueError("pair index out of range")
        out.append({"i": i, "j": j, "cosine": _cosine(vecs[i], vecs[j]), "text_i": texts[i], "text_j": texts[j]})
    return {
        "provider": "NVIDIA Hosted NIM",
        "capability": "embedding_similarity",
        "model": model,
        "dimensions": rows[0]["dimensions"] if rows else 0,
        "pairs": out,
        "evidence_role": "external_embedding_runtime_proxy_for_semantic_geometry",
        "boundary": "Embedding similarity is not causal identity, role identity, canonical truth, authority or latent hidden-state equivalence."
    }


def rerank(query: str, passages: list[str], *, model: str = DEFAULT_RERANK_MODEL, truncate: str = "END") -> dict[str, Any]:
    if not query.strip() or not passages or any(not str(x).strip() for x in passages):
        raise ValueError("query and non-empty passages required")
    payload = {
        "model": model,
        "query": {"text": query},
        "passages": [{"text": str(x)} for x in passages],
        "truncate": truncate,
    }
    endpoint = RERANK_ENDPOINTS.get(model)
    route = "model_bound_function_endpoint" if endpoint else "generic_v1_ranking"
    raw = _request_url(endpoint, payload) if endpoint else _request("/ranking", payload)
    rankings = raw.get("rankings") or raw.get("data") or []
    return {
        "provider": "NVIDIA Hosted NIM",
        "capability": "reranking",
        "model": model,
        "route": route,
        "rankings": rankings,
        "usage": raw.get("usage") or {},
        "evidence_role": "external_reranker_runtime",
    }


def _clean_error(text: str) -> str:
    text = re.sub(r"account\s+['\"][^'\"]+['\"]", "account [REDACTED]", text, flags=re.I)
    return text[:2000]


def process_request(path: Path) -> dict[str, Any]:
    req = json.loads(path.read_text(encoding="utf-8"))
    rid = str(req.get("request_id") or path.stem)
    if not ID_RE.fullmatch(rid):
        raise ValueError("invalid request_id")
    mode = str(req.get("mode") or "list_models")
    envelope: dict[str, Any] = {
        "schema_version": "1.1",
        "request_id": rid,
        "tool": "nvidia_nim",
        "request_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        if mode == "list_models":
            ids = model_ids()
            envelope["result"] = {
                "provider": "NVIDIA Hosted NIM",
                "capability": "model_catalog",
                "models": ids,
                "model_count": len(ids),
                "credential_source": secret_source("NVIDIA_API_KEY"),
                "credential_value_exposed": False,
            }
        elif mode == "chat":
            envelope["result"] = chat(
                str(req.get("prompt") or ""),
                model=str(req.get("model") or ""),
                max_tokens=int(req.get("max_tokens") or 512),
                temperature=float(req.get("temperature") or 0.0),
                system=str(req.get("system")) if req.get("system") else None,
            )
        elif mode == "embeddings":
            values = req.get("input")
            if isinstance(values, str):
                values = [values]
            envelope["result"] = embeddings(
                list(values or []),
                model=str(req.get("model") or DEFAULT_EMBED_MODEL),
                input_type=str(req.get("input_type") or "query"),
                truncate=str(req.get("truncate") or "END"),
            )
        elif mode == "embedding_similarity":
            envelope["result"] = embedding_similarity(
                [str(x) for x in (req.get("texts") or [])],
                [[int(y) for y in x] for x in (req.get("pairs") or [])],
                model=str(req.get("model") or DEFAULT_EMBED_MODEL),
            )
        elif mode == "rerank":
            envelope["result"] = rerank(
                str(req.get("query") or ""),
                [str(x) for x in (req.get("passages") or [])],
                model=str(req.get("model") or DEFAULT_RERANK_MODEL),
                truncate=str(req.get("truncate") or "END"),
            )
        else:
            raise ValueError(f"unsupported mode: {mode}")
        envelope["status"] = "SUCCESS"
    except Exception as exc:
        envelope["status"] = "FAILED"
        envelope["error_type"] = type(exc).__name__
        envelope["error"] = _clean_error(str(exc))
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{rid}.json"
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"request_id": rid, "status": envelope["status"], "result_path": str(out.relative_to(ROOT))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    args = ap.parse_args()
    print(json.dumps(process_request(Path(args.request)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
