#!/usr/bin/env python3
"""Allowlisted GitHub-runner bridge for FRANK/RAE research tools.

ChatGPT connector workers can read/write the private canonical repository but cannot
execute repository-local adapters. They may enqueue a JSON request under
research_entity/runtime/tool_requests/. A GitHub runner executes an allowlisted adapter
and writes a sanitized result under tool_results/.

This bridge does not expose credentials and does not execute arbitrary commands on the
GitHub runner. Remote-code tools accept Python source only and execute it inside the
provider sandbox/runtime, never directly in the Actions host.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
REQUESTS = ROOT / "research_entity" / "runtime" / "tool_requests"
RESULTS = ROOT / "research_entity" / "runtime" / "tool_results"
sys.path.insert(0, str(TOOLS))

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
from rae_secret_loader import SecretError, get_secret  # noqa: E402

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
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
    return out[:2000]


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        clean = {}
        for k, v in value.items():
            if str(k).lower() in {"api_key", "key", "token", "authorization", "credential_value"}:
                clean[k] = "[REDACTED]"
            else:
                clean[k] = _sanitize(v)
        return clean
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, str):
        return _redact(value)
    return value


def _int(v: Any, default: int, lo: int, hi: int) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        n = default
    return max(lo, min(hi, n))


def _execute(req: dict[str, Any]) -> Any:
    tool = req.get("tool")
    query = str(req.get("query") or "").strip()
    options = req.get("options") or {}
    if not isinstance(options, dict):
        raise ValueError("options must be an object")

    if tool == "openalex_search":
        if not query:
            raise ValueError("query required")
        return openalex_search.search_works(query, per_page=_int(options.get("per_page"), 10, 1, 25), filter_expr=options.get("filter"), sort=options.get("sort"))

    if tool == "arxiv_search":
        if not query:
            raise ValueError("query required")
        return arxiv_search.query(query, max_results=_int(options.get("max_results"), 10, 1, 25))

    if tool == "semantic_scholar_search":
        if options.get("paper_id"):
            return semantic_scholar_search.lookup(str(options["paper_id"]))
        if not query:
            raise ValueError("query required")
        return semantic_scholar_search.search(query, _int(options.get("limit"), 10, 1, 25))

    if tool == "crossref_lookup":
        doi = str(options.get("doi") or "").strip()
        if doi:
            return crossref_search.doi_lookup(doi)
        if not query:
            raise ValueError("query or options.doi required")
        return crossref_search.works_search(query, _int(options.get("rows"), 10, 1, 25))

    if tool == "tavily_search":
        if not query:
            raise ValueError("query required")
        depth = str(options.get("search_depth") or "basic")
        if depth not in {"basic", "advanced"}:
            depth = "basic"
        return tavily_search.search(query, max_results=_int(options.get("max_results"), 5, 1, 10), search_depth=depth, include_answer=bool(options.get("include_answer", False)), include_raw_content=False)

    if tool == "duckduckgo_search":
        if not query:
            raise ValueError("query required")
        return ddgs_search.search(query, _int(options.get("max_results"), 10, 1, 20), str(options.get("region") or "wt-wt"))

    if tool == "exa_search":
        if not query:
            raise ValueError("query required")
        return exa_search.search(query, num_results=_int(options.get("num_results"), 5, 1, 10), include_domains=options.get("include_domains"), exclude_domains=options.get("exclude_domains"), highlights=True, text=bool(options.get("text", False)))

    if tool == "huggingface_inference":
        mode = str(options.get("mode") or "list_models")
        if mode == "list_models":
            return huggingface_inference.list_models(_int(options.get("limit"), 10, 1, 50))
        if mode != "chat":
            raise ValueError("Hugging Face mode must be list_models or chat")
        if not bool(req.get("allow_cost", False)):
            raise PermissionError("HF chat requires allow_cost=true")
        if not query:
            raise ValueError("query required for HF chat")
        model = str(options.get("model") or "openai/gpt-oss-120b:cheapest")
        return huggingface_inference.chat(model, query, max_tokens=_int(options.get("max_tokens"), 128, 1, 512), temperature=float(options.get("temperature", 0.0)))

    # Remote-code adapters: Python-only, bounded source; execution happens at the
    # remote provider, not in the GitHub Actions host.
    if tool in {"e2b_sandbox", "judge0_execute", "piston_execute"}:
        code = str(req.get("code") or "")
        if not code or len(code.encode("utf-8")) > 50000:
            raise ValueError("bounded Python code required (1..50000 bytes)")
        if tool == "e2b_sandbox":
            # Write source through a JSON-safe Python literal in the isolated sandbox.
            command = "python3 -c " + json.dumps(code)
            return e2b_sandbox.run_command(command, timeout=_int(options.get("timeout"), 30, 1, 120))
        if tool == "judge0_execute":
            return judge0_execute.execute(code, "Python", str(options.get("stdin") or ""))
        return piston_execute.execute(code, "python", str(options.get("stdin") or ""))

    raise ValueError(f"tool is not bridge-allowlisted: {tool!r}")


def process(path: Path, force: bool = False) -> dict[str, Any]:
    req = json.loads(path.read_text(encoding="utf-8"))
    rid = str(req.get("request_id") or path.stem)
    if not ID_RE.fullmatch(rid):
        raise ValueError("invalid request_id")
    out_path = RESULTS / f"{rid}.json"
    if out_path.exists() and not force:
        return {"request_id": rid, "status": "ALREADY_PROCESSED", "result_path": str(out_path.relative_to(ROOT))}

    request_bytes = path.read_bytes()
    envelope: dict[str, Any] = {
        "schema_version": "1.0",
        "request_id": rid,
        "tool": req.get("tool"),
        "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        envelope["status"] = "SUCCESS"
        envelope["result"] = _sanitize(_execute(req))
    except Exception as exc:
        envelope["status"] = "FAILED"
        envelope["error_type"] = type(exc).__name__
        envelope["error"] = _redact(str(exc))
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"request_id": rid, "status": envelope["status"], "result_path": str(out_path.relative_to(ROOT))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("request", nargs="?", help="request JSON path")
    ap.add_argument("--all-pending", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.all_pending:
        REQUESTS.mkdir(parents=True, exist_ok=True)
        outputs = [process(p, force=args.force) for p in sorted(REQUESTS.glob("*.json"))]
        print(json.dumps(outputs, ensure_ascii=False, indent=2))
        return
    if not args.request:
        ap.error("request path required unless --all-pending")
    print(json.dumps(process(Path(args.request), force=args.force), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
