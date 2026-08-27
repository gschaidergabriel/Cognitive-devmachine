#!/usr/bin/env python3
"""Causal differential for the two independent CC-WP-03 blockers.

This research validator binds the V7 typed-fn surface to the selected V17 relation membrane,
then compares current-main typed IR against the existing AST-context keyword-identifier
candidate supplied as an explicit file. It never edits production selection or work-package
status.

PASS requires:
1. strict LALR construction of the research grammar with interegular present;
2. strict full G9 + Dialect parsing;
3. exact relation/call/bare-qid boundary behavior;
4. compact subtraction remains distinct from addition;
5. current-main typed IR reproduces the known grammar/IR mismatch on `status` identifiers;
6. candidate typed IR preserves `status` across declaration/field/function/parameter/interface/method positions;
7. candidate typed IR compiles full G9 + Dialect deterministically under the same exact grammar.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import resource
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import claycode_base_frontend as front  # noqa: E402
import claycode_base_typed_ir as main_tir  # noqa: E402

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_RESEARCH_V7_TYPED_FN_V17_RELATION_MEMBRANE.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"

KEYWORD_FIXTURE = (
    "record status {\n status:Symbol\n}\n"
    "fn status(status:Symbol)->Symbol=status\n"
    "interface status {\n status(status:Symbol)->Symbol\n}\n"
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("claycode_tir_candidate_external", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def compile_text(tir, text: str, name: str, grammar: Path):
    with tempfile.TemporaryDirectory(prefix="clay-wp03-diff-") as td:
        p = Path(td) / name
        p.write_text(text, encoding="utf-8")
        return tir.compile_sources([p], grammar)


def keyword_shape(program: dict) -> dict:
    decls = program.get("declarations", [])
    record = next((x for x in decls if x.get("kind") == "record"), None)
    fn = next((x for x in decls if x.get("kind") == "function"), None)
    interface = next((x for x in decls if x.get("kind") == "interface"), None)
    return {"record": record, "function": fn, "interface": interface}


def candidate_keyword_ok(shape: dict) -> bool:
    r = shape.get("record") or {}
    f = shape.get("function") or {}
    i = shape.get("interface") or {}
    return (
        r.get("name") == "status"
        and r.get("fields") == [{"name": "status", "type": "Symbol", "default_tokens": None}]
        and f.get("name") == "status"
        and f.get("params") == [{"name": "status", "type": "Symbol"}]
        and i.get("name") == "status"
        and i.get("methods") == [{"name": "status", "params": [{"name": "status", "type": "Symbol"}], "returns": "Symbol"}]
    )


def parse_case(parser, source: str, expected: bool) -> dict:
    try:
        tree = parser.parse(source)
        return {"source": source, "accepted": True, "expected": expected, "pass": expected, "tree_hash": sha(tree.pretty().encode())}
    except Exception as exc:
        return {"source": source, "accepted": False, "expected": expected, "pass": not expected, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--typed-ir-candidate", type=Path, required=True)
    args = ap.parse_args()

    candidate_tir = load_module(args.typed_ir_candidate)
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    t0 = time.perf_counter()
    parser = front.build_parser(grammar_text, strict=True)
    strict_build_ms = (time.perf_counter() - t0) * 1000

    full_source_rows = []
    for path in (G9, DIALECT):
        text = path.read_text(encoding="utf-8")
        a = front.compile_frontend(text, grammar_text, strict=True)
        b = front.compile_frontend(text, grammar_text, strict=True)
        full_source_rows.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha(text.encode()),
            "semantic_hash": a["semantic_hash"],
            "repeat_semantic_hash": b["semantic_hash"],
            "deterministic": a["semantic_hash"] == b["semantic_hash"],
        })

    boundary_accept = [
        "rule Needle.owns(X)\n",
        "rule Needle.owns (X)\n",
        "rule Needle.owns\t(X)\n",
        "rule Needle.owns X\n",
        "rule Needle.owns\tX\n",
        "rule Needle.lowers X\n",
        "rule Needle.lowers\tX\n",
        "rule 4B_need_not_learn Needle.owns\n",
        "rule Needle.owns   \n",
    ]
    boundary_reject = [
        "rule Needle.lowers\n",
        "rule Needle.lowers (X)\n",
        "rule Needle.lowers\t(X)\n",
    ]
    boundaries = [parse_case(parser, x, True) for x in boundary_accept]
    boundaries += [parse_case(parser, x, False) for x in boundary_reject]

    add = front.compile_frontend("fn f(x:Int,y:Int)->Int=x+y\n", grammar_text, strict=True)
    sub = front.compile_frontend("fn f(x:Int,y:Int)->Int=x-y\n", grammar_text, strict=True)
    operator_discriminated = add["semantic_hash"] != sub["semantic_hash"]

    main_error = None
    main_keyword_shape = None
    try:
        main_kw = compile_text(main_tir, KEYWORD_FIXTURE, "keyword.clay", GRAMMAR)
        main_keyword_shape = keyword_shape(main_kw)
    except Exception as exc:
        main_error = f"{type(exc).__name__}: {exc}"
    main_bug_reproduced = main_error is not None or not candidate_keyword_ok(main_keyword_shape or {})

    candidate_kw = compile_text(candidate_tir, KEYWORD_FIXTURE, "keyword.clay", GRAMMAR)
    candidate_shape = keyword_shape(candidate_kw)
    keyword_fix_pass = candidate_keyword_ok(candidate_shape)

    full_candidate_a = candidate_tir.compile_sources([G9, DIALECT], GRAMMAR)
    full_candidate_b = candidate_tir.compile_sources([G9, DIALECT], GRAMMAR)
    full_candidate_deterministic = (
        full_candidate_a["program_semantic_id"] == full_candidate_b["program_semantic_id"]
        and candidate_tir.canon_bytes(full_candidate_a) == candidate_tir.canon_bytes(full_candidate_b)
    )

    passed = (
        all(x["deterministic"] for x in full_source_rows)
        and all(x["pass"] for x in boundaries)
        and operator_discriminated
        and main_bug_reproduced
        and keyword_fix_pass
        and bool(full_candidate_a.get("declarations"))
        and full_candidate_deterministic
    )

    out = {
        "schema_version": "1.0",
        "experiment": "WP03 V7 typed-fn plus V17 relation membrane / typed-IR causal differential",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "EXECUTABLE_RESEARCH_DIFFERENTIAL",
        "runtime": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "strict_build_ms": strict_build_ms,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "inputs": {
            "grammar_path": str(GRAMMAR.relative_to(ROOT)),
            "grammar_sha256": sha(grammar_text.encode()),
            "main_typed_ir_path": "tools/claycode_base_typed_ir.py",
            "main_typed_ir_sha256": sha((ROOT / "tools/claycode_base_typed_ir.py").read_bytes()),
            "candidate_typed_ir_path": str(args.typed_ir_candidate),
            "candidate_typed_ir_sha256": sha(args.typed_ir_candidate.read_bytes()),
        },
        "strict_full_sources": full_source_rows,
        "relation_boundary": boundaries,
        "operator_identity": {
            "add_semantic_hash": add["semantic_hash"],
            "sub_semantic_hash": sub["semantic_hash"],
            "discriminated": operator_discriminated,
        },
        "main_typed_ir_baseline": {
            "known_bug_reproduced": main_bug_reproduced,
            "error": main_error,
            "keyword_shape_if_any": main_keyword_shape,
        },
        "candidate_typed_ir": {
            "keyword_fixture_pass": keyword_fix_pass,
            "keyword_shape": candidate_shape,
            "full_program_semantic_id": full_candidate_a["program_semantic_id"],
            "full_frozen_sources_deterministic": full_candidate_deterministic,
            "declaration_count": len(full_candidate_a.get("declarations", [])),
        },
        "pass": passed,
        "promotion": "NONE",
        "architecture_delta": "SUPPORTED_COMPOSED_RESEARCH_CANDIDATE" if passed else "REFUTED_OR_INCOMPLETE_KEEP_EXISTING_SELECTIONS",
        "scope_guard": "PASS supports only the composed WP03 research path on exact tested bytes. V17 remains the selected WP02 frontend; this does not close WP03/WP04/BASE, merge the typed-IR PR, prove effect semantics, alter Frank Harness authority, or replace registered Andreas Ubuntu acceptance.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
