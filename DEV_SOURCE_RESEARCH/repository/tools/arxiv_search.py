#!/usr/bin/env python3
"""arXiv Atom API adapter for FRANK/RAE.

Credential-free scholarly preprint discovery via the classic arXiv API.
The adapter returns compact JSON metadata and preserves arXiv as PREPRINT evidence;
publication/peer-review status must be verified separately when decision-relevant.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

BASE = "https://export.arxiv.org/api/query"
USER_AGENT = "FRANK-RAE/8.8 arxiv-research-adapter"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}


def _text(node: ET.Element, path: str) -> str | None:
    child = node.find(path, NS)
    if child is None or child.text is None:
        return None
    return " ".join(child.text.split())


def _entry(entry: ET.Element) -> dict[str, Any]:
    authors = [
        _text(author, "atom:name")
        for author in entry.findall("atom:author", NS)
    ]
    authors = [a for a in authors if a]
    links = {}
    for link in entry.findall("atom:link", NS):
        rel = link.attrib.get("rel", "related")
        title = link.attrib.get("title") or rel
        href = link.attrib.get("href")
        if href:
            links[title] = href
    categories = [c.attrib.get("term") for c in entry.findall("atom:category", NS) if c.attrib.get("term")]
    primary = entry.find("arxiv:primary_category", NS)
    return {
        "id": _text(entry, "atom:id"),
        "title": _text(entry, "atom:title"),
        "summary": _text(entry, "atom:summary"),
        "published": _text(entry, "atom:published"),
        "updated": _text(entry, "atom:updated"),
        "authors": authors,
        "categories": categories,
        "primary_category": primary.attrib.get("term") if primary is not None else None,
        "doi": _text(entry, "arxiv:doi"),
        "journal_ref": _text(entry, "arxiv:journal_ref"),
        "comment": _text(entry, "arxiv:comment"),
        "links": links,
    }


def query(search_query: str, *, start: int = 0, max_results: int = 25,
          sort_by: str = "relevance", sort_order: str = "descending",
          retries: int = 3) -> dict[str, Any]:
    if not 1 <= max_results <= 100:
        raise ValueError("max_results must be between 1 and 100")
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/atom+xml"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                root = ET.fromstring(response.read())
            entries = [_entry(e) for e in root.findall("atom:entry", NS)]
            total = _text(root, "opensearch:totalResults")
            return {
                "provider": "arXiv",
                "tool": "arxiv_search",
                "evidence_class": "external_preprint",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "credential_required": False,
                "query": search_query,
                "start": start,
                "max_results": max_results,
                "total_results": int(total) if total and total.isdigit() else total,
                "results": entries,
            }
        except urllib.error.HTTPError as exc:
            if (exc.code == 429 or 500 <= exc.code < 600) and attempt < retries:
                time.sleep(max(3, min(3 * (attempt + 1), 12)))
                continue
            body = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"arXiv HTTP {exc.code}: {body}") from exc
        except (urllib.error.URLError, ET.ParseError) as exc:
            if attempt < retries:
                time.sleep(max(3, min(3 * (attempt + 1), 12)))
                continue
            raise RuntimeError(f"arXiv request failed: {exc}") from exc
    raise RuntimeError("arXiv request failed")


def smoke_test() -> dict[str, Any]:
    result = query("id:2106.14834", max_results=1)
    ok = bool(result.get("results"))
    if not ok:
        raise RuntimeError("arXiv smoke test returned no result")
    return {
        "provider": "arXiv",
        "tool": "arxiv_search",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_required": False,
        "verification_endpoint_class": "api_query",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="FRANK/RAE arXiv preprint search")
    ap.add_argument("query", nargs="?", help="arXiv search_query expression, e.g. all:\"global workspace\"")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--max-results", type=int, default=25)
    ap.add_argument("--sort-by", default="relevance", choices=["relevance", "lastUpdatedDate", "submittedDate"])
    ap.add_argument("--sort-order", default="descending", choices=["ascending", "descending"])
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.smoke_test:
            out = smoke_test()
        else:
            if not args.query:
                ap.error("query is required unless --smoke-test is used")
            out = query(args.query, start=args.start, max_results=args.max_results,
                        sort_by=args.sort_by, sort_order=args.sort_order)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc))


if __name__ == "__main__":
    main()
