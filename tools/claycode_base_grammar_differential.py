#!/usr/bin/env python3
"""Full-corpus D baseline -> V4 repair differential for ClayCode BASE.

Purpose: distinguish a parser-table repair from an accidental source-meaning rewrite.
The baseline is intentionally constructed non-strict because its known 13 LALR conflicts
make strict construction fail. The repaired grammar is constructed strict. For the
currently admitted G9 V3 and Dialect V3 sources we require identical deterministic parse
structure. Separately, we require the repair to reject the two ambiguous keyword-as-
identifier surfaces (`if`, `invariant`) that caused 12/13 conflicts while preserving
valid statement/newline cases.

This receipt is evidence for CC-WP-02 only. Parse-tree equivalence is not typed canonical
IR equivalence and must never be promoted as CC-WP-02 PASS by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark, Tree, Token

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "research_entity/trigger_runs/claycode/claycode-20260809T1717p0700-all-workers-production-parser/D_LALR_GRAMMAR_CANDIDATE_V3.lark"
REPAIR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(node: Any) -> Any:
    if isinstance(node, Tree):
        return [str(node.data), [canonical(x) for x in node.children]]
    if isinstance(node, Token):
        return [node.type, str(node)]
    return [type(node).__name__, str(node)]


def tree_hash(tree: Tree) -> str:
    payload = json.dumps(canonical(tree), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256(payload)


def parse_case(parser: Lark, text: str) -> tuple[bool, str | None, str | None]:
    try:
        tree = parser.parse(text)
        return True, tree_hash(tree), None
    except Exception as exc:
        return False, None, f"{type(exc).__name__}: {exc}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=str(BASELINE))
    ap.add_argument("--repair", default=str(REPAIR))
    ap.add_argument("--output")
    args = ap.parse_args()

    baseline_path = Path(args.baseline)
    repair_path = Path(args.repair)
    baseline_text = baseline_path.read_text(encoding="utf-8")
    repair_text = repair_path.read_text(encoding="utf-8")

    baseline = Lark(baseline_text, parser="lalr", lexer="contextual", strict=False, start="start")
    repair = Lark(repair_text, parser="lalr", lexer="contextual", strict=True, start="start")

    source_rows = []
    for path in SOURCES:
        text = path.read_text(encoding="utf-8")
        bt1 = baseline.parse(text)
        bt2 = baseline.parse(text)
        rt1 = repair.parse(text)
        rt2 = repair.parse(text)
        bh1, bh2 = tree_hash(bt1), tree_hash(bt2)
        rh1, rh2 = tree_hash(rt1), tree_hash(rt2)
        source_rows.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha256(text.encode("utf-8")),
            "baseline_tree_hash": bh1,
            "baseline_repeat_hash": bh2,
            "repair_tree_hash": rh1,
            "repair_repeat_hash": rh2,
            "baseline_deterministic": bh1 == bh2,
            "repair_deterministic": rh1 == rh2,
            "baseline_vs_repair_equal": bh1 == rh1,
            "baseline_nodes": sum(1 for _ in bt1.iter_subtrees()),
            "repair_nodes": sum(1 for _ in rt1.iter_subtrees()),
        })

    intentionally_tightened = {
        "if_record_field": "record X { if:Int }\n",
        "if_parameter": "needle f(if:Int)->Int\n",
        "invariant_record_field": "record X { invariant:Int }\n",
        "invariant_parameter": "needle f(invariant:Int)->Int\n",
    }
    tightened_rows = []
    for name, src in intentionally_tightened.items():
        b_ok, b_hash, b_err = parse_case(baseline, src)
        r_ok, r_hash, r_err = parse_case(repair, src)
        tightened_rows.append({
            "case": name,
            "baseline_accepted": b_ok,
            "repair_accepted": r_ok,
            "expected_repair": "REJECT",
            "pass": not r_ok,
            "baseline_hash": b_hash,
            "repair_hash": r_hash,
            "baseline_error": b_err,
            "repair_error": r_err,
        })

    preserved_boundaries = {
        "if_statement": "cycle(input:Ref){\nif input {\ntrue\n}\n}\n",
        "invariant_statement": "invariant activation!=truth\n",
        "record_blank_lines": "record X {\n\n a:Int\n\n b:Int\n\n}\n",
        "cycle_blank_lines": "cycle(input:Ref){\n\n input\n\n}\n",
        "ordinary_keyword_like_names": "record X { status:Int; dialect:Int; version:Int; requires:Int }\n",
    }
    preserved_rows = []
    for name, src in preserved_boundaries.items():
        b_ok, b_hash, b_err = parse_case(baseline, src)
        r_ok, r_hash, r_err = parse_case(repair, src)
        preserved_rows.append({
            "case": name,
            "baseline_accepted": b_ok,
            "repair_accepted": r_ok,
            "tree_equal_when_both_accept": bool(b_ok and r_ok and b_hash == r_hash),
            "pass": bool(b_ok and r_ok and b_hash == r_hash),
            "baseline_error": b_err,
            "repair_error": r_err,
        })

    sources_pass = all(
        row["baseline_deterministic"]
        and row["repair_deterministic"]
        and row["baseline_vs_repair_equal"]
        for row in source_rows
    )
    tightened_pass = all(row["pass"] for row in tightened_rows)
    boundaries_pass = all(row["pass"] for row in preserved_rows)
    passed = sources_pass and tightened_pass and boundaries_pass

    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE D baseline-vs-repair full-corpus grammar differential",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "baseline": {
            "path": str(baseline_path.relative_to(ROOT)),
            "sha256": sha256(baseline_text.encode("utf-8")),
            "mode": "lalr/contextual strict=False because known parser-table conflicts are the subject under repair",
        },
        "repair": {
            "path": str(repair_path.relative_to(ROOT)),
            "sha256": sha256(repair_text.encode("utf-8")),
            "mode": "lalr/contextual strict=True",
        },
        "sources": source_rows,
        "intentionally_tightened_keyword_identifier_cases": tightened_rows,
        "preserved_boundary_cases": preserved_rows,
        "pass": passed,
        "scope_guard": (
            "PASS establishes identical deterministic parse-tree structure for the current admitted G9 V3 and Dialect V3 corpus, "
            "plus the declared keyword/newline boundary behavior. It is not typed canonical-AST, type/effect, evaluator, lowering, "
            "runtime, Ubuntu-target or application-suite proof and cannot alone close CC-WP-02 or any later BASE package."
        ),
    }
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
