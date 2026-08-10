#!/usr/bin/env python3
"""Shadow validation for ClayCode BASE D V18 no-lookahead candidate.

Research-only: V18 is not selected as production grammar by this tool. The validator
compares V18 against the current V17 production frontend on the current G9/Dialect
sources and on the exact Needle call/relation boundary that motivated V17.

Promotion guard: V18 must construct under Lark strict=True on the target lane, preserve
accept/reject behavior, and after explicit tree normalization produce byte-identical
ClayCodeBaseFrontendAST/v1 semantic hashes to V17. Grammar/contract hashes are expected
to differ; semantic hashes must not drift for equivalent accepted programs.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path

from lark import Token, Tree

import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
V18 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_NO_LOOKAHEAD.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_v18_tree(node):
    """Map V18 parser-only shapes back to the existing V17 AST/v1 contract."""
    if isinstance(node, Tree):
        kind = str(node.data)
        if kind == "special_owns_call":
            qid = Tree("qid", [Token("NAME", "Needle"), Token("DOT", "."), Token("NAME", "owns")])
            return Tree("call", [qid, *[normalize_v18_tree(x) for x in node.children[1:]]])
        if kind == "needle_owns_atom":
            return Tree("qid", [Token("NAME", "Needle"), Token("DOT", "."), Token("NAME", "owns")])
        return Tree(node.data, [normalize_v18_tree(x) for x in node.children])
    if isinstance(node, Token) and node.type in {"NEEDLE_OWNS", "NEEDLE_LOWERS"}:
        return Token("DOTTED_PREFIX_REL", str(node))
    return node


def semantic_hash(tree: Tree) -> str:
    ast = front.canonical_node(tree)
    return sha(front.DOMAIN + front.canonical_bytes(ast))


def parse_state(parser, source: str) -> tuple[bool, str | None, Tree | None]:
    try:
        tree = parser.parse(source)
        return True, None, tree
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}", None


def main() -> int:
    g17 = V17.read_text(encoding="utf-8")
    g18 = V18.read_text(encoding="utf-8")

    # Strict=True is deliberate. If interegular is missing this validator must fail,
    # rather than silently downgrade the collision evidence.
    p17 = front.build_parser(g17, strict=True)
    p18 = front.build_parser(g18, strict=True)

    source_rows = []
    for path in SOURCES:
        src = path.read_text(encoding="utf-8")
        t17 = p17.parse(src)
        t18 = normalize_v18_tree(p18.parse(src))
        h17 = semantic_hash(t17)
        h18 = semantic_hash(t18)
        source_rows.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha(src.encode("utf-8")),
            "v17_semantic_hash": h17,
            "v18_normalized_semantic_hash": h18,
            "semantic_equal": h17 == h18,
            "v17_tree_nodes": sum(1 for _ in t17.iter_subtrees()),
            "v18_normalized_tree_nodes": sum(1 for _ in t18.iter_subtrees()),
        })

    expected_accept = [
        "rule Needle.lowers X\n",
        "rule Needle.lowers\tX\n",
        "rule Needle.owns X\n",
        "rule Needle.owns\tX\n",
        "rule Needle.owns(X)\n",
        "rule Needle.owns (X)\n",
        "rule Needle.owns\t(X)\n",
        "rule Needle.owns \t (X)\n",
        "rule 4B_need_not_learn Needle.owns\n",
    ]
    expected_reject = [
        "rule Needle.lowers\n",
        "rule Needle.lowers (X)\n",
        "rule Needle.lowers\t(X)\n",
    ]

    cases = []
    for src in expected_accept + expected_reject:
        expect = src in expected_accept
        ok17, err17, t17 = parse_state(p17, src)
        ok18, err18, t18 = parse_state(p18, src)
        sem_equal = None
        if ok17 and ok18 and t17 is not None and t18 is not None:
            sem_equal = semantic_hash(t17) == semantic_hash(normalize_v18_tree(t18))
        cases.append({
            "source": src,
            "expected_accept": expect,
            "v17_accept": ok17,
            "v18_accept": ok18,
            "v17_error": err17,
            "v18_error": err18,
            "semantic_equal_if_accepted": sem_equal,
            "pass": ok17 == expect and ok18 == expect and (sem_equal is not False),
        })

    call_variants = [
        "rule Needle.owns(X)\n",
        "rule Needle.owns (X)\n",
        "rule Needle.owns\t(X)\n",
        "rule Needle.owns \t (X)\n",
    ]
    relation_variants = ["rule Needle.owns X\n", "rule Needle.owns\tX\n"]
    v18_call_hashes = {semantic_hash(normalize_v18_tree(p18.parse(x))) for x in call_variants}
    v18_relation_hashes = {semantic_hash(normalize_v18_tree(p18.parse(x))) for x in relation_variants}
    metamorphic = {
        "call_horizontal_trivia_invariant": len(v18_call_hashes) == 1,
        "relation_horizontal_trivia_invariant": len(v18_relation_hashes) == 1,
        "call_vs_relation_discriminated": next(iter(v18_call_hashes)) != next(iter(v18_relation_hashes)),
    }

    lookaround = "(?=" in g18 or "(?<=" in g18 or "(?!" in g18 or "(?<!" in g18
    passed = (
        not lookaround
        and all(x["semantic_equal"] for x in source_rows)
        and all(x["pass"] for x in cases)
        and all(metamorphic.values())
    )

    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE D V18 no-lookahead shadow differential",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime": {
            "lark_version": pkg("lark"),
            "interegular_version": pkg("interegular"),
            "parser": "lalr/contextual",
            "strict": True,
            "maybe_placeholders": False,
        },
        "v17_grammar_sha256": sha(g17.encode("utf-8")),
        "v18_grammar_sha256": sha(g18.encode("utf-8")),
        "v18_regex_lookaround_present": lookaround,
        "sources": source_rows,
        "boundary_cases": cases,
        "metamorphic": metamorphic,
        "pass": passed,
        "selection_status": "RESEARCH_CANDIDATE_ONLY",
        "scope_guard": (
            "PASS supports V18 as a no-lookahead parser candidate with strict construction and V17 AST/v1 semantic equivalence on the current bounded corpus. "
            "It does not select V18, close CC-WP-02, prove typed IR/type/effect semantics, or substitute for an Ubuntu/current-main receipt."
        ),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
