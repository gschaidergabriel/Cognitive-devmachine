#!/usr/bin/env python3
"""Bounded WP03 shadow validation: selected V17 semantics plus typed single-expression fn.

Research-only. This does not select a new production grammar and does not promote CC-WP-03.
It asks one narrow question: can the typed-IR function slice stop depending on the strict-blocked
V7 grammar while preserving the currently selected V17 declarative semantics?
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

import claycode_base_frontend as front
import claycode_base_typed_ir as tir

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
OVERLAY = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_RESEARCH_V17_WP03_TYPED_FN_OVERLAY.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def quantile(values: list[float], q: float) -> float:
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def timing_summary(values_ms: list[float]) -> dict[str, Any]:
    return {
        "n": len(values_ms),
        "mean_ms": statistics.fmean(values_ms),
        "p50_ms": quantile(values_ms, 0.50),
        "p90_ms": quantile(values_ms, 0.90),
        "p95_ms": quantile(values_ms, 0.95),
        "p99_ms": quantile(values_ms, 0.99),
        "min_ms": min(values_ms),
        "max_ms": max(values_ms),
    }


def strict_build_times(grammar: str, reps: int = 5) -> tuple[list[float], str | None]:
    times: list[float] = []
    err = None
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        try:
            front.build_parser(grammar, strict=True)
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            break
        times.append((time.perf_counter_ns() - t0) / 1_000_000)
    return times, err


def compile_fixture(source: str, name: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="clay-wp03-v17fn-") as td:
        path = Path(td) / name
        path.write_text(source, encoding="utf-8")
        return tir.compile_sources([path], OVERLAY)


def function_decl(ir: dict[str, Any]) -> dict[str, Any]:
    return next(x for x in ir["declarations"] if x["kind"] == "function")


def parse_state(parser, source: str) -> dict[str, Any]:
    try:
        tree = parser.parse(source)
        ast = front.canonical_node(tree)
        sem = sha256(front.DOMAIN + front.canonical_bytes(ast))
        return {"accept": True, "semantic_hash": sem}
    except Exception as exc:
        return {"accept": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    g17 = V17.read_text(encoding="utf-8")
    gov = OVERLAY.read_text(encoding="utf-8")
    source_paths = [G9, DIALECT]

    v17_build, v17_error = strict_build_times(g17)
    ov_build, ov_error = strict_build_times(gov)
    strict_ok = v17_error is None and ov_error is None and len(v17_build) == 5 and len(ov_build) == 5

    rows: list[dict[str, Any]] = []
    if strict_ok:
        for path in source_paths:
            text = path.read_text(encoding="utf-8")
            a = front.compile_frontend(text, g17, strict=True)
            b = front.compile_frontend(text, gov, strict=True)
            rows.append({
                "path": str(path.relative_to(ROOT)),
                "source_sha256": sha256(text.encode("utf-8")),
                "v17_semantic_hash": a["semantic_hash"],
                "overlay_semantic_hash": b["semantic_hash"],
                "semantic_equal": a["semantic_hash"] == b["semantic_hash"],
            })

    ir_v17 = None
    ir_overlay = None
    ir_equal = False
    ir_error = None
    if strict_ok:
        try:
            ir_v17 = tir.compile_sources(source_paths, V17)
            ir_overlay = tir.compile_sources(source_paths, OVERLAY)
            ir_equal = ir_v17["program_semantic_id"] == ir_overlay["program_semantic_id"]
        except Exception as exc:
            ir_error = f"{type(exc).__name__}: {exc}"

    fixtures: dict[str, Any] = {}
    fixture_error = None
    if strict_ok:
        try:
            add = compile_fixture("fn add(a:Int,b:Int)->Int=a+b\n", "add.clay")
            add_ws = compile_fixture("fn add ( a : Int , b : Int ) -> Int = a + b\n", "add_ws.clay")
            sub_spaced = compile_fixture("fn add(a:Int,b:Int)->Int=a - b\n", "sub_spaced.clay")
            hyphen_compact = compile_fixture("fn add(a:Int,b:Int)->Int=a-b\n", "hyphen_compact.clay")
            f_add = function_decl(add)
            f_sub = function_decl(sub_spaced)
            f_hyphen = function_decl(hyphen_compact)
            fixtures = {
                "typed_signature": f_add,
                "layout_identity_equal": add["program_semantic_id"] == add_ws["program_semantic_id"],
                "spaced_subtraction_discriminated": add["program_semantic_id"] != sub_spaced["program_semantic_id"],
                "compact_hyphen_not_spaced_subtraction": hyphen_compact["program_semantic_id"] != sub_spaced["program_semantic_id"],
                "compact_hyphen_body_tokens": f_hyphen["body_tokens"],
                "spaced_subtraction_body_tokens": f_sub["body_tokens"],
                "compact_hyphen_is_single_identifier": f_hyphen["body_tokens"] == ["a-b"],
            }
        except Exception as exc:
            fixture_error = f"{type(exc).__name__}: {exc}"

    boundaries = {}
    if strict_ok:
        p_overlay = front.build_parser(gov, strict=True)
        boundary_sources = {
            "frozen_bare_owns": "rule 4B_need_not_learn Needle.owns\n",
            "owns_relation": "rule Needle.owns [tool_schema,api_wire]\n",
            "lowers_relation": "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
            "owns_call_tight": "rule Needle.owns(X)\n",
            "owns_call_spaced": "rule Needle.owns (X)\n",
            "bare_owns_trailing_spaces": "rule Needle.owns   \n",
            "bare_owns_trailing_comment": "rule Needle.owns   // comment\n",
        }
        boundaries = {k: parse_state(p_overlay, v) for k, v in boundary_sources.items()}

    boundary_ok = bool(boundaries) and all(x.get("accept") for x in boundaries.values())
    fixture_ok = (
        fixture_error is None
        and fixtures.get("layout_identity_equal") is True
        and fixtures.get("spaced_subtraction_discriminated") is True
        and fixtures.get("compact_hyphen_not_spaced_subtraction") is True
        and fixtures.get("compact_hyphen_is_single_identifier") is True
        and fixtures.get("typed_signature", {}).get("params") == [
            {"name": "a", "type": "Int"}, {"name": "b", "type": "Int"}
        ]
        and fixtures.get("typed_signature", {}).get("returns") == "Int"
    )
    full_source_parity = bool(rows) and all(x["semantic_equal"] for x in rows)
    passed = strict_ok and full_source_parity and ir_error is None and ir_equal and fixture_ok and boundary_ok

    receipt = {
        "schema_version": "1.0",
        "scope": "CC-WP-03_V17_TYPED_FN_OVERLAY_SHADOW",
        "created_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "runtime": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "lark": pkg("lark"),
            "interegular": pkg("interegular"),
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "identity": {
            "v17_path": str(V17.relative_to(ROOT)),
            "v17_sha256": sha256(g17.encode("utf-8")),
            "overlay_path": str(OVERLAY.relative_to(ROOT)),
            "overlay_sha256": sha256(gov.encode("utf-8")),
            "typed_ir_module_sha256": sha256((ROOT / "tools/claycode_base_typed_ir.py").read_bytes()),
            "frontend_module_sha256": sha256((ROOT / "tools/claycode_base_frontend.py").read_bytes()),
        },
        "strict_construction": {
            "v17": timing_summary(v17_build) if v17_build else None,
            "overlay": timing_summary(ov_build) if ov_build else None,
            "v17_error": v17_error,
            "overlay_error": ov_error,
            "pass": strict_ok,
        },
        "frozen_source_frontend_parity": rows,
        "frozen_source_typed_ir": {
            "v17_program_semantic_id": ir_v17.get("program_semantic_id") if ir_v17 else None,
            "overlay_program_semantic_id": ir_overlay.get("program_semantic_id") if ir_overlay else None,
            "semantic_equal": ir_equal,
            "error": ir_error,
        },
        "typed_fn_fixtures": fixtures,
        "typed_fn_fixture_error": fixture_error,
        "needle_boundaries": boundaries,
        "legacy_v7_fixture_diagnosis": {
            "old_fixture": "fn add(a:Int,b:Int)->Int=a-b",
            "selected_v17_semantics": "a-b is a hyphenated identifier, not subtraction",
            "v17_compatible_subtraction_fixture": "fn add(a:Int,b:Int)->Int=a - b",
            "classification": "STALE_CROSS_VERSION_TEST_EXPECTATION",
        },
        "pass": passed,
        "promotion": "NONE_AUTOMATIC",
        "architecture_delta": (
            "SUPPORTED_SHADOW_REMOVE_V7_DEPENDENCY_CANDIDATE"
            if passed
            else "REFUTED_OR_UNRESOLVED_KEEP_CURRENT_BINDING_UNTIL_DIAGNOSED"
        ),
        "scope_guard": (
            "PASS supports only the hypothesis that WP03 typed single-expression fn can be evaluated on a minimal overlay of selected V17 without changing frozen G9/Dialect semantic identity or V17 Needle/hyphen boundaries. "
            "It does not select the overlay as production grammar, close CC-WP-02/03, prove WP04/05/06, replace registered Andreas Ubuntu acceptance, or authorize a Frank Harness change."
        ),
    }

    text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
