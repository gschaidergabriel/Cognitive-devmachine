#!/usr/bin/env python3
"""Deterministic property/mutation/differential suite for ClayCode BASE.

The suite attacks the current V7 pure compiler slice and host authority runtime. It is
not a substitute for target-host/application conformance, but it creates the production
oracle machinery required by CC-WP-11 and refuses the known failure mode where hashes
alone bless a semantically wrong lowering.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from claycode_base_pure_toolchain import ClayError, TypeFailure, compile_source, differential, evaluate
from claycode_base_runtime import CapabilityFault, ClayRuntime, VersionedCell

OUT = ROOT / "research_entity/claycode/autonomous/WP11_FUZZ_CONFORMANCE_RECEIPT.json"
SEED = 0xC1A7C0DE


def int_program(op: str) -> str:
    return f"module fuzz.int\nfn f(a:Int,b:Int)->Int=a{op}b\n"


def bool_program(op: str) -> str:
    return f"module fuzz.bool\nfn f(a:Int,b:Int)->Bool=a{op}b\n"


def main() -> int:
    rng = random.Random(SEED)
    checks: list[dict] = []
    failures: list[str] = []

    def record(name: str, ok: bool, detail=None):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})
        if not ok:
            failures.append(name)

    # 1) Native differential oracle: source -> typed IR interpreter vs independently
    # compiled C11 execution. This is the mandatory antidote to self-consistent bad hashes.
    native_rows = []
    arithmetic_ops = ["+", "-", "*"]
    compare_ops = [">", "<", ">=", "<=", "==", "!="]
    for i in range(72):
        if i % 3:
            op = rng.choice(arithmetic_ops)
            source = int_program(op)
        else:
            op = rng.choice(compare_ops)
            source = bool_program(op)
        a = rng.randint(-1000, 1000)
        b = rng.randint(-1000, 1000)
        typed = compile_source(source)
        row = differential(typed, "f", [a, b])
        native_rows.append({"operator": op, "a": a, "b": b, "match": bool(row["match"]), "semantic_hash": typed["semantic_hash"], "generated_c_sha256": row["generated_c_sha256"]})
    record("native_differential_72", all(x["match"] for x in native_rows), {"cases": len(native_rows), "mismatches": sum(not x["match"] for x in native_rows)})

    # 2) Operator mutation discrimination: semantic hashes and observable values must not
    # collapse for carefully chosen discriminating inputs.
    mutation_pairs = [
        ("+", "-", [7, 3]),
        ("+", "*", [7, 3]),
        (">", "<", [7, 3]),
        (">=", "<=", [7, 3]),
        ("==", "!=", [7, 3]),
    ]
    mutation_rows = []
    for left_op, right_op, args in mutation_pairs:
        left_src = int_program(left_op) if left_op in arithmetic_ops else bool_program(left_op)
        right_src = int_program(right_op) if right_op in arithmetic_ops else bool_program(right_op)
        left = compile_source(left_src)
        right = compile_source(right_src)
        lv = evaluate(left, "f", args)
        rv = evaluate(right, "f", args)
        ok = left["semantic_hash"] != right["semantic_hash"] and lv != rv
        mutation_rows.append({"left": left_op, "right": right_op, "hash_distinct": left["semantic_hash"] != right["semantic_hash"], "value_distinct": lv != rv, "pass": ok})
    record("operator_mutation_discrimination", all(x["pass"] for x in mutation_rows), mutation_rows)

    # 3) Determinism: identical source repeatedly produces identical typed semantic hash.
    deterministic_source = "module fuzz.det\nfn f(a:Int,b:Int)->Int=a*b+a-b\n"
    hashes = [compile_source(deterministic_source)["semantic_hash"] for _ in range(32)]
    record("typed_ir_hash_repeat_determinism", len(set(hashes)) == 1, {"runs": 32, "unique_hashes": len(set(hashes))})

    # 4) Negative type/symbol/arity corpus must fail closed.
    negatives = {
        "return_type": "module fuzz.bad\nfn f(a:Int)->Bool=a+1\n",
        "unknown_symbol": "module fuzz.bad\nfn f(a:Int)->Int=a+missing\n",
        "arg_type": "module fuzz.bad\nfn g(a:Int)->Int=a+1\nfn f(a:Bool)->Int=g(a)\n",
        "arity": "module fuzz.bad\nfn g(a:Int,b:Int)->Int=a+b\nfn f(a:Int)->Int=g(a)\n",
    }
    negative_rows = []
    for name, source in negatives.items():
        rejected = False
        error = None
        try:
            compile_source(source)
        except ClayError as exc:
            rejected = True
            error = f"{type(exc).__name__}:{exc}"
        negative_rows.append({"case": name, "rejected": rejected, "error": error})
    record("negative_type_symbol_arity_fail_closed", all(x["rejected"] for x in negative_rows), negative_rows)

    # 5) Runtime authority mutation: text/cross-runtime/stale/revoked handles cannot become
    # authority. This is separate from compiler expressibility.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="wp11_rt_") as td:
        rt = ClayRuntime(td)
        cap = rt.mint_capability("fs.write")
        unauthorized_accepts = 0
        attacks = []
        for attack_name, value in [
            ("text", "fs.write"),
            ("dict", {"kind": "fs.write"}),
            ("none", None),
        ]:
            try:
                rt.invoke("fs.write_text", value, "x.txt", "bad")
                unauthorized_accepts += 1
                attacks.append({"attack": attack_name, "rejected": False})
            except CapabilityFault:
                attacks.append({"attack": attack_name, "rejected": True})
        rt.revoke(cap)
        try:
            rt.invoke("fs.write_text", cap, "x.txt", "bad")
            unauthorized_accepts += 1
            attacks.append({"attack": "revoked", "rejected": False})
        except CapabilityFault:
            attacks.append({"attack": "revoked", "rejected": True})
        record("runtime_authority_mutations_fail_closed", unauthorized_accepts == 0, {"unauthorized_accepts": unauthorized_accepts, "attacks": attacks})

    # 6) ABA property over randomized round trips: a stale generation can never write.
    aba_failures = 0
    for i in range(256):
        a = rng.randint(-9999, 9999)
        b = rng.randint(-9999, 9999)
        cell = VersionedCell(a)
        v0, _ = cell.snapshot()
        ok1, v1, _ = cell.compare_and_swap(v0, b)
        ok2, v2, _ = cell.compare_and_swap(v1, a)
        stale, observed_v, observed = cell.compare_and_swap(v0, rng.randint(-9999, 9999))
        if not (ok1 and ok2 and not stale and observed_v == v2 and observed == a):
            aba_failures += 1
    record("cas_aba_property_256", aba_failures == 0, {"cases": 256, "failures": aba_failures})

    report = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE WP11 deterministic fuzz/conformance/differential suite",
        "seed": SEED,
        "evidence_class": "HOSTED_OR_LOCAL_CONFORMANCE_NOT_FULL_TARGET_APPLICATION_ACCEPTANCE",
        "counts_as_target_acceptance": False,
        "counts_as_full_wp11_pass": False,
        "known_gate_dependency": "final WP11 promotion additionally requires production application/runtime target receipts and full frozen-language corpus",
        "checks": checks,
        "native_differential_rows": native_rows,
        "failures": failures,
        "pass": not failures,
        "oracle_policy": "semantic/effect differential observations outrank self-consistent provenance/hash chains",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "checks": len(checks), "failures": failures, "native_cases": len(native_rows)}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
