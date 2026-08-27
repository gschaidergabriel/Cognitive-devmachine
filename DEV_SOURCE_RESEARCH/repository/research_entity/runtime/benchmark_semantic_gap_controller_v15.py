from __future__ import annotations

"""Synthetic discriminating benchmark for U15 gap-controlled deepening.

The test holds one graph/ground truth constant and compares:
1. FIXED_DEPTH2_STRUCTURAL: collect every reachable node to depth 2;
2. GAP_CONTROLLED_QUERY_AWARE: start from the same compiled field and traverse only edges
   whose evidence tags intersect the explicit unresolved gap.

This is mechanism evidence only, not universal retrieval/database superiority.
"""

from collections import defaultdict, deque
import json
import math
import random
import statistics
import time
from typing import Any

from .semantic_gap_controller_v15 import (
    EvidenceItem,
    EvidenceRequirement,
    SufficiencyGapControllerV15,
)

SEEDS = (7, 17, 42)
FAMILIES = 240
DISTRACTORS_PER_HOP = 8
QUERIES_PER_SEED = 1200
MAX_ITEMS = 32


def percentile(xs: list[float], q: float) -> float:
    ys = sorted(xs)
    p = (len(ys) - 1) * q
    lo, hi = math.floor(p), math.ceil(p)
    return ys[lo] if lo == hi else ys[lo] * (hi - p) + ys[hi] * (p - lo)


def make_world(seed: int):
    rng = random.Random(seed)
    items: dict[str, EvidenceItem] = {}
    adj: dict[str, list[str]] = defaultdict(list)
    truth: dict[str, tuple[str, ...]] = {}
    anchors = []
    for i in range(FAMILIES):
        a = f"f{i}:anchor"
        b = f"f{i}:hop1"
        c = f"f{i}:hop2"
        items[a] = EvidenceItem(a, frozenset({f"family:{i}", "anchor"}))
        items[b] = EvidenceItem(b, frozenset({f"family:{i}", "need:one"}))
        items[c] = EvidenceItem(c, frozenset({f"family:{i}", "need:two"}))
        adj[a].append(b)
        adj[b].append(c)
        for hop, src in ((1, a), (2, b)):
            for j in range(DISTRACTORS_PER_HOP):
                d = f"f{i}:d{hop}:{j}"
                # Distractors are topologically plausible but do not satisfy the required tag.
                items[d] = EvidenceItem(d, frozenset({f"noise:{rng.randrange(64)}", f"hop:{hop}"}))
                adj[src].append(d)
        rng.shuffle(adj[a]); rng.shuffle(adj[b])
        truth[a] = (a, b, c)
        anchors.append(a)
    return items, adj, truth, anchors


def fixed_depth2(anchor: str, items: dict[str, EvidenceItem], adj: dict[str, list[str]], limit: int):
    out = []
    q = deque([(anchor, 0)])
    seen = set()
    while q and len(out) < limit:
        ref, depth = q.popleft()
        if ref in seen:
            continue
        seen.add(ref); out.append(items[ref])
        if depth < 2:
            for nxt in adj.get(ref, ()):
                q.append((nxt, depth + 1))
    return out


def score(got: list[EvidenceItem], expected: set[str]):
    refs = [x.ref for x in got]
    hit = len(set(refs) & expected)
    return {
        "recall": hit / len(expected),
        "precision": hit / len(refs) if refs else 0.0,
        "items": len(refs),
    }


