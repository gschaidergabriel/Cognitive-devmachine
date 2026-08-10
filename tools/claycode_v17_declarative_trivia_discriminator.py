#!/usr/bin/env python3
"""Discriminate minimal V17 declarative trivia repair against active V9.

The discriminator is intentionally narrow: V17 must preserve V9 semantics for the entire
current admitted G9 + Dialect corpora and every existing V5/V6 regression fixture, while
repairing the concrete horizontal-whitespace call counterexample:

    Needle.owns(X) == Needle.owns (X)

It does not test or import the V7/V10/V16 typed-fn surface. Strict mode requires
interegular and is mandatory before V17 can supersede V9 for CC-WP-02.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark

import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
V9 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark"
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
CORPORA = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
DEFAULT_OUT = ROOT / "research_entity/claycode/base/receipts/CC_WP02_V17_DECLARATIVE_TRIVIA_DISCRIMINATOR.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def compile_semantic(source: str, grammar: str, *, strict: bool) -> tuple[bool, str | None, str | None]:
    try:
        row = front.compile_frontend(source, grammar, strict=strict)
        return True, str(row["semantic_hash"]), None
    except Exception as exc:
        return False, None, f"{type(exc).__name__}: {exc}"


def parse_ok(parser: Lark, source: str) -> tuple[bool, str | None]:
    try:
        parser.parse(source)
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def display_path(path: Path) -> str:
    """Render repo-relative paths when possible, otherwise preserve the exact path."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--require-strict", action="store_true")
    args = ap.parse_args()

    strict_dependency = version("interegular") is not None
    strict = bool(args.require_strict)
    if strict and not strict_dependency:
        out = {
            "schema_version": "1.0",
            "experiment": "CC-WP02 V17 declarative trivia discriminator",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "pass": False,
            "failure": "STRICT_DEPENDENCY_MISSING",
            "runtime": {"lark": version("lark"), "interegular": version("interegular")},
            "counts_as_wp02_pass": False,
            "promotion_allowed": False,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(out, sort_keys=True))
        return 3

    g9 = V9.read_text(encoding="utf-8")
    g17 = V17.read_text(encoding="utf-8")
    parser9 = Lark(g9, parser="lalr", lexer="contextual", strict=strict, start="start", keep_all_tokens=True)
    parser17 = Lark(g17, parser="lalr", lexer="contextual", strict=strict, start="start", keep_all_tokens=True)

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, **detail: Any) -> None:
        checks.append({"name": name, "pass": bool(passed), **detail})

    # Full admitted declarative corpora must remain byte-source distinct but semantically
    # identical across V9 and V17. This guards against collateral language drift.
    for path in CORPORA:
        source = path.read_text(encoding="utf-8")
        ok9, h9, e9 = compile_semantic(source, g9, strict=strict)
        ok17, h17, e17 = compile_semantic(source, g17, strict=strict)
        check(
            f"corpus_semantic_equivalence:{path.name}",
            ok9 and ok17 and h9 == h17,
            source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            v9_semantic_hash=h9,
            v17_semantic_hash=h17,
            v9_error=e9,
            v17_error=e17,
        )

    # Concrete counterexample: V9 makes horizontal trivia semantically active because the
    # high-priority dotted token consumes `Needle.owns` when whitespace precedes `(`.
    call_tight = "rule Needle.owns(X)\n"
    call_spaced = "rule Needle.owns (X)\n"
    v9_tight = compile_semantic(call_tight, g9, strict=strict)
    v9_spaced = compile_semantic(call_spaced, g9, strict=strict)
    v17_tight = compile_semantic(call_tight, g17, strict=strict)
    v17_spaced = compile_semantic(call_spaced, g17, strict=strict)
    check(
        "v9_counterexample_reproduced",
        v9_tight[0] and v9_spaced[0] and v9_tight[1] != v9_spaced[1],
        tight_hash=v9_tight[1],
        spaced_hash=v9_spaced[1],
        tight_error=v9_tight[2],
        spaced_error=v9_spaced[2],
    )
    check(
        "v17_call_horizontal_trivia_equivalence",
        v17_tight[0] and v17_spaced[0] and v17_tight[1] == v17_spaced[1],
        tight_hash=v17_tight[1],
        spaced_hash=v17_spaced[1],
        tight_error=v17_tight[2],
        spaced_error=v17_spaced[2],
    )

    # Preserve the V5/V6 repair obligations.
    fixtures = [
        ("bare_owns_operand", "rule 4B_need_not_learn Needle.owns\n", True),
        ("bare_lowers_rejected", "rule Needle.lowers\n", False),
        ("dotted_owns_relation", "rule Needle.owns X\n", True),
        ("dotted_lowers_relation", "rule Needle.lowers X\n", True),
        ("dotted_owns_comment_not_rhs", "rule Needle.owns // comment\n", True),
        ("dotted_lowers_call_form_rejected", "rule Needle.lowers (X)\n", False),
    ]
    for name, source, expected in fixtures:
        observed, err = parse_ok(parser17, source)
        check(name, observed is expected, expected_accept=expected, observed_accept=observed, error=err)

    # Ensure semantic identity for ordinary declarative examples not involving the repaired
    # token, catching accidental grammar edits outside the one-line delta.
    ordinary = [
        "module clay.demo\nlaw residual>=0\n",
        "record X { a:Int; b:Ref? }\n",
        "needle f(x:Int)->Result<Int|Error>\n",
        "rule external_effect lifecycle=[REQUESTED,AUTHORIZED,DONE]\n",
    ]
    for i, source in enumerate(ordinary, 1):
        a = compile_semantic(source, g9, strict=strict)
        b = compile_semantic(source, g17, strict=strict)
        check(f"ordinary_semantic_equivalence_{i}", a[0] and b[0] and a[1] == b[1], v9=a[1], v17=b[1], v9_error=a[2], v17_error=b[2])

    # Record scaling evidence; do not make wall-clock thresholds a semantic gate.
    timings = []
    for n in (10, 100, 1000, 5000, 10000, 40000):
        src = "rule Needle.owns" + (" " * n) + "X\n"
        t0 = time.perf_counter()
        ok, err = parse_ok(parser17, src)
        dt = time.perf_counter() - t0
        timings.append({"spaces": n, "seconds": dt, "accepted": ok, "error": err})
        check(f"scaling_accept_{n}", ok, seconds=dt, error=err)

    failed = [row["name"] for row in checks if not row["pass"]]
    passed = not failed
    out = {
        "schema_version": "1.1",
        "experiment": "CC-WP02 V17 minimal declarative trivia repair discriminator",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": __import__("platform").python_version(), "lark": version("lark"), "interegular": version("interegular"), "strict": strict},
        "baseline": {"path": str(V9.relative_to(ROOT)), "sha256": sha(V9)},
        "candidate": {"path": str(V17.relative_to(ROOT)), "sha256": sha(V17)},
        "checks": checks,
        "failed_checks": failed,
        "timings": timings,
        "pass": passed,
        "v9_counterexample_confirmed": next((x["pass"] for x in checks if x["name"] == "v9_counterexample_reproduced"), False),
        "counts_as_wp02_pass": passed and strict,
        "promotion_allowed": passed and strict,
        "scope_guard": "A strict PASS proves only the minimal V9->V17 declarative trivia repair and current admitted declarative corpus equivalence. It does not merge the V7 typed-fn surface and does not imply target/application/FULL_FRANK/WP14 acceptance.",
        "authority_invariant": "model output != execution authority",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": passed, "strict": strict, "failed_checks": failed, "output": display_path(args.output)}, ensure_ascii=False))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
