#!/usr/bin/env python3
"""Bounded falsifier for the ClayCode WP06 V16 typed-fn parser boundary.

Question: can the current pure-function compiler consume the exact current V16 typed-fn
slice when Lark strict collision checking is forced ON, without changing production code?

This is deliberately not a grammar redesign and not a promotion receipt.  It monkeypatches
only the compiler module's Lark constructor inside this disposable test process, records the
compiler's requested strict mode, forces strict=True, then exercises build -> reference eval
-> C11 lowering on a small typed program.  A PASS is evidence that a production strict-mode
migration is plausible; it is not proof that the full compiler regression suite passes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark as RealLark

ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "tools/claycode_base_compiler.py"
TYPED_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V16_GENERIC_DOTTED_LINEAR_LOOKAHEAD.lark"
TARGET_CONTRACT = ROOT / "research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    started = time.perf_counter_ns()
    contract = json.loads(TARGET_CONTRACT.read_text(encoding="utf-8"))
    separation = str(contract["wp02_parser_contract"].get("executable_slice_separation", ""))
    separation_ok = "typed-fn" in separation and "must not be relabeled as WP02" in separation

    grammar_text = TYPED_GRAMMAR.read_text(encoding="utf-8")
    grammar_sha = sha256_file(TYPED_GRAMMAR)

    # First falsifier: exact V16 bytes must construct under strict LALR/contextual mode.
    direct_strict_error = None
    try:
        RealLark(
            grammar_text,
            parser="lalr",
            lexer="contextual",
            strict=True,
            start="start",
            keep_all_tokens=True,
        )
        direct_strict_ok = True
    except Exception as exc:  # receipt must preserve the actual failure class/message
        direct_strict_ok = False
        direct_strict_error = f"{type(exc).__name__}:{exc}"

    spec = importlib.util.spec_from_file_location("claycode_base_compiler_v16_strict_falsifier", COMPILER)
    if spec is None or spec.loader is None:
        raise RuntimeError("COMPILER_IMPORT_SPEC_FAILED")
    cc = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = cc
    spec.loader.exec_module(cc)

    constructor_calls: list[dict[str, Any]] = []

    def strict_forcing_lark(*ctor_args: Any, **ctor_kwargs: Any):
        requested = ctor_kwargs.get("strict", "UNSPECIFIED")
        ctor_kwargs["strict"] = True
        constructor_calls.append({
            "requested_strict": requested,
            "forced_strict": True,
            "parser": ctor_kwargs.get("parser"),
            "lexer": ctor_kwargs.get("lexer"),
            "start": ctor_kwargs.get("start"),
        })
        return RealLark(*ctor_args, **ctor_kwargs)

    # Disposable process-local intervention only. Production source bytes stay untouched.
    cc.Lark = strict_forcing_lark

    smoke_source = (
        "fn add(a:Int,b:Int)->Int=a+b\n"
        "fn gt(a:Int,b:Int)->Bool=a>b\n"
        "fn half(x:Real)->Real=x/2.0\n"
        "fn echo(s:String)->String=s\n"
    )
    smoke_error = None
    smoke_details: dict[str, Any] = {}
    try:
        built = cc.build(smoke_source, grammar_text)
        add_value = cc.eval_function(built["ir"], "add", [2, 5])
        gt_value = cc.eval_function(built["ir"], "gt", [5, 2])
        half_value = cc.eval_function(built["ir"], "half", [9.0])
        echo_value = cc.eval_function(built["ir"], "echo", ["Grüße🙂"])
        c_source = cc.lower_c(built["ir"], "add")
        smoke_ok = (
            add_value == 7
            and gt_value is True
            and half_value == 4.5
            and echo_value == "Grüße🙂"
            and isinstance(c_source, str)
            and len(c_source) > 0
        )
        smoke_details = {
            "add": add_value,
            "gt": gt_value,
            "half": half_value,
            "echo_utf8_sha256": hashlib.sha256(echo_value.encode("utf-8")).hexdigest(),
            "generated_c_sha256": hashlib.sha256(c_source.encode("utf-8")).hexdigest(),
            "generated_c_bytes": len(c_source.encode("utf-8")),
        }
    except Exception as exc:
        smoke_ok = False
        smoke_error = f"{type(exc).__name__}:{exc}"

    production_requested_nonstrict = any(x["requested_strict"] is False for x in constructor_calls)
    forced_all_strict = bool(constructor_calls) and all(x["forced_strict"] is True for x in constructor_calls)
    passed = separation_ok and direct_strict_ok and forced_all_strict and smoke_ok

    receipt = {
        "schema_version": "1.0",
        "receipt_id": "CC_WP06_V16_STRICT_MIGRATION_FALSIFIER_V1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "BOUNDED_DISPOSABLE_STRICT_MODE_INTERVENTION",
        "question": "Can current WP06 typed-fn build/eval/lower execute on exact V16 grammar bytes when strict LALR collision checking is forced on?",
        "target_contract": {
            "path": str(TARGET_CONTRACT.relative_to(ROOT)),
            "sha256": sha256_file(TARGET_CONTRACT),
            "typed_fn_separation_present": separation_ok,
            "separation_text": separation,
        },
        "typed_grammar": {
            "path": str(TYPED_GRAMMAR.relative_to(ROOT)),
            "sha256": grammar_sha,
        },
        "compiler": {
            "path": str(COMPILER.relative_to(ROOT)),
            "sha256": sha256_file(COMPILER),
            "constructor_calls": constructor_calls,
            "production_requested_nonstrict_observed": production_requested_nonstrict,
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "lark": package_version("lark"),
            "interegular": package_version("interegular"),
        },
        "direct_strict_construction": {
            "pass": direct_strict_ok,
            "error": direct_strict_error,
        },
        "forced_strict_smoke": {
            "pass": smoke_ok,
            "error": smoke_error,
            "details": smoke_details,
        },
        "elapsed_ns": time.perf_counter_ns() - started,
        "pass": passed,
        "promotion": "NONE",
        "next_falsifier_if_pass": "Run the complete current-main WP06 regression under production strict=True, then compare exact evaluator/native outputs and resources against the current strict=False baseline before changing compiler source.",
        "scope_guard": "PASS does not close WP03/WP06/BASE and is not Hostinger or Andreas-target acceptance. It only falsifies the narrow claim that strict=True is immediately incompatible with the current V16 typed-fn smoke path.",
    }

    rendered = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
