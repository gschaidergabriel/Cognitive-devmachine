#!/usr/bin/env python3
"""Replay the newest WP06 compiler hardening on current-main without conflating grammar authorities.

V17 is the contract-selected *declarative WP02* grammar. The current pure-function compiler
requires fn_decl and therefore uses the separately versioned V16 typed-fn executable slice,
which the Andreas target contract explicitly permits. This replay binds both identities in
one receipt and tests compiler behavior; it does not promote WP02/WP06/BASE or target status.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import random
import resource
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "tools/claycode_base_compiler.py"
TARGET_CONTRACT = ROOT / "research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json"
TYPED_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V16_GENERIC_DOTTED_LINEAR_LOOKAHEAD.lark"

spec = importlib.util.spec_from_file_location("claycode_base_compiler_wp06_replay", COMPILER)
cc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cc
assert spec.loader is not None
spec.loader.exec_module(cc)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def timed(name: str, fn: Callable[[], Any], rows: list[dict]) -> Any:
    before = resource.getrusage(resource.RUSAGE_SELF)
    start = time.perf_counter()
    try:
        value = fn()
    except Exception as exc:
        elapsed = time.perf_counter() - start
        after = resource.getrusage(resource.RUSAGE_SELF)
        rows.append({
            "test": name,
            "pass": False,
            "elapsed_ms": round(elapsed * 1000, 3),
            "user_cpu_ms": round((after.ru_utime - before.ru_utime) * 1000, 3),
            "system_cpu_ms": round((after.ru_stime - before.ru_stime) * 1000, 3),
            "error": f"{type(exc).__name__}:{exc}",
        })
        raise
    elapsed = time.perf_counter() - start
    after = resource.getrusage(resource.RUSAGE_SELF)
    rows.append({
        "test": name,
        "pass": True,
        "elapsed_ms": round(elapsed * 1000, 3),
        "user_cpu_ms": round((after.ru_utime - before.ru_utime) * 1000, 3),
        "system_cpu_ms": round((after.ru_stime - before.ru_stime) * 1000, 3),
    })
    return value


def gcc_identity() -> str:
    return subprocess.check_output(["gcc", "--version"], text=True).splitlines()[0]


def compile_c(c_source: str, entry_name: str | None, args: list[str] | None = None) -> str:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        c_path = d / "program.c"
        c_path.write_text(c_source, encoding="utf-8")
        if entry_name is None:
            obj = d / "program.o"
            subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-c", str(c_path), "-o", str(obj)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return sha256_file(obj)
        exe = d / "program"
        subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(c_path), "-o", str(exe)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return subprocess.check_output([str(exe), *(args or [])], text=True).rstrip("\n")


def make_chain_source(n: int) -> str:
    lines = ["fn f0(a:Int)->Int=a+1"]
    for i in range(1, n):
        lines.append(f"fn f{i}(a:Int)->Int=f{i-1}(a)+1")
    return "\n".join(lines) + "\n"


def make_manual_chain_ir(n: int) -> dict:
    functions = [{"name": "f0", "params": [{"name": "a", "type": "Int"}], "return": "Int", "body": {"k": "bin", "op": "+", "l": {"k": "name", "v": "a"}, "r": {"k": "num", "v": 1}}}]
    for i in range(1, n):
        functions.append({"name": f"f{i}", "params": [{"name": "a", "type": "Int"}], "return": "Int", "body": {"k": "bin", "op": "+", "l": {"k": "call", "f": f"f{i-1}", "a": [{"k": "name", "v": "a"}]}, "r": {"k": "num", "v": 1}}})
    return {"schema": "claycode.typed-ir.v0", "functions": functions}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    contract = json.loads(TARGET_CONTRACT.read_text(encoding="utf-8"))
    selected_rel = contract["wp02_parser_contract"]["selected_grammar_path"]
    selected = ROOT / selected_rel
    required_selected = "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
    if selected_rel != required_selected:
        raise SystemExit(f"WP02_SELECTED_GRAMMAR_DRIFT:{selected_rel}")
    separation = str(contract["wp02_parser_contract"].get("executable_slice_separation", ""))
    if "typed-fn" not in separation or "must not be relabeled as WP02" not in separation:
        raise SystemExit("EXECUTABLE_SLICE_SEPARATION_CONTRACT_MISSING")

    typed_text = TYPED_GRAMMAR.read_text(encoding="utf-8")
    rows: list[dict] = []
    failures: list[str] = []
    details: dict[str, Any] = {}

    def run(name: str, fn: Callable[[], Any]):
        try:
            value = timed(name, fn, rows)
            details[name] = value
            return value
        except Exception as exc:
            failures.append(f"{name}:{type(exc).__name__}:{exc}")
            return None

    # 1) Current typed grammar can still build/evaluate/lower the compiler's own surface.
    smoke_src = """fn add(a:Int,b:Int)->Int=a+b
