#!/usr/bin/env python3
from __future__ import annotations

"""Measure U16 observability overhead and route-waste visibility against U14.

The mechanisms are deterministic in-memory mocks so this benchmark isolates planner/receipt
overhead rather than storage-engine performance.  Final result equivalence is mandatory.
"""

import json
import math
import platform
import random
import sqlite3
import statistics
import time
from typing import Any

from .adaptive_semantic_read_plane_v14 import (
    AdaptiveReadRequest,
    AdaptiveSemanticReadPlaneV14,
    VerifiedReadBasis,
)
from .measured_adaptive_read_plane_v16 import (
    MeasuredAdaptiveSemanticReadPlaneV16,
    aggregate_route_telemetry,
)

SEED = 20260810
N = 30000


def pct(xs: list[int], q: float) -> float:
    ys = sorted(xs)
    p = (len(ys) - 1) * q
    lo, hi = math.floor(p), math.ceil(p)
    return float(ys[lo] if lo == hi else ys[lo] * (hi - p) + ys[hi] * (p - lo))


def summary(xs: list[int]) -> dict[str, float]:
    return {
        "p50_ns": float(statistics.median(xs)),
        "p95_ns": pct(xs, .95),
        "p99_ns": pct(xs, .99),
        "mean_ns": float(statistics.mean(xs)),
    }


def basis(r):
    return VerifiedReadBasis(f"b:{r.source_epoch}:{r.graph_epoch}", r.source_epoch, r.graph_epoch, "d" * 64, True)


def exact(key, basis, limit):
    del basis, limit
    return ("exact",) if key.startswith("hit:") else ()


def compiled(text, basis, limit):
    del basis, limit
    return ("compiled",) if text.startswith("compiled ") else ()


def resolve(text, basis):
    del basis
    return "entity:1" if "entity" in text else None


def graph(entity, text, basis, limit):
    del basis, limit
    return ("graph",) if entity == "entity:1" and "graph" in text else ()


def composition(text, basis, limit):
    del basis, limit
    return ("pareto",) if "compose" in text else ()


def fallback(text, basis, limit):
    del basis, limit
    return ("fallback",) if "fallback" in text else ()


def make_planes():
    kwargs = dict(
        verify_read_basis=basis,
        exact_lookup=exact,
        compiled_semantic_lookup=compiled,
        resolve_entity=resolve,
        graph_lookup=graph,
        compositional_lookup=composition,
        fallback_lookup=fallback,
    )
    return AdaptiveSemanticReadPlaneV14(**kwargs), MeasuredAdaptiveSemanticReadPlaneV16(**kwargs)


def make_requests(n: int):
    rng = random.Random(SEED)
    classes = ("EXACT_HIT", "EXACT_MISS", "COMPILED", "COMPOSITION", "GRAPH", "FALLBACK", "MISS")
    out = []
    for i in range(n):
        cls = classes[i % len(classes)]
        if cls == "EXACT_HIT":
            r = AdaptiveReadRequest(f"q{i}", "plain", 5, 7, exact_normalized_key=f"hit:{i}")
        elif cls == "EXACT_MISS":
            r = AdaptiveReadRequest(f"q{i}", "fallback", 5, 7, exact_normalized_key=f"miss:{i}")
        elif cls == "COMPILED":
            r = AdaptiveReadRequest(f"q{i}", "compiled fact", 5, 7)
        elif cls == "COMPOSITION":
            r = AdaptiveReadRequest(f"q{i}", "entity compose", 5, 7, compositional=True)
        elif cls == "GRAPH":
            r = AdaptiveReadRequest(f"q{i}", "entity graph", 5, 7)
        elif cls == "FALLBACK":
            r = AdaptiveReadRequest(f"q{i}", "fallback", 5, 7)
        else:
            r = AdaptiveReadRequest(f"q{i}", "nothing useful", 5, 7)
        out.append((cls, r))
    rng.shuffle(out)
    return out


def run(n: int = N) -> dict[str, Any]:
    v14, v16 = make_planes()
    requests = make_requests(n)
    old_lat: list[int] = []
    new_lat: list[int] = []
    receipts = []
    mismatches = 0
    by_class: dict[str, dict[str, int]] = {}

    for cls, request in requests:
        t = time.perf_counter_ns(); old = v14.query(request); old_lat.append(time.perf_counter_ns() - t)
        t = time.perf_counter_ns(); new = v16.query(request); new_lat.append(time.perf_counter_ns() - t)
        receipts.append(new)
        if (
            old.mode,
            old.refs,
            old.resolved_logical_id,
            old.sufficient,
            old.lexical_padding_used,
            old.source_epoch,
            old.graph_epoch,
            old.read_basis_id,
            old.derivation_hash,
        ) != (
            new.mode,
            new.refs,
            new.resolved_logical_id,
            new.sufficient,
            new.lexical_padding_used,
            new.source_epoch,
            new.graph_epoch,
            new.read_basis_id,
            new.derivation_hash,
        ):
            mismatches += 1
        row = by_class.setdefault(cls, {"queries": 0, "attempts": 0})
        row["queries"] += 1
        row["attempts"] += len(new.attempts)

    profile = aggregate_route_telemetry(receipts)
    old_s = summary(old_lat); new_s = summary(new_lat)
    return {
        "schema_version": "1.0",
        "benchmark": "U16_ROUTE_TELEMETRY_EQUIVALENCE_AND_OVERHEAD",
        "execution_class": "EXECUTED_WHEN_RUN",
        "requests": n,
        "seed": SEED,
        "semantic_mismatches_vs_v14": mismatches,
        "v14_latency": old_s,
        "v16_latency": new_s,
        "telemetry_overhead_p50_ns": new_s["p50_ns"] - old_s["p50_ns"],
        "telemetry_overhead_ratio_p50": new_s["p50_ns"] / max(1.0, old_s["p50_ns"]),
        "attempts_by_query_class": {
            k: {
                **v,
                "mean_attempts_per_query": v["attempts"] / max(1, v["queries"]),
            }
            for k, v in sorted(by_class.items())
        },
        "route_profile": profile,
        "environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "claim_boundary": [
            "Mocks isolate routing/receipt overhead; this is not a database/retrieval latency benchmark.",
            "U16 is valuable only if final semantics remain identical and telemetry later supports a separately validated routing improvement.",
            "No cost-based reorder is performed in U16; measurement precedes adaptation.",
        ],
    }


def main():
    print(json.dumps(run(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
