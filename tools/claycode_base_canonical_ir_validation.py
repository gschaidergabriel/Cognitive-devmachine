#!/usr/bin/env python3
"""Deterministic canonical-IR evidence gate for ClayCode BASE WP-02.

This validator is deliberately frontend-only. It binds the current V17 repaired LALR
surface to a deterministic JSON canonical representation, proves serialization roundtrip,
checks semantic mutation discrimination, and checks trivia-equivalent source pairs.
It does NOT claim typed-IR/type-effect/evaluator closure and does NOT by itself promote
CC-WP-02 to PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
SCHEMA = "claycode-canonical-parse-ir/1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def canonical_obj(node: Any) -> Any:
    """Create an order-preserving, location/trivia-free canonical JSON value."""
    if isinstance(node, Tree):
        children = [canonical_obj(child) for child in node.children]
        return {"node": str(node.data), "children": [x for x in children if x is not None]}
    if isinstance(node, Token):
        if node.type == "NEWLINE":
            return None
        return {"token": node.type, "value": str(node)}
    if node is None:
        return None
    raise TypeError(f"unsupported parse value: {type(node)!r}")


def canonical_bytes(tree: Tree) -> bytes:
    return json.dumps(
        {"schema": SCHEMA, "root": canonical_obj(tree)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_hash(parser: Lark, source: str) -> tuple[str, bytes]:
    payload = canonical_bytes(parser.parse(source))
    return sha256_bytes(payload), payload


def stable_roundtrip(payload: bytes) -> bool:
    decoded = json.loads(payload.decode("utf-8"))
    encoded = json.dumps(decoded, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return payload == encoded


def pair(parser: Lark, left: str, right: str, expect_same: bool) -> dict[str, Any]:
    lh, lp = canonical_hash(parser, left)
    rh, rp = canonical_hash(parser, right)
    same = lh == rh
    return {
        "left_hash": lh,
        "right_hash": rh,
        "expected_same": expect_same,
        "observed_same": same,
        "left_roundtrip": stable_roundtrip(lp),
        "right_roundtrip": stable_roundtrip(rp),
        "pass": same == expect_same and stable_roundtrip(lp) and stable_roundtrip(rp),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output")
    args = ap.parse_args()

    wall0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    parser = Lark(
        grammar_text,
        parser="lalr",
        lexer="contextual",
        strict=True,
        start="start",
        keep_all_tokens=True,
        maybe_placeholders=False,
        propagate_positions=False,
    )

    source_results = []
    for path in SOURCES:
        source = path.read_text(encoding="utf-8")
        h1, p1 = canonical_hash(parser, source)
        h2, p2 = canonical_hash(parser, source)
        source_results.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha256_bytes(source.encode("utf-8")),
            "canonical_sha256": h1,
            "repeat_canonical_sha256": h2,
            "deterministic_repeat": h1 == h2 and p1 == p2,
            "json_roundtrip_stable": stable_roundtrip(p1),
            "canonical_bytes": len(p1),
        })

    mutation_pairs = {
        "greater_vs_less": ("rule x>0\n", "rule x<0\n"),
        "true_vs_false": ("rule true\n", "rule false\n"),
        "call_argument_order": ("rule f(a,b)\n", "rule f(b,a)\n"),
        "dotted_relation_kind": ("rule Needle.owns X\n", "rule Needle.lowers X\n"),
        "field_type": ("record X { a:Int }\n", "record X { a:String }\n"),
    }
    mutation = [
        {"case": name, **pair(parser, left, right, False)}
        for name, (left, right) in mutation_pairs.items()
    ]

    trivia_pairs = {
        "horizontal_space_comment": ("rule x>0\n", "rule   x > 0   // comment\n"),
        "blank_lines": ("record X {\n a:Int\n b:Int\n}\n", "record X {\n\n a:Int\n\n b:Int\n\n}\n"),
        "qualified_call_space": ("rule Needle.owns(X)\n", "rule Needle.owns (X)\n"),
        "qualified_call_tab": ("rule Needle.owns(X)\n", "rule Needle.owns\t(X)\n"),
        "dotted_rhs_tab": ("rule Needle.owns X\n", "rule Needle.owns\tX\n"),
    }
    trivia = [
        {"case": name, **pair(parser, left, right, True)}
        for name, (left, right) in trivia_pairs.items()
    ]

    passed = (
        all(row["deterministic_repeat"] and row["json_roundtrip_stable"] for row in source_results)
        and all(row["pass"] for row in mutation)
        and all(row["pass"] for row in trivia)
    )
    result = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE WP02 deterministic canonical IR/hash validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_schema": SCHEMA,
        "grammar_path": str(GRAMMAR.relative_to(ROOT)),
        "grammar_sha256": sha256_bytes(grammar_text.encode("utf-8")),
        "runtime": {
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "pid": os.getpid(),
            "lark_version": package_version("lark"),
            "interegular_version": package_version("interegular"),
        },
        "sources": source_results,
        "semantic_mutation_discrimination": mutation,
        "trivia_equivalence": trivia,
        "timing": {"wall_ns": time.perf_counter_ns() - wall0, "cpu_ns": time.process_time_ns() - cpu0},
        "pass": passed,
        "scope_guard": (
            "PASS proves deterministic current-V17 parse-derived canonical serialization, JSON roundtrip, selected semantic mutation discrimination, selected trivia invariance, and full-current G9/Dialect coverage on this runtime. It does not prove typed IR, type/effect semantics, evaluator/lowering, Frank handoff, or final Andreas-target acceptance."
        ),
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