fn gt(a:Int,b:Int)->Bool=a>b
fn echo(s:String)->String=s
fn half(x:Real)->Real=x/2.0
"""
    smoke = run("typed_slice_smoke_build", lambda: cc.build(smoke_src, typed_text))

    # 2) Host-stack deep-expression regression: 4000 operators for build/eval/lower.
    def deep_expr():
        n = 4000
        src = "fn deep(a:Int)->Int=a" + "+1" * n + "\n"
        built = cc.build(src, typed_text)
        observed = cc.eval_function(built["ir"], "deep", [0])
        if observed != n:
            raise AssertionError((observed, n))
        c_src = cc.lower_c(built["ir"], "deep")
        return {"operators": n, "reference": observed, "generated_c_sha256": sha256_bytes(c_src.encode("utf-8"))}
    run("deep_expression_4000_build_eval_lower", deep_expr)

    # 3) Native C deep-expression compile at the historical 2000-operator hardening point.
    def deep_native():
        n = 2000
        src = "fn deep(a:Int)->Int=a" + "+1" * n + "\n"
        built = cc.build(src, typed_text)
        c_src = cc.lower_c(built["ir"], "deep")
        observed = int(compile_c(c_src, "deep", ["0"]))
        if observed != n:
            raise AssertionError((observed, n))
        return {"operators": n, "native": observed}
    run("deep_expression_2000_native_werror", deep_native)

    # 4) Acyclic call-chain regression through source/parser/compiler/native C.
    def chain_native():
        n = 300
        built = cc.build(make_chain_source(n), typed_text)
        reference = cc.eval_function(built["ir"], f"f{n-1}", [0])
        c_src = cc.lower_c(built["ir"], f"f{n-1}")
        native = int(compile_c(c_src, f"f{n-1}", ["0"]))
        if reference != n or native != reference:
            raise AssertionError({"reference": reference, "native": native, "expected": n})
        return {"functions": n, "reference": reference, "native": native}
    run("acyclic_call_chain_300_source_eval_native", chain_native)

    # 5) 5000-function manual IR explicit-stack evaluation regression.
    def manual_chain():
        n = 5000
        ir = make_manual_chain_ir(n)
        observed = cc.eval_function(ir, f"f{n-1}", [0])
        if observed != n:
            raise AssertionError((observed, n))
        return {"functions": n, "reference": observed}
    run("acyclic_call_chain_5000_manual_ir_eval", manual_chain)

    # 6) No-entry object must survive -Werror -c without unused-static failures.
    def object_no_entry():
        built = cc.build("fn inc(a:Int)->Int=a+1\nfn twice(a:Int)->Int=inc(inc(a))\n", typed_text)
        c_src = cc.lower_c(built["ir"], None)
        return {"object_sha256": compile_c(c_src, None)}
    run("no_entry_object_werror", object_no_entry)

    # 7) Unicode String CLI/reference/native differential.
    def unicode_string():
        built = cc.build("fn echo(s:String)->String=s\n", typed_text)
        value = "Grüße🙂"
        reference = cc.eval_function(built["ir"], "echo", [value])
        native = compile_c(cc.lower_c(built["ir"], "echo"), "echo", [value])
        if native != reference:
            raise AssertionError({"reference": reference, "native": native})
        return {"value_sha256": sha256_bytes(value.encode("utf-8")), "utf8_bytes": len(value.encode("utf-8"))}
    run("unicode_string_cli_native_differential", unicode_string)

    # 8) Explicit NUL stays fail-closed at the documented const-char backend boundary.
    def nul_rejection():
        built = cc.build('fn nul()->String="a\\u0000b"\n', typed_text)
        try:
            cc.lower_c(built["ir"], "nul")
        except cc.CompileError as exc:
            if "C11_STRING_NUL_UNSUPPORTED" in str(exc):
                return {"expected_error": "C11_STRING_NUL_UNSUPPORTED"}
            raise
        raise AssertionError("NUL_WAS_SILENTLY_LOWERED")
    run("embedded_nul_explicit_rejection", nul_rejection)

    # 9) Composite typed evaluator/native differential: Int + Bool + Real entries.
    composite_src = """fn add(a:Int,b:Int)->Int=a+b
