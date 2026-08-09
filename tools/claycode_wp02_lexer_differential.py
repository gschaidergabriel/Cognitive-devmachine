#!/usr/bin/env python3
"""Bounded WP-02 lexer-dependence diagnostic for ClayCode BASE.

This is the one out-of-the-box experiment for go/2026-08-10T06:40+07:00.
It does not replace the production frontend validator and must not promote CC-WP-02.
It asks whether the admitted V17 grammar's observable parse semantics depend on
Lark's contextual lexer rather than grammar structure alone.

A basic-lexer failure/difference is diagnostic counterevidence, not an automatic
bug claim: Lark explicitly permits the contextual lexer to resolve token overlap.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from lark import Lark, Tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_tree(node):
    if isinstance(node, Tree):
        return [str(node.data), [canonical_tree(x) for x in node.children]]
    return [getattr(node, "type", type(node).__name__), str(node)]


def tree_hash(tree: Tree) -> str:
    payload = json.dumps(canonical_tree(tree), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def construct(grammar: str, lexer: str):
    try:
        return Lark(
            grammar,
            parser="lalr",
            lexer=lexer,
            strict=True,
            start="start",
            keep_all_tokens=True,
        ), None
    except Exception as exc:  # receipt must preserve exact construction failure
        return None, f"{type(exc).__name__}: {exc}"


def parse_case(parser: Lark, source: str) -> dict:
    try:
        tree = parser.parse(source)
        return {"accepted": True, "tree_hash": tree_hash(tree), "error": None}
    except Exception as exc:
        return {"accepted": False, "tree_hash": None, "error": f"{type(exc).__name__}: {exc}"}


def evaluate_mode(grammar: str, lexer: str) -> dict:
    parser, construction_error = construct(grammar, lexer)
    out = {
        "lexer": lexer,
        "constructed": parser is not None,
        "construction_error": construction_error,
        "sources": [],
        "equivalence_families": {},
        "discrimination": {},
    }
    if parser is None:
        return out

    for path in SOURCES:
        text = path.read_text(encoding="utf-8")
        row = parse_case(parser, text)
        row.update({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha256_bytes(text.encode("utf-8")),
        })
        out["sources"].append(row)

    equivalence_families = {
        "qualified_call_horizontal_trivia": [
            "rule Needle.owns(X)\n",
            "rule Needle.owns (X)\n",
            "rule Needle.owns  (X)\n",
            "rule Needle.owns        (X)\n",
        ],
        "prefix_relation_horizontal_trivia": [
            "rule Needle.owns X\n",
            "rule Needle.owns  X\n",
            "rule Needle.owns        X\n",
        ],
        "comment_trivia": [
            "rule x>0\n",
            "rule x > 0 // diagnostic comment\n",
        ],
    }
    for name, cases in equivalence_families.items():
        rows = [parse_case(parser, case) for case in cases]
        accepted = all(r["accepted"] for r in rows)
        hashes = {r["tree_hash"] for r in rows if r["tree_hash"] is not None}
        out["equivalence_families"][name] = {
            "cases": cases,
            "results": rows,
            "all_accepted": accepted,
            "single_semantic_hash": accepted and len(hashes) == 1,
        }

    discriminations = {
        "call_vs_prefix_relation": ("rule Needle.owns(X)\n", "rule Needle.owns X\n"),
        "lowers_call_vs_prefix_relation": ("rule Needle.lowers(X)\n", "rule Needle.lowers X\n"),
    }
    for name, (left, right) in discriminations.items():
        lrow = parse_case(parser, left)
        rrow = parse_case(parser, right)
        out["discrimination"][name] = {
            "left": left,
            "right": right,
            "left_result": lrow,
            "right_result": rrow,
            "both_accepted": lrow["accepted"] and rrow["accepted"],
            "different_semantic_hash": (
                lrow["accepted"] and rrow["accepted"] and lrow["tree_hash"] != rrow["tree_hash"]
            ),
        }
    return out


def mode_semantic_summary(mode: dict) -> dict:
    return {
        "constructed": mode["constructed"],
        "source_acceptance": [x["accepted"] for x in mode["sources"]],
        "source_hashes": [x["tree_hash"] for x in mode["sources"]],
        "equivalence": {
            k: (v["all_accepted"], v["single_semantic_hash"])
            for k, v in mode["equivalence_families"].items()
        },
        "discrimination": {
            k: (v["both_accepted"], v["different_semantic_hash"])
            for k, v in mode["discrimination"].items()
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--output")
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    grammar = grammar_path.read_text(encoding="utf-8")

    contextual = evaluate_mode(grammar, "contextual")
    basic = evaluate_mode(grammar, "basic")

    contextual_gate = (
        contextual["constructed"]
        and contextual["sources"]
        and all(x["accepted"] for x in contextual["sources"])
        and all(
            x["all_accepted"] and x["single_semantic_hash"]
            for x in contextual["equivalence_families"].values()
        )
        and all(
            x["both_accepted"] and x["different_semantic_hash"]
            for x in contextual["discrimination"].values()
        )
    )

    contextual_summary = mode_semantic_summary(contextual)
    basic_summary = mode_semantic_summary(basic)
    if not basic["constructed"]:
        dependence = "BASIC_LEXER_CONSTRUCTION_FAILED_CONTEXTUAL_DEPENDENCE_SIGNAL"
    elif contextual_summary != basic_summary:
        dependence = "CONTEXTUAL_VS_BASIC_OBSERVABLE_DIFFERENCE"
    else:
        dependence = "NO_CONTEXTUAL_LEXER_DEPENDENCE_OBSERVED_ON_BOUNDARY_FIXTURES"

    try:
        lark_version = importlib.metadata.version("lark")
    except importlib.metadata.PackageNotFoundError:
        lark_version = "UNKNOWN"
    try:
        interegular_version = importlib.metadata.version("interegular")
    except importlib.metadata.PackageNotFoundError:
        interegular_version = "UNKNOWN"

    out = {
        "schema_version": "1.0",
        "experiment": "WP02 bounded contextual-vs-basic lexer differential under horizontal-trivia perturbation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "OUT_OF_BOX_EXPERIMENT_ONLY_NOT_WP02_PROMOTION",
        "hypothesis": "V17 preserves admitted call/relation semantics under horizontal trivia without hidden contextual-lexer dependence on tested boundaries.",
        "counterhypothesis": "The apparent V17 repair relies materially on contextual-lexer state and can diverge or fail under a basic lexer on semantically equivalent boundary fixtures.",
        "grammar_path": str(grammar_path.relative_to(ROOT)),
        "grammar_sha256": sha256_bytes(grammar.encode("utf-8")),
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "UNKNOWN",
            "lark": lark_version,
            "interegular": interegular_version,
        },
        "contextual": contextual,
        "basic": basic,
        "contextual_gate_pass": contextual_gate,
        "dependency_classification": dependence,
        "interpretation_guard": "A basic-lexer difference is evidence of contextual-lexer dependence on these fixtures, not proof of an upstream Lark bug or ClayCode semantic failure. Promotion still requires the production WP02 canonicalizer/hash and Ubuntu receipts.",
    }

    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")
    if not contextual_gate:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
