#!/usr/bin/env python3
"""Detect silent identifier-prefix shadowing in ClayCode BASE D V18.

V18 gives NEEDLE_OWNS/NEEDLE_LOWERS priority 11. This probe checks whether
longer syntactically valid qid components that merely start with those strings
are silently tokenized as a reserved dotted relation plus a suffix identifier.

This is a negative-evidence probe for the exact V18 candidate. It does not
select a replacement grammar and does not close CC-WP-02/03.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import resource
from datetime import datetime, timezone
from pathlib import Path

from lark import Lark, Tree

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_NO_LOOKAHEAD.lark"


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def parse(parser: Lark, source: str) -> Tree:
    return parser.parse(source)


def contains_kind(node: Tree, kind: str) -> bool:
    return any(str(t.data) == kind for t in node.iter_subtrees())


def main() -> int:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    parser = Lark(
        grammar,
        parser="lalr",
        lexer="contextual",
        strict=False,
        start="start",
        keep_all_tokens=True,
        maybe_placeholders=False,
    )

    # NAME excludes exact reserved words at a word boundary, but these longer
    # suffix-bearing identifiers remain syntactically valid NAME components.
    qid_cases = [
        "Needle.ownership",
        "Needle.owns_extra",
        "Needle.ownsX",
        "Needle.lowers_more",
        "Needle.lowersX",
    ]
    rows = []
    for expr in qid_cases:
        source = f"rule {expr}\n"
        tree = parse(parser, source)
        rows.append({
            "expr": expr,
            "accepted": True,
            "parsed_as_prefix_relation": contains_kind(tree, "prefix_relation"),
            "parsed_as_qid": contains_kind(tree, "qid"),
            "tree": tree.pretty(),
        })

    controls = {}
    for name, source, expected_kind in [
        ("owns_relation", "rule Needle.owns X\n", "prefix_relation"),
        ("owns_call", "rule Needle.owns(X)\n", "special_owns_call"),
        ("owns_call_spaced", "rule Needle.owns (X)\n", "special_owns_call"),
        ("lowers_relation", "rule Needle.lowers X\n", "prefix_relation"),
    ]:
        tree = parse(parser, source)
        controls[name] = {
            "expected_kind": expected_kind,
            "observed": contains_kind(tree, expected_kind),
        }

    shadowed = [r["expr"] for r in rows if r["parsed_as_prefix_relation"]]
    clean_qids = [r["expr"] for r in rows if not r["parsed_as_prefix_relation"]]
    refuted = bool(shadowed) and all(x["observed"] for x in controls.values())

    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode V18 reserved-prefix shadow falsifier",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(GRAMMAR.relative_to(ROOT)),
        "grammar_sha256": hashlib.sha256(grammar.encode("utf-8")).hexdigest(),
        "runtime": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "lark": pkg("lark"),
            "interegular": pkg("interegular"),
            "strict": False,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "qid_cases": rows,
        "controls": controls,
        "shadowed_identifiers": shadowed,
        "clean_identifiers": clean_qids,
        "result": "REFUTED" if refuted else "UNRESOLVED",
        "interpretation": (
            "Current V18 priority terminals silently steal prefixes from longer valid qid components, changing parse meaning without a syntax error."
            if refuted
            else "No reserved-prefix semantic shadow was demonstrated by this bounded probe."
        ),
        "promotion": "NONE",
        "architecture_delta": "NO_CHANGE_KEEP_V17_SELECTED; any future no-lookahead candidate must add identifier-prefix discrimination before semantic-hash differential promotion.",
        "scope_guard": "REFUTED applies to the exact V18 token-priority design. It does not prove V17 globally optimal, close CC-WP-02/03, or authorize Frank Harness changes.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if refuted else 1


if __name__ == "__main__":
    raise SystemExit(main())
