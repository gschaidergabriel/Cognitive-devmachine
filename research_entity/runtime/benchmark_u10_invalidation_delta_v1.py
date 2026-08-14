#!/usr/bin/env python3
"""Synthetic scale proxy for U10 depth-3 structural invalidation.

Matches the cardinalities of U10-POSSIBILITY-PREPROCESSOR-SYNTH-001 (6000 nodes,
41963 edges, 120 active anchors) but uses a fresh random topology. Therefore affected-anchor
counts are an invalidation mechanism proxy, NOT a replay of the U10 benchmark fixture.
"""
from __future__ import annotations

from collections import defaultdict
import json
import platform
import random
import statistics
import time

from u10_invalidation_delta_v1 import U10Depth3InvalidationIndex

SEED = 7341902
NODES = 6000
EDGES = 41963
ANCHORS = 120
MUTATIONS = 1000


def pct(values: list[float], p: float) -> float:
    xs = sorted(values)
    return xs[min(len(xs) - 1, max(0, int((len(xs) - 1) * p)))]


def main() -> None:
    rng = random.Random(SEED)
    refs = [f"n:{i}" for i in range(NODES)]
    edge_ids: set[tuple[int, int]] = set()
    while len(edge_ids) < EDGES:
        u = rng.randrange(NODES)
        v = rng.randrange(NODES)
        if u != v:
            edge_ids.add((u, v))
    anchors = tuple(refs[i] for i in rng.sample(range(NODES), ANCHORS))
    edges = tuple((refs[u], refs[v]) for u, v in edge_ids)

    started = time.perf_counter_ns()
    idx = U10Depth3InvalidationIndex(
        source_epoch=1,
        graph_epoch=1,
        semantic_refs=refs,
        forward_edges=edges,
        active_anchor_refs=anchors,
    )
    build_ms = (time.perf_counter_ns() - started) / 1_000_000

    forward: dict[int, set[int]] = defaultdict(set)
    for u, v in edge_ids:
        forward[u].add(v)

    source_epoch = graph_epoch = 1
    identify_ms: list[float] = []
    mutation_ms: list[float] = []
    affected_counts: list[int] = []

    for _ in range(MUTATIONS):
        if rng.random() < 0.5:
            while True:
                u = rng.randrange(NODES)
                v = rng.randrange(NODES)
                if u != v and v not in forward.get(u, ()):
                    break
            t = time.perf_counter_ns()
            affected = idx.affected_anchors_before_edge_mutation(
                refs[u], basis_source_epoch=source_epoch, basis_graph_epoch=graph_epoch
            )
            identify_ms.append((time.perf_counter_ns() - t) / 1_000_000)
            ns, ng = source_epoch + 1, graph_epoch + 1
            t = time.perf_counter_ns()
            receipt = idx.add_forward_edge(
                refs[u], refs[v],
                basis_source_epoch=source_epoch,
                basis_graph_epoch=graph_epoch,
                result_source_epoch=ns,
                result_graph_epoch=ng,
            )
            mutation_ms.append((time.perf_counter_ns() - t) / 1_000_000)
            forward[u].add(v)
        else:
            sources = [u for u, targets in forward.items() if targets]
            u = rng.choice(sources)
            v = rng.choice(tuple(forward[u]))
            t = time.perf_counter_ns()
            affected = idx.affected_anchors_before_edge_mutation(
                refs[u], basis_source_epoch=source_epoch, basis_graph_epoch=graph_epoch
            )
            identify_ms.append((time.perf_counter_ns() - t) / 1_000_000)
            ns, ng = source_epoch + 1, graph_epoch + 1
            t = time.perf_counter_ns()
            receipt = idx.remove_forward_edge(
                refs[u], refs[v],
                basis_source_epoch=source_epoch,
                basis_graph_epoch=graph_epoch,
                result_source_epoch=ns,
                result_graph_epoch=ng,
            )
            mutation_ms.append((time.perf_counter_ns() - t) / 1_000_000)
            forward[u].remove(v)

        assert affected == receipt.affected_anchor_refs
        affected_counts.append(receipt.affected_anchor_count)
        source_epoch, graph_epoch = ns, ng

    exact, bad = idx.reverse.verify_exact()
    out = {
        "schema": "clay.u10_invalidation_delta_benchmark.v1",
        "scope": "synthetic random-topology invalidation proxy matching U10 fixture cardinalities; not the original U10 topology",
        "seed": SEED,
        "workload": {"nodes": NODES, "edges": EDGES, "active_anchors": ANCHORS, "mutations": MUTATIONS},
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "UNKNOWN",
        },
        "reverse_reachability_build_ms": build_ms,
        "identify_affected_anchors_ms": {
            "p50": statistics.median(identify_ms),
            "p95": pct(identify_ms, 0.95),
        },
        "apply_reverse_support_delta_ms": {
            "p50": statistics.median(mutation_ms),
            "p95": pct(mutation_ms, 0.95),
        },
        "affected_anchor_count": {
            "mean": statistics.mean(affected_counts),
            "median": statistics.median(affected_counts),
            "max": max(affected_counts),
            "zero_fraction": sum(v == 0 for v in affected_counts) / len(affected_counts),
        },
        "exact_after_all_mutations": exact,
        "bad_refs": list(bad[:20]),
        "interpretation_guard": "Only affected anchors are candidates for U10 recompile; weighted field semantics remain owned and reverified by U10.",
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