fn sub(a:Int,b:Int)->Int=a-b
fn combo(a:Int,b:Int)->Int=add(a,sub(a,b))
fn gt(a:Int,b:Int)->Bool=a>b
fn half(x:Real)->Real=x/2.0
"""
    def composite():
        built = cc.build(composite_src, typed_text)
        rng = random.Random(20260810)
        mismatches = []
        combo_c = cc.lower_c(built["ir"], "combo")
        gt_c = cc.lower_c(built["ir"], "gt")
        half_c = cc.lower_c(built["ir"], "half")
        # Compilation is intentionally repeated per invocation by compile_c; keep the bounded sample small.
        for i in range(12):
            a = rng.randint(-50000, 50000); b = rng.randint(-50000, 50000)
            ref = cc.eval_function(built["ir"], "combo", [a, b])
            nat = int(compile_c(combo_c, "combo", [str(a), str(b)]))
            if ref != nat: mismatches.append({"i": i, "entry": "combo", "ref": ref, "native": nat})
        for a, b in [(1, 2), (2, 1), (-1, -1), (0, -1)]:
            ref = cc.eval_function(built["ir"], "gt", [a, b])
            nat = bool(int(compile_c(gt_c, "gt", [str(a), str(b)])))
            if ref != nat: mismatches.append({"entry": "gt", "a": a, "b": b, "ref": ref, "native": nat})
        for x in [0.0, 1.5, -4.25, 1000.125]:
            ref = cc.eval_function(built["ir"], "half", [x])
            nat = float(compile_c(half_c, "half", [repr(x)]))
            if ref != nat: mismatches.append({"entry": "half", "x": x, "ref": ref, "native": nat})
        if mismatches:
            raise AssertionError(mismatches[:8])
        return {"cases": 20, "mismatch_count": 0}
    run("composite_evaluator_native_differential", composite)

    maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report = {
        "schema_version": "1.0",
        "receipt_id": "CC_WP06_CURRENT_MAIN_V17_CONTEXT_REPLAY_V1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "EXECUTABLE_CURRENT_MAIN_COMPILER_REGRESSION",
        "scope": "WP06_TYPED_FN_SLICE_REPLAY_BOUND_TO_SELECTED_WP02_CONTEXT_NOT_TARGET_ACCEPTANCE",
        "github_sha": os.environ.get("GITHUB_SHA", ""),
        "selected_wp02_grammar": {"path": selected_rel, "sha256": sha256_file(selected)},
        "typed_executable_slice": {"path": str(TYPED_GRAMMAR.relative_to(ROOT)), "sha256": sha256_file(TYPED_GRAMMAR)},
        "compiler": {"path": str(COMPILER.relative_to(ROOT)), "sha256": sha256_file(COMPILER)},
        "slice_separation_contract": separation,
        "host": {
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "gcc": gcc_identity(),
            "cpu_count": os.cpu_count(),
            "maxrss_kib_linux_semantics": maxrss,
        },
        "tests": rows,
        "details": details,
        "failures": failures,
        "pass": not failures,
        "promotion": "NONE",
        "authority_invariant": "model output != execution authority",
        "epistemic_limits": {
            "counts_as_wp02_pass": False,
            "counts_as_wp06_formal_pass": False,
            "counts_as_andreas_target_acceptance": False,
            "reason": "This is current-main regression evidence for the separately versioned typed-fn compiler slice. Formal promotion still requires the declared WP02 and target-host receipts."
        }
    }
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "tests": len(rows), "failures": failures, "selected_wp02_sha256": report["selected_wp02_grammar"]["sha256"], "typed_slice_sha256": report["typed_executable_slice"]["sha256"]}, ensure_ascii=False, sort_keys=True))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
