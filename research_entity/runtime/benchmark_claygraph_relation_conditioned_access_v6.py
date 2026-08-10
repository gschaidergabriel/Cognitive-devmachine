#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import platform
import random
import sqlite3
import statistics
import time

from research_entity.runtime.claygraph_relation_conditioned_access_v6 import (
    ClayGraphRelationConditionedAccessV6,
)

SEED = 20260810
ROOTS = 800
RELATIONS = (
    "REQUIRES", "DEPENDS_ON", "SUPPORTS", "CONTRADICTS",
    "BLOCKS", "DERIVED_FROM", "SUPERSEDES", "ALTERNATIVE",
)
PER_RELATION = 32
TOTAL_BUDGET = 32
RELATION_RESERVE = 8

SCHEMA = """
CREATE TABLE graph_head_edges(
  logical_edge_id TEXT PRIMARY KEY,
  edge_version_id TEXT NOT NULL UNIQUE,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  source_logical_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  weight REAL NOT NULL,
  confidence REAL,
  provenance_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  causal_class TEXT,
  source_status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_graph_head_edges_current_source_weight_v6
  ON graph_head_edges(source_logical_id,weight DESC,target_logical_id,logical_edge_id)
  WHERE source_status='CURRENT';
CREATE INDEX idx_graph_head_edges_current_source_relation_weight_v6
  ON graph_head_edges(source_logical_id,relation_type,weight DESC,target_logical_id,logical_edge_id)
  WHERE source_status='CURRENT';
"""


def percentile(values, p):
    ys = sorted(values)
    k = (len(ys) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return ys[lo] if lo == hi else ys[lo] * (hi - k) + ys[hi] * (k - lo)


def timing(values):
    return {
        "n": len(values),
        "p50_us": percentile(values, 0.50),
        "p95_us": percentile(values, 0.95),
        "p99_us": percentile(values, 0.99),
        "mean_us": statistics.fmean(values),
        "min_us": min(values),
        "max_us": max(values),
    }


def build_fixture():
    rng = random.Random(SEED)
    c = sqlite3.connect(":memory:")
    c.executescript(SCHEMA)
    rows = []
    truth = {}
    for r in range(ROOTS):
        source = f"root_{r:04d}"
        all_edges = []
        bases = {rel: rng.uniform(0.55, 0.99) for rel in RELATIONS}
        for rel in RELATIONS:
            relation_edges = []
            for j in range(PER_RELATION):
                weight = bases[rel] - j * 0.006 + rng.uniform(-0.001, 0.001)
                target = f"{source}:{rel}:{j:02d}"
                relation_edges.append((target, weight))
            relation_edges.sort(key=lambda x: (-x[1], x[0]))
            truth[(source, rel)] = relation_edges[0][0]
            for target, weight in relation_edges:
                edge_id = f"edge:{target}"
                all_edges.append((
                    edge_id, edge_id + ":v1", 4, 7, source, target, rel, weight, 0.9,
                    "{}", "{}", "ASSOCIATIVE", "CURRENT", "t",
                ))
        rows.extend(all_edges)
    c.executemany("INSERT INTO graph_head_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    c.commit()
    return c, truth, len(rows)


def evaluate(access, truth, queries, mode):
    lat = []
    hits = 0
    relation_precision = []
    for source, relation in queries:
        started = time.perf_counter_ns()
        if mode == "global":
            edges, _ = access.query(source_logical_id=source, total_budget=TOTAL_BUDGET)
        elif mode == "counter_only":
            typed = relation if relation in {"CONTRADICTS", "BLOCKS", "SUPERSEDES"} else None
            edges, _ = access.query(
                source_logical_id=source,
                total_budget=TOTAL_BUDGET,
                typed_relation=typed,
                relation_reserve=6,
            )
        elif mode == "relation":
            edges, _ = access.query(
                source_logical_id=source,
                total_budget=TOTAL_BUDGET,
                typed_relation=relation,
                relation_reserve=RELATION_RESERVE,
            )
        else:
            raise AssertionError(mode)
        lat.append((time.perf_counter_ns() - started) / 1000.0)
        target = truth[(source, relation)]
        hits += int(target in {edge.target_logical_id for edge in edges})
        relation_precision.append(sum(edge.relation_type == relation for edge in edges) / max(1, len(edges)))
    return {
        "recall_at_32": hits / len(queries),
        "mean_query_relation_precision_at_32": statistics.fmean(relation_precision),
        "latency": timing(lat),
    }


def main():
    c, truth, edge_count = build_fixture()
    access = ClayGraphRelationConditionedAccessV6(c)
    rng = random.Random(SEED ^ 0xA55A)
    queries = [(f"root_{r:04d}", rng.choice(RELATIONS)) for r in range(ROOTS)]
    global_result = evaluate(access, truth, queries, "global")
    counter_result = evaluate(access, truth, queries, "counter_only")
    relation_result = evaluate(access, truth, queries, "relation")
    result = {
        "schema_version": "1.0",
        "benchmark": "CLAYGRAPH_V6_RELATION_CONDITIONED_FIXED_BUDGET",
        "evidence_class": "SYNTHETIC_ADVERSARIAL_MECHANISM",
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
        },
        "fixture": {
            "seed": SEED,
            "roots": ROOTS,
            "relations": list(RELATIONS),
            "edges": edge_count,
            "out_degree": len(RELATIONS) * PER_RELATION,
            "queries": len(queries),
        },
        "budget": {"total": TOTAL_BUDGET, "relation_reserve": RELATION_RESERVE},
        "global_top_weight": global_result,
        "counter_only_reserve": counter_result,
        "query_relation_reserve": relation_result,
        "delta_relation_vs_global": {
            "recall_points": relation_result["recall_at_32"] - global_result["recall_at_32"],
            "relation_precision_points": (
                relation_result["mean_query_relation_precision_at_32"]
                - global_result["mean_query_relation_precision_at_32"]
            ),
            "p50_latency_ratio": (
                relation_result["latency"]["p50_us"] / global_result["latency"]["p50_us"]
            ),
        },
        "limitations": [
            "Synthetic high-degree relation-intent workload; it does not establish live Clay/Frank accuracy.",
            "Typed relation intent is assumed correct and is supplied by the benchmark; planner calibration is a separate gate.",
            "A conventional database can implement the same two indexes and application-level typed relation selection.",
            "Promotion requires real-contract/held-out graph queries and false-relation-intent controls.",
        ],
    }
    result["pass"] = bool(
        relation_result["recall_at_32"] > global_result["recall_at_32"]
        and relation_result["recall_at_32"] >= counter_result["recall_at_32"]
        and relation_result["recall_at_32"] == 1.0
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    c.close()
    raise SystemExit(0 if result["pass"] else 2)


if __name__ == "__main__":
    main()
