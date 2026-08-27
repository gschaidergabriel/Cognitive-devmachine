#!/usr/bin/env python3
"""Token-efficient OpenAlex adapter for FRANK/RAE.

Uses OPENALEX_API_KEY through rae_secret_loader. Secret values are never printed.
Default output is compact scholarly metadata suitable for source discovery; primary
papers/publisher sources remain preferred for final verification.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from rae_secret_loader import SecretError, get_secret, secret_source

BASE = "https://api.openalex.org"
DEFAULT_SELECT = "id,doi,display_name,publication_year,publication_date,type,cited_by_count,primary_location,open_access,authorships,topics"
USER_AGENT = "FRANK-RAE/8.8 scholarly-research-adapter"


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if k.lower() in {"api_key", "key", "token"} else _sanitize(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value


def _get(path: str, params: dict[str, Any], retries: int = 3) -> dict[str, Any]:
    api_key = get_secret("OPENALEX_API_KEY")
    safe_params = {k: v for k, v in params.items() if v is not None and v != ""}
    safe_params["api_key"] = api_key
    url = f"{BASE}{path}?{urllib.parse.urlencode(safe_params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return _sanitize(payload)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 or 500 <= exc.code < 600:
                if attempt < retries:
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 8)
                    time.sleep(delay)
                    continue
            body = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"OpenAlex HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RuntimeError(f"OpenAlex network error: {exc.reason}") from exc
    raise RuntimeError("OpenAlex request failed")


def search_works(query: str, *, per_page: int = 25, filter_expr: str | None = None,
                 sort: str | None = None, cursor: str | None = None,
                 select: str = DEFAULT_SELECT) -> dict[str, Any]:
    if not 1 <= per_page <= 100:
        raise ValueError("per_page must be between 1 and 100")
    payload = _get("/works", {
        "search": query,
        "filter": filter_expr,
        "sort": sort,
        "per_page": per_page,
        "cursor": cursor,
        "select": select,
    })
    return {
        "provider": "OpenAlex",
        "tool": "openalex_search",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "credential_source": secret_source("OPENALEX_API_KEY"),
        "query": query,
        "filter": filter_expr,
        "meta": payload.get("meta", {}),
        "results": payload.get("results", []),
    }


def smoke_test() -> dict[str, Any]:
    payload = _get("/rate-limit", {})
    return {
        "provider": "OpenAlex",
        "tool": "openalex_search",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_source": secret_source("OPENALEX_API_KEY"),
        "rate_limit": payload,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="FRANK/RAE OpenAlex scholarly search")
    ap.add_argument("query", nargs="?", help="full-text works search")
    ap.add_argument("--per-page", type=int, default=25)
    ap.add_argument("--filter")
    ap.add_argument("--sort")
    ap.add_argument("--cursor")
    ap.add_argument("--select", default=DEFAULT_SELECT)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.smoke_test:
            out = smoke_test()
        else:
            if not args.query:
                ap.error("query is required unless --smoke-test is used")
            out = search_works(args.query, per_page=args.per_page, filter_expr=args.filter,
                               sort=args.sort, cursor=args.cursor, select=args.select)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except (SecretError, ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc))


if __name__ == "__main__":
    main()
