#!/usr/bin/env python3
"""WP03 differential: selected V17 + contextual typed-fn overlay + PR145 typed-IR candidate.

Research-only. This separates the upstream grammar contract from the downstream typed-IR
identifier bug. PASS means the exact selected V17 semantics can be extended with typed
single-expression functions without changing frozen-source meaning, while the PR145
AST-context identifier candidate repairs the independently observed keyword-identifier defect.
It does not select or merge either candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import resource
import statistics
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import claycode_base_frontend as front  # noqa: E402
import claycode_base_typed_ir as main_tir  # noqa: E402

V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"
EXPECTED_V17_SHA256 = "83abde2348e6a40204e94ed91021a6e2f79a5ad1f0d96b09437214158ac70a64"

KEYWORD_FIXTURE = (
    "record status {\n status:Symbol\n}\n"
    "fn status(status:Symbol)->Symbol=status\n"
    "interface status {\n status(status:Symbol)->Symbol\n}\n"
)


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("claycode_pr145_typed_ir_candidate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def derive_overlay(g17: str) -> str:
    lines = g17.splitlines()
    statement_hits = 0
    cycle_hits = 0
    out: list[str] = []
    for line in lines:
        if line.startswith("?statement:"):
            if "fn_decl" in line:
                raise RuntimeError("selected V17 unexpectedly already contains fn_decl")
            line += " | fn_decl"
            statement_hits += 1
        out.append(line)
        if line.startswith("cycle_decl:"):
            out.extend([
                'fn_decl: "fn" ident "(" [typed_params] ")" "->" type_expr "=" expr',
                'typed_params: typed_param ("," typed_param)*',
                'typed_param: ident ":" type_expr',
            ])
            cycle_hits += 1
    if (statement_hits, cycle_hits) != (1, 1):
        raise RuntimeError({"statement_hits": statement_hits, "cycle_hits": cycle_hits})
    # Intentionally do not exclude `fn` from NAME. Contextual lexing keeps it a V17
    # identifier where ident is expected while accepting the declaration literal at statement start.
    return "\n".join(out) + ("\n" if g17.endswith("\n") else "")


def quantile(values: list[float], q: float) -> float:
    xs = sorted(values)
    p = (len(xs) - 1) * q
    lo = int(p)
    hi = min(lo + 1, len(xs) - 1)
    f = p - lo
    return xs[lo] * (1 - f) + xs[hi] * f


def dist(values: list[float]) -> dict[str, Any]:
    return {
        "n": len(values),
        "mean_ms": statistics.fmean(values),
        "p50_ms": quantile(values, 0.50),
        "p90_ms": quantile(values, 0.90),
        "p95_ms": quantile(values, 0.95),
        "p99_ms": quantile(values, 0.99),
        "min_ms": min(values),
        "max_ms": max(values),
    }


def strict_build_times(grammar: str, reps: int = 7) -> tuple[list[float], str | None]:
    vals: list[float] = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        try:
            front.build_parser(grammar, strict=True)
        except Exception as exc:
            return vals, f"{type(exc).__name__}: {exc}"
        vals.append((time.perf_counter_ns() - t0) / 1_000_000)
    return vals, None


def compile_text(tir, source: str, grammar_path: Path, name: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="clay-wp03-v17-pr145-") as td:
        p = Path(td) / name
        p.write_text(source, encoding="utf-8")
        return tir.compile_sources([p], grammar_path)


def parse_state(parser, source: str) -> dict[str, Any]:
    try:
        tree = parser.parse(source)
        ast = front.canonical_node(tree)
        return {
            "accepted": True,
            "semantic_hash": sha(front.DOMAIN + front.canonical_bytes(ast)),
            "tree_hash": sha(tree.pretty().encode("utf-8")),
        }
    except Exception as exc:
        return {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}


def decl_shape(program: dict[str, Any]) -> dict[str, Any]:
    decls = program.get("declarations", [])
    return {
        "record": next((x for x in decls if x.get("kind") == "record"), None),
        "function": next((x for x in decls if x.get("kind") == "function"), None),
        "interface": next((x for x in decls if x.get("kind") == "interface"), None),
    }


def keyword_shape_ok(shape: dict[str, Any]) -> bool:
    record = shape.get("record") or {}
    function = shape.get("function") or {}
    interface = shape.get("interface") or {}
    return (
        record.get("name") == "status"
        and record.get("fields") == [{"name": "status", "type": "Symbol", "default_tokens": None}]
        and function.get("name") == "status"
        and function.get("params") == [{"name": "status", "type": "Symbol"}]
        and function.get("returns") == "Symbol"
        and interface.get("name") == "status"
        and interface.get("methods") == [
            {"name": "status", "params": [{"name": "status", "type": "Symbol"}], "returns": "Symbol"}
        ]
    )


def fn_body(program: dict[str, Any]) -> list[str]:
    fn = next(x for x in program["declarations"] if x["kind"] == "function")
    return fn["body_tokens"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--typed-ir-candidate", type=Path, required=True)
    args = ap.parse_args()
    candidate_tir = load_module(args.typed_ir_candidate)

    g17 = V17.read_text(encoding="utf-8")
    v17_sha = sha(g17.encode("utf-8"))
    if v17_sha != EXPECTED_V17_SHA256:
        print(json.dumps({
            "schema_version": "1.0",
            "pass": False,
            "classification": "STALE_SELECTED_V17_BYTES",
            "expected": EXPECTED_V17_SHA256,
            "observed": v17_sha,
            "promotion": "NONE",
        }, indent=2, sort_keys=True))
        return 2

    overlay = derive_overlay(g17)
    overlay_sha = sha(overlay.encode("utf-8"))

    with tempfile.TemporaryDirectory(prefix="clay-v17-overlay-") as td:
        overlay_path = Path(td) / "V17_TYPED_FN_CONTEXTUAL_OVERLAY.lark"
        overlay_path.write_text(overlay, encoding="utf-8")

        v17_times, v17_error = strict_build_times(g17)
        overlay_times, overlay_error = strict_build_times(overlay)
        strict_ok = v17_error is None and overlay_error is None

        frontend_rows = []
        parser = None
        if strict_ok:
            parser = front.build_parser(overlay, strict=True)
            for path in (G9, DIALECT):
                text = path.read_text(encoding="utf-8")
                baseline = front.compile_frontend(text, g17, strict=True)
                candidate = front.compile_frontend(text, overlay, strict=True)
                frontend_rows.append({
                    "path": str(path.relative_to(ROOT)),
                    "source_sha256": sha(text.encode("utf-8")),
                    "v17_semantic_hash": baseline["semantic_hash"],
                    "overlay_semantic_hash": candidate["semantic_hash"],
                    "semantic_equal": baseline["semantic_hash"] == candidate["semantic_hash"],
                })

        boundary_sources = {
            "bare_owns": "rule 4B_need_not_learn Needle.owns\n",
            "owns_relation": "rule Needle.owns [tool_schema,api_wire]\n",
            "lowers_relation": "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
            "owns_call_tight": "rule Needle.owns(X)\n",
            "owns_call_spaced": "rule Needle.owns (X)\n",
            "bare_owns_spaces": "rule Needle.owns   \n",
            "bare_owns_comment": "rule Needle.owns   // trailing comment\n",
            "fn_identifier_rule": "rule fn\n",
            "fn_identifier_record": "record fn { id:Int }\n",
            "fn_identifier_function": "fn fn(fn:Int)->Int=fn\n",
            "hyphenated_record": "record user-profile { id:Int }\n",
        }
        boundaries = {k: parse_state(parser, v) for k, v in boundary_sources.items()} if parser else {}

        main_baseline = {"error": None, "keyword_shape": None, "full_error": None}
        candidate = {"error": None, "keyword_shape": None, "full_error": None}
        typed_checks: dict[str, Any] = {}

        if strict_ok:
            try:
                main_kw = compile_text(main_tir, KEYWORD_FIXTURE, overlay_path, "keyword-main.clay")
                main_baseline["keyword_shape"] = decl_shape(main_kw)
            except Exception as exc:
                main_baseline["error"] = f"{type(exc).__name__}: {exc}"
            try:
                main_tir.compile_sources([G9, DIALECT], overlay_path)
            except Exception as exc:
                main_baseline["full_error"] = f"{type(exc).__name__}: {exc}"

            try:
                candidate_kw = compile_text(candidate_tir, KEYWORD_FIXTURE, overlay_path, "keyword-candidate.clay")
                candidate["keyword_shape"] = decl_shape(candidate_kw)
                cand_full_a = candidate_tir.compile_sources([G9, DIALECT], overlay_path)
                cand_full_b = candidate_tir.compile_sources([G9, DIALECT], overlay_path)
                candidate["program_semantic_id"] = cand_full_a["program_semantic_id"]
                candidate["full_deterministic"] = (
                    cand_full_a["program_semantic_id"] == cand_full_b["program_semantic_id"]
                    and candidate_tir.canon_bytes(cand_full_a) == candidate_tir.canon_bytes(cand_full_b)
                )

                compact = compile_text(candidate_tir, "fn f(a:Int,b:Int)->Int=a-b\n", overlay_path, "compact.clay")
                subtract = compile_text(candidate_tir, "fn f(a:Int,b:Int)->Int=a - b\n", overlay_path, "subtract.clay")
                add = compile_text(candidate_tir, "fn f(a:Int,b:Int)->Int=a + b\n", overlay_path, "add.clay")
                fn_named = compile_text(candidate_tir, "fn fn(fn:Int)->Int=fn\n", overlay_path, "fn-named.clay")
                typed_checks = {
                    "compact_hyphen_body_tokens": fn_body(compact),
                    "spaced_subtraction_body_tokens": fn_body(subtract),
                    "addition_body_tokens": fn_body(add),
                    "fn_named_shape": decl_shape(fn_named)["function"],
                    "compact_differs_from_subtraction": compact["program_semantic_id"] != subtract["program_semantic_id"],
                    "addition_differs_from_subtraction": add["program_semantic_id"] != subtract["program_semantic_id"],
                }
            except Exception as exc:
                candidate["full_error"] = f"{type(exc).__name__}: {exc}"

        main_bug_reproduced = (
            main_baseline["error"] is not None
            or not keyword_shape_ok(main_baseline.get("keyword_shape") or {})
        )
        candidate_keyword_ok = keyword_shape_ok(candidate.get("keyword_shape") or {})
        frontend_equal = bool(frontend_rows) and all(x["semantic_equal"] for x in frontend_rows)
        boundary_ok = bool(boundaries) and all(x.get("accepted") is True for x in boundaries.values())
        selected_hyphen_semantics_ok = (
            typed_checks.get("compact_hyphen_body_tokens") == ["a-b"]
            and typed_checks.get("spaced_subtraction_body_tokens") == ["a", "-", "b"]
            and typed_checks.get("compact_differs_from_subtraction") is True
        )
        fn_contextual_ok = (
            typed_checks.get("fn_named_shape", {}).get("name") == "fn"
            and typed_checks.get("fn_named_shape", {}).get("params") == [{"name": "fn", "type": "Int"}]
        )
        candidate_ok = (
            candidate.get("full_error") is None
            and candidate.get("full_deterministic") is True
            and candidate_keyword_ok
            and selected_hyphen_semantics_ok
            and fn_contextual_ok
        )

        passed = strict_ok and frontend_equal and boundary_ok and main_bug_reproduced and candidate_ok
        out = {
            "schema_version": "1.0",
            "experiment": "WP03 selected V17 contextual typed-fn overlay + PR145 typed-IR differential",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "evidence_class": "EXECUTABLE_RESEARCH_DIFFERENTIAL",
            "runtime": {
                "platform": platform.platform(),
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
            "inputs": {
                "selected_v17_path": str(V17.relative_to(ROOT)),
                "selected_v17_sha256": v17_sha,
                "derived_overlay_sha256": overlay_sha,
                "main_typed_ir_sha256": sha((ROOT / "tools/claycode_base_typed_ir.py").read_bytes()),
                "candidate_typed_ir_path": str(args.typed_ir_candidate),
                "candidate_typed_ir_sha256": sha(args.typed_ir_candidate.read_bytes()),
                "g9_sha256": sha(G9.read_bytes()),
                "dialect_sha256": sha(DIALECT.read_bytes()),
            },
            "strict_construction": {
                "v17": dist(v17_times) if v17_times else None,
                "overlay": dist(overlay_times) if overlay_times else None,
                "v17_error": v17_error,
                "overlay_error": overlay_error,
                "pass": strict_ok,
            },
            "frozen_source_frontend_parity": frontend_rows,
            "boundary_cases": boundaries,
            "main_typed_ir_baseline": {**main_baseline, "known_keyword_bug_reproduced": main_bug_reproduced},
            "pr145_candidate": {
                **candidate,
                "keyword_shape_pass": candidate_keyword_ok,
                "selected_hyphen_semantics_pass": selected_hyphen_semantics_ok,
                "contextual_fn_identifier_pass": fn_contextual_ok,
                "typed_checks": typed_checks,
            },
            "pass": passed,
            "classification": "SUPPORTED_SELECTED_V17_WP03_STACK_CANDIDATE" if passed else "UNRESOLVED_OR_REFUTED",
            "architecture_delta": (
                "SUPPORTED_CANDIDATE: keep selected V17 lexical/Needle semantics, add typed-fn contextually, and port only PR145 AST-context identifier extraction after fresh-main review. Do not inherit V7 compact-subtraction/NAME semantics."
                if passed else
                "NO_PROMOTION: minimize the first failing layer before changing language semantics or typed IR."
            ),
            "promotion": "NONE",
            "scope_guard": "PASS is bounded research evidence for the selected-V17 grammar surface plus PR145 identifier extraction on exact tested bytes. It does not merge PR145, close CC-WP-03/BASE, prove checker/evaluator/compiler/effect semantics, replace registered Andreas Ubuntu target acceptance, or authorize Frank Harness mutation.",
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