def run_seed(seed: int) -> dict[str, Any]:
    items, adj, truth, anchors = make_world(seed)
    rng = random.Random(seed + 1000)
    classes = ("SUFFICIENT", "ONE_HOP_GAP", "TWO_HOP_GAP")
    queries = [(rng.choice(anchors), classes[i % 3]) for i in range(QUERIES_PER_SEED)]

    fixed_rows = []
    fixed_lat = []
    gap_rows = []
    gap_lat = []
    deepening_rounds = []

    current_anchor = [""]
    def expand(query_text, terms, selected, source_epoch, graph_epoch, budget):
        del query_text, source_epoch, graph_epoch
        # Query-aware gate: only descendants whose evidence tags intersect unresolved terms.
        frontier = list(selected)
        candidates = []
        seen = set(selected)
        for _ in range(2):
            nxt = []
            for src in frontier:
                for ref in adj.get(src, ()):
                    if ref in seen:
                        continue
                    seen.add(ref); nxt.append(ref)
                    if set(items[ref].tags) & set(terms):
                        candidates.append(items[ref])
                        if len(candidates) >= budget:
                            return candidates
            frontier = nxt
        return candidates

    ctl = SufficiencyGapControllerV15(expand=expand, max_rounds=2, max_items=MAX_ITEMS)

    for anchor, qclass in queries:
        expected_all = set(truth[anchor])
        if qclass == "SUFFICIENT":
            initial = [items[x] for x in truth[anchor]]
            req = [EvidenceRequirement("complete", required_refs=frozenset(expected_all), min_items=3)]
            expected = expected_all
        elif qclass == "ONE_HOP_GAP":
            initial = [items[anchor]]
            wanted = truth[anchor][1]
            req = [EvidenceRequirement("need-one", required_refs=frozenset({wanted}), min_items=1)]
            expected = {anchor, wanted}
        else:
            initial = [items[anchor]]
            wanted = truth[anchor][2]
            req = [EvidenceRequirement("need-two", required_refs=frozenset({wanted}), min_items=1)]
            expected = {anchor, wanted}

        t = time.perf_counter_ns()
        f = fixed_depth2(anchor, items, adj, MAX_ITEMS)
        fixed_lat.append(time.perf_counter_ns() - t)
        fixed_rows.append(score(f, expected))

        t = time.perf_counter_ns()
        g = ctl.assemble(
            query_id=f"{seed}:{anchor}:{qclass}",
            query_text=f"{anchor} {qclass}",
            source_epoch=1,
            graph_epoch=1,
            initial_items=initial,
            requirements=req,
        )
        gap_lat.append(time.perf_counter_ns() - t)
        selected_items = [items[r] for r in g.selected_refs]
        gap_rows.append(score(selected_items, expected))
        deepening_rounds.append(g.deepening_rounds)

    def summarize(rows, lat):
        return {
            "mean_recall": statistics.mean(x["recall"] for x in rows),
            "mean_precision": statistics.mean(x["precision"] for x in rows),
            "mean_context_items": statistics.mean(x["items"] for x in rows),
            "latency_us": {
                "p50": percentile(lat, .5) / 1000.0,
                "p95": percentile(lat, .95) / 1000.0,
                "p99": percentile(lat, .99) / 1000.0,
                "mean": statistics.mean(lat) / 1000.0,
            },
        }
    return {
        "seed": seed,
        "fixed_depth2_structural": summarize(fixed_rows, fixed_lat),
        "gap_controlled_query_aware": summarize(gap_rows, gap_lat),
        "gap_mean_deepening_rounds": statistics.mean(deepening_rounds),
    }


def main():
    runs = [run_seed(s) for s in SEEDS]
    def agg(mode, field):
        return statistics.mean(r[mode][field] for r in runs)
    out = {
        "schema_version": "1.0",
        "benchmark": "U15_GAP_CONTROLLED_VS_FIXED_DEPTH2_STRUCTURAL",
        "evidence_class": "SYNTHETIC_EXECUTED_TEST_WHEN_RUN",
        "scope_guard": "Mechanism benchmark only; query-aware tags are synthetic ground-truth metadata and can advantage U15. Not universal DB/retrieval superiority.",
        "configuration": {
            "seeds": list(SEEDS),
            "families_per_seed": FAMILIES,
            "queries_per_seed": QUERIES_PER_SEED,
            "distractors_per_hop": DISTRACTORS_PER_HOP,
            "max_items": MAX_ITEMS,
            "query_classes": ["SUFFICIENT", "ONE_HOP_GAP", "TWO_HOP_GAP"],
        },
        "runs": runs,
        "aggregate": {
            "fixed_depth2_mean_recall": agg("fixed_depth2_structural", "mean_recall"),
            "fixed_depth2_mean_precision": agg("fixed_depth2_structural", "mean_precision"),
            "fixed_depth2_mean_context_items": agg("fixed_depth2_structural", "mean_context_items"),
            "gap_mean_recall": agg("gap_controlled_query_aware", "mean_recall"),
            "gap_mean_precision": agg("gap_controlled_query_aware", "mean_precision"),
            "gap_mean_context_items": agg("gap_controlled_query_aware", "mean_context_items"),
            "gap_mean_deepening_rounds": statistics.mean(r["gap_mean_deepening_rounds"] for r in runs),
        },
        "limitations": [
            "Synthetic tags encode the evidence gap explicitly; real Clay gap extraction remains a separate validation problem.",
            "Python microbenchmark timing is not a storage-engine comparison.",
            "Fixed-depth baseline intentionally represents query-blind structural expansion, not every graph-retrieval method.",
            "Held-out real Clay queries and Hostinger/Andreas target execution remain required."
        ],
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
