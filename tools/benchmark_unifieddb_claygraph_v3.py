#!/usr/bin/env python3
"""Reproducible falsifier/benchmark for UnifiedDB V10 + ClayGraph V3.

No third-party dependencies. Measures:
1) semantic_records multi-version correctness;
2) exact old/new ClayGraph result equivalence under adversarial statuses/epochs;
3) old/new latest-edge latency and SQLite query plans.

This benchmark does NOT claim generic superiority over other database engines. It tests
Clay's specific versioned semantic-state / graph-neighborhood hot path.
"""
import argparse
import json
import math
import os
import platform
import random
import resource
import sqlite3
import statistics
import sys
import time


def quantile(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, math.ceil(p * len(xs)) - 1))]


def environment():
    return {
        "python": sys.version.split()[0],
        "sqlite": sqlite3.sqlite_version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
    }


OLD_SEMANTIC = """
CREATE TABLE semantic_records(
  record_id TEXT PRIMARY KEY,
  record_kind TEXT NOT NULL,
  record_key TEXT NOT NULL,
  scope TEXT NOT NULL,
  epistemic_class TEXT NOT NULL,
  payload_clay TEXT NOT NULL,
  source_ref TEXT,
  source_hash TEXT,
  valid_from TEXT,
  valid_to TEXT,
  status TEXT NOT NULL,
  source_epoch INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(record_kind,record_key,scope,status)
);
CREATE VIEW v_current_semantic_records AS
SELECT * FROM semantic_records
WHERE status='CURRENT' AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP);
"""

V10 = """
DROP VIEW IF EXISTS v_current_semantic_records;
CREATE TABLE semantic_records_v10(
  record_id TEXT PRIMARY KEY,
  record_kind TEXT NOT NULL,
  record_key TEXT NOT NULL,
  scope TEXT NOT NULL,
  epistemic_class TEXT NOT NULL,
  payload_clay TEXT NOT NULL,
  source_ref TEXT,
  source_hash TEXT,
  valid_from TEXT,
  valid_to TEXT,
  status TEXT NOT NULL,
  source_epoch INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
INSERT INTO semantic_records_v10 SELECT * FROM semantic_records;
DROP TABLE semantic_records;
ALTER TABLE semantic_records_v10 RENAME TO semantic_records;
CREATE INDEX idx_semantic_records_lookup
  ON semantic_records(record_kind,record_key,scope,status);
CREATE INDEX idx_semantic_records_history
  ON semantic_records(record_kind,record_key,scope,source_epoch DESC,updated_at DESC);
CREATE UNIQUE INDEX uq_semantic_records_current
  ON semantic_records(record_kind,record_key,scope)
  WHERE status='CURRENT';
CREATE VIEW v_current_semantic_records AS
SELECT * FROM semantic_records
WHERE status='CURRENT' AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP);
"""

GRAPH_BASE = """
CREATE TABLE graph_edges(
  edge_version_id TEXT PRIMARY KEY,
  logical_edge_id TEXT NOT NULL,
  graph_epoch INTEGER NOT NULL,
  source_logical_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 0.0,
  confidence REAL,
  provenance_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  causal_class TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_graph_edges_source
  ON graph_edges(source_logical_id,graph_epoch DESC);
CREATE INDEX idx_graph_edges_target
  ON graph_edges(target_logical_id,graph_epoch DESC);
CREATE VIEW old_latest AS
SELECT e.* FROM graph_edges e
JOIN (
  SELECT logical_edge_id,MAX(graph_epoch) ge
  FROM graph_edges
  GROUP BY logical_edge_id
) x ON x.logical_edge_id=e.logical_edge_id AND x.ge=e.graph_epoch
WHERE e.status='CURRENT';
"""

