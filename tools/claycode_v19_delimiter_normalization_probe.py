#!/usr/bin/env python3
"""Research discriminator for ClayCode BASE D V19.

Tests the no-lookahead delimiter-consuming V19 candidate against selected V17.
The key claim under test is narrow: dedicated tokens may consume horizontal trivia
(and the opening parenthesis for Needle.owns calls) without changing the existing
ClayCodeBaseFrontendAST/v1 semantics, provided a deterministic normalization maps
those parse nodes/tokens back to the V17 canonical shape.

This script is research evidence only. PASS does not promote V19, close WP02/WP03,
or authorize any Frank Harness change.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
V19 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V19_DELIMITER_NORMALIZABLE.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
DOMAIN = b"ClayCodeBaseFrontendAST/v1\x00"


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parser(grammar: str, *, strict: bool) -> Lark:
    return Lark(
        grammar,
        parser="lalr",
        lexer="contextual",
        strict=strict,
        start="start",
        keep_all_tokens=True,
        maybe_placeholders=False,
    )


def token_obj(token_type: str, value: str) -> dict[str, str]:
    return {"token": token_type, "value": value}


def canonical(node: Any, *, v19: bool) -> Any:
    if isinstance(node, Tree):
        if v19 and str(node.data) == "special_owns_call":
            # V19 consumes `Needle.owns` + horizontal trivia + `(` as one token.
            # Reconstruct the exact V17 canonical call/qid shape deterministically.
            children: list[Any] = [
                {
                    "kind": "qid",
                    "children": [
                        token_obj("NAME", "Needle"),
                        token_obj("DOT", "."),
                        token_obj("NAME", "owns"),
                    ],
                },
                token_obj("LPAR", "("),
            ]
            for child in node.children[1:]:
                value = canonical(child, v19=True)
                if value is not None:
                    children.append(value)
            return {"kind": "call", "children": children}

        children = []
        for child in node.children:
            value = canonical(child, v19=v19)
            if value is not None:
                children.append(value)
        return {"kind": str(node.data), "children": children}

    if isinstance(node, Token):
        if node.type in {"NEWLINE", "SEMICOLON"} or str(node) == ";":
            return None
        if v19 and node.type in {"NEEDLE_OWNS_REL", "NEEDLE_LOWERS_REL"}:
            return token_obj("DOTTED_PREFIX_REL", str(node).strip())
        if v19 and node.type == "NEEDLE_OWNS_CALL":
            raise AssertionError("NEEDLE_OWNS_CALL must be normalized by special_owns_call parent")
        return token_obj(node.type, str(node))

    raise TypeError(type(node))


def semantic_hash(ast: Any) -> str:
    payload = json.dumps(ast, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha(DOMAIN + payload)


def has_kind(tree: Tree, kind: str) -> bool:
    return any(str(t.data) == kind for t in tree.iter_subtrees())


def parse_ok(p: Lark, source: str) -> tuple[bool, str | None, Tree | None]:
    try:
        return True, None, p.parse(source)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}", None


def main() -> int:
    g17 = V17.read_text(encoding="utf-8")
    g19 = V19.read_text(encoding="utf-8")

    strict_rows = []
    parsers = {}
    for name, grammar in (("v17", g17), ("v19", g19)):
        t0 = time.perf_counter()
        try:
            parsers[name] = parser(grammar, strict=True)
            strict_rows.append({"grammar": name, "pass": True, "error": None, "elapsed_ms": (time.perf_counter() - t0) * 1000})
        except Exception as exc:
            strict_rows.append({"grammar": name, "pass": False, "error": f"{type(exc).__name__}: {exc}", "elapsed_ms": (time.perf_counter() - t0) * 1000})

    if "v17" not in parsers:
        parsers["v17"] = parser(g17, strict=False)
    if "v19" not in parsers:
        parsers["v19"] = parser(g19, strict=False)

    source_rows = []
    for path in SOURCES:
        source = path.read_text(encoding="utf-8")
        t0 = time.perf_counter()
        t17a = parsers["v17"].parse(source)
        t17b = parsers["v17"].parse(source)
        t19a = parsers["v19"].parse(source)
        t19b = parsers["v19"].parse(source)
        a17 = canonical(t17a, v19=False)
        b17 = canonical(t17b, v19=False)
        a19 = canonical(t19a, v19=True)
        b19 = canonical(t19b, v19=True)
        h17 = semantic_hash(a17)
        h19 = semantic_hash(a19)
        source_rows.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha(source.encode("utf-8")),
            "v17_semantic_hash": h17,
            "v19_normalized_semantic_hash": h19,
            "semantic_hash_equal": h17 == h19,
            "v17_repeat_equal": a17 == b17,
            "v19_repeat_equal": a19 == b19,
            "elapsed_ms": (time.perf_counter() - t0) * 1000,
        })

    positive = [
        "rule 4B_need_not_learn Needle.owns\n",
        "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
        "rule Needle.lowers\tEffectIntent -> concrete_adapter_plan\n",
        "rule Needle.owns [tool_schema,api_wire]\n",
        "rule Needle.owns\t[tool_schema,api_wire]\n",
        "rule Needle.owns(X)\n",
        "rule Needle.owns (X)\n",
        "rule Needle.owns\t(X)\n",
        "rule Needle.owns \t (X)\n",
        "rule Needle.ownership\n",
        "rule Needle.owns_extra\n",
        "rule Needle.ownsX\n",
        "rule Needle.lowers_more\n",
        "rule Needle.lowersX\n",
    ]
    negative = [
        "rule Needle.lowers\n",
        "rule Needle.lowers (X)\n",
        "rule Needle.lowers\t(X)\n",
    ]

    fixture_rows = []
    for source in positive:
        ok17, e17, t17 = parse_ok(parsers["v17"], source)
        ok19, e19, t19 = parse_ok(parsers["v19"], source)
        same = False
        if ok17 and ok19 and t17 is not None and t19 is not None:
            same = canonical(t17, v19=False) == canonical(t19, v19=True)
        fixture_rows.append({
            "source": source,
            "expected": "ACCEPT_EQUIVALENT",
            "v17_accept": ok17,
            "v19_accept": ok19,
            "normalized_equal": same,
            "v17_error": e17,
            "v19_error": e19,
            "pass": ok17 and ok19 and same,
        })

    for source in negative:
        ok17, e17, _ = parse_ok(parsers["v17"], source)
        ok19, e19, _ = parse_ok(parsers["v19"], source)
        fixture_rows.append({
            "source": source,
            "expected": "REJECT_BOTH",
            "v17_accept": ok17,
            "v19_accept": ok19,
            "v17_error": e17,
            "v19_error": e19,
            "pass": (not ok17) and (not ok19),
        })

    shadow_sources = [
        "rule Needle.ownership\n",
        "rule Needle.owns_extra\n",
        "rule Needle.ownsX\n",
        "rule Needle.lowers_more\n",
        "rule Needle.lowersX\n",
    ]
    shadow_rows = []
    for source in shadow_sources:
        tree = parsers["v19"].parse(source)
        special = has_kind(tree, "prefix_relation") or has_kind(tree, "special_owns_call")
        shadow_rows.append({"source": source, "special_relation_or_call": special, "pass": not special})

    regex_lookaround_present = any(x in g19 for x in ("(?=", "(?<=", "(?!", "(?<!"))
    passed = (
        all(r["pass"] for r in strict_rows)
        and all(r["semantic_hash_equal"] and r["v17_repeat_equal"] and r["v19_repeat_equal"] for r in source_rows)
        and all(r["pass"] for r in fixture_rows)
        and all(r["pass"] for r in shadow_rows)
        and not regex_lookaround_present
    )

    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode V19 delimiter-normalization discriminator",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "EXECUTABLE_RESEARCH_DISCRIMINATOR",
        "runtime": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "lark": pkg("lark"),
            "interegular": pkg("interegular"),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "inputs": {
            "v17_path": str(V17.relative_to(ROOT)),
            "v17_sha256": sha(g17.encode("utf-8")),
            "v19_path": str(V19.relative_to(ROOT)),
            "v19_sha256": sha(g19.encode("utf-8")),
        },
        "strict_construction": strict_rows,
        "full_sources": source_rows,
        "fixtures": fixture_rows,
        "prefix_shadow_negatives": shadow_rows,
        "regex_lookaround_present": regex_lookaround_present,
        "pass": passed,
        "adjudication": "SUPPORTED_RESEARCH_CANDIDATE" if passed else "REFUTED_OR_INCOMPLETE",
        "promotion": "NONE",
        "scope_guard": "PASS means V19 strictly constructs in this runtime, accepts the two frozen BASE sources, avoids the V18 prefix-shadow cases, preserves the selected fixture behavior, and maps deterministically to the existing V17 canonical AST/hash under this explicit normalizer. It does not promote V19, close WP02/WP03, prove all downstream typed-IR semantics, or count as Andreas-target acceptance.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
