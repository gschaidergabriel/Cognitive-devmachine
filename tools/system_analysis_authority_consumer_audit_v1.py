#!/usr/bin/env python3
"""Fail-closed audit for monitoring authority/runtime-credit consumers.

Authority- or runtime-credit-bearing Python code must not consume the compatibility mirrors
`free swarm/SYSTEM_ANALYSIS_LIVE.json` or `SYSTEM_ANALYSIS_PROVENANCE.json` directly.
It must resolve the verified publication generation through
`tools.system_analysis_current_reader_v1.read_current_publication`.

This tool is static/source-only. It performs no provider/network calls and no writes.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Iterable

FORBIDDEN_MIRROR_NAMES = {
    "SYSTEM_ANALYSIS_LIVE.json",
    "SYSTEM_ANALYSIS_PROVENANCE.json",
}
REQUIRED_READER_SYMBOL = "read_current_publication"

# Publishers, the verifier itself, tests, and historical/receipt material are not consumers.
EXEMPT_EXACT = {
    Path("free swarm/update_system_analysis.py"),
    Path("free swarm/update_system_analysis_v4.py"),
    Path("free swarm/update_system_analysis_v5.py"),
    Path("free swarm/update_system_analysis_v6.py"),
    Path("tools/system_analysis_current_reader_v1.py"),
    Path("tools/system_analysis_authority_consumer_audit_v1.py"),
}
EXEMPT_PREFIXES = (
    Path("tests"),
    Path("research_entity/continuity/receipts"),
    Path("research_entity/trigger_runs"),
    Path("research_entity/global/j-space/research"),
)

# Names strongly indicating an authority/runtime-credit consumer. A direct mirror reference in
# other production Python is still reported as REVIEW, never silently ignored.
AUTHORITY_HINTS = (
    "authority",
    "admission",
    "supervisor",
    "quiescence",
    "provider_gate",
    "promotion_gate",
    "runtime_credit",
    "acceptance",
    "adjudicat",
)


def _is_exempt(rel: Path) -> bool:
    if rel in EXEMPT_EXACT:
        return True
    return any(rel == p or p in rel.parents for p in EXEMPT_PREFIXES)


def _python_files(repo: Path) -> Iterable[Path]:
    for p in repo.rglob("*.py"):
        rel = p.relative_to(repo)
        if ".git" in rel.parts or _is_exempt(rel):
            continue
        yield p


def _literal_strings(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.add(node.value)
    return out


def _imports_verified_reader(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.endswith("system_analysis_current_reader_v1"):
                if any(alias.name == REQUIRED_READER_SYMBOL for alias in node.names):
                    return True
        elif isinstance(node, ast.Import):
            if any(alias.name.endswith("system_analysis_current_reader_v1") for alias in node.names):
                return True
    return False


def _authority_likely(rel: Path, text: str) -> bool:
    hay = (str(rel) + "\n" + text[:12000]).lower()
    return any(h in hay for h in AUTHORITY_HINTS)


def audit(repo: Path) -> dict:
    repo = repo.resolve()
    violations = []
    review = []
    verified_consumers = []
    parse_errors = []

    for path in _python_files(repo):
        rel = path.relative_to(repo)
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(rel))
        except Exception as exc:
            parse_errors.append({"path": str(rel), "error": type(exc).__name__})
            continue

        literals = _literal_strings(tree)
        mirror_hits = sorted(
            name for name in FORBIDDEN_MIRROR_NAMES
            if any(name in literal for literal in literals)
        )
        reader = _imports_verified_reader(tree) or REQUIRED_READER_SYMBOL in text

        if reader:
            verified_consumers.append(str(rel))

        if not mirror_hits:
            continue

        item = {
            "path": str(rel),
            "mirror_hits": mirror_hits,
            "verified_reader_referenced": reader,
            "authority_likely": _authority_likely(rel, text),
        }
        if item["authority_likely"]:
            violations.append(item)
        else:
            review.append(item)

    state = "PASS" if not violations and not parse_errors else "FAIL_CLOSED"
    return {
        "schema": "CLAY_SYSTEM_ANALYSIS_AUTHORITY_CONSUMER_AUDIT/v1",
        "state": state,
        "rule": "AUTHORITY_RUNTIME_CREDIT_CONSUMERS_MUST_USE_VERIFIED_CURRENT_POINTER_READER",
        "violations": violations,
        "review_non_authority_direct_mirror_refs": review,
        "verified_reader_consumers": sorted(set(verified_consumers)),
        "parse_errors": parse_errors,
        "credit": {"runtime": 0, "grid10": 0, "hcu": 0},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()
    result = audit(Path(args.repo))
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["state"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
