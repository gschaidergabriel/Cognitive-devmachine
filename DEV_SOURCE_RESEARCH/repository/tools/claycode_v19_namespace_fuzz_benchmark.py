#!/usr/bin/env python3
"""Supplemental adversarial namespace fuzz for the canonical ClayCode V19 candidate.

This deliberately reuses the earlier concurrent V19 grammar and normalization probe instead
of creating a second V19 truth. It tests the specific defect that refuted V18: high-priority
special terminals stealing longer valid qid prefixes. PASS is research evidence only.
"""
from __future__ import annotations

import json
import os
import platform
import random
import resource
import statistics
import string
import time
from datetime import datetime, timezone

import claycode_v19_delimiter_normalization_probe as base

SEED = 20260810
SUFFIXES_PER_PREFIX = 256
REPS = 5


def suffixes(n: int) -> list[str]:
    rng = random.Random(SEED)
    chars = string.ascii_letters + string.digits + "_-"
    out = {"X", "2", "_more", "hip", "-more", "A", "0", "99"}
    while len(out) < n:
        out.add("".join(rng.choice(chars) for _ in range(rng.randint(1, 8))))
    return sorted(out)


def q(values: list[float], p: float) -> float:
    xs = sorted(values)
    pos = (len(xs) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def canonical_hash(tree, *, v19: bool) -> str:
    return base.semantic_hash(base.canonical(tree, v19=v19))


def benchmark(parser, corpus: list[str], *, v19: bool) -> dict:
    for source in corpus[:32]:
        canonical_hash(parser.parse(source), v19=v19)
    samples = []
    rng = random.Random(424242)
    order = list(corpus)
    for _ in range(REPS):
        rng.shuffle(order)
        for source in order:
            t0 = time.perf_counter_ns()
            canonical_hash(parser.parse(source), v19=v19)
            samples.append((time.perf_counter_ns() - t0) / 1_000_000)
    return {
        "n": len(samples),
        "mean_ms": statistics.fmean(samples),
        "p50_ms": q(samples, 0.50),
        "p90_ms": q(samples, 0.90),
        "p95_ms": q(samples, 0.95),
        "p99_ms": q(samples, 0.99),
        "min_ms": min(samples),
        "max_ms": max(samples),
    }


def main() -> int:
    g17 = base.V17.read_text(encoding="utf-8")
    g19 = base.V19.read_text(encoding="utf-8")
    # Strict construction is intentionally mandatory; missing interegular is a red result.
    p17 = base.parser(g17, strict=True)
    p19 = base.parser(g19, strict=True)

    ss = suffixes(SUFFIXES_PER_PREFIX)
    corpus = [f"rule Needle.owns{s}\n" for s in ss]
    corpus += [f"rule Needle.lowers{s}\n" for s in ss]

    rows = []
    for source in corpus:
        ok17, e17, t17 = base.parse_ok(p17, source)
        ok19, e19, t19 = base.parse_ok(p19, source)
        equal = False
        if ok17 and ok19 and t17 is not None and t19 is not None:
            equal = canonical_hash(t17, v19=False) == canonical_hash(t19, v19=True)
        rows.append({
            "source": source.strip(),
            "v17_accept": ok17,
            "v19_accept": ok19,
            "normalized_semantic_equal": equal,
            "v17_error": e17,
            "v19_error": e19,
            "pass": ok17 and ok19 and equal,
        })

    rejects = [r["source"] for r in rows if not r["v19_accept"]]
    drifts = [r["source"] for r in rows if r["v17_accept"] and r["v19_accept"] and not r["normalized_semantic_equal"]]
    baseline_failures = [r["source"] for r in rows if not r["v17_accept"]]
    perf17 = benchmark(p17, corpus, v19=False)
    perf19 = benchmark(p19, corpus, v19=True)

    passed = all(r["pass"] for r in rows)
    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode V19 namespace fuzz + performance shadow",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "EXECUTABLE_RESEARCH_DISCRIMINATOR",
        "runtime": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "lark": base.pkg("lark"),
            "interegular": base.pkg("interegular"),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "inputs": {
            "v17_path": str(base.V17.relative_to(base.ROOT)),
            "v17_sha256": base.sha(g17.encode("utf-8")),
            "v19_path": str(base.V19.relative_to(base.ROOT)),
            "v19_sha256": base.sha(g19.encode("utf-8")),
            "seed": SEED,
            "suffixes_per_prefix": SUFFIXES_PER_PREFIX,
            "total_cases": len(rows),
        },
        "result": {
            "baseline_v17_reject_count": len(baseline_failures),
            "v19_reject_count": len(rejects),
            "v19_normalized_semantic_drift_count": len(drifts),
            "v19_reject_examples": rejects[:20],
            "v19_drift_examples": drifts[:20],
        },
        "performance_parse_plus_canonical_hash": {"v17": perf17, "v19": perf19},
        "pass": passed,
        "promotion": "NONE",
        "architecture_delta": "SUPPORTED_FUZZ_SHADOW_KEEP_V17_SELECTED" if passed else "V19_COUNTEREVIDENCE_KEEP_V17_SELECTED",
        "scope_guard": "PASS covers only this deterministic 512-case namespace family and matched runtime. It does not select V19, close WP02/WP03, prove downstream typed-IR/type-effect semantics, or replace registered Andreas Ubuntu acceptance.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
