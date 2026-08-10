#!/usr/bin/env python3
"""Discriminate V7 / V16 / V17 ClayCode BASE grammar architecture.

Purpose
=======
Test the narrow fusion hypothesis that V16 can safely unify the current declarative
WP02 V17 surface with the typed-fn/operator surface still consumed by active typed IR
under V7. This is a research discriminator, not a grammar promotion.

Promotion is deliberately fail-closed. V16 is only SUPPORTABLE when it:
- constructs under strict LALR/contextual + interegular;
- accepts the exact admitted G9 + Dialect corpora;
- preserves V17 canonical frontend semantics for those declarative corpora;
- preserves V17 horizontal-trivia call/relation behavior;
- preserves V7 typed-fn + exact operator canonical semantics;
- preserves V7 active typed-IR identity on a typed-fn fixture;
- preserves V7/V16 active typed-IR identity for the admitted corpora;
- emits no synthetic None optional placeholders through the production frontend.

Strong counterhypothesis
========================
Separate grammar contracts are safer: V17 remains the declarative WP02 grammar and V7
(or another typed grammar) remains the typed/compiler grammar because V16 changes either
surface, fails strict construction, or changes active typed-IR identity.

No V18 is proposed by this test. A failure is evidence for split contracts or a more
specific falsifier, not permission to invent another grammar.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Tree

import claycode_base_frontend as front
import claycode_base_typed_ir as typed

ROOT = Path(__file__).resolve().parents[1]
V7 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
V16 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V16_GENERIC_DOTTED_LINEAR_LOOKAHEAD.lark"
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
CORPORA = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def count_none(node: Any) -> int:
    if node is None:
        return 1
    if isinstance(node, Tree):
        return sum(count_none(x) for x in node.children)
    return 0


def compile_row(source: str, grammar_text: str) -> dict[str, Any]:
    try:
        result = front.compile_frontend(source, grammar_text, strict=True)
        parser = front.build_parser(grammar_text, strict=True)
        tree = parser.parse(source)
        return {
            "accepted": True,
            "semantic_hash": result["semantic_hash"],
            "grammar_sha256": result["grammar_sha256"],
            "none_placeholder_count": count_none(tree),
            "error": None,
            "frontend": result,
        }
    except Exception as exc:
        return {
            "accepted": False,
            "semantic_hash": None,
            "grammar_sha256": hashlib.sha256(grammar_text.encode("utf-8")).hexdigest(),
            "none_placeholder_count": None,
            "error": f"{type(exc).__name__}: {exc}",
            "frontend": None,
        }


def strict_row(grammar_text: str) -> dict[str, Any]:
    try:
        front.build_parser(grammar_text, strict=True)
        return {"pass": True, "error": None}
    except Exception as exc:
        return {"pass": False, "error": f"{type(exc).__name__}: {exc}"}


def semantic_pair(source: str, left: str, right: str) -> dict[str, Any]:
    a = compile_row(source, left)
    b = compile_row(source, right)
    same = (
        a["accepted"]
        and b["accepted"]
        and a["semantic_hash"] == b["semantic_hash"]
        and a["none_placeholder_count"] == 0
        and b["none_placeholder_count"] == 0
    )
    return {
        "source": source,
        "left": {k: v for k, v in a.items() if k != "frontend"},
        "right": {k: v for k, v in b.items() if k != "frontend"},
        "same_semantics": same,
    }


def typed_ir_from_sources(named_sources: list[tuple[str, str]], grammar_text: str) -> dict[str, Any]:
    units: list[typed.SourceUnit] = []
    frontend_rows = []
    try:
        for name, source in named_sources:
            compiled = front.compile_frontend(source, grammar_text, strict=True)
            units.append(typed.SourceUnit(Path(name), compiled))
            frontend_rows.append({
                "name": name,
                "source_sha256": compiled["source_sha256"],
                "semantic_hash": compiled["semantic_hash"],
                "grammar_sha256": compiled["grammar_sha256"],
            })
        ir = typed.build_typed_ir(units)
        again = typed.build_typed_ir(units)
        deterministic = (
            ir["typed_ir_sha256"] == again["typed_ir_sha256"]
            and typed.canon_bytes(ir) == typed.canon_bytes(again)
        )
        functions = [
            {"name": x.get("name"), "params": x.get("params"), "returns": x.get("returns"), "body_tokens": x.get("body_tokens")}
            for x in ir.get("declarations", [])
            if x.get("kind") == "function"
        ]
        return {
            "accepted": True,
            "typed_ir_sha256": ir["typed_ir_sha256"],
            "program_semantic_id": ir["program_semantic_id"],
            "deterministic": deterministic,
            "functions": functions,
            "declaration_count": len(ir.get("declarations", [])),
            "type_count": len(ir.get("types", [])),
            "frontend_rows": frontend_rows,
            "error": None,
        }
    except Exception as exc:
        return {
            "accepted": False,
            "typed_ir_sha256": None,
            "program_semantic_id": None,
            "deterministic": False,
            "functions": [],
            "declaration_count": None,
            "type_count": None,
            "frontend_rows": frontend_rows,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    paths = {"v7": V7, "v16": V16, "v17": V17}
    grammars = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}
    identities = {name: {"path": str(path.relative_to(ROOT)), "git_content_sha256": sha(path)} for name, path in paths.items()}
    strict = {name: strict_row(text) for name, text in grammars.items()}

    corpus_rows = []
    v16_v17_corpus_equal = True
    v7_v16_corpus_equal = True
    for path in CORPORA:
        source = path.read_text(encoding="utf-8")
        rows = {name: compile_row(source, text) for name, text in grammars.items()}
        compact = {
            name: {k: v for k, v in row.items() if k != "frontend"}
            for name, row in rows.items()
        }
        eq_16_17 = (
            rows["v16"]["accepted"] and rows["v17"]["accepted"]
            and rows["v16"]["semantic_hash"] == rows["v17"]["semantic_hash"]
            and rows["v16"]["none_placeholder_count"] == rows["v17"]["none_placeholder_count"] == 0
        )
        eq_7_16 = (
            rows["v7"]["accepted"] and rows["v16"]["accepted"]
            and rows["v7"]["semantic_hash"] == rows["v16"]["semantic_hash"]
            and rows["v7"]["none_placeholder_count"] == rows["v16"]["none_placeholder_count"] == 0
        )
        v16_v17_corpus_equal &= eq_16_17
        v7_v16_corpus_equal &= eq_7_16
        corpus_rows.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "grammars": compact,
            "v16_equals_v17_frontend_semantics": eq_16_17,
            "v7_equals_v16_frontend_semantics": eq_7_16,
        })

    call_tight = "rule Needle.owns(X)\n"
    call_spaced = "rule Needle.owns (X)\n"
    call_long = "rule Needle.owns          (X)\n"
    prefix = "rule Needle.owns X\n"
    relation_rows = {}
    for name in ("v7", "v16", "v17"):
        g = grammars[name]
        tight = compile_row(call_tight, g)
        spaced = compile_row(call_spaced, g)
        long = compile_row(call_long, g)
        pref = compile_row(prefix, g)
        relation_rows[name] = {
            "tight": {k: v for k, v in tight.items() if k != "frontend"},
            "spaced": {k: v for k, v in spaced.items() if k != "frontend"},
            "long": {k: v for k, v in long.items() if k != "frontend"},
            "prefix": {k: v for k, v in pref.items() if k != "frontend"},
            "call_horizontal_trivia_equivalent": (
                tight["accepted"] and spaced["accepted"] and long["accepted"]
                and tight["semantic_hash"] == spaced["semantic_hash"] == long["semantic_hash"]
                and tight["none_placeholder_count"] == spaced["none_placeholder_count"] == long["none_placeholder_count"] == 0
            ),
            "call_distinct_from_prefix_relation": (
                tight["accepted"] and pref["accepted"] and tight["semantic_hash"] != pref["semantic_hash"]
            ),
        }

    typed_fn = "fn add(x:Int,y:Int)->Int=x+y\n"
    typed_fn_sub = "fn add(x:Int,y:Int)->Int=x-y\n"
    typed_front = {name: compile_row(typed_fn, text) for name, text in grammars.items()}
    typed_front_sub = {name: compile_row(typed_fn_sub, text) for name, text in grammars.items()}
    typed_front_compact = {
        name: {
            "add": {k: v for k, v in typed_front[name].items() if k != "frontend"},
            "sub": {k: v for k, v in typed_front_sub[name].items() if k != "frontend"},
        }
        for name in grammars
    }

    typed_fn_v7_v16_equal = (
        typed_front["v7"]["accepted"] and typed_front["v16"]["accepted"]
        and typed_front["v7"]["semantic_hash"] == typed_front["v16"]["semantic_hash"]
        and typed_front["v7"]["none_placeholder_count"] == typed_front["v16"]["none_placeholder_count"] == 0
    )
    operator_identity_v7 = (
        typed_front["v7"]["accepted"] and typed_front_sub["v7"]["accepted"]
        and typed_front["v7"]["semantic_hash"] != typed_front_sub["v7"]["semantic_hash"]
    )
    operator_identity_v16 = (
        typed_front["v16"]["accepted"] and typed_front_sub["v16"]["accepted"]
        and typed_front["v16"]["semantic_hash"] != typed_front_sub["v16"]["semantic_hash"]
    )
    v17_rejects_typed_fn = not typed_front["v17"]["accepted"]

    typed_fixture_units = [("typed_fn_fixture.clay", typed_fn)]
    typed_ir_fixture = {
        name: typed_ir_from_sources(typed_fixture_units, grammars[name])
        for name in ("v7", "v16", "v17")
    }
    typed_ir_v7_v16_equal = (
        typed_ir_fixture["v7"]["accepted"] and typed_ir_fixture["v16"]["accepted"]
        and typed_ir_fixture["v7"]["deterministic"] and typed_ir_fixture["v16"]["deterministic"]
        and typed_ir_fixture["v7"]["typed_ir_sha256"] == typed_ir_fixture["v16"]["typed_ir_sha256"]
        and bool(typed_ir_fixture["v7"]["functions"])
        and typed_ir_fixture["v7"]["functions"] == typed_ir_fixture["v16"]["functions"]
    )

    corpus_units = [(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8")) for path in CORPORA]
    typed_ir_corpora = {
        name: typed_ir_from_sources(corpus_units, grammars[name])
        for name in ("v7", "v16", "v17")
    }
    typed_ir_v7_v16_corpora_equal = (
        typed_ir_corpora["v7"]["accepted"] and typed_ir_corpora["v16"]["accepted"]
        and typed_ir_corpora["v7"]["deterministic"] and typed_ir_corpora["v16"]["deterministic"]
        and typed_ir_corpora["v7"]["typed_ir_sha256"] == typed_ir_corpora["v16"]["typed_ir_sha256"]
    )
    typed_ir_v16_v17_corpora_equal = (
        typed_ir_corpora["v16"]["accepted"] and typed_ir_corpora["v17"]["accepted"]
        and typed_ir_corpora["v16"]["deterministic"] and typed_ir_corpora["v17"]["deterministic"]
        and typed_ir_corpora["v16"]["typed_ir_sha256"] == typed_ir_corpora["v17"]["typed_ir_sha256"]
    )

    checks = {
        "v16_strict_lalr": strict["v16"]["pass"],
        "v16_v17_current_corpus_frontend_semantics_equal": v16_v17_corpus_equal,
        "v7_v16_current_corpus_frontend_semantics_equal": v7_v16_corpus_equal,
        "v16_call_horizontal_trivia_equivalent": relation_rows["v16"]["call_horizontal_trivia_equivalent"],
        "v16_call_distinct_from_prefix_relation": relation_rows["v16"]["call_distinct_from_prefix_relation"],
        "v17_call_horizontal_trivia_equivalent": relation_rows["v17"]["call_horizontal_trivia_equivalent"],
        "v7_counterexample_or_non_equivalence_observable": not relation_rows["v7"]["call_horizontal_trivia_equivalent"],
        "v7_v16_typed_fn_frontend_semantics_equal": typed_fn_v7_v16_equal,
        "v7_operator_identity_preserved": operator_identity_v7,
        "v16_operator_identity_preserved": operator_identity_v16,
        "v17_typed_fn_out_of_surface": v17_rejects_typed_fn,
        "v7_v16_typed_fn_active_typed_ir_equal": typed_ir_v7_v16_equal,
        "v7_v16_current_corpus_active_typed_ir_equal": typed_ir_v7_v16_corpora_equal,
        "v16_v17_current_corpus_active_typed_ir_equal": typed_ir_v16_v17_corpora_equal,
    }

    # V7 itself need not satisfy the repaired call-trivia contract; observing its failure
    # is useful baseline evidence. V16 support requires every declared fusion obligation.
    support_required = [
        "v16_strict_lalr",
        "v16_v17_current_corpus_frontend_semantics_equal",
        "v7_v16_current_corpus_frontend_semantics_equal",
        "v16_call_horizontal_trivia_equivalent",
        "v16_call_distinct_from_prefix_relation",
        "v17_call_horizontal_trivia_equivalent",
        "v7_v16_typed_fn_frontend_semantics_equal",
        "v7_operator_identity_preserved",
        "v16_operator_identity_preserved",
        "v17_typed_fn_out_of_surface",
        "v7_v16_typed_fn_active_typed_ir_equal",
        "v7_v16_current_corpus_active_typed_ir_equal",
        "v16_v17_current_corpus_active_typed_ir_equal",
    ]
    failed = [name for name in support_required if not checks[name]]
    v16_supported = not failed

    out = {
        "schema_version": "1.0",
        "experiment": "CC_BASE_V7_V16_V17_GRAMMAR_FUSION_DISCRIMINATOR",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "V16 can unify V17 declarative WP02 semantics with V7 typed-fn/operator semantics without changing active typed-IR identity on the tested surfaces.",
        "strongest_counterhypothesis": "Separate grammar contracts are safer because V16 changes at least one declarative, typed-fn/operator, strict-parser or active typed-IR invariant.",
        "runtime": {
            "python": __import__("platform").python_version(),
            "lark": package_version("lark"),
            "interegular": package_version("interegular"),
            "production_frontend_constructor": "claycode_base_frontend.build_parser",
            "maybe_placeholders": False,
            "active_typed_ir": "tools/claycode_base_typed_ir.py",
        },
        "grammars": identities,
        "strict": strict,
        "corpora": corpus_rows,
        "relation_boundary": relation_rows,
        "typed_fn_frontend": typed_front_compact,
        "typed_ir_fixture": typed_ir_fixture,
        "typed_ir_corpora": typed_ir_corpora,
        "checks": checks,
        "support_required": support_required,
        "failed_support_checks": failed,
        "v16_fusion_supported_on_tested_surfaces": v16_supported,
        "split_grammar_counterhypothesis_supported": not v16_supported,
        "promotion_allowed": False,
        "counts_as_wp02_pass": False,
        "counts_as_wp03_pass": False,
        "counts_as_andreas_target_acceptance": False,
        "architecture_delta": "CANDIDATE_ONLY" if v16_supported else "NO_CHANGE_SPLIT_GRAMMAR_REMAINS_SAFER",
        "next_falsifier": (
            "If V16 is supported here, run exact immutable Ubuntu differential compiler/type-effect/evaluator receipts before any grammar contract change."
            if v16_supported
            else "Localize the first failed support check; preserve split grammar contracts unless a smaller measured repair resolves it. Do not create V18 without a concrete executable counterexample."
        ),
        "scope_guard": "This discriminator compares parser/canonical/typed-IR semantics only. It cannot promote WP02/WP03, cannot authorize a grammar switch, and cannot replace downstream compiler/type-effect/evaluator or Andreas Ubuntu target evidence.",
        "authority_invariant": "model output != execution authority",
    }

    rendered = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({
        "v16_fusion_supported_on_tested_surfaces": v16_supported,
        "failed_support_checks": failed,
        "v7_call_trivia_equivalent": relation_rows["v7"]["call_horizontal_trivia_equivalent"],
        "v16_call_trivia_equivalent": relation_rows["v16"]["call_horizontal_trivia_equivalent"],
        "v17_call_trivia_equivalent": relation_rows["v17"]["call_horizontal_trivia_equivalent"],
    }, sort_keys=True))
    if args.output:
        print(str(args.output))
    return 0 if v16_supported else 2


if __name__ == "__main__":
    raise SystemExit(main())
