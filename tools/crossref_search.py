#!/usr/bin/env python3
"""Crossref REST API adapter for FRANK/RAE.

Supports exact DOI lookup and bibliographic search. No API key is required. Optional
CROSSREF_MAILTO joins Crossref's polite pool. Output is bibliographic metadata, not
independent scientific confirmation.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rae_secret_loader import get_secret  # noqa: E402

BASE = "https://api.crossref.org"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 4


def _mailto() -> str | None:
    return get_secret("CROSSREF_MAILTO", required=False)


def _headers() -> dict[str, str]:
    # Crossref's REST endpoint reliably accepts ordinary JSON. The previous vendor
    # media type produced HTTP 406 on the current endpoint/runner combination.
    mailto = _mailto()
    contact = f"; mailto:{mailto}" if mailto else ""
    return {
        "Accept": "application/json",
        "User-Agent": f"FRANK-RAE/8.8 (Crossref metadata research adapter{contact})",
    }


def _request(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> tuple[dict, dict[str, str]]:
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=_headers())
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                response_headers = {k.lower(): v for k, v in resp.headers.items()}
                return payload, response_headers
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == MAX_RETRIES - 1:
                body = exc.read().decode("utf-8", errors="replace")[:500]
                raise RuntimeError(f"Crossref HTTP {exc.code}: {body}") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 8)
            time.sleep(delay)
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"Crossref network error: {exc.reason}") from exc
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"Crossref request failed: {last_error}")


def _params(extra: dict[str, str | int]) -> str:
    params: dict[str, str | int] = dict(extra)
    mailto = _mailto()
    if mailto:
        params["mailto"] = mailto
    return urllib.parse.urlencode(params)


def _compact_work(w: dict) -> dict:
    title = w.get("title") or []
    container = w.get("container-title") or []
    authors = []
    for a in w.get("author") or []:
        name = " ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip()
        if name:
            authors.append(name)
    issued = None
    parts = ((w.get("issued") or {}).get("date-parts") or [])
    if parts and parts[0]:
        issued = "-".join(str(x) for x in parts[0])
    return {
        "doi": w.get("DOI"),
        "title": title[0] if title else None,
        "authors": authors,
        "issued": issued,
        "type": w.get("type"),
        "publisher": w.get("publisher"),
        "container_title": container[0] if container else None,
        "url": w.get("URL"),
        "is_referenced_by_count": w.get("is-referenced-by-count"),
        "references_count": w.get("references-count"),
        "relation": w.get("relation"),
        "update_to": w.get("update-to"),
        "license": w.get("license"),
    }


def doi_lookup(doi: str) -> dict:
    doi = doi.strip()
    encoded = urllib.parse.quote(doi, safe="")
    query = _params({})
    url = f"{BASE}/works/{encoded}" + (f"?{query}" if query else "")
    payload, headers = _request(url)
    return {
        "provider": "Crossref",
        "tool": "crossref_lookup",
        "mode": "doi_lookup",
        "doi": doi,
        "message_type": payload.get("message-type"),
        "work": _compact_work(payload.get("message") or {}),
        "rate_limit": {
            "pool": headers.get("x-api-pool"),
            "limit": headers.get("x-rate-limit-limit"),
            "interval": headers.get("x-rate-limit-interval"),
            "type": headers.get("x-rate-limit-type"),
        },
    }


def works_search(query: str, rows: int = 10) -> dict:
    rows = max(1, min(rows, 100))
    qs = _params({"query.bibliographic": query, "rows": rows})
    payload, headers = _request(f"{BASE}/works?{qs}")
    msg = payload.get("message") or {}
    return {
        "provider": "Crossref",
        "tool": "crossref_lookup",
        "mode": "works_search",
        "query": query,
        "total_results": msg.get("total-results"),
        "items": [_compact_work(x) for x in msg.get("items") or []],
        "rate_limit": {
            "pool": headers.get("x-api-pool"),
            "limit": headers.get("x-rate-limit-limit"),
            "interval": headers.get("x-rate-limit-interval"),
            "type": headers.get("x-rate-limit-type"),
        },
    }


def smoke_test() -> dict:
    result = doi_lookup("10.1038/nphys1170")
    if (result.get("work", {}).get("doi") or "").lower() != "10.1038/nphys1170":
        raise RuntimeError("Crossref smoke test returned an unexpected DOI")
    return {
        "schema_version": "1.0",
        "provider": "Crossref",
        "tool": "crossref_lookup",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_required": False,
        "mailto_configured": bool(_mailto()),
        "verification_endpoint_class": "works/{doi}",
        "verified_doi": result["work"]["doi"],
        "rate_limit": result.get("rate_limit"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Crossref scholarly metadata adapter")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--doi", help="retrieve exact metadata for a DOI")
    group.add_argument("--query", help="bibliographic works search")
    group.add_argument("--smoke-test", action="store_true", help="verify live Crossref access")
    ap.add_argument("--rows", type=int, default=10, help="search result count (1-100)")
    args = ap.parse_args()
    if args.smoke_test:
        out = smoke_test()
    elif args.doi:
        out = doi_lookup(args.doi)
    else:
        out = works_search(args.query, args.rows)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
