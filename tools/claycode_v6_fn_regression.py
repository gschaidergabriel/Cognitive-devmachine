#!/usr/bin/env python3
"""Strict V6 typed-function frontend/canonical identity regression.

This is an evidence gate for the WP02->WP03 boundary, not a production checker/evaluator.
Operator/punctuation identity is preserved; newline/comment/spacing layout is ignored.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedInput

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V6_FN.lark"
OUT = ROOT / "research_entity/claycode/autonomous/V6_FN_FRONTEND_IDENTITY_RECEIPT.json"

VALID = {
    "typed_add": "fn add(a:Int,b:Int)->Int=a+b\n",
    "typed_call": "fn twice(x:Int)->Int=add(x,x)\n",
    "fn_contextual_field": "record X { fn:Int }\n",
    "typed_union_optional": "fn choose(x:Ref|Unknown,y:Ref?)->Ref=x\n",
}
INVALID = {
    "untyped_parameter": "fn bad(a)->Int=a\n",
    "missing_return_type": "fn bad(a:Int)=a\n",
    "missing_body": "fn bad(a:Int)->Int\n",
}
EQUIV_A = "fn add(a:Int,b:Int)->Int=a+b\n"
EQUIV_B = "// formatting-only\nfn   add ( a : Int , b : Int ) -> Int = a + b\n"
MUTATIONS = {
    "plus_to_minus": "fn add(a:Int,b:Int)->Int=a-b\n",
    "return_type": "fn add(a:Int,b:Int)->Real=a+b\n",
    "parameter_order": "fn add(b:Int,a:Int)->Int=a+b\n",
}


def normalized(node):
    if isinstance(node, Tree):
        children = []
        for x in node.children:
            v = normalized(x)
            if v is not None:
                children.append(v)
        return [str(node.data), children]
    if isinstance(node, Token):
        if node.type == "NEWLINE":
            return None
        return [node.type, str(node)]
    return node


def semantic_tree_hash(tree: Tree) -> str:
    payload = json.dumps(normalized(tree), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    parser = Lark(
        grammar_text,
        parser="lalr",
        lexer="contextual",
        strict=True,
        start="start",
        keep_all_tokens=True,
    )
    failures: list[str] = []
    valid = {}
    invalid = {}

    for name, source in VALID.items():
        try:
            valid[name] = {"pass": True, "tree_hash": semantic_tree_hash(parser.parse(source))}
        except Exception as exc:
            valid[name] = {"pass": False, "error": repr(exc)}
            failures.append(f"valid:{name}")

    for name, source in INVALID.items():
        try:
            parser.parse(source)
            invalid[name] = {"pass": False, "error": "unexpected_accept"}
            failures.append(f"invalid:{name}")
        except UnexpectedInput as exc:
            invalid[name] = {"pass": True, "error_type": type(exc).__name__}

    ha = semantic_tree_hash(parser.parse(EQUIV_A))
    hb = semantic_tree_hash(parser.parse(EQUIV_B))
    equiv_ok = ha == hb
    if not equiv_ok:
        failures.append("format_comment_semantic_identity")

    mutation_rows = {}
    for name, source in MUTATIONS.items():
        hm = semantic_tree_hash(parser.parse(source))
        ok = hm != ha
        mutation_rows[name] = {"pass": ok, "base": ha, "mutated": hm}
        if not ok:
            failures.append(f"semantic_mutation_discrimination:{name}")

    report = {
        "schema_version": "1.1",
        "scope": "V6_TYPED_FN_FRONTEND_AND_LITERAL_SAFE_PARSE_IDENTITY_NOT_PRODUCTION_TYPED_IR",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "grammar_sha256": hashlib.sha256(grammar_text.encode("utf-8")).hexdigest(),
        "strict_lalr_constructed": True,
        "parser_identity_policy": "keep_all_tokens=True; NEWLINE dropped from identity; ignored comments/WS absent; operators/punctuation retained",
        "valid_cases": valid,
        "invalid_cases": invalid,
        "format_comment_equivalence": {"pass": equiv_ok, "hash_a": ha, "hash_b": hb},
        "semantic_mutation_discrimination": mutation_rows,
        "authority_guard": "Parsing/binding surface never mints effect authority; production type/effect checker remains separate.",
        "failure_count": len(failures),
        "failures": failures,
        "pass": not failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "failures": failures, "out": str(OUT.relative_to(ROOT))}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
