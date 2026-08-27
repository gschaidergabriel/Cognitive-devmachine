#!/usr/bin/env python3
"""Post-commit held-out corpus for ClayCode BASE (CC-WP-11/12 evidence).

A fresh cryptographic seed is generated at execution time unless supplied explicitly.
The compiler checkout therefore exists before exact test cases are known. The receipt
reveals the seed afterwards for reproducibility and records compiler/source hashes.
This is evidence only: it never marks a release work package PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from claycode_base_pure_toolchain import (  # noqa: E402
    ClayError,
    TypeFailure,
    Unsupported,
    compile_source,
    differential,
)

OUT = ROOT / "research_entity/claycode/autonomous/WP12_HELDOUT_CORPUS_RECEIPT.json"
TOOLCHAIN = ROOT / "tools/claycode_base_pure_toolchain.py"
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def positive_case(rng: random.Random, i: int) -> tuple[str, str, list[int]]:
    a = rng.randint(-25, 25)
    b = rng.randint(-25, 25)
    k = rng.randint(1, 9)
    template = rng.randrange(6)
    module = f"heldout.p{i}"
    if template == 0:
        src = f"module {module}\nfn f(a:Int,b:Int)->Int=a+{k}*b\n"
        return src, "f", [a, b]
    if template == 1:
        src = f"module {module}\nfn helper(x:Int)->Int=x*{k}\nfn f(a:Int,b:Int)->Int=helper(a)-b\n"
        return src, "f", [a, b]
    if template == 2:
        src = f"module {module}\nfn f(a:Int,b:Int)->Bool=a+{k}>b\n"
        return src, "f", [a, b]
    if template == 3:
        src = f"module {module}\nfn left(a:Int,b:Int)->Int=a-b\nfn f(a:Int,b:Int)->Int=left(a,b)+{k}\n"
        return src, "f", [a, b]
    if template == 4:
        src = f"module {module}\nfn f(a:Int,b:Int)->Bool=a==b+{k}\n"
        return src, "f", [a, b]
    src = f"module {module}\nfn f(a:Int,b:Int)->Int=(a*{k})+(b*2)\n"
    return src, "f", [a, b]


def negative_case(rng: random.Random, i: int) -> tuple[str, str]:
    k = rng.randrange(8)
    module = f"heldout.n{i}"
    cases = [
        (f"module {module}\nfn bad(a:Int,b:Bool)->Int=a+b\n", "numeric_bool_mismatch"),
        (f"module {module}\nfn bad(a:Bool,b:Int)->Bool=a>b\n", "ordered_bool_mismatch"),
        (f"module {module}\nfn bad(a:Int,b:Bool)->Bool=a&&b\n", "logical_int_mismatch"),
        (f"module {module}\nfn bad(a:Int)->Bool=a+1\n", "return_type_mismatch"),
        (f"module {module}\nfn bad(a:Int)->Int=missing(a)\n", "unknown_function"),
        (f"module {module}\nfn f(a:Int)->Int=a\nfn bad(a:Int)->Int=f(a,a)\n", "arity_mismatch"),
        (f"module {module}\nfn f(a:Int,a:Int)->Int=a\n", "duplicate_parameter"),
        (f"module {module}\nfn f(a:Int)->Int=a\nfn f(a:Int)->Int=a+1\n", "duplicate_function"),
    ]
    return cases[k]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", help="hex seed; omitted = fresh cryptographic seed")
    ap.add_argument("--positive", type=int, default=96)
    ap.add_argument("--negative", type=int, default=64)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    if args.positive < 1 or args.negative < 1:
        raise SystemExit("positive/negative counts must be >0")
    seed_hex = args.seed or secrets.token_hex(32)
    try:
        seed_int = int(seed_hex, 16)
    except ValueError as exc:
        raise SystemExit("--seed must be hexadecimal") from exc
    rng = random.Random(seed_int)

    positive_rows = []
    positive_failures = []
    for i in range(args.positive):
        src, entry, argv = positive_case(rng, i)
        row = {"id": f"P{i:04d}", "source_sha256": sha(src.encode()), "source": src, "entry": entry, "args": argv}
        try:
            typed = compile_source(src)
            diff = differential(typed, entry, argv)
            row.update({
                "semantic_hash": typed["semantic_hash"],
                "generated_c_sha256": diff["generated_c_sha256"],
                "interpreter_result": diff["interpreter_result"],
                "native_stdout": diff["native_stdout"],
                "pass": bool(diff["match"]),
            })
        except Exception as exc:
            row.update({"pass": False, "error": f"{type(exc).__name__}: {exc}"})
        if not row["pass"]:
            positive_failures.append(row["id"])
        positive_rows.append(row)

    negative_rows = []
    negative_failures = []
    for i in range(args.negative):
        src, category = negative_case(rng, i)
        row = {"id": f"N{i:04d}", "category": category, "source_sha256": sha(src.encode()), "source": src}
        try:
            compile_source(src)
            row.update({"pass": False, "error": "unexpected_accept"})
        except TypeFailure as exc:
            row.update({"pass": True, "rejected_as": "TypeFailure", "message": str(exc)})
        except (Unsupported, ClayError) as exc:
            # A type-negative program must reach the type/effect checker. Rejection by a
            # smaller parser/subset is not credited as a typed negative-corpus PASS.
            row.update({"pass": False, "rejected_as": type(exc).__name__, "message": str(exc)})
        except Exception as exc:
            row.update({"pass": False, "rejected_as": type(exc).__name__, "message": str(exc)})
        if not row["pass"]:
            negative_failures.append(row["id"])
        negative_rows.append(row)

    # Metamorphic operator-identity oracle independent of concrete result values.
    mutation_rows = []
    for i in range(24):
        lhs = rng.randint(-9, 9)
        rhs = rng.randint(-9, 9)
        add_src = f"module heldout.m{i}.add\nfn f(a:Int,b:Int)->Int=a+b\n"
        sub_src = f"module heldout.m{i}.sub\nfn f(a:Int,b:Int)->Int=a-b\n"
        try:
            add = compile_source(add_src)
            sub = compile_source(sub_src)
            distinct = add["semantic_hash"] != sub["semantic_hash"]
            da = differential(add, "f", [lhs, rhs])
            ds = differential(sub, "f", [lhs, rhs])
            mutation_rows.append({
                "id": f"M{i:04d}",
                "add_source_sha256": sha(add_src.encode()),
                "sub_source_sha256": sha(sub_src.encode()),
                "semantic_hash_distinct": distinct,
                "both_native_match": bool(da["match"] and ds["match"]),
                "pass": bool(distinct and da["match"] and ds["match"]),
            })
        except Exception as exc:
            mutation_rows.append({"id": f"M{i:04d}", "pass": False, "error": f"{type(exc).__name__}: {exc}"})

    mutation_failures = [x["id"] for x in mutation_rows if not x["pass"]]
    overall = not positive_failures and not negative_failures and not mutation_failures
    receipt = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE post-commit heldout differential/type-negative corpus",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed_revealed_after_execution": seed_hex,
        "seed_sha256": sha(bytes.fromhex(seed_hex)),
        "anti_leak_design": "fresh seed generated by test runner after compiler checkout; seed revealed only in resulting receipt",
        "toolchain_sha256": sha(TOOLCHAIN.read_bytes()),
        "grammar_sha256": sha(GRAMMAR.read_bytes()),
        "positive": positive_rows,
        "negative": negative_rows,
        "mutations": mutation_rows,
        "summary": {
            "positive_passed": len(positive_rows) - len(positive_failures),
            "positive_total": len(positive_rows),
            "negative_passed": len(negative_rows) - len(negative_failures),
            "negative_total": len(negative_rows),
            "mutation_passed": len(mutation_rows) - len(mutation_failures),
            "mutation_total": len(mutation_rows),
            "failures": positive_failures + negative_failures + mutation_failures,
            "pass": overall,
        },
        "evidence_class": "POST_COMMIT_HELDOUT_HOSTED_LINUX_NOT_ANDREAS_TARGET_ACCEPTANCE",
        "supports": ["CC-WP-11-FUZZ-CONFORMANCE", "CC-WP-12-CORPUS-HELDOUT"],
        "counts_as_work_package_pass": False,
        "counts_as_target_acceptance": False,
        "promotion": "NONE_AUTOMATIC",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": overall, **receipt["summary"], "output": str(args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output)}, sort_keys=True))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
