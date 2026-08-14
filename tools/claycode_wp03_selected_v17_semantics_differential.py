#!/usr/bin/env python3
"""Adversarial CC-WP-03 differential anchored to the selected V17 language semantics.

Research-only. It compares three surfaces on exact repository bytes:
A) selected V17 production grammar;
B) an in-memory minimal V17 + typed-single-expression-fn overlay;
C) the research V7 typed-fn + V17 relation-membrane composition.

The goal is to detect cross-version semantic inheritance, especially compact `x-y` and
hyphenated identifiers, before WP03 binds typed IR to a grammar that differs from WP02.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import statistics
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import claycode_base_frontend as front
import claycode_base_typed_ir as tir

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
COMPOSED = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_RESEARCH_V7_TYPED_FN_V17_RELATION_MEMBRANE.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"
EXPECTED_V17_SHA256 = "83abde2348e6a40204e94ed91021a6e2f79a5ad1f0d96b09437214158ac70a64"


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def derive_v17_typed_fn_overlay(g17: str) -> str:
    """Apply only the three surface edits required for typed expression-bodied fn."""
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
    text = "\n".join(out) + ("\n" if g17.endswith("\n") else "")
    # Deliberately DO NOT reserve `fn` in NAME. With Lark's contextual lexer the same
    # spelling remains a V17 identifier where an ident is expected and becomes the
    # declaration literal only at a statement position that admits fn_decl.
    if (statement_hits, cycle_hits) != (1, 1):
        raise RuntimeError({"statement_hits": statement_hits, "cycle_hits": cycle_hits})
    return text


def build_times(grammar: str, reps: int = 5) -> tuple[list[float], str | None]:
    vals: list[float] = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        try:
            front.build_parser(grammar, strict=True)
        except Exception as exc:
            return vals, f"{type(exc).__name__}: {exc}"
        vals.append((time.perf_counter_ns() - t0) / 1_000_000)
    return vals, None


def parse_row(parser, source: str) -> dict[str, Any]:
    try:
        tree = parser.parse(source)
        ast = front.canonical_node(tree)
        return {
            "accept": True,
            "semantic_hash": sha(front.DOMAIN + front.canonical_bytes(ast)),
            "tree": tree.pretty(),
        }
    except Exception as exc:
        return {"accept": False, "error": f"{type(exc).__name__}: {exc}"}


def compile_text(text: str, grammar: Path, name: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="clay-wp03-selected-sem-") as td:
        p = Path(td) / name
        p.write_text(text, encoding="utf-8")
        return tir.compile_sources([p], grammar)


def fn_body(ir: dict[str, Any]) -> list[str]:
    fn = next(x for x in ir["declarations"] if x["kind"] == "function")
    return fn["body_tokens"]


def main() -> int:
    g17 = V17.read_text(encoding="utf-8")
    composed = COMPOSED.read_text(encoding="utf-8")
    v17_sha = sha(g17.encode("utf-8"))
    if v17_sha != EXPECTED_V17_SHA256:
        print(json.dumps({
            "schema_version": "1.0",
            "pass": False,
            "classification": "STALE_SELECTED_V17_BYTES",
            "expected_v17_sha256": EXPECTED_V17_SHA256,
            "observed_v17_sha256": v17_sha,
            "promotion": "NONE",
        }, indent=2, sort_keys=True))
        return 2

    overlay = derive_v17_typed_fn_overlay(g17)
    overlay_sha = sha(overlay.encode("utf-8"))

    with tempfile.TemporaryDirectory(prefix="clay-v17fn-grammar-") as td:
        overlay_path = Path(td) / "V17_TYPED_FN_OVERLAY.lark"
        overlay_path.write_text(overlay, encoding="utf-8")

        timings = {}
        strict_errors = {}
        parsers = {}
        for name, grammar in (("v17", g17), ("v17_typed_fn_overlay", overlay), ("v7_v17_composed", composed)):
            vals, err = build_times(grammar)
            timings[name] = dist(vals) if vals else None
            strict_errors[name] = err
            if err is None:
                parsers[name] = front.build_parser(grammar, strict=True)
        strict_ok = all(v is None for v in strict_errors.values())

        full_source_rows = []
        if strict_ok:
            for path in (G9, DIALECT):
                text = path.read_text(encoding="utf-8")
                a = front.compile_frontend(text, g17, strict=True)
                b = front.compile_frontend(text, overlay, strict=True)
                c = front.compile_frontend(text, composed, strict=True)
                full_source_rows.append({
                    "path": str(path.relative_to(ROOT)),
                    "source_sha256": sha(text.encode("utf-8")),
                    "selected_v17_semantic_hash": a["semantic_hash"],
                    "overlay_semantic_hash": b["semantic_hash"],
                    "composed_semantic_hash": c["semantic_hash"],
                    "overlay_equal_selected": b["semantic_hash"] == a["semantic_hash"],
                    "composed_equal_selected": c["semantic_hash"] == a["semantic_hash"],
                })

        fixtures = {
            "compact": "fn f(a:Int,b:Int)->Int=a-b\n",
            "spaced_sub": "fn f(a:Int,b:Int)->Int=a - b\n",
            "spaced_add": "fn f(a:Int,b:Int)->Int=a + b\n",
            "hyphen_decl": "record user-profile { id:Int }\n",
            "fn_identifier_rule": "rule fn\n",
            "fn_identifier_record": "record fn { id:Int }\n",
            "fn_identifier_everywhere": "fn fn(fn:Int)->Int=fn\n",
        }
        parse_matrix = {}
        if strict_ok:
            for key, src in fixtures.items():
                parse_matrix[key] = {
                    "overlay": parse_row(parsers["v17_typed_fn_overlay"], src),
                    "composed": parse_row(parsers["v7_v17_composed"], src),
                }

        typed = {}
        typed_error = None
        if strict_ok:
            try:
                selected_ir = tir.compile_sources([G9, DIALECT], V17)
                overlay_ir = tir.compile_sources([G9, DIALECT], overlay_path)
                compact_overlay = compile_text(fixtures["compact"], overlay_path, "compact.clay")
                sub_overlay = compile_text(fixtures["spaced_sub"], overlay_path, "sub.clay")
                compact_composed = compile_text(fixtures["compact"], COMPOSED, "compact_composed.clay")
                sub_composed = compile_text(fixtures["spaced_sub"], COMPOSED, "sub_composed.clay")
                typed = {
                    "full_selected_program_semantic_id": selected_ir["program_semantic_id"],
                    "full_overlay_program_semantic_id": overlay_ir["program_semantic_id"],
                    "full_overlay_equal_selected": selected_ir["program_semantic_id"] == overlay_ir["program_semantic_id"],
                    "compact_overlay_body_tokens": fn_body(compact_overlay),
                    "spaced_sub_overlay_body_tokens": fn_body(sub_overlay),
                    "compact_composed_body_tokens": fn_body(compact_composed),
                    "spaced_sub_composed_body_tokens": fn_body(sub_composed),
                }
            except Exception as exc:
                typed_error = f"{type(exc).__name__}: {exc}"

        compact_overlay_is_identifier = typed.get("compact_overlay_body_tokens") == ["a-b"]
        spaced_overlay_is_sub = typed.get("spaced_sub_overlay_body_tokens") == ["a", "-", "b"]
        compact_composed_is_sub = typed.get("compact_composed_body_tokens") == ["a", "-", "b"]
        semantic_conflict = compact_overlay_is_identifier and compact_composed_is_sub
        hyphen_decl_conflict = (
            parse_matrix.get("hyphen_decl", {}).get("overlay", {}).get("accept") is True
            and parse_matrix.get("hyphen_decl", {}).get("composed", {}).get("accept") is False
        )
        overlay_preserves_full_selected = bool(full_source_rows) and all(x["overlay_equal_selected"] for x in full_source_rows)
        contextual_fn_identifier_preserved = all(
            parse_matrix.get(k, {}).get("overlay", {}).get("accept") is True
            for k in ("fn_identifier_rule", "fn_identifier_record", "fn_identifier_everywhere")
        )
        passed = (
            strict_ok
            and overlay_preserves_full_selected
            and typed_error is None
            and typed.get("full_overlay_equal_selected") is True
            and compact_overlay_is_identifier
            and spaced_overlay_is_sub
            and compact_composed_is_sub
            and semantic_conflict
            and hyphen_decl_conflict
            and contextual_fn_identifier_preserved
        )

        out = {
            "schema_version": "1.0",
            "experiment": "CC-WP-03 selected-V17 semantics differential",
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
            "identity": {
                "selected_v17_path": str(V17.relative_to(ROOT)),
                "selected_v17_sha256": v17_sha,
                "derived_overlay_sha256": overlay_sha,
                "composed_path": str(COMPOSED.relative_to(ROOT)),
                "composed_sha256": sha(composed.encode("utf-8")),
                "frontend_sha256": sha((ROOT / "tools/claycode_base_frontend.py").read_bytes()),
                "typed_ir_sha256": sha((ROOT / "tools/claycode_base_typed_ir.py").read_bytes()),
            },
            "strict_build": {"timings": timings, "errors": strict_errors, "pass": strict_ok},
            "frozen_source_frontend": full_source_rows,
            "targeted_parse_matrix": parse_matrix,
            "typed_ir": {**typed, "error": typed_error},
            "causal_checks": {
                "overlay_preserves_full_selected_frontend": overlay_preserves_full_selected,
                "overlay_preserves_full_selected_typed_ir": typed.get("full_overlay_equal_selected") is True,
                "selected_compact_hyphen_is_identifier": compact_overlay_is_identifier,
                "selected_spaced_minus_is_subtraction": spaced_overlay_is_sub,
                "composed_compact_minus_is_subtraction": compact_composed_is_sub,
                "same_source_compact_semantic_conflict": semantic_conflict,
                "hyphenated_declaration_acceptance_conflict": hyphen_decl_conflict,
                "contextual_fn_identifier_preserved": contextual_fn_identifier_preserved,
            },
            "pass": passed,
            "classification": "CROSS_VERSION_SEMANTIC_DRIFT_PROVEN" if passed else "UNRESOLVED_OR_REFUTED",
            "architecture_delta": (
                "KEEP_SELECTED_V17_SEMANTICS; treat typed-fn as additive overlay or explicit normalized extension. Do not inherit V7 compact-subtraction/NAME semantics into WP03 without a separate owner-approved language-semantic change backed by executable counterevidence."
                if passed else
                "NO_PROMOTION_PENDING_DIAGNOSIS"
            ),
            "promotion": "NONE",
            "scope_guard": "PASS proves only a bounded semantic mismatch between the selected V17 language contract and the tested V7/V17 composed WP03 research grammar while showing a minimal contextual typed-fn overlay can preserve selected V17 on the declared frozen-source and fixture scope, including existing `fn` identifier uses. It does not close WP02/03/BASE, prove evaluator/compiler equivalence, or authorize Frank Harness changes.",
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
