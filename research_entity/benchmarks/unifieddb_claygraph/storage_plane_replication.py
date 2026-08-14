#!/usr/bin/env python3
"""Differential storage-plane benchmark for UnifiedDB + ClayGraph candidates.

This benchmark is deliberately synthetic. It measures physical access-path behavior while
preserving the current semantic boundary: UnifiedDB remains authority; ClayGraph heads are
rebuildable projections. It MUST NOT be reported as universal database superiority.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import sqlite3
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane


def p95(values: list[float]) -> float:
    xs = sorted(values)
    return xs[max(0, min(len(xs) - 1, math.ceil(0.95 * len(xs)) - 1))]


def timed(fn, repetitions: int) -> dict[str, float | int]:
    fn()
    samples: list[float] = []
    for _ in range(repetitions):
        started = time.perf_counter_ns()
        fn()
        samples.append((time.perf_counter_ns() - started) / 1e6)
    return {
        "n": repetitions,
        "p50_ms": statistics.median(samples),
        "p95_ms": p95(samples),
        "max_ms": max(samples),
    }


class SyntheticLedger:
    """Minimal read-compatible ledger adapter; no canonical state mutation."""

    def __init__(self, rows: int, domains: int):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.epoch = 0
        self.semantic_state_hash = "SYNTHETIC_NONCANONICAL"
        self.conn.execute(
            """CREATE TABLE state(
                 domain TEXT NOT NULL,k TEXT NOT NULL,value_json TEXT,
                 epistemic TEXT NOT NULL,status TEXT NOT NULL,
                 domain_epoch INTEGER NOT NULL,semantic_hash TEXT NOT NULL,
                 PRIMARY KEY(domain,k))"""
        )
        batch = []
        for i in range(rows):
            status = "CURRENT" if i % 5 < 3 else ("SUPERSEDED" if i % 5 == 3 else "RETRACTED")
            epistemic = "KNOWN" if i % 7 < 4 else ("UNKNOWN" if i % 7 < 6 else "CONFLICT")
            batch.append((
                f"d:{i % domains:03d}", f"k:{i:07d}", '{"v":1}', epistemic, status,
                1, f"h{i:07d}",
            ))
            if len(batch) >= 5000:
                self.conn.executemany("INSERT INTO state VALUES(?,?,?,?,?,?,?)", batch)
                batch = []
        if batch:
            self.conn.executemany("INSERT INTO state VALUES(?,?,?,?,?,?,?)", batch)
        self.conn.commit()

    def materialized(self) -> list[dict[str, Any]]:
        out = []
        for row in self.conn.execute(
            "SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash FROM state"
        ):
            out.append({
                "domain": row["domain"],
                "key": row["k"],
                "value": json.loads(row["value_json"]) if row["value_json"] is not None else None,
                "epistemic": row["epistemic"],
                "status": row["status"],
                "domain_epoch": int(row["domain_epoch"]),
                "semantic_hash": row["semantic_hash"],
            })
        return out


STATE_SCHEMA = """CREATE TABLE state(
  domain TEXT NOT NULL,k TEXT NOT NULL,value_json TEXT,
  epistemic TEXT NOT NULL,status TEXT NOT NULL,
  domain_epoch INTEGER NOT NULL,semantic_hash TEXT NOT NULL,
  PRIMARY KEY(domain,k));"""

INDEX_SQL = {
    "base": "",
    "order": "CREATE INDEX idx_state_current_order ON state(domain,k,epistemic) WHERE status='CURRENT';",
    "key": "CREATE INDEX idx_state_key_current ON state(k,domain,epistemic) WHERE status='CURRENT';",
    "both": """
      CREATE INDEX idx_state_current_order ON state(domain,k,epistemic) WHERE status='CURRENT';
      CREATE INDEX idx_state_key_current ON state(k,domain,epistemic) WHERE status='CURRENT';
    """,
}


def fill_state(con: sqlite3.Connection, start: int, count: int, domains: int) -> None:
    batch = []
    for i in range(start, start + count):
        status = "CURRENT" if i % 5 < 3 else ("SUPERSEDED" if i % 5 == 3 else "RETRACTED")
        epistemic = "KNOWN" if i % 7 < 4 else ("UNKNOWN" if i % 7 < 6 else "CONFLICT")
        batch.append((
            f"d:{i % domains:03d}", f"k:{i:07d}", '{"v":1}', epistemic, status,
            1, f"h{i:07d}",
        ))
        if len(batch) >= 5000:
            con.executemany("INSERT INTO state VALUES(?,?,?,?,?,?,?)", batch)
            batch = []
    if batch:
        con.executemany("INSERT INTO state VALUES(?,?,?,?,?,?,?)", batch)
    con.commit()


def raw_state_query(con: sqlite3.Connection, kind: str, limit: int = 64):
    if kind == "key":
        return con.execute(
            "SELECT domain,k FROM state WHERE k=? AND status=? AND epistemic=? ORDER BY domain,k LIMIT ?",
            ("k:0012377", "CURRENT", "KNOWN", limit + 1),
        ).fetchall()
    if kind == "domain":
        return con.execute(
            "SELECT domain,k FROM state WHERE domain=? AND status=? AND epistemic=? ORDER BY domain,k LIMIT ?",
            ("d:177", "CURRENT", "KNOWN", limit + 1),
        ).fetchall()
    if kind == "global":
        return con.execute(
            "SELECT domain,k FROM state WHERE status=? AND epistemic=? ORDER BY domain,k LIMIT ?",
            ("CURRENT", "KNOWN", limit + 1),
        ).fetchall()
    raise ValueError(kind)


def benchmark_udb_pushdown(rows: int, repetitions_legacy: int, repetitions_fast: int) -> dict[str, Any]:
    ledger = SyntheticLedger(rows, 100)
    plane = UnifiedDBQueryPlane(ledger)
    cases = {
        "point": QuerySpec("point", domains=("d:077",), keys=("k:0012377",), epistemic=("KNOWN",), limit=64),
        "domain_known": QuerySpec("domain", domains=("d:077",), epistemic=("KNOWN",), limit=64),
        "three_domain": QuerySpec("three", domains=("d:003", "d:077", "d:099"), epistemic=("KNOWN",), limit=64),
        "global_known": QuerySpec("global", epistemic=("KNOWN",), limit=64),
    }
    out: dict[str, Any] = {"rows": rows, "cases": {}}
    for name, spec in cases.items():
        legacy_rows, legacy_truncated = plane._query_rows_legacy(spec)
        fast_rows, fast_truncated = plane._query_rows_fast(spec)
        equivalent = (legacy_rows, legacy_truncated) == (fast_rows, fast_truncated)
        legacy = timed(lambda s=spec: plane._query_rows_legacy(s), repetitions_legacy)
        fast = timed(lambda s=spec: plane._query_rows_fast(s), repetitions_fast)
        out["cases"][name] = {
            "equivalent": equivalent,
            "legacy": legacy,
            "fast": fast,
            "p50_speedup": legacy["p50_ms"] / fast["p50_ms"],
        }
    ledger.conn.close()
    return out


def benchmark_index_ablation(rows: int, domains: int, repetitions: int) -> dict[str, Any]:
    result: dict[str, Any] = {"rows": rows, "configs": {}}
    for config in ("base", "order", "key", "both"):
        con = sqlite3.connect(":memory:")
        con.executescript(STATE_SCHEMA + INDEX_SQL[config])
        fill_state(con, 0, rows, domains)
        page_size = con.execute("PRAGMA page_size").fetchone()[0]
        logical_bytes = con.execute("PRAGMA page_count").fetchone()[0] * page_size
        reads = {
            "key": timed(lambda: raw_state_query(con, "key", 64), repetitions),
            "domain": timed(lambda: raw_state_query(con, "domain", 64), repetitions),
            "global_4096": timed(lambda: raw_state_query(con, "global", 4096), repetitions),
        }
        started = time.perf_counter_ns()
        fill_state(con, rows, 20_000, domains)
        append_20k_ms = (time.perf_counter_ns() - started) / 1e6
        result["configs"][config] = {
            "logical_bytes": logical_bytes,
            "reads": reads,
            "append_20k_ms": append_20k_ms,
        }
        con.close()
    return result


def benchmark_claygraph(logical_edges: int, versions: int, repetitions_legacy: int, repetitions_fast: int) -> dict[str, Any]:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript((ROOT / "research_entity/runtime/RAE_CLAYGRAPH_SCHEMA.sql").read_text())
    con.executescript((ROOT / "research_entity/runtime/RAE_CLAYGRAPH_V3_CURRENT_PROJECTIONS.sql").read_text())
    for epoch in range(1, versions + 1):
        con.execute(
            "INSERT INTO graph_epochs(graph_epoch,source_epoch,reason,created_at,status) VALUES(?,?,?,?,?)",
            (epoch, epoch, "synthetic-benchmark", "2026-08-10T00:00:00Z", "CURRENT"),
        )
    relations = ("dependency", "re_entry", "candidate", "provenance")
    batch = []
    for epoch in range(1, versions + 1):
        for i in range(logical_edges):
            status = "RETRACTED" if epoch == versions and i % 5 == 0 else "CURRENT"
            batch.append((
                f"E{epoch}:{i:07d}", f"L{i:07d}", epoch, f"N{i % 800:04d}",
                f"N{(i * 37 + epoch * 13) % 50000:05d}", relations[i % 4], (i % 100) / 100,
                0.9, "{}", "{}", "DERIVED", status, "2026-08-10T00:00:00Z",
            ))
            if len(batch) >= 5000:
                con.executemany("INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                batch = []
        if batch:
            con.executemany("INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
            batch = []
        con.commit()

    legacy_ids = {r[0] for r in con.execute("SELECT logical_edge_id FROM v_latest_graph_edges")}
    fast_ids = {r[0] for r in con.execute("SELECT logical_edge_id FROM v_graph_current_edges_fast")}

    queries = {
        "source": (
            "SELECT logical_edge_id,target_logical_id,relation_type,weight FROM {} WHERE source_logical_id=? ORDER BY relation_type,target_logical_id,logical_edge_id LIMIT 64",
            ("N0777",),
        ),
        "source_relation": (
            "SELECT logical_edge_id,target_logical_id,relation_type,weight FROM {} WHERE source_logical_id=? AND relation_type=? ORDER BY relation_type,target_logical_id,logical_edge_id LIMIT 64",
            ("N0777", "re_entry"),
        ),
        "global_relation": (
            "SELECT logical_edge_id,source_logical_id,target_logical_id,weight FROM {} WHERE relation_type=? ORDER BY weight DESC,logical_edge_id LIMIT 64",
            ("dependency",),
        ),
    }
    cases: dict[str, Any] = {}
    for name, (template, args) in queries.items():
        legacy_sql = template.format("v_latest_graph_edges")
        fast_sql = template.format("v_graph_current_edges_fast")
        legacy_rows = [tuple(r) for r in con.execute(legacy_sql, args)]
        fast_rows = [tuple(r) for r in con.execute(fast_sql, args)]
        legacy = timed(lambda s=legacy_sql, a=args: con.execute(s, a).fetchall(), repetitions_legacy)
        fast = timed(lambda s=fast_sql, a=args: con.execute(s, a).fetchall(), repetitions_fast)
        cases[name] = {
            "equivalent": legacy_rows == fast_rows,
            "legacy": legacy,
            "fast": fast,
            "p50_speedup": legacy["p50_ms"] / fast["p50_ms"],
        }

    retired = "L0000000"
    before = tuple(con.execute(
        "SELECT graph_epoch,source_status,target_logical_id FROM graph_head_edges WHERE logical_edge_id=?",
        (retired,),
    ).fetchone())
    con.execute(
        "INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("ZZZ_OLD", retired, max(1, versions - 1), "N0000", "N99999", "dependency", 1.0, 1.0,
         "{}", "{}", "DERIVED", "CURRENT", "2026-08-10T00:00:00Z"),
    )
    after = tuple(con.execute(
        "SELECT graph_epoch,source_status,target_logical_id FROM graph_head_edges WHERE logical_edge_id=?",
        (retired,),
    ).fetchone())
    result = {
        "logical_edges": logical_edges,
        "versions": versions,
        "physical_edge_rows": logical_edges * versions,
        "full_latest_set_equivalence": legacy_ids == fast_ids,
        "latest_current_edges": len(legacy_ids),
        "out_of_order_old_version_resurrection_guard": before == after,
        "cases": cases,
    }
    con.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-rows", type=int, default=100_000)
    parser.add_argument("--index-rows", type=int, default=200_000)
    parser.add_argument("--graph-logical", type=int, default=80_000)
    parser.add_argument("--graph-versions", type=int, default=3)
    parser.add_argument("--legacy-reps", type=int, default=5)
    parser.add_argument("--fast-reps", type=int, default=40)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = {
        "schema_version": "clay.storage_plane_replication.v1",
        "scope": "synthetic differential component benchmark; not universal database superiority",
        "environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "unifieddb_query_pushdown": benchmark_udb_pushdown(args.state_rows, args.legacy_reps, args.fast_reps),
        "unifieddb_index_ablation": benchmark_index_ablation(args.index_rows, 200, args.fast_reps),
        "claygraph_head_projection": benchmark_claygraph(args.graph_logical, args.graph_versions, args.legacy_reps, args.fast_reps),
    }
    text = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