V3 = """
CREATE INDEX idx_graph_edges_logical
  ON graph_edges(logical_edge_id,graph_epoch DESC);
CREATE INDEX idx_graph_edges_current_source
  ON graph_edges(source_logical_id,relation_type,weight DESC,target_logical_id)
  WHERE status='CURRENT';
CREATE INDEX idx_graph_edges_current_target
  ON graph_edges(target_logical_id,relation_type,weight DESC,source_logical_id)
  WHERE status='CURRENT';
CREATE VIEW new_latest AS
SELECT e.* FROM graph_edges e
WHERE e.status='CURRENT'
  AND NOT EXISTS (
    SELECT 1 FROM graph_edges newer
    WHERE newer.logical_edge_id=e.logical_edge_id
      AND newer.graph_epoch>e.graph_epoch
  );
"""


def semantic_correctness(cycles):
    def insert(con, rid, epoch, status="CURRENT"):
        con.execute(
            """INSERT INTO semantic_records(
                 record_id,record_kind,record_key,scope,epistemic_class,payload_clay,
                 status,source_epoch,created_at,updated_at
               ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (rid, "world", "same-key", "global", "EVIDENCE", f"v{epoch}",
             status, epoch, "t", "t"),
        )

    old = sqlite3.connect(":memory:")
    old.executescript(OLD_SEMANTIC)
    old_failure = None
    try:
        for epoch in range(1, cycles + 1):
            old.execute(
                "UPDATE semantic_records SET status='SUPERSEDED' "
                "WHERE record_kind='world' AND record_key='same-key' "
                "AND scope='global' AND status='CURRENT'"
            )
            insert(old, f"r{epoch}", epoch)
        old.commit()
    except Exception as exc:  # expected falsifier on current schema
        old_failure = {
            "cycle": epoch,
            "type": type(exc).__name__,
            "message": str(exc),
        }

    candidate = sqlite3.connect(":memory:")
    candidate.executescript(OLD_SEMANTIC)
    candidate.executescript(V10)
    for epoch in range(1, cycles + 1):
        candidate.execute(
            "UPDATE semantic_records SET status='SUPERSEDED' "
            "WHERE record_kind='world' AND record_key='same-key' "
            "AND scope='global' AND status='CURRENT'"
        )
        insert(candidate, f"r{epoch}", epoch)
    candidate.commit()

    history_rows = candidate.execute("SELECT count(*) FROM semantic_records").fetchone()[0]
    current_heads = candidate.execute(
        "SELECT count(*) FROM semantic_records WHERE status='CURRENT'"
    ).fetchone()[0]
    epochs = [r[0] for r in candidate.execute(
        "SELECT source_epoch FROM semantic_records ORDER BY source_epoch"
    )]
    expected = list(range(1, cycles + 1))
    passed = bool(
        old_failure is not None
        and history_rows == cycles
        and current_heads == 1
        and epochs == expected
    )
    return {
        "baseline_failure": old_failure,
        "candidate_cycles": cycles,
        "candidate_history_rows": history_rows,
        "candidate_current_heads": current_heads,
        "candidate_epoch_sequence_exact": epochs == expected,
        "pass": passed,
    }


def populate_graph(con, logical_edges, versions, adversarial=False):
    rng = random.Random(7)
    batch = []
    sources = max(100, min(5000, logical_edges // 10))
    for i in range(logical_edges):
        logical_id = f"e{i:08d}"
        source = f"n{i % sources:06d}"
        target = f"n{(i * 17 + 13) % sources:06d}"
        version_count = versions if not adversarial else rng.randint(1, max(1, versions))
        for version in range(1, version_count + 1):
            status = (
                rng.choice(["CURRENT", "SUPERSEDED", "RETIRED"])
                if adversarial
                else ("CURRENT" if version == version_count else "SUPERSEDED")
            )
            batch.append((
                f"{logical_id}:v{version}", logical_id, version, source, target,
                "DEPENDS_ON", 0.5, 0.9, "{}", "{}", None, status, "t"
            ))
        if len(batch) >= 30000:
            con.executemany(
                "INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", batch
            )
            batch = []
    if batch:
        con.executemany(
            "INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", batch
        )
    con.commit()
    return sources


def graph_equivalence(cases, versions):
    con = sqlite3.connect(":memory:")
    con.executescript(GRAPH_BASE)
    con.executescript(V3)
    populate_graph(con, cases, versions, adversarial=True)
    old = {r[0] for r in con.execute("SELECT edge_version_id FROM old_latest")}
    new = {r[0] for r in con.execute("SELECT edge_version_id FROM new_latest")}
    return {
        "adversarial_logical_edges": cases,
        "old_rows": len(old),
        "new_rows": len(new),
        "symmetric_diff": len(old ^ new),
        "pass": old == new,
    }


def graph_performance(logical_edges, versions, reps, source_queries):
    def build(candidate):
        con = sqlite3.connect(":memory:")
        con.execute("PRAGMA temp_store=MEMORY")
        con.execute("PRAGMA cache_size=-200000")
        con.executescript(GRAPH_BASE)
        if candidate:
            con.executescript(V3)
        sources = populate_graph(con, logical_edges, versions, adversarial=False)
        return con, sources

    result = {}
    for label, candidate, view in [
        ("baseline", False, "old_latest"),
        ("candidate", True, "new_latest"),
    ]:
        con, sources = build(candidate)
        con.execute(f"SELECT count(*) FROM {view}").fetchone()  # warm-up
        global_ms = []
        for _ in range(reps):
            start = time.perf_counter()
            count = con.execute(f"SELECT count(*) FROM {view}").fetchone()[0]
            global_ms.append((time.perf_counter() - start) * 1000)

        rng = random.Random(42)
        source_ids = [
            f"n{i:06d}"
            for i in rng.sample(range(sources), min(source_queries, sources))
        ]
        source_ms = []
        row_counts = []
        for source in source_ids:
            start = time.perf_counter()
            rows = con.execute(
                f"SELECT logical_edge_id,target_logical_id,weight "
                f"FROM {view} WHERE source_logical_id=?",
                (source,),
            ).fetchall()
            source_ms.append((time.perf_counter() - start) * 1000)
            row_counts.append(len(rows))

        plan = [
            row[-1]
            for row in con.execute(
                f"EXPLAIN QUERY PLAN SELECT logical_edge_id,target_logical_id,weight "
                f"FROM {view} WHERE source_logical_id='n000001'"
            )
        ]
        result[label] = {
            "rows": count,
            "global_ms": {
                "p50": statistics.median(global_ms),
                "p95": quantile(global_ms, 0.95),
                "min": min(global_ms),
                "max": max(global_ms),
            },
            "source_ms": {
                "p50": statistics.median(source_ms),
                "p95": quantile(source_ms, 0.95),
                "min": min(source_ms),
                "max": max(source_ms),
            },
            "mean_source_rows": statistics.mean(row_counts),
            "query_plan": plan,
        }
        con.close()

    base_source = result["baseline"]["source_ms"]["p50"]
    new_source = result["candidate"]["source_ms"]["p50"]
    result["speedup_source_p50"] = base_source / new_source if new_source else None
    result["speedup_global_p50"] = (
        result["baseline"]["global_ms"]["p50"]
        / result["candidate"]["global_ms"]["p50"]
    )
    result["row_count_equal"] = result["baseline"]["rows"] == result["candidate"]["rows"]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logical-edges", type=int, default=120000)
    parser.add_argument("--versions", type=int, default=3)
    parser.add_argument("--reps", type=int, default=15)
    parser.add_argument("--source-queries", type=int, default=100)
    parser.add_argument("--semantic-cycles", type=int, default=100)
    parser.add_argument("--adversarial-edges", type=int, default=10000)
    args = parser.parse_args()

    started = time.perf_counter()
    semantic = semantic_correctness(args.semantic_cycles)
    equivalence = graph_equivalence(args.adversarial_edges, max(5, args.versions))
    performance = graph_performance(
        args.logical_edges, args.versions, args.reps, args.source_queries
    )
    result = {
        "schema_version": "1.0",
        "benchmark": "UnifiedDB-V10 + ClayGraph-V3",
        "environment": environment(),
        "parameters": vars(args),
        "semantic_history_correctness": semantic,
        "graph_result_equivalence": equivalence,
        "graph_performance": performance,
        "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "wall_seconds": time.perf_counter() - started,
    }
    result["overall_pass"] = bool(
        semantic["pass"]
        and equivalence["pass"]
        and performance["row_count_equal"]
        and performance["speedup_source_p50"] > 1.0
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
