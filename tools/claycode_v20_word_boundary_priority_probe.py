#!/usr/bin/env python3
"""Research discriminator for ClayCode BASE D V20 word-boundary/rule-priority candidate.

V20 attempts to preserve the selected V17 language while removing the Needle relation
lookahead and the V19 trivia-consuming regression. It uses exact word-boundary terminals
plus LALR rule priorities. A PASS is research evidence only; it cannot close WP02/WP03,
promote a parser, or authorize any Frank Harness change.
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
V20 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V20_WORD_BOUNDARY_RULE_PRIORITY.lark"
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
    return Lark(grammar, parser="lalr", lexer="contextual", strict=strict, start="start", keep_all_tokens=True, maybe_placeholders=False)


def token_obj(token_type: str, value: str) -> dict[str, str]:
    return {"token": token_type, "value": value}


def qid_needle_owns() -> dict[str, Any]:
    return {"kind": "qid", "children": [token_obj("NAME", "Needle"), token_obj("DOT", "."), token_obj("NAME", "owns")]}


def canonical(node: Any, *, v20: bool) -> Any:
    if isinstance(node, Tree):
        kind = str(node.data)
        if v20 and kind == "needle_owns_atom":
            return qid_needle_owns()
        if v20 and kind == "special_owns_call":
            children: list[Any] = [qid_needle_owns()]
            for child in node.children[1:]:
                value = canonical(child, v20=True)
                if value is not None:
                    children.append(value)
            return {"kind": "call", "children": children}
        children = []
        for child in node.children:
            value = canonical(child, v20=v20)
            if value is not None:
                children.append(value)
        return {"kind": kind, "children": children}
    if isinstance(node, Token):
        if node.type in {"NEWLINE", "SEMICOLON"} or str(node) == ";":
            return None
        if v20 and node.type in {"NEEDLE_OWNS", "NEEDLE_LOWERS"}:
            return token_obj("DOTTED_PREFIX_REL", str(node))
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


def normalized_equal(p17: Lark, p20: Lark, source: str) -> tuple[bool, dict[str, Any]]:
    ok17, e17, t17 = parse_ok(p17, source)
    ok20, e20, t20 = parse_ok(p20, source)
    same = bool(ok17 and ok20 and t17 is not None and t20 is not None and canonical(t17, v20=False) == canonical(t20, v20=True))
    return same, {"source": source, "v17_accept": ok17, "v20_accept": ok20, "normalized_equal": same, "v17_error": e17, "v20_error": e20}


def main() -> int:
    g17 = V17.read_text(encoding="utf-8")
    g20 = V20.read_text(encoding="utf-8")
    strict_rows, parsers = [], {}
    for name, grammar in (("v17", g17), ("v20", g20)):
        t0 = time.perf_counter()
        try:
            parsers[name] = parser(grammar, strict=True)
            strict_rows.append({"grammar": name, "pass": True, "error": None, "elapsed_ms": (time.perf_counter() - t0) * 1000})
        except Exception as exc:
            strict_rows.append({"grammar": name, "pass": False, "error": f"{type(exc).__name__}: {exc}", "elapsed_ms": (time.perf_counter() - t0) * 1000})
    if "v17" not in parsers:
        parsers["v17"] = parser(g17, strict=False)
    if "v20" not in parsers:
        parsers["v20"] = parser(g20, strict=False)

    p17, p20 = parsers["v17"], parsers["v20"]
    source_rows = []
    for path in SOURCES:
        source = path.read_text(encoding="utf-8")
        t0 = time.perf_counter()
        t17a, t17b = p17.parse(source), p17.parse(source)
        t20a, t20b = p20.parse(source), p20.parse(source)
        a17, b17 = canonical(t17a, v20=False), canonical(t17b, v20=False)
        a20, b20 = canonical(t20a, v20=True), canonical(t20b, v20=True)
        h17, h20 = semantic_hash(a17), semantic_hash(a20)
        source_rows.append({
            "path": str(path.relative_to(ROOT)), "source_sha256": sha(source.encode("utf-8")),
            "v17_semantic_hash": h17, "v20_normalized_semantic_hash": h20,
            "semantic_hash_equal": h17 == h20, "v17_repeat_equal": a17 == b17,
            "v20_repeat_equal": a20 == b20, "elapsed_ms": (time.perf_counter() - t0) * 1000,
        })

    positive = [
        "rule 4B_need_not_learn Needle.owns\n",
        "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
        "rule Needle.lowers\tEffectIntent -> concrete_adapter_plan\n",
        "rule Needle.owns [tool_schema,api_wire]\n",
        "rule Needle.owns\t[tool_schema,api_wire]\n",
        "rule Needle.owns(X)\n", "rule Needle.owns (X)\n", "rule Needle.owns\t(X)\n", "rule Needle.owns \t (X)\n",
        "rule Needle.ownership\n", "rule Needle.owns_extra\n", "rule Needle.ownsX\n",
        "rule Needle.lowers_more\n", "rule Needle.lowersX\n",
        "rule Needle.owns   \n", "rule Needle.owns\t\n",
        "rule Needle.owns   // trailing comment\n", "rule Needle.owns\t// trailing comment\n",
    ]
    negative = ["rule Needle.lowers\n", "rule Needle.lowers (X)\n", "rule Needle.lowers\t(X)\n"]
    fixture_rows = []
    for source in positive:
        same, row = normalized_equal(p17, p20, source)
        row.update({"expected": "ACCEPT_EQUIVALENT", "pass": same})
        fixture_rows.append(row)
    for source in negative:
        ok17, e17, _ = parse_ok(p17, source)
        ok20, e20, _ = parse_ok(p20, source)
        fixture_rows.append({"source": source, "expected": "REJECT_BOTH", "v17_accept": ok17, "v20_accept": ok20, "v17_error": e17, "v20_error": e20, "pass": (not ok17) and (not ok20)})

    shadow_rows = []
    for source in ["rule Needle.ownership\n", "rule Needle.owns_extra\n", "rule Needle.ownsX\n", "rule Needle.lowers_more\n", "rule Needle.lowersX\n"]:
        tree = p20.parse(source)
        special = has_kind(tree, "prefix_relation") or has_kind(tree, "special_owns_call") or has_kind(tree, "needle_owns_atom")
        shadow_rows.append({"source": source, "special_needle_path": special, "pass": not special})

    needle_lines = [line for line in g20.splitlines() if line.lstrip().startswith(("NEEDLE_OWNS", "NEEDLE_LOWERS"))]
    relation_lookaround_present = any(marker in line for line in needle_lines for marker in ("(?=", "(?<=", "(?!", "(?<!"))
    word_boundary_present = all("\\b" in line for line in needle_lines if line.strip())
    strict_pass = all(r["pass"] for r in strict_rows)
    source_pass = all(r["semantic_hash_equal"] and r["v17_repeat_equal"] and r["v20_repeat_equal"] for r in source_rows)
    fixture_pass = all(r["pass"] for r in fixture_rows)
    shadow_pass = all(r["pass"] for r in shadow_rows)
    passed = strict_pass and source_pass and fixture_pass and shadow_pass and not relation_lookaround_present and word_boundary_present

    out = {
        "schema_version": "1.0", "experiment": "ClayCode V20 word-boundary rule-priority discriminator",
        "created_at": datetime.now(timezone.utc).isoformat(), "evidence_class": "EXECUTABLE_RESEARCH_DISCRIMINATOR",
        "runtime": {"platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version(), "lark": pkg("lark"), "interegular": pkg("interegular"), "cpu_count": os.cpu_count(), "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "github_sha": os.environ.get("GITHUB_SHA"), "github_run_id": os.environ.get("GITHUB_RUN_ID"), "runner_name": os.environ.get("RUNNER_NAME")},
        "inputs": {"v17_path": str(V17.relative_to(ROOT)), "v17_sha256": sha(g17.encode("utf-8")), "v20_path": str(V20.relative_to(ROOT)), "v20_sha256": sha(g20.encode("utf-8"))},
        "strict_construction": strict_rows, "full_sources": source_rows, "fixtures": fixture_rows,
        "prefix_shadow_negatives": shadow_rows, "needle_relation_lookaround_present": relation_lookaround_present,
        "needle_word_boundary_present": word_boundary_present,
        "strict_pass": strict_pass, "source_semantic_pass": source_pass, "fixture_pass": fixture_pass, "shadow_pass": shadow_pass,
        "pass": passed, "adjudication": "SUPPORTED_RESEARCH_CANDIDATE" if passed else "REFUTED_OR_INCOMPLETE",
        "promotion": "NONE", "architecture_delta": "TESTING_ONLY" if passed else "NO_CHANGE_KEEP_V17_SELECTED",
        "scope_guard": "PASS would establish only this strict/frozen-source/fixture semantic slice. Source-span parity, downstream typed-IR replay, Hostinger and registered Andreas Ubuntu acceptance remain separate gates.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
