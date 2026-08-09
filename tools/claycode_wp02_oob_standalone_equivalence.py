#!/usr/bin/env python3
"""Bounded GO out-of-box experiment: dynamic vs generated standalone V17 LALR parser.

This is evidence-only and never promotes ClayCode semantics by itself.  It asks whether
Lark's generated standalone LALR parser preserves the selected WP02 grammar's observed
accept/reject behavior and parse-tree identity on the admitted current corpus plus a small
boundary matrix around the V17 Needle.owns/Needle.lowers lookahead repair.

The experiment is deliberately reversible/lesionable: delete this script and its receipt.
It does not edit the grammar, canonicalizer, compiler, runtime or authority boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import tempfile
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
EXPERIMENT_ID = "GO-OOB-WP02-STANDALONE-PARSER-EQUIVALENCE-V1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canon(node: Any) -> Any:
    if isinstance(node, Tree):
        return ["tree", str(node.data), [canon(x) for x in node.children]]
    if isinstance(node, Token):
        return ["token", str(node.type), str(node)]
    return ["literal", str(node)]


def tree_hash(tree: Tree) -> str:
    payload = json.dumps(canon(tree), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def parse_one(parser: Any, text: str) -> dict[str, Any]:
    started = time.perf_counter_ns()
    try:
        tree = parser.parse(text)
    except Exception as exc:
        elapsed = time.perf_counter_ns() - started
        return {
            "accepted": False,
            "tree_sha256": None,
            "elapsed_ns": elapsed,
            "error_type": type(exc).__name__,
        }
    elapsed = time.perf_counter_ns() - started
    return {
        "accepted": True,
        "tree_sha256": tree_hash(tree),
        "elapsed_ns": elapsed,
        "error_type": None,
    }


def load_standalone(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("claycode_v17_standalone_generated", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("STANDALONE_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Lark_StandAlone()


def compare_case(name: str, text: str, dynamic: Any, standalone: Any, expected_accept: bool | None) -> dict[str, Any]:
    d1 = parse_one(dynamic, text)
    d2 = parse_one(dynamic, text)
    s1 = parse_one(standalone, text)
    s2 = parse_one(standalone, text)
    acceptance_equal = d1["accepted"] == s1["accepted"]
    dynamic_deterministic = d1["accepted"] == d2["accepted"] and d1["tree_sha256"] == d2["tree_sha256"]
    standalone_deterministic = s1["accepted"] == s2["accepted"] and s1["tree_sha256"] == s2["tree_sha256"]
    tree_equal = (not d1["accepted"] and not s1["accepted"]) or d1["tree_sha256"] == s1["tree_sha256"]
    expected_ok = expected_accept is None or d1["accepted"] == expected_accept == s1["accepted"]
    passed = acceptance_equal and dynamic_deterministic and standalone_deterministic and tree_equal and expected_ok
    return {
        "case": name,
        "source_sha256": sha256_bytes(text.encode("utf-8")),
        "expected_accept": expected_accept,
        "dynamic": d1,
        "dynamic_repeat": d2,
        "standalone": s1,
        "standalone_repeat": s2,
        "acceptance_equal": acceptance_equal,
        "tree_identity_equal": tree_equal,
        "dynamic_deterministic": dynamic_deterministic,
        "standalone_deterministic": standalone_deterministic,
        "expected_behavior_ok": expected_ok,
        "pass": passed,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    grammar = GRAMMAR.read_text(encoding="utf-8")
    dynamic = Lark(grammar, parser="lalr", lexer="contextual", strict=True, start="start")

    with tempfile.TemporaryDirectory(prefix="claycode-v17-standalone-") as td:
        generated = Path(td) / "v17_standalone.py"
        started = time.perf_counter_ns()
        with generated.open("wb") as out:
            cp = subprocess.run(
                [sys.executable, "-m", "lark.tools.standalone", str(GRAMMAR)],
                cwd=ROOT,
                stdout=out,
                stderr=subprocess.PIPE,
                check=False,
            )
        generation_elapsed_ns = time.perf_counter_ns() - started
        generation_stderr = cp.stderr.decode("utf-8", errors="replace")
        if cp.returncode != 0:
            receipt = {
                "schema_version": "1.0",
                "experiment_id": EXPERIMENT_ID,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "pass": False,
                "failure": "STANDALONE_GENERATION_FAILED",
                "generation_returncode": cp.returncode,
                "generation_stderr_sha256": sha256_bytes(cp.stderr),
                "generation_stderr_tail": generation_stderr[-2000:],
            }
            rendered = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
            print(rendered, end="")
            return 2

        generated_sha = sha256_path(generated)
        generated_size = generated.stat().st_size
        standalone = load_standalone(generated)

        cases: list[tuple[str, str, bool | None]] = []
        for path in SOURCES:
            cases.append((str(path.relative_to(ROOT)), path.read_text(encoding="utf-8"), True))

        cases.extend([
            ("call_tight", "rule Needle.owns(X)\n", True),
            ("call_space", "rule Needle.owns (X)\n", True),
            ("call_many_spaces", "rule Needle.owns          (X)\n", True),
            ("call_tab", "rule Needle.owns\t(X)\n", True),
            ("prefix_owns", "rule Needle.owns X\n", True),
            ("prefix_lowers", "rule Needle.lowers X\n", True),
            ("bare_owns", "rule 4B_need_not_learn Needle.owns\n", True),
            ("bare_lowers", "rule Needle.lowers\n", False),
            ("reserved_if_field", "record X { if:Int }\n", False),
            ("reserved_invariant_parameter", "needle f(invariant:Int)->Int\n", False),
            ("unicode_string", "rule f(\"Grüße 世界\")\n", True),
            ("newline_record", "record X {\n\n a:Int\n\n b:Int\n\n}\n", True),
        ])

        rows = [compare_case(name, text, dynamic, standalone, expected) for name, text, expected in cases]

        by_name = {row["case"]: row for row in rows}
        call_hashes = [
            by_name[name]["dynamic"]["tree_sha256"]
            for name in ["call_tight", "call_space", "call_many_spaces", "call_tab"]
        ]
        call_trivia_identity = len(set(call_hashes)) == 1
        relation_distinct = (
            by_name["call_tight"]["dynamic"]["tree_sha256"]
            != by_name["prefix_owns"]["dynamic"]["tree_sha256"]
        )
        passed = all(row["pass"] for row in rows) and call_trivia_identity and relation_distinct

        receipt = {
            "schema_version": "1.0",
            "experiment_id": EXPERIMENT_ID,
            "class": "BOUNDED_OUT_OF_BOX_DIFFERENTIAL",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hypothesis": "Generated standalone LALR execution preserves V17 observed behavior and tree identity for admitted corpus and boundary cases.",
            "counterhypothesis": "Standalone generation/runtime changes contextual-lexer or V17 lookahead behavior, producing an acceptance or tree-identity differential.",
            "grammar_path": str(GRAMMAR.relative_to(ROOT)),
            "grammar_sha256": sha256_path(GRAMMAR),
            "dynamic_runtime": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "lark_module": str(Path(sys.modules["lark"].__file__).resolve()),
                "parser": "lalr/contextual",
                "strict": True,
            },
            "standalone_generation": {
                "command": [sys.executable, "-m", "lark.tools.standalone", str(GRAMMAR)],
                "returncode": cp.returncode,
                "elapsed_ns": generation_elapsed_ns,
                "generated_sha256": generated_sha,
                "generated_size_bytes": generated_size,
                "stderr_sha256": sha256_bytes(cp.stderr),
            },
            "cases": rows,
            "call_horizontal_trivia_tree_identity": call_trivia_identity,
            "call_vs_prefix_relation_distinct": relation_distinct,
            "pass": passed,
            "promotion": "NONE",
            "rollback": "Delete this script/workflow/receipt; no grammar or runtime semantics are mutated.",
            "scope_guard": "Evidence-only GO experiment. PASS is additional WP02 translation/deployment evidence, not WP02/H1/H2/H3/BASE release authority. FAIL preserves V17 as unpromoted and requires the smallest discriminating repair.",
            "authority_invariant": "model output != execution authority",
        }

    rendered = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
