#!/usr/bin/env python3
"""Unified, sanitized health audit for FRANK/RAE external research providers.

Runs the smallest practical smoke probe for each registered provider, classifies failures,
and can write a single provider-health document plus per-provider receipts. Secret values
are never emitted. This separates three concepts that were previously conflated:
credential validity, provider/runtime health, and worker-surface invocability.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from rae_secret_loader import SecretError, get_secret  # noqa: E402
import openalex_search  # noqa: E402
import arxiv_search  # noqa: E402
import semantic_scholar_search  # noqa: E402
import crossref_search  # noqa: E402
import tavily_search  # noqa: E402
import ddgs_search  # noqa: E402
import exa_search  # noqa: E402
import e2b_sandbox  # noqa: E402
import judge0_execute  # noqa: E402
import piston_execute  # noqa: E402
import huggingface_inference  # noqa: E402

OUT = ROOT / "research_entity" / "runtime" / "PROVIDER_HEALTH.json"

PROVIDERS: list[tuple[str, str, Callable[[], dict[str, Any]], str]] = [
    ("openalex_search", "OpenAlex", openalex_search.smoke_test, "research_entity/runtime/openalex_verification.json"),
    ("arxiv_search", "arXiv", arxiv_search.smoke_test, "research_entity/runtime/arxiv_verification.json"),
    ("semantic_scholar_search", "Semantic Scholar", semantic_scholar_search.smoke_test, "research_entity/runtime/semantic_scholar_verification.json"),
    ("crossref_lookup", "Crossref", crossref_search.smoke_test, "research_entity/runtime/crossref_verification.json"),
    ("tavily_search", "Tavily", tavily_search.smoke_test, "research_entity/runtime/tavily_verification.json"),
    ("duckduckgo_search", "DuckDuckGo/DDGS", ddgs_search.smoke_test, "research_entity/runtime/ddgs_verification.json"),
    ("exa_search", "Exa", exa_search.smoke_test, "research_entity/runtime/exa_verification.json"),
    ("e2b_sandbox", "E2B", e2b_sandbox.smoke_test, "research_entity/runtime/e2b_verification.json"),
    ("judge0_execute", "Judge0", judge0_execute.smoke_test, "research_entity/runtime/judge0_verification.json"),
    ("piston_execute", "Piston", piston_execute.smoke_test, "research_entity/runtime/piston_verification.json"),
    ("huggingface_inference", "Hugging Face Inference Providers", huggingface_inference.smoke_test, "research_entity/runtime/huggingface_verification.json"),
]

SECRET_NAMES = ["OPENALEX_API_KEY", "TAVILY_API_KEY", "EXA_API_KEY", "E2B_API_KEY", "HF_TOKEN", "SEMANTIC_SCHOLAR_API_KEY", "JUDGE0_API_KEY"]


def _redact(text: str) -> str:
    out = text
    for name in SECRET_NAMES:
        try:
            value = get_secret(name, required=False)
        except Exception:
            value = None
        if value:
            out = out.replace(value, "[REDACTED]")
    return out[:800]


def _classify(exc: Exception) -> str:
    if isinstance(exc, SecretError):
        return "CREDENTIAL_UNAVAILABLE"
    if isinstance(exc, ModuleNotFoundError) or "package missing" in str(exc).lower() or "install with" in str(exc).lower():
        return "DEPENDENCY_MISSING"
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in {401, 403}:
            return "AUTH_FAILED"
        if exc.code == 402:
            return "QUOTA_OR_PLAN_EXHAUSTED"
        if exc.code == 429:
            return "RATE_LIMITED"
        if 500 <= exc.code <= 599:
            return "PROVIDER_UNAVAILABLE"
        return "HTTP_ERROR"
    msg = str(exc).lower()
    if "credential" in msg and ("not configured" in msg or "missing" in msg):
        return "CREDENTIAL_UNAVAILABLE"
    if "429" in msg or "rate limit" in msg:
        return "RATE_LIMITED"
    if "401" in msg or "403" in msg or "unauthorized" in msg or "forbidden" in msg:
        return "AUTH_FAILED"
    if "quota" in msg or "credit" in msg or "payment" in msg:
        return "QUOTA_OR_PLAN_EXHAUSTED"
    if "timed out" in msg or "network" in msg or "urlopen" in msg or "temporary failure" in msg:
        return "NETWORK_OR_PROVIDER_UNAVAILABLE"
    return "SMOKE_FAILED"


def _sanitize_receipt(obj: Any) -> Any:
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in {"api_key", "key", "token", "authorization", "credential_value"}:
                clean[k] = "[REDACTED]"
            else:
                clean[k] = _sanitize_receipt(v)
        return clean
    if isinstance(obj, list):
        return [_sanitize_receipt(v) for v in obj]
    if isinstance(obj, str):
        return _redact(obj)
    return obj


def audit(write: bool = False) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    results: list[dict[str, Any]] = []
    for tool, provider, fn, receipt_path in PROVIDERS:
        try:
            receipt = _sanitize_receipt(fn())
            status = "RUNTIME_VERIFIED" if receipt.get("status") == "RUNTIME_VERIFIED" else "SMOKE_FAILED"
            item = {"tool": tool, "provider": provider, "status": status, "receipt": receipt, "receipt_path": receipt_path}
            if write and status == "RUNTIME_VERIFIED":
                p = ROOT / receipt_path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:
            item = {
                "tool": tool,
                "provider": provider,
                "status": _classify(exc),
                "error_type": type(exc).__name__,
                "error": _redact(str(exc)),
                "receipt_path": receipt_path,
            }
        results.append(item)

    counts: dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    out = {
        "schema_version": "1.0",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "started_at": started,
        "scope": "provider credential/runtime smoke health; not worker-surface invocability",
        "results": results,
        "counts": counts,
        "worker_invocation_note": "A RUNTIME_VERIFIED provider may still be unavailable to a ChatGPT worker unless an invokable connector or the repo-runner bridge is used.",
    }
    if write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    print(json.dumps(audit(write=args.write), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
