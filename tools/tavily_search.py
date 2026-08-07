#!/usr/bin/env python3
"""Tavily Search API adapter for FRANK/RAE.

Uses the canonical RAE credential loader and never prints the API key. Tavily output is
classified as web-discovery evidence; downstream verification should prefer the
primary/authoritative sources discovered by the search.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rae_secret_loader import get_secret, secret_source  # noqa: E402

ENDPOINT = "https://api.tavily.com/search"
DEFAULT_TIMEOUT = 45
MAX_RETRIES = 4


def _request(payload: dict, *, timeout: int = DEFAULT_TIMEOUT) -> dict:
    key = get_secret("TAVILY_API_KEY")
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "FRANK-RAE/8.8 Tavily research adapter",
    }
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(ENDPOINT, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == MAX_RETRIES - 1:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                raise RuntimeError(f"Tavily HTTP {exc.code}: {detail}") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 8)
            time.sleep(delay)
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"Tavily request failed: {last_error}")


def search(
    query: str,
    *,
    max_results: int = 5,
    search_depth: str = "basic",
    topic: str = "general",
    include_answer: bool = False,
    include_raw_content: bool = False,
    safe_search: bool = False,
) -> dict:
    max_results = max(1, min(max_results, 20))
    payload = {
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "topic": topic,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
        "include_images": False,
        "include_image_descriptions": False,
        "include_favicon": False,
        "auto_parameters": False,
        "safe_search": safe_search,
    }
    data = _request(payload)
    results = []
    for item in data.get("results") or []:
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content"),
            "score": item.get("score"),
            "raw_content": item.get("raw_content") if include_raw_content else None,
        })
    return {
        "provider": "Tavily",
        "tool": "tavily_search",
        "evidence_class": "external_web_discovery",
        "query": query,
        "answer": data.get("answer") if include_answer else None,
        "results": results,
        "response_time": data.get("response_time"),
        "request_id": data.get("request_id"),
        "usage": data.get("usage"),
    }


def smoke_test() -> dict:
    data = search("OpenAlex API official documentation", max_results=1, search_depth="basic")
    if not data.get("results"):
        raise RuntimeError("Tavily smoke test returned no results")
    return {
        "schema_version": "1.0",
        "provider": "Tavily",
        "tool": "tavily_search",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_source": secret_source("TAVILY_API_KEY"),
        "credential_value_persisted_here": False,
        "verification_endpoint_class": "search",
        "request_id": data.get("request_id"),
        "usage": data.get("usage"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Tavily web research adapter")
    ap.add_argument("query", nargs="?", help="web search query")
    ap.add_argument("--max-results", type=int, default=5)
    ap.add_argument("--search-depth", choices=["basic", "advanced"], default="basic")
    ap.add_argument("--topic", choices=["general", "news"], default="general")
    ap.add_argument("--include-answer", action="store_true")
    ap.add_argument("--include-raw-content", action="store_true")
    ap.add_argument("--safe-search", action="store_true")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        out = smoke_test()
    else:
        if not args.query:
            ap.error("query is required unless --smoke-test is used")
        out = search(
            args.query,
            max_results=args.max_results,
            search_depth=args.search_depth,
            topic=args.topic,
            include_answer=args.include_answer,
            include_raw_content=args.include_raw_content,
            safe_search=args.safe_search,
        )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
