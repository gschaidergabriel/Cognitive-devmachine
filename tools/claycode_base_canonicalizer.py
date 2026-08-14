#!/usr/bin/env python3
"""Deterministic syntax canonicalizer for the active ClayCode BASE repaired frontend.

Scope: CC-WP-02 only. This converts an accepted Lark syntax tree into a stable JSON
representation that is insensitive to comments and equivalent block-separator/layout
trivia while preserving every non-layout semantic value that can change program meaning.
The canonical hash is bound to the exact grammar bytes so parser-contract drift cannot
silently preserve an old identity. It does NOT claim typed canonical IR; that remains
CC-WP-03.

The JSON serialization below is a project-local ClayCode syntax-identity envelope. It uses
deterministic compact key-sorted serialization, but it does not claim RFC 8785/JCS
conformance; grammar binding and ClayCode's own syntax contract remain authoritative.

CRITICAL PARITY LAW: canonical AST semantics have one active implementation only:
``claycode_base_frontend.canonical_node``. This standalone tool may wrap that AST in its
own grammar-bound canonical-syntax envelope/hash, but it may not independently reinterpret
parser nodes. That prevents production-vs-standalone semantic drift.

V18 inherits V17's mandatory semantic-trivia guards: `Needle.owns(X)` ==
`Needle.owns (X)` while `Needle.owns X` remains a distinct prefix relation. Redundant
expression grouping is also surface syntax: `x>0`, `(x>0)`, `((x>0))`, and a grouped call
must retain production AST identity. V18 additionally admits only the measured current-G9
reward relations `preserves`, `required_before`, and `cannot_be_silently_averaged_away`.
Calls/lists/sets/operators remain structurally preserved by the production canonicalizer.

The canonicalizer MUST use the exact production parser constructor. In particular,
production sets maybe_placeholders=False, so absent [] optionals are semantic absence and
must never become synthetic `None` children in canonical syntax identity.

STRING tokens inherit production canonicalization: decoded JSON Unicode scalar sequence,
not escape spelling. Thus `"é"` and `"\\u00e9"` share syntax identity, while `"é"` and
`"e\\u0301"` remain different. Unpaired surrogates are rejected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark, Tree

import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
DEFAULT_SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
CANON_SCHEMA = "claycode-base-canonical-syntax/2"


class CanonicalizationError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_node(node: Any) -> Any | None:
    """Use the production frontend as the sole canonical-AST semantic authority."""
    if node is None:
        raise CanonicalizationError(
            "unexpected None parse child: production maybe_placeholders=False contract drifted"
        )
    try:
        return front.canonical_node(node)
    except front.CanonicalizationError as exc:
        raise CanonicalizationError(str(exc)) from exc


def count_none_children(node: Any) -> int:
    if node is None:
        return 1
    if isinstance(node, Tree):
        return sum(count_none_children(child) for child in node.children)
    return 0


def semantic_hash(payload: Any, grammar_sha256: str) -> str:
    envelope = {"schema": CANON_SCHEMA, "grammar_sha256": grammar_sha256, "ast": payload}
    return sha256_bytes(stable_json(envelope))


def parse_canonical(parser: Lark, source: str, grammar_sha256: str) -> tuple[Any, str]:
    tree = parser.parse(source)
    if count_none_children(tree) != 0:
        raise CanonicalizationError(
            "synthetic optional placeholder detected: canonicalizer must match production absence semantics"
        )
    payload = canonical_node(tree)
    return payload, semantic_hash(payload, grammar_sha256)


def verify_roundtrip(payload: Any, grammar_sha256: str, expected_hash: str) -> dict[str, Any]:
    encoded = stable_json(payload)
    decoded = json.loads(encoded.decode("utf-8"))
    recomputed = semantic_hash(decoded, grammar_sha256)
    return {
        "json_roundtrip_equal": decoded == payload,
        "semantic_hash_recomputed": recomputed,
        "semantic_hash_matches": recomputed == expected_hash,
    }


def layout_variant(source: str) -> str:
    return "// canonicalizer-layout-variant\n\n" + source.replace("\n", "\n\n") + "\n// canonicalizer-layout-end\n"


def pair_receipt(parser: Lark, grammar_sha256: str, left: str, right: str, expect_same: bool) -> dict[str, Any]:
    _, lh = parse_canonical(parser, left, grammar_sha256)
    _, rh = parse_canonical(parser, right, grammar_sha256)
    observed_same = lh == rh
    return {
        "left": left,
        "right": right,
        "left_hash": lh,
        "right_hash": rh,
        "expected_same": expect_same,
        "observed_same": observed_same,
        "pass": observed_same == expect_same,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--source", action="append", dest="sources")
    ap.add_argument("--output")
    ap.add_argument(
        "--relaxed-parser-for-test",
        action="store_true",
        help="Disable strict collision checking only in disposable environments lacking interegular; never a release receipt.",
    )
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    grammar = grammar_path.read_text(encoding="utf-8")
    grammar_sha = sha256_bytes(grammar.encode("utf-8"))
    strict = not args.relaxed_parser_for_test
    parser = front.build_parser(grammar, strict=strict)

    source_paths = [Path(x) for x in args.sources] if args.sources else list(DEFAULT_SOURCES)
    rows = []
    overall = True
    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        ast1, h1 = parse_canonical(parser, text, grammar_sha)
        _, h2 = parse_canonical(parser, text, grammar_sha)
        _, hv = parse_canonical(parser, layout_variant(text), grammar_sha)
        repeat_ok = h1 == h2
        layout_ok = h1 == hv
        roundtrip = verify_roundtrip(ast1, grammar_sha, h1)
        roundtrip_ok = all(v for k, v in roundtrip.items() if k != "semantic_hash_recomputed")
        overall = overall and repeat_ok and layout_ok and roundtrip_ok
        rows.append({
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "source_sha256": sha256_bytes(text.encode("utf-8")),
            "canonical_syntax_sha256": h1,
            "repeat_canonical_sha256": h2,
            "layout_variant_canonical_sha256": hv,
            "repeat_deterministic": repeat_ok,
            "comment_whitespace_layout_invariant": layout_ok,
            "canonical_json_roundtrip": roundtrip,
            "canonical_root_kind": ast1.get("kind") if isinstance(ast1, dict) else None,
        })

    distinct_cases = {
        "greater_vs_less": ("rule x>0\n", "rule x<0\n"),
        "gte_vs_lte": ("rule x>=0\n", "rule x<=0\n"),
        "equal_vs_not_equal": ("rule x=0\n", "rule x!=0\n"),
        "plus_vs_minus": ("rule x+1\n", "rule x-1\n"),
        "and_vs_or": ("rule x&&true\n", "rule x||true\n"),
        "boolean_value": ("rule true\n", "rule false\n"),
        "argument_order": ("rule f(a,b)\n", "rule f(b,a)\n"),
        "dotted_relation_kind": ("rule Needle.lowers X\n", "rule Needle.owns X\n"),
        "bare_owns_vs_prefix_owns": ("rule 4B_need_not_learn Needle.owns\n", "rule Needle.owns X\n"),
        "call_vs_prefix_owns": ("rule Needle.owns(X)\n", "rule Needle.owns X\n"),
        "lifecycle_order": (
            "rule external_effect lifecycle=[REQUESTED,AUTHORIZED,DONE]\n",
            "rule external_effect lifecycle=[AUTHORIZED,REQUESTED,DONE]\n",
        ),
        "optional_type": ("record X { a:Int }\n", "record X { a:Int? }\n"),
        "string_exact_scalar_sequence": ('rule label="é"\n', 'rule label="e\\u0301"\n'),
        "preserves_vs_requires": ("rule a preserves b\n", "rule a requires b\n"),
        "required_before_vs_requires": ("rule a required_before b\n", "rule a requires b\n"),
    }
    distinct = [
        {"case": name, **pair_receipt(parser, grammar_sha, left, right, expect_same=False)}
        for name, (left, right) in distinct_cases.items()
    ]

    equivalent_cases = {
        "space_comment_layout": ("rule x>0\n", "// ignored\nrule   x > 0 // ignored\n"),
        "record_block_separator": (
            "record X {\n a:Int\n b:Int\n}\n",
            "record X { a:Int; b:Int }\n",
        ),
        "qualified_owns_call_horizontal_trivia": (
            "rule Needle.owns(X)\n",
            "rule Needle.owns (X)\n",
        ),
        "qualified_owns_call_long_horizontal_trivia": (
            "rule Needle.owns(X)\n",
            "rule Needle.owns          (X)\n",
        ),
        "single_redundant_group": ("rule x>0\n", "rule (x>0)\n"),
        "nested_redundant_group": ("rule x>0\n", "rule ((x>0))\n"),
        "grouped_call": ("rule Needle.owns(X)\n", "rule (Needle.owns(X))\n"),
        "string_escape_spelling": ('rule label="é"\n', 'rule label="\\u00e9"\n'),
        "string_surrogate_pair_escape_spelling": ('rule label="𝄞"\n', 'rule label="\\ud834\\udd1e"\n'),
    }
    equivalent = [
        {"case": name, **pair_receipt(parser, grammar_sha, left, right, expect_same=True)}
        for name, (left, right) in equivalent_cases.items()
    ]

    postfix_reward_guards = []
    for name, source in {
        "cannot_be_silently_averaged_away": "rule brake cannot_be_silently_averaged_away\n",
    }.items():
        try:
            _, h = parse_canonical(parser, source, grammar_sha)
            postfix_reward_guards.append({"case": name, "semantic_hash": h, "pass": True, "error": None})
        except Exception as exc:
            postfix_reward_guards.append({"case": name, "semantic_hash": None, "pass": False, "error": str(exc)})

    optional_absence_sources = {
        "record_without_typeparams_or_defaults": "record X { a:Int }\n",
        "needle_without_params": "needle f()->Int\n",
        "record_without_field_defaults": "record X { a:Int; b:Ref }\n",
        "module_without_optional_grammar_elements": "module clay.demo\nlaw residual>=0\n",
    }
    optional_absence = []
    for name, source in optional_absence_sources.items():
        tree = parser.parse(source)
        none_count = count_none_children(tree)
        try:
            parse_canonical(parser, source, grammar_sha)
            canonical_ok = True
            error = None
        except CanonicalizationError as exc:
            canonical_ok = False
            error = str(exc)
        optional_absence.append({
            "case": name,
            "none_placeholder_count": none_count,
            "canonicalized": canonical_ok,
            "pass": none_count == 0 and canonical_ok,
            "error": error,
        })

    invalid_cases = {
        "unpaired_surrogate_rejected": 'rule label="\\ud800"\n',
    }
    invalid = []
    for name, source in invalid_cases.items():
        try:
            parse_canonical(parser, source, grammar_sha)
            row = {"case": name, "expected": "REJECT", "pass": False, "error": "unexpected_accept"}
        except CanonicalizationError as exc:
            row = {"case": name, "expected": "REJECT", "pass": True, "error": str(exc)}
        invalid.append(row)

    overall = (
        overall
        and all(x["pass"] for x in distinct)
        and all(x["pass"] for x in equivalent)
        and all(x["pass"] for x in postfix_reward_guards)
        and all(x["pass"] for x in optional_absence)
        and all(x["pass"] for x in invalid)
    )
    receipt = {
        "schema_version": "1.8",
        "experiment": "ClayCode BASE deterministic V18 grammar-bound syntax canonicalization with production-AST parity",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(grammar_path.relative_to(ROOT)) if grammar_path.is_relative_to(ROOT) else str(grammar_path),
        "grammar_sha256": grammar_sha,
        "canonical_schema": CANON_SCHEMA,
        "runtime": {
            "parser": "lark",
            "mode": "lalr/contextual",
            "strict": strict,
            "keep_all_tokens": True,
            "production_parser_constructor": "claycode_base_frontend.build_parser",
            "production_canonical_ast_constructor": "claycode_base_frontend.canonical_node",
            "maybe_placeholders": False,
        },
        "canonicalizer": "production frontend canonical AST -> grammar-bound sorted compact JSON envelope; standalone tool does not reinterpret parser nodes",
        "sources": rows,
        "semantic_surface_discrimination": distinct,
        "layout_equivalence": equivalent,
        "postfix_reward_guards": postfix_reward_guards,
        "optional_placeholder_absence": optional_absence,
        "invalid_semantic_values": invalid,
        "v17_trivia_counterexample_guard_present": True,
        "v18_reward_relation_guards_present": True,
        "grouping_equivalence_guard_present": True,
        "production_ast_single_authority": True,
        "string_escape_identity_guard_present": True,
        "optional_placeholder_absence_guard_present": True,
        "pass": overall,
        "scope_guard": "PASS proves deterministic selected-grammar layout/trivia, redundant-grouping, current reward-relation, decoded-string identity and production-parser absent-optional semantics for the listed admitted sources and regression/mutation pairs while sharing the production canonical-AST implementation. A relaxed-parser run is sandbox evidence only. This is CC-WP-02 evidence and does not prove typed IR/type/effect semantics (CC-WP-03/04) or substitute for Hostinger/Andreas target receipts.",
    }
    rendered = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not overall:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
