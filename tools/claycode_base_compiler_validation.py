#!/usr/bin/env python3
"""Executable validation for the ClayCode BASE pure-function compiler candidate."""
from __future__ import annotations

import importlib.util
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "tools/claycode_base_compiler.py"
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
OUT = ROOT / "research_entity/claycode/autonomous/BASE_TYPED_IR_EVAL_NATIVE_RECEIPT.json"

spec = importlib.util.spec_from_file_location("claycode_base_compiler", COMPILER)
cc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cc
assert spec.loader is not None
spec.loader.exec_module(cc)

BASE = """fn add(a:Int,b:Int)->Int=a+b
fn sub(a:Int,b:Int)->Int=a-b
fn mix(a:Int,b:Int)->Int=add(a,sub(a,b))
fn gt(a:Int,b:Int)->Bool=a>b
"""
VARIANT = """// formatting/comment/order variant
fn gt ( a : Int , b : Int ) -> Bool = a > b
fn mix(a:Int,b:Int)->Int=add(a,sub(a,b))
fn sub(a:Int,b:Int)->Int=a - b
fn add(a:Int,b:Int)->Int=a + b
"""

NEGATIVE = [
    ("undefined_function", "fn f(a:Int)->Int=nope(a)\n", "UNDEFINED_FUNCTION"),
    ("arity_mismatch", "fn g(a:Int)->Int=a\nfn f(a:Int)->Int=g(a,a)\n", "ARITY_MISMATCH"),
    ("return_type", "fn f(a:Int)->Bool=a+1\n", "RETURN_TYPE_MISMATCH"),
    ("argument_type", "fn g(a:Bool)->Bool=a\nfn f(a:Int)->Bool=g(a)\n", "ARG_TYPE_MISMATCH"),
    ("duplicate_function", "fn f(a:Int)->Int=a\nfn f(a:Int)->Int=a\n", "DUPLICATE_FUNCTION"),
]


def main() -> int:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    base = cc.build(BASE, grammar)
    variant = cc.build(VARIANT, grammar)
    failures = []

    semantic_equivalence = base["semantic_hash"] == variant["semantic_hash"]
    if not semantic_equivalence:
        failures.append("format_comment_order_semantic_equivalence")

    mutated = cc.build(BASE.replace("a-b", "a+b"), grammar)
    mutation_discriminated = mutated["semantic_hash"] != base["semantic_hash"]
    if not mutation_discriminated:
        failures.append("operator_mutation_discrimination")

    negatives = []
    for name, source, expected in NEGATIVE:
        try:
            cc.build(source, grammar)
            negatives.append({"case": name, "pass": False, "error": "unexpected_accept"})
            failures.append(f"negative:{name}")
        except cc.CompileError as exc:
            ok = expected in str(exc)
            negatives.append({"case": name, "pass": ok, "error": str(exc)})
            if not ok:
                failures.append(f"negative:{name}:wrong_error")

    ir = base["ir"]
    c_source = cc.lower_c(ir, "mix")
    random_cases = 1000
    mismatches = []
    compiler_identity = None
    binary_identity = None
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        c_path = temp / "program.c"
        exe = temp / "program"
        c_path.write_text(c_source, encoding="utf-8")
        subprocess.run(["gcc", "-O2", "-std=c11", "-Wall", "-Wextra", "-Werror", str(c_path), "-o", str(exe)], check=True)
        compiler_identity = subprocess.check_output(["gcc", "--version"], text=True).splitlines()[0]
        binary_identity = cc.sha256(exe.read_bytes())
        rng = random.Random(20260809)
        for index in range(random_cases):
            a = rng.randint(-100000, 100000)
            b = rng.randint(-100000, 100000)
            reference = cc.eval_function(ir, "mix", [a, b])
            observed = int(subprocess.check_output([str(exe), str(a), str(b)], text=True).strip())
            if reference != observed:
                mismatches.append({"case": index, "a": a, "b": b, "reference": reference, "observed": observed})
                if len(mismatches) >= 10:
                    break
    if mismatches:
        failures.append("native_differential")

    report = {
        "schema_version": "1.0",
        "scope": "INTEGRATED_PURE_FN_TYPED_IR_EVALUATOR_NATIVE_C_LOWERING_NOT_FULL_BASE",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "compiler": str(COMPILER.relative_to(ROOT)),
        "semantic_hash": base["semantic_hash"],
        "format_comment_function_order_semantic_equivalence": semantic_equivalence,
        "operator_mutation_discriminated": mutation_discriminated,
        "negative_type_binding_cases": negatives,
        "native_backend": {
            "target": "C11/GCC native host executable",
            "compiler_identity": compiler_identity,
            "generated_c_sha256": cc.sha256(c_source.encode("utf-8")),
            "binary_sha256": binary_identity,
            "random_differential_cases": random_cases,
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
        },
        "authority_boundary": "This slice is pure and has no effect/FFI primitive; therefore it cannot mint execution authority.",
        "work_package_evidence": {
            "CC-WP-03-IR-TYPES": "integrated candidate evidence",
            "CC-WP-04-TYPE-EFFECT": "pure typed subset only; external effect checker still open",
            "CC-WP-05-EVALUATOR": "integrated pure-function evaluator evidence",
            "CC-WP-06-COMPILER-LOWERING": "integrated C11/GCC lowering evidence",
        },
        "promotion": "NONE",
        "failures": failures,
        "pass": not failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "failures": failures, "out": str(OUT.relative_to(ROOT))}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
