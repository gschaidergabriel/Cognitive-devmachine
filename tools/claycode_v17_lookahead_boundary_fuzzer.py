#!/usr/bin/env python3
"""Adversarial metamorphic replication for the ClayCode BASE-D V17 lookahead boundary.

This is intentionally independent of the CC-WP-02 canonicalizer implementation lane.
It tests the one V17 mechanism whose regex lookahead is not fully covered by ordinary
strict-regex collision analysis: DOTTED_PREFIX_REL.

No result from this probe closes CC-WP-02 or authorizes a grammar change.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import claycode_base_frontend as front  # noqa: E402

V9 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark"
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
DEFAULT_OUT = ROOT / "research_entity/claycode/base/receipts/CC_WP02_V17_LOOKAHEAD_ADVERSARIAL.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def q(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    i = min(len(s) - 1, max(0, round((len(s) - 1) * p)))
    return s[i]


def tree_contains(node: Any, *, kind: str | None = None, token: str | None = None) -> bool:
    if isinstance(node, dict):
        if kind is not None and node.get("kind") == kind:
            return True
        if token is not None and node.get("token") == token:
            return True
        return any(tree_contains(v, kind=kind, token=token) for v in node.values())
    if isinstance(node, list):
        return any(tree_contains(v, kind=kind, token=token) for v in node)
    return False


def compile_case(source: str, parser: Any) -> tuple[dict[str, Any] | None, str | None, int]:
    started = time.perf_counter_ns()
    try:
        tree = parser.parse(source)
        ast = front.canonical_node(tree)
        semantic_hash = sha256_bytes(front.DOMAIN + front.canonical_bytes(ast))
        return {"canonical_ast": ast, "semantic_hash": semantic_hash}, None, time.perf_counter_ns() - started
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}", time.perf_counter_ns() - started


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1729)
    ap.add_argument("--prefix-cases", type=int, default=768)
    ap.add_argument("--call-cases", type=int, default=384)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    g9 = V9.read_text(encoding="utf-8")
    g17 = V17.read_text(encoding="utf-8")
    parser9 = front.build_parser(g9, strict=True)
    parser17 = front.build_parser(g17, strict=True)
    rng = random.Random(args.seed)
    failures: list[dict[str, Any]] = []
    durations_ms: list[float] = []

    def fail(kind: str, **detail: Any) -> None:
        if len(failures) < 50:
            failures.append({"kind": kind, **detail})

    # Baseline lesion/rescue: reproduce the V9 horizontal-trivia bug, then require V17 rescue.
    tight = "rule Needle.owns(X)\n"
    spaced = "rule Needle.owns (X)\n"
    v9_t, e9t, d = compile_case(tight, parser9); durations_ms.append(d / 1e6)
    v9_s, e9s, d = compile_case(spaced, parser9); durations_ms.append(d / 1e6)
    v17_t, e17t, d = compile_case(tight, parser17); durations_ms.append(d / 1e6)
    v17_s, e17s, d = compile_case(spaced, parser17); durations_ms.append(d / 1e6)
    v9_bug = bool(v9_t and v9_s and v9_t["semantic_hash"] != v9_s["semantic_hash"])
    v17_rescue = bool(v17_t and v17_s and v17_t["semantic_hash"] == v17_s["semantic_hash"])
    if not v9_bug:
        fail("V9_COUNTEREXAMPLE_NOT_REPRODUCED", tight_error=e9t, spaced_error=e9s)
    if not v17_rescue:
        fail("V17_RESCUE_FAILED", tight_error=e17t, spaced_error=e17s)

    rhs_pool = ["X", "@a/b", "1", "\"x\"", "true", "[X]", "{X}", "f(X)"]
    rel_pool = ["Needle.owns", "Needle.lowers"]

    # Metamorphic prefix family: any nonempty run of grammar-admitted horizontal trivia
    # before a valid RHS must preserve the dotted-prefix relation classification.
    for i in range(args.prefix_cases):
        rel = rng.choice(rel_pool)
        rhs = rng.choice(rhs_pool)
        n = rng.randint(1, 64)
        ws = "".join(rng.choice((" ", "\t")) for _ in range(n))
        source = f"rule {rel}{ws}{rhs}\n"
        row, err, d = compile_case(source, parser17)
        durations_ms.append(d / 1e6)
        ok = bool(
            row
            and tree_contains(row["canonical_ast"], kind="prefix_relation")
            and tree_contains(row["canonical_ast"], token="DOTTED_PREFIX_REL")
        )
        if not ok:
            fail("PREFIX_BOUNDARY", index=i, relation=rel, rhs=rhs, whitespace_repr=repr(ws), error=err)

    # Metamorphic call family: horizontal trivia immediately before '(' is presentation
    # trivia for the admitted Needle.owns call and must not turn into DOTTED_PREFIX_REL.
    tight_hash = v17_t["semantic_hash"] if v17_t else None
    for i in range(args.call_cases):
        n = rng.randint(1, 64)
        ws = "".join(rng.choice((" ", "\t")) for _ in range(n))
        source = f"rule Needle.owns{ws}(X)\n"
        row, err, d = compile_case(source, parser17)
        durations_ms.append(d / 1e6)
        ok = bool(
            row
            and row["semantic_hash"] == tight_hash
            and tree_contains(row["canonical_ast"], kind="call")
            and not tree_contains(row["canonical_ast"], token="DOTTED_PREFIX_REL")
        )
        if not ok:
            fail("CALL_TRIVIA_BOUNDARY", index=i, whitespace_repr=repr(ws), error=err,
                 observed_hash=row["semantic_hash"] if row else None, expected_hash=tight_hash)

    # Excluded-start boundaries in the regex lookahead.
    boundary_cases = [
        ("owns_comment_equivalence", "rule Needle.owns\n", "rule Needle.owns // c\n", True),
        ("owns_call_equivalence", tight, "rule Needle.owns\t\t(X)\n", True),
    ]
    boundary_results = []
    for name, left, right, expect_same in boundary_cases:
        l, le, d = compile_case(left, parser17); durations_ms.append(d / 1e6)
        r, re, d = compile_case(right, parser17); durations_ms.append(d / 1e6)
        observed_same = bool(l and r and l["semantic_hash"] == r["semantic_hash"])
        passed = observed_same == expect_same
        boundary_results.append({
            "name": name, "pass": passed, "expected_same": expect_same,
            "observed_same": observed_same, "left_error": le, "right_error": re,
        })
        if not passed:
            fail("EXCLUDED_START_BOUNDARY", name=name, left_error=le, right_error=re)

    # Mutation discrimination: the relation label itself must remain semantically visible.
    owns, oe, d = compile_case("rule Needle.owns X\n", parser17); durations_ms.append(d / 1e6)
    lowers, le, d = compile_case("rule Needle.lowers X\n", parser17); durations_ms.append(d / 1e6)
    mutation_discriminated = bool(owns and lowers and owns["semantic_hash"] != lowers["semantic_hash"])
    if not mutation_discriminated:
        fail("RELATION_MUTATION_NOT_DISCRIMINATED", owns_error=oe, lowers_error=le)

    total = 4 + args.prefix_cases + args.call_cases + 2 * len(boundary_cases) + 2
    passed = not failures
    receipt = {
        "schema_version": "1.0",
        "experiment": "CC-WP02 V17 lookahead-boundary adversarial metamorphic replication",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "V17 can hide a semantic boundary instability behind a lookahead terminal even when strict LALR construction succeeds.",
        "counterhypothesis": "The V17 minimal repair is stable; bounded metamorphic boundary expansion finds no new semantic failure beyond the known V9 counterexample.",
        "baseline": {
            "v9_path": str(V9.relative_to(ROOT)),
            "v9_sha256": sha256_bytes(g9.encode("utf-8")),
            "known_counterexample_reproduced": v9_bug,
        },
        "candidate": {
            "v17_path": str(V17.relative_to(ROOT)),
            "v17_sha256": sha256_bytes(g17.encode("utf-8")),
            "known_counterexample_rescued": v17_rescue,
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "lark": version("lark"),
            "interegular": version("interegular"),
            "strict": True,
            "github_sha": os.getenv("GITHUB_SHA"),
            "runner_name": os.getenv("RUNNER_NAME"),
            "runner_os": os.getenv("RUNNER_OS"),
            "runner_arch": os.getenv("RUNNER_ARCH"),
        },
        "seed": args.seed,
        "case_counts": {
            "prefix": args.prefix_cases,
            "call": args.call_cases,
            "boundary_pairs": len(boundary_cases),
            "total_compile_attempts": total,
        },
        "boundary_results": boundary_results,
        "relation_mutation_discriminated": mutation_discriminated,
        "timing_ms": {
            "n": len(durations_ms),
            "mean": statistics.fmean(durations_ms) if durations_ms else None,
            "p50": q(durations_ms, 0.50),
            "p95": q(durations_ms, 0.95),
            "p99": q(durations_ms, 0.99),
            "max": max(durations_ms) if durations_ms else None,
        },
        "failures": failures,
        "pass": passed,
        "result_class": "NO_NEW_FAILURE_FOUND" if passed else "COUNTEREXAMPLE_FOUND",
        "promotion_allowed": False,
        "counts_as_wp02_pass": False,
        "scope_guard": "Independent adversarial replication of the V17 regex-lookahead boundary only. It neither edits nor promotes the grammar/canonicalizer and cannot substitute for WP02 target-host or full BASE acceptance.",
        "authority_invariant": "model output != execution authority",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "pass": passed,
        "result_class": receipt["result_class"],
        "failures": len(failures),
        "cases": total,
        "output": str(args.output),
    }, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
