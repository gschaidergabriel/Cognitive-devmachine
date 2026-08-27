#!/usr/bin/env python3
"""Exa Search API adapter for FRANK/RAE.

Uses the canonical RAE credential loader and never prints the API key. Exa is a
web-discovery capability; discovered primary/authoritative sources remain the preferred
verification target.
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

ENDPOINT = "https://api.exa.ai/search"
DEFAULT_TIMEOUT = 45
MAX_RETRIES = 4


def _request(payload: dict, *, timeout: int = DEFAULT_TIMEOUT) -> dict:
    key = get_secret("EXA_API_KEY")
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "x-api-key": key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "FRANK-RAE/8.8 Exa research adapter",
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
                raise RuntimeError(f"Exa HTTP {exc.code}: {detail}") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 8)
            time.sleep(delay)
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"Exa request failed: {last_error}")


def search(query: str, *, num_results: int = 5, include_domains: list[str] | None = None,
           exclude_domains: list[str] | None = None, highlights: bool = True,
           text: bool = False) -> dict:
    num_results = max(1, min(num_results, 100))
    payload: dict = {
        "query": query,
        "numResults": num_results,
    }
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains
    contents: dict = {}
    if highlights:
        contents["highlights"] = True
    if text:
        contents["text"] = True
    if contents:
        payload["contents"] = contents

    data = _request(payload)
    results = []
    for item in data.get("results") or []:
        results.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "url": item.get("url"),
            "published_date": item.get("publishedDate"),
            "author": item.get("author"),
            "text": item.get("text") if text else None,
            "highlights": item.get("highlights") if highlights else None,
            "highlight_scores": item.get("highlightScores") if highlights else None,
            "summary": item.get("summary"),
        })
    return {
        "provider": "Exa",
        "tool": "exa_search",
        "evidence_class": "external_web_discovery",
        "query": query,
        "results": results,
        "request_id": data.get("requestId"),
        "resolved_search_type": data.get("resolvedSearchType"),
        "cost_dollars": data.get("costDollars"),
    }


def smoke_test() -> dict:
    data = search("OpenAlex API official documentation", num_results=1, highlights=False)
    if not data.get("results"):
        raise RuntimeError("Exa smoke test returned no results")
    return {
        "schema_version": "1.0",
        "provider": "Exa",
        "tool": "exa_search",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_source": secret_source("EXA_API_KEY"),
        "credential_value_persisted_here": False,
        "verification_endpoint_class": "search",
        "request_id": data.get("request_id"),
        "cost_dollars": data.get("cost_dollars"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Exa semantic web research adapter")
    ap.add_argument("query", nargs="?", help="web search query")
    ap.add_argument("--num-results", type=int, default=5)
    ap.add_argument("--include-domain", action="append", default=[])
    ap.add_argument("--exclude-domain", action="append", default=[])
    ap.add_argument("--no-highlights", action="store_true")
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        out = smoke_test()
    else:
        if not args.query:
            ap.error("query is required unless --smoke-test is used")
        out = search(
            args.query,
            num_results=args.num_results,
            include_domains=args.include_domain or None,
            exclude_domains=args.exclude_domain or None,
            highlights=not args.no_highlights,
            text=args.text,
        )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
