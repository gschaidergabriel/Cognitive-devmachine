#!/usr/bin/env python3
"""Research discriminator for ClayCode BASE D V19.

Tests the no-lookahead delimiter-consuming V19 candidate against selected V17.
The candidate must satisfy strict construction, frozen-source acceptance, deterministic
V17-normalized semantic identity, prefix-shadow negatives, and V17 trailing-trivia
semantics. Any known counterexample dominates otherwise-green evidence.

Research evidence only: this probe never promotes V19 or authorizes Frank Harness changes.
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
    return Lark(grammar, parser="lalr", lexer="contextual", strict=strict, start="start", keep_all_tokens=True, maybe_placeholders=False)


def token_obj(token_type: str, value: str) -> dict[str, str]:
    return {"token": token_type, "value": value}


def canonical(node: Any, *, v19: bool) -> Any:
    if isinstance(node, Tree):
        if v19 and str(node.data) == "special_owns_call":
            children: list[Any] = [
                {"kind": "qid", "children": [token_obj("NAME", "Needle"), token_obj("DOT", "."), token_obj("NAME", "owns")]},
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
    strict_rows, parsers = [], {}
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
        t17a, t17b = parsers["v17"].parse(source), parsers["v17"].parse(source)
        t19a, t19b = parsers["v19"].parse(source), parsers["v19"].parse(source)
        a17, b17 = canonical(t17a, v19=False), canonical(t17b, v19=False)
        a19, b19 = canonical(t19a, v19=True), canonical(t19b, v19=True)
        h17, h19 = semantic_hash(a17), semantic_hash(a19)
        source_rows.append({
            "path": str(path.relative_to(ROOT)), "source_sha256": sha(source.encode("utf-8")),
            "v17_semantic_hash": h17, "v19_normalized_semantic_hash": h19,
            "semantic_hash_equal": h17 == h19, "v17_repeat_equal": a17 == b17, "v19_repeat_equal": a19 == b19,
            "elapsed_ms": (time.perf_counter() - t0) * 1000,
        })

    positive = [
        "rule 4B_need_not_learn Needle.owns\n", "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
        "rule Needle.lowers\tEffectIntent -> concrete_adapter_plan\n", "rule Needle.owns [tool_schema,api_wire]\n",
        "rule Needle.owns\t[tool_schema,api_wire]\n", "rule Needle.owns(X)\n", "rule Needle.owns (X)\n",
        "rule Needle.owns\t(X)\n", "rule Needle.owns \t (X)\n", "rule Needle.ownership\n",
        "rule Needle.owns_extra\n", "rule Needle.ownsX\n", "rule Needle.lowers_more\n", "rule Needle.lowersX\n",
    ]
    negative = ["rule Needle.lowers\n", "rule Needle.lowers (X)\n", "rule Needle.lowers\t(X)\n"]
    fixture_rows = []
    for source in positive:
        ok17, e17, t17 = parse_ok(parsers["v17"], source)
        ok19, e19, t19 = parse_ok(parsers["v19"], source)
        same = bool(ok17 and ok19 and t17 is not None and t19 is not None and canonical(t17, v19=False) == canonical(t19, v19=True))
        fixture_rows.append({"source": source, "expected": "ACCEPT_EQUIVALENT", "v17_accept": ok17, "v19_accept": ok19, "normalized_equal": same, "v17_error": e17, "v19_error": e19, "pass": ok17 and ok19 and same})
    for source in negative:
        ok17, e17, _ = parse_ok(parsers["v17"], source)
        ok19, e19, _ = parse_ok(parsers["v19"], source)
        fixture_rows.append({"source": source, "expected": "REJECT_BOTH", "v17_accept": ok17, "v19_accept": ok19, "v17_error": e17, "v19_error": e19, "pass": (not ok17) and (not ok19)})

    shadow_rows = []
    for source in ["rule Needle.ownership\n", "rule Needle.owns_extra\n", "rule Needle.ownsX\n", "rule Needle.lowers_more\n", "rule Needle.lowersX\n"]:
        tree = parsers["v19"].parse(source)
        special = has_kind(tree, "prefix_relation") or has_kind(tree, "special_owns_call")
        shadow_rows.append({"source": source, "special_relation_or_call": special, "pass": not special})

    trailing_rows = []
    for source in ["rule Needle.owns   \n", "rule Needle.owns\t\n", "rule Needle.owns   // trailing comment\n", "rule Needle.owns\t// trailing comment\n"]:
        ok17, e17, t17 = parse_ok(parsers["v17"], source)
        ok19, e19, t19 = parse_ok(parsers["v19"], source)
        same = bool(ok17 and ok19 and t17 is not None and t19 is not None and canonical(t17, v19=False) == canonical(t19, v19=True))
        trailing_rows.append({"source": source, "v17_accept": ok17, "v19_accept": ok19, "normalized_equal": same, "v17_error": e17, "v19_error": e19, "pass": ok17 and ok19 and same})

    needle_lines = [line for line in g19.splitlines() if line.lstrip().startswith(("NEEDLE_OWNS_CALL", "NEEDLE_OWNS_REL", "NEEDLE_LOWERS_REL"))]
    needle_relation_lookaround_present = any(marker in line for line in needle_lines for marker in ("(?=", "(?<=", "(?!", "(?<!"))
    structural_pass = all(r["pass"] for r in strict_rows) and all(r["semantic_hash_equal"] and r["v17_repeat_equal"] and r["v19_repeat_equal"] for r in source_rows) and all(r["pass"] for r in fixture_rows) and all(r["pass"] for r in shadow_rows) and not needle_relation_lookaround_present
    trailing_pass = all(r["pass"] for r in trailing_rows)
    passed = structural_pass and trailing_pass
    known_counterexample = structural_pass and not trailing_pass

    out = {
        "schema_version": "1.2", "experiment": "ClayCode V19 delimiter-normalization discriminator",
        "created_at": datetime.now(timezone.utc).isoformat(), "evidence_class": "EXECUTABLE_RESEARCH_DISCRIMINATOR",
        "runtime": {"platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version(), "lark": pkg("lark"), "interegular": pkg("interegular"), "cpu_count": os.cpu_count(), "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "github_sha": os.environ.get("GITHUB_SHA"), "github_run_id": os.environ.get("GITHUB_RUN_ID"), "runner_name": os.environ.get("RUNNER_NAME")},
        "inputs": {"v17_path": str(V17.relative_to(ROOT)), "v17_sha256": sha(g17.encode("utf-8")), "v19_path": str(V19.relative_to(ROOT)), "v19_sha256": sha(g19.encode("utf-8"))},
        "strict_construction": strict_rows, "full_sources": source_rows, "fixtures": fixture_rows,
        "prefix_shadow_negatives": shadow_rows, "trailing_trivia_equivalence": trailing_rows,
        "needle_relation_lookaround_present": needle_relation_lookaround_present, "structural_pass": structural_pass, "trailing_trivia_pass": trailing_pass,
        "pass": passed, "adjudication": "SUPPORTED_RESEARCH_CANDIDATE" if passed else ("REFUTED_TRAILING_TRIVIA" if known_counterexample else "REFUTED_OR_INCOMPLETE"),
        "promotion": "NONE",
        "architecture_delta": "NO_CHANGE_KEEP_V17_SELECTED" if not passed else "TESTING_ONLY",
        "scope_guard": "A known V17-valid counterexample dominates otherwise-green strict/full-source/hash evidence. NAME keyword-reservation lookaround is baseline lexical behavior and is not counted as a Needle relation lookaround. PASS still would not close WP02/WP03 or count as Andreas-target acceptance.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
