#!/usr/bin/env python3
"""Fresh-main validator for the supported WP03 AST-context typed-IR port.

The parser baseline remains selected V17. A contextual typed-fn overlay is derived in
memory without importing older V7 lexical semantics. The current main typed-IR builder
must then preserve frozen G9+Dialect frontend meaning, compile deterministically, preserve
grammar-admitted keyword identifiers, keep compact hyphenated identifiers distinct from
spaced subtraction, and keep declaration authority NONE.

PASS is implementation evidence only; formal WP02/WP03 and Andreas-target gates remain
separate.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import claycode_base_frontend as front
import claycode_base_typed_ir as tir

ROOT = Path(__file__).resolve().parents[1]
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


def derive_overlay(g17: str) -> str:
    lines = g17.splitlines()
    statement_hits = cycle_hits = 0
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
    return "\n".join(out) + ("\n" if g17.endswith("\n") else "")


def compile_text(source: str, grammar_path: Path, name: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="clay-wp03-main-") as td:
        p = Path(td) / name
        p.write_text(source, encoding="utf-8")
        return tir.compile_sources([p], grammar_path)


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
    g17 = V17.read_text(encoding="utf-8")
    v17_sha = sha(g17.encode("utf-8"))
    if v17_sha != EXPECTED_V17_SHA256:
        print(json.dumps({"pass": False, "classification": "STALE_V17_BYTES",
                          "expected": EXPECTED_V17_SHA256, "observed": v17_sha,
                          "promotion": "NONE"}, indent=2, sort_keys=True))
        return 2

    overlay = derive_overlay(g17)
    t0 = time.perf_counter_ns()
    try:
        front.build_parser(g17, strict=True)
        front.build_parser(overlay, strict=True)
        strict_error = None
    except Exception as exc:
        strict_error = f"{type(exc).__name__}: {exc}"
    strict_ms = (time.perf_counter_ns() - t0) / 1_000_000

    frontend_rows: list[dict[str, Any]] = []
    full: dict[str, Any] = {}
    keyword: dict[str, Any] = {}
    semantic: dict[str, Any] = {}
    error = None

    if strict_error is None:
        try:
            for path in (G9, DIALECT):
                text = path.read_text(encoding="utf-8")
                base = front.compile_frontend(text, g17, strict=True)
                ext = front.compile_frontend(text, overlay, strict=True)
                frontend_rows.append({
                    "path": str(path.relative_to(ROOT)),
                    "source_sha256": sha(text.encode("utf-8")),
                    "v17_semantic_hash": base["semantic_hash"],
                    "overlay_semantic_hash": ext["semantic_hash"],
                    "semantic_equal": base["semantic_hash"] == ext["semantic_hash"],
                })

            with tempfile.TemporaryDirectory(prefix="clay-wp03-main-grammar-") as td:
                gp = Path(td) / "V17_TYPED_FN_CONTEXTUAL_OVERLAY.lark"
                gp.write_text(overlay, encoding="utf-8")
                full_a = tir.compile_sources([G9, DIALECT], gp)
                full_b = tir.compile_sources([G9, DIALECT], gp)
                kw = compile_text(KEYWORD_FIXTURE, gp, "keyword.clay")
                compact = compile_text("fn f(a:Int,b:Int)->Int=a-b\n", gp, "compact.clay")
                subtract = compile_text("fn f(a:Int,b:Int)->Int=a - b\n", gp, "subtract.clay")
                addition = compile_text("fn f(a:Int,b:Int)->Int=a + b\n", gp, "addition.clay")
                fn_named = compile_text("fn fn(fn:Int)->Int=fn\n", gp, "fn-named.clay")

                full = {
                    "declaration_count": len(full_a.get("declarations", [])),
                    "program_semantic_id": full_a.get("program_semantic_id"),
                    "deterministic": (
                        full_a.get("program_semantic_id") == full_b.get("program_semantic_id")
                        and tir.canon_bytes(full_a) == tir.canon_bytes(full_b)
                    ),
                    "authority_all_none": all(d.get("authority") == "NONE" for d in full_a.get("declarations", [])),
                }
                keyword = {"shape": decl_shape(kw), "pass": keyword_shape_ok(decl_shape(kw))}
                semantic = {
                    "compact_body_tokens": fn_body(compact),
                    "subtract_body_tokens": fn_body(subtract),
                    "addition_body_tokens": fn_body(addition),
                    "compact_differs_from_subtraction": compact.get("program_semantic_id") != subtract.get("program_semantic_id"),
                    "addition_differs_from_subtraction": addition.get("program_semantic_id") != subtract.get("program_semantic_id"),
                    "fn_named_shape": decl_shape(fn_named)["function"],
                }
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

    frontend_pass = bool(frontend_rows) and all(x["semantic_equal"] for x in frontend_rows)
    semantics_pass = (
        semantic.get("compact_body_tokens") == ["a-b"]
        and semantic.get("subtract_body_tokens") == ["a", "-", "b"]
        and semantic.get("addition_body_tokens") == ["a", "+", "b"]
        and semantic.get("compact_differs_from_subtraction") is True
        and semantic.get("addition_differs_from_subtraction") is True
        and (semantic.get("fn_named_shape") or {}).get("name") == "fn"
        and (semantic.get("fn_named_shape") or {}).get("params") == [{"name": "fn", "type": "Int"}]
    )
    passed = (
        strict_error is None and error is None and frontend_pass
        and full.get("deterministic") is True
        and full.get("authority_all_none") is True
        and keyword.get("pass") is True
        and semantics_pass
    )

    out = {
        "schema_version": "1.0",
        "experiment": "WP03 fresh-main AST-context typed-IR port validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime": {"platform": platform.platform(), "machine": platform.machine(),
                    "python": platform.python_version(), "cpu_count": os.cpu_count(),
                    "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    "lark": pkg("lark"), "interegular": pkg("interegular"),
                    "github_sha": os.environ.get("GITHUB_SHA"),
                    "github_run_id": os.environ.get("GITHUB_RUN_ID"),
                    "runner_name": os.environ.get("RUNNER_NAME")},
        "inputs": {"v17_sha256": v17_sha, "overlay_sha256": sha(overlay.encode("utf-8")),
                   "typed_ir_sha256": sha((ROOT / "tools/claycode_base_typed_ir.py").read_bytes())},
        "strict": {"pass": strict_error is None, "error": strict_error, "elapsed_ms": strict_ms},
        "frozen_frontend": frontend_rows,
        "full_typed_ir": full,
        "keyword_identifiers": keyword,
        "semantic_identity_checks": semantic,
        "error": error,
        "pass": passed,
        "classification": "SUPPORTED_MAIN_IMPLEMENTATION_SLICE" if passed else "REFUTED_OR_INCOMPLETE",
        "promotion": "NONE",
        "architecture_delta": "KEEP_MINIMAL_AST_CONTEXT_PORT; formal WP03 remains receipt-gated" if passed else "ROLLBACK_OR_REPAIR_MAIN_PORT",
        "scope_guard": "PASS is GitHub-hosted implementation evidence only. It does not substitute for the registered Andreas Ubuntu target receipt, close WP02/WP03, advance WP04, or grant effect authority.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
