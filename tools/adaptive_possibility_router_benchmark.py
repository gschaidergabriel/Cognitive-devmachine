#!/usr/bin/env python3
from __future__ import annotations

"""Same-corpus differential for Clay's adaptive possibility-channel router.

Compares:
1. SQLite FTS5/BM25 flat baseline,
2. current always-on possibility preprocessor,
3. adaptive internal routing over the same preprocessor.

This benchmark uses the repository's source-grounded possibility cases. It tests retrieval
quality and component latency only; it is not a universal database benchmark and not a
live-FRANK outcome test.
"""

import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rae_core import possibility_preprocessor as base  # noqa: E402
from rae_core import adaptive_possibility_router as adaptive  # noqa: E402


def percentile(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    ys = sorted(xs)
    pos = (len(ys) - 1) * p
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ys[lo]
    return ys[lo] * (hi - pos) + ys[hi] * (pos - lo)


def retrieval_metrics(got: list[str], expected: list[str], k: int) -> dict[str, float]:
    got = list(dict.fromkeys(got))[:k]
    truth = set(expected)
    hits = [1 if x in truth else 0 for x in got]
    tp = sum(hits)
    precision = tp / k if k else 0.0
    recall = tp / len(truth) if truth else 1.0
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    rr = 0.0
    for i, h in enumerate(hits, 1):
        if h:
            rr = 1.0 / i
            break
    dcg = sum(h / math.log2(i + 1) for i, h in enumerate(hits, 1))
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(k, len(truth)) + 1))
    return {
        "precision_at_k": precision,
        "recall_at_k": recall,
        "f1_at_k": f1,
        "mrr": rr,
        "ndcg_at_k": dcg / ideal if ideal else 1.0,
    }


def time_mode(fn: Callable[[], list[str]], repeats: int) -> tuple[list[str], dict[str, Any]]:
    for _ in range(2):
        fn()
    latencies: list[float] = []
    got: list[str] = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        got = fn()
        latencies.append((time.perf_counter_ns() - t0) / 1e6)
    return got, {
        "n": len(latencies),
        "p50_ms": percentile(latencies, 0.50),
        "p95_ms": percentile(latencies, 0.95),
        "p99_ms": percentile(latencies, 0.99),
        "mean_ms": statistics.fmean(latencies),
    }


def mean(rows: list[dict[str, float]], key: str) -> float:
    return statistics.fmean(x[key] for x in rows)


def run(cases: list[dict[str, Any]], repeats: int) -> dict[str, Any]:
    details = []
    aggregate_quality: dict[str, list[dict[str, float]]] = {
        "sqlite_bm25": [], "always_on": [], "adaptive": []
    }
    aggregate_latency: dict[str, list[float]] = {
        "sqlite_bm25": [], "always_on": [], "adaptive": []
    }
    route_counts = {"FULL": 0, "FAST": 0}

    for case in cases:
        query = str(case["query"])
        limit = int(case.get("limit", 5))
        expected = list(case.get("expected_claim_ids", []))
        experiment = case.get("experiment")
        packet = case.get("packet")

        def flat() -> list[str]:
            return [r["claim_id"] for r in base.bm25_claims(query, limit=limit)]

        def full() -> list[str]:
            return [r["claim_id"] for r in base.assemble_claims(
                query, limit=limit, experiment=experiment, packet=packet,
                counterevidence_reserve=True,
            )["selected"]]

        def adapt() -> list[str]:
            return [r["claim_id"] for r in adaptive.assemble_claims_adaptive(
                query, limit=limit, experiment=experiment, packet=packet,
                counterevidence_reserve=True,
            )["selected"]]

        row: dict[str, Any] = {
            "id": case["id"], "query": query, "expected": expected,
            "contrastive": bool(case.get("contrastive")),
        }
        for name, fn in (("sqlite_bm25", flat), ("always_on", full), ("adaptive", adapt)):
            got, timing = time_mode(fn, repeats)
            quality = retrieval_metrics(got, expected, limit)
            aggregate_quality[name].append(quality)
            aggregate_latency[name].extend(timing["p50_ms"] for _ in range(1))
            row[name] = {"got": got, "quality": quality, "latency": timing}
        decision = adaptive.route_decision(query, experiment=experiment, packet=packet)
        route_counts[decision["route"]] += 1
        row["adaptive_route"] = decision
        details.append(row)

    summary: dict[str, Any] = {}
    for name in ("sqlite_bm25", "always_on", "adaptive"):
        q = aggregate_quality[name]
        case_p50 = [r[name]["latency"]["p50_ms"] for r in details]
        case_p95 = [r[name]["latency"]["p95_ms"] for r in details]
        summary[name] = {
            "mean_precision_at_k": mean(q, "precision_at_k"),
            "mean_recall_at_k": mean(q, "recall_at_k"),
            "mean_f1_at_k": mean(q, "f1_at_k"),
            "mean_mrr": mean(q, "mrr"),
            "mean_ndcg_at_k": mean(q, "ndcg_at_k"),
            "median_case_p50_ms": statistics.median(case_p50),
            "p95_of_case_p50_ms": percentile(case_p50, 0.95),
            "median_case_p95_ms": statistics.median(case_p95),
        }

    full = summary["always_on"]
    cand = summary["adaptive"]
    quality_keys = ("mean_precision_at_k", "mean_recall_at_k", "mean_f1_at_k", "mean_mrr", "mean_ndcg_at_k")
    quality_non_degraded = all(cand[k] + 1e-12 >= full[k] for k in quality_keys)
    quality_exact = all(abs(cand[k] - full[k]) <= 1e-12 for k in quality_keys)
    latency_improved = cand["median_case_p50_ms"] < full["median_case_p50_ms"]

    return {
        "schema": "clay.adaptive-possibility-router.benchmark.v0.1",
        "benchmark_class": "CLAY_SELF_USE_SOURCE_GROUNDED_DIFFERENTIAL",
        "cases": len(cases),
        "repeats_per_case": repeats,
        "route_counts": route_counts,
        "summary": summary,
        "adaptive_vs_always_on": {
            "quality_non_degraded": quality_non_degraded,
            "quality_exact": quality_exact,
            "median_case_p50_delta_ms": cand["median_case_p50_ms"] - full["median_case_p50_ms"],
            "p95_of_case_p50_delta_ms": cand["p95_of_case_p50_ms"] - full["p95_of_case_p50_ms"],
            "latency_improved": latency_improved,
            "promote_candidate_on_this_suite": quality_non_degraded and latency_improved,
        },
        "rows": details,
        "limitations": [
            "Repository claim cases are source-grounded but small and project-internal.",
            "This is not independent evidence of superiority over every database or retriever.",
            "Routing terms are model-authored and can overfit the current suite; held-out/OOD queries are required.",
            "Component retrieval quality is not downstream answer quality.",
            "Runner/cache/filesystem state can materially affect latency; preserve execution metadata in CI.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(ROOT / "benchmarks" / "possibility_preprocessor" / "cases.json"))
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--output")
    args = ap.parse_args()
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    result = run(cases, max(1, min(args.repeat, 20)))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
