#!/usr/bin/env python3
"""Discriminate the ClayCode V10 unified frontend candidate against live V9/V7 contracts.

This tool is evidence-oriented and deliberately non-promoting.  It answers one narrow
question: can V10 remove the current parser-contract drift without changing the typed/pure
semantics already implemented by V7, while preserving V9 frontend/canonical obligations?
The provenance-bound FRANK root is probed in the same run so a still-open high-level
surface gap cannot be silently mistaken for V10 BASE acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark, Tree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import claycode_base_canonical_ir_validation as cir  # noqa: E402
import claycode_base_compiler as compiler  # noqa: E402
import claycode_base_typed_ir as tir  # noqa: E402
import claycode_frank_frontend_gap_probe as frank_probe  # noqa: E402

V7 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
V9 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark"
V10 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V10_OPERATOR_FN_DOTTED.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"
PURE = ROOT / "research_entity/claycode/base/examples/PURE_CORE_V1.clay"
FRANK = ROOT / "frank_reference/claycode/frank_runtime.clay"
FRANK_PROV = ROOT / "frank_reference/claycode/frank_runtime.provenance.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grammar_row(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def parser_for(path: Path, *, strict: bool) -> Lark:
    return Lark(
        path.read_text(encoding="utf-8"),
        parser="lalr",
        lexer="contextual",
        strict=strict,
        start="start",
        keep_all_tokens=True,
        maybe_placeholders=False,
    )


def canonical_tree(node: Any) -> Any:
    if isinstance(node, Tree):
        return [str(node.data), [canonical_tree(x) for x in node.children]]
    return [getattr(node, "type", type(node).__name__), str(node)]


def parse_source(parser: Lark, path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    t1 = parser.parse(source)
    t2 = parser.parse(source)
    h1 = sha(json.dumps(canonical_tree(t1), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    h2 = sha(json.dumps(canonical_tree(t2), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    return {
        "path": str(path.relative_to(ROOT)),
        "source_sha256": sha(source.encode("utf-8")),
        "tree_hash": h1,
        "repeat_tree_hash": h2,
        "deterministic": h1 == h2,
        "tree_nodes": sum(1 for _ in t1.iter_subtrees()),
    }


def canonical_suite(parser: Lark, sources: list[Path]) -> dict[str, Any]:
    rows = [cir.source_receipt(parser, p) for p in sources]
    cases = [
        cir.pair_case(parser, "ignored_space_comment", "rule x>0\n", "rule   x > 0 // comment\n", True),
        cir.pair_case(parser, "greater_vs_less", "rule x>0\n", "rule x<0\n", False),
        cir.pair_case(parser, "gte_vs_lte", "rule x>=0\n", "rule x<=0\n", False),
        cir.pair_case(parser, "equal_vs_not_equal", "rule x=0\n", "rule x!=0\n", False),
        cir.pair_case(parser, "plus_vs_minus", "rule x+1\n", "rule x-1\n", False),
        cir.pair_case(parser, "and_vs_or", "rule x&&true\n", "rule x||true\n", False),
        cir.pair_case(parser, "true_vs_false", "rule true\n", "rule false\n", False),
        cir.pair_case(parser, "ordered_call_arguments", "rule f(a,b)\n", "rule f(b,a)\n", False),
        cir.pair_case(parser, "dotted_relation_kind", "rule Needle.lowers X\n", "rule Needle.owns X\n", False),
        cir.pair_case(parser, "bare_owns_vs_prefix_owns", "rule 4B_need_not_learn Needle.owns\n", "rule Needle.owns X\n", False),
    ]
    passed = all(x["roundtrip_byte_identical"] and x["repeat_parse_byte_identical"] for x in rows) and all(x["pass"] for x in cases)
    return {"sources": rows, "cases": cases, "pass": passed}


def typed_ir_pair() -> dict[str, Any]:
    a = tir.compile_sources([G9, DIALECT], V7)
    b = tir.compile_sources([G9, DIALECT], V10)
    same_semantic_id = a["program_semantic_id"] == b["program_semantic_id"]
    same_semantic_core = tir.canon_bytes({k: v for k, v in a.items() if k not in {"sources", "typed_ir_sha256", "program_semantic_id"}}) == tir.canon_bytes({k: v for k, v in b.items() if k not in {"sources", "typed_ir_sha256", "program_semantic_id"}})
    return {
        "v7_program_semantic_id": a["program_semantic_id"],
        "v10_program_semantic_id": b["program_semantic_id"],
        "same_program_semantic_id": same_semantic_id,
        "same_semantic_core": same_semantic_core,
        "v7_source_contracts": a.get("sources", []),
        "v10_source_contracts": b.get("sources", []),
        "pass": same_semantic_id and same_semantic_core,
    }


def pure_compiler_pair() -> dict[str, Any]:
    source = PURE.read_text(encoding="utf-8")
    g7 = V7.read_text(encoding="utf-8")
    g10 = V10.read_text(encoding="utf-8")
    a = compiler.build(source, g7)
    b = compiler.build(source, g10)
    same_ir = a["ir"] == b["ir"]
    same_semantic_hash = a["semantic_hash"] == b["semantic_hash"]
    functions = {f["name"]: f for f in a["ir"]["functions"]}
    cases = {
        "add": [2, 3],
        "muladd": [2, 3, 4],
        "twice": [9],
        "positive": [-7],
        "same": [4, 4],
        "both": [True, False],
        "ratio": [5, 2],
    }
    evaluations = []
    for name, args in cases.items():
        if name not in functions:
            evaluations.append({"name": name, "args": args, "pass": False, "error": "MISSING_FUNCTION"})
            continue
        av = compiler.eval_function(a["ir"], name, args)
        bv = compiler.eval_function(b["ir"], name, args)
        evaluations.append({"name": name, "args": args, "v7": av, "v10": bv, "pass": av == bv})
    c7 = compiler.lower_c(a["ir"])
    c10 = compiler.lower_c(b["ir"])
    return {
        "v7_semantic_hash": a["semantic_hash"],
        "v10_semantic_hash": b["semantic_hash"],
        "same_typed_ir": same_ir,
        "same_semantic_hash": same_semantic_hash,
        "same_lowered_c": c7 == c10,
        "lowered_c_sha256_v7": sha(c7.encode("utf-8")),
        "lowered_c_sha256_v10": sha(c10.encode("utf-8")),
        "evaluations": evaluations,
        "pass": same_ir and same_semantic_hash and c7 == c10 and all(x["pass"] for x in evaluations),
    }


def frank_surface(parser: Lark) -> dict[str, Any]:
    source = FRANK.read_text(encoding="utf-8")
    try:
        tree = parser.parse(source)
        return {"accepted": True, "error_class": None, "error": None, "tree_nodes": sum(1 for _ in tree.iter_subtrees())}
    except Exception as exc:
        return {"accepted": False, "error_class": type(exc).__name__, "error": str(exc), "tree_nodes": None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    ap.add_argument("--proxy-nonstrict", action="store_true", help="Hosted/sandbox evidence only; never target acceptance.")
    args = ap.parse_args()
    strict = not args.proxy_nonstrict

    provenance = frank_probe.read_provenance(FRANK_PROV, FRANK)
    parsers: dict[str, Lark] = {}
    construction: dict[str, dict[str, Any]] = {}
    for label, path in (("V9", V9), ("V10", V10)):
        try:
            parsers[label] = parser_for(path, strict=strict)
            construction[label] = {"pass": True, "error": None}
        except Exception as exc:
            construction[label] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"}

    if not all(x["pass"] for x in construction.values()):
        receipt = {
            "schema_version": "1.0",
            "experiment": "ClayCode V10 unified frontend discriminator",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "evidence_class": "HOSTED_PROXY_NONSTRICT" if args.proxy_nonstrict else "STRICT_HOST_DISCRIMINATOR",
            "strict_parser": strict,
            "grammars": {"V7": grammar_row(V7), "V9": grammar_row(V9), "V10": grammar_row(V10)},
            "parser_construction": construction,
            "pass": False,
            "v10_adoption_candidate": False,
            "scope_guard": "Parser construction failed; no downstream equivalence result is valid and no promotion is allowed.",
        }
        text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 2

    full_corpus = {label: [parse_source(parser, G9), parse_source(parser, DIALECT)] for label, parser in parsers.items()}
    canonical = {label: canonical_suite(parser, [G9, DIALECT]) for label, parser in parsers.items()}
    typed = typed_ir_pair()
    pure = pure_compiler_pair()
    frank = {label: frank_surface(parser) for label, parser in parsers.items()}

    v9_frank = frank["V9"]["accepted"]
    v10_frank = frank["V10"]["accepted"]
    frank_no_regression = v10_frank or not v9_frank
    frank_route_open = not v10_frank
    corpus_pass = all(all(x["deterministic"] for x in rows) for rows in full_corpus.values())
    core_pass = corpus_pass and all(x["pass"] for x in canonical.values()) and typed["pass"] and pure["pass"] and frank_no_regression

    receipt = {
        "schema_version": "1.0",
        "experiment": "ClayCode V10 unified frontend discriminator",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "HOSTED_PROXY_NONSTRICT" if args.proxy_nonstrict else "STRICT_HOST_DISCRIMINATOR",
        "strict_parser": strict,
        "grammars": {"V7": grammar_row(V7), "V9": grammar_row(V9), "V10": grammar_row(V10)},
        "parser_construction": construction,
        "full_corpus": full_corpus,
        "canonical_ir": canonical,
        "typed_ir_v7_vs_v10": typed,
        "pure_compiler_v7_vs_v10": pure,
        "frank_source": {"provenance": provenance, "V9": frank["V9"], "V10": frank["V10"], "v10_no_regression": frank_no_regression, "surface_route_still_open": frank_route_open},
        "pass": core_pass,
        "v10_adoption_candidate": core_pass and strict,
        "promotion_allowed": False,
        "decision": (
            "V10 may advance to explicit review as the unified BASE frontend candidate only when this strict discriminator passes. "
            "A still-rejected provenance-bound FRANK root remains a separate dialect/pre-lowering classification blocker; it is not silently waived."
        ),
        "scope_guard": "Even strict PASS is a discriminator receipt, not CC-WP-02/03/BASE PASS. Physical Andreas Ubuntu BASE14 and FULL_FRANK receipts remain separate gates.",
    }
    text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if core_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
