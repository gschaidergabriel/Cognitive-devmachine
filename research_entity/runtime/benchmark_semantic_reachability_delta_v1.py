#!/usr/bin/env python3
"""Deterministic microbenchmark for the bounded semantic reachability delta candidate.

Scope: mechanism/update benchmark only. It does not establish general database superiority
or downstream Frank answer quality. It compares exact local recomputation with exact sparse
support-count deltas for the same <=2-hop reachability semantics.
"""
from __future__ import annotations

from collections import defaultdict
import json
import platform
import random
import statistics
import time

from semantic_reachability_delta_v1 import BoundedReachability2

SEED = 2608103
N = 1400
INITIAL_EDGES = 5600
MUTATIONS = 2000


def percentile(values: list[float], p: float) -> float:
    xs = sorted(values)
    return xs[min(len(xs) - 1, max(0, int((len(xs) - 1) * p)))]


class TargetedRecompute2:
    """Fair exact local baseline: recompute only sources that can be affected."""

    def __init__(self, n: int, edges: set[tuple[int, int]]):
        self.n = n
        self.adj: dict[int, set[int]] = defaultdict(set)
        self.rev: dict[int, set[int]] = defaultdict(set)
        for u, v in edges:
            if u != v:
                self.adj[u].add(v)
                self.rev[v].add(u)
        self.masks = [self._mask(u) for u in range(n)]

    def _mask(self, source: int) -> int:
        mask = 1 << source
        for mid in self.adj.get(source, ()):
            mask |= 1 << mid
            for target in self.adj.get(mid, ()):
                mask |= 1 << target
        return mask

    def add(self, u: int, v: int) -> None:
        predecessors = set(self.rev.get(u, ()))
        self.adj[u].add(v)
        self.rev[v].add(u)
        for source in {u, *predecessors}:
            self.masks[source] = self._mask(source)

    def remove(self, u: int, v: int) -> None:
        predecessors = set(self.rev.get(u, ()))
        self.adj[u].remove(v)
        self.rev[v].remove(u)
        for source in {u, *predecessors}:
            self.masks[source] = self._mask(source)


class StringDeltaAdapter:
    def __init__(self, n: int, edges: set[tuple[int, int]]):
        self.refs = [f"s:{i}" for i in range(n)]
        self.index = BoundedReachability2(
            source_epoch=1,
            graph_epoch=1,
            semantic_refs=self.refs,
            edges=((self.refs[u], self.refs[v]) for u, v in edges),
        )
        self.source_epoch = 1
        self.graph_epoch = 1

    @property
    def adj(self):
        return self.index.adj

    @property
    def masks(self):
        return self.index.masks

    def add(self, u: int, v: int) -> None:
        ns = self.source_epoch + 1
        ng = self.graph_epoch + 1
        self.index.add_edge(
            self.refs[u], self.refs[v],
            basis_source_epoch=self.source_epoch,
            basis_graph_epoch=self.graph_epoch,
            result_source_epoch=ns,
            result_graph_epoch=ng,
        )
        self.source_epoch, self.graph_epoch = ns, ng

    def remove(self, u: int, v: int) -> None:
        ns = self.source_epoch + 1
        ng = self.graph_epoch + 1
        self.index.remove_edge(
            self.refs[u], self.refs[v],
            basis_source_epoch=self.source_epoch,
            basis_graph_epoch=self.graph_epoch,
            result_source_epoch=ns,
            result_graph_epoch=ng,
        )
        self.source_epoch, self.graph_epoch = ns, ng


def build_initial(rng: random.Random) -> set[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    while len(edges) < INITIAL_EDGES:
        u = rng.randrange(N)
        v = rng.randrange(N)
        if u != v:
            edges.add((u, v))
    return edges


def build_mutations(initial: set[tuple[int, int]], rng: random.Random):
    planner = TargetedRecompute2(N, initial)
    operations: list[tuple[str, int, int]] = []
    for _ in range(MUTATIONS):
        if rng.random() < 0.5:
            while True:
                u = rng.randrange(N)
                v = rng.randrange(N)
                if u != v and v not in planner.adj.get(u, ()):
                    break
            operations.append(("add", u, v))
            planner.add(u, v)
        else:
            sources = [u for u, targets in planner.adj.items() if targets]
            u = rng.choice(sources)
            v = rng.choice(tuple(planner.adj[u]))
            operations.append(("remove", u, v))
            planner.remove(u, v)
    return operations


def run(candidate, operations):
    add_ms: list[float] = []
    remove_ms: list[float] = []
    for operation, u, v in operations:
        started = time.perf_counter_ns()
        getattr(candidate, operation)(u, v)
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        (add_ms if operation == "add" else remove_ms).append(elapsed_ms)
    return {
        "add_p50_ms": statistics.median(add_ms),
        "add_p95_ms": percentile(add_ms, 0.95),
        "remove_p50_ms": statistics.median(remove_ms),
        "remove_p95_ms": percentile(remove_ms, 0.95),
    }


def main() -> None:
    rng = random.Random(SEED)
    initial = build_initial(rng)
    operations = build_mutations(initial, rng)

    baseline = TargetedRecompute2(N, initial)
    baseline_metrics = run(baseline, operations)

    delta = StringDeltaAdapter(N, initial)
    delta_metrics = run(delta, operations)
    exact, bad = delta.index.verify_exact()

    output = {
        "schema": "clay.semantic_reachability_delta_benchmark.v1",
        "scope": "exact <=2-hop update mechanism; synthetic deterministic; not universal DB superiority",
        "seed": SEED,
        "workload": {"semantic_refs": N, "initial_edges": INITIAL_EDGES, "mutations": MUTATIONS},
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "UNKNOWN",
        },
        "targeted_recompute": baseline_metrics,
        "support_count_delta": delta_metrics,
        "speedup": {
            "add_p50": baseline_metrics["add_p50_ms"] / delta_metrics["add_p50_ms"],
            "add_p95": baseline_metrics["add_p95_ms"] / delta_metrics["add_p95_ms"],
            "remove_p50": baseline_metrics["remove_p50_ms"] / delta_metrics["remove_p50_ms"],
            "remove_p95": baseline_metrics["remove_p95_ms"] / delta_metrics["remove_p95_ms"],
        },
        "exact_after_all_mutations": exact,
        "bad_refs": list(bad[:20]),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
