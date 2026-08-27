#!/usr/bin/env python3
from __future__ import annotations

"""Benchmark the possibility-conditioned preprocessor against fair retrieval baselines.

This is a Clay self-use engineering proxy. It is not evidence that one storage engine is
universally better than another and it is not live-FRANK cognitive performance.
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

from rae_core import possibility_preprocessor as pp  # noqa: E402
from rae_core.cli import query_db  # noqa: E402


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    return xs[min(len(xs) - 1, max(0, math.ceil(0.95 * len(xs)) - 1))]


def score(got: list[str], expected: list[str]) -> dict[str, float]:
    gs = list(dict.fromkeys(got))
    es = set(expected)
    tp = len(set(gs) & es)
    precision = tp / len(gs) if gs else (1.0 if not es else 0.0)
    recall = tp / len(es) if es else 1.0
    rr = 0.0
    for i, cid in enumerate(gs, 1):
        if cid in es:
            rr = 1.0 / i
            break
    dcg = 0.0
    for i, cid in enumerate(gs, 1):
        if cid in es:
            dcg += 1.0 / math.log2(i + 1)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(es), len(gs)) + 1))
    ndcg = dcg / ideal if ideal else 1.0
    return {"precision": precision, "recall": recall, "mrr": rr, "ndcg": ndcg}


def run_mode(fn: Callable[[], list[str]], repeat: int) -> tuple[list[str], dict[str, float]]:
    lat: list[float] = []
    got: list[str] = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        got = fn()
        lat.append((time.perf_counter() - t0) * 1000)
    return got, {
        "median_ms": round(statistics.median(lat), 3),
        "p95_ms": round(p95(lat), 3),
        "runs_ms": [round(x, 3) for x in lat],
    }


def benchmark(cases: list[dict[str, Any]], repeat: int) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    modes = ["sqlite_bm25", "legacy_hybrid", "possibility_lesion", "possibility_counterevidence"]

    for case in cases:
        query = case["query"]
        limit = int(case.get("limit", 5))
        expected = list(case.get("expected_claim_ids", []))
        per_mode: dict[str, Any] = {}

        got, timing = run_mode(
            lambda: [r["claim_id"] for r in pp.bm25_claims(query, limit=limit)], repeat
        )
        per_mode["sqlite_bm25"] = {**score(got, expected), "got": got, "latency": timing}

        got, timing = run_mode(
            lambda: [r["claim_id"] for r in query_db(
                query,
                limit=limit,
                experiment=case.get("experiment"),
                packet=case.get("packet"),
            )["claims"]], repeat
        )
        per_mode["legacy_hybrid"] = {**score(got, expected), "got": got, "latency": timing}

        got, timing = run_mode(
            lambda: [r["claim_id"] for r in pp.assemble_claims(
                query,
                limit=limit,
                experiment=case.get("experiment"),
                packet=case.get("packet"),
                counterevidence_reserve=False,
            )["selected"]], repeat
        )
        per_mode["possibility_lesion"] = {**score(got, expected), "got": got, "latency": timing}

        got, timing = run_mode(
            lambda: [r["claim_id"] for r in pp.assemble_claims(
                query,
                limit=limit,
                experiment=case.get("experiment"),
                packet=case.get("packet"),
                counterevidence_reserve=True,
            )["selected"]], repeat
        )
        per_mode["possibility_counterevidence"] = {**score(got, expected), "got": got, "latency": timing}
        rows.append({
            "id": case["id"],
            "query": query,
            "expected": expected,
            "contrastive": bool(case.get("contrastive")),
            "modes": per_mode,
        })

    summary: dict[str, Any] = {}
    for mode in modes:
        selected = [r["modes"][mode] for r in rows]
        summary[mode] = {
            "mean_precision_at_k": round(statistics.mean(x["precision"] for x in selected), 4),
            "mean_recall_at_k": round(statistics.mean(x["recall"] for x in selected), 4),
            "mean_mrr": round(statistics.mean(x["mrr"] for x in selected), 4),
            "mean_ndcg": round(statistics.mean(x["ndcg"] for x in selected), 4),
            "median_case_latency_ms": round(statistics.median(x["latency"]["median_ms"] for x in selected), 3),
            "p95_case_median_latency_ms": round(p95([x["latency"]["median_ms"] for x in selected]), 3),
        }

    contrast_rows = [r for r in rows if r["contrastive"]]
    contrast: dict[str, Any] = {}
    for mode in ["possibility_lesion", "possibility_counterevidence"]:
        xs = [r["modes"][mode] for r in contrast_rows]
        contrast[mode] = {
            "mean_recall_at_k": round(statistics.mean(x["recall"] for x in xs), 4) if xs else None,
            "mean_precision_at_k": round(statistics.mean(x["precision"] for x in xs), 4) if xs else None,
        }

    bm = summary["sqlite_bm25"]
    cand = summary["possibility_counterevidence"]
    delta = {
        "precision": round(cand["mean_precision_at_k"] - bm["mean_precision_at_k"], 4),
        "recall": round(cand["mean_recall_at_k"] - bm["mean_recall_at_k"], 4),
        "mrr": round(cand["mean_mrr"] - bm["mean_mrr"], 4),
        "ndcg": round(cand["mean_ndcg"] - bm["mean_ndcg"], 4),
        "latency_ms": round(cand["median_case_latency_ms"] - bm["median_case_latency_ms"], 3),
    }
    quality_dominates = (
        cand["mean_recall_at_k"] >= bm["mean_recall_at_k"]
        and cand["mean_precision_at_k"] >= bm["mean_precision_at_k"]
        and cand["mean_ndcg"] >= bm["mean_ndcg"]
        and (
            cand["mean_recall_at_k"] > bm["mean_recall_at_k"]
            or cand["mean_precision_at_k"] > bm["mean_precision_at_k"]
            or cand["mean_ndcg"] > bm["mean_ndcg"]
        )
    )
    return {
        "schema_version": "1.0",
        "benchmark_class": "CLAY_SELF_USE_ENGINEERING_PROXY",
        "cases": len(rows),
        "repeat": repeat,
        "summary": summary,
        "contrastive_lesion": contrast,
        "candidate_vs_sqlite_bm25": delta,
        "quality_dominates_sqlite_bm25_on_this_suite": quality_dominates,
        "rows": rows,
        "limitations": [
            "The suite is small and project-internal; it is not an independent general database benchmark.",
            "Expected claim IDs are source-grounded but model-authored and therefore can contain benchmark-design bias.",
            "SQLite FTS5 BM25 is used as a strong conventional lexical baseline; this does not represent every database or vector retriever.",
            "ClayGraph currently loads a derived graph materialization in Python; latency is expected to be worse until the qualified neighborhood is indexed/materialized incrementally.",
            "Claim retrieval quality is not equivalent to downstream answer quality; later live/held-out assembly tests are required."
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(ROOT / "benchmarks" / "possibility_preprocessor" / "cases.json"))
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--output")
    args = ap.parse_args()
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    out = benchmark(cases, max(1, min(args.repeat, 10)))
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
