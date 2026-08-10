#!/usr/bin/env python3
"""Adversarial shadow validation for ClayCode BASE D V19 delimiter-bound no-lookahead.

Research-only. V17 remains the selected production frontend. V19 exists to test whether
we can remove V17's regex lookahead without V18's reserved-prefix namespace shadow.

PASS requires all of the following on exact bytes:
- strict=True construction for both V17 and V19 (therefore interegular must exist),
- V19 contains no regex lookaround,
- current G9 V3 + Dialect V3 semantic hashes equal V17 after parser-only normalization,
- exact call/relation/bare-qid controls preserve V17 accept/reject + AST/v1 semantics,
- 512 deterministic qid-prefix fuzz cases preserve V17 acceptance + AST/v1 semantics,
- V19 remains a shadow candidate only; no production selection or CC-WP promotion.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import random
import resource
import statistics
import string
import time
from datetime import datetime, timezone
from pathlib import Path

from lark import Token, Tree

import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
V19 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V19_DELIMITED_NO_LOOKAHEAD.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def semantic_hash(tree: Tree) -> str:
    ast = front.canonical_node(tree)
    return sha(front.DOMAIN + front.canonical_bytes(ast))


def normalize_v19(node):
    """Map V19 parser-only delimiter consumption back to the V17 AST/v1 contract."""
    if isinstance(node, Tree):
        kind = str(node.data)
        if kind == "special_owns_call":
            # V19's first token consumes `Needle.owns` + horizontal trivia + `(`.
            # Reconstruct the exact V17 qid + LPAR shape; the remaining children
            # already include arguments/commas and the closing RPAR.
            qid = Tree("qid", [Token("NAME", "Needle"), Token("DOT", "."), Token("NAME", "owns")])
            lpar = Token("LPAR", "(")
            return Tree("call", [qid, lpar, *[normalize_v19(x) for x in node.children[1:]]])
        return Tree(node.data, [normalize_v19(x) for x in node.children])
    if isinstance(node, Token) and node.type in {"NEEDLE_OWNS_REL", "NEEDLE_LOWERS_REL"}:
        # V19 deliberately consumes relation-disambiguating horizontal trivia.
        # V17's lookahead token does not consume it, so strip only that trivia.
        return Token("DOTTED_PREFIX_REL", str(node).rstrip(" \t"))
    return node


def parse_state(parser, source: str) -> tuple[bool, str | None, Tree | None]:
    try:
        tree = parser.parse(source)
        return True, None, tree
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}", None


def compare_case(p17, p19, source: str, expected_accept: bool) -> dict:
    ok17, err17, t17 = parse_state(p17, source)
    ok19, err19, t19 = parse_state(p19, source)
    sem_equal = None
    if ok17 and ok19 and t17 is not None and t19 is not None:
        sem_equal = semantic_hash(t17) == semantic_hash(normalize_v19(t19))
    return {
        "source": source,
        "expected_accept": expected_accept,
        "v17_accept": ok17,
        "v19_accept": ok19,
        "v17_error": err17,
        "v19_error": err19,
        "semantic_equal_if_accepted": sem_equal,
        "pass": ok17 == expected_accept and ok19 == expected_accept and (sem_equal is not False),
    }


def deterministic_suffixes(n: int = 256) -> list[str]:
    rng = random.Random(20260810)
    chars = string.ascii_letters + string.digits + "_-"
    out = {"X", "2", "_more", "hip", "-more", "A", "0", "99"}
    while len(out) < n:
        size = rng.randint(1, 8)
        out.add("".join(rng.choice(chars) for _ in range(size)))
    return sorted(out)


def quantile(values: list[float], q: float) -> float:
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def benchmark(parser, normalize, corpus: list[str], reps: int = 5) -> dict:
    # Warmup is explicit and excluded.
    for source in corpus[:32]:
        semantic_hash(normalize(parser.parse(source)))
    samples_ms = []
    order = list(corpus)
    rng = random.Random(424242)
    for _ in range(reps):
        rng.shuffle(order)
        for source in order:
            t0 = time.perf_counter_ns()
            semantic_hash(normalize(parser.parse(source)))
            samples_ms.append((time.perf_counter_ns() - t0) / 1_000_000)
    return {
        "n": len(samples_ms),
        "mean_ms": statistics.fmean(samples_ms),
        "p50_ms": quantile(samples_ms, 0.50),
        "p90_ms": quantile(samples_ms, 0.90),
        "p95_ms": quantile(samples_ms, 0.95),
        "p99_ms": quantile(samples_ms, 0.99),
        "min_ms": min(samples_ms),
        "max_ms": max(samples_ms),
    }


def main() -> int:
    g17 = V17.read_text(encoding="utf-8")
    g19 = V19.read_text(encoding="utf-8")

    lookaround = "(?=" in g19 or "(?<=" in g19 or "(?!" in g19 or "(?<!" in g19

    # Strict is mandatory. Missing interegular or any grammar/regex collision is a red result.
    try:
        p17 = front.build_parser(g17, strict=True)
        p19 = front.build_parser(g19, strict=True)
        strict_ok = True
        strict_error = None
    except Exception as exc:
        out = {
            "schema_version": "1.0",
            "experiment": "ClayCode BASE D V19 delimiter-bound no-lookahead shadow differential",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "strict_ok": False,
            "strict_error": f"{type(exc).__name__}: {exc}",
            "v17_grammar_sha256": sha(g17.encode("utf-8")),
            "v19_grammar_sha256": sha(g19.encode("utf-8")),
            "v19_regex_lookaround_present": lookaround,
            "promotion": "NONE",
            "pass": False,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    source_rows = []
    for path in SOURCES:
        text = path.read_text(encoding="utf-8")
        t17 = p17.parse(text)
        t19 = normalize_v19(p19.parse(text))
        h17 = semantic_hash(t17)
        h19 = semantic_hash(t19)
        source_rows.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha(text.encode("utf-8")),
            "v17_semantic_hash": h17,
            "v19_normalized_semantic_hash": h19,
            "semantic_equal": h17 == h19,
            "v17_tree_nodes": sum(1 for _ in t17.iter_subtrees()),
            "v19_normalized_tree_nodes": sum(1 for _ in t19.iter_subtrees()),
        })

    accepted_controls = [
        "rule Needle.owns(X)\n",
        "rule Needle.owns (X)\n",
        "rule Needle.owns\t(X)\n",
        "rule Needle.owns \t (X)\n",
        "rule Needle.owns X\n",
        "rule Needle.owns\tX\n",
        "rule Needle.lowers X\n",
        "rule Needle.lowers\tX\n",
        "rule 4B_need_not_learn Needle.owns\n",
        "rule Needle.owns.foo\n",
        "rule Needle.owns.foo()\n",
        "rule Needle.owns?\n",
        "rule Needle.ownership\n",
        "rule Needle.owns_extra\n",
        "rule Needle.lowers_more\n",
    ]
    rejected_controls = [
        "rule Needle.lowers\n",
        "rule Needle.lowers(X)\n",
        "rule Needle.lowers (X)\n",
        "rule Needle.lowers\t(X)\n",
    ]
    controls = [compare_case(p17, p19, x, True) for x in accepted_controls]
    controls += [compare_case(p17, p19, x, False) for x in rejected_controls]

    suffixes = deterministic_suffixes(256)
    fuzz_sources = [f"rule Needle.owns{s}\n" for s in suffixes]
    fuzz_sources += [f"rule Needle.lowers{s}\n" for s in suffixes]
    fuzz_rows = [compare_case(p17, p19, source, True) for source in fuzz_sources]
    fuzz_rejects = [x["source"].strip() for x in fuzz_rows if not x["v19_accept"]]
    fuzz_semantic_drifts = [
        x["source"].strip()
        for x in fuzz_rows
        if x["v17_accept"] and x["v19_accept"] and x["semantic_equal_if_accepted"] is False
    ]

    bench17 = benchmark(p17, lambda x: x, fuzz_sources)
    bench19 = benchmark(p19, normalize_v19, fuzz_sources)

    passed = (
        strict_ok
        and not lookaround
        and all(x["semantic_equal"] for x in source_rows)
        and all(x["pass"] for x in controls)
        and all(x["pass"] for x in fuzz_rows)
        and not fuzz_rejects
        and not fuzz_semantic_drifts
    )

    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE D V19 delimiter-bound no-lookahead shadow differential",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "lark_version": pkg("lark"),
            "interegular_version": pkg("interegular"),
            "parser": "lalr/contextual",
            "strict": True,
            "maybe_placeholders": False,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "strict_ok": strict_ok,
        "strict_error": strict_error,
        "v17_grammar_sha256": sha(g17.encode("utf-8")),
        "v19_grammar_sha256": sha(g19.encode("utf-8")),
        "v19_regex_lookaround_present": lookaround,
        "sources": source_rows,
        "controls": controls,
        "namespace_fuzz": {
            "seed": 20260810,
            "suffix_count_per_reserved_prefix": len(suffixes),
            "total_cases": len(fuzz_rows),
            "v19_reject_count": len(fuzz_rejects),
            "v19_semantic_drift_count": len(fuzz_semantic_drifts),
            "reject_examples": fuzz_rejects[:20],
            "semantic_drift_examples": fuzz_semantic_drifts[:20],
        },
        "performance_shadow_parse_plus_semantic_hash": {
            "v17": bench17,
            "v19": bench19,
            "gate": "RECORDED_NOT_PROMOTION_SCALAR",
        },
        "pass": passed,
        "selection_status": "RESEARCH_CANDIDATE_ONLY",
        "architecture_delta": (
            "SUPPORTED_SHADOW_CANDIDATE_KEEP_V17_SELECTED"
            if passed
            else "REFUTED_OR_UNRESOLVED_KEEP_V17_SELECTED"
        ),
        "scope_guard": (
            "PASS supports only V19 as a bounded no-lookahead shadow candidate that preserves V17 AST/v1 semantics on current G9/Dialect plus the declared namespace/call/relation corpus. "
            "It does not select V19, close CC-WP-02/03, prove typed IR/type-effect semantics, replace registered Andreas Ubuntu evidence, or authorize Frank Harness changes."
        ),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
